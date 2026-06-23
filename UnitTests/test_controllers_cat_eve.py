import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from Models import Base
from DatabaseSqlAlchemy import SqlAlchemyCategoryRepository, SqlAlchemyEventRepository
from Controllers import CategoryController, EventController
from Core import ResourceNotFoundError, InvalidDateRangeError, ValidationError


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def repos(db_session):
    cat_repo = SqlAlchemyCategoryRepository(db_session)
    ev_repo = SqlAlchemyEventRepository(db_session)
    return cat_repo, ev_repo


@pytest.fixture
def controllers(repos):
    cat_repo, ev_repo = repos
    event_ctrl = EventController(ev_repo, cat_repo, None)
    cat_ctrl = CategoryController(cat_repo, ev_repo)
    return cat_ctrl, event_ctrl


def test_create_category_success(controllers):
    cat_ctrl, _ = controllers

    cat_id = cat_ctrl.create_category("Praca", "#7986cb", True)

    assert cat_id > 0
    saved_cat = cat_ctrl.get_category_by_id(cat_id)
    assert saved_cat.name == "Praca"
    assert saved_cat.color.hex_code == "#7986cb"


def test_edit_category_updates_fields(controllers):
    cat_ctrl, _ = controllers
    cat_id = cat_ctrl.create_category("Stara", "#7986cb")

    cat_ctrl.edit_category(cat_id, {"name": "Nowa", "color_hex": "#8e24aa"})

    updated = cat_ctrl.get_category_by_id(cat_id)
    assert updated.name == "Nowa"
    assert updated.color.hex_code == "#8e24aa"


def test_delete_category_cascade_false_removes_link(controllers):
    cat_ctrl, event_ctrl = controllers

    cat_id = cat_ctrl.create_category("Tymczasowa", "#7986cb")
    ev_id = event_ctrl.create_new_event("Zadanie powiązane", "Opis", cat_id)

    cat_ctrl.delete_category(cat_id, cascade=False)

    assert cat_ctrl.get_category_by_id(cat_id) is None
    event = event_ctrl.get_event_by_id(ev_id)
    assert event.category is None


def test_delete_category_cascade_true_deletes_events(controllers):
    cat_ctrl, event_ctrl = controllers

    cat_id = cat_ctrl.create_category("Do skasowania", "#7986cb")
    ev_id = event_ctrl.create_new_event("Zadanie usunięte z kategorią", "Opis", cat_id)
    print(event_ctrl.get_event_by_id(ev_id))

    cat_ctrl.delete_category(cat_id, cascade=True)

    assert cat_ctrl.get_category_by_id(cat_id) is None
    assert event_ctrl.get_event_by_id(ev_id) is None


def test_create_event_success(controllers):
    _, event_ctrl = controllers
    now = datetime.now()

    ev_id = event_ctrl.create_new_event(
        title="  Nowe Zadanie  ",
        description="Brak",
        category_id=None,
        start_datetime=now,
        end_datetime=now + timedelta(hours=1),
        priority=True,
    )

    event = event_ctrl.get_event_by_id(ev_id)
    assert event.title == "Nowe Zadanie"
    assert event.is_high_priority is True


def test_create_event_invalid_dates_raises_error(controllers):
    _, event_ctrl = controllers
    now = datetime.now()

    with pytest.raises(InvalidDateRangeError):
        event_ctrl.create_new_event(
            title="Błąd dat",
            description="",
            category_id=None,
            start_datetime=now,
            end_datetime=now - timedelta(hours=1),  # Data zakończenia przed rozpoczęciem
        )


def test_edit_event_updates_partial_fields(controllers):
    _, event_ctrl = controllers
    ev_id = event_ctrl.create_new_event("Stare zadanie", "Opis", None)

    event_ctrl.edit_event(ev_id, {"title": "Nowy tytuł", "priority": True})

    updated = event_ctrl.get_event_by_id(ev_id)
    assert updated.title == "Nowy tytuł"
    assert updated.is_high_priority is True
    assert updated.description == "Opis"  # Reszta pozostaje bez zmian


