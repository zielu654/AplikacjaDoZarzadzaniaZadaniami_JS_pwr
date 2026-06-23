"""
Widoki kalendarzowe: tygodniowy i miesieczny.

WeekCalendarContent  - 7 kolumn (Pn-Nd) z timeline godzin po lewej, zadania
                       jako kolorowe bloki w odpowiedniej kolumnie+godzinie.
MonthCalendarContent - grid 7x6 dni miesiaca, kazda komorka pokazuje numer
                       dnia i krotkie etykiety zadan tego dnia.

Oba widgety obsluguja update_layout(view_width, canvas_height) - dynamicznie
przeliczaja layout zeby wszystko miescilo sie bez scrollowania.

Aplikacja woluje calendar_widget.update_layout(...) z View.update_fonts.
"""

import tkinter as tk
from datetime import datetime, date, timedelta
import calendar as _cal_module

from front.theme import (
    BG, FG, INFO_FG, ON_COLOR_FG, DEFAULT_BORDER, PRIORYTETOWE_COLOR, DONE_FG,
)
from front.components import make_font
from front.views.time_blocks import (
    HOUR_START, HOUR_END, MIN_ROW_HEIGHT,
    _task_time_range, _accent_color_for_task,
)


DAY_NAMES_PL_SHORT = ["Pn", "Wt", "Śr", "Cz", "Pt", "So", "Nd"]
MONTH_NAMES_PL = [
    "Styczeń", "Luty", "Marzec", "Kwiecień", "Maj", "Czerwiec",
    "Lipiec", "Sierpień", "Wrzesień", "Październik", "Listopad", "Grudzień",
]


def _fit_text(text, font, max_width, max_lines=1):
    """Skraca tekst zeby zmiescil sie w max_width * max_lines, dodajac '...'.

    Dla max_lines=1: prosty truncate single-line.
    Dla max_lines>1: greedy word-wrap, ostatnia widoczna linia konczy '...'."""
    if max_width < 10:
        return text  # za waskie zeby cokolwiek zmierzyc sensownie

    if max_lines <= 1:
        if font.measure(text) <= max_width:
            return text
        while text and font.measure(text + "…") > max_width:
            text = text[:-1]
        return (text + "…") if text else "…"

    words = text.split()
    if not words:
        return text
    lines = []
    cur = ""
    for w in words:
        cand = (cur + " " + w) if cur else w
        if font.measure(cand) <= max_width:
            cur = cand
        else:
            if cur:
                lines.append(cur)
                cur = w
            else:
                # pojedyncze slowo szersze niz max_width - i tak je zaczynamy
                cur = w
            if len(lines) >= max_lines:
                # juz mamy max linii, ale jeszcze jest tekst - skroc ostatnia
                last = lines[max_lines - 1]
                while last and font.measure(last + "…") > max_width:
                    last = last[:-1]
                lines[max_lines - 1] = (last.rstrip() + "…") if last else "…"
                return "\n".join(lines[:max_lines])
    if cur:
        lines.append(cur)
    if len(lines) > max_lines:
        last = lines[max_lines - 1]
        while last and font.measure(last + "…") > max_width:
            last = last[:-1]
        lines[max_lines - 1] = (last.rstrip() + "…") if last else "…"
        return "\n".join(lines[:max_lines])
    return "\n".join(lines)


# ============================================================
# Helpery - obliczanie zakresow tygodnia/miesiaca
# ============================================================

def _week_bounds(d):
    """Zwraca (monday, sunday) dla tygodnia zawierajacego date d.
    Tydzien zaczyna sie w poniedzialek (zgodnie z polskim/ISO standardem)."""
    monday = d - timedelta(days=d.weekday())
    sunday = monday + timedelta(days=6)
    return monday, sunday


