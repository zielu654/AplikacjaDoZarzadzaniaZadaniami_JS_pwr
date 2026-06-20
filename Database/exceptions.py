from functools import wraps
from sqlalchemy.exc import SQLAlchemyError

class RepositoryError(Exception):
    """Główna klasa błędu dla wszystkich problemów z bazą."""
    pass

class RecordNotFoundError(RepositoryError):
    """Rzucany, gdy szukany rekord (Event, Category itp.) nie istnieje."""
    pass

class RecordAlreadyExistsError(RepositoryError):
    """Rzucany, gdy próbujemy dodać rekord, który narusza unikalność (np. duplikat nazwy)."""
    pass


def db_error_handler(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except SQLAlchemyError as e:
            self.session.rollback()
            raise RepositoryError(f"Błąd bazy danych w metodzie '{func.__name__}': {str(e)}")

    return wrapper