# Dokumentacja Techniczna i Architektoniczna – Backend Aplikacji do Zarządzania Zadaniami

Niniejszy dokument stanowi kompletny opis architektury, wzorców projektowych, struktur danych oraz algorytmów synchronizacji zastosowanych w warstwie backendowej aplikacji do zarządzania zadaniami. System oferuje pełną obsługę cyklu życia zadań (CRUD), zaawansowane filtrowanie, zarządzanie kategoriami z walidacją kolorystyczną oraz zaawansowaną, dwukierunkową synchronizację z API Kalendarza Google w oparciu o mechanizm **Last Writer Wins (LWW)** oraz strategię **Soft Delete**.

---

## 1. Architektura Systemu (Clean Architecture)

Aplikacja została zaprojektowana zgodnie z pryncypiami **Czystej Architektury (Clean Architecture)** oraz **Zasadą Odwrócenia Zależności (Dependency Inversion Principle - DIP)**. Kod został podzielony na odizolowane warstwy, gdzie warstwy wewnętrzne (logika biznesowa i domena) nie wiedzą o istnieniu warstw zewnętrznych (baza danych, integracje API).

### Warstwy i Przepływ Zależności

1. **Warstwa Core (Domena / Kontrakty):**
   - Stanowi serce aplikacji. Definiuje interfejsy (protokoły) oraz bazowe wyjątki biznesowe (`EmptyFieldError`, `ValidationError`, `InvalidDateRangeError`, `ResourceNotFoundError`).
   - Nie posiada zależności od żadnych zewnętrznych bibliotek (oprócz biblioteki standardowej Pythona).
2. **Warstwa DTO (Data Transfer Objects):**
   - Klasy pośredniczące w transferze danych pomiędzy bazą danych, usługami a kontrolerami. Zapobiegają one wyciekowi encji ORM (SQLAlchemy) do wyższych warstw, chroniąc integralność bazy danych.
3. **Warstwa Kontrolerów (Logika Aplikacyjna):**
   - Koordynuje przepływ danych, wykonuje walidację biznesową i realizuje scenariusze użycia. Kontrolery komunikują się z warstwą dostępu do danych wyłącznie poprzez interfejsy zdefiniowane w `Core`.
4. **Warstwa Usług (Services):**
   - Odpowiada za integrację z zewnętrznymi systemami (Google Calendar API) oraz orkiestrację procesów przekraczających granice pojedynczych encji (np. synchronizacja).
5. **Warstwa Infrastruktury (DatabaseSqlAlchemy):**
   - Szczegół implementacyjny systemu. Zawiera konkretne implementacje repozytoriów oparte na systemie SQLite oraz ORM SQLAlchemy.

---

## 2. Szczegółowy Opis Komponentów

### 2.1. Warstwa Core – Kontrakty i Protokoly (`interfaces.py`)

Zamiast klas abstrakcyjnych, w projekcie wykorzystano moduł `typing.Protocol` do realizacji typowania strukturalnego (duck-typing w sposób statyczny).

* **`IEventQuery`**: Interfejs typu *Query Object* (Płynne API). Umożliwia łańcuchowe budowanie zapytań filtrujących dla zadań:
    * `overdue()` – filtruje zadania nieukończone, których termin minął.
    * `high_priority()` / `low_priority()` – filtruje na podstawie priorytetu.
    * `by_category(category_id)` – filtruje zadania przypisane do konkretnej kategorii.
    * `for_date(target_date)` – filtruje zadania na dany dzień.
    * `sort_by(field_name, ascending)` – definiuje kryteria sortowania wyników.
    * `get_list()` – wykonuje zapytanie i zwraca listę obiektów `EventDTO`.
* **`IEventRepository`**: Odpowiada za utrwalanie obiektów `EventDTO`. Zawiera metodę `get_dirty_records()`, służącą do identyfikacji lokalnie zmodyfikowanych rekordów, które należy zsynchronizować.
* **`ICategoryRepository`**: Definiuje operacje CRUD dla kategorii zadań.
* **`IUserCredentialsRepository`**: Odpowiada za bezpieczny zapis, odczyt oraz aktualizację tokenów OAuth 2.0 użytkownika.

### 2.2. Warstwa Kontrolerów (Controllers)

