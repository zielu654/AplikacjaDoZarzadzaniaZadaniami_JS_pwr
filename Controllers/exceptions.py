class AppError(Exception):
    """Główny wyjątek aplikacji. Wszystkie inne wyjątki kontrolerów po nim dziedziczą."""
    pass

class ValidationError(AppError):
    """Ogólny błąd walidacji danych."""
    pass

class EmptyFieldError(ValidationError):
    """Rzucany, gdy wymagane pole (tytuł zadania, nazwa kategorii) jest puste."""
    pass

class InvalidDateRangeError(ValidationError):
    """Rzucany, gdy daty są nielogiczne (np. koniec przed początkiem)."""
    pass

class ResourceNotFoundError(AppError):
    """Rzucany, gdy próbujemy odwołać się do czegoś, co nie istnieje"""
    pass

class AuthenticationError(AppError):
    """Rzucany, gdy logowanie/autoryzacja (np. do Google) się nie powiedzie."""
    pass