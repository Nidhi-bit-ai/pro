from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    created_at: datetime


class AuthResponse(BaseModel):
    user: UserResponse
    token: TokenResponse