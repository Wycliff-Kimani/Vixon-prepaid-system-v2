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
    package_id: Optional[int] = None

class UserOut(BaseModel):
    id: int
    full_name: str
    email: str
    phone: Optional[str]
    role: UserRole
    is_active: bool
    distro_id: Optional[int]
    package_id: Optional[int]
    pin: Optional[str]
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

# --- Packages ---
class PackageCreate(BaseModel):
    name: str
    price_kes: float
    credits: int
    description: str | None = None
    is_active: bool = True

class PackageUpdate(BaseModel):
    name: str | None = None
    price_kes: float | None = None
    credits: int | None = None
    description: str | None = None
    is_active: bool | None = None

class PackageOut(BaseModel):
    id: int
    name: str
    price_kes: float
    credits: int
    description: str | None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

# --- User Balance ---
class BalanceOut(BaseModel):
    user_id: int
    full_name: str
    balance_mins: float
    total_topped: float
    total_used: float
    last_updated: datetime

    class Config:
        from_attributes = True

class TopUpBalance(BaseModel):
    user_id: int
    minutes: float

# --- Distro Settings ---
class DistroSettingsOut(BaseModel):
    distro_id: int
    commission_rate: float
    updated_at: datetime

    class Config:
        from_attributes = True

class DistroSettingsUpdate(BaseModel):
    commission_rate: float

# --- Machine PIN Access ---
class PinLoginRequest(BaseModel):
    pin: str

class PinLoginResponse(BaseModel):
    success: bool
    user_id: int
    full_name: str
    balance_mins: float
    package_name: str | None
    message: str

# --- User Messages ---
class UserMessageCreate(BaseModel):
    message: str

class UserMessageOut(BaseModel):
    id: int
    user_id: int
    full_name: str
    message: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True