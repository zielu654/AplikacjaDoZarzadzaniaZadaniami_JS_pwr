"""
Pakiet testow funkcjonalnych - sprawdza ze nowa architektura widokow dziala
jak ustalilismy.
"""
import sys
import tkinter as tk

import main_app as app

from front.theme import PRIORYTETOWE_COLOR
from front.sidebar import (
    Sidebar, KEY_DZIS, KEY_WSZYSTKIE, KEY_NAWYKI,
    KEY_PRIORYTETOWE, KEY_CATEGORY_PREFIX,
)
from front.task_row import TaskRow
from front.components import (
    IconButton, CheckCircle, DropdownButton, ContextMenuButton, ScrollableContent,
)
from front.views import View, ListView, NawykiView, WszystkieView, DzisView
from front.right_panel import RightPanel
from front.header_toolbar import Header, Toolbar
from fake_data import FakeTaskRepository, TaskRepository


errors = []
def check(label, condition):
    status = "OK" if condition else "FAIL"
    if not condition:
        errors.append(label)
    print(f"  [{status}] {label}")


print("=== 1. Hierarchia klas View ===")
check("NawykiView dziedziczy ListView", issubclass(NawykiView, ListView))
check("WszystkieView dziedziczy ListView", issubclass(WszystkieView, ListView))
check("DzisView dziedziczy ListView", issubclass(DzisView, ListView))
check("ListView dziedziczy View", issubclass(ListView, View))


print("\n=== 2. Class attributes konkretnych views ===")
check("NawykiView.TITLE == 'Nawyki'", NawykiView.TITLE == "Nawyki")
check("WszystkieView.TITLE == 'Wszystkie'", WszystkieView.TITLE == "Wszystkie")
check("DzisView.TITLE == 'Dziś'", DzisView.TITLE == "Dziś")
check("NawykiView TASK_STYLE == 'outlined'", NawykiView.TASK_STYLE == "outlined")
check("DzisView TASK_STYLE == 'outlined' (tak jak reszta)", DzisView.TASK_STYLE == "outlined")
check("DzisView.SORT_OPTIONS is None (brak Sortuj)", DzisView.SORT_OPTIONS is None)
check("NawykiView.SORT_OPTIONS = Data/Priorytet/Kategorie",
      NawykiView.SORT_OPTIONS == ["Data", "Priorytet", "Kategorie"])
check("WszystkieView ma 'Rodzaj' w FILTER_CATEGORIES",
      "Rodzaj" in WszystkieView.FILTER_CATEGORIES)
check("DzisView nie ma 'Data' w FILTER_CATEGORIES (i tak dzisiejsza)",
      "Data" not in DzisView.FILTER_CATEGORIES)
check("Wszystkie views maja DISPLAY_MODE_OPTIONS",
      all(v.DISPLAY_MODE_OPTIONS for v in [NawykiView, WszystkieView, DzisView]))


print("\n=== 3. Repository pattern ===")
repo = FakeTaskRepository()
check("FakeTaskRepository dziedziczy TaskRepository",
      issubclass(FakeTaskRepository, TaskRepository))
check("get_habits zwraca tylko cykliczne",
      all(t.recurrence_rule for t in repo.get_habits()))
check("get_all filtruje is_deleted",
      all(not t.is_deleted for t in repo.get_all()))


print("\n=== 4. get_tasks() - kazdy view zwraca rozne zadania ===")
# Tworzymy testowe instancje (bez place'owania) - sprawdzamy ze get_tasks dziala
nawyki_v = NawykiView(app.window, repository=repo)
wszystkie_v = WszystkieView(app.window, repository=repo)
dzis_v = DzisView(app.window, repository=repo)

check("NawykiView.get_tasks() == repo.get_habits()",
      [t.id for t in nawyki_v.get_tasks()] == [t.id for t in repo.get_habits()])
check("WszystkieView.get_tasks() == repo.get_all()",
      [t.id for t in wszystkie_v.get_tasks()] == [t.id for t in repo.get_all()])
check("DzisView.get_tasks() filtruje po dacie (lista, moze byc pusta)",
      isinstance(dzis_v.get_tasks(), list))
# Wszystkie zadania w DzisView maja today date
from datetime import datetime
today = datetime.now().date()
check("DzisView.get_tasks() - kazde zadanie ma due_date.date() == today",
      all(t.due_date.date() == today for t in dzis_v.get_tasks()))

