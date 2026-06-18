from datetime import datetime
from enum import Enum
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
from database import Base

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

    @classmethod
    def from_row(cls, row: tuple) -> 'Event':
        if not row:
            return None

        def parse_dt(dt_str):
            if not dt_str: return None
            return datetime.fromisoformat(dt_str)

        return cls(
            id=row[0],
            category_id=row[1],
            title=row[2],
            description=row[3],
            start_datetime=parse_dt(row[4]),
            end_datetime=parse_dt(row[5]),
            is_completed=bool(row[6]),
            is_high_priority=bool(row[7]),
            is_deleted=bool(row[8]),
            created_at=parse_dt(row[9]),
            updated_at=parse_dt(row[10]),
            source=EventSource(row[11])
        )