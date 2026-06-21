from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from Models.base import Base
from DatabaseSqlAlchemy.sql_alchemy_category_repository import SqlAlchemyCategoryRepository
from DatabaseSqlAlchemy.sql_alchemy_event_repository import SqlAlchemyEventRepository
from Controllers.category_controller import CategoryController
from Controllers.event_controller import EventController


def run_demo():
    print("=" * 50)
    print("🚀 START DEMO APLIKACJI")
    print("=" * 50)

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

    print("\n[2] Dodawanie wydarzeń do kategorii...")
    now = datetime.now()

    ev1_id = event_ctrl.create_new_event(
        title="Wdrożenie nowej wersji",
        description="Pamiętać o backupie bazy!",
        category_id=cat_work_id,
        start_dt=now,
        end_dt=now + timedelta(hours=2),
        priority=True
    )

    ev2_id = event_ctrl.create_new_event(
        title="Spotkanie z zespołem",
        description="Omawianie nowych ficzerów",
        category_id=cat_work_id,
        start_dt=now + timedelta(days=1),
        end_dt=now + timedelta(days=1, hours=1)
    )

    ev3_id = event_ctrl.create_new_event(
        title="Wielkie sprzątanie",
        description="Kupić płyn do okien",
        category_id=cat_home_id
    )
    print(" ✅ Dodano 3 nowe wydarzenia.")

    print("\n[3] Odczyt i weryfikacja podpięcia kategorii:")
    for ev_id in [ev1_id, ev2_id, ev3_id]:
        ev = event_ctrl.get_event_by_id(ev_id)
        cat_name = ev.category.name if ev.category else "BRAK KATEGORII"
        priorytet = "🔥" if ev.is_high_priority else "  "
        status = "✅" if ev.is_completed else "❌"
        print(f" -> {priorytet} [{cat_name}] {ev.title} (Ukończone: {status})")

    print("\n[4] Wykonywanie operacji na wydarzeniach...")
    print(" -> Zaznaczam 'Wielkie sprzątanie' jako ukończone.")
    event_ctrl.mark_completed(ev3_id)

    print(" -> Edytuję 'Spotkanie z zespołem' (zmiana tytułu i priorytetu).")
    event_ctrl.edit_event(ev2_id, {"title": "Spotkanie z zespołem (ONLINE)", "priority": True})

    ev2 = event_ctrl.get_event_by_id(ev2_id)
    ev3 = event_ctrl.get_event_by_id(ev3_id)
    print(f"    Wynik edycji: '{ev2.title}', wysoki priorytet: {ev2.is_high_priority}")
    print(f"    Wynik ukończenia: '{ev3.title}', status: {'✅' if ev3.is_completed else '❌'}")

    print("\n[5] Odczyt i weryfikacja podpięcia kategorii:")
    for ev_id in [ev1_id, ev2_id, ev3_id]:
        ev = event_ctrl.get_event_by_id(ev_id)
        cat_name = ev.category.name if ev.category else "BRAK KATEGORII"
        priorytet = "🔥" if ev.is_high_priority else "  "
        status = "✅" if ev.is_completed else "❌"
        print(f" -> {priorytet} [{cat_name}] {ev.title} (Ukończone: {status})")

    print("\n[6] Testowanie usuwania kategorii (Cascade = False)...")
    print(f" -> Usuwam kategorię 'Praca' (ID: {cat_work_id}) bez usuwania jej zadań.")
    cat_ctrl.delete_category(cat_work_id, cascade=False)

    ev1_after_delete = event_ctrl.get_event_by_id(ev1_id)
    cat_name_after = ev1_after_delete.category.name if ev1_after_delete.category else "BRAK KATEGORII"
    print(f" -> Sprawdzam zadanie 'Wdrożenie nowej wersji'. Obecna kategoria: {cat_name_after}")

    print("\n[7] Odczyt i weryfikacja podpięcia kategorii:")
    for ev_id in [ev1_id, ev2_id, ev3_id]:
        ev = event_ctrl.get_event_by_id(ev_id)
        cat_name = ev.category.name if ev.category else "BRAK KATEGORII"
        priorytet = "🔥" if ev.is_high_priority else "  "
        status = "✅" if ev.is_completed else "❌"
        print(f" -> {priorytet} [{cat_name}] {ev.title} (Ukończone: {status})")
    print("\n" + "=" * 50)
    print("🏁 DEMO ZAKOŃCZONE SUKCESEM!")
    print("=" * 50)

    session.close()


if __name__ == "__main__":
    run_demo()