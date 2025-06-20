from datetime import datetime
from enum import Enum
from uuid import UUID

from internal.helpers.utils import get_timestamp
from internal.models.db_base import Base
from pydantic import BaseModel
from sqlalchemy import CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column


# Enum for account status
class AccountStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"
    CLOSED = "CLOSED"


class AccountDB(Base):
    __tablename__ = "accounts"
    id: Mapped[UUID] = mapped_column(primary_key=True)
    customer_id: Mapped[UUID] = mapped_column(nullable=False)
    account_number: Mapped[str] = mapped_column(nullable=False, unique=True)
    current_balance: Mapped[float] = mapped_column(nullable=False)
    version: Mapped[int] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=get_timestamp())
    updated_at: Mapped[datetime] = mapped_column(default=get_timestamp())
    status: Mapped[AccountStatus] = mapped_column(nullable=False, default=AccountStatus.ACTIVE)
    # Constraints
    __table_args__ = (CheckConstraint("current_balance >= 0", name="check_positive_balance"),)


# API model
class CreateAccountRequest(BaseModel):
    customer_id: UUID
    initial_deposit: float


class AccountBalanceResponse(BaseModel):
    id: UUID
    customer_id: UUID
    account_number: str
    current_balance: float

    class Config:
        from_attributes = True


class AccountDetailsResponse(BaseModel):
    id: UUID
    customer_id: UUID
    account_number: str
    created_at: datetime
    status: AccountStatus

    class Config:
        from_attributes = True
