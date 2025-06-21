from datetime import datetime
from enum import Enum
from uuid import UUID

from internal.helpers.utils import get_timestamp, get_uuid
from internal.models.db_base import Base
from pydantic import BaseModel
from sqlalchemy.orm import Mapped, mapped_column


# Enum for transfer description
class TransferStatus(str, Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class TransferType(str, Enum):
    INITIAL_DEPOSIT = "INITIAL_DEPOSIT"
    STANDARD = "STANDARD"


class TransferDB(Base):
    __tablename__ = "transfers"

    source_account_id: Mapped[UUID] = mapped_column(nullable=False)
    destination_account_id: Mapped[UUID] = mapped_column(nullable=False)
    amount: Mapped[float] = mapped_column(nullable=False)
    idempotency_key: Mapped[UUID] = mapped_column(nullable=False, unique=True)
    description: Mapped[str] = mapped_column(nullable=False)
    transfer_type: Mapped[TransferType] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=get_timestamp())
    updated_at: Mapped[datetime] = mapped_column(nullable=False, default=get_timestamp())
    id: Mapped[UUID] = mapped_column(primary_key=True, default=get_uuid())
    status: Mapped[TransferStatus] = mapped_column(nullable=False, default=TransferStatus.PENDING)
    is_initial_deposit: Mapped[bool] = mapped_column(nullable=False, default=False)


# API model
class CreateTransferRequest(BaseModel):
    source_account_id: UUID
    destination_account_id: UUID
    amount: float
    idempotency_key: UUID = get_uuid()
    description: str = ""
    transfer_type: TransferType = TransferType.STANDARD


class TransferDetailsResponse(BaseModel):
    id: UUID
    source_account_id: UUID
    destination_account_id: UUID
    amount: float
    status: TransferStatus
    description: str
    transfer_type: TransferType
    created_at: datetime

    class Config:
        from_attributes = True
