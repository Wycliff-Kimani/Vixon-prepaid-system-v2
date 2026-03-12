from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from database import get_db
from models import User, UserBalance, UserMessage, UserRole
from schemas import PinLoginRequest, PinLoginResponse, UserMessageCreate, UserMessageOut
from auth import get_current_user, require_super_admin

router = APIRouter(prefix="/machine", tags=["Machine"])


# --- PIN + Phone login at machine ---
@router.post("/login", response_model=PinLoginResponse)
def machine_pin_login(
    data: PinLoginRequest,
    db: Session = Depends(get_db)
):
    # Find user by PIN
    user = db.query(User).filter(
        User.pin == data.pin,
        User.role == UserRole.user,
        User.is_active == True
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="Invalid PIN or phone number")

    # Check last 3 digits of phone
    if not user.phone or not user.phone.endswith(data.phone_last3):
        raise HTTPException(status_code=404, detail="Invalid PIN or phone number")

    # Get balance
    balance = db.query(UserBalance).filter(UserBalance.user_id == user.id).first()
    if not balance:
        balance = UserBalance(user_id=user.id)
        db.add(balance)
        db.commit()
        db.refresh(balance)

    package_name = user.package.name if user.package else None

    return {
        "success": True,
        "user_id": user.id,
        "full_name": user.full_name,
        "balance_mins": balance.balance_mins,
        "package_name": package_name,
        "message": "Welcome! You can start the machine." if balance.balance_mins > 0 else "No balance. Please top up."
    }


# --- User sends message to admin ---
@router.post("/message")
def send_message(
    data: UserMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    msg = UserMessage(
        user_id=current_user.id,
        message=data.message
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return {"success": True, "message": "Message sent to admin"}


# --- Admin views all messages ---
@router.get("/messages", response_model=list[UserMessageOut])
def get_all_messages(
    db: Session = Depends(get_db),
    admin: User = Depends(require_super_admin)
):
    messages = db.query(UserMessage).order_by(
        UserMessage.created_at.desc()
    ).all()

    return [
        {
            "id": m.id,
            "user_id": m.user_id,
            "full_name": m.user.full_name,
            "message": m.message,
            "is_read": m.is_read,
            "created_at": m.created_at
        }
        for m in messages
    ]


# --- Admin marks message as read ---
@router.patch("/messages/{message_id}/read")
def mark_message_read(
    message_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_super_admin)
):
    msg = db.query(UserMessage).filter(UserMessage.id == message_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    msg.is_read = True
    db.commit()
    return {"success": True, "message": "Marked as read"}


# --- Unread messages count ---
@router.get("/messages/unread/count")
def unread_count(
    db: Session = Depends(get_db),
    admin: User = Depends(require_super_admin)
):
    count = db.query(UserMessage).filter(UserMessage.is_read == False).count()
    return {"unread_messages": count}