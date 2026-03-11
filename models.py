from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime
import enum

class UserRole(str, enum.Enum):
    super_admin = "super_admin"
    secretary   = "secretary"
    distributor = "distributor"
    user        = "user"

class User(Base):
    __tablename__ = "users"

    id               = Column(Integer, primary_key=True, index=True)
    full_name        = Column(String, nullable=False)
    email            = Column(String, unique=True, index=True, nullable=False)
    phone            = Column(String, unique=True, nullable=True)
    hashed_password  = Column(String, nullable=False)
    role             = Column(Enum(UserRole), default=UserRole.user)
    is_active        = Column(Boolean, default=True)
    distro_id        = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at       = Column(DateTime, default=datetime.utcnow)

    # Self-referencing relationship with remote_side
    managed_users = relationship(
        "User",
        foreign_keys="User.distro_id",
        primaryjoin="User.distro_id == User.id",
        remote_side="User.id"
    )

    user_transactions = relationship(
        "Transaction",
        foreign_keys="Transaction.user_id",
        back_populates="user"
    )

    distro_transactions = relationship(
        "Transaction",
        foreign_keys="Transaction.distro_id",
        back_populates="distro"
    )

class Machine(Base):
    __tablename__ = "machines"

    id         = Column(Integer, primary_key=True, index=True)
    machine_id = Column(String, unique=True, index=True)
    name       = Column(String)
    location   = Column(String, nullable=True)
    is_active  = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    transactions = relationship("Transaction", back_populates="machine")

class Transaction(Base):
    __tablename__ = "transactions"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=True)
    machine_id = Column(Integer, ForeignKey("machines.id"), nullable=True)
    distro_id  = Column(Integer, ForeignKey("users.id"), nullable=True)
    amount     = Column(Float)
    credits    = Column(Float)
    mpesa_ref  = Column(String, nullable=True)
    phone      = Column(String, nullable=True)
    package_id = Column(String, nullable=True)
    status     = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)

    user    = relationship("User", foreign_keys=[user_id], back_populates="user_transactions")
    distro  = relationship("User", foreign_keys=[distro_id], back_populates="distro_transactions")
    machine = relationship("Machine", back_populates="transactions")

class DistroEarnings(Base):
    __tablename__ = "distro_earnings"

    id             = Column(Integer, primary_key=True, index=True)
    distro_id      = Column(Integer, ForeignKey("users.id"))
    transaction_id = Column(Integer, ForeignKey("transactions.id"))
    amount         = Column(Float)
    is_paid        = Column(Boolean, default=False)
    period         = Column(String)
    created_at     = Column(DateTime, default=datetime.utcnow)