from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
from database import Base

class SyncMetadata(Base):
    __tablename__ = "sync_metadata"

    event_id: Mapped[int] = mapped_column(primary_key=True)
    google_event_id: Mapped[str] = mapped_column(default="")
    last_synced: Mapped[Optional[datetime]] = mapped_column(default=None)
