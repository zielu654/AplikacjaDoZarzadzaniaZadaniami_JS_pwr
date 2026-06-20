from datetime import datetime
from enum import Enum
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
from Models.base import Base

class EventSource(Enum):
    LOCAL = "local"
    GOOGLE = "google"

class Event(Base):
    __tablename__ = "events"

    id: Mapped[Optional[int]] = mapped_column(primary_key=True, autoincrement=True, init=False, default=None)
    category_id: Mapped[Optional[int]] = mapped_column(default=None)
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
