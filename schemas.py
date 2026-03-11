from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from models import UserRole

# --- Auth ---
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    full_name: str

# --- Users ---
class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    password: str
    role: UserRole = UserRole.user
    distro_id: Optional[int] = None

class UserOut(BaseModel):
    id: int
    full_name: str
    email: str
    phone: Optional[str]
    role: UserRole
    is_active: bool
    distro_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True

# --- Machine ---
class MachineCreate(BaseModel):
    machine_id: str
    name: str
    location: Optional[str] = None

class MachineOut(MachineCreate):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True