#### `AuthController`
Odpowiada za cykl życia sesji uwierzytelniania w Google API.
* `login()`: Wywołuje proces uwierzytelniania i inicjalizuje obiekt usługi Google Calendar.
* `logout()`: Czyści instancję usługi w pamięci oraz całkowicie usuwa tokeny dostępowe z bazy danych w celu zabezpieczenia konta.
* `is_logged_in()`: Sprawdza ważność tokena (zarówno czy aktualny token sesji żyje, czy dostępny jest `refresh_token` do jego odnowienia).
* `get_connected_account_info()`: Bezpiecznie odpytuje Google o identyfikator kalendarza `primary` w celu weryfikacji tożsamości zalogowanego użytkownika.

#### `CategoryController`
Zarządza kategoriami zadań oraz mapowaniem ich atrybutów wizualnych na standardy Google Calendar.
* **Walidacja kolorów**: Podczas tworzenia kategorii, system pobiera kod HEX i konwertuje go metodą `CalendarColor.color_hex_to_callendarColor(color_hex)`. Jeśli kolor nie figuruje na liście predefiniowanych kolorów obsługiwanych przez interfejs kalendarza Google, zgłaszany jest wyjątek `ValidationError`.
* **Usuwanie kaskadowe**: Metoda `delete_category(category_id, cascade=True/False)` obsługuje dwa zachowania:
    * `cascade=True`: Wszystkie zadania przypisane do tej kategorii zostają automatycznie oznaczone jako usunięte (`delete`).
    * `cascade=False`: Zadania zachowują swój status, ale ich powiązanie z kategorią zostaje przerwane (`category_id = None`).

#### `EventController`
Główny punkt wejściowy dla operacji na zadaniach. Wykonuje ścisłą walidację (np. chronologia dat rozpoczęcia i zakończenia zadania). Zawiera wyspecjalizowane metody przeznaczone dla procesów synchronizacji, takie jak `sync_create_from_google()`, `sync_update_from_google()`, oraz `sync_update_metadata()`, która aktualizuje wyłącznie identyfikatory zewnętrzne oraz znaczniki czasu po udanej operacji eksportu do chmury.

### 2.3. Warstwa Infrastruktury (DatabaseSqlAlchemy)

Repozytoria realizują wzorzec izolacji dostępu do danych, dbając o czyszczenie i bezpieczeństwo transakcji. Wszystkie metody zapisu i odczytu są oplecione dekoratorem `@db_error_handler`, który przechwytuje wewnętrzne błędy bazy danych i mapuje je na czytelne wyjątki domenowe.

#### Wzorzec Soft Delete (Miękkie Usuwanie)
Zarówno zadania (`Event`), jak i kategorie (`Category`) nie są fizycznie usuwane z tabel bazy danych przy użyciu instrukcji `DELETE`. Zamiast tego:
1. Pole `is_deleted` przyjmuje wartość `True`.
2. Pole `updated_at` jest aktualizowane do bieżącej daty i godziny systemowej.
3. Obiekt `SqlAlchemyEventQuery` oraz metody `get_all()` automatycznie filtrują zapytania, dokładając warunek `is_deleted == False`.

*Dlaczego to kluczowe?* Dzięki zachowaniu rekordu z flagą `is_deleted` w bazie, proces synchronizacji jest w stanie wykryć, że dany obiekt istniał, ale został usunięty przez użytkownika lokalnie, co pozwala na wysłanie żądania usunięcia (HTTP DELETE) bezpośrednio do API Kalendarza Google podczas najbliższej synchronizacji.

#### Implementacja Query Object (`SqlAlchemyEventQuery`)
Klasa ta hermetyzuje zapytania SQL za pomocą obiektów Query z SQLAlchemy. Zamiast pisać surowe zapytania SQL w kodzie biznesowym, kontroler buduje kryteria dynamicznie, np.:

```python
# Przykład wewnętrznego budowania zapytań przez kontroler
query = repo.query().high_priority().by_category(5).sort_by("start_datetime")
events = query.get_list() # Dopiero tutaj następuje wykonanie zapytania i mapowanie na EventDTO
```
### 3. Usługa Google Calendar (`google_calendar_service.py`)

Klasa `GoogleCalendarService` odpowiada za enkapsulację protokołu OAuth 2.0 oraz komunikację sieciową z zewnętrznym API Google.

**Autoodświeżanie Tokenów (Token Lifecycle)**
* Podczas inicjalizacji usługa pobiera zaszyfrowany/zapisany ciąg znaków JSON z repozytorium poświadczeń bazy danych.
* Jeśli token dostępowy (`access_token`) wygasł, ale struktura zawiera `refresh_token`, usługa wywołuje obiekt `google.auth.transport.requests.Request()` w celu bezwiednego dla użytkownika odnowienia sesji.
* Nowe poświadczenia są automatycznie mapowane do `UserCredentialsDTO` i nadpisywane w lokalnej bazie danych.
* W przypadku braku tokenów (pierwsze uruchomienie), uruchamiany jest lokalny serwer autoryzacyjny `InstalledAppFlow`, przekierowujący użytkownika do przeglądarki internetowej.

**Pobieranie Zmian Przerzucanych z Google**
* Do pobierania różnicowego (delta sync) wykorzystywana jest metoda `get_events_since(last_sync_time)`. Wykorzystuje ona parametr `updatedMin` w zapytaniu do API Google.
* **Obsługa usunięć w chmurze:** Jeśli wydarzenie zostało skasowane po stronie Google Calendar, API zwraca obiekt o statusie `status: "cancelled"`. Usługa rozpoznaje ten stan i mapuje go na specjalistyczny obiekt `DeletedGoogleEventDTO`, przekazując do mediatora wyłącznie `google_event_id` oraz timestamp modyfikacji z Google (`updated_at`).

---

### 4. Algorytm Synchronizacji Dwukierunkowej (`sync_mediator.py`)

Klasa `SyncMediator` działa jako rozjemca (Mediator), łącząc dane z bazy lokalnej oraz z API Google Calendar, eliminując występowanie pętli nieskończonych zmian oraz rozwiązując konflikty edycji.

**Strategia Rozwiązywania Konfliktów: Last Writer Wins (LWW)**
W przypadku, gdy od czasu ostatniej udanej synchronizacji ten sam obiekt został zmodyfikowany zarówno w bazie lokalnej (np. przez użytkownika w aplikacji), jak i w Kalendarzu Google (np. na telefonie), aplikacja stosuje deterministyczne podejście LWW. Decyzja o nadrzędności danych opiera się na porównaniu mikrosekundowych znaczników czasu ostatniej edycji (`updated_at`).

**Przebieg Algorytmu Synchronizacji (Krok po Kroku)**

1. **Inicjalizacja i Okno Czasowe:**
   Mediator sprawdza w bazie datę ostatniej udanej synchronizacji (`last_sync_time`). Jeśli synchronizacja nigdy nie miała miejsca, system domyślnie przyjmuje okno czasowe równe 21 dni wstecz.
2. **Pobranie zestawów zmian:**
   * Pobranie zmian z Google (`get_events_since(last_sync_time)`).
   * Pobranie zmian lokalnych z bazy danych (`get_events_modified_since(last_sync_time)`).
3. **Mapowanie i Identyfikacja Stanów:**
   Wszystkie zmiany są grupowane w słownikach na podstawie unikalnego identyfikatora `google_event_id`.
4. **Główna Pętla Decyzyjna:**
   Dla każdego elementu, który uległ zmianie, mediator wykonuje analizę logiczną:

| Przypadek Lokalny | Przypadek Google | Decyzja i Działanie Mediator |
| :--- | :--- | :--- |
| Brak zmiany | Nowy event w Google | Tworzy nowe zadanie w bazie lokalnej (`sync_create_from_google`). |
| Brak zmiany | Usunięty w Google (`DeletedGoogleEventDTO`) | Oznacza zadanie w bazie lokalnej jako usunięte (`delete_event`). |
| Brak zmiany | Zmodyfikowany w Google | Nadpisuje dane lokalne danymi z chmury (`sync_update_from_google`). |
| Modyfikacja / Nowy lokalnie | Brak zmiany w Google | Wypycha zmianę do Google (`insert_event` lub `update_event`). Aktualizuje lokalne metadane. |
| Usunięty lokalnie (`is_deleted=True`) | Brak zmiany w Google | Wywołuje `delete_event` w API Google, trwale usuwając wydarzenie z chmury. |
| **Konflikt:** Modyfikacja lokalna | **Konflikt:** Modyfikacja w Google | **Zastosowanie LWW:** Porównanie znaczników `updated_at`. Jeśli Google jest nowsze -> aktualizacja bazy lokalnej. Jeśli lokalne jest nowsze -> wywołanie `update_event` w API Google. |
| **Konflikt:** Usunięty lokalnie | **Konflikt:** Modyfikacja w Google | **Zastosowanie LWW:** Jeśli usunięcie lokalne nastąpiło po modyfikacji w Google -> usuń z Google. Jeśli modyfikacja w Google była późniejsza -> przywróć obiekt lokalnie z danymi z Google. |

5. **Finalizacja Transakcji:**
   Po pomyślnym przetworzeniu wszystkich obiektów, mediator wywołuje metodę `update_last_synced()`, zapisując aktualny znacznik czasu jako punkt odniesienia dla kolejnego wywołania procesu synchronizacji.

---

## 5. Struktura Bazy Danych i Encji

Modele bazy danych zdefiniowane w katalogu `/Models/` zostały zaimplementowane przy użyciu nowoczesnego mapowania deklaratywnego w SQLAlchemy i posiadają następującą strukturę oraz powiązania relacyjne:

* **`UserCredentials(id:Optional[int], user_id:int, token_data:str, last_synced:Optional[datetime], created_at:datetime, updated_at:datetime)`**
  Przechowuje zautoryzowane dane sesji OAuth dla poszczególnych użytkowników systemu. Unikalny identyfikator `user_id` zapewnia jednoznaczność wpisów, podczas gdy zserializowana struktura tokenów trafia do pola tekstowego `token_data`. Tabela zarządza również czasem ostatniej synchronizacji (`last_synced`) oraz metadanymi czasu utworzenia i modyfikacji rekordu (`created_at`, `updated_at`).

* **`Category(id:Optional[int], name:str, color:CalendarColor, sync_enabled:bool, is_deleted:bool, updated_at:datetime)`**
  Zawiera unikalną nazwę kategorii (`name`) oraz flagę bezpieczeństwa `sync_enabled` (wyłączenie tej flagi powoduje, że mediator ignoruje zadania należące do tej kategorii). Pole `color` wykorzystuje zaawansowany enum `CalendarColor`, który mapuje kolory aplikacji na identyfikatory (ID) oraz kody HEX natywnie obsługiwane przez Google Calendar. Tabela implementuje mechanizm miękkiego usuwania poprzez flagi `is_deleted` i `updated_at`.

* **`Event(id:Optional[int], category_id:Optional[int], category:Optional[Category], title:str, description:str, start_datetime:Optional[datetime], end_datetime:Optional[datetime], is_completed:bool, is_high_priority:bool, is_deleted:bool, created_at:Optional[datetime], updated_at:Optional[datetime], source:EventSource, recurrence_rule:Optional[RecurrenceRule], sync_metadata:Optional[SyncMetadata])`**
  Główna encja przechowująca parametry zadania (m.in. `title`, `description`, flagi `is_completed`, `is_high_priority` oraz ramy czasowe `start_datetime` i `end_datetime`). Pole `source` (`EventSource`) określa pochodzenie rekordu (`LOCAL` / `GOOGLE`). Posiada relację wiele-do-jednego z encją `Category` za pomocą opcjonalnego klucza obcego `category_id`. Ponadto definiuje dwie ścisłe relacje jeden-do-jednego z automatycznym usuwaniem kaskadowym (`cascade="all, delete-orphan"`):

* **`RecurrenceRule(id:Optional[int], event_id:Optional[int], event:Optional[Event], rrule_string:str)`**
  Odpowiada za powtarzalność zadań. Przechowuje ciąg tekstowy `rrule_string` zgodny ze specyfikacją standardu iCalendar RFC 5545. Powiązanie z tabelą zdarzeń realizowane jest przez unikalny klucz obcy `event_id` z regułą kaskadową na poziomie bazy danych (`ondelete="CASCADE"`).

* **`SyncMetadata(event_id:int, google_event_id:str, last_synced:Optional[datetime], event:Event)`**
  Kluczowa tabela pomocnicza dla procesów synchronizacji. Przechowuje zewnętrzny identyfikator zasobu w chmurze (`google_event_id`) oraz dokładny znacznik czasu `last_synced`. Relacja opiera się na polu `event_id`, które pełni tu potrójną rolę: klucza głównego (PK), klucza obcego (FK) oraz gwaranta relacji jeden-do-jednego.

---
### 6. Testy

**Jak uruchomić testy jednostkowe?**
Wszystkie komponenty posiadają przygotowane mocki interfejsów. Testy sprawdzają poprawność izolacji warstw i algorytmu LWW. Wywołaj komendę w terminalu:

```bash
python -m pytest UnitTests