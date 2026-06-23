"""
PriorytetoweView - widok zadań priorytetowych (priority=True).
"""

from front.views.base import ListView


class PriorytetoweView(ListView):
    TITLE = "Priorytetowe"
    SORT_OPTIONS = ["Data", "Kategorie"]
    FILTER_CATEGORIES = ["Kategoria", "Rodzaj", "Status", "Data"]
    TASK_STYLE = "outlined"

    def get_tasks(self):
        return [t for t in self.repository.get_all() if t.priority]