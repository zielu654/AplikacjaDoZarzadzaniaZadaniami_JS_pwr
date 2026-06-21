"""
Pakiet testow funkcjonalnych - sprawdza ze nowa architektura dziala
jak ustalilismy.
"""
import sys
import tkinter as tk

# Importujemy main_app jako modul - top-level kod sie wykona ale mainloop
# nie odpali (chronione if __name__ == "__main__").
import main_app as app

from front.theme import PRIORYTETOWE_COLOR
from front.sidebar import (
    Sidebar, SidebarItem, SidebarColorRow, SidebarHeader,
    KEY_DZIS, KEY_WSZYSTKIE, KEY_NAWYKI, KEY_PRIORYTETOWE, KEY_CATEGORY_PREFIX,
)
from front.task_row import TaskRow
from front.components import IconButton, CheckCircle, DropdownButton, ContextMenuButton, ScrollableContent
from front.views.base import View, ListView
from front.views.nawyki import NawykiView, SORT_OPTIONS, FILTER_OPTIONS
from front.header_toolbar import Header, Toolbar
from fake_data import FakeTaskRepository, TaskRepository


errors = []
def check(label, condition):
    status = "OK" if condition else "FAIL"
    if not condition:
        errors.append(label)
    print(f"  [{status}] {label}")


print("=== 1. Struktura plikow i klas ===")
check("FakeTaskRepository dziedziczy po TaskRepository (wzorzec Repository)",
      issubclass(FakeTaskRepository, TaskRepository))
check("NawykiView dziedziczy po ListView", issubclass(NawykiView, ListView))
check("ListView dziedziczy po View", issubclass(ListView, View))
check("View dziedziczy po tk.Frame", issubclass(View, tk.Frame))
check("Sidebar dziedziczy po tk.Frame", issubclass(Sidebar, tk.Frame))

print("\n=== 2. Wzorzec Repository - FakeTaskRepository ma wymagane metody ===")
repo = FakeTaskRepository()
check("get_all istnieje", callable(getattr(repo, "get_all", None)))
check("get_habits istnieje", callable(getattr(repo, "get_habits", None)))
check("get_categories istnieje", callable(getattr(repo, "get_categories", None)))
check("get_category istnieje", callable(getattr(repo, "get_category", None)))
check("get_all() filtruje is_deleted=True domyslnie",
      all(not t.is_deleted for t in repo.get_all()))
check("get_all(include_deleted=True) pokazuje usuniete",
      any(t.is_deleted for t in repo.get_all(include_deleted=True)))
check("get_habits zwraca tylko zadania z recurrence_rule",
      all(t.recurrence_rule is not None for t in repo.get_habits()))
check("get_habits pomija is_deleted",
      all(not t.is_deleted for t in repo.get_habits()))


print("\n=== 3. Sidebar - struktura wg szkicow ===")
app.window.update_idletasks()
entries = app.sidebar.entries

# kolejnosc wpisow
kinds = [e["kind"] for e in entries]
check("Pierwszy wpis: 'dodaj' (Dodaj zadanie)", kinds[0] == "dodaj")

# pozycje nawigacyjne
items_text = [e["widget"].cget("text") for e in entries if e["kind"] == "item"]
check("Pozycje nawigacyjne: Dziś, Wszystkie, Nawyki",
      items_text == ["Dziś", "Wszystkie", "Nawyki"])

# naglowki
headers_text = [e["widget"].cget("text") for e in entries if e["kind"] == "header"]
check("Naglowek 'Kategorie' istnieje", "Kategorie" in headers_text)

# kolorowe pozycje
color_rows = [e for e in entries if e["kind"] == "color"]
color_texts = [e["widget"].label.cget("text") for e in color_rows]
check("Pierwsza pozycja kolorowa to 'Priorytetowe' (hardcoded)",
      color_texts[0] == "Priorytetowe")
check("Priorytetowe ma kolor PRIORYTETOWE_COLOR (czerwony stonowany)",
      color_rows[0]["widget"].cget("bg") == PRIORYTETOWE_COLOR)
