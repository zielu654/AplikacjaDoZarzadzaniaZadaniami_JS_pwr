"""
Bazowe klasy widokow.

Terminologia:
  - "view" (np. NawykiView, WszystkieView, DzisView) - JEDNA z duzych
    pozycji w sidebarze, jeden ekran aplikacji.
  - "display mode" (Lista / Kalendarz / TimeBlocks) - SPOSOB wyswietlenia
    zawartosci w obrebie jednego view. W UI nazywa sie "Widok" (polski).

Hierarchia:
  View (abstract)              - szkielet: Header + Toolbar + ScrollableContent
   └── ListView                - wyswietla zadania jako liste TaskRow
        ├── NawykiView         - tylko zadania z recurrence_rule
        ├── WszystkieView      - wszystkie zadania
        └── DzisView           - tylko zadania na dzisiaj

Stan sortowania/filtrowania/display_mode:
  Kazdy view przechowuje:
    - sort_option: None lub str (aktualnie wybrana opcja Sortuj)
    - filter_state: dict (np. {"Priorytet": "Tak", "Status": "Nieukonczone"})
    - display_mode: str (na razie tylko "Lista" jest renderowany)
  Aplikacja wola apply_sort/apply_filter/apply_display_mode - View
  aktualizuje stan i _rebuild_content() ponownie buduje liste przeliczona
  przez _get_displayed_tasks() = get_tasks -> filter -> sort.

Konkretne views nadpisuja CLASS ATTRIBUTES (TITLE, SORT_OPTIONS, FILTER_CATEGORIES,
DISPLAY_MODE_OPTIONS, SHOW_ADD, TASK_STYLE).
"""

import tkinter as tk
from datetime import datetime, timedelta

from front.theme import BG
from front.header_toolbar import Header, Toolbar
from front.components import ScrollableContent
from front.task_row import TaskRow


CONTENT_PADX = 20
CONTENT_PADY = 10


# ============================================================
# View - baza abstrakcyjna
# ============================================================

