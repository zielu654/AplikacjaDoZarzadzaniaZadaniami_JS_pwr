"""
WszystkieView - widok wszystkich zadan (poza usunietymi).

Rozni sie od Nawykow:
  - get_tasks() - bez filtrowania (wszystkie zadania)
  - FILTER_OPTIONS ma dodatkowo "Rodzaj" (Jednorazowe/Nawyki) - wg szkicow
"""

from front.views.base import ListView


class WszystkieView(ListView):
    TITLE = "Wszystkie"
    SORT_OPTIONS = ["Data", "Priorytet", "Kategorie"]
    FILTER_CATEGORIES = ["Priorytet", "Kategoria", "Rodzaj", "Status", "Data"]
    TASK_STYLE = "outlined"

    def get_tasks(self):
        return self.repository.get_all()