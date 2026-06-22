from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional, TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from Models.base import Base

if TYPE_CHECKING:
    from Models.recurrence_rule import RecurrenceRule
    from Models.sync_metadata import SyncMetadata

class EventSource(Enum):
    LOCAL = "local"
    GOOGLE = "google"

class Event(Base):
    __tablename__ = "events"

    id: Mapped[Optional[int]] = mapped_column(primary_key=True, autoincrement=True, init=False, default=None)
    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey("categories.id"), default=None)
    category: Mapped[Optional["Category"]] = relationship(init=False)
    title: Mapped[str] = mapped_column(default="")
    description: Mapped[str] = mapped_column(default="")
    start_datetime: Mapped[Optional[datetime]] = mapped_column(default=None)
    end_datetime: Mapped[Optional[datetime]] = mapped_column(default=None)
    is_completed: Mapped[bool] = mapped_column(default=False)
    is_high_priority: Mapped[bool] = mapped_column(default=False)
    is_deleted: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[Optional[datetime]] = mapped_column(default=None)
    updated_at: Mapped[Optional[datetime]] = mapped_column(default=None)
    source: Mapped[EventSource] = mapped_column(default=EventSource.LOCAL)
    recurrence_rule: Mapped[Optional[RecurrenceRule]] = relationship(
        back_populates="event",
        cascade="all, delete-orphan",
        init=False
    )
    sync_metadata: Mapped[Optional[SyncMetadata]] = relationship(
        back_populates="event",
        cascade="all, delete-orphan",
        init=False
    )

