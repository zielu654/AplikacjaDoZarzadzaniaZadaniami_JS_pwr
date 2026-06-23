"""
NawykiView - widok listy nawykow (zadan cyklicznych, recurrence_rule != None).

Konfiguracja toolbara dla tego widoku wg szkicow:
  - Sortuj: Data, Priorytet, Kategorie
  - Filtruj: Priorytet, Kategoria, Status, Data
  - + (dodaj nawyk)

Styl wierszy: 'outlined' (kolorowa ramka, biale tlo).
"""

from front.views.base import ListView

# Opcje toolbara wg szkicow - na razie tylko stringi do wyswietlenia
SORT_OPTIONS = ["Data", "Priorytet", "Kategorie"]
FILTER_OPTIONS = ["Priorytet", "Kategoria", "Status", "Data"]


class NawykiView(ListView):
    """Widok listy nawykow.

    Konstruktor:
      parent      - rodzic Tk
      repository  - TaskRepository (wywola .get_habits() na nim)
      on_add        - klik na "+" w toolbarze
      on_sort/filter - wybor opcji z menu (na razie pass)
      on_toggle_task - klik checkboxa na zadaniu
      on_task_menu   - klik "..." na zadaniu
    """

    def __init__(
        self, parent, repository, on_add=None, on_sort=None, on_filter=None, on_toggle_task=None, on_task_menu=None
    ):
        tasks = repository.get_habits()
        super().__init__(
            parent,
            title="Nawyki",
            tasks=tasks,
            repository=repository,
            task_style="outlined",
            on_toggle_task=on_toggle_task,
            on_task_menu=on_task_menu,
            # toolbar
            sort_options=SORT_OPTIONS,
            filter_options=FILTER_OPTIONS,
            show_add=True,
            on_sort=on_sort,
            on_filter=on_filter,
            on_add=on_add,
        )
