"""
NawykiView - widok listy nawykow (zadania cykliczne, recurrence_rule != None).
"""

from front.views.base import ListView


class NawykiView(ListView):
    TITLE = "Nawyki"
    SORT_OPTIONS = ["Data", "Priorytet", "Kategorie"]
    FILTER_CATEGORIES = ["Priorytet", "Kategoria", "Status", "Data"]
    TASK_STYLE = "outlined"

    def get_tasks(self):
        return self.repository.get_habits()