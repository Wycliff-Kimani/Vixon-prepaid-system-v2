 
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models, schemas
from auth import require_distributor, get_current_user

router = APIRouter(prefix="/distro", tags=["Distributor"])

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