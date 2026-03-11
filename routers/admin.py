 
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models, schemas
from auth import require_super_admin, hash_password

router = APIRouter(prefix="/admin", tags=["Admin"])

# --- Get all users ---
@router.get("/users")
def get_all_users(
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_super_admin)
):
    users = db.query(models.User).all()
    return users

# --- Get all distributors ---
@router.get("/distributors")
def get_distributors(
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_super_admin)
):
    distros = db.query(models.User).filter(
        models.User.role == models.UserRole.distributor
    ).all()
    return distros

# --- Create distributor ---
@router.post("/distributors", response_model=schemas.UserOut)
def create_distributor(
    payload: schemas.UserCreate,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_super_admin)
):
    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    distro = models.User(
        full_name=payload.full_name,
        email=payload.email,
        phone=payload.phone,
        hashed_password=hash_password(payload.password),
        role=models.UserRole.distributor
    )
    db.add(distro)
    db.commit()
    db.refresh(distro)
    return distro

# --- Create user under a distributor ---
@router.post("/users", response_model=schemas.UserOut)
def create_user(
    payload: schemas.UserCreate,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_super_admin)
):
    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Validate distro exists if distro_id provided
    if payload.distro_id:
        distro = db.query(models.User).filter(
            models.User.id == payload.distro_id,
            models.User.role == models.UserRole.distributor
        ).first()
        if not distro:
            raise HTTPException(status_code=404, detail="Distributor not found")

    user = models.User(
        full_name=payload.full_name,
        email=payload.email,
        phone=payload.phone,
        hashed_password=hash_password(payload.password),
        role=models.UserRole.user,
        distro_id=payload.distro_id
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

# --- Deactivate user ---
@router.patch("/users/{user_id}/deactivate")
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_super_admin)
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = False
    db.commit()
    return {"success": True, "message": f"User {user.full_name} deactivated"}

# --- Add machine ---
@router.post("/machines", response_model=schemas.MachineOut)
def create_machine(
    payload: schemas.MachineCreate,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_super_admin)
):
    existing = db.query(models.Machine).filter(
        models.Machine.machine_id == payload.machine_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Machine ID already exists")

    machine = models.Machine(
        machine_id=payload.machine_id,
        name=payload.name,
        location=payload.location
    )
    db.add(machine)
    db.commit()
    db.refresh(machine)
    return machine

# --- Get all machines ---
@router.get("/machines")
def get_machines(
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_super_admin)
):
    return db.query(models.Machine).all()