nawyki_v.destroy()
wszystkie_v.destroy()
dzis_v.destroy()


print("\n=== 5. Aktualnie wyswietlany view (start = NawykiView) ===")
check("app.view istnieje", app.view is not None)
check("app.view jest NawykiView (default)", isinstance(app.view, NawykiView))
check("app.right_panel istnieje", app.right_panel is not None)
check("app.right_panel jest RightPanel", isinstance(app.right_panel, RightPanel))


print("\n=== 6. ViewSwitcher - przelaczanie views ===")
app.on_sidebar_select(KEY_WSZYSTKIE)
app.window.update_idletasks()
check("Po kliku 'wszystkie' -> WszystkieView", isinstance(app.view, WszystkieView))
check("Aktualny title 'Wszystkie'", app.view.header.cget("text") == "Wszystkie")

app.on_sidebar_select(KEY_DZIS)
app.window.update_idletasks()
check("Po kliku 'dzis' -> DzisView", isinstance(app.view, DzisView))
check("DzisView Sortuj BRAK w toolbarze (toolbar.lbl_sortuj is None)",
      app.view.toolbar.lbl_sortuj is None)
check("DzisView ma '+' w toolbarze", app.view.toolbar.lbl_plus is not None)

app.on_sidebar_select(KEY_NAWYKI)
app.window.update_idletasks()
check("Po kliku 'nawyki' -> NawykiView", isinstance(app.view, NawykiView))
check("Nawyki ma Sortuj w toolbarze", app.view.toolbar.lbl_sortuj is not None)

# Klik na te sama klase (Nawyki) - nie powinien re-tworzyc view (optymalizacja)
old_view = app.view
app.on_sidebar_select(KEY_NAWYKI)
check("Klik na ta sama klase = nie podmienia view (optymalizacja)",
      app.view is old_view)


print("\n=== 7. RightPanel - sparowany z aktualnym view ===")
# Po przelaczeniu na Wszystkie, RightPanel powinien miec 5 opcji Filtruj (z Rodzaj)
app.on_sidebar_select(KEY_WSZYSTKIE)
app.window.update_idletasks()
check("Po Wszystkie - Filtruj ma 5 opcji (z Rodzaj)",
      len(app.right_panel.lbl_filtruj._opts) == 5)

# Po przelaczeniu na Dzis, RightPanel ma 4 opcje Filtruj (bez Data)
app.on_sidebar_select(KEY_DZIS)
app.window.update_idletasks()
check("Po Dzis - Filtruj ma 4 opcje (bez Data)",
      len(app.right_panel.lbl_filtruj._opts) == 4)

app.on_sidebar_select(KEY_NAWYKI)
app.window.update_idletasks()


print("\n=== 8. Sidebar struktura ===")
entries = app.sidebar.entries
kinds = [e["kind"] for e in entries]
check("Pierwszy wpis: 'dodaj' (Dodaj zadanie)", kinds[0] == "dodaj")
items_text = [e["widget"].cget("text") for e in entries if e["kind"] == "item"]
check("Pozycje nawigacyjne: Dziś, Wszystkie, Nawyki",
      items_text == ["Dziś", "Wszystkie", "Nawyki"])
color_rows = [e for e in entries if e["kind"] == "color"]
color_texts = [e["widget"].label.cget("text") for e in color_rows]
check("Pierwsza kolorowa: Priorytetowe (hardcoded)",
      color_texts[0] == "Priorytetowe")
check("Priorytetowe jest pierwszym wpisem kolorowym",
      color_texts[0] == "Priorytetowe")


print("\n=== 9. Pozycje w toolbarze (Sortuj+ po prawej View) ===")
app.window.geometry('1440x900')
app.window.update_idletasks()
app.window.update()
app.right_panel.sync_with_view()
app.window.update_idletasks()

sortuj_x = app.view.toolbar.lbl_sortuj.winfo_rootx()
plus_x = app.view.toolbar.lbl_plus.winfo_rootx()
view_left_x = app.view.winfo_rootx()
view_center_x = view_left_x + app.view.winfo_width() // 2
check(f"Sortuj (x={sortuj_x}) po prawej polowie View (center={view_center_x})",
      sortuj_x > view_center_x)
check(f"Plus (x={plus_x}) jeszcze bardziej w prawo niz Sortuj",
      plus_x > sortuj_x)


