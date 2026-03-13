from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models, schemas
from auth import require_distributor, hash_password
import random

router = APIRouter(prefix="/distro", tags=["Distributor"])


def generate_unique_pin(db: Session) -> str:
    while True:
        pin = str(random.randint(1000, 9999))
        exists = db.query(models.User).filter(models.User.pin == pin).first()
        if not exists:
            return pin


# --- Get my users ---
@router.get("/users")
def get_my_users(
    db: Session = Depends(get_db),
    distro: models.User = Depends(require_distributor)
):
    users = db.query(models.User).filter(
        models.User.distro_id == distro.id
    ).all()
    return users


# --- Create user under this distro ---
@router.post("/users", response_model=schemas.UserOut)
def create_user_as_distro(
    payload: schemas.UserCreate,
    db: Session = Depends(get_db),
    distro: models.User = Depends(require_distributor)
):
    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    if payload.package_id:
        package = db.query(models.Package).filter(
            models.Package.id == payload.package_id,
            models.Package.is_active == True
        ).first()
        if not package:
            raise HTTPException(status_code=404, detail="Package not found")

    user = models.User(
        full_name=payload.full_name,
        email=payload.email,
        phone=payload.phone,
        hashed_password=hash_password(payload.password),
        role=models.UserRole.user,
        distro_id=distro.id,
        package_id=payload.package_id,
        pin=generate_unique_pin(db)
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    balance = models.UserBalance(user_id=user.id)
    db.add(balance)
    db.commit()

    return user


# --- Deactivate a user under this distro ---
@router.patch("/users/{user_id}/deactivate")
def deactivate_my_user(
    user_id: int,
    db: Session = Depends(get_db),
    distro: models.User = Depends(require_distributor)
):
    user = db.query(models.User).filter(
        models.User.id == user_id,
        models.User.distro_id == distro.id
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found or not under your account")
    user.is_active = False
    db.commit()
    return {"success": True, "message": f"{user.full_name} deactivated"}


# --- Get my transactions ---
@router.get("/transactions")
def get_my_transactions(
    db: Session = Depends(get_db),
    distro: models.User = Depends(require_distributor)
):
    transactions = db.query(models.Transaction).filter(
        models.Transaction.distro_id == distro.id
    ).order_by(models.Transaction.created_at.desc()).all()
    return transactions


# --- Get my earnings summary ---
@router.get("/earnings")
def get_my_earnings(
    db: Session = Depends(get_db),
    distro: models.User = Depends(require_distributor)
):
    earnings = db.query(models.DistroEarnings).filter(
        models.DistroEarnings.distro_id == distro.id
    ).all()

    total = sum(e.amount for e in earnings)
    paid = sum(e.amount for e in earnings if e.is_paid)
    pending = total - paid

    return {
        "total_earned": total,
        "total_paid": paid,
        "pending_payout": pending,
        "transactions": len(earnings)
    }


# --- Get my profile ---
@router.get("/me")
def get_my_profile(
    distro: models.User = Depends(require_distributor)
):
    return {
        "id": distro.id,
        "full_name": distro.full_name,
        "email": distro.email,
        "phone": distro.phone,
        "role": distro.role
    }