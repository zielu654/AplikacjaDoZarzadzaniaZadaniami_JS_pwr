import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from Models.base import Base
from DatabaseSqlAlchemy.sql_alchemy_category_repository import SqlAlchemyCategoryRepository
from DatabaseSqlAlchemy.sql_alchemy_event_repository import SqlAlchemyEventRepository
from DatabaseSqlAlchemy.sql_alchemy_user_credentials_repository import SqlAlchemyUserCredentialsRepository
from Controllers.event_controller import EventController
from Controllers.auth_controller import AuthController
from Services.google_calendar_service import GoogleCalendarService
from Services.sync_mediator import SyncMediator

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

    mediator = SyncMediator(google_service)
    event_ctrl = EventController(ev_repo, cat_repo, mediator)
    mediator.set_controllers(event_ctrl, auth_ctrl)

    if not auth_ctrl.is_logged_in():
        print(" -> Użytkownik nie jest zalogowany (zrób to w pierwszym skrypcie).")
        return
    else:
        print(f" -> Pomyślnie odzyskano sesję Google dla: {auth_ctrl.get_connected_account_info()}")

    print("\n[1] Stan lokalny PRZED synchronizacją:")
    events_before = ev_repo.get_all()
    if not events_before:
        print("   Brak wydarzeń lokalnych.")
    for ev in events_before:
        print(f"   -> [{ev.id}] {ev.title} Godzina {ev.start_datetime} (Zaktualizowano: {ev.updated_at})")

    print("\n[2] WYWOŁANIE SYNCHRONIZACJI (Pobieranie zmian z Google)...")
    event_ctrl.trigger_manual_sync()
    print(" ✅ Synchronizacja wykonana pomyślnie!")

    print("\n[3] Stan lokalny PO synchronizacji:")
    events_after = ev_repo.get_all()

    for ev in events_after:
        title = ev.title
        status = "✅ ZROBIONE" if ev.is_completed else "🕒 DO ZROBIENIA"
        print(
            f"   -> [{ev.id}] {title} | Status: {status} | Godzina {ev.start_datetime} | Ostatni Sync: {ev.updated_at}"
        )

    print("\n" + "=" * 60)
    print("🏁 KROK 2 ZAKOŃCZONY!")
    print("Jeśli zmieniłeś coś na calendar.google.com, powyższa lista powinna to odzwierciedlać.")
    print("=" * 60)

    session.close()


if __name__ == "__main__":
    run_sync_demo()
