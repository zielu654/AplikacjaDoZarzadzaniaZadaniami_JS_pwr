"""
TimeBlocksContent - widget timeline z godzinami i zadaniami jako kolorowe bloki.

Uzywany w DzisView w display_mode='TimeBlocks'. Struktura:
  +---+----------------------+
  |  7|                      |
  |  8|                      |
  |  9|  [Zadanie 1       ]  |   <- blok pozycjonowany wg godziny task
  | ..|                      |
  | 22|                      |
  +---+----------------------+

Wysokosc kazdej godziny (ROW_HEIGHT) liczona DYNAMICZNIE z dostepnej wysokosci:
  row_height = canvas_height // (HOUR_END - HOUR_START + 1)
Dzieki temu cala doba (7-22) miesci sie bez scrollowania niezaleznie od
rozmiaru okna. Aplikacja wola update_layout(view_width, canvas_height) po
update_fonts View - patrz DzisView.update_fonts.

Szerokosc lewej kolumny godzin tez dynamicznie - z font.measure("22:00") +
padding, zeby przy wiekszym foncie labelki sie nie urywaly.
"""

import re
import tkinter as tk
from datetime import timedelta

from front.theme import (
    BG, INFO_FG, ON_COLOR_FG, DEFAULT_BORDER, PRIORYTETOWE_COLOR, DONE_FG,
)
from front.components import CheckCircle, ContextMenuButton, make_font


# Zakres godzin do pokazania (od 7:00 do 22:00 wlacznie - 16 godzin)
HOUR_START = 7
HOUR_END = 22

# Minimum wysokosci 1 godziny (gdy okno bardzo male)
MIN_ROW_HEIGHT = 24

# Padding bloku od kolumny godzin / prawej krawedzi
BLOCK_LEFT_PAD = 5
BLOCK_RIGHT_PAD = 10

# regex do parsowania "HH:MM-HH:MM" w recurrence_rule
_TIME_RANGE_RE = re.compile(r"(\d{1,2}):(\d{2})-(\d{1,2}):(\d{2})")


def _task_time_range(task):
    """Zwraca (start_dt, end_dt) - czas rozpoczecia i zakonczenia zadania.
    Jesli recurrence_rule zawiera zakres godzin, parsuje go.
    Inaczej end = start + 30 min (default)."""
    start = task.due_date
    if task.recurrence_rule:
        m = _TIME_RANGE_RE.search(task.recurrence_rule)
        if m:
            sh, sm, eh, em = (int(g) for g in m.groups())
            start = task.due_date.replace(hour=sh, minute=sm,
                                           second=0, microsecond=0)
            end = task.due_date.replace(hour=eh, minute=em,
                                         second=0, microsecond=0)
            return start, end
    return start, start + timedelta(minutes=30)


def _accent_color_for_task(task, repository):
    """Kolor bloku - czerwony jesli priority, inaczej kategoria."""
    if task.priority:
        return PRIORYTETOWE_COLOR
    cat = repository.get_category(task.category_id)
    return cat.color if cat else DEFAULT_BORDER


# ============================================================
# TimeBlock - pojedynczy kolorowy pasek zadania
# ============================================================

