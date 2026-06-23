import os
from datetime import timedelta, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from Controllers import EventController, AuthController
from DatabaseSqlAlchemy.sql_alchemy_category_repository import SqlAlchemyCategoryRepository, SqlAlchemyEventRepository, SqlAlchemyUserCredentialsRepository
from Services.google_calendar_service import GoogleCalendarService, SyncMediator

DB_PATH = "demo_test.db"


def run_sync_demo():
    print("=" * 60)
    print("🔄 START DEMO: TYLKO SYNCHRONIZACJA (KROK 2)")
    print("=" * 60)

    if not os.path.exists(DB_PATH):
        print(f"Błąd: Nie znaleziono bazy {DB_PATH}. Najpierw uruchom `demo_full_app.py`!")
        return

    engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()

    cat_repo = SqlAlchemyCategoryRepository(session)
    ev_repo = SqlAlchemyEventRepository(session)
    cred_repo = SqlAlchemyUserCredentialsRepository(session)

    google_service = GoogleCalendarService(cred_repo, current_user_id=1, credentials_path="../Secrets/credentials.json")
    auth_ctrl = AuthController(google_service, cred_repo, current_user_id=1)

    mediator = SyncMediator(google_service, ev_repo, cred_repo)
    event_ctrl = EventController(ev_repo, cat_repo, mediator)

    if not auth_ctrl.is_logged_in():
        print(" -> Użytkownik nie jest zalogowany (zrób to w pierwszym skrypcie).")
        return
    else:
        print(f" -> Pomyślnie odzyskano sesję Google dla: {auth_ctrl.get_connected_account_info()}")
    now = datetime.now()

    event_ctrl.create_new_event(
        title="Test",
        description="Testowo dodajemy do aplikacji i synchronizacja z google",
        category_id=None,
        start_dt=now,
        end_dt=now + timedelta(hours=3),
    )
    event_ctrl.trigger_manual_sync()


if __name__ == "__main__":
    run_sync_demo()
