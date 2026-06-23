"""
TaskRow - jeden wiersz zadania na liscie. Bierze obiekt Task i sam z niego
wyciaga wszystko potrzebne do wyswietlenia.

Style wizualne:
  - 'outlined' (default): kolorowa OBWODKA + biale tlo (uzywane w Nawykach,
    Kategoriach, Wszystkie - lista typu plana)
  - 'filled': pelne kolorowe TLO + bialy tekst (uzywane w widoku Dzis -
    timeline, bo tam zadania sa jak bloki czasu).

Kolor ramki/tla:
  - jesli task.priority=True -> czerwony (PRIORYTETOWE_COLOR), niezaleznie
    od kategorii
  - inaczej -> kolor kategorii z repozytorium
  - jesli brak kategorii -> DEFAULT_BORDER
"""

import re
import tkinter as tk

from front.theme import (
    BG,
    FG,
    INFO_FG,
    DONE_FG,
    DEFAULT_BORDER,
    PRIORYTETOWE_COLOR,
    ON_COLOR_FG,
    SIZE_TASK_TITLE,
    SIZE_TASK_INFO,
    TASK_TITLE_SCALE,
    TASK_INFO_SCALE,
    TASK_CHECKBOX_SCALE,
    scaled,
)
from front.components import CheckCircle, ContextMenuButton, make_font

# ============================================================
# IKONY i parametry layoutu
# ============================================================
ICON_RECURRENCE = "\u21ba"  # ↺

TASK_CHECKBOX_RESERVE = 64  # px na checkbox + padding
TASK_MENU_RESERVE = 65  # px na "..." + prawy padding
TASK_TITLE_MIN_PX = 100  # absolutne minimum tytulu w px
MIN_INFO_RESERVE = 80  # minimalna szerokosc info (zeby tytul nie zjadl wszystkiego)

# wykrywa "HH:MM-HH:MM" na koncu stringa
_TIME_RANGE_RE = re.compile(r"\d{1,2}:\d{2}-\d{1,2}:\d{2}$")


# ============================================================
# Helpery formatowania Task -> string (do UI)
# ============================================================


def _parse_recurrence(rule):
    """'co pon 18:00-19:00' -> ('co pon', '18:00 - 19:00')"""
    if not rule:
        return None, None
    match = _TIME_RANGE_RE.search(rule)
    if not match:
        return rule.strip(), None
    cycle = rule[: match.start()].strip()
    start, end = match.group(0).split("-", 1)
    return cycle, f"{start} - {end}"


def _format_task_info(task):
    """Tekst po prawej tytulu: '↺ co pon  20:00 - 21:15' lub samo 'HH:MM'."""
    cycle, time_range = _parse_recurrence(task.recurrence_rule)
    prefix = f"{ICON_RECURRENCE} {cycle}    " if cycle else ""
    if not time_range:
        if task.due_date.hour == 0 and task.due_date.minute == 0:
            time_range = ""
        else:
            time_range = task.due_date.strftime("%H:%M")
    return prefix + time_range


def _accent_color_for_task(task, repository):
    """Kolor ramki/tla zadania.
    Priorytet ma pierwszenstwo nad kategoria - zadania priorytetowe sa
    czerwone niezaleznie od tego, do ktorej kategorii naleza."""
    if task.priority:
        return PRIORYTETOWE_COLOR
    cat = repository.get_category(task.category_id)
    return cat.color if cat else DEFAULT_BORDER


# ============================================================
# TaskRow
# ============================================================


