"""
KategoriaView - widok zadań dla konkretnej kategorii.
"""

from front.views.base import ListView


class KategoriaView(ListView):
    TITLE = "Kategoria"
    SORT_OPTIONS = ["Data", "Priorytet"]
    FILTER_CATEGORIES = ["Priorytet", "Rodzaj", "Status", "Data"]
    TASK_STYLE = "outlined"

    def __init__(self, *args, category_id=None, **kwargs):
        self.category_id = category_id
        super().__init__(*args, **kwargs)

        # Nadpisz tytuł w Headerze na nazwę klikniętej kategorii
        cat = self.repository.get_category(self.category_id)
        if cat:
            self.header.set_text(cat.name)

    def get_tasks(self):
        return [t for t in self.repository.get_all() if t.category_id == self.category_id]