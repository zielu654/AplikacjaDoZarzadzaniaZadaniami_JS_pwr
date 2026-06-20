from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
from Models.base import Base

class UserCredentials(Base):
    __tablename__ = "user_credentials"

    id: Mapped[Optional[int]] = mapped_column(primary_key=True, autoincrement=True, init=False, default=None)
    refresh_token: Mapped[str] = mapped_column(default="")
    token_uri: Mapped[str] = mapped_column(default="")
    client_id: Mapped[str] = mapped_column(default="")
    client_secret: Mapped[str] = mapped_column(default="")
