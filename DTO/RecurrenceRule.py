from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
from database import Base

class RecurrenceRule(Base):
    __tablename__ = "recurrence_rules"

    id: Mapped[Optional[int]] = mapped_column(primary_key=True, autoincrement=True, init=False, default=None)
    event_id: Mapped[Optional[int]] = mapped_column(default=None)
    rrule_string: Mapped[str] = mapped_column(default="")