print("\n=== 10. Pozycje w RightPanel (Filtruj na wys. Sortuj, Widok wyzej) ===")
sortuj_center_y = app.view.toolbar.lbl_sortuj.winfo_rooty() + app.view.toolbar.lbl_sortuj.winfo_height() // 2
filtruj_center_y = app.right_panel.lbl_filtruj.winfo_rooty() + app.right_panel.lbl_filtruj.winfo_height() // 2
check(f"Filtruj center_y={filtruj_center_y} == Sortuj center_y={sortuj_center_y} (tol 10px)",
      abs(filtruj_center_y - sortuj_center_y) < 10)

widok_y = app.right_panel.lbl_widok.winfo_rooty()
header_center_y = app.view.header.winfo_rooty() + app.view.header.winfo_height() // 2
widok_center_y = widok_y + app.right_panel.lbl_widok.winfo_height() // 2
check(f"Widok center_y={widok_center_y} == Header center_y={header_center_y} (tol 10px)",
      abs(widok_center_y - header_center_y) < 10)


print("\n=== 11. Task ma atrybut is_done (ukonczone) + toggle dziala ===")
row = app.view.task_rows[0]
before = row.task.is_done
row.toggle_done()
check("is_done przelaczyl sie", row.task.is_done != before)
check("CheckCircle._done == task.is_done", row.checkbox._done == row.task.is_done)
row.toggle_done()
check("Powrot do stanu", row.task.is_done == before)


print("\n=== 11b. Sortowanie - apply_sort faktycznie zmienia kolejnosc ===")
app.on_sidebar_select(KEY_WSZYSTKIE)
app.window.update_idletasks()

# Sortuj po dacie - sprawdzamy ze due_date rosnie
app.view.apply_sort("Data")
app.window.update_idletasks()
dates = [r.task.due_date for r in app.view.task_rows]
check("apply_sort('Data') - daty rosnaco", dates == sorted(dates))

# Sortuj po priorytecie - priorytetowe na poczatku
app.view.apply_sort("Priorytet")
app.window.update_idletasks()
n_priority_first = 0
for r in app.view.task_rows:
    if r.task.priority:
        n_priority_first += 1
    else:
        break
total_priority = sum(1 for r in app.view.task_rows if r.task.priority)
check(f"apply_sort('Priorytet') - priorytetowe na gorze ({n_priority_first}/{total_priority})",
      n_priority_first == total_priority)


print("\n=== 11c. Filtrowanie - apply_filter faktycznie filtruje liste ===")
# Wyzeruj stan
app.view.filter_state = {}
app.view.sort_option = None
app.view._rebuild_content()
total = len(app.view.task_rows)

# Filtruj Status=Zrealizowane
app.view.apply_filter("Status", "Zrealizowane")
app.window.update_idletasks()
done_count = len(app.view.task_rows)
check("apply_filter('Status', 'Zrealizowane') - tylko ukonczone",
      all(r.task.is_done for r in app.view.task_rows))

# Wyzeruj filtr
app.view.apply_filter("Status", "Wszystkie")
app.window.update_idletasks()
check("apply_filter('Status', 'Wszystkie') - filtr usuniety, pelna lista",
      len(app.view.task_rows) == total)

# Wiele filtrow na raz
app.view.apply_filter("Priorytet", "Tak")
app.view.apply_filter("Status", "Nieukończone")
app.window.update_idletasks()
check("filter_state ma 2 wpisy (Priorytet + Status)",
      len(app.view.filter_state) == 2)
check("apply_filter laczy filtry - tylko priorytetowe i nieukonczone",
      all(r.task.priority and not r.task.is_done for r in app.view.task_rows))

# Filtr Rodzaj=Nawyki (tylko cykliczne)
app.view.filter_state = {}
app.view._rebuild_content()
app.view.apply_filter("Rodzaj", "Nawyki")
app.window.update_idletasks()
check("apply_filter('Rodzaj', 'Nawyki') - tylko cykliczne",
      all(r.task.recurrence_rule for r in app.view.task_rows))

# Reset i powrot do Nawykow
app.view.filter_state = {}
app.view.sort_option = None
app.view._rebuild_content()
app.on_sidebar_select(KEY_NAWYKI)
app.window.update_idletasks()


