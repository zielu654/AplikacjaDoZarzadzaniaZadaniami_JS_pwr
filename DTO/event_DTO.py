from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from DTO.category_DTO import CategoryDTO
from Models.event import EventSource


@dataclass
class EventDTO:
    id: int | None
    title: str | None
    description: str | None
    start_datetime: datetime | None
    end_datetime: datetime | None
    is_high_priority: bool | None
    is_completed: bool | None
    rrule_str: str | None = None
    category: CategoryDTO | None = None
    source: EventSource = EventSource.LOCAL
