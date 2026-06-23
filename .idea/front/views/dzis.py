"""
DzisView - widok zadan na dzisiaj.

Rozni sie od Nawykow/Wszystkie:
  - get_tasks() - filtruje wg dzisiejszej daty (due_date.date() == today)
  - SORT_OPTIONS = None - brak Sortuj (zadania sa naturalnie po godzinach)
  - FILTER_CATEGORIES bez "Data" (i tak tylko dzisiejsza)
  - DISPLAY_MODE_OPTIONS rozszerzone o "TimeBlocks" (oprocz Lista/Kalendarz)
  - build_content sprawdza display_mode i renderuje albo TaskRow'y (Lista)
    albo TimeBlocksContent (TimeBlocks)
"""

from datetime import datetime

from front.views.base import ListView, CONTENT_PADX
from front.views.time_blocks import TimeBlocksContent


class DzisView(ListView):
    TITLE = "Dziś"
    SORT_OPTIONS = None  # Dzis nie ma Sortuj w toolbarze (wg szkicow)
    FILTER_CATEGORIES = ["Priorytet", "Kategoria", "Rodzaj", "Status"]
    DISPLAY_MODE_OPTIONS = [
        "Lista",
        ("Kalendarz", ["Tygodniowy", "Miesięczny"]),
        "TimeBlocks",
    ]
    TASK_STYLE = "outlined"

    def __init__(self, *args, **kwargs):
        # Referencja do TimeBlocks (gdy active) - dla update_fonts
        self.time_blocks_widget = None
        super().__init__(*args, **kwargs)

    def get_tasks(self):
        today = datetime.now().date()
        return [t for t in self.repository.get_all()
                if t.due_date.date() == today]

    def build_content(self, container):
        """Override - jesli display_mode == 'TimeBlocks', buduj timeline.
        W innych przypadkach - normalna lista (ListView super)."""
        self.time_blocks_widget = None  # reset

        if self.display_mode == "TimeBlocks":
            self._build_time_blocks(container)
        else:
            # Lista (default) - ListView buduje TaskRow'y
            super().build_content(container)

    def _build_time_blocks(self, container):
        tasks = self._get_displayed_tasks()
        self.time_blocks_widget = TimeBlocksContent(
            container, tasks, repository=self.repository,
            on_toggle=self.on_toggle_task,
            on_menu=self.on_task_menu,
        )
        self.time_blocks_widget.pack(fill="both", expand=True,
                                      padx=CONTENT_PADX, pady=5)

    def update_fonts(self, width, height):
        super().update_fonts(width, height)
        # Jesli TimeBlocks jest aktywny - przekazujemy mu szerokosc + DOSTEPNA
        # WYSOKOSC (= wysokosc canvas w ScrollableContent, czyli widoczna
        # przestrzen po Header+Toolbar). Nie cala wysokosc view, bo TimeBlocks
        # ma sie zmiescic bez scrollowania.
        if self.time_blocks_widget is not None:
            try:
                self.scroll._canvas.update_idletasks()
                canvas_h = self.scroll._canvas.winfo_height()
                if canvas_h > 50:
                    self.time_blocks_widget.update_layout(width, canvas_h)
            except Exception:
                pass