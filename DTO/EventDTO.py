from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from DTO.CategoryDTO import CategoryDTO


@dataclass
class EventDTO:
    id: int
    title: str
    description: str
    start_time: datetime
    end_time: datetime

    category: Optional[CategoryDTO] = None