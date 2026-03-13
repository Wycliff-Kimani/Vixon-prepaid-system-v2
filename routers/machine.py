from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models
from pydantic import BaseModel
from auth import require_super_admin

router = APIRouter(prefix="/machine", tags=["Machine"])


class LoginPayload(BaseModel):
    pin: str
    phone_last3: str


class MessagePayload(BaseModel):
    user_id: int
    message: str


# --- Combined login (PIN + phone last 3) ---
@router.post("/login")
def machine_login(payload: LoginPayload, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(
        models.User.pin == payload.pin,
        models.User.is_active == True
    ).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid PIN")
    if not user.phone or not user.phone.endswith(payload.phone_last3):
        raise HTTPException(status_code=401, detail="Phone confirmation failed")

    balance = db.query(models.UserBalance).filter(
        models.UserBalance.user_id == user.id
    ).first()

    package_name = None
    if user.package_id:
        package = db.query(models.Package).filter(
            models.Package.id == user.package_id
        ).first()
        if package:
            package_name = package.name

    return {
        "user_id": user.id,
        "full_name": user.full_name,
        "phone": user.phone,
        "package_name": package_name,
        "balance_mins": balance.balance_mins if balance else 0.0
    }


# --- Send message to admin (no auth needed — machine user has no JWT) ---
@router.post("/message")
def send_message(payload: MessagePayload, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(
        models.User.id == payload.user_id,
        models.User.is_active == True
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    msg = models.UserMessage(
        user_id=payload.user_id,
        message=payload.message.strip()
    )
    db.add(msg)
    db.commit()
    return {"success": True, "message": "Message sent to admin"}


# --- Get all messages (admin only) ---
@router.get("/messages")
def get_messages(
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_super_admin)
):
    messages = db.query(models.UserMessage).order_by(
        models.UserMessage.created_at.desc()
    ).all()
    result = []
    for m in messages:
        result.append({
            "id": m.id,
            "user_id": m.user_id,
            "full_name": m.user.full_name if m.user else "Unknown",
            "message": m.message,
            "is_read": m.is_read,
            "created_at": m.created_at.isoformat()
        })
    return result


# --- Mark message as read (admin only) ---
@router.patch("/messages/{message_id}/read")
def mark_message_read(
    message_id: int,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_super_admin)
):
    msg = db.query(models.UserMessage).filter(
        models.UserMessage.id == message_id
    ).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    msg.is_read = True
    db.commit()
    return {"success": True}


# --- Unread message count (admin overview) ---
@router.get("/messages/unread/count")
def unread_count(
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_super_admin)
):
    count = db.query(models.UserMessage).filter(
        models.UserMessage.is_read == False
    ).count()
    return {"unread_messages": count}