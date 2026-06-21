from dataclasses import dataclass

from Models.category import CalendarColor


@dataclass
class CategoryDTO:
    id: int
    name: str
    color: CalendarColor
    sync_enabled: bool