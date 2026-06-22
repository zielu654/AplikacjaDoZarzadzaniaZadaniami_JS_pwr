from datetime import datetime
from typing import Optional, Text
from sqlalchemy.orm import Mapped, mapped_column
from Models.base import Base


class UserCredentials(Base):
    __tablename__ = "user_credentials"

    id: Mapped[Optional[int]] = mapped_column(primary_key=True, autoincrement=True, init=False, default=None)

    user_id: Mapped[int] = mapped_column(unique=True)

    token_data: Mapped[str] = mapped_column(default="")

    created_at: Mapped[datetime] = mapped_column(default_factory=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(default_factory=datetime.now, onupdate=datetime.now)
