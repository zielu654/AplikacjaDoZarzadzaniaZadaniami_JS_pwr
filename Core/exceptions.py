from functools import wraps
from sqlalchemy.exc import SQLAlchemyError

class RepositoryError(Exception):
    pass

class RecordNotFoundError(RepositoryError):
    pass

class RecordAlreadyExistsError(RepositoryError):
    pass

class GoogleCalendarError(Exception):
    pass

class GoogleEventNotFoundError(GoogleCalendarError):
    pass

class GoogleAuthError(GoogleCalendarError):
    pass

class AppError(Exception):
    pass

class ValidationError(AppError):
    pass

class EmptyFieldError(ValidationError):
    pass

class InvalidDateRangeError(ValidationError):
    pass

class ResourceNotFoundError(AppError):
    pass

class AuthenticationError(AppError):
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