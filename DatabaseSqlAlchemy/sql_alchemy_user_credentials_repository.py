from datetime import datetime, timezone
from typing import Optional

from DTO.user_credentialsDTO import UserCredentialsDTO
from Models.user_credentials import UserCredentials
from Core.interfaces import IUserCredentialsRepository
from Core.exceptions import db_error_handler, RecordNotFoundError


class SqlAlchemyUserCredentialsRepository(IUserCredentialsRepository):
    def __init__(self, session):
        self.session = session

    @db_error_handler
    def get_by_user_id(self, user_id: int) -> Optional[UserCredentialsDTO]:
        creds = self.session.query(UserCredentials).filter(UserCredentials.user_id == user_id).first()

        if not creds:
            return None

        return self._map_to_dto(creds)

    @db_error_handler
    def save(self, credentials_dto: UserCredentialsDTO) -> None:
        existing_creds = (
            self.session.query(UserCredentials).filter(UserCredentials.user_id == credentials_dto.user_id).first()
        )

        if existing_creds:
            existing_creds.token_data = credentials_dto.token_data
            if credentials_dto.last_synced is not None:
                existing_creds.last_synced = credentials_dto.last_synced
            existing_creds.updated_at = datetime.now(timezone.utc)
        else:
            new_creds = UserCredentials(
                user_id=credentials_dto.user_id,
                token_data=credentials_dto.token_data,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                last_synced=credentials_dto.last_synced,
            )
            self.session.add(new_creds)

        self.session.commit()

    @db_error_handler
    def update_last_synced(self, user_id: int, sync_time: datetime) -> None:
        creds = self.session.query(UserCredentials).filter(UserCredentials.user_id == user_id).first()

        if not creds:
            raise RecordNotFoundError(f"Nie znaleziono poświadczeń dla użytkownika {user_id}")

        creds.last_synced = sync_time
        self.session.commit()

    @db_error_handler
    def delete_for_user(self, user_id: int) -> None:
        creds = self.session.query(UserCredentials).filter(UserCredentials.user_id == user_id).first()

        if not creds:
            raise RecordNotFoundError(f"Nie znaleziono danych uwierzytelniających dla użytkownika {user_id}")

        self.session.delete(creds)
        self.session.commit()

    def _map_to_dto(self, creds: UserCredentials) -> UserCredentialsDTO:
        return UserCredentialsDTO(user_id=creds.user_id, token_data=creds.token_data, last_synced=creds.last_synced)