def test_mark_completed_changes_status(controllers):
    _, event_ctrl = controllers
    ev_id = event_ctrl.create_new_event("Zadanie", "Opis", None)

    event_ctrl.mark_completed(ev_id)

    event = event_ctrl.get_event_by_id(ev_id)
    assert event.is_completed is True


def test_create_event_with_recurrence_rule(controllers):
    _, event_ctrl = controllers

    ev_id = event_ctrl.create_new_event(
        title="Codzienne spotkanie", description="Daily standup", category_id=None, rrule="FREQ=DAILY"
    )

    event = event_ctrl.get_event_by_id(ev_id)
    assert event.rrule_str == "FREQ=DAILY"


def test_edit_event_adds_recurrence_rule_to_single_event(controllers):
    _, event_ctrl = controllers
    ev_id = event_ctrl.create_new_event("Zadanie jednorazowe", "Opis", None)

    event_ctrl.edit_event(ev_id, {"rrule_string": "FREQ=YEARLY"})

    updated = event_ctrl.get_event_by_id(ev_id)
    assert updated.rrule_str == "FREQ=YEARLY"


def test_edit_event_updates_existing_recurrence_rule(controllers):
    _, event_ctrl = controllers
    ev_id = event_ctrl.create_new_event("Zadanie", "Opis", None, rrule="FREQ=WEEKLY")

    event_ctrl.edit_event(ev_id, {"rrule_string": "FREQ=MONTHLY"})

    updated = event_ctrl.get_event_by_id(ev_id)
    assert updated.rrule_str == "FREQ=MONTHLY"


def test_edit_event_removes_recurrence_rule_completely(controllers):
    _, event_ctrl = controllers
    ev_id = event_ctrl.create_new_event("Zadanie cykliczne", "Opis", None, rrule="FREQ=DAILY")

    event_ctrl.edit_event(ev_id, {"rrule_string": None})

    updated = event_ctrl.get_event_by_id(ev_id)
    assert updated.rrule_str is None


def test_edit_nonexistent_event_raises_not_found(controllers):
    _, event_ctrl = controllers
    with pytest.raises(ResourceNotFoundError):
        event_ctrl.edit_event(9999, {"title": "Nowy tytuł"})


def test_mark_completed_nonexistent_event_raises_not_found(controllers):
    _, event_ctrl = controllers
    with pytest.raises(ResourceNotFoundError):
        event_ctrl.mark_completed(9999)


def test_create_event_with_fake_category_raises_not_found(controllers):
    _, event_ctrl = controllers
    with pytest.raises(ResourceNotFoundError):
        event_ctrl.create_new_event("Tytuł", "Opis", category_id=9999)


def test_create_category_with_invalid_color_raises_validation_error(controllers):
    cat_ctrl, _ = controllers

    with pytest.raises(ValidationError) as excinfo:
        cat_ctrl.create_category("Zła kategoria", "#000000")

    assert "nie pasuje do żadnego z dozwolonych kolorów" in str(excinfo.value)


def test_delete_event_removes_it_from_active_queries(controllers):
    _, event_ctrl = controllers
    ev_id = event_ctrl.create_new_event("Do usunięcia", "Opis", None)

    event_ctrl.delete_event(ev_id)

    assert event_ctrl.get_event_by_id(ev_id) is None


def test_edit_category_with_invalid_color_raises_validation_error(controllers):
    cat_ctrl, _ = controllers

    cat_id = cat_ctrl.create_category("Testowa", "#7986cb")  # Poprawny lavender

    with pytest.raises(ValidationError):
        cat_ctrl.edit_category(cat_id, {"color_hex": "#111111"})

    with pytest.raises(ValidationError):
        cat_ctrl.edit_category(cat_id, {"color_name": "KolorSeledynowy"})
