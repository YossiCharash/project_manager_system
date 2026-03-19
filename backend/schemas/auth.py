from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: Optional[str] = None
    requires_password_change: Optional[bool] = False


class LoginInput(BaseModel):
    email: str
    password: str
    remember_me: bool = True


class RefreshTokenInput(BaseModel):
    refresh_token: str


class PasswordResetRequest(BaseModel):
    email: str


class PasswordReset(BaseModel):
    token: str
    new_password: str


class ResetPasswordWithToken(BaseModel):
    token: str
    new_password: str
    temp_password: Optional[str] = None


class ChangePassword(BaseModel):
    current_password: str
    new_password: str


class UserProfile(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime
    group_id: Optional[int] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    calendar_color: Optional[str] = None
    calendar_date_display: str = "gregorian"
    show_jewish_holidays: bool = True
    show_islamic_holidays: bool = False

    model_config = ConfigDict(from_attributes=True)
