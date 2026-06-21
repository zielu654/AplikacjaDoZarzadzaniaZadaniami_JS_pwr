"""
Glowny plik aplikacji.

Tworzy okno, Sidebar po lewej i NawykiView po prawej (jedyny dostepny widok
w tej iteracji). Klikalnosci sidebara/toolbara sa, ale callbacki sa puste
(`pass`) - to celowo, mechanika podmiany widokow i sortowania/filtrowania
przyjdzie w kolejnej iteracji.
"""

import tkinter as tk

from front.theme import BG, SEPARATOR_COLOR, LEFT_RELWIDTH, LIST_RELWIDTH
from front.sidebar import Sidebar
from front.views.nawyki import NawykiView
from fake_data import FakeTaskRepository


# proporcje window: 30% sidebar, 50% widok, 20% margines z prawej
SEPARATOR_RELX = LEFT_RELWIDTH


# ============================================================
# Repozytorium
# ============================================================
repository = FakeTaskRepository()


# ============================================================
# Okno glowne
# ============================================================
window = tk.Tk()
window.title("Lista zadań")
window.geometry("950x600")
window.configure(bg=BG)
# Ponizej ~680px szerokosci panel widoku za waski, layout sie rozjezdza.
window.minsize(700, 400)

# body trzyma cala tresc - sidebar + separator + widok
body = tk.Frame(window, bg=BG)
body.pack(side="top", fill="both", expand=True)


# ============================================================
# Callbacki (na razie wszystkie puste)
# ============================================================

def on_dodaj_zadanie():
    """Klik na 'Dodaj zadanie' / '+' w sidebarze.
    TODO: otworzyc dialog tworzenia nowego zadania."""
    pass


def on_sidebar_select(key):
    """Klik na pozycje nawigacyjna w sidebarze.
    TODO: podmienic aktywny widok. Na razie nic."""
    pass


def on_category_menu(category):
    """Klik na '...' przy kategorii w sidebarze (lub Priorytetowe gdy category=None).
    TODO: pokazac dialog Edytuj/Usun/Dodaj zadanie do kategorii."""
    pass


def on_view_add():
    """Klik na '+' w toolbarze widoku."""
    pass


def on_view_sort(option):
    """Wybor opcji sortowania w widoku."""
    pass


def on_view_filter(option):
    """Wybor opcji filtrowania w widoku."""
    pass


def on_task_toggle(task):
    """Klik checkboxa na zadaniu (toggle done).
    Stan zostal juz zmieniony w TaskRow. TODO: zapisac do repozytorium."""
    pass


def on_task_menu(task):
    """Klik '...' na zadaniu."""
    pass


# ============================================================
# Sidebar
# ============================================================
sidebar = Sidebar(
    body,
    repository=repository,
    on_dodaj_zadanie=on_dodaj_zadanie,
    on_select=on_sidebar_select,
    on_category_menu=on_category_menu,
)
sidebar.place(x=0, y=0, relwidth=LEFT_RELWIDTH, relheight=1)


# ============================================================
# Separator - cienka linia na granicy sidebar/widok
# ============================================================
separator = tk.Frame(body, bg=SEPARATOR_COLOR, width=2)
separator.place(relx=SEPARATOR_RELX, x=-1, y=0, relheight=1)


# ============================================================
# Widok glowny (NawykiView)
# ============================================================
view = NawykiView(
    body,
    repository=repository,
    on_add=on_view_add,
    on_sort=on_view_sort,
    on_filter=on_view_filter,
    on_toggle_task=on_task_toggle,
    on_task_menu=on_task_menu,
)
view.place(relx=LEFT_RELWIDTH, y=0, relwidth=LIST_RELWIDTH, relheight=1)


# ============================================================
# Responsywnosc - rozprowadza zmiany szerokosci do sidebara i widoku
# ============================================================
def update_responsive_layout(event):
    if event.widget is body:
        sidebar.update_fonts(int(event.width * LEFT_RELWIDTH), event.height)
        # widok dostaje update_fonts() przez wlasny bind <Configure> wewnatrz View,
        # bo i tak jego rozmiar zmienia sie w gore za body. Nie ma potrzeby wolac
        # tutaj jeszcze raz.


body.bind("<Configure>", update_responsive_layout)


if __name__ == "__main__":
    window.mainloop()
