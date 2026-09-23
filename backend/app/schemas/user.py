from pydantic import BaseModel, ConfigDict
from typing import Optional

class UserCreate(BaseModel):
    username: str
    password: str
    role: str
    facility_type: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    username: str
    role: str
    facility_type: Optional[str] = None
    is_active: bool

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
