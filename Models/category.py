from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column

from Core import CalendarColor
from Models import Base



class Category(Base):
    __tablename__ = "categories"

    id: Mapped[Optional[int]] = mapped_column(primary_key=True, autoincrement=True, init=False, default=None)
    name: Mapped[str] = mapped_column(unique=True)
    color: Mapped[CalendarColor] = mapped_column(default=CalendarColor.DEFAULT)
    sync_enabled: Mapped[bool] = mapped_column(default=True)
    is_deleted: Mapped[bool] = mapped_column(default=False)
    updated_at: Mapped[datetime] = mapped_column(default_factory=datetime.now, onupdate=datetime.now)