print("\n=== 11d. Callback z menu (parent, option) faktycznie wywoluje apply ===")
# Symulacja klika na "Sortuj > Priorytet" - wywoluje callback z _opts
for label, cb in app.view.toolbar.lbl_sortuj._opts:
    if label == "Priorytet":
        cb()  # callback to lambda(): on_view_sort(None, "Priorytet") -> view.apply_sort("Priorytet")
        break
check("Klik Sortuj > Priorytet -> view.sort_option = 'Priorytet'",
      app.view.sort_option == "Priorytet")

# Symulacja klika na "Filtruj > Status > Nieukończone"
for label, sub in app.right_panel.lbl_filtruj._opts:
    if label == "Status":
        for sub_label, sub_cb in sub:
            if sub_label == "Nieukończone":
                sub_cb()  # callback to lambda(): on_view_filter("Status", "Nieukończone")
                break
        break
check("Klik Filtruj > Status > Nieukończone -> filter_state['Status'] = 'Nieukończone'",
      app.view.filter_state.get("Status") == "Nieukończone")

# Symulacja klika na "Widok > Kalendarz > Tygodniowy" (parent='Kalendarz')
for label, sub in app.right_panel.lbl_widok._opts:
    if label == "Kalendarz":
        for sub_label, sub_cb in sub:
            if sub_label == "Tygodniowy":
                sub_cb()  # callback to lambda(): on_display_mode_select("Kalendarz", "Tygodniowy")
                break
        break
check("Klik Widok > Kalendarz > Tygodniowy -> display_mode = 'Kalendarz - Tygodniowy'",
      app.view.display_mode == "Kalendarz - Tygodniowy")

# Reset stanu zeby kolejne testy mialy czysty stan
app.view.sort_option = None
app.view.filter_state = {}
app.view._rebuild_content()


print("\n=== 12. Submenu w Widoku - Kalendarz ma Tygodniowy/Miesieczny ===")
view_opts = app.right_panel.lbl_widok._opts
kalendarz = view_opts[1]
check("Druga opcja 'Kalendarz' ma submenu",
      kalendarz[0] == "Kalendarz" and isinstance(kalendarz[1], list))
check("Kalendarz submenu: Tygodniowy + Miesieczny",
      [opt[0] for opt in kalendarz[1]] == ["Tygodniowy", "Miesięczny"])


print("\n=== 13. Override koloru ramki dla priority=True ===")
for row in app.view.task_rows:
    if row.task.priority:
        check(f"'{row.task.title}' priority=True -> czerwona ramka",
              row.accent_color == PRIORYTETOWE_COLOR)
        break


print("\n=== 14. Responsywnosc - menu_btn miesci sie w roznych szerokosciach ===")
for geo in ['700x500', '950x700', '1280x800', '1440x900', '1512x982', '1920x1080', '2560x1440']:
    app.window.geometry(geo)
    app.window.update_idletasks()
    app.window.update()
    # Po samym update niektore after_idle moga nie zdazyc - wymuszamy update_fonts
    # bezposrednio na aktualnym view, zeby task_rows na pewno mialy aktualne wraplength
    app.view.update_fonts(app.view.winfo_width(), app.view.winfo_height())
    app.window.update_idletasks()
    app.window.update()
    bad = []
    for row in app.view.task_rows:
        menu_right = row.menu_btn.winfo_x() + row.menu_btn.winfo_width()
        inner_w = row.inner.winfo_width()
        if menu_right > inner_w + 2:
            bad.append(f"{row.task.title}:+{menu_right-inner_w}")
    check(f"{geo}: menu_btn miesci sie", not bad)


print("\n=== 15. minsize blokuje zmniejszanie ponizej 700px ===")
app.window.geometry('300x300')
app.window.update_idletasks()
check("minsize zachowany", app.window.winfo_width() >= 700)


print("\n=== 16. TimeBlocks tylko w DzisView ===")
app.window.geometry('1280x900')
app.window.update_idletasks()

# Nawyki nie ma TimeBlocks
app.on_sidebar_select(KEY_NAWYKI)
app.window.update_idletasks()
nawyki_opts = [o[0] for o in app.right_panel.lbl_widok._opts]
check(f"Nawyki Widok bez TimeBlocks ({nawyki_opts})",
      "TimeBlocks" not in nawyki_opts)

# Wszystkie nie ma TimeBlocks
app.on_sidebar_select(KEY_WSZYSTKIE)
app.window.update_idletasks()
wszystkie_opts = [o[0] for o in app.right_panel.lbl_widok._opts]
check(f"Wszystkie Widok bez TimeBlocks ({wszystkie_opts})",
      "TimeBlocks" not in wszystkie_opts)

