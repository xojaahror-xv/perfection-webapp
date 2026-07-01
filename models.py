from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, unique=True, index=True) # Telegram id
    full_name = Column(String)
    phone_number = Column(String)
    level = Column(String)
    points = Column(Integer, default=0)
    streak_days = Column(Integer, default=0)
    last_login = Column(DateTime, default=func.now())
    is_premium = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())

class DailyContent(Base):
    __tablename__ = "daily_content"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(String, unique=True, index=True) # e.g. "2026-06-13"
    words = Column(Text) # JSON string of 5 words
    idiom = Column(String)
    idiom_meaning = Column(String)

class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Integer)
    provider = Column(String) # "click" or "payme"
    status = Column(String, default="pending") # "pending", "success", "failed"
    created_at = Column(DateTime, default=func.now())
    
    user = relationship("User")
