import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from Models.base import Base
from DatabaseSqlAlchemy.sql_alchemy_category_repository import SqlAlchemyCategoryRepository
from DatabaseSqlAlchemy.sql_alchemy_event_repository import SqlAlchemyEventRepository
from DatabaseSqlAlchemy.sql_alchemy_user_credentials_repository import SqlAlchemyUserCredentialsRepository
from Controllers.category_controller import CategoryController
from Controllers.event_controller import EventController
from Controllers.auth_controller import AuthController
from Services.google_calendar_service import GoogleCalendarService
from Services.sync_mediator import SyncMediator

DB_PATH = "demo_test.db"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CREDENTIALS_PATH = os.path.join(BASE_DIR, "Secrets", "credentials.json")


def run_demo():
    print("=" * 60)
    print("🚀 START DEMO APLIKACJI Z SYNCHRONIZACJĄ (KROK 1)")
    print("=" * 60)

    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(" -> Usunięto starą bazę demo_test.db")

    engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    cat_repo = SqlAlchemyCategoryRepository(session)
    ev_repo = SqlAlchemyEventRepository(session)
    cred_repo = SqlAlchemyUserCredentialsRepository(session)

    google_service = GoogleCalendarService(cred_repo, current_user_id=1, credentials_path=CREDENTIALS_PATH)

    auth_ctrl = AuthController(google_service, cred_repo, current_user_id=1)

    mediator = SyncMediator(google_service, ev_repo, cred_repo)

    event_ctrl = EventController(ev_repo, cat_repo, mediator)
    cat_ctrl = CategoryController(cat_repo, ev_repo)

    print("\n[1] Logowanie do Google Calendar...")
    if not auth_ctrl.is_logged_in():
        print(" -> Wymagane logowanie w przeglądarce!")
        auth_ctrl.login()
    else:
        print(f" -> Zalogowano jako: {auth_ctrl.get_connected_account_info()}")

    print("\n[2] Tworzenie kategorii lokalnie...")
    cat_work_id = cat_ctrl.create_category("Projekt PWR", "#d50000", True)

    print("\n[3] Dodawanie testowych zadań do bazy lokalnej...")
    now = datetime.now()

    ev1_id = event_ctrl.create_new_event(
        title="Napisać demo dla użytkownika",
        description="Demo pokazujące jak działa synchronizacja (dodane lokalnie)",
        category_id=cat_work_id,
        start_datetime=now,
        end_datetime=now + timedelta(hours=1),
        priority=True,
    )

    ev2_id = event_ctrl.create_new_event(
        title="Zadanie cykliczne - daily standup",
        description="Sprawdzamy jak działa RRULE z Google",
        category_id=cat_work_id,
        start_datetime=now + timedelta(days=1),
        end_datetime=now + timedelta(days=1, hours=1),
        rrule="FREQ=DAILY;COUNT=3",
    )

    print(" ✅ Zadania zapisane lokalnie w SQLite.")

    print("\n[4] WYWOŁANIE SYNCHRONIZACJI (Lokalna Baza -> Google Calendar)...")
    event_ctrl.trigger_manual_sync()
    print(" ✅ Zsynchronizowano pomyślnie!")

    print("\n[5] Stan bazy lokalnej po synchronizacji:")
    for ev_id in [ev1_id, ev2_id]:
        ev = event_ctrl.get_event_by_id(ev_id)
        print(f" -> ID: {ev.id} | Google ID: {ev.google_event_id} | Tytuł: {ev.title} | Ostatni Sync: {ev.updated_at}")

    print("\n" + "=" * 60)
    print("🏁 KROK 1 ZAKOŃCZONY!")
    print("Wejdź na calendar.google.com, zmodyfikuj nazwę/datę tych zadań lub dodaj nowe,")
    print("a następnie uruchom skrypt `demo_sync.py`!")
    print("=" * 60)

    session.close()


if __name__ == "__main__":
    run_demo()
