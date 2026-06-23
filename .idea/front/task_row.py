"""
TaskRow - jeden wiersz zadania na liscie.

Layout poziomy (od lewej):
  [☐] [Title          ]  [date|cycle]  [time]  [⏰]  [⋯]

Pack strategy:
  Aby zagwarantowac ze menu (⋯) ZAWSZE jest widoczne (nawet w bardzo waskim
  oknie), pakujemy elementy w specjalnej kolejnosci. side="right" pakowane
  od konca PIERWSZE = najbardziej na prawo, wiec menu_btn dostaje miejsce
  jako pierwszy z prawej i nikt go nie wypchnie.

  Pack order (kolejnosc wywolania ma znaczenie!):
    1. checkbox    -> side="left"   (zawsze rezerwuje lewa krawedz)
    2. menu_btn    -> side="right"  (zawsze rezerwuje prawa krawedz)
    3. info_frame  -> side="right"  (na lewo od menu; znika w T3 jesli ciasno)
    4. lbl_title   -> side="left" + fill="x" expand=True (bierze reszte miedzy
                                  checkboxem a info_frame)

info_frame zawiera (od lewej):
  - lbl_date  : "19.06" (one-time)  LUB  "↺ co dzien" (recurring)
  - lbl_time  : "10:00"             LUB  "7:00 – 7:30"
  - lbl_clock : ⏰

Tier sizing (drop od najmniej waznego gdy okno waskie):
  T1: pelne info (data + czas + zegar)
  T2: bez zegara (data + czas)
  T3: ukryj cale info_frame (tylko checkbox + tytul + menu)

Tier wybierany w update_fonts() na podstawie inner_w vs. zmierzonych szerokosci
labelek przy AKTUALNYM foncie. Sprawdzamy najwyzszy tier ktory pozwala tytulowi
zmiescic najdluzsze slowo (zeby tkinter nie splitowal slow na znaki).
"""

import re
import tkinter as tk

from front.theme import (
    BG, FG, INFO_FG, DONE_FG, DEFAULT_BORDER, PRIORYTETOWE_COLOR, ON_COLOR_FG,
    SIZE_TASK_TITLE, SIZE_TASK_INFO,
    TASK_TITLE_SCALE, TASK_INFO_SCALE, TASK_CHECKBOX_SCALE,
    scaled,
)
from front.components import CheckCircle, ContextMenuButton, make_font


# ============================================================
# Stale
# ============================================================
ICON_RECURRENCE = "\u21ba"   # ↺
ICON_TIME       = "\u23f0"   # ⏰

_TIME_RANGE_RE = re.compile(r"\d{1,2}:\d{2}-\d{1,2}:\d{2}$")


# ============================================================
# Helpery parsowania
# ============================================================

def _parse_recurrence(rule):
    """Zwraca (cycle, start, end). None,None,None gdy brak reguly."""
    if not rule:
        return None, None, None
    match = _TIME_RANGE_RE.search(rule)
    if match:
        cycle = rule[:match.start()].strip() or None
        start, end = match.group(0).split("-", 1)
        return cycle, start, end
    return rule.strip() or None, None, None


def _accent_color_for_task(task, repository):
    if task.priority:
        return PRIORYTETOWE_COLOR
    cat = repository.get_category(task.category_id)
    return cat.color if cat else DEFAULT_BORDER


def _format_date(dt):
    """'19.06' - dzien.miesiac, bez roku."""
    return dt.strftime("%d.%m")


# ============================================================
# TaskRow
# ============================================================

