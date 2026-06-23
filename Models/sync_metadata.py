from __future__ import annotations

from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship
from Models.base import Base
from sqlalchemy import ForeignKey

if TYPE_CHECKING:
    from Models.event import Event


class SyncMetadata(Base):
    __tablename__ = "sync_metadata"

    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), primary_key=True)
    google_event_id: Mapped[str] = mapped_column(default="")
    last_synced: Mapped[Optional[datetime]] = mapped_column(default=None)
    event: Mapped[Event] = relationship(back_populates="sync_metadata", init=False)
