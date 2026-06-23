from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from Models import Base
from DatabaseSqlAlchemy import SqlAlchemyEventRepository, SqlAlchemyCategoryRepository
from Controllers import EventController


def print_events(title: str, events: list):
    """Pomocnicza funkcja do ładnego wypisywania wyników"""
    print(f"\n{'=' * 10} {title} ({len(events)}) {'=' * 10}")
    if not events:
        print("Brak wyników.")
    for e in events:
        start_str = e.start_datetime.strftime("%Y-%m-%d %H:%M") if e.start_datetime else "Brak daty"
        priorytet = "[Ważne]" if e.is_high_priority else "[Normalne]"
        print(f"ID: {e.id} | {start_str} | {priorytet} | {e.title}")


def run_tests():
    engine = create_engine("sqlite:///:memory:")

    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    event_repo = SqlAlchemyEventRepository(session)
    category_repo = SqlAlchemyCategoryRepository(session)

    controller = EventController(event_repo, category_repo, sync_mediator=None)

    now = datetime.now()

    controller.create_new_event(
        title="Ważne spotkanie",
        description="Omówienie architektury",
        category_id=None,
        start_dt=now + timedelta(days=1),
        priority=True,
    )

    controller.create_new_event(
        title="Zakupy",
        description="Mleko, chleb",
        category_id=None,
        start_dt=now - timedelta(days=1),
        end_dt=now - timedelta(hours=20),
        priority=False,
    )

    controller.create_new_event(
        title="Wizyta u dentysty",
        description="Przegląd",
        category_id=None,
        start_dt=now + timedelta(days=7),
        priority=False,
    )

    controller.create_new_event(
        title="Wysłanie maila do klienta",
        description="Wycena projektu",
        category_id=None,
        start_dt=now + timedelta(hours=2),
        priority=True,
    )

    wszystkie = controller.build_query().sort_by("start_datetime", ascending=True).get_list()
    print_events("Wszystkie zadania (Rosnąco po dacie)", wszystkie)

    wazne = controller.build_query().high_priority().sort_by("start_datetime").get_list()
    print_events("Tylko wysoki priorytet", wazne)

    zalegle = controller.build_query().overdue().get_list()
    print_events("Zadania zaległe", zalegle)


if __name__ == "__main__":
    run_tests()
