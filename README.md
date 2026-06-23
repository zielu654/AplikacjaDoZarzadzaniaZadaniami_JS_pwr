# Aplikacja do Zarządzania Zadaniami (Backend)

Ten projekt stanowi backend aplikacji do zarządzania zadaniami, umożliwiającej m.in. dodawanie zadań, ich cykliczne powtarzanie, kategoryzację oraz pełną, dwukierunkową synchronizację z Google Calendar.

## Główne funkcjonalności

- **Zarządzanie zadaniami:** Tworzenie, edycja, usuwanie (soft delete), oznaczanie jako ukończone.
- **Kategorie zadań:** Grupowanie zadań z przypisanymi kolorami.
- **Zadania cykliczne:** Wsparcie dla powtarzających się zadań (RRULE).
- **Synchronizacja z Google Calendar:** Dwukierunkowa synchronizacja z uwzględnieniem wzorca "Last Writer Wins" (LWW).
- **Architektura Czysta:** Podział na kontrolery, serwisy, DTO, modele i repozytoria bazy danych.

## Wymagania i zależności

Aby uruchomić aplikację, wymagany jest Python (najlepiej w wersji 3.10+). Główne pakiety, których używa projekt to:

- `SQLAlchemy` - jako ORM do komunikacji z bazą danych SQLite.
- `google-api-python-client` - do interakcji z API Google Calendar.
- `google-auth-oauthlib` - do obsługi uwierzytelniania OAuth 2.0 (logowanie użytkownika do Google).
- `pytest` - do uruchamiania testów jednostkowych (w folderze `UnitTests`).

Zalecane jest stworzenie i uruchomienie wirtualnego środowiska (np. `.venv`), a następnie instalacja powyższych pakietów (np. `pip install sqlalchemy google-api-python-client google-auth-httplib2 google-auth-oauthlib pytest`).

## Struktura Projektu

- `/Core/` - Jądro aplikacji. Zawiera abstrakcyjne interfejsy repozytoriów i serwisów (zgodnie z Dependency Inversion Principle) oraz ogólne wyjątki domenowe.
- `/Controllers/` - Kontrolery zarządzające przepływem logiki biznesowej, integrujące logikę synchronizacji i dostęp do bazy (`auth_controller.py`, `event_controller.py`).
- `/DatabaseSqlAlchemy/` - Warstwa dostępu do danych (Repozytoria). Zawiera implementacje interfejsów z warstwy Core oparte o bazę SQLite (ORM).
- `/DTO/` - Data Transfer Objects. Obiekty służące do bezpiecznego przesyłania danych między warstwami bez ujawniania pełnych modeli bazy danych.
- `/Models/` - Definicje modeli bazy danych (SQLAlchemy), takie jak `Event`, `Category`, `SyncMetadata`, `RecurrenceRule`, itd.
- `/Services/` - Usługi biznesowe. Główne to `google_calendar_service.py` do komunikacji z Google oraz `sync_mediator.py` zarządzający synchronizacją.
- `/Secrets/` - Folder przeznaczony na pliki dostępowe API. Musisz tu umieścić pobrany z Google Cloud plik `credentials.json`.
- `/UnitTests/` - Zestawy testów jednostkowych weryfikujących logikę biznesową.
- `/Demos/` - Skrypty pokazowe, ilustrujące użycie poszczególnych komponentów (np. `demo_full_app.py`, `demo_sync.py`).

## Uruchomienie

### 1. Konfiguracja API Google Calendar
Aby używać synchronizacji:
1. Przejdź do Google Cloud Console.
2. Utwórz projekt i włącz `Google Calendar API`.
3. Wygeneruj dane logowania typu "Desktop app" (OAuth 2.0 Client IDs).
4. Pobierz plik JSON, nazwij go `credentials.json` i umieść w folderze `Secrets/`.

### 2. Działanie Aplikacji
Aplikacja została napisana z naciskiem na demonstracyjne użycie z poziomu kodu:

Możesz wywołać kompleksowy pokaz logiki dodając zadania, a następnie wykonując pełną synchronizację z Google przy użyciu pliku demonstracyjnego:
```bash
python Demos/demo_full_app.py
```
*Uwaga: Przy pierwszym uruchomieniu zostaniesz poproszony o zalogowanie się w przeglądarce i udzielenie dostępu do swojego Kalendarza Google.*

Aby uruchomić jedynie proces pobierania zmian i rozwiązywania konfliktów (tzw. dwukierunkową synchronizację po tym, jak aplikacja już powstała):
```bash
python Demos/demo_sync.py
```

### 3. Uruchamianie Testów
Aplikacja jest dokładnie przetestowana. Z głównego folderu uruchom testy za pomocą komendy:
```bash
python -m pytest UnitTests
```

### 4. Github
https://github.com/zielu654/AplikacjaDoZarzadzaniaZadaniami_JS_pwr
```
