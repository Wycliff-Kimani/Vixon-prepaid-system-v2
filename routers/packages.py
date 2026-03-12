from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Package, User
from schemas import PackageCreate, PackageUpdate, PackageOut
from auth import get_current_user

router = APIRouter(prefix="/packages", tags=["Packages"])


def require_super_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Super admin access required")
    return current_user


@router.get("/", response_model=list[PackageOut])
def list_packages(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Package).filter(Package.is_active == True).all()


@router.get("/{package_id}", response_model=PackageOut)
def get_package(
    package_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    pkg = db.query(Package).filter(Package.id == package_id).first()
    if not pkg:
        raise HTTPException(status_code=404, detail="Package not found")
    return pkg


@router.post("/", response_model=PackageOut)
def create_package(
    data: PackageCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_super_admin)
):
    pkg = Package(**data.dict())
    db.add(pkg)
    db.commit()
    db.refresh(pkg)
    return pkg


@router.put("/{package_id}", response_model=PackageOut)
def update_package(
    package_id: int,
    data: PackageUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_super_admin)
):
    pkg = db.query(Package).filter(Package.id == package_id).first()
    if not pkg:
        raise HTTPException(status_code=404, detail="Package not found")
    for field, value in data.dict(exclude_unset=True).items():
        setattr(pkg, field, value)
    db.commit()
    db.refresh(pkg)
    return pkg


@router.delete("/{package_id}")
def deactivate_package(
    package_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_super_admin)
):
    pkg = db.query(Package).filter(Package.id == package_id).first()
    if not pkg:
        raise HTTPException(status_code=404, detail="Package not found")
    pkg.is_active = False
    db.commit()
    return {"success": True, "message": f"Package '{pkg.name}' deactivated"}