def _month_grid(year, month):
    """Zwraca liste 6 wierszy x 7 dni (date objects) dla siatki kalendarza
    miesiacu. Pierwszy wiersz moze zawierac konce poprzedniego miesiaca,
    ostatni - poczatek nastepnego."""
    cal = _cal_module.Calendar(firstweekday=0)  # 0 = poniedzialek
    weeks = []
    for week in cal.monthdatescalendar(year, month):
        weeks.append(week)
    # Wymuszamy 6 wierszy zeby wysokosc byla stala niezaleznie od miesiaca
    while len(weeks) < 6:
        last = weeks[-1][-1]
        nxt = [last + timedelta(days=i + 1) for i in range(7)]
        weeks.append(nxt)
    return weeks[:6]


# ============================================================
# WeekCalendarContent - timeline 7 dni
# ============================================================

class WeekCalendarContent(tk.Frame):
    """7 kolumn (Pn-Nd), godziny po lewej (HOUR_START-HOUR_END), zadania
    jako kolorowe bloki pozycjonowane wg dnia tygodnia + godziny."""

    HOUR_COL_W_BASE = 50   # bazowa szerokosc kolumny godzin (skalowana z fontem)
    HEADER_H = 32          # wysokosc paska z nazwami dni
    BLOCK_X_PAD = 2        # padding bloku od krawedzi kolumny dnia

    def __init__(self, parent, tasks, repository, anchor_date=None,
                 on_toggle=None, on_menu=None):
        super().__init__(parent, bg=BG)
        self.tasks = tasks
        self.repository = repository
        self.on_toggle = on_toggle or (lambda t: None)
        self.on_menu = on_menu or (lambda t, a: None)
        self.anchor_date = anchor_date or date.today()

        # Wyznacz tydzien (Pon-Nd)
        self.monday, self.sunday = _week_bounds(self.anchor_date)

        # Ramka dookola
        self.frame = tk.Frame(self, bg=BG, bd=1, relief="solid")
        self.frame.pack(fill="both", expand=True, padx=10, pady=3)

        # Obszar wewnetrzny
        self.area = tk.Frame(self.frame, bg=BG)
        self.area.pack(fill="both", expand=True, padx=6, pady=4)

        self.hours_font = make_font(11)
        self.day_header_font = make_font(11, weight="bold")
        self.block_font = make_font(10)

        # Naglowki dni (Pn Wt ... Nd) - place'owane w _relayout
        self.day_headers = []
        for i, name in enumerate(DAY_NAMES_PL_SHORT):
            d = self.monday + timedelta(days=i)
            text = f"{name}\n{d.day}.{d.month:02d}"
            lbl = tk.Label(self.area, text=text, font=self.day_header_font,
                            bg=BG, fg=FG, justify="center")
            self.day_headers.append((lbl, i))

        # Labelki godzin
        self.hour_labels = []
        for h in range(HOUR_START, HOUR_END + 1):
            lbl = tk.Label(self.area, text=f"{h:02d}:00",
                            font=self.hours_font, bg=BG, fg=INFO_FG)
            self.hour_labels.append((lbl, h))

        # Bloki zadan - tylko te ktore wpadaja w aktualny tydzien
        self.day_blocks = []  # (block_widget, task, day_index)
        for task in self.tasks:
            day_idx = (task.due_date.date() - self.monday).days
            if 0 <= day_idx < 7:
                block = WeekTaskBlock(self.area, task,
                                       repository=self.repository,
                                       font=self.block_font,
                                       on_toggle=self.on_toggle,
                                       on_menu=self.on_menu)
                self.day_blocks.append((block, task, day_idx))

        self.area.bind("<Configure>", self._on_area_resize)

    def _on_area_resize(self, event):
        if event.width > 10 and event.height > 10:
            self._relayout(event.width, event.height)

    def _relayout(self, w, h):
        total_hours = HOUR_END - HOUR_START + 1

        # Szerokosc kolumny godzin - skala fontu
        label_w = self.hours_font.measure("22:00")
        hour_col_w = label_w + 13

        # Szerokosc 1 kolumny dnia
        day_col_w = max(60, (w - hour_col_w) // 7)

        # Wysokosc dostepna na timeline (po odjeciu paska naglowkow dni)
        timeline_h = h - self.HEADER_H
        row_height = max(MIN_ROW_HEIGHT // 2, timeline_h // total_hours)

        # Naglowki dni - na samej gorze
        for lbl, i in self.day_headers:
            x = hour_col_w + i * day_col_w + day_col_w // 2
            lbl.place(x=x, y=2, anchor="n")

        # Labelki godzin (pod naglowkiem dni)
        for lbl, hour in self.hour_labels:
            y = self.HEADER_H + (hour - HOUR_START) * row_height
            lbl.place(x=7, y=y, anchor="nw")

        # Bloki zadan
        for block, task, day_idx in self.day_blocks:
            start, end = _task_time_range(task)
            start_min = (start.hour - HOUR_START) * 60 + start.minute
            end_min = (end.hour - HOUR_START) * 60 + end.minute
            max_min = total_hours * 60
            if end_min <= 0 or start_min >= max_min:
                block.place_forget()
                continue
            start_min = max(0, start_min)
            end_min = min(max_min, end_min)

            x = hour_col_w + day_idx * day_col_w + self.BLOCK_X_PAD
            y = self.HEADER_H + int(start_min * row_height / 60)
            block_w = max(20, day_col_w - 2 * self.BLOCK_X_PAD)
            block_h = max(18, int((end_min - start_min) * row_height / 60))
            block.place(x=x, y=y, width=block_w, height=block_h)
            # Dopasuj tytul: oblicz ile linii sie miesci, skroc tekst '...' jesli za dlugi
            block.fit_label(block_w, block_h)

    def update_layout(self, view_width, canvas_height):
        target_h = max(MIN_ROW_HEIGHT * (HOUR_END - HOUR_START + 1) + self.HEADER_H,
                       canvas_height - 18)
        self.config(height=target_h)
        self.pack_propagate(False)

        # Fonty - skala z widokiem
        h_size = max(10, min(14, int(view_width * 0.016)))
        d_size = max(10, min(15, int(view_width * 0.017)))
        b_size = max(9, min(13, int(view_width * 0.014)))
        self.hours_font.config(size=h_size)
        self.day_header_font.config(size=d_size)
        self.block_font.config(size=b_size)

        self.update_idletasks()
        aw = self.area.winfo_width()
        ah = self.area.winfo_height()
        if aw > 10 and ah > 10:
            self._relayout(aw, ah)


class WeekTaskBlock(tk.Frame):
    """Pojedynczy blok w widoku tygodniowym - kompaktowy, bez checkboxa,
    tylko tytul. Klik = otworz menu (edit/delete).

    Sam blok ma 1px biala ramke (highlightthickness) by sasiadujace zadania
    tego samego koloru nie zlewaly sie wizualnie."""

    def __init__(self, parent, task, repository, font, on_toggle=None, on_menu=None):
        self.task = task
        self.repository = repository
        self.on_toggle = on_toggle or (lambda t: None)
        self.on_menu = on_menu or (lambda t, a: None)
        self.accent_color = _accent_color_for_task(task, repository)
        # Zachowujemy oryginalny tytul - przy resize obetniemy do nowej szerokosci
        self._full_title = task.title

        bg = DONE_FG if task.is_done else self.accent_color
        super().__init__(parent, bg=bg, cursor="hand2",
                         highlightthickness=1, highlightbackground="white")
        self.title_font = font

        self.lbl = tk.Label(self, text=task.title, font=font,
                             bg=bg, fg=ON_COLOR_FG,
                             anchor="nw", padx=4, pady=2,
                             justify="left")
        self.lbl.pack(fill="both", expand=True)
        if task.is_done:
            self.title_font.config(overstrike=1)

        # Klik = otworz menu kontekstowe (Edytuj/Usun)
        self.bind("<Button-1>", self._show_menu)
        self.lbl.bind("<Button-1>", self._show_menu)

    def fit_label(self, block_w, block_h):
        """Sprobuj zmiescic _full_title w bloku, dodajac '...' gdy potrzeba."""
        line_h = max(self.title_font.metrics("linespace"), 12)
        avail_w = max(20, block_w - 10)   # minus padx labela
        avail_h = max(line_h, block_h - 6)
        max_lines = max(1, avail_h // line_h)
        text = _fit_text(self._full_title, self.title_font, avail_w, max_lines)
        self.lbl.config(text=text, wraplength=avail_w)

    def _show_menu(self, event):
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Podgląd", command=lambda: self.on_menu(self.task, "preview"))
        menu.add_command(label="Edytuj",  command=lambda: self.on_menu(self.task, "edit"))
        menu.add_command(label="Usuń",    command=lambda: self.on_menu(self.task, "delete"))
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()


# ============================================================
# MonthCalendarContent - siatka dni miesiaca
# ============================================================

class MonthCalendarContent(tk.Frame):
    """Klasyczny kalendarz miesieczny - 7 kolumn x 6 wierszy. Kazda komorka
    pokazuje numer dnia i do 3 najwazniejszych zadan (etykiety kolorowe).

    Dni z poprzedniego/nastepnego miesiaca - wyszarzone."""

    MONTH_LABEL_H = 28  # wysokosc paska z nazwa miesiaca
    HEADER_H = 28       # pasek z nazwami dni tygodnia (pod nazwa miesiaca)
    MIN_CELL_H = 60

    def __init__(self, parent, tasks, repository, anchor_date=None,
                 on_toggle=None, on_menu=None):
        super().__init__(parent, bg=BG)
        self.tasks = tasks
        self.repository = repository
        self.on_toggle = on_toggle or (lambda t: None)
        self.on_menu = on_menu or (lambda t, a: None)
        self.anchor_date = anchor_date or date.today()

        # Ramka dookola
        self.frame = tk.Frame(self, bg=BG, bd=1, relief="solid")
        self.frame.pack(fill="both", expand=True, padx=10, pady=3)

        self.area = tk.Frame(self.frame, bg=BG)
        self.area.pack(fill="both", expand=True, padx=4, pady=4)

        self.month_name_font = make_font(14, weight="bold")
        self.day_name_font = make_font(11, weight="bold")
        self.day_num_font = make_font(11, weight="bold")
        self.task_lbl_font = make_font(9)

        # Nagłówek - nazwa miesiąca i rok
        month_name = MONTH_NAMES_PL[self.anchor_date.month - 1]
        self.month_label = tk.Label(self.area,
                                     text=f"{month_name} {self.anchor_date.year}",
                                     font=self.month_name_font,
                                     bg=BG, fg=FG)
        self.month_label.place(relx=0.5, y=2, anchor="n")

        # Naglowki dni tygodnia (Pn Wt Sr ... Nd)
        self.day_name_labels = []
        for i, name in enumerate(DAY_NAMES_PL_SHORT):
            lbl = tk.Label(self.area, text=name, font=self.day_name_font,
                            bg=BG, fg=INFO_FG)
            self.day_name_labels.append((lbl, i))

        # Siatka komorek (6 x 7)
        self.month_grid = _month_grid(self.anchor_date.year, self.anchor_date.month)
        self.cells = []  # lista (cell_frame, day_date, day_num_label, [task_labels])
        for row in range(6):
            for col in range(7):
                d = self.month_grid[row][col]
                cell = tk.Frame(self.area, bg="white", bd=1, relief="solid")

                is_current_month = (d.month == self.anchor_date.month)
                num_fg = FG if is_current_month else "#BBBBBB"

                num_lbl = tk.Label(cell, text=str(d.day),
                                    font=self.day_num_font,
                                    bg="white", fg=num_fg,
                                    anchor="nw", padx=4, pady=2)
                num_lbl.pack(side="top", anchor="nw", fill="x")

                # Etykiety zadan dla tego dnia (do 3)
                tasks_today = [t for t in self.tasks if t.due_date.date() == d]
                task_lbls = []
                for t in tasks_today[:3]:
                    accent = _accent_color_for_task(t, self.repository)
                    bg = DONE_FG if t.is_done else accent
                    # highlightthickness=1 + biala highlightbackground = 1px biala
                    # ramka, dzieki temu sasiadujace etykiety nie zlewaja sie.
                    tl = tk.Label(cell, text=t.title,
                                    font=self.task_lbl_font,
                                    bg=bg, fg=ON_COLOR_FG,
                                    anchor="w", padx=4, pady=1,
                                    wraplength=120, justify="left",
                                    cursor="hand2",
                                    highlightthickness=1,
                                    highlightbackground="white")
                    tl.task = t
                    tl._full_title = t.title  # do re-truncate przy resize
                    tl.bind("<Button-1>", self._make_task_clicker(t))
                    tl.pack(side="top", fill="x", padx=2, pady=1)
                    task_lbls.append(tl)

                if len(tasks_today) > 3:
                    more = tk.Label(cell, text=f"+{len(tasks_today) - 3}",
                                     font=self.task_lbl_font,
                                     bg="white", fg=INFO_FG, padx=4)
                    more.pack(side="top", anchor="w")

                self.cells.append((cell, d, num_lbl, task_lbls, is_current_month))

        self.area.bind("<Configure>", self._on_area_resize)

    def _make_task_clicker(self, task):
        def on_click(event):
            menu = tk.Menu(self, tearoff=0)
            menu.add_command(label="Podgląd",
                              command=lambda: self.on_menu(task, "preview"))
            menu.add_command(label="Edytuj",
                              command=lambda: self.on_menu(task, "edit"))
            menu.add_command(label="Usuń",
                              command=lambda: self.on_menu(task, "delete"))
            try:
                menu.tk_popup(event.x_root, event.y_root)
            finally:
                menu.grab_release()
        return on_click

    def _on_area_resize(self, event):
        if event.width > 10 and event.height > 10:
            self._relayout(event.width, event.height)

    def _relayout(self, w, h):
        col_w = max(40, w // 7)
        # Wysokosc dla siatki = h - pasek miesiaca - pasek dni
        grid_h = h - self.MONTH_LABEL_H - self.HEADER_H
        cell_h = max(self.MIN_CELL_H // 2, grid_h // 6)

        # Naglowki dni tygodnia (pod paskiem miesiaca)
        for lbl, i in self.day_name_labels:
            x = i * col_w + col_w // 2
            lbl.place(x=x, y=self.MONTH_LABEL_H + 4, anchor="n")

        # Truncate task labels do rzeczywistej szerokosci komorki
        text_avail = max(20, col_w - 16)   # minus padx celli + labela
        for _cell, _d, _num_lbl, task_lbls, _is_cur in self.cells:
            for tl in task_lbls:
                tl.config(text=_fit_text(tl._full_title, self.task_lbl_font,
                                         text_avail, max_lines=1),
                          wraplength=text_avail)

        # Komorki dni
        for idx, (cell, d, _num_lbl, _task_lbls, _is_cur) in enumerate(self.cells):
            row = idx // 7
            col = idx % 7
            x = col * col_w
            y = self.MONTH_LABEL_H + self.HEADER_H + row * cell_h
            cell.place(x=x, y=y, width=col_w, height=cell_h)

    def update_layout(self, view_width, canvas_height):
        total_header = self.MONTH_LABEL_H + self.HEADER_H
        target_h = max(self.MIN_CELL_H * 6 + total_header, canvas_height - 18)
        self.config(height=target_h)
        self.pack_propagate(False)

        n_size = max(10, min(14, int(view_width * 0.016)))
        d_size = max(11, min(15, int(view_width * 0.017)))
        t_size = max(9, min(12, int(view_width * 0.013)))
        m_size = max(12, min(18, int(view_width * 0.020)))
        self.month_name_font.config(size=m_size)
        self.day_name_font.config(size=n_size)
        self.day_num_font.config(size=d_size)
        self.task_lbl_font.config(size=t_size)

        self.update_idletasks()
        aw = self.area.winfo_width()
        ah = self.area.winfo_height()
        if aw > 10 and ah > 10:
            self._relayout(aw, ah)