# DzisView MA TimeBlocks
app.on_sidebar_select(KEY_DZIS)
app.window.update_idletasks()
dzis_opts = [o[0] for o in app.right_panel.lbl_widok._opts]
check(f"DzisView Widok z TimeBlocks ({dzis_opts})",
      "TimeBlocks" in dzis_opts)


print("\n=== 17. Przelaczanie Lista <-> TimeBlocks w DzisView ===")
# Default Lista - task_rows powinny istniec
check("DzisView start: display_mode == 'Lista'",
      app.view.display_mode == "Lista")
n_tasks_lista = len(app.view.task_rows)
check(f"DzisView Lista: task_rows={n_tasks_lista} > 0",
      n_tasks_lista > 0)
check("DzisView Lista: time_blocks_widget is None",
      app.view.time_blocks_widget is None)

# Przelacz na TimeBlocks
for label, cb in app.right_panel.lbl_widok._opts:
    if label == "TimeBlocks":
        cb()
        break
app.window.update_idletasks()
check("Po kliku TimeBlocks: display_mode == 'TimeBlocks'",
      app.view.display_mode == "TimeBlocks")
check("Po TimeBlocks: task_rows pusty",
      len(app.view.task_rows) == 0)
check("Po TimeBlocks: time_blocks_widget istnieje",
      app.view.time_blocks_widget is not None)
n_blocks = len(app.view.time_blocks_widget.time_blocks)
check(f"TimeBlocks renderuje bloki ({n_blocks} blokow dla zadan na dzis)",
      n_blocks > 0)

# Przelacz z powrotem na Liste - TimeBlocks znika
for label, cb in app.right_panel.lbl_widok._opts:
    if label == "Lista":
        cb()
        break
app.window.update_idletasks()
check("Po powrocie do Lista: display_mode == 'Lista'",
      app.view.display_mode == "Lista")
check("Po powrocie: time_blocks_widget znowu None",
      app.view.time_blocks_widget is None)
check(f"Po powrocie: task_rows ({len(app.view.task_rows)}) == start ({n_tasks_lista})",
      len(app.view.task_rows) == n_tasks_lista)


print("\n=== 18. Repository CRUD - add/update/delete task i category ===")
from fake_data import Task as _Task, Category as _Category
from datetime import datetime as _dt

_test_repo = FakeTaskRepository()
_n_before = len(_test_repo.get_all())
_new = _Task(id=0, title="_TEST_add", description="", due_date=_dt.now(),
              is_done=False, priority=False, category_id=None,
              created_at=_dt.now(), modified_at=_dt.now())
_added = _test_repo.add_task(_new)
check("add_task zwraca task z id != 0", _added.id != 0)
check("add_task zwiekszyl liczbe zadan", len(_test_repo.get_all()) == _n_before + 1)

_added.title = "_TEST_updated"
_test_repo.update_task(_added)
_fresh = next(t for t in _test_repo.get_all() if t.id == _added.id)
check("update_task zmienil title", _fresh.title == "_TEST_updated")

_test_repo.delete_task(_added.id)
_after_del = [t for t in _test_repo.get_all() if t.id == _added.id]
check("delete_task: soft delete - is_deleted=True, znikniete z get_all()",
      len(_after_del) == 0)

_n_cats = len(_test_repo.get_categories())
_new_cat = _Category(id=0, name="_TEST_cat", color="#FF00FF")
_added_cat = _test_repo.add_category(_new_cat)
check("add_category zwraca z id != 0", _added_cat.id != 0)
check("add_category zwiekszyl liczbe kategorii", len(_test_repo.get_categories()) == _n_cats + 1)

_test_repo.delete_category(_added_cat.id)
check("delete_category usuwa kategorie",
      len(_test_repo.get_categories()) == _n_cats)


print("\n=== 19. Menu kontekstowe ma 2 opcje: Edytuj / Usun ===")
# Najpierw vrocmy do Nawykow
app.on_sidebar_select(KEY_NAWYKI)
app.window.update_idletasks()

# TaskRow menu_btn ma options [(Edytuj, ...), (Usun, ...)]
task_row_opts = [o[0] for o in app.view.task_rows[0].menu_btn._opts]
check(f"TaskRow menu: {task_row_opts}",
      task_row_opts == ["Edytuj", "Usuń"])

