from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from Models.base import Base
from DatabaseSqlAlchemy.sql_alchemy_category_repository import SqlAlchemyCategoryRepository
from DatabaseSqlAlchemy.sql_alchemy_event_repository import SqlAlchemyEventRepository
from Controllers.category_controller import CategoryController
from Controllers.event_controller import EventController


def run_demo():
    print("=" * 60)
    print("🚀 START DEMO APLIKACJI (Z OBSŁUGĄ REGUŁ POWTARZANIA 1:1)")
    print("=" * 60)

    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    cat_repo = SqlAlchemyCategoryRepository(session)
    ev_repo = SqlAlchemyEventRepository(session)

    event_ctrl = EventController(ev_repo, cat_repo, None)
    cat_ctrl = CategoryController(cat_repo, ev_repo)

    print("\n[1] Tworzenie kategorii...")
    cat_work_id = cat_ctrl.create_category("Praca", "#e53935", True)
    cat_home_id = cat_ctrl.create_category("Dom", "#43a047", True)
    print(f" ✅ Dodano kategorię 'Praca' (ID: {cat_work_id})")
    print(f" ✅ Dodano kategorię 'Dom' (ID: {cat_home_id})")

    print("\n[2] Dodawanie wydarzeń do kategorii (w tym cyklicznych)...")
    now = datetime.now()

    ev1_id = event_ctrl.create_new_event(
        title="Wdrożenie nowej wersji",
        description="Pamiętać o backupie bazy!",
        category_id=cat_work_id,
        start_dt=now,
        end_dt=now + timedelta(hours=2),
        priority=True
    )

    # ev2 tworzymy od razu z regułą powtarzania co tydzień (rrule)
    ev2_id = event_ctrl.create_new_event(
        title="Spotkanie z zespołem",
        description="Omawianie nowych ficzerów",
        category_id=cat_work_id,
        start_dt=now + timedelta(days=1),
        end_dt=now + timedelta(days=1, hours=1),
        rrule="FREQ=WEEKLY"
    )

    ev3_id = event_ctrl.create_new_event(
        title="Wielkie sprzątanie",
        description="Kupić płyn do okien",
        category_id=cat_home_id
    )
    print(" ✅ Dodano 3 nowe wydarzenia (w tym jedno cykliczne).")

    print("\n[3] Pierwszy odczyt i weryfikacja danych:")
    for ev_id in [ev1_id, ev2_id, ev3_id]:
        ev = event_ctrl.get_event_by_id(ev_id)
        cat_name = ev.category.name if ev.category else "BRAK KATEGORII"
        priorytet = "🔥" if ev.is_high_priority else "  "
        status = "✅" if ev.is_completed else "❌"
        # Wyświetlamy regułę jeśli istnieje
        powtarzanie = f"🔁 [{ev.rrule_str}]" if ev.rrule_str else "      "
        print(f" -> {priorytet} {powtarzanie} [{cat_name}] {ev.title} (Status: {status})")

    print("\n[4] Wykonywanie podstawowych operacji na wydarzeniach...")
    print(" -> Zaznaczam 'Wielkie sprzątanie' jako ukończone.")
    event_ctrl.mark_completed(ev3_id)

    print(" -> Edytuję 'Spotkanie z zespołem' (zmiana tytułu i priorytetu).")
    event_ctrl.edit_event(ev2_id, {"title": "Spotkanie z zespołem (ONLINE)", "priority": True})

    print("\n[5] Zarządzanie regułami powtarzania (Relacja 1:1)...")
    print(" -> [DODAWANIE]: Dodaję regułę 'FREQ=YEARLY' do jednorazowego wydarzenia (Wdrożenie)...")
    event_ctrl.edit_event(ev1_id, {"rrule_str": "FREQ=YEARLY"})

    print(" -> [EDYCJA]: Zmieniam regułę 'Spotkania z zespołem' z WEEKLY na DAILY...")
    event_ctrl.edit_event(ev2_id, {"rrule_str": "FREQ=DAILY"})

    # Stan przejściowy - pokazujemy zmiany reguł
    print("\n    --- Stan reguł po dodaniu i edycji ---")
    for ev_id in [ev1_id, ev2_id]:
        ev = event_ctrl.get_event_by_id(ev_id)
        print(f"    -> {ev.title}: reguła = {ev.rrule_str}")

    print("\n -> [USUWANIE]: Całkowicie usuwam regułę z 'Spotkanie z zespołem' (ustawiam None)...")
    event_ctrl.edit_event(ev2_id, {"rrule_str": None})

    print("\n[6] Odczyt i weryfikacja po wszystkich modyfikacjach reguł:")
    for ev_id in [ev1_id, ev2_id, ev3_id]:
        ev = event_ctrl.get_event_by_id(ev_id)
        cat_name = ev.category.name if ev.category else "BRAK KATEGORII"
        priorytet = "🔥" if ev.is_high_priority else "  "
        status = "✅" if ev.is_completed else "❌"
        powtarzanie = f"🔁 [{ev.rrule_str}]" if ev.rrule_str else "      "
        print(f" -> {priorytet} {powtarzanie} [{cat_name}] {ev.title} (Status: {status})")

    print("\n[7] Testowanie usuwania kategorii (Cascade = False)...")
    print(f" -> Usuwam kategorię 'Praca' (ID: {cat_work_id}) bez usuwania jej zadań.")
    cat_ctrl.delete_category(cat_work_id, cascade=False)

    ev1_after_delete = event_ctrl.get_event_by_id(ev1_id)
    cat_name_after = ev1_after_delete.category.name if ev1_after_delete.category else "BRAK KATEGORII"
    print(f" -> Sprawdzam zadanie 'Wdrożenie nowej wersji'. Obecna kategoria: {cat_name_after}")

    print("\n[8] Końcowy podgląd bazy danych:")
    for ev_id in [ev1_id, ev2_id, ev3_id]:
        ev = event_ctrl.get_event_by_id(ev_id)
        cat_name = ev.category.name if ev.category else "BRAK KATEGORII"
        priorytet = "🔥" if ev.is_high_priority else "  "
        status = "✅" if ev.is_completed else "❌"
        powtarzanie = f"🔁 [{ev.rrule_str}]" if ev.rrule_str else "      "
        print(f" -> {priorytet} {powtarzanie} [{cat_name}] {ev.title} (Status: {status})")

    print("\n" + "=" * 60)
    print("🏁 DEMO ZAKOŃCZONE PEŁNYM SUKCESEM!")
    print("=" * 60)

    session.close()


if __name__ == "__main__":
    run_demo()