class TimeBlock(tk.Frame):
    """Pojedynczy blok w timeline - kolorowy pasek z checkboxem, tytulem i menu."""

    def __init__(self, parent, task, repository, on_toggle=None, on_menu=None):
        self.task = task
        self.repository = repository
        self.on_toggle = on_toggle or (lambda t: None)
        # on_menu(task, action) - action in {"edit", "delete"}
        self.on_menu = on_menu or (lambda t, a: None)
        self.accent_color = _accent_color_for_task(task, repository)

        # highlightthickness=1 + bg dziala jako 1px biala ramka wokol bloku.
        # Bez niej dwa kolejne bloki tego samego koloru ze stykajacymi sie
        # godzinami zlewaja sie wizualnie. Z nia - widac wyrazne 2px (1+1)
        # rozdzielenie nawet gdy obok siebie.
        bg = DONE_FG if task.is_done else self.accent_color
        super().__init__(parent, bg=bg,
                         highlightthickness=1, highlightbackground="white")

        self.title_font = make_font(14)

        # Checkbox - bialy na kolorowym tle (on_dark_bg=True)
        self.checkbox = CheckCircle(self, on_click=self.toggle_done, bg=bg)
        self.checkbox.set_size(22)
        self.checkbox.set_state(done=task.is_done,
                                accent_color=self.accent_color,
                                on_dark_bg=True)
        self.checkbox.pack(side="left", padx=(10, 8))

        # Tytul - bialy tekst
        self.lbl_title = tk.Label(self, text=task.title, font=self.title_font,
                                   bg=bg, fg=ON_COLOR_FG,
                                   anchor="w")
        self.lbl_title.pack(side="left", fill="x", expand=True)

        # ••• menu - bialy na kolorowym tle. Opcje Edytuj/Usun z action dispatch.
        self.menu_btn = ContextMenuButton(
            self, font=self.title_font,
            bg=bg, fg=ON_COLOR_FG,
            options=[
                ("Podgląd", lambda: self.on_menu(self.task, "preview")),
                ("Edytuj",  lambda: self.on_menu(self.task, "edit")),
                ("Usuń",    lambda: self.on_menu(self.task, "delete")),
            ],
        )
        self.menu_btn.pack(side="right", padx=(0, 12))

        if task.is_done:
            self.title_font.config(overstrike=1)

    def toggle_done(self):
        self.task.is_done = not self.task.is_done
        # Recalc bg - szary jesli done, kolor kategorii jesli nie.
        new_bg = DONE_FG if self.task.is_done else self.accent_color
        self.config(bg=new_bg)
        self.checkbox.config(bg=new_bg)
        self.lbl_title.config(bg=new_bg)
        self.menu_btn.config(bg=new_bg)
        self.checkbox.set_state(done=self.task.is_done,
                                accent_color=self.accent_color,
                                on_dark_bg=True)
        self.title_font.config(overstrike=1 if self.task.is_done else 0)
        self.on_toggle(self.task)


# ============================================================
# TimeBlocksContent - kontener timeline
# ============================================================

