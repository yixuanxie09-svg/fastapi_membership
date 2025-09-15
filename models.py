from sqlalchemy import Boolean,Column,ForeignKey,Integer, String,DateTime , Float, PrimaryKeyConstraint
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    question_text= Column(String, unique=True, index=True)
    
class Choices(Base):
    __tablename__ = "choices"
    
    id = Column(Integer, primary_key=True, index=True)
    choice_text = Column(String,index=True)
    is_correct = Column(Boolean,default=False)
    question_id = Column(Integer,ForeignKey("questions.id"))
    
class Member(Base):
    __tablename__ = "members"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    age = Column(Integer)
    password = Column(String)
    phone_number = Column(String, nullable=True) # 字串欄位，允許為空
    
    
    driving_records = relationship("DrivingRecord", back_populates="member", cascade="all, delete")
 

class DrivingRecord(Base):
    __tablename__ = "driving_records"

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.id"))
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    location_start = Column(String)
    location_end = Column(String)
    fatigue_level = Column(String)  # 可選：LOW / MEDIUM / HIGH
    fatigue_detected = Column(Boolean)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    data_logs = relationship("DrivingDataLog", back_populates="driving_record", cascade="all, delete")
    
    member = relationship("Member", back_populates="driving_records")
    
    # optional: 若之後要從會員反查駕駛紀錄可用
    # member = relationship("Member", back_populates="driving_records")
    
    
class ResetToken(Base):
    __tablename__ = "reset_tokens"
    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.id"))
    token = Column(String, index=True, unique=True)
    method = Column(String)  # "email" or "sms"
    expires_at = Column(DateTime)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    

class DrivingDataLog(Base):
    __tablename__ = "driving_data_logs"

    driving_record_id = Column(Integer, ForeignKey("driving_records.id", ondelete="CASCADE"))
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # 連續數據
    blink_rate = Column(Float, nullable=True)            # 眨眼次數/分鐘
    yawn_rate = Column(Float, nullable=True)             # 哈欠次數/分鐘
    eye_closure_duration = Column(Float, nullable=True)  # 閉眼持續時間(秒)
    fatigue_index = Column(Float, nullable=True)         # 疲勞指數(1-10)
    fatigue_detected = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        PrimaryKeyConstraint("driving_record_id", "timestamp"),
    )

    # 關聯到 DrivingRecord
    driving_record = relationship("DrivingRecord", back_populates="data_logs")