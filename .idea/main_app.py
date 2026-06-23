"""
Glowny plik aplikacji.

Layout 3-kolumnowy:
  +----------+--------------------+----------+
  | Sidebar  | View (Nawyki /     | Right    |
  | 30%      | Wszystkie / Dzis)  | Panel    |
  |          | 50%                | 20%      |
  +----------+--------------------+----------+

Sidebar trzyma nawigacje i jest stale. View i RightPanel sa podmienialne
poprzez ViewSwitcher - klik w pozycje sidebara przelacza aktualny view
(NawykiView <-> WszystkieView <-> DzisView) i odpowiednio RightPanel z
opcjami Filtruj/Widok dla tego view.

Pozostale callbacki (klik "+", opcje Sortuj/Filtruj/Widok, klik na zadanie,
klik "..." na kategoriach) sa puste - mechanika dojdzie pozniej.
"""

import os
import tkinter as tk
from tkinter import messagebox
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from front.theme import BG, SEPARATOR_COLOR, LEFT_RELWIDTH, LIST_RELWIDTH
from front.sidebar import (
    Sidebar, KEY_DZIS, KEY_WSZYSTKIE, KEY_NAWYKI,
    KEY_PRIORYTETOWE, KEY_CATEGORY_PREFIX
)
from front.right_panel import RightPanel
from front.views import NawykiView, WszystkieView, DzisView
from front.views.priorytetowe import PriorytetoweView
from front.views.kategoria import KategoriaView
from front.dialogs import TaskFormDialog, CategoryFormDialog, TaskPreviewDialog
from front.notifications import ConflictNotification, find_conflicts

# Importy backendu
from Models.base import Base
from DatabaseSqlAlchemy.sql_alchemy_category_repository import SqlAlchemyCategoryRepository
from DatabaseSqlAlchemy.sql_alchemy_event_repository import SqlAlchemyEventRepository
from DatabaseSqlAlchemy.sql_alchemy_user_credentials_repository import SqlAlchemyUserCredentialsRepository
from Controllers.category_controller import CategoryController
from Controllers.event_controller import EventController
from Controllers.auth_controller import AuthController
from Services.google_calendar_service import GoogleCalendarService
from Services.sync_mediator import SyncMediator
from backend_integration import DatabaseTaskRepository

# proporcje: 30% sidebar, 50% view, 20% right panel
SEPARATOR_RELX = LEFT_RELWIDTH
RIGHT_PANEL_RELX = LEFT_RELWIDTH + LIST_RELWIDTH  # 0.3 + 0.5 = 0.8
RIGHT_PANEL_RELWIDTH = 1.0 - RIGHT_PANEL_RELX     # 0.2

# Klikalnosci pozycji sidebara - mapuja klucz na klase view do utworzenia
SIDEBAR_VIEW_MAP = {
    KEY_DZIS:         DzisView,
    KEY_WSZYSTKIE:    WszystkieView,
    KEY_NAWYKI:       NawykiView,
    KEY_PRIORYTETOWE: PriorytetoweView,
}


# ============================================================
# Repozytorium (Inicjalizacja SQLite + Google Calendar)
# ============================================================
DB_PATH = "app_database.db"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_PATH = os.path.join(BASE_DIR, 'Secrets', 'credentials.json')

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

cat_repo = SqlAlchemyCategoryRepository(session)
ev_repo = SqlAlchemyEventRepository(session)
cred_repo = SqlAlchemyUserCredentialsRepository(session)

google_service = GoogleCalendarService(cred_repo, current_user_id=1, credentials_path=CREDENTIALS_PATH)
auth_ctrl = AuthController(google_service, cred_repo, current_user_id=1)
mediator = SyncMediator(google_service)

event_ctrl = EventController(ev_repo, cat_repo, mediator)
cat_ctrl = CategoryController(cat_repo, ev_repo)
mediator.set_controllers(event_ctrl, auth_ctrl)

repository = DatabaseTaskRepository(session, event_ctrl, cat_ctrl)


# ============================================================
# Okno glowne
# ============================================================
window = tk.Tk()
window.title("Lista zadań")
window.geometry("950x600")
window.configure(bg=BG)
window.minsize(700, 400)

