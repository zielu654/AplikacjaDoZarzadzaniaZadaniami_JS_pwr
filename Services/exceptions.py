class GoogleCalendarError(Exception):
    """Główna klasa błędu dla komunikacji z Google Calendar."""
    pass

class GoogleEventNotFoundError(GoogleCalendarError):
    """Rzucany, gdy próbujemy zaktualizować/usunąć wydarzenie, którego już nie ma w Google."""
    pass

class GoogleAuthError(GoogleCalendarError):
    """Rzucany, gdy brakuje autoryzacji lub token jest nieważny."""
    pass