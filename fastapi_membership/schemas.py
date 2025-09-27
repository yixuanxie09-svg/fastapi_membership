from pydantic import BaseModel, EmailStr
from typing import Optional , List
from datetime import datetime

class MemberBase(BaseModel):
    name: str
    email: EmailStr
    age: int
    phone_number: Optional[str] = None

class MemberCreate(MemberBase):
    password: str  #  接收密碼並加密後存入資料庫

class MemberOut(MemberBase):
    id: int

    class Config:
        orm_mode = True
        
class DrivingRecordCreate(BaseModel):
    member_id: int
    start_time: datetime
    end_time: datetime
    location_start: str
    location_end: str
    fatigue_level: Optional[str] = None  # LOW / MEDIUM / HIGH
    fatigue_detected: Optional[bool] = None

class DrivingRecordOut(DrivingRecordCreate):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str
    
class PhoneRequest(BaseModel):
    phone_number: str
    
class VerifyPhoneCodeRequest(BaseModel):
    phone_number: str
    code: str
  
class ResetPasswordWithPhoneRequest(BaseModel):
    phone_number: str
    code: str  

class PhoneReset(BaseModel):
    phone_number: str
    new_password: str
    code: str

class ForgotPasswordByPhoneRequest(BaseModel):
    phone_number: str

class ResetPasswordByPhoneRequest(BaseModel):
    phone_number: str
    code: str
    new_password: str
    
class DrivingDataLogCreate(BaseModel):
    driving_record_id: int
    timestamp: Optional[datetime] = None
    blink_rate: float
    yawn_rate: float
    eye_closure_duration: float
    fatigue_index: float
    fatigue_detected: bool


class DrivingDataLogOut(BaseModel):
    id: int
    driving_record_id: int
    timestamp: datetime
    blink_rate: float
    yawn_rate: float
    eye_closure_duration: float
    fatigue_index: float
    fatigue_detected: bool