body = tk.Frame(window, bg=BG)
body.pack(side="top", fill="both", expand=True)


# ============================================================
# Callbacki
# ============================================================

def _open_task_dialog(task=None):
    """Helper: otwiera TaskFormDialog. task=None to tryb create, inaczej edit.
    Po Zapisz: add_task lub update_task + rebuild aktualnego view.
    Po Usun (tylko w trybie edit): delete_task + rebuild."""
    dlg = TaskFormDialog(window, repository=repository, task=task)

    # Usun ma priorytet nad result - sprawdzamy go pierwszy
    if dlg.deleted and task is not None:
        repository.delete_task(task.id)
        if switcher.current_view is not None:
            switcher.current_view._rebuild_content()
        return

    if dlg.result is None:
        return  # user kliknal Anuluj

    all_tasks = repository.get_all()
    tasks_to_check = [t for t in all_tasks if t.id != dlg.result.id]
    tasks_to_check.append(dlg.result)

    conflicts = find_conflicts(tasks_to_check, repository)
    my_conflicts = [c for c in conflicts if c[0] is dlg.result or c[1] is dlg.result]

    if my_conflicts:
        messagebox.showwarning("Konflikt", "Nie udało się dodać zadania, ponieważ nakłada się z innym.")
        ConflictNotification(window, my_conflicts, repository=repository)
        return

    if task is None:
        repository.add_task(dlg.result)
    else:
        repository.update_task(dlg.result)
    if switcher.current_view is not None:
        switcher.current_view._rebuild_content()


def _open_category_dialog(category=None):
    """Helper: otwiera CategoryFormDialog. category=None to tryb create.
    Po Usun (tylko w trybie edit): delete_category + refresh sidebar."""
    dlg = CategoryFormDialog(window, repository=repository, category=category)

    if dlg.deleted and category is not None:
        repository.delete_category(category.id)
        sidebar.refresh()
        if switcher.current_view is not None:
            switcher.current_view._rebuild_content()
        return

    if dlg.result is None:
        return
    if category is None:
        repository.add_category(dlg.result)
    else:
        repository.update_category(dlg.result)
    # Sidebar (kategorie sa tam wyswietlone) + view (kolory zadan moga sie zmienic)
    sidebar.refresh()
    if switcher.current_view is not None:
        switcher.current_view._rebuild_content()


def on_dodaj_zadanie():
    """Klik na 'Dodaj zadanie' / '+' w sidebarze - otwiera dialog tworzenia."""
    _open_task_dialog(task=None)


def on_dodaj_kategoria():
    """Klik na 'Kategorie' lub '+' obok w sidebarze - otwiera dialog tworzenia kategorii."""
    _open_category_dialog(category=None)


def on_category_menu(category, action):
    """Klik na opcje '...' przy kategorii w sidebarze.
    action: 'edit' albo 'delete'."""
    if action == "edit":
        _open_category_dialog(category)
    elif action == "delete":
        repository.delete_category(category.id)
        sidebar.refresh()
        if switcher.current_view is not None:
            switcher.current_view._rebuild_content()


def on_view_add():
    """Klik na '+' w toolbarze view - tworzy nowe zadanie."""
    _open_task_dialog(task=None)


def on_view_sort(parent, option):
    """Wybor opcji sortowania w view. parent=None (Sortuj nie ma submenu)."""
    if switcher.current_view is not None:
        switcher.current_view.apply_sort(option)


def on_view_filter(parent, option):
    """Wybor opcji filtrowania. parent = nazwa kategorii filtra (Priorytet/Status/...),
    option = wybrana wartosc submenu (Tak/Nie/Wszystkie/...)."""
    if switcher.current_view is not None:
        switcher.current_view.apply_filter(parent, option)


def on_display_mode_select(parent, option):
    """Wybor opcji z menu 'Widok'. parent=None dla Lista/TimeBlocks,
    parent='Kalendarz' dla Tygodniowy/Miesieczny."""
    if switcher.current_view is not None:
        switcher.current_view.apply_display_mode(parent, option)


def on_task_toggle(task):
    """Klik checkboxa na zadaniu (toggle is_done). TaskRow sam zmienia stan,
    tu zapisujemy do repo (update_task)."""
    repository.update_task(task)


