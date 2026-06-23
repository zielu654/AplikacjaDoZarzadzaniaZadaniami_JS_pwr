import re
from datetime import datetime
from typing import List, Optional

from fake_data import Task, Category, TaskRepository
from Models.event import Event
from Models.recurrence_rule import RecurrenceRule
from Models.category import CalendarColor
from DTO.eventDTO import EventDTO


class DatabaseTaskRepository(TaskRepository):
    """Adapter łączący frontendowy TaskRepository z kontrolerami bazy i Google API."""

    def __init__(self, session, event_ctrl, cat_ctrl):
        self.session = session
        self.event_ctrl = event_ctrl
        self.cat_ctrl = cat_ctrl

    def _event_dto_to_task(self, dto: EventDTO) -> Task:
        rrule_frontend = None
        if dto.start_datetime and dto.end_datetime:
            time_str = f"{dto.start_datetime.strftime('%H:%M')}-{dto.end_datetime.strftime('%H:%M')}"
            if dto.rrule_str:
                prefix = "co dzien"
                if "FREQ=DAILY" in dto.rrule_str:
                    prefix = "co dzien"
                elif "FREQ=WEEKLY" in dto.rrule_str:
                    prefix = "co dwa tyg" if "INTERVAL=2" in dto.rrule_str else "co tydz"
                rrule_frontend = f"{prefix} {time_str}"
            else:
                rrule_frontend = time_str

        return Task(
            id=dto.id,
            title=dto.title or "",
            description=dto.description or "",
            due_date=dto.start_datetime or datetime.now(),
            is_done=dto.is_completed or False,
            priority=dto.is_high_priority or False,
            category_id=dto.category.id if dto.category else None,
            created_at=dto.start_datetime or datetime.now(),
            modified_at=dto.updated_at or dto.start_datetime or datetime.now(),
            is_deleted=False,
            recurrence_rule=rrule_frontend
        )

    def _parse_time_and_rrule(self, task: Task):
        sh, sm, eh, em = 12, 0, 13, 0
        rrule_backend = None
        if task.recurrence_rule:
            match = re.search(r"(\d{1,2}):(\d{2})-(\d{1,2}):(\d{2})", task.recurrence_rule)
            if match:
                sh, sm, eh, em = (int(x) for x in match.groups())
                prefix = task.recurrence_rule[:match.start()].strip()
                if "co dzien" in prefix:
                    rrule_backend = "FREQ=DAILY"
                elif "co dwa tyg" in prefix:
                    rrule_backend = "FREQ=WEEKLY;INTERVAL=2"
                elif "co tydz" in prefix:
                    rrule_backend = "FREQ=WEEKLY"

        start_dt = task.due_date.replace(hour=sh, minute=sm, second=0,
                                         microsecond=0) if task.due_date else datetime.now()
        end_dt = task.due_date.replace(hour=eh, minute=em, second=0, microsecond=0) if task.due_date else datetime.now()
        return start_dt, end_dt, rrule_backend

    def get_all(self, include_deleted: bool = False) -> List[Task]:
        dtos = self.event_ctrl._event_repo.get_all()
        return [self._event_dto_to_task(d) for d in dtos]

    def get_habits(self) -> List[Task]:
        return [t for t in self.get_all() if t.recurrence_rule and "co " in t.recurrence_rule]

    def get_categories(self) -> List[Category]:
        dtos = self.cat_ctrl.get_all_categories()
        return [Category(id=d.id, name=d.name, color=d.color.hex_code) for d in dtos]

    def get_category(self, category_id: Optional[int]) -> Optional[Category]:
        if category_id is None:
            return None
        d = self.cat_ctrl.get_category_by_id(category_id)
        return Category(id=d.id, name=d.name, color=d.color.hex_code) if d else None

    def add_task(self, task: Task) -> Task:
        start_dt, end_dt, rrule_backend = self._parse_time_and_rrule(task)
        new_id = self.event_ctrl.create_new_event(
            title=task.title,
            description=task.description,
            category_id=task.category_id,
            start_datetime=start_dt,
            end_datetime=end_dt,
            priority=task.priority,
            rrule=rrule_backend
        )
        task.id = new_id
        return task

    def update_task(self, task: Task) -> Optional[Task]:
        event = self.session.get(Event, task.id)
        if not event:
            return None

        start_dt, end_dt, rrule_backend = self._parse_time_and_rrule(task)
        event.title = task.title
        event.description = task.description
        event.category_id = task.category_id
        event.is_high_priority = task.priority
        event.is_completed = task.is_done
        event.start_datetime = start_dt
        event.end_datetime = end_dt

        if rrule_backend:
            if event.recurrence_rule:
                event.recurrence_rule.rrule_string = rrule_backend
            else:
                event.recurrence_rule = RecurrenceRule(rrule_string=rrule_backend)
        else:
            if event.recurrence_rule:
                self.session.delete(event.recurrence_rule)
                event.recurrence_rule = None

        event.updated_at = datetime.now()
        self.session.commit()
        return task

    def delete_task(self, task_id: int) -> bool:
        try:
            self.event_ctrl.delete_event(task_id)
            return True
        except Exception:
            return False

    def add_category(self, category: Category) -> Category:
        # Mapowanie dowolnego koloru na bezpieczny odpowiednik Google
        mapped_color = CalendarColor.color_hex_to_callendarColor(category.color)
        valid_hex = mapped_color.hex_code

        new_id = self.cat_ctrl.create_category(
            name=category.name,
            color_hex=valid_hex,
            is_syncable=True
        )

        category.id = new_id
        category.color = valid_hex  # Zwracamy prawidłowy kolor do UI
        return category

    def update_category(self, category: Category) -> Optional[Category]:
        mapped_color = CalendarColor.color_hex_to_callendarColor(category.color)
        updates = {
            'name': category.name,
            'color_name': mapped_color.display_name
        }
        self.cat_ctrl.edit_category(category.id, updates)
        return category

    def delete_category(self, category_id: int) -> bool:
        try:
            self.cat_ctrl.delete_category(category_id, cascade=False)
            return True
        except Exception:
            return False