# Sidebar color row menu (Priorytetowe ma category=None, weź pierwszą realna)
color_rows = [e for e in app.sidebar.entries if e["kind"] == "color"]
kategoria_row = next((cr for cr in color_rows if cr["widget"].label.cget("text") != "Priorytetowe"), None)
if kategoria_row:
    cat_opts = [o[0] for o in kategoria_row["widget"].menu_btn._opts]
    check(f"Sidebar kategoria menu: {cat_opts}",
          cat_opts == ["Edytuj", "Usuń"])


print("\n=== 20. ChipToggle widget - toggle on/off ===")
from front.components import ChipToggle as _Chip
_chip_root = tk.Toplevel(app.window)
_chip = _Chip(_chip_root, text="Test", initial=False)
check("ChipToggle.is_on() startuje False", _chip.is_on() is False)
_chip.toggle()
check("po toggle - is_on() True", _chip.is_on() is True)
_chip.set(False)
check("po set(False) - is_on() False", _chip.is_on() is False)
_chip_root.destroy()


print("\n=== 21. Sidebar Kategorie header ma '+' i klikalny label ===")
from front.sidebar import SidebarKategorieHeader
_kat_entries = [e for e in app.sidebar.entries
                if isinstance(e["widget"], SidebarKategorieHeader)]
check("Sidebar ma 1 SidebarKategorieHeader", len(_kat_entries) == 1)
if _kat_entries:
    _kat = _kat_entries[0]["widget"]
    check("Header label = 'Kategorie'", _kat.label.cget("text") == "Kategorie")
    check("Header ma '+' obok", _kat.btn_plus.cget("text") == "+")
    check("Header.on_add jest callable", callable(_kat.on_add))


print("\n=== 22. Kalendarz Tygodniowy + Miesieczny dziala dla wszystkich views ===")
from front.views.calendar import WeekCalendarContent, MonthCalendarContent
app.on_sidebar_select(KEY_WSZYSTKIE)
app.window.update_idletasks()

# Przelacz na Tygodniowy
for label, sub in app.right_panel.lbl_widok._opts:
    if label == "Kalendarz":
        for s_label, s_cb in sub:
            if s_label == "Tygodniowy":
                s_cb()
                break
        break
app.window.update_idletasks()
check("Wszystkie + Tygodniowy: calendar_widget to WeekCalendarContent",
      isinstance(app.view.calendar_widget, WeekCalendarContent))
check("Wszystkie + Tygodniowy: task_rows pusty (Lista off)",
      len(app.view.task_rows) == 0)

# Miesieczny
for label, sub in app.right_panel.lbl_widok._opts:
    if label == "Kalendarz":
        for s_label, s_cb in sub:
            if s_label == "Miesięczny":
                s_cb()
                break
        break
app.window.update_idletasks()
check("Wszystkie + Miesięczny: calendar_widget to MonthCalendarContent",
      isinstance(app.view.calendar_widget, MonthCalendarContent))
check("Miesięczny ma 42 komorki (6 wierszy x 7 dni)",
      len(app.view.calendar_widget.cells) == 42)

# Powrot do Listy - kalendarz znika
for label, cb in app.right_panel.lbl_widok._opts:
    if label == "Lista":
        cb()
        break
app.window.update_idletasks()
check("Po powrocie do Lista: calendar_widget = None",
      app.view.calendar_widget is None)
check("Po powrocie do Lista: task_rows znow ma elementy",
      len(app.view.task_rows) > 0)

# Sprawdz w NawykiView tez (wszystkie views obsluguja kalendarz)
app.on_sidebar_select(KEY_NAWYKI)
app.window.update_idletasks()
for label, sub in app.right_panel.lbl_widok._opts:
    if label == "Kalendarz":
        for s_label, s_cb in sub:
            if s_label == "Tygodniowy":
                s_cb()
                break
        break
app.window.update_idletasks()
check("NawykiView tez obsluguje Tygodniowy",
      isinstance(app.view.calendar_widget, WeekCalendarContent))

# Reset do Lista
for label, cb in app.right_panel.lbl_widok._opts:
    if label == "Lista":
        cb()
        break
app.window.update_idletasks()


print("\n" + "=" * 50)
if errors:
    print(f"BLEDOW: {len(errors)}")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)
else:
    print("WSZYSTKO OK - 0 bledow")