from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from Models.base import Base

if TYPE_CHECKING:
    from Models.event import Event


class RecurrenceRule(Base):
    __tablename__ = "recurrence_rules"

    id: Mapped[Optional[int]] = mapped_column(primary_key=True, autoincrement=True, init=False, default=None)
    event_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"), unique=True, default=None
    )
    event: Mapped[Optional[Event]] = relationship(back_populates="recurrence_rule", init=False)
    rrule_string: Mapped[str] = mapped_column(default="")
