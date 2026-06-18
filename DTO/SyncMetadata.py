from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
from database import Base

class SyncMetadata(Base):
    __tablename__ = "sync_metadata"

    event_id: Mapped[int] = mapped_column(primary_key=True)
    google_event_id: Mapped[str] = mapped_column(default="")
    last_synced: Mapped[Optional[datetime]] = mapped_column(default=None)

    @classmethod
    def from_row(cls, row: tuple) -> 'SyncMetadata':
        if not row: return None
        return cls(
            event_id=row[0],
            google_event_id=row[1],
            last_synced=datetime.fromisoformat(row[2]) if row[2] else None
        )