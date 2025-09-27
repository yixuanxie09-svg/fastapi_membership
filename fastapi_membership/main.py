from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import List, Annotated , Optional
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
import secrets

import models
from database import engine, SessionLocal
from models import Member, DrivingRecord, ResetToken , DrivingDataLog
from schemas import DrivingRecordCreate, DrivingRecordOut, ForgotPasswordRequest, ResetPasswordRequest , ForgotPasswordByPhoneRequest, ResetPasswordByPhoneRequest ,VerifyPhoneCodeRequest ,ResetPasswordWithPhoneRequest
     


app = FastAPI()
models.Base.metadata.create_all(bind=engine)

from models import Member, DrivingRecord  
from schemas import DrivingRecordCreate, DrivingRecordOut  

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class ChoiceBase(BaseModel):
    choice_text:str
    is_correct:bool
    
class QuestionBase(BaseModel):
    question_text:str
    choices:List[ChoiceBase]
    
class MemberCreate(BaseModel):
    name: str
    email: EmailStr
    age: int
    password: str
    phone_number: str

    
class MemberOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    age: int
    phone_number: Optional[str] = None

    class Config:
        orm_mode = True
    
def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
db_dependency = Annotated[Session,Depends(get_db)]

@app.get("/question/{question_id}")
async def read_question(question_id: int, db:db_dependency):
    result = db.query(models.Question).filter(models.Question.id == question_id).first()
    if not result:
        raise HTTPException(status_code=404,detail='Question is not found')
    return result
        
@app.get("/choice/{question_id}")
async def read_choices(question_id: int, db:db_dependency):
    result = db.query(models.Choices).filter(models.Choices.question_id == question_id).all()
    if not result:
        raise HTTPException(status_code=404,detail='Choices is not found')
    return result
    
@app.post("/questions/")
async def create_questions(question: QuestionBase, db:db_dependency):
    db_question = models.Question(question_text=question.question_text)
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    for choice in question.choices:
        db_choice=models.Choices(choice_text=choice.choice_text,is_correct=choice.is_correct,question_id=db_question.id)
        db.add(db_choice)
        
    db.commit()
    return {"message": "Question and choices created"}
        
# 新增會員 API
@app.post("/members/", response_model=List[MemberOut])
def create_members(members:List[MemberCreate], db: Session = Depends(get_db)):
    created_members = []
    for member in members:
        hashed_password = pwd_context.hash(member.password)
        print(f"Received password for {member.email}, hashed: {hashed_password}")
        db_member = Member(name=member.name, email=member.email, age=member.age, password=hashed_password,phone_number=member.phone_number)
        try:
            db.add(db_member)
            db.commit()
            db.refresh(db_member)
            created_members.append(db_member)
        except IntegrityError:
            db.rollback()
            # 可以選擇記錄錯誤，不 raise，讓流程繼續
            continue  # Skip this member
    return created_members

# 查詢會員列表 API
@app.get("/members/", response_model=List[MemberOut])
def read_members(db: Session = Depends(get_db)):
    return db.query(Member).all()
    
    
@app.get("/")
async def root():
    return {"message": "Hello, this is the homepage!"}
    
class LoginForm(BaseModel):
    email: EmailStr
    password: str
    
