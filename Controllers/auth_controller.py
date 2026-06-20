from typing import Optional


class AuthController:
    def __init__(self, google_api_service: any, sync_repo: any):
        self._google_api = google_api_service
        self._sync_repo = sync_repo

    def login(self) -> bool:
        """
        Odpala proces logowania do Google (OAuth2).
        Zwraca True jeśli logowanie się powiodło, False jeśli użytkownik anulował.
        """
        pass

    def logout(self) -> None:
        """Wylogowuje użytkownika: usuwa tokeny z bazy oraz pliki sesji z dysku"""
        pass

    def is_logged_in(self) -> bool:
        """Sprawdza, czy aplikacja posiada ważne (lub możliwe do odświeżenia) konto Google"""
        pass

    def get_connected_account_info(self) -> Optional[str]:
        """Zwraca np. e-mail zalogowanego użytkownika, aby wyświetlić go w GUI (np. 'Zalogowano jako: user@gmail.com')"""
        pass