import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from DTO.event_DTO import EventDTO
from DTO.user_credentials_DTO import UserCredentialsDTO
from DatabaseSqlAlchemy.sql_alchemy_user_credentials_repository import SqlAlchemyUserCredentialsRepository
from Models.sync_metadata import SyncMetadata
from DatabaseSqlAlchemy.sql_alchemy_event_repository import SqlAlchemyEventRepository
from Models.base import Base
from Models.event import Event
from Models.category import Category
from DatabaseSqlAlchemy.exceptions import RecordNotFoundError
from Models.user_credentials import UserCredentials


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

    dto = EventDTO(id=0, title="Nowe zadanie", description=None, start_datetime=None,
                   end_datetime=None, is_high_priority=False, is_completed=False, category=None)

    new_id = repo.add(dto)

    assert isinstance(new_id, int)
    assert new_id > 0


def test_add_event_saves_to_database(db_session):
    repo = SqlAlchemyEventRepository(db_session)
    dto = EventDTO(id=0, title="Testowy zapis", description=None, start_datetime=None,
                   end_datetime=None, is_high_priority=False, is_completed=False, category=None)

    new_id = repo.add(dto)

    saved_event = db_session.get(Event, new_id)
    assert saved_event is not None
    assert saved_event.title == "Testowy zapis"
    assert saved_event.is_deleted is False


def test_update_event_changes_data_and_updated_at(db_session):
    repo = SqlAlchemyEventRepository(db_session)

    dto = EventDTO(id=0, title="Stary tytuł", description=None, start_datetime=None,
                   end_datetime=None, is_high_priority=False, is_completed=False, category=None)
    event_id = repo.add(dto)

    past_time = datetime.now() - timedelta(days=1)
    db_model = db_session.get(Event, event_id)
    db_model.updated_at = past_time
    db_session.commit()

    event_to_update = repo.get_by_id(event_id)
    event_to_update.title = "Zaktualizowany tytuł"
    repo.update(event_to_update)

    updated_db_model = db_session.get(Event, event_id)
    assert updated_db_model.title == "Zaktualizowany tytuł"
    assert updated_db_model.updated_at > past_time


def test_delete_performs_soft_delete(db_session):
    repo = SqlAlchemyEventRepository(db_session)
    dto = EventDTO(id=0, title="Do usunięcia", description=None, start_datetime=None,
                   end_datetime=None, is_high_priority=False, is_completed=False, category=None)
    event_id = repo.add(dto)

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

    dto1 = EventDTO(id=0, title="Aktywne 1", description=None, start_datetime=None,
                    end_datetime=None, is_high_priority=False, is_completed=False, category=None)
    dto2 = EventDTO(id=0, title="Aktywne 2", description=None, start_datetime=None,
                    end_datetime=None, is_high_priority=False, is_completed=False, category=None)
    repo.add(dto1)
    repo.add(dto2)

    deleted_db_event = Event(title="Usunięte 1", is_deleted=True, updated_at=datetime.now())
    db_session.add(deleted_db_event)
    db_session.commit()

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

    dto = EventDTO(id=0, title="Event 1", description=None, start_datetime=None,
                   end_datetime=None, is_high_priority=False, is_completed=False, category=None)
    repo.add(dto)

    deleted_db_event = Event(title="Event 2", is_deleted=True, updated_at=datetime.now())
    db_session.add(deleted_db_event)
    db_session.commit()

    results = repo.get_dirty_records()

    assert len(results) == 2
    titles = [e.title for e in results]
    assert "Event 1" in titles
    assert "Event 2" in titles


def test_get_dirty_records_returns_only_modified_after_sync(db_session):
    repo = SqlAlchemyEventRepository(db_session)

    now = datetime.now()
    sync_date = now - timedelta(days=2)
    old_date = sync_date - timedelta(days=1)

    old_event_dto = EventDTO(
        id=0,
        title="Stary",
        description=None,
        start_datetime=None,
        end_datetime=None,
        is_high_priority=False,
        is_completed=False,
        category=None
    )
    old_id = repo.add(old_event_dto)

    old_db_model = db_session.get(Event, old_id)
    old_db_model.updated_at = old_date
    db_session.commit()

    sync_meta = SyncMetadata(event_id=old_id, last_synced=sync_date)
    db_session.add(sync_meta)
    db_session.commit()

    new_event_dto = EventDTO(
        id=0,
        title="Nowy",
        description=None,
        start_datetime=None,
        end_datetime=None,
        is_high_priority=False,
        is_completed=False,
        category=None
    )
    repo.add(new_event_dto)

    results = repo.get_dirty_records()

    assert len(results) == 1
    assert results[0].title == "Nowy"

    assert isinstance(results[0], EventDTO)

def test_save_new_user_credentials_saves_to_db(db_session):
    repo = SqlAlchemyUserCredentialsRepository(db_session)
    dto = UserCredentialsDTO(user_id=1, token_data='{"token": "xyz"}')

    repo.save(dto)

    saved = db_session.query(UserCredentials).filter(UserCredentials.user_id == 1).first()
    assert saved is not None
    assert saved.token_data == '{"token": "xyz"}'

def test_save_existing_user_credentials_updates_it(db_session):
    repo = SqlAlchemyUserCredentialsRepository(db_session)
    dto1 = UserCredentialsDTO(user_id=1, token_data='{"token": "stary"}')
    repo.save(dto1)

    dto2 = UserCredentialsDTO(user_id=1, token_data='{"token": "nowy"}')
    repo.save(dto2)

    all_creds = db_session.query(UserCredentials).all()
    assert len(all_creds) == 1
    assert all_creds[0].token_data == '{"token": "nowy"}'