class View(tk.Frame):
    """Abstrakcyjna baza dla widokow.

    Subklasa nadpisuje CLASS ATTRIBUTES i implementuje:
      - get_tasks()        - zwraca liste Task do wyswietlenia
      - build_content()    - wypelnia container widgetami (ListView juz to ma)
    """

    # ---- Class attributes: subklasy nadpisuja ----
    TITLE = "View"
    SORT_OPTIONS = ["Data", "Priorytet"]            # None = brak Sortuj w toolbarze
    FILTER_CATEGORIES = ["Priorytet", "Status", "Data"]  # kategorie filtra (submenu)
    DISPLAY_MODE_OPTIONS = [
        "Lista",
        ("Kalendarz", ["Tygodniowy", "Miesięczny"]),
        # TimeBlocks tylko w DzisView - tam nadpisane
    ]
    SHOW_ADD = True

    def __init__(self, parent, repository,
                 on_sort=None, on_filter=None,
                 on_display_mode=None, on_add=None,
                 on_toggle_task=None, on_task_menu=None,
                 on_conflict_check=None, on_sync=None):
        super().__init__(parent, bg=BG)
        self.repository = repository

        # ---- Stan sortowania/filtrowania/display ----
        self.sort_option = None              # np. "Data" / "Priorytet" / "Kategorie"
        self.filter_state = {}               # {"Priorytet": "Tak", "Status": "Nieukonczone"}
        self.display_mode = "Lista"          # default

        # ---- Wygenerowane opcje (dla RightPanel) ----
        self.filter_options = self._build_filter_options()
        self.display_mode_options = self.DISPLAY_MODE_OPTIONS

        # ---- Callbacki ----
        self.on_filter_callback = on_filter or (lambda p, o: None)
        self.on_display_mode_callback = on_display_mode or (lambda p, o: None)
        self.on_toggle_task = on_toggle_task or (lambda t: None)
        self.on_task_menu = on_task_menu or (lambda t, a: None)

        # ---- Header ----
        self.header = Header(self, self.TITLE)
        self.header.pack(side="top", pady=(Header.HEADER_TOP_PADY,
                                            Header.HEADER_BOT_PADY))

        # ---- Toolbar ----
        self.toolbar = Toolbar(self,
                               sort_options=self.SORT_OPTIONS,
                               show_add=self.SHOW_ADD,
                               on_sort=on_sort,
                               on_add=on_add,
                               on_conflict_check=on_conflict_check,
                               on_sync=on_sync,
                               is_sort_selected=self._sort_is_selected)
        self.toolbar.pack(side="top", fill="x",
                          padx=Toolbar.LIST_PADX,
                          pady=(0, Toolbar.TOOLBAR_BOT_PADY))

        # ---- Scrollowalna zawartosc ----
        self.scroll = ScrollableContent(self, bg=BG)
        self.scroll.pack(side="top", fill="both", expand=True)

        self.build_content(self.scroll.container)

        self.bind("<Configure>", self._on_configure)

    def get_tasks(self):
        return self.repository.get_all()

    def build_content(self, container):
        pass

    def _build_filter_options(self):
        result = []
        for cat in self.FILTER_CATEGORIES:
            values = self._filter_values_for(cat)
            result.append((cat, values))
        return result

    def _filter_values_for(self, category):
        if category == "Priorytet":
            return ["Tak", "Nie", "Wszystkie"]
        if category == "Kategoria":
            names = [c.name for c in self.repository.get_categories()]
            return names + ["Wszystkie"]
        if category == "Status":
            return ["Nieukończone", "Zrealizowane", "Wszystkie"]
        if category == "Rodzaj":
            return ["Jednorazowe", "Nawyki", "Wszystkie"]
        if category == "Data":
            return ["Dziś", "Ten tydzień", "Wszystkie"]
        return ["Wszystkie"]

    def apply_sort(self, option):
        self.sort_option = option
        self._rebuild_content()

    def apply_filter(self, category, value):
        if value == "Wszystkie":
            self.filter_state.pop(category, None)
        else:
            self.filter_state[category] = value
        self._rebuild_content()

    def apply_display_mode(self, parent, option):
        if parent is not None:
            new_mode = f"{parent} - {option}"
        else:
            new_mode = option
        if new_mode != self.display_mode:
            self.display_mode = new_mode
            self._rebuild_content()

    # ---- Predykaty selected dla dropdownow w toolbarze/right panelu ----
    # Wolane przez DropdownButton._decorate przy KAZDYM otwarciu menu, wiec
    # czytaja zywy stan view (sort_option, filter_state, display_mode).

    def _sort_is_selected(self, label, parent_label=None):
        return label == self.sort_option

    def _filter_is_selected(self, label, parent_label=None):
        if parent_label is None:
            # Top-level: nazwa kategorii filtra (kaskada). Mark gdy aktywny filtr.
            return label in self.filter_state
        # Subitem: wartosc w kategorii. "Wszystkie" oznacza brak filtra.
        current = self.filter_state.get(parent_label)
        if current is None:
            return label == "Wszystkie"
        return label == current

    def _display_is_selected(self, label, parent_label=None):
        if parent_label is None:
            # Top-level: "Lista", "TimeBlocks" lub kaskada "Kalendarz"
            if label == "Kalendarz":
                return self.display_mode.startswith("Kalendarz - ")
            return self.display_mode == label
        # Subitem w "Kalendarz": "Tygodniowy"/"Miesięczny"
        return self.display_mode == f"{parent_label} - {label}"

    def _rebuild_content(self):
        pass

    def _on_configure(self, event):
        if event.widget is self:
            self.update_fonts(event.width, event.height)

    def update_fonts(self, width, height):
        self.header.update_fonts(width, height)
        self.toolbar.update_fonts(width, height)


# ============================================================
# ListView - widok z lista TaskRow
# ============================================================

