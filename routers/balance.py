from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from database import get_db
from models import UserBalance, User
from schemas import BalanceOut, TopUpBalance
from auth import get_current_user, require_super_admin

router = APIRouter(prefix="/balance", tags=["Balance"])


# --- Get my own balance (any logged-in user) --- MUST be before /{user_id}
@router.get("/me/balance", response_model=BalanceOut)
def get_my_balance(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    balance = db.query(UserBalance).filter(UserBalance.user_id == current_user.id).first()
    if not balance:
        balance = UserBalance(user_id=current_user.id)
        db.add(balance)
        db.commit()
        db.refresh(balance)

    return {
        "user_id": current_user.id,
        "full_name": current_user.full_name,
        "balance_mins": balance.balance_mins,
        "total_topped": balance.total_topped,
        "total_used": balance.total_used,
        "last_updated": balance.last_updated
    }


# --- Get any user's balance (admin only) ---
@router.get("/{user_id}", response_model=BalanceOut)
def get_user_balance(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    balance = db.query(UserBalance).filter(UserBalance.user_id == user_id).first()
    if not balance:
        balance = UserBalance(user_id=user_id)
        db.add(balance)
        db.commit()
        db.refresh(balance)

    return {
        "user_id": user.id,
        "full_name": user.full_name,
        "balance_mins": balance.balance_mins,
        "total_topped": balance.total_topped,
        "total_used": balance.total_used,
        "last_updated": balance.last_updated
    }


# --- Top up a user's balance manually (admin only) ---
@router.post("/topup", response_model=BalanceOut)
def topup_balance(
    data: TopUpBalance,
    db: Session = Depends(get_db),
    admin: User = Depends(require_super_admin)
):
    user = db.query(User).filter(User.id == data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    balance = db.query(UserBalance).filter(UserBalance.user_id == data.user_id).first()
    if not balance:
        balance = UserBalance(user_id=data.user_id)
        db.add(balance)

    balance.balance_mins += data.minutes
    balance.total_topped += data.minutes
    balance.last_updated = datetime.utcnow()
    db.commit()
    db.refresh(balance)

    return {
        "user_id": user.id,
        "full_name": user.full_name,
        "balance_mins": balance.balance_mins,
        "total_topped": balance.total_topped,
        "total_used": balance.total_used,
        "last_updated": balance.last_updated
    }


# --- Deduct minutes (called when machine runs, per minute) ---
@router.post("/deduct")
def deduct_balance(
    user_id: int,
    minutes: float = 1.0,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    balance = db.query(UserBalance).filter(UserBalance.user_id == user_id).first()
    if not balance:
        raise HTTPException(status_code=404, detail="No balance record found")
    if balance.balance_mins <= 0:
        raise HTTPException(status_code=400, detail="Out of credit")

    balance.balance_mins = max(0.0, balance.balance_mins - minutes)
    balance.total_used += minutes
    balance.last_updated = datetime.utcnow()
    db.commit()

    return {
        "success": True,
        "remaining_mins": balance.balance_mins,
        "out_of_credit": balance.balance_mins == 0
    }