class TaskRow(tk.Frame):
    def __init__(self, parent, task, repository, style="outlined",
                 on_toggle=None, on_menu=None):
        self.task = task
        self.repository = repository
        self.style = style
        self.on_toggle = on_toggle or (lambda t: None)
        self.on_menu = on_menu or (lambda t, a: None)
        self.accent_color = _accent_color_for_task(task, repository)

        super().__init__(parent, bg=BG)

        self.card_bg = "white" if style == "outlined" else self.accent_color
        self._text_fg = FG if style == "outlined" else ON_COLOR_FG
        self._info_fg = INFO_FG if style == "outlined" else ON_COLOR_FG

        # Canvas rysuje zaokraglona karte w tle
        self.canvas = tk.Canvas(self, bg=BG, highlightthickness=0)
        self.canvas.place(relwidth=1.0, relheight=1.0)

        self.inner = tk.Frame(self, bg=self.card_bg)
        self.inner.pack(fill="both", expand=True, padx=22, pady=10)

        self.title_font = make_font(SIZE_TASK_TITLE)
        self.info_font  = make_font(SIZE_TASK_INFO)

        # ---- Parse zadanie do tekstow ----
        cycle, start_t, end_t = _parse_recurrence(task.recurrence_rule)

        # Time text
        if start_t:
            self._time_text = f"{start_t} \u2013 {end_t}" if end_t else start_t
        elif task.due_date.hour != 0 or task.due_date.minute != 0:
            self._time_text = task.due_date.strftime("%H:%M")
        else:
            self._time_text = None

        # Date text
        if cycle:
            self._date_text = f"{ICON_RECURRENCE} {cycle}"
        else:
            self._date_text = _format_date(task.due_date)

        # ---- Widgety ----

        # Checkbox - left
        self.checkbox = CheckCircle(self.inner, on_click=self.toggle_done,
                                    bg=self.card_bg)

        # Menu "..." - right (zarezerwuj prawa krawedz)
        self.menu_btn = ContextMenuButton(
            self.inner, font=self.info_font,
            bg=self.card_bg, fg=self._text_fg,
            options=[
                ("Podgląd", lambda: self.on_menu(self.task, "preview")),
                ("Edytuj",  lambda: self.on_menu(self.task, "edit")),
                ("Usuń",    lambda: self.on_menu(self.task, "delete")),
            ],
        )

        # Info frame (kontener na date/time/clock)
        self.info_frame = tk.Frame(self.inner, bg=self.card_bg)

        # Date label - zawsze w info_frame
        self.lbl_date = tk.Label(
            self.info_frame, text=self._date_text,
            font=self.info_font, bg=self.card_bg, fg=self._info_fg,
            anchor="w",
        )
        self.lbl_date.pack(side="left", padx=(0, 8))

        # Time label - tylko jesli mamy czas
        if self._time_text:
            self.lbl_time = tk.Label(
                self.info_frame, text=self._time_text,
                font=self.info_font, bg=self.card_bg, fg=self._info_fg,
                anchor="w",
            )
            self.lbl_time.pack(side="left", padx=(0, 4))

            self.lbl_clock = tk.Label(
                self.info_frame, text=ICON_TIME,
                font=self.info_font, bg=self.card_bg, fg=self._info_fg,
            )
            self.lbl_clock.pack(side="left")
        else:
            self.lbl_time = None
            self.lbl_clock = None

        # Title - last, fill + expand zeby zabrac wolne miejsce w srodku
        self.lbl_title = tk.Label(
            self.inner, text=task.title,
            font=self.title_font,
            bg=self.card_bg, fg=self._text_fg,
            anchor="w", justify="left", wraplength=200,
        )

        # Inicjalne pakowanie w prawidlowej kolejnosci
        self._current_tier = None  # bedzie ustawione w pierwszym _apply_tier
        self._repack_in_order(show_info=True)

        # Canvas background
        self.bind("<Configure>", self._draw_bg)

        if task.is_done:
            self._apply_done_style()
        else:
            self.checkbox.set_state(done=False, accent_color=self.accent_color,
                                    on_dark_bg=(self.style == "filled"))

    # ============================================================
    # Pack management
    # ============================================================

    def _repack_in_order(self, show_info):
        """Forget WSZYSTKO i pakuje w prawidlowej kolejnosci, zeby kolejnosc
        wizualna byla zgodna z [checkbox][title][info][menu].

        Konieczne bo tkinter.pack honoruje kolejnosc zaplakowania - gdy
        info_frame jest forgotten i ponownie packowany side='right', moze
        trafic w nieoczekiwane miejsce. Bezpieczniej: forget all + repack."""
        # Forget all
        self.checkbox.pack_forget()
        self.menu_btn.pack_forget()
        self.info_frame.pack_forget()
        self.lbl_title.pack_forget()

        # Repack in correct order:
        # 1. checkbox -> left (rezerwuje lewa krawedz)
        self.checkbox.pack(side="left", padx=(12, 10), pady=4)
        # 2. menu -> right (rezerwuje prawa krawedz, ZAWSZE widoczne)
        self.menu_btn.pack(side="right", padx=(0, 12))
        # 3. info_frame -> right (na lewo od menu), opcjonalnie
        if show_info:
            self.info_frame.pack(side="right", padx=(0, 10))
        # 4. title -> left + fill + expand (bierze reszte)
        self.lbl_title.pack(side="left", fill="x", expand=True, padx=(0, 10))

    # ============================================================
    # Canvas rysowanie tla
    # ============================================================

    def _draw_bg(self, event=None):
        if event is not None:
            w, h = event.width, event.height
        else:
            w = self.winfo_width()
            h = self.winfo_height()
        if w < 4 or h < 4:
            return

        self.canvas.delete("all")
        r = 12
        x1, y1, x2, y2 = 2, 2, w - 3, h - 3

        points = [
            x1 + r, y1, x1 + r, y1, x2 - r, y1, x2 - r, y1,
            x2, y1, x2, y1 + r, x2, y1 + r, x2, y2 - r, x2, y2 - r,
            x2, y2, x2 - r, y2, x2 - r, y2, x1 + r, y2, x1 + r, y2,
            x1, y2, x1, y2 - r, x1, y2 - r, x1, y1 + r, x1, y1 + r, x1, y1
        ]

        accent = DONE_FG if self.task.is_done else self.accent_color
        border = DEFAULT_BORDER if self.style == "outlined" else accent
        self.canvas.create_polygon(points, outline=border, fill=self.card_bg,
                                   width=1, smooth=True)

        if self.style == "outlined":
            self.canvas.create_line(12, 16, 12, h - 16, fill=accent,
                                    width=4, capstyle="round")

    # ============================================================
    # Toggle done
    # ============================================================

    def toggle_done(self):
        self.task.is_done = not self.task.is_done
        if self.task.is_done:
            self._apply_done_style()
        else:
            self._apply_undone_style()
        self.on_toggle(self.task)

    def _apply_done_style(self):
        self.checkbox.set_state(done=True, accent_color=self.accent_color,
                                on_dark_bg=(self.style == "filled"))
        self.title_font.config(overstrike=1)
        self.lbl_title.config(fg=DONE_FG if self.style == "outlined" else ON_COLOR_FG)
        for lbl in (self.lbl_date, self.lbl_time, self.lbl_clock):
            if lbl is not None:
                lbl.config(fg=DONE_FG)
        self._draw_bg()

    def _apply_undone_style(self):
        self.checkbox.set_state(done=False, accent_color=self.accent_color,
                                on_dark_bg=(self.style == "filled"))
        self.title_font.config(overstrike=0)
        self.lbl_title.config(fg=self._text_fg)
        for lbl in (self.lbl_date, self.lbl_time, self.lbl_clock):
            if lbl is not None:
                lbl.config(fg=self._info_fg)
        self._draw_bg()

    # ============================================================
    # Sizing logic (tier system)
    # ============================================================

    def update_fonts(self, width, height=None):
        # 1. Scale fonts + checkbox size (pozostaje oryginalne, liniowe tylko dla tytułu i checkboxa)
        new_title_size = scaled(width, TASK_TITLE_SCALE)
        new_check_size = scaled(width, TASK_CHECKBOX_SCALE)

        self.title_font.config(size=new_title_size)
        self.checkbox.set_size(new_check_size)

        # 2. Available inner width
        inner_w = max(120, width - 44)

        # 3. Zmierz szerokosci kolumn przy AKTUALNYM foncie
        checkbox_w = 12 + new_check_size + 10

        menu_text_w = self.info_font.measure("\u2022\u2022\u2022")
        menu_w = menu_text_w + 12 + 6

        date_w = self.info_font.measure(self._date_text)
        if self._time_text:
            time_w = self.info_font.measure(self._time_text)
            clock_w = self.info_font.measure(ICON_TIME) + 6
        else:
            time_w = 0
            clock_w = 0

        info_outer_pad = 10
        info_w_full   = date_w + 8 + time_w + 4 + clock_w + info_outer_pad
        info_w_no_clk = date_w + 8 + time_w + info_outer_pad
        info_w_date_only = date_w + info_outer_pad

        title_right_gap = 10

        # 4. Title minimum
        words = self.task.title.split() or [self.task.title]
        longest_word_w = max(self.title_font.measure(w) for w in words)
        title_min = longest_word_w + 8

        # --- DODANO BUFOR BEZPIECZEŃSTWA (20px), KTÓRY ELIMINUJE UCINANIE TEKSTU ---
        safety = 20

        # 5. Dobor tieru: najwyzszy ktory daje title >= title_min
        has_time = self._time_text is not None

        if has_time:
            title_at_t1 = inner_w - checkbox_w - info_w_full   - title_right_gap - menu_w - safety
            title_at_t2 = inner_w - checkbox_w - info_w_no_clk - title_right_gap - menu_w - safety
            title_at_t3 = inner_w - checkbox_w - 0             - menu_w - safety

            if title_at_t1 >= title_min:
                tier, title_avail = 1, title_at_t1
            elif title_at_t2 >= title_min:
                tier, title_avail = 2, title_at_t2
            else:
                tier, title_avail = 3, max(title_min, title_at_t3)
        else:
            title_at_t1 = inner_w - checkbox_w - info_w_date_only - title_right_gap - menu_w - safety
            title_at_t3 = inner_w - checkbox_w - 0 - menu_w - safety

            if title_at_t1 >= title_min:
                tier, title_avail = 1, title_at_t1
            else:
                tier, title_avail = 3, max(title_min, title_at_t3)

        # 6. Aplikuj tier (show/hide info elements)
        self._apply_tier(tier)

        # 7. Wraplength tytulu
        natural_title_w = self.title_font.measure(self.task.title)
        title_wrap = max(title_min, min(natural_title_w + 10, title_avail))
        self.lbl_title.config(wraplength=title_wrap)

    def _apply_tier(self, tier):
        """Pokaz/ukryj elementy info wg tieru."""
        if tier == self._current_tier:
            return
        self._current_tier = tier

        if tier == 3:
            self._repack_in_order(show_info=False)
        else:
            if not self.info_frame.winfo_ismapped():
                self._repack_in_order(show_info=True)

            if self.lbl_clock is not None:
                if tier == 1:
                    if not self.lbl_clock.winfo_ismapped():
                        self.lbl_clock.pack(side="left")
                else:
                    if self.lbl_clock.winfo_ismapped():
                        self.lbl_clock.pack_forget()