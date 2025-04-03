from sqlalchemy import Boolean, Column, Integer, String, DateTime, Text, Enum
from sqlalchemy.sql import func
import enum

from app.db.session import Base

class Gender(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    
    # 基本个人资料
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    # 扩展个人资料
    avatar_url = Column(String, nullable=True)
    bio = Column(Text, nullable=True)
    location = Column(String, nullable=True)
    website = Column(String, nullable=True)
    gender = Column(Enum(Gender), nullable=True)
    phone = Column(String, nullable=True)
    birth_date = Column(DateTime, nullable=True)
    
    # 社交账号关联
    github_id = Column(String, nullable=True, unique=True)
    google_id = Column(String, nullable=True, unique=True)
    
    # 隐私设置
    is_private = Column(Boolean, default=False)
    
    # 审计字段
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)