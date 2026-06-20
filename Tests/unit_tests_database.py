import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from Models.sync_metadata import SyncMetadata
from Database.sql_alchemy_event_repository import SqlAlchemyEventRepository
from Models.base import Base
from Models.event import Event
from Database.exceptions import RecordNotFoundError


@pytest.fixture
def db_session():
    """Tworzy czystą bazę w pamięci RAM przed każdym testem."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_add_event_success_returns_id(db_session):
    repo = SqlAlchemyEventRepository(db_session)
    now_time = datetime.now()
    event = Event(title="Nowe zadanie", is_deleted=False, updated_at=now_time)

    new_id = repo.add(event)

    assert isinstance(new_id, int)
    assert new_id > 0
    assert event.id == new_id


def test_add_event_saves_to_database(db_session):
    repo = SqlAlchemyEventRepository(db_session)
    event = Event(title="Testowy zapis", is_deleted=False, updated_at=datetime.now())

    repo.add(event)

    saved_event = db_session.get(Event, event.id)
    assert saved_event is not None
    assert saved_event.title == "Testowy zapis"


def test_update_event_changes_data_and_updated_at(db_session):
    repo = SqlAlchemyEventRepository(db_session)

    past_time = datetime.now() - timedelta(days=1)
    event = Event(title="Stary tytuł", is_deleted=False, updated_at=past_time)
    repo.add(event)

    event.title = "Zaktualizowany tytuł"
    repo.update(event)

    updated_event = db_session.get(Event, event.id)
    assert updated_event.title == "Zaktualizowany tytuł"
    assert updated_event.updated_at > past_time


def test_delete_performs_soft_delete(db_session):
    repo = SqlAlchemyEventRepository(db_session)
    event = Event(title="Do usunięcia", is_deleted=False, updated_at=datetime.now())
    event_id = repo.add(event)

    repo.delete(event_id)

    deleted_event = db_session.get(Event, event_id)
    assert deleted_event is not None
    assert deleted_event.is_deleted is True


def test_delete_raises_record_not_found(db_session):
    repo = SqlAlchemyEventRepository(db_session)

    with pytest.raises(RecordNotFoundError):
        repo.delete(9999)



def test_get_all_returns_only_active_events(db_session):
    repo = SqlAlchemyEventRepository(db_session)
    event1 = Event(title="Aktywne 1", is_deleted=False, updated_at=datetime.now())
    event2 = Event(title="Usunięte 1", is_deleted=True, updated_at=datetime.now())
    event3 = Event(title="Aktywne 2", is_deleted=False, updated_at=datetime.now())

    repo.add(event1)
    repo.add(event2)
    repo.add(event3)

    results = repo.get_all()

    assert len(results) == 2
    titles = [e.title for e in results]
    assert "Aktywne 1" in titles
    assert "Aktywne 2" in titles
    assert "Usunięte 1" not in titles


def test_get_all_empty_database_returns_empty_list(db_session):
    repo = SqlAlchemyEventRepository(db_session)

    results = repo.get_all()

    assert results == []


def test_get_dirty_records_without_sync_metadata_returns_all(db_session):
    repo = SqlAlchemyEventRepository(db_session)
    event1 = Event(title="Event 1", is_deleted=False, updated_at=datetime.now())
    event2 = Event(title="Event 2", is_deleted=True, updated_at=datetime.now())
    repo.add(event1)
    repo.add(event2)

    results = repo.get_dirty_records()

    assert len(results) == 2


def test_get_dirty_records_returns_only_modified_after_sync(db_session):
    repo = SqlAlchemyEventRepository(db_session)

    sync_date = datetime.now() - timedelta(days=2)
    old_event = Event(title="Stary", is_deleted=False)
    repo.add(old_event)
    old_event.updated_at = sync_date - timedelta(days=1)
    db_session.commit()

    sync_meta = SyncMetadata(old_event.id, last_synced=sync_date)
    db_session.add(sync_meta)
    db_session.commit()

    new_event = Event(title="Nowy", is_deleted=False)

    repo.add(new_event)

    results = repo.get_dirty_records()

    assert len(results) == 1
    assert results[0].title == "Nowy"