def on_task_menu(task, action):
    """Klik opcji w menu '...' zadania. action: 'preview', 'edit' albo 'delete'."""
    if action == "preview":
        TaskPreviewDialog(window, repository=repository, task=task)
    elif action == "edit":
        _open_task_dialog(task)
    elif action == "delete":
        repository.delete_task(task.id)
        if switcher.current_view is not None:
            switcher.current_view._rebuild_content()


def on_conflict_check():
    """Klik na 'Konflikty ⚠' w toolbarze - wykrywa konflikty czasowe
    i pokazuje ConflictNotification."""
    all_tasks = repository.get_all()
    conflicts = find_conflicts(all_tasks, repository)
    ConflictNotification(window, conflicts, repository=repository)


def on_sync_click():
    """Logowanie do Google oraz wymiana danych."""
    if not auth_ctrl.is_logged_in():
        messagebox.showinfo("Google Calendar", "Przekierowanie do przeglądarki w celu zalogowania...")
        success = auth_ctrl.login()
        if not success:
            messagebox.showerror("Błąd", "Nie udało się zalogować do konta Google.")
            return

    try:
        messagebox.showinfo("Synchronizacja", "Trwa synchronizacja z Google Calendar...")
        mediator.run_two_way_sync()

        sidebar.refresh()
        if switcher.current_view is not None:
            switcher.current_view._rebuild_content()

        messagebox.showinfo("Sukces", "Pomyślnie zsynchronizowano zadania.")
    except Exception as e:
        messagebox.showerror("Błąd", f"Wystąpił problem: {str(e)}")


# ============================================================
# ViewSwitcher - mechanika podmiany aktualnego view + RightPanel
# ============================================================

class ViewSwitcher:
    """Zarzadza zywotnoscia aktualnego view i sparowanego z nim RightPanel.

    switch_to(view_class) niszczy poprzednia pare i tworzy nowa. RightPanel
    bierze swoja konfiguracje (filter_options, display_mode_options, callbacki)
    z atrybutow nowo utworzonego view przez RightPanel.from_view(view).

    Po podmianie aktualizuje tez module-level zmienne `view` i `right_panel`
    zeby kod zewnetrzny (testy, main_app inne funkcje) zawsze mial referencje
    do aktualnej pary.
    """

    def __init__(self, parent):
        self.parent = parent
        self.current_view = None
        self.current_right_panel = None
        self.current_view_class = None

    def switch_to(self, view_class, **kwargs):
        # Sprawdz czy klikamy dokladnie ten sam widok (uwzgledniajac category_id dla KategoriaView)
        is_same_class = (view_class is self.current_view_class)
        is_same_cat = (getattr(self.current_view, 'category_id', None) == kwargs.get('category_id'))

        if is_same_class and is_same_cat:
            return

        # Posprzataj poprzednie
        if self.current_view is not None:
            self.current_view.destroy()
        if self.current_right_panel is not None:
            self.current_right_panel.destroy()

        # Utworz nowy view
        self.current_view = view_class(
            self.parent, repository=repository,
            on_add=on_view_add,
            on_sort=on_view_sort,
            on_filter=on_view_filter,
            on_display_mode=on_display_mode_select,
            on_toggle_task=on_task_toggle,
            on_task_menu=on_task_menu,
            on_conflict_check=on_conflict_check,
            on_sync=on_sync_click,
            **kwargs
        )
        self.current_view.place(relx=LEFT_RELWIDTH, y=0,
                                 relwidth=LIST_RELWIDTH, relheight=1)

        # Utworz nowy RightPanel sparowany z view
        self.current_right_panel = RightPanel.from_view(self.parent, self.current_view)
        self.current_right_panel.place(relx=RIGHT_PANEL_RELX, y=0,
                                        relwidth=RIGHT_PANEL_RELWIDTH, relheight=1)

        self.current_view_class = view_class

        # Zaktualizuj module-level globale dla kodu zewnetrznego
        global view, right_panel
        view = self.current_view
        right_panel = self.current_right_panel

        # Sync pozycji Widok/Filtruj w RightPanel z Header/Toolbar view
        # (after_idle bo pozycje sa znane dopiero po renderowaniu)
        window.after_idle(self.current_right_panel.sync_with_view)
        # Trigger responsive layout (po podmianie body sie nie zmienia,
        # wiec jego <Configure> nie wystrzeli - reczne wywolanie)
        window.after_idle(_trigger_responsive_layout)


