from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
from database import Base

class UserCredentials(Base):
    __tablename__ = "user_credentials"

    id: Mapped[Optional[int]] = mapped_column(primary_key=True, autoincrement=True, init=False, default=None)
    refresh_token: Mapped[str] = mapped_column(default="")
    token_uri: Mapped[str] = mapped_column(default="")
    client_id: Mapped[str] = mapped_column(default="")
    client_secret: Mapped[str] = mapped_column(default="")

    @classmethod
    def from_row(cls, row: tuple) -> 'UserCredentials':
        if not row: return None
        return cls(
            id=row[0],
            refresh_token=row[1],
            token_uri=row[2],
            client_id=row[3],
            client_secret=row[4]
        )