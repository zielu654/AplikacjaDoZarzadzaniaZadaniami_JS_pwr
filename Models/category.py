from datetime import datetime
from typing import Optional
from enum import Enum
from sqlalchemy.orm import Mapped, mapped_column
from Models.base import Base


class CalendarColor(Enum):
    LAVENDER = ("1", "#7986cb", "Lawenda")
    SAGE = ("2", "#33b679", "Szałwia")
    GRAPE = ("3", "#8e24aa", "Winogrona")
    FLAMINGO = ("4", "#e67c73", "Flaming")
    BANANA = ("5", "#f6bf26", "Banan")
    TANGERINE = ("6", "#f4511e", "Mandarynka")
    PEACOCK = ("7", "#039be5", "Niebo")
    GRAPHITE = ("8", "#616161", "Grafit")
    BLUEBERRY = ("9", "#3f51b5", "Jagoda")
    BASIL = ("10", "#0b8043", "Bazylia")
    TOMATO = ("11", "#d50000", "Pomidor")
    DEFAULT = (None, "#039be5", "Kolor domyślny")

    @property
    def id(self) -> str:
        return self.value[0]

    @property
    def hex_code(self) -> str:
        return self.value[1]

    @property
    def display_name(self) -> str:
        return self.value[2]

    @staticmethod
    def color_name_to_callendarColor(color_name: str) -> "CalendarColor":
        if not color_name:
            return CalendarColor.DEFAULT

        search_name = color_name.strip().lower()

        for color in CalendarColor:
            if color.display_name.lower() == search_name:
                return color

        return CalendarColor.DEFAULT

    @staticmethod
    def color_hex_to_callendarColor(color_hex: str) -> "CalendarColor":
        if not color_hex:
            return CalendarColor.DEFAULT

        search_hex = color_hex.strip().lower()

        for color in CalendarColor:
            if color.hex_code.lower() == search_hex:
                return color

        return CalendarColor.DEFAULT


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[Optional[int]] = mapped_column(primary_key=True, autoincrement=True, init=False, default=None)
    name: Mapped[str] = mapped_column(unique=True)
    color: Mapped[CalendarColor] = mapped_column(default=CalendarColor.DEFAULT)
    sync_enabled: Mapped[bool] = mapped_column(default=True)
    is_deleted: Mapped[bool] = mapped_column(default=False)
    updated_at: Mapped[datetime] = mapped_column(default_factory=datetime.now, onupdate=datetime.now)
