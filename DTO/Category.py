from typing import Optional
from enum import Enum
from sqlalchemy.orm import Mapped, mapped_column
from database import Base

class CalendarColor(Enum):
    LAVENDER = ("1", "#7986cb", "Lawenda")
    SAGE     = ("2", "#33b679", "Szałwia")
    GRAPE    = ("3", "#8e24aa", "Winogrona")
    FLAMINGO = ("4", "#e67c73", "Flaming")
    BANANA   = ("5", "#f6bf26", "Banan")
    TANGERINE= ("6", "#f4511e", "Mandarynka")
    PEACOCK  = ("7", "#039be5", "Niebo")
    GRAPHITE = ("8", "#616161", "Grafit")
    BLUEBERRY= ("9", "#3f51b5", "Jagoda")
    BASIL    = ("10", "#0b8043", "Bazylia")
    TOMATO   = ("11", "#d50000", "Pomidor")
    DEFAULT  = (None, "#039be5", "Kolor domyślny")

    @property
    def id(self) -> str:
        return self.value[0]

    @property
    def hex_code(self) -> str:
        return self.value[1]

    @property
    def display_name(self) -> str:
        return self.value[2]

class Category(Base):
    __tablename__ = "categories"

    id: Mapped[Optional[int]] = mapped_column(primary_key=True, autoincrement=True, init=False, default=None)
    name: Mapped[str] = mapped_column(default="")
    color: Mapped[CalendarColor] = mapped_column(default=CalendarColor.DEFAULT)
    is_synced: Mapped[bool] = mapped_column(default=True)

    @classmethod
    def from_row(cls, row: tuple) -> 'Category':
        if not row:
            return None
        return cls(
            id=row[0],
            name=row[1],
            color=CalendarColor[row[2]] if row[2] in CalendarColor.__members__ else CalendarColor.DEFAULT,
            is_synced=bool(row[3])
        )