check("Sa 3 kategorie z fake_data po Priorytetowe",
      color_texts[1:] == ["Kategoria 1", "Kategoria 2", "Kategoria 3"])

# kazda kolorowa pozycja ma ContextMenuButton z opcjami Edytuj/Dodaj/Usun
first_cat = color_rows[1]["widget"]
check("Kazda kategoria ma menu_btn (ContextMenuButton)",
      isinstance(first_cat.menu_btn, ContextMenuButton))


print("\n=== 4. Klikalnosci - sidebar ===")
clicks = {"dodaj": 0, "select": [], "category_menu": []}

# Tworzymy testowy sidebar z naszymi callbackami
test_sidebar = Sidebar(
    app.window,
    repository=repo,
    on_dodaj_zadanie=lambda: clicks.__setitem__("dodaj", clicks["dodaj"] + 1),
    on_select=lambda k: clicks["select"].append(k),
    on_category_menu=lambda c: clicks["category_menu"].append(c),
)
test_sidebar.update_idletasks()

# Klik na "Dodaj zadanie"
test_sidebar.entries[0]["widget"].click()
check("Klik na 'Dodaj zadanie' wola on_dodaj_zadanie", clicks["dodaj"] == 1)

# Klik na pozycje nawigacyjne
for e in test_sidebar.entries:
    if e["kind"] == "item":
        e["widget"].click()
check("Klik na pozycje nawigacyjne woluje on_select z odpowiednim kluczem",
      clicks["select"] == [KEY_DZIS, KEY_WSZYSTKIE, KEY_NAWYKI])

# Klik na nazwe kolorowej pozycji (sama nazwa, nie '...')
clicks["select"] = []
for e in test_sidebar.entries:
    if e["kind"] == "color":
        e["widget"].click()
expected_color_keys = [KEY_PRIORYTETOWE, f"{KEY_CATEGORY_PREFIX}1",
                       f"{KEY_CATEGORY_PREFIX}2", f"{KEY_CATEGORY_PREFIX}3"]
check("Klik na kolorowa pozycje woluje on_select z key 'priorytetowe' lub 'kategoria_N'",
      clicks["select"] == expected_color_keys)

# Klik na ContextMenuButton (...) na kategorii - sprawdz ze opcje wywoluja on_category_menu
clicks["category_menu"] = []
first_color_row = [e for e in test_sidebar.entries if e["kind"] == "color"][1]  # Kategoria 1
for label, callback in first_color_row["widget"].menu_btn._opts:
    callback()
check("Wszystkie 3 opcje menu (Edytuj/Dodaj/Usun) na kategorii wolaly on_category_menu",
      len(clicks["category_menu"]) == 3)

test_sidebar.destroy()


print("\n=== 5. NawykiView - konfiguracja ===")
check("Tytul widoku = 'Nawyki'",
      app.view.header.cget("text") == "Nawyki")
check("Sort options = Data/Priorytet/Kategorie",
      [opt[0] for opt in app.view.toolbar.lbl_sortuj._opts] == SORT_OPTIONS)
check("Filter options = Priorytet/Kategoria/Status/Data",
      [opt[0] for opt in app.view.toolbar.lbl_filtruj._opts] == FILTER_OPTIONS)
check("BRAK 'Widok' w toolbar (tylko Dzis ma)",
      app.view.toolbar.lbl_widok is None)
check("MA przycisk '+' w toolbar",
      app.view.toolbar.lbl_plus is not None)


print("\n=== 6. NawykiView - tylko zadania cykliczne, bez usunietych ===")
titles = [r.task.title for r in app.view.task_rows]
check("Wszystkie wiersze maja recurrence_rule",
      all(r.task.recurrence_rule for r in app.view.task_rows))
check("'Stare zadanie' (is_deleted=True) nie wystepuje",
      "Stare zadanie" not in titles)
