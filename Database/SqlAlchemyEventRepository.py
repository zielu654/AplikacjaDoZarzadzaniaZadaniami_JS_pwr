from typing import List

from Controllers.Interfaces import IEventRepository
from DTO.Event import Event


class SqlAlchemyEventRepository(IEventRepository):
    def __init__(self, session):
        self.session = session

    def add(self, event: Event) -> int:
        return super().add(event)

    def update(self, event: Event) -> None:
        super().update(event)

    def delete(self, event_id: int) -> None:
        super().delete(event_id)

    def get_all(self) -> List[Event]:
        return super().get_all()

    def get_dirty_records(self) -> List[Event]:
        return super().get_dirty_records()