@app.post("/login")
def login(form: LoginForm, db: Session = Depends(get_db)):
    user = db.query(Member).filter(Member.email == form.email).first()
    if not user or not pwd_context.verify(form.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return {"message": "Login success"}
    
    
@app.post("/driving_records", response_model=DrivingRecordOut)
def create_record(record: DrivingRecordCreate, db: Session = Depends(get_db)):
    db_record = DrivingRecord(**record.dict())
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record

@app.get("/driving_records", response_model=List[DrivingRecordOut])
def get_records(member_id: Optional[int] = None, db: Session = Depends(get_db)):
    if member_id:
        return db.query(DrivingRecord).filter(DrivingRecord.member_id == member_id).all()
    return db.query(DrivingRecord).all()

@app.post("/forgot-password")
def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    member = db.query(Member).filter(Member.email == request.email).first()
    if not member:
        raise HTTPException(status_code=404, detail="Email not found")

    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(minutes=10)

    reset_token = ResetToken(
        member_id=member.id,
        token=token,
        method="email",
        expires_at=expires_at
    )
    db.add(reset_token)
    db.commit()

    print(f"Send this reset link to user: https://yourapp.com/reset-password?token={token}")

    return {"message": "Password reset link sent"}

@app.post("/reset-password")
def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    reset_token = db.query(ResetToken).filter(ResetToken.token == request.token).first()
    if not reset_token:
        raise HTTPException(status_code=400, detail="Invalid token")
    if reset_token.used:
        raise HTTPException(status_code=400, detail="Token already used")
    if reset_token.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Token expired")

    member = db.query(Member).filter(Member.id == reset_token.member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="User not found")

    member.password = pwd_context.hash(request.new_password)
    reset_token.used = True
    db.commit()

    return {"message": "Password has been reset successfully"}
    
@app.post("/forgot-password-phone")
def forgot_password_phone(request: ForgotPasswordByPhoneRequest, db: Session = Depends(SessionLocal)):
    member = db.query(Member).filter(Member.phone_number == request.phone_number).first()
    if not member:
        raise HTTPException(status_code=404, detail="Phone number not found")

    code = secrets.randbelow(899999) + 100000
    expires_at = datetime.utcnow() + timedelta(minutes=5)

    reset_token = ResetToken(
        member_id=member.id,
        token=str(code),
        method="phone",
        expires_at=expires_at
    )
    db.add(reset_token)
    db.commit()

    print(f"🔴 Send this code to user via SMS: {code}")
    return {"message": "Verification code sent to phone"}

# 🔴 驗證手機驗證碼 (選擇性)
@app.post("/verify-phone-code")
def verify_phone_code(request: VerifyPhoneCodeRequest, db: Session = Depends(SessionLocal)):
    reset_token = db.query(ResetToken).filter(
        ResetToken.token == request.code,
        ResetToken.method == "phone",
        ResetToken.used == False
    ).join(Member).filter(Member.phone_number == request.phone_number).first()

    if not reset_token:
        raise HTTPException(status_code=400, detail="Invalid or expired code")
    if reset_token.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Code expired")

    return {"message": "Phone code verified"}

# 🔴 手機驗證碼重設密碼
@app.post("/reset-password-phone")
def reset_password_phone(request: ResetPasswordWithPhoneRequest, db: Session = Depends(SessionLocal)):
    reset_token = db.query(ResetToken).filter(
        ResetToken.token == request.new_password[:6],
        ResetToken.method == "phone",
        ResetToken.used == False
    ).join(Member).filter(Member.phone_number == request.phone_number).first()

    if not reset_token or reset_token.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired code")

    member = db.query(Member).filter(Member.id == reset_token.member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="User not found")

    member.password = pwd_context.hash(request.new_password)
    reset_token.used = True
    db.commit()

    return {"message": "Password has been reset via phone successfully"}
    
    
class DrivingDataLogCreate(BaseModel):
    driving_record_id: int
    timestamp: Optional[datetime] = None
    blink_rate: Optional[float] = None
    yawn_rate: Optional[float] = None
    eye_closure_duration: Optional[float] = None
    fatigue_index: Optional[float] = None
    fatigue_detected: Optional[bool] = False

class DrivingDataLogOut(DrivingDataLogCreate):
    created_at: datetime

    class Config:
        orm_mode = True

# === 新增 === 新增一筆駕駛連續數據
@app.post("/driving_data_logs", response_model=DrivingDataLogOut)
def create_driving_data_log(log: DrivingDataLogCreate, db: Session = Depends(get_db)):
    driving_record = db.query(DrivingRecord).filter(DrivingRecord.id == log.driving_record_id).first()
    if not driving_record:
        raise HTTPException(status_code=404, detail="Driving record not found")

    new_log = DrivingDataLog(
        driving_record_id=log.driving_record_id,
        timestamp=log.timestamp or datetime.utcnow(),
        blink_rate=log.blink_rate,
        yawn_rate=log.yawn_rate,
        eye_closure_duration=log.eye_closure_duration,
        fatigue_index=log.fatigue_index,
        fatigue_detected=log.fatigue_detected
    )
    db.add(new_log)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Log with same timestamp already exists")
    db.refresh(new_log)
    return new_log

# === 新增 === 查詢某次駕駛紀錄的所有連續數據
@app.get("/driving_data_logs/{driving_record_id}", response_model=List[DrivingDataLogOut])
def get_driving_data_logs(driving_record_id: int, db: Session = Depends(get_db)):
    logs =(
        db.query(DrivingDataLog)
        .filter(DrivingDataLog.driving_record_id == driving_record_id)
        .order_by(DrivingDataLog.timestamp) 
        .all()
    )
    return logs