from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Enum, func, Text
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
    pin              = Column(String(4), unique=True, nullable=True)
    package_id       = Column(Integer, ForeignKey("packages.id"), nullable=True)
    created_at       = Column(DateTime, default=datetime.utcnow)

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

    balance  = relationship("UserBalance", back_populates="user", uselist=False)
    package  = relationship("Package", foreign_keys=[package_id])
    messages = relationship("UserMessage", back_populates="user")


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


class Package(Base):
    __tablename__ = "packages"

    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String, nullable=False)
    price_kes   = Column(Float, nullable=False)
    credits     = Column(Integer, nullable=False)
    description = Column(String, nullable=True)
    is_active   = Column(Boolean, default=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())


class UserBalance(Base):
    __tablename__ = "user_balance"

    id           = Column(Integer, primary_key=True, index=True)
    user_id      = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    balance_mins = Column(Float, default=0.0)
    total_topped = Column(Float, default=0.0)
    total_used   = Column(Float, default=0.0)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="balance")


class DistroSettings(Base):
    __tablename__ = "distro_settings"

    id              = Column(Integer, primary_key=True, index=True)
    distro_id       = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    commission_rate = Column(Float, default=10.0)
    created_at      = Column(DateTime, default=datetime.utcnow)
    updated_at      = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    distro = relationship("User", foreign_keys=[distro_id])


class UserMessage(Base):
    __tablename__ = "user_messages"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    message    = Column(Text, nullable=False)
    is_read    = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="messages")