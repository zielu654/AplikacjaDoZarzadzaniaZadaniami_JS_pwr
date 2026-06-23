"""
View - abstrakcyjna klasa bazowa dla wszystkich widokow.
ListView - widok z lista zadan (Nawyki, Wszystkie, Kategoria, Priorytetowe).

Architektura widoku:
  +------------------------------------+
  |  Header (tytul)        [STALY]     |
  +------------------------------------+
  |  Toolbar               [STALY]     |
  +------------------------------------+
  |  ScrollableContent                 |
  |  +------------------------------+  |
  |  |  build_content() wstawia tu  |  |
  |  |  swoje widgety               |  |
  |  +------------------------------+  |
  +------------------------------------+

Header i Toolbar siedza POZA scrollem, wiec nie ruszaja sie przy
scrollowaniu listy.

Podklasy implementuja `build_content(container)` - dostaja gotowy Frame
do wypelnienia. Konfiguracja toolbara (jakie opcje sort/filter/view, czy
ma "+", jaki tytul) idzie do `__init__` super klasy.
"""

import tkinter as tk

from front.theme import BG
from front.header_toolbar import Header, Toolbar
from front.components import ScrollableContent
from front.task_row import TaskRow

# Padding wewnatrz scrollowalnego kontentu
CONTENT_PADX = 20
CONTENT_PADY = 10


# ============================================================
# View - baza
# ============================================================


class View(tk.Frame):
    """Abstrakcyjna baza dla widokow.

    Konstruktor:
      parent       - rodzic Tk
      title        - tytul widoku (Header)
      toolbar_*    - wszystkie opcje przekazywane do Toolbar()
                     (sort_options, filter_options, view_options, show_add,
                      on_sort, on_filter, on_view, on_add)

    Podklasa implementuje:
      build_content(container) - wypelnia self.scroll.container swoimi widgetami

    Wola sie ja DOPIERO po super().__init__(), bo tam tworzy sie scroll.
    """

    def __init__(self, parent, title, **toolbar_kwargs):
        super().__init__(parent, bg=BG)

        self.header = Header(self, title)
        self.header.pack(side="top", pady=(Header.HEADER_TOP_PADY, Header.HEADER_BOT_PADY))

        self.toolbar = Toolbar(self, **toolbar_kwargs)
        self.toolbar.pack(side="top", fill="x", padx=Toolbar.LIST_PADX, pady=(0, Toolbar.TOOLBAR_BOT_PADY))

        self.scroll = ScrollableContent(self, bg=BG)
        self.scroll.pack(side="top", fill="both", expand=True)

        # Podklasa wypelnia kontent
        self.build_content(self.scroll.container)

        # Bind responsywnosci wewnatrz widoku - propaguje do header/toolbar
        # i (w ListView) do kazdego TaskRow.
        self.bind("<Configure>", self._on_configure)

    # -------- do implementacji w podklasach --------

    def build_content(self, container):
        """Wypelnia container (Frame w srodku scrolla) swoimi widgetami.
        Domyslna implementacja jest pusta - podklasa ma to nadpisac."""
        pass

    # -------- responsywnosc --------

    def _on_configure(self, event):
        if event.widget is self:
            self.update_fonts(event.width, event.height)

    def update_fonts(self, width, height):
        self.header.update_fonts(width, height)
        self.toolbar.update_fonts(width, height)


# ============================================================
# ListView - widok z lista zadan
# ============================================================


class ListView(View):
    """Widok wyswietlajacy liste zadan jako TaskRow.

    Konstruktor (oprocz tych z View):
      tasks            - lista obiektow Task do wyswietlenia
      repository       - TaskRepository (potrzebne TaskRow do koloru kategorii)
      task_style       - 'outlined' (default) lub 'filled'
      on_toggle_task   - callback(task) gdy user klika checkbox
      on_task_menu     - callback(task) gdy user klika "..." na zadaniu

    Sortowanie/filtrowanie listy zadan na razie NIE jest implementowane
    (klikalnosc Sortuj/Filtruj jest ale callbacki sa pass).
    """

    TASK_GAP_PADY = 10

    def __init__(
        self,
        parent,
        title,
        tasks,
        repository,
        task_style="outlined",
        on_toggle_task=None,
        on_task_menu=None,
        **toolbar_kwargs,
    ):
        # Trzymamy parametry wierszy ZANIM wolamy super (bo build_content
        # bedzie zawolane w super().__init__() i potrzebuje tych pol).
        self.tasks = tasks
        self.repository = repository
        self.task_style = task_style
        self.on_toggle_task = on_toggle_task or (lambda t: None)
        self.on_task_menu = on_task_menu or (lambda t: None)
        self.task_rows = []

        # Zapamietana szerokosc/wysokosc do skalowania nowych wierszy
        # (gdyby ktos pozniej zawolal set_tasks)
        self._last_width = None
        self._last_height = None

        super().__init__(parent, title, **toolbar_kwargs)

    def build_content(self, container):
        for task in self.tasks:
            self._add_task_row(container, task)

    def _add_task_row(self, container, task):
        row = TaskRow(
            container,
            task,
            repository=self.repository,
            style=self.task_style,
            on_toggle=self.on_toggle_task,
            on_menu=self.on_task_menu,
        )
        row.pack(fill="x", padx=CONTENT_PADX, pady=self.TASK_GAP_PADY)
        self.task_rows.append(row)
        # Jesli mamy juz znana szerokosc - przelicz fonty nowego wiersza od razu
        if self._last_width is not None:
            row_width = max(100, self._last_width - 2 * CONTENT_PADX - 4)
            row.update_fonts(row_width, self._last_height)
        return row

    def set_tasks(self, tasks):
        """Wymien liste zadan - usuwa istniejace wiersze i tworzy nowe."""
        for row in self.task_rows:
            row.destroy()
        self.task_rows = []
        self.tasks = tasks
        for task in tasks:
            self._add_task_row(self.scroll.container, task)

    def update_fonts(self, width, height):
        super().update_fonts(width, height)
        self._last_width = width
        self._last_height = height

        # Realna szerokosc wewnatrz wiersza:
        # panel - 2*padding_listy - 4px obwodki wiersza (z padx=2 dwustronnie)
        row_width = max(100, width - 2 * CONTENT_PADX - 4)
        for row in self.task_rows:
            row.update_fonts(row_width, height)
