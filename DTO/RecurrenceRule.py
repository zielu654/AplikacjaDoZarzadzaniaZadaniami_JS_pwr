from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
from database import Base

class RecurrenceRule(Base):
    __tablename__ = "recurrence_rules"

    id: Mapped[Optional[int]] = mapped_column(primary_key=True, autoincrement=True, init=False, default=None)
    event_id: Mapped[Optional[int]] = mapped_column(default=None)
    rrule_string: Mapped[str] = mapped_column(default="")

    @classmethod
    def from_row(cls, row: tuple) -> 'RecurrenceRule':
        if not row: return None
        return cls(id=row[0], event_id=row[1], rrule_string=row[2])