class TimeBlocksContent(tk.Frame):
    """Timeline z godzinami po lewej i blokami zadan po prawej.

    Wewnatrz - bialy obszar z ramka. Wysokosci wierszy godzin i pozycje
    blokow liczone dynamicznie w _relayout(w, h) zeby calosc miescila sie
    w dostepnej przestrzeni bez scrollowania.
    """

    def __init__(self, parent, tasks, repository,
                 on_toggle=None, on_menu=None):
        super().__init__(parent, bg=BG)
        self.tasks = tasks
        self.repository = repository
        self.on_toggle = on_toggle
        self.on_menu = on_menu

        # Ramka dookola obszaru TimeBlocks
        self.frame = tk.Frame(self, bg=BG, bd=1, relief="solid")
        self.frame.pack(fill="both", expand=True, padx=10, pady=3)

        # Wewnetrzny area - tu beda labelki godzin i bloki, place'owane w _relayout
        self.area = tk.Frame(self.frame, bg=BG)
        self.area.pack(fill="both", expand=True, padx=8, pady=4)

        self.hours_font = make_font(13)

        # Twórz wszystkie labelki godzin BEZ pozycji (_relayout je rozmiesci)
        self.hour_labels = []
        for h in range(HOUR_START, HOUR_END + 1):
            lbl = tk.Label(self.area, text=f"{h:02d}:00",
                            font=self.hours_font, bg=BG, fg=INFO_FG)
            self.hour_labels.append((lbl, h))

        # Twórz bloki BEZ pozycji
        self.time_blocks = []
        for task in self.tasks:
            block = TimeBlock(self.area, task, repository=self.repository,
                                on_toggle=self.on_toggle, on_menu=self.on_menu)
            self.time_blocks.append((block, task))

        # Auto-relayout przy kazdej zmianie rozmiaru area
        self.area.bind("<Configure>", self._on_area_resize)

    def _on_area_resize(self, event):
        if event.width > 10 and event.height > 10:
            self._relayout(event.width, event.height)

    def _relayout(self, w, h):
        """Rozmiesc labelki godzin i bloki zadan w dostepnej przestrzeni (w x h)."""
        total_hours = HOUR_END - HOUR_START + 1
        # Wysokosc 1 godziny - dynamiczna, by zmiescic wszystkie 16h w dostepnej h
        row_height = max(MIN_ROW_HEIGHT, h // total_hours)

        # Szerokosc kolumny godzin - z font.measure("22:00") (najszerszy mozliwy
        # tekst godziny) + padding. Padding 13 (zamiast 20) - na zyczenie usera
        # zeby blok byl blizej kolumny godzin i godziny nie sprawialy wrazenia
        # ucinanych.
        label_w = self.hours_font.measure("22:00")
        hour_col_w = label_w + 13

        # Pozycjonuj labelki godzin (anchor="nw" - gorna-lewa, y to linia godziny)
        # x=7 zamiast 10 - mniejszy lewy padding, labelki bardziej w lewo
        for lbl, hour in self.hour_labels:
            y = (hour - HOUR_START) * row_height
            lbl.place(x=7, y=y, anchor="nw")

        # Pozycjonuj bloki zadan
        for block, task in self.time_blocks:
            start, end = _task_time_range(task)
            start_min = (start.hour - HOUR_START) * 60 + start.minute
            end_min = (end.hour - HOUR_START) * 60 + end.minute

            max_min = total_hours * 60
            if end_min <= 0 or start_min >= max_min:
                block.place_forget()
                continue

            start_min = max(0, start_min)
            end_min = min(max_min, end_min)

            y = int(start_min * row_height / 60)
            block_h = max(22, int((end_min - start_min) * row_height / 60))

            # relwidth=1.0 + width=-X: blok ma szerokosc parent minus rezerwacja
            # (kolumna godzin + paddingi)
            block.place(x=hour_col_w + BLOCK_LEFT_PAD, y=y,
                         relwidth=1.0,
                         width=-(hour_col_w + BLOCK_LEFT_PAD + BLOCK_RIGHT_PAD),
                         height=block_h)

    def update_layout(self, view_width, canvas_height):
        """Aktualizuj fonty i wymus wysokosc kontenera = canvas_height.

        Wolane z DzisView.update_fonts. canvas_height to dostepna przestrzen
        ScrollableContent._canvas - wysokosc do ktorej musimy zmiescic
        16 godzin (zeby uniknac scrollowania).
        """
        # Wymuszamy wysokosc kontenera. Buffer 18px uwzglednia pady=5 (z pack
        # w DzisView) + ramka + paddingi wewnetrzne. Po zmniejszeniu paddingow
        # bufor 30px byl za duzy i niepotrzebnie ucinal jedna godzine na dole.
        target_h = max(MIN_ROW_HEIGHT * (HOUR_END - HOUR_START + 1),
                       canvas_height - 18)
        self.config(height=target_h)
        self.pack_propagate(False)

        # Fonty - skalowanie z szerokoscia View, wieksze cap niz w poprzedniej
        # wersji (10-14, 11-16 bylo za male, szczegolnie w fullscreen).
        h_size = max(12, min(18, int(view_width * 0.022)))
        t_size = max(14, min(20, int(view_width * 0.028)))
        self.hours_font.config(size=h_size)
        for block, _task in self.time_blocks:
            block.title_font.config(size=t_size)

        # Po zmianie fontu - relayout (hour_col_w zalezne od fontu)
        self.update_idletasks()
        aw = self.area.winfo_width()
        ah = self.area.winfo_height()
        if aw > 10 and ah > 10:
            self._relayout(aw, ah)