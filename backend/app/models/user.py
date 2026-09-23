from sqlalchemy import Column, String, Boolean, Enum as SQLEnum
from app.models.base import BaseModel
import enum

class RoleEnum(str, enum.Enum):
    health_worker = "health_worker"
    nurse = "nurse"
    doctor = "doctor"
    admin = "admin"

class User(BaseModel):
    __tablename__ = "users"
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(SQLEnum(RoleEnum), nullable=False)
    facility_type = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