# pomocniczo: ile sie wyswietla
print(f"  zadania w NawykiView: {titles}")
check("Mamy 4 nawyki (Poranny trening, Sprzatanie, Mycie samochodu, Codzienna medytacja)",
      set(titles) == {"Poranny trening", "Sprzatanie", "Mycie samochodu", "Codzienna medytacja"})


print("\n=== 7. Override koloru ramki dla priority=True ===")
for row in app.view.task_rows:
    if row.task.priority:
        check(f"'{row.task.title}' (priority=True) ma kolor PRIORYTETOWE_COLOR czerwony",
              row.accent_color == PRIORYTETOWE_COLOR)
        # Pomijamy reszte - mamy tylko jedno priorytetowe w nawykach
        break


print("\n=== 8. toggle_done dziala i modyfikuje obiekt Task ===")
row = app.view.task_rows[0]
state_before = row.task.is_done
row.toggle_done()
check("is_done sie przelaczyl", row.task.is_done != state_before)
check("CheckCircle._done = task.is_done", row.checkbox._done == row.task.is_done)
row.toggle_done()
check("Powrot do stanu poczatkowego", row.task.is_done == state_before)


print("\n=== 9. Klikalnosci - toolbar (Sortuj/Filtruj/+) ===")
sort_clicks = []
filter_clicks = []
add_clicks = []

test_view = NawykiView(
    app.window, repository=repo,
    on_add=lambda: add_clicks.append(True),
    on_sort=lambda opt: sort_clicks.append(opt),
    on_filter=lambda opt: filter_clicks.append(opt),
)
test_view.update_idletasks()
# Symulacja wyboru opcji - wywolujemy bezposrednio callback z _opts
# (event_generate na Menu jest skomplikowane, lepiej testowac przez callback)
for label, callback in test_view.toolbar.lbl_sortuj._opts:
    callback()
check("Sortuj opcje wywoluja on_sort z parametrami w kolejnosci",
      sort_clicks == SORT_OPTIONS)
for label, callback in test_view.toolbar.lbl_filtruj._opts:
    callback()
check("Filtruj opcje wywoluja on_filter z parametrami w kolejnosci",
      filter_clicks == FILTER_OPTIONS)
test_view.toolbar.lbl_plus.click()
check("Klik na '+' wywoluje on_add", len(add_clicks) == 1)

test_view.destroy()


print("\n=== 10. Klikalnosci - ContextMenuButton na zadaniu ===")
menu_clicks = []
test_view2 = NawykiView(
    app.window, repository=repo,
    on_task_menu=lambda task: menu_clicks.append(task),
)
test_view2.update_idletasks()
row = test_view2.task_rows[0]
# kazda opcja menu w ContextMenuButton powinna wolac on_menu(task)
for label, callback in row.menu_btn._opts:
    callback()
check("Wszystkie 3 opcje menu (Edytuj/Dodaj/Usun) wolaly on_task_menu(task)",
      len(menu_clicks) == 3 and all(t is row.task for t in menu_clicks))

test_view2.destroy()


print("\n=== 11. Responsywnosc - update_fonts dziala na roznych szerokosciach ===")
for w in (700, 1200, 1920):
    app.window.geometry(f'{w}x800')
    app.window.update_idletasks()
    # sprawdz ze pierwszy task ma sensowny rozmiar fontu
    task_font_size = app.view.task_rows[0].title_font.cget("size")
    sidebar_font_size = app.sidebar.item_font.cget("size")
    check(f"w={w}: font tytulu zadania w zakresie [16, 30] -> {task_font_size}",
          16 <= task_font_size <= 30)
    check(f"w={w}: font sidebara w zakresie [12, 36] -> {sidebar_font_size}",
          12 <= sidebar_font_size <= 36)


print("\n=== 12. minsize blokuje zmniejszanie ponizej 700px ===")
app.window.geometry('300x300')
app.window.update_idletasks()
check("Okno nie schodzi ponizej minsize (700x400)",
      app.window.winfo_width() >= 700)


print("\n" + "=" * 50)
if errors:
    print(f"BLEDOW: {len(errors)}")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)
else:
    print("WSZYSTKO OK - 0 bledow")
