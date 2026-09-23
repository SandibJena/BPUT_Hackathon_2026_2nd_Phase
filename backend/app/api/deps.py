from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.user import UserResponse
from fastapi.security import OAuth2PasswordBearer
from typing import List

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

MOCK_USERS = {
    "health_worker_1": {"id": "hw-1", "username": "health_worker_1", "role": "health_worker", "is_active": True},
    "nurse_1": {"id": "n-1", "username": "nurse_1", "role": "nurse", "is_active": True},
    "doctor_1": {"id": "d-1", "username": "doctor_1", "role": "doctor", "is_active": True},
    "admin_1": {"id": "a-1", "username": "admin_1", "role": "admin", "is_active": True},
}

def get_current_user(token: str = Depends(oauth2_scheme)) -> UserResponse:
    # MOCK implementation for hackathon
    username = token.replace("mock-token-", "")
    if username not in MOCK_USERS:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return UserResponse(**MOCK_USERS[username])

def require_role(*roles: str):
    def role_checker(current_user: UserResponse = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user
    return role_checker
