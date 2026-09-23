from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from app.schemas.user import Token, UserResponse
from app.api.deps import get_current_user, MOCK_USERS

router = APIRouter()

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if form_data.password != "demo123":
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if form_data.username not in MOCK_USERS:
        raise HTTPException(status_code=401, detail="Invalid credentials")
        
    return Token(access_token=f"mock-token-{form_data.username}", token_type="bearer")

@router.post("/refresh")
def refresh_token():
    return {"status": "mock refresh"}

@router.get("/me", response_model=UserResponse)
def get_me(current_user: UserResponse = Depends(get_current_user)):
    return current_user
