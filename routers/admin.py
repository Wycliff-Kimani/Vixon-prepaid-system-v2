import random
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models, schemas
from auth import require_super_admin, hash_password

router = APIRouter(prefix="/admin", tags=["Admin"])


def generate_unique_pin(db: Session) -> str:
    while True:
        pin = str(random.randint(1000, 9999))
        exists = db.query(models.User).filter(models.User.pin == pin).first()
        if not exists:
            return pin


# --- Get all users ---
@router.get("/users")
def get_all_users(
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_super_admin)
):
    return db.query(models.User).all()


# --- Get all distributors ---
@router.get("/distributors")
def get_distributors(
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_super_admin)
):
    return db.query(models.User).filter(
        models.User.role == models.UserRole.distributor
    ).all()


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
        role=models.UserRole.distributor,
        pin=generate_unique_pin(db)
    )
    db.add(distro)
    db.commit()
    db.refresh(distro)

    settings = models.DistroSettings(distro_id=distro.id, commission_rate=10.0)
    db.add(settings)
    db.commit()

    return distro


# --- Create user ---
@router.post("/users", response_model=schemas.UserOut)
def create_user(
    payload: schemas.UserCreate,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_super_admin)
):
    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    if payload.distro_id:
        distro = db.query(models.User).filter(
            models.User.id == payload.distro_id,
            models.User.role == models.UserRole.distributor
        ).first()
        if not distro:
            raise HTTPException(status_code=404, detail="Distributor not found")

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
        distro_id=payload.distro_id,
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


# --- Get distro commission settings ---
@router.get("/distributors/{distro_id}/settings", response_model=schemas.DistroSettingsOut)
def get_distro_settings(
    distro_id: int,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_super_admin)
):
    settings = db.query(models.DistroSettings).filter(
        models.DistroSettings.distro_id == distro_id
    ).first()
    if not settings:
        raise HTTPException(status_code=404, detail="Distro settings not found")
    return settings


# --- Update distro commission rate ---
@router.patch("/distributors/{distro_id}/settings", response_model=schemas.DistroSettingsOut)
def update_distro_settings(
    distro_id: int,
    payload: schemas.DistroSettingsUpdate,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_super_admin)
):
    settings = db.query(models.DistroSettings).filter(
        models.DistroSettings.distro_id == distro_id
    ).first()
    if not settings:
        raise HTTPException(status_code=404, detail="Distro settings not found")
    settings.commission_rate = payload.commission_rate
    db.commit()
    db.refresh(settings)
    return settings


# --- Update user package ---
@router.patch("/users/{user_id}/package")
def update_user_package(
    user_id: int,
    package_id: int,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_super_admin)
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    package = db.query(models.Package).filter(
        models.Package.id == package_id,
        models.Package.is_active == True
    ).first()
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")

    user.package_id = package_id
    db.commit()
    return {"success": True, "message": f"Package updated to {package.name} for {user.full_name}"}