class TaskRow(tk.Frame):
    """Jeden wiersz listy zadan.

    Sklad wizualny: [ramka 2px] -> [tlo (biale/kolorowe)] -> [O  Tytul  ↺ info  ...]
    """

    def __init__(self, parent, task, repository, style="outlined", on_toggle=None, on_menu=None):
        self.task = task
        self.repository = repository
        self.style = style  # 'outlined' lub 'filled'
        self.on_toggle = on_toggle or (lambda t: None)
        self.on_menu = on_menu or (lambda t: None)
        self.accent_color = _accent_color_for_task(task, repository)

        # Layout zewnetrzny: kolorowy Frame + bialy Frame wewnatrz (outlined),
        # albo jeden kolorowy Frame (filled).
        if style == "filled":
            outer_bg = self.accent_color
            inner_bg = self.accent_color
            text_fg = ON_COLOR_FG
            info_fg = ON_COLOR_FG
        else:  # outlined
            outer_bg = self.accent_color
            inner_bg = BG
            text_fg = FG
            info_fg = INFO_FG

        super().__init__(parent, bg=outer_bg, padx=2, pady=2)

        inner = tk.Frame(self, bg=inner_bg)
        inner.pack(fill="both", expand=True)
        inner.columnconfigure(1, weight=1, minsize=110)
        self.inner = inner
        self._inner_bg = inner_bg
        self._text_fg = text_fg
        self._info_fg = info_fg

        # Fonty (skalowane pozniej przez update_fonts)
        self.title_font = make_font(SIZE_TASK_TITLE)
        self.info_font = make_font(SIZE_TASK_INFO)

        # Checkbox - rysowany kolko/ptaszek
        self.checkbox = CheckCircle(inner, on_click=self.toggle_done, bg=inner_bg)
        self.checkbox.grid(row=0, column=0, padx=(12, 10), pady=12)

        # Tytul - z wraplength, wiec zawija sie zamiast ucinac
        self.lbl_title = tk.Label(
            inner,
            text=task.title,
            font=self.title_font,
            bg=inner_bg,
            fg=text_fg,
            anchor="w",
            justify="left",
            wraplength=200,
        )
        self.lbl_title.grid(row=0, column=1, sticky="w")

        # Info (powtarzalnosc + godziny)
        self.lbl_info = tk.Label(
            inner,
            text=_format_task_info(task),
            font=self.info_font,
            bg=inner_bg,
            fg=info_fg,
            wraplength=150,
            justify="left",
        )
        self.lbl_info.grid(row=0, column=2, padx=(10, 6))

        # Menu kontekstowe "..." (Edytuj/Dodaj/Usun). Wszystkie opcje na razie
        # wolaja ten sam callback on_menu(task) - logika rozdzielania (czy klik
        # to byl "Edytuj" czy "Usun") przyjdzie pozniej, na razie sygnalizujemy
        # tylko ze user klikal cos w menu kontekstowym tego zadania.
        self.menu_btn = ContextMenuButton(
            inner,
            font=self.info_font,
            bg=inner_bg,
            fg=text_fg,
            options=[
                ("Edytuj", lambda: self.on_menu(self.task)),
                ("Dodaj", lambda: self.on_menu(self.task)),
                ("Usun", lambda: self.on_menu(self.task)),
            ],
        )
        self.menu_btn.grid(row=0, column=3, padx=(0, 20))

        # Stan poczatkowy
        if task.is_done:
            self._apply_done_style()
        else:
            self.checkbox.set_state(done=False, accent_color=self.accent_color)

    # -------- toggle --------

    def toggle_done(self):
        self.task.is_done = not self.task.is_done
        if self.task.is_done:
            self._apply_done_style()
        else:
            self._apply_undone_style()
        self.on_toggle(self.task)

    def _apply_done_style(self):
        self.checkbox.set_state(done=True, accent_color=self.accent_color)
        self.title_font.config(overstrike=1)
        self.lbl_title.config(fg=DONE_FG if self.style == "outlined" else ON_COLOR_FG)

    def _apply_undone_style(self):
        self.checkbox.set_state(done=False, accent_color=self.accent_color)
        self.title_font.config(overstrike=0)
        self.lbl_title.config(fg=self._text_fg)

    # -------- responsywnosc --------

    def update_fonts(self, width, height=None):
        self.title_font.config(size=scaled(width, TASK_TITLE_SCALE))
        self.info_font.config(size=scaled(width, TASK_INFO_SCALE))
        self.checkbox.set_size(scaled(width, TASK_CHECKBOX_SCALE))

        # Tytul: tyle ile FAKTYCZNIE potrzebuje (font.measure), ograniczone
        # przez to co zostaje po zarezerwowaniu checkboxa+menu+info_floor.
        available = max(TASK_TITLE_MIN_PX, width - TASK_CHECKBOX_RESERVE - TASK_MENU_RESERVE - MIN_INFO_RESERVE)
        natural = self.title_font.measure(self.task.title)
        title_min = max(TASK_TITLE_MIN_PX, min(natural + 10, available))
        self.inner.columnconfigure(1, minsize=title_min)
        self.lbl_title.config(wraplength=title_min)

        # Info: tyle, ile zostaje po wszystkim (z drobnym zapasem bezpieczenstwa).
        wraplength_info = max(80, width - TASK_CHECKBOX_RESERVE - title_min - TASK_MENU_RESERVE - 10)
        self.lbl_info.config(wraplength=wraplength_info)
