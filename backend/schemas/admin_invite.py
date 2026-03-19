from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class AdminInviteCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)
    expires_days: int = Field(default=7, ge=1, le=30)


class AdminInviteOut(BaseModel):
    id: int
    invite_token: str
    email: str
    full_name: str
    created_by: Optional[int]
    is_used: bool
    used_at: Optional[datetime]
    expires_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminInviteList(BaseModel):
    id: int
    invite_code: Optional[str] = None
    email: str
    full_name: str
    is_used: bool
    used_at: Optional[datetime] = None
    expires_at: datetime
    created_at: datetime
    is_expired: bool

    model_config = ConfigDict(from_attributes=True)


class AdminInviteUse(BaseModel):
    invite_code: str
    password: str = Field(min_length=8, max_length=128)
