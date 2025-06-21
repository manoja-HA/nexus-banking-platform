from datetime import datetime
from uuid import UUID

from internal.helpers.utils import get_timestamp, get_uuid
from internal.models.db_base import Base
from pydantic import BaseModel
from sqlalchemy.orm import Mapped, mapped_column


class CustomerDB(Base):
    __tablename__ = "customers"
    name: Mapped[str] = mapped_column(nullable=False)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=get_uuid())
    created_at: Mapped[datetime] = mapped_column(default=get_timestamp())
    updated_at: Mapped[datetime] = mapped_column(default=get_timestamp())


# API model
class CustomerCreate(BaseModel):
    name: str


class CustomerFindResponse(BaseModel):
    id: UUID
    name: str
    created_at: datetime

    class Config:
        from_attributes = True