def _trigger_responsive_layout():
    """Recznie wywoluje update_fonts na sidebar, right_panel I view.

    Wazne: view tez. <Configure> wystrzela tylko gdy widget zmieni rozmiar -
    po switch_to nowy view dostaje DOKLADNIE te same wymiary co stary, wiec
    Configure moze nie wystrzelic i view zostaje z domyslnym fontem (efekt:
    w fullscreen po zmianie zakładki layout 'gorzej wyglada'). Recznie
    wymuszamy update_fonts zeby gwarantowac spojny stan.

    update_idletasks() PRZED odczytem rozmiarow - po stworzeniu nowego view
    canvas wewnatrz scroll moze nie miec jeszcze swojej finalnej szerokosci
    (pending geometry events). Bez tego ListView.update_fonts czyta canvas_w
    = 1px, wpada w fallback, skaluje fonty TaskRow z byle czego i layout
    sie rozjezdza. Po update_idletasks - canvas ma juz prawdziwa szerokosc."""
    if switcher.current_right_panel is None:
        return

    # Wymus przetworzenie pending geometry events
    body.update_idletasks()

    w = body.winfo_width()
    h = body.winfo_height()
    sidebar.update_fonts(int(w * LEFT_RELWIDTH), h)
    switcher.current_right_panel.update_fonts(int(w * LIST_RELWIDTH), h)
    if switcher.current_view is not None:
        # Drugie update_idletasks bezposrednio przed view.update_fonts -
        # gdyby cos sie jeszcze nie ustabilizowalo po pierwszym.
        switcher.current_view.update_idletasks()
        switcher.current_view.update_fonts(int(w * LIST_RELWIDTH), h)


def on_sidebar_select(key):
    """Klik w pozycje sidebara - przelacza view jesli key jest w SIDEBAR_VIEW_MAP lub to kategoria."""
    if key.startswith(KEY_CATEGORY_PREFIX):
        cat_id = int(key[len(KEY_CATEGORY_PREFIX):])
        switcher.switch_to(KategoriaView, category_id=cat_id)
    else:
        view_class = SIDEBAR_VIEW_MAP.get(key)
        if view_class is not None:
            switcher.switch_to(view_class)


# ============================================================
# Sidebar
# ============================================================
sidebar = Sidebar(
    body,
    repository=repository,
    on_dodaj_zadanie=on_dodaj_zadanie,
    on_select=on_sidebar_select,
    on_category_menu=on_category_menu,
    on_dodaj_kategoria=on_dodaj_kategoria,
)
sidebar.place(x=0, y=0, relwidth=LEFT_RELWIDTH, relheight=1)


# ============================================================
# Separator sidebar/view
# ============================================================
separator = tk.Frame(body, bg=SEPARATOR_COLOR, width=2)
separator.place(relx=SEPARATOR_RELX, x=-1, y=0, relheight=1)


# ============================================================
# ViewSwitcher + pierwszy view (Nawyki)
# ============================================================
# Module-level zmienne aktualizowane przez switcher.switch_to().
# Kod zewnetrzny (testy, callbacki) uzywa app.view / app.right_panel.
view = None
right_panel = None

switcher = ViewSwitcher(body)
switcher.switch_to(NawykiView)


# ============================================================
# Responsywnosc - przy resize body, przeskaluj sidebar i right_panel.
# View sam reaguje na swoj <Configure>.
# ============================================================
def update_responsive_layout(event):
    if event.widget is body:
        sidebar.update_fonts(int(event.width * LEFT_RELWIDTH), event.height)
        if switcher.current_right_panel is not None:
            switcher.current_right_panel.update_fonts(int(event.width * LIST_RELWIDTH), event.height)
            window.after_idle(switcher.current_right_panel.sync_with_view)


body.bind("<Configure>", update_responsive_layout)


if __name__ == "__main__":
    window.mainloop()