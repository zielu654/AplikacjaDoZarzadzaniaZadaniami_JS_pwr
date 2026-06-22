import datetime
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from Models.base import Base
from Models.event import Event
from Models.category import Category
from Models.sync_metadata import SyncMetadata
from Models.user_credentials import UserCredentials
from Models.recurrence_rule import RecurrenceRule

from DTO.categoryDTO import CategoryDTO
from DTO.eventDTO import EventDTO

from DatabaseSqlAlchemy.sql_alchemy_user_credentials_repository import SqlAlchemyUserCredentialsRepository
from Models.category import CalendarColor
from Services.google_calendar_service import GoogleCalendarService


def run_demo():
    print("🚀 Rozpoczynam demonstrację integracji z Google Calendar...\n")

    current_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(current_dir, "demo_test.db")
    project_root = os.path.dirname(current_dir)
    creds_path = os.path.join(project_root, "Secrets", "credentials.json")

    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    repo_creds = SqlAlchemyUserCredentialsRepository(session)

    print("🔑 Łączenie z Google API... (Jeśli nie masz tokenu w demo_test.db, otworzy się przeglądarka)")
    google_service = GoogleCalendarService(credentials_repository=repo_creds, current_user_id=1, credentials_path=creds_path)
    print("✅ Połączono i zautoryzowano!\n")

    now = datetime.datetime.now(datetime.timezone.utc)

    kategoria_praca = CategoryDTO(
        id=1, name="Praca", color=CalendarColor.TOMATO, sync_enabled=True
    )

    event1 = EventDTO(
        id=None,
        title="[DEMO] Ważne Spotkanie",
        description="To jest testowe spotkanie z przypisaną kategorią.",
        start_datetime=now + datetime.timedelta(hours=1),
        end_datetime=now + datetime.timedelta(hours=2),
        is_high_priority=True,
        is_completed=False,
        category=kategoria_praca
    )

    event2 = EventDTO(
        id=None,
        title="[DEMO] Zwykłe zadanie",
        description="Zadanie bez kategorii i koloru.",
        start_datetime=now + datetime.timedelta(hours=3),
        end_datetime=now + datetime.timedelta(hours=4),
        is_high_priority=False,
        is_completed=False,
        category=None
    )

    event3 = EventDTO(
        id=None,
        title="[DEMO] Codzienny Standup",
        description="Test reguły powtarzania. Powinno pojawić się 3 razy dzień po dniu.",
        start_datetime=now + datetime.timedelta(days=1, hours=2),
        end_datetime=now + datetime.timedelta(days=1, hours=3),
        is_high_priority=False,
        is_completed=False,
        rrule_str="FREQ=DAILY;COUNT=3",
        category=kategoria_praca
    )

    events_to_send = [event1, event2, event3]

    print("📤 Wysyłanie wydarzeń do chmury Google...")
    google_ids = []
    for ev in events_to_send:
        g_id = google_service.push_event(ev)
        google_ids.append(g_id)
        print(f"   -> Wysłano: '{ev.title}' (Nadane ID Google: {g_id})")
    print("✅ Zakończono wysyłanie.\n")

    print("📥 Pobieranie nadchodzących wydarzeń z Google Calendar...")
    fetched_events = google_service.get_upcoming_events(max_results=15)

    print("✅ Zakończono pobieranie. Znalezione wydarzenia (zawierające tag [DEMO]):")

    demo_events_found = 0
    for fetched_ev in fetched_events:
        if "[DEMO]" in fetched_ev.title:
            demo_events_found += 1
            print("-" * 50)
            print(f"🔹 Tytuł:       {fetched_ev.title}")
            print(f"🔹 Start:       {fetched_ev.start_datetime.astimezone().strftime('%Y-%m-%d %H:%M')}")
            print(f"🔹 Opis:        {fetched_ev.description}")
            if fetched_ev.rrule_str:
                print(f"🔹 Cykliczność: {fetched_ev.rrule_str}")
            print(f"🔹 Źródło:      {fetched_ev.source.name}")

    print("-" * 50)
    print(f"\n🎉 Test zakończony! Znalazłem {demo_events_found} wystąpień wydarzeń testowych w Google Calendar.")
    print("👉 Wejdź teraz na swój Google Calendar w przeglądarce i sprawdź, czy tam są!")
    print("👉 Mają prefiks [DEMO], więc łatwo je wyszukasz i usuniesz.")

    session.close()


if __name__ == "__main__":
    run_demo()