class ListView(View):
    """Widok wyswietlajacy zadania - jako lista TaskRow (default) ALBO jako
    kalendarz tygodniowy/miesieczny (wybor przez display_mode).

    DzisView dodatkowo override'uje build_content dla TimeBlocks.

    Implementuje logike sortowania/filtrowania (_get_displayed_tasks).
    """

    TASK_STYLE = "outlined"
    TASK_GAP_PADY = 10

    def __init__(self, *args, **kwargs):
        self.task_rows = []
        self.calendar_widget = None
        self._last_width = None
        self._last_height = None
        super().__init__(*args, **kwargs)

    def build_content(self, container):
        self.calendar_widget = None

        if self.display_mode == "Kalendarz - Tygodniowy":
            self._build_week_calendar(container)
        elif self.display_mode == "Kalendarz - Miesięczny":
            self._build_month_calendar(container)
        else:
            for task in self._get_displayed_tasks():
                self._add_task_row(container, task)

    def _build_week_calendar(self, container):
        from front.views.calendar import WeekCalendarContent
        self.calendar_widget = WeekCalendarContent(
            container, self._get_displayed_tasks(),
            repository=self.repository,
            on_toggle=self.on_toggle_task,
            on_menu=self.on_task_menu,
        )
        self.calendar_widget.pack(fill="both", expand=True, padx=CONTENT_PADX, pady=5)

    def _build_month_calendar(self, container):
        from front.views.calendar import MonthCalendarContent
        self.calendar_widget = MonthCalendarContent(
            container, self._get_displayed_tasks(),
            repository=self.repository,
            on_toggle=self.on_toggle_task,
            on_menu=self.on_task_menu,
        )
        self.calendar_widget.pack(fill="both", expand=True, padx=CONTENT_PADX, pady=5)

    def _get_displayed_tasks(self):
        tasks = list(self.get_tasks())

        for category, value in self.filter_state.items():
            tasks = self._apply_filter(tasks, category, value)

        if self.sort_option == "Data":
            tasks = sorted(tasks, key=lambda t: t.due_date)
        elif self.sort_option == "Priorytet":
            tasks = sorted(tasks, key=lambda t: (not t.priority, t.due_date))
        elif self.sort_option == "Kategorie":
            tasks = sorted(tasks, key=lambda t: (t.category_id is None, t.category_id or 0, t.due_date))

        return tasks

    def _apply_filter(self, tasks, category, value):
        if category == "Priorytet":
            if value == "Tak":
                return [t for t in tasks if t.priority]
            if value == "Nie":
                return [t for t in tasks if not t.priority]
        elif category == "Kategoria":
            cat = next((c for c in self.repository.get_categories() if c.name == value), None)
            if cat is not None:
                return [t for t in tasks if t.category_id == cat.id]
        elif category == "Status":
            if value == "Nieukończone":
                return [t for t in tasks if not t.is_done]
            if value == "Zrealizowane":
                return [t for t in tasks if t.is_done]
        elif category == "Rodzaj":
            if value == "Jednorazowe":
                return [t for t in tasks if not t.recurrence_rule]
            if value == "Nawyki":
                return [t for t in tasks if t.recurrence_rule]
        elif category == "Data":
            today = datetime.now().date()
            if value == "Dziś":
                return [t for t in tasks if t.due_date.date() == today]
            if value == "Ten tydzień":
                week_end = today + timedelta(days=7)
                return [t for t in tasks if today <= t.due_date.date() <= week_end]
        return tasks

    def _rebuild_content(self):
        for child in self.scroll.container.winfo_children():
            child.destroy()
        self.task_rows = []
        self.build_content(self.scroll.container)
        if self._last_width is not None:
            self.update_fonts(self._last_width, self._last_height)

    def _add_task_row(self, container, task):
        row = TaskRow(container, task, repository=self.repository,
                      style=self.TASK_STYLE,
                      on_toggle=self.on_toggle_task,
                      on_menu=self.on_task_menu)
        row.pack(fill="x", padx=CONTENT_PADX, pady=self.TASK_GAP_PADY)
        self.task_rows.append(row)
        if self._last_width is not None:
            canvas_w = max(100, self._last_width - 20)
            row_width = max(100, canvas_w - 2 * CONTENT_PADX - 4)
            row.update_fonts(row_width, self._last_height)
        return row

    def update_fonts(self, width, height):
        super().update_fonts(width, height)
        self._last_width = width
        self._last_height = height

        # Deterministyczna kalkulacja szerokosci eliminuje problemy
        # ze skalowaniem wystepujace przy zmianie zakladek.
        canvas_w = max(100, width - 20)
        row_width = max(100, canvas_w - 2 * CONTENT_PADX - 4)

        for row in self.task_rows:
            row.update_fonts(row_width, height)

        if self.calendar_widget is not None:
            try:
                self.scroll._canvas.update_idletasks()
                canvas_h = self.scroll._canvas.winfo_height()
                if canvas_h > 50:
                    self.calendar_widget.update_layout(width, canvas_h)
            except Exception:
                pass