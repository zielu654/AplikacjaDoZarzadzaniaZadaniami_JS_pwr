"""
Tymczasowa reprezentacja zadania i kategorii + przykladowe dane.

Sluzy WYLACZNIE do budowania frontu, zanim repozytorium kolegi bedzie
gotowe. FakeTaskRepository implementuje ten sam interfejs, ktory mialaby
mial pozniejszy SQLiteTaskRepository - front pyta repozytorium, nie
fake_data bezposrednio. Gdy backend bedzie gotowy, podmieniamy
implementacje, front sie nie zmienia.

PRIORYTETOWE: To nie jest kategoria w bazie. To osobna flaga (priority: bool)
na zadaniu. W sidebarze "Priorytetowe" to filtr-pseudokategoria pokazujaca
zadania z dowolnej kategorii z priority=True, kolor czerwony hardcoded
w theme.PRIORYTETOWE_COLOR.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List


# ============================================================
# MODELE DOMENOWE
# ============================================================

@dataclass
class Category:
    id: int
    name: str
    color: str  # hex


@dataclass
class Task:
    id: int
    title: str
    description: str
    due_date: datetime
    is_done: bool
    priority: bool                     # NIE kategoria - patrz uwaga wyzej
    category_id: Optional[int]         # None = "Bez Kategorii"
    created_at: datetime
    modified_at: datetime
    is_deleted: bool = False
    recurrence_rule: Optional[str] = None  # None = jednorazowe, tekst = nawyk


# ============================================================
# KOLORY KATEGORII - stonowane, "basic" wg preferencji
# (bootstrap-style, srednie nasycenie, czytelne)
# ============================================================

FAKE_CATEGORIES = {
    1: Category(id=1, name="Kategoria 1", color="#4A90D9"),  # niebieski stonowany
    2: Category(id=2, name="Kategoria 2", color="#5CB85C"),  # zielony stonowany
    3: Category(id=3, name="Kategoria 3", color="#A973B5"),  # fiolet stonowany
}


# ============================================================
# ZADANIA - mix scenariuszy: dzisiejsze/przyszle/przeszle,
# wykonane/nie, priorytetowe, cykliczne, bez kategorii, usuniete
# ============================================================

FAKE_TASKS = [
    # Cykliczne (nawyki)
    Task(id=1, title="Poranny trening", description="30 minut biegania",
         due_date=datetime(2026, 6, 19, 7, 0), is_done=False, priority=False,
         category_id=2, created_at=datetime(2026, 6, 1, 9, 0),
         modified_at=datetime(2026, 6, 1, 9, 0),
         recurrence_rule="co dzien 7:00-7:30"),

    Task(id=5, title="Sprzatanie", description="",
         due_date=datetime.now().replace(hour=18, minute=0, second=0, microsecond=0),
         is_done=False, priority=False,
         category_id=2, created_at=datetime(2026, 5, 1, 10, 0),
         modified_at=datetime(2026, 5, 1, 10, 0),
         recurrence_rule="co pon 18:00-19:00"),

    Task(id=10, title="Mycie samochodu", description="",
         due_date=datetime(2026, 6, 21, 11, 0), is_done=False, priority=False,
         category_id=3, created_at=datetime(2026, 5, 1, 10, 0),
         modified_at=datetime(2026, 5, 1, 10, 0),
         recurrence_rule="co dr niedz 11:00-11:30"),

    # Nawyk priorytetowy - testuje czy ramka jest czerwona zamiast koloru kategorii
    Task(id=11, title="Codzienna medytacja", description="",
         due_date=datetime(2026, 6, 19, 22, 0), is_done=False, priority=True,
         category_id=2, created_at=datetime(2026, 5, 1, 10, 0),
         modified_at=datetime(2026, 5, 1, 10, 0),
         recurrence_rule="co dzien 22:00-22:15"),

    # Jednorazowe (NIE nawyki - pokazuja sie tylko w Wszystkie/Kategoria, nie w Nawykach)
    Task(id=2, title="Spotkanie z zespolem", description="Omowienie postepow",
         due_date=datetime(2026, 6, 19, 10, 0), is_done=False, priority=True,
         category_id=1, created_at=datetime(2026, 6, 10, 12, 0),
         modified_at=datetime(2026, 6, 17, 8, 30)),

    Task(id=3, title="Kupic prezent", description="",
         due_date=datetime(2026, 6, 20, 0, 0), is_done=False, priority=False,
         category_id=3, created_at=datetime(2026, 6, 15, 14, 0),
         modified_at=datetime(2026, 6, 15, 14, 0)),

    Task(id=4, title="Wyslac raport", description="",
         due_date=datetime(2026, 6, 18, 16, 0), is_done=True, priority=False,
         category_id=1, created_at=datetime(2026, 6, 10, 9, 0),
         modified_at=datetime(2026, 6, 18, 16, 5)),

    Task(id=6, title="Zadzwonic do mamy", description="",
         due_date=datetime(2026, 6, 19, 19, 0), is_done=False, priority=False,
         category_id=None, created_at=datetime(2026, 6, 19, 8, 0),
         modified_at=datetime(2026, 6, 19, 8, 0)),

    Task(id=7, title="Oddac ksiazki do biblioteki", description="",
         due_date=datetime(2026, 6, 15, 17, 0), is_done=False, priority=True,
         category_id=3, created_at=datetime(2026, 6, 5, 11, 0),
         modified_at=datetime(2026, 6, 5, 11, 0)),

    # Zadania na dzisiaj - dynamicznie wzgledem datetime.now() zeby zawsze
    # pojawialy sie w DzisView niezaleznie od daty uruchomienia aplikacji.
    Task(id=12, title="Spotkanie ze studentami", description="",
         due_date=datetime.now().replace(hour=10, minute=0, second=0, microsecond=0),
         is_done=False, priority=False,
         category_id=1, created_at=datetime(2026, 6, 20, 9, 0),
         modified_at=datetime(2026, 6, 20, 9, 0),
         recurrence_rule="10:00-11:00"),

    Task(id=13, title="Obiad z mama", description="",
         due_date=datetime.now().replace(hour=14, minute=0, second=0, microsecond=0),
         is_done=False, priority=True,
         category_id=None, created_at=datetime(2026, 6, 21, 18, 0),
         modified_at=datetime(2026, 6, 21, 18, 0),
         recurrence_rule="14:00-15:00"),

    Task(id=14, title="Czytanie ksiazki", description="",
         due_date=datetime.now().replace(hour=21, minute=30, second=0, microsecond=0),
         is_done=False, priority=False,
         category_id=3, created_at=datetime(2026, 6, 22, 8, 0),
         modified_at=datetime(2026, 6, 22, 8, 0),
         recurrence_rule="21:30-22:00"),

    # Zadanie kolidujace z "Spotkanie ze studentami" (10:00-11:00) - dla demo konfliktow
    Task(id=15, title="Rozmowa telefoniczna", description="",
         due_date=datetime.now().replace(hour=10, minute=30, second=0, microsecond=0),
         is_done=False, priority=False,
         category_id=1, created_at=datetime.now(),
         modified_at=datetime.now(),
         recurrence_rule="10:30-11:30"),

    Task(id=9, title="Przygotowac prezentacje", description="",
         due_date=datetime(2026, 6, 25, 13, 0), is_done=False, priority=True,
         category_id=1, created_at=datetime(2026, 6, 14, 10, 0),
         modified_at=datetime(2026, 6, 16, 15, 0)),

    # USUNIETE - nigdy nie powinno byc widoczne poza koszem
    Task(id=8, title="Stare zadanie", description="",
         due_date=datetime(2026, 6, 10, 12, 0), is_done=False, priority=False,
         category_id=2, created_at=datetime(2026, 6, 1, 9, 0),
         modified_at=datetime(2026, 6, 12, 9, 0),
         is_deleted=True),
]


# ============================================================
# WZORZEC REPOZYTORIUM - interfejs uzywany przez front
# ============================================================

class TaskRepository:
    """Abstrakcyjny interfejs repozytorium zadan.

    Front woła te metody, nie sięga bezposrednio do fake_data. Dzieki temu
    pozniej mozna podmienic implementacje (SQLiteTaskRepository, lub
    SyncedTaskRepository ktore laczy SQLite + Google Calendar przez
    SyncMediator) bez tykania UI."""

    def get_all(self, include_deleted: bool = False) -> List[Task]:
        raise NotImplementedError

    def get_habits(self) -> List[Task]:
        """Zwraca tylko zadania cykliczne (recurrence_rule != None) i nieusuniete."""
        raise NotImplementedError

    def get_categories(self) -> List[Category]:
        raise NotImplementedError

    def get_category(self, category_id: Optional[int]) -> Optional[Category]:
        raise NotImplementedError

    # ---- mutacje (CRUD) ----
    def add_task(self, task: Task) -> Task:
        raise NotImplementedError

    def update_task(self, task: Task) -> Optional[Task]:
        raise NotImplementedError

    def delete_task(self, task_id: int) -> bool:
        raise NotImplementedError

    def add_category(self, category: Category) -> Category:
        raise NotImplementedError

    def update_category(self, category: Category) -> Optional[Category]:
        raise NotImplementedError

    def delete_category(self, category_id: int) -> bool:
        raise NotImplementedError


class FakeTaskRepository(TaskRepository):
    """In-memory implementacja na FAKE_TASKS/FAKE_CATEGORIES."""

    def get_all(self, include_deleted=False):
        if include_deleted:
            return list(FAKE_TASKS)
        return [t for t in FAKE_TASKS if not t.is_deleted]

    def get_habits(self):
        return [t for t in self.get_all() if t.recurrence_rule]

    def get_categories(self):
        return list(FAKE_CATEGORIES.values())

    def get_category(self, category_id):
        if category_id is None:
            return None
        return FAKE_CATEGORIES.get(category_id)

    # ---- CRUD - mutacje ----

    def add_task(self, task):
        """Dodaje task do listy, autoassign id, ustawia created/modified."""
        new_id = max((t.id for t in FAKE_TASKS), default=0) + 1
        task.id = new_id
        now = datetime.now()
        if not task.created_at:
            task.created_at = now
        task.modified_at = now
        FAKE_TASKS.append(task)
        return task

    def update_task(self, task):
        """Podmienia istniejacy task po id. Zwraca None jesli nie znaleziono."""
        for i, t in enumerate(FAKE_TASKS):
            if t.id == task.id:
                task.modified_at = datetime.now()
                FAKE_TASKS[i] = task
                return task
        return None

    def delete_task(self, task_id):
        """Soft delete - ustawia is_deleted=True. Zwraca True jesli znaleziono."""
        for t in FAKE_TASKS:
            if t.id == task_id:
                t.is_deleted = True
                t.modified_at = datetime.now()
                return True
        return False

    def add_category(self, category):
        new_id = max(FAKE_CATEGORIES.keys(), default=0) + 1
        category.id = new_id
        FAKE_CATEGORIES[new_id] = category
        return category

    def update_category(self, category):
        if category.id in FAKE_CATEGORIES:
            FAKE_CATEGORIES[category.id] = category
            return category
        return None

    def delete_category(self, category_id):
        """Twardy delete kategorii. Tasks z tym category_id zostaja
        z category_id=None (zachowuja sie, nie usuwane)."""
        if category_id not in FAKE_CATEGORIES:
            return False
        del FAKE_CATEGORIES[category_id]
        for t in FAKE_TASKS:
            if t.category_id == category_id:
                t.category_id = None
        return True


# ============================================================
# Stara funkcyjna fasada - zostawiona dla kompatybilnosci wstecz
# (gdyby ktos jeszcze ja wolal). Nowy kod uzywa FakeTaskRepository.
# ============================================================

_default_repo = FakeTaskRepository()

def get_all_tasks(include_deleted=False):
    return _default_repo.get_all(include_deleted)

def get_category(category_id):
    return _default_repo.get_category(category_id)

def get_all_categories():
    return _default_repo.get_categories()