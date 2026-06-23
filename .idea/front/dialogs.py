"""
Modale dialogowe - okna do dodawania/edycji zadan i kategorii.

REDESIGN: pola w bialych kartach z subtelna ramka (jak TaskRow), etykietki
nad polami, custom TimePicker z duzymi cyframi, kolorowe akcenty zgodne
z reszta apki (niebieski Zapisz, czerwony Usuń).

Hierarchia:
  Modal (tk.Toplevel)            - baza: header z tytulem, body z polami,
                                    przyciski Usun (lewo) / Anuluj+Zapisz (prawo)
                                    Flagi: self.result (None/obiekt), self.deleted (bool)
  ├── TaskFormDialog             - dodaj/edytuj zadanie
  └── CategoryFormDialog         - dodaj/edytuj kategorie

Uzycie:
    dlg = TaskFormDialog(parent, repository=repo, task=existing_task_or_None)
    if dlg.deleted:
        repo.delete_task(existing_task.id)
    elif dlg.result is not None:
        repo.update_task(dlg.result)  # lub add_task w trybie create
    # else: user kliknął Anuluj / ESC / X
"""

import re
import tkinter as tk
import calendar as _cal_module
from tkinter import messagebox
from datetime import datetime, timedelta

from front.theme import BG, FG, INFO_FG, PRIORYTETOWE_COLOR, DEFAULT_BORDER
from front.components import make_font, ChipToggle
from fake_data import Task, Category


# ============================================================
# Paleta dialogow
# ============================================================
DIALOG_BG            = "#FFFFFF"           # bialy bg calego popupu (zamiast BG/light-gray)
BRAND_PRIMARY        = "#1A73E8"          # niebieski Zapisz / akcent fokusu
BRAND_PRIMARY_HOVER  = "#1557B0"
DANGER_FG            = PRIORYTETOWE_COLOR  # czerwony Usun
DANGER_HOVER_BG      = "#FCE8E6"
LABEL_FG             = "#5F6368"           # etykietki nad polami
PLACEHOLDER_FG       = "#9AA0A6"
FIELD_BORDER         = DEFAULT_BORDER
FIELD_BG             = "#FFFFFF"
HOVER_BG_LIGHT       = "#F8F9FA"


# ============================================================
# HoverButton - klikalny label z efektem hover, opcjonalna ramka
# ============================================================

class HoverButton(tk.Label):
    def __init__(self, parent, text, on_click, bg, fg, hover_bg,
                 font=None, padx=20, pady=8, bordered=False):
        kwargs = dict(text=text, font=font, bg=bg, fg=fg,
                      cursor="hand2", padx=padx, pady=pady)
        if bordered:
            kwargs["bd"] = 1
            kwargs["relief"] = "solid"
        super().__init__(parent, **kwargs)
        self._default_bg = bg
        self._hover_bg = hover_bg
        self.bind("<Button-1>", lambda e: on_click())
        self.bind("<Enter>", lambda e: self.config(bg=self._hover_bg))
        self.bind("<Leave>", lambda e: self.config(bg=self._default_bg))


# ============================================================
# FieldLabel - etykietka nad polem (mala szara, bold)
# ============================================================

class FieldLabel(tk.Label):
    def __init__(self, parent, text):
        super().__init__(parent, text=text, bg=DIALOG_BG, fg=LABEL_FG,
                         font=make_font(11, weight="bold"),
                         anchor="w")


# ============================================================
# TextField - input tekstowy w bialej karcie z subtelna ramka.
# Border zmienia kolor na niebieski przy fokusie. Placeholder
# znika po focus, wraca po blur jesli pole puste.
# ============================================================

class TextField(tk.Frame):
    def __init__(self, parent, placeholder, initial="",
                 font_size=14, bold=False):
        # outer frame = kolor ramki (border)
        super().__init__(parent, bg=FIELD_BORDER, bd=0)

        # inner frame = bialy fill, padx=1 daje 1px ramke
        inner = tk.Frame(self, bg=FIELD_BG)
        inner.pack(fill="both", expand=True, padx=1, pady=1)

        font = make_font(font_size, weight="bold" if bold else "normal")

        self.entry = tk.Entry(inner, font=font,
                              bg=FIELD_BG, fg=FG,
                              bd=0, highlightthickness=0,
                              insertbackground=FG)
        self.entry.pack(fill="x", padx=14, pady=11)

        self.placeholder = placeholder
        self._has_placeholder = False

        if initial:
            self.entry.insert(0, initial)
        else:
            self._show_placeholder()

        self.entry.bind("<FocusIn>", self._on_focus_in)
        self.entry.bind("<FocusOut>", self._on_focus_out)

    def _show_placeholder(self):
        self.entry.delete(0, "end")
        self.entry.insert(0, self.placeholder)
        self.entry.config(fg=PLACEHOLDER_FG)
        self._has_placeholder = True

    def _on_focus_in(self, _e):
        self.config(bg=BRAND_PRIMARY)  # niebieska ramka przy fokusie
        if self._has_placeholder:
            self.entry.delete(0, "end")
            self.entry.config(fg=FG)
            self._has_placeholder = False

    def _on_focus_out(self, _e):
        self.config(bg=FIELD_BORDER)
        if not self.entry.get():
            self._show_placeholder()

    def get_value(self):
        return "" if self._has_placeholder else self.entry.get()


# ============================================================
# TimeUnit - jedna jednostka czasu (HH lub MM) z duza cyfra,
# subtelnymi strzalkami nad/pod, scroll wheel do zmiany,
# klik na cyfre = inkrementacja.
# ============================================================

class TimeUnit(tk.Frame):
    """Jedna cyfra czasu (HH lub MM). Wartosc zawija sie wokol
    granicy (HH: 0-23, MM: 0-59)."""

    def __init__(self, parent, initial, max_val, big_font):
        super().__init__(parent, bg=FIELD_BG)
        self.max_val = max_val
        self.var = tk.StringVar(value=f"{int(initial):02d}")

        arrow_font = make_font(8)

        # ▲ strzalka w gore - subtelna, ciemnieje na hover
        self.up = tk.Label(self, text="▲", bg=FIELD_BG, fg="#BDC1C6",
                           font=arrow_font, cursor="hand2")
        self.up.pack()
        self.up.bind("<Button-1>", lambda e: self._change(1))
        self.up.bind("<Enter>", lambda e: self.up.config(fg=FG))
        self.up.bind("<Leave>", lambda e: self.up.config(fg="#BDC1C6"))

        # Cyfra - duzo wieksza, bold, kursor hand2 (klikalna -> +1)
        self.lbl = tk.Label(self, textvariable=self.var,
                            bg=FIELD_BG, fg=FG, font=big_font,
                            cursor="hand2")
        self.lbl.pack()
        self.lbl.bind("<Button-1>", lambda e: self._change(1))

        # ▼ strzalka w dol
        self.down = tk.Label(self, text="▼", bg=FIELD_BG, fg="#BDC1C6",
                             font=arrow_font, cursor="hand2")
        self.down.pack()
        self.down.bind("<Button-1>", lambda e: self._change(-1))
        self.down.bind("<Enter>", lambda e: self.down.config(fg=FG))
        self.down.bind("<Leave>", lambda e: self.down.config(fg="#BDC1C6"))

        # Scroll wheel na calym TimeUnit i samej cyfrze
        for w in (self, self.lbl, self.up, self.down):
            w.bind("<MouseWheel>", self._on_wheel)
            w.bind("<Button-4>", lambda e: self._change(1))    # Linux up
            w.bind("<Button-5>", lambda e: self._change(-1))   # Linux down

    def _change(self, delta):
        cur = int(self.var.get())
        new = (cur + delta) % (self.max_val + 1)  # wrap around
        self.var.set(f"{new:02d}")

    def _on_wheel(self, e):
        self._change(1 if e.delta > 0 else -1)

    def get(self):
        return self.var.get()


# ============================================================
# TimePicker - 4 TimeUnits w karcie: HH : MM — HH : MM
# ============================================================

class TimePicker(tk.Frame):
    def __init__(self, parent, sh, sm, eh, em):
        super().__init__(parent, bg=FIELD_BORDER, bd=0)

        inner = tk.Frame(self, bg=FIELD_BG)
        inner.pack(fill="both", expand=True, padx=1, pady=1)

        big_font  = make_font(20, weight="bold")
        sep_font  = make_font(20, weight="bold")
        dash_font = make_font(16)

        row = tk.Frame(inner, bg=FIELD_BG)
        row.pack(expand=True, pady=2)

        self.sh = TimeUnit(row, sh, 23, big_font); self.sh.pack(side="left", padx=2)
        tk.Label(row, text=":", bg=FIELD_BG, fg=FG, font=sep_font).pack(side="left")
        self.sm = TimeUnit(row, sm, 59, big_font); self.sm.pack(side="left", padx=2)

        tk.Label(row, text="—", bg=FIELD_BG, fg=INFO_FG,
                 font=dash_font).pack(side="left", padx=12)

        self.eh = TimeUnit(row, eh, 23, big_font); self.eh.pack(side="left", padx=2)
        tk.Label(row, text=":", bg=FIELD_BG, fg=FG, font=sep_font).pack(side="left")
        self.em = TimeUnit(row, em, 59, big_font); self.em.pack(side="left", padx=2)

    def get_values(self):
        return self.sh.get(), self.sm.get(), self.eh.get(), self.em.get()


# ============================================================
# ============================================================
# DatePicker - custom popup zamiast tkcalendar.DateEntry
# ============================================================
# ============================================================

class CalendarPopup(tk.Toplevel):
    """Popup z miesiecznym kalendarzem. Klik na dzien wybiera + zamyka.
    ◀/▶ przelacza miesiace. Escape lub klik poza popupem - zamyka."""

    POLISH_MONTHS = [
        "Styczeń", "Luty", "Marzec", "Kwiecień", "Maj", "Czerwiec",
        "Lipiec", "Sierpień", "Wrzesień", "Październik", "Listopad", "Grudzień",
    ]
    DAYS = ["Pn", "Wt", "Śr", "Cz", "Pt", "So", "Nd"]

    def __init__(self, parent, initial_date, on_select, x, y):
        super().__init__(parent)
        self.on_select = on_select
        self._displayed_year = initial_date.year
        self._displayed_month = initial_date.month
        self._selected = initial_date

        self.overrideredirect(True)  # bez ramki okna - clean popup
        self.configure(bg=FIELD_BG, highlightthickness=1,
                       highlightbackground=FIELD_BORDER)
        self.geometry(f"280x310+{x}+{y}")

        self._build()

        # KRYTYCZNE: parent (dialog Modal) ma grab_set(), wiec tk blokuje
        # klikniecia we wszystkich innych widgetach (rowniez w tym popupie).
        # Musimy zwolnic grab parent toplevelu i wziac wlasny - inaczej
        # popup zachowuje sie jak zamarl (klikniecia nie docieraja).
        self._parent_top = parent.winfo_toplevel()
        self._restore_grab = False
        try:
            if self._parent_top.grab_current() == self._parent_top:
                self._restore_grab = True
                self._parent_top.grab_release()
        except tk.TclError:
            pass

        self.bind("<Escape>", self._close)
        # Wymus focus + grab po krotkim opoznieniu (po zmapowaniu okna).
        self.after(50, self._grab_focus)

    def _grab_focus(self):
        try:
            self.grab_set()
            self.focus_force()
        except tk.TclError:
            pass

    def destroy(self):
        # Przywroc grab parent dialog'u zeby modal nadal byl modalny.
        if self._restore_grab:
            try:
                self._parent_top.grab_set()
            except tk.TclError:
                pass
        super().destroy()

    def _close(self, _e=None):
        self.destroy()

    def _build(self):
        # Header: ◀  Miesiąc Rok  ▶
        header = tk.Frame(self, bg=FIELD_BG)
        header.pack(fill="x", padx=6, pady=(8, 4))

        prev_btn = tk.Label(header, text="◀", bg=FIELD_BG, fg=FG,
                            font=make_font(13), cursor="hand2", padx=10)
        prev_btn.pack(side="left")
        prev_btn.bind("<Button-1>", lambda e: self._change_month(-1))
        prev_btn.bind("<Enter>", lambda e: prev_btn.config(fg=BRAND_PRIMARY))
        prev_btn.bind("<Leave>", lambda e: prev_btn.config(fg=FG))

        next_btn = tk.Label(header, text="▶", bg=FIELD_BG, fg=FG,
                            font=make_font(13), cursor="hand2", padx=10)
        next_btn.pack(side="right")
        next_btn.bind("<Button-1>", lambda e: self._change_month(1))
        next_btn.bind("<Enter>", lambda e: next_btn.config(fg=BRAND_PRIMARY))
        next_btn.bind("<Leave>", lambda e: next_btn.config(fg=FG))

        self.month_lbl = tk.Label(
            header,
            text=self._month_year_label(),
            bg=FIELD_BG, fg=FG,
            font=make_font(13, weight="bold"),
        )
        self.month_lbl.pack(side="left", fill="x", expand=True)

        # Wiersz nazw dni Pn Wt Sr Cz Pt So Nd
        days_row = tk.Frame(self, bg=FIELD_BG)
        days_row.pack(fill="x", padx=8)
        for name in self.DAYS:
            tk.Label(days_row, text=name, bg=FIELD_BG, fg=INFO_FG,
                     font=make_font(10, weight="bold"),
                     width=4).pack(side="left", expand=True)

        # Siatka 6x7 dni
        self.grid_frame = tk.Frame(self, bg=FIELD_BG)
        self.grid_frame.pack(fill="both", expand=True, padx=8, pady=(2, 8))

        self._build_grid()

    def _month_year_label(self):
        return f"{self.POLISH_MONTHS[self._displayed_month - 1]} {self._displayed_year}"

    def _build_grid(self):
        for w in self.grid_frame.winfo_children():
            w.destroy()

        cal = _cal_module.Calendar(firstweekday=0)
        weeks = list(cal.monthdatescalendar(self._displayed_year,
                                            self._displayed_month))
        while len(weeks) < 6:
            last = weeks[-1][-1]
            weeks.append([last + timedelta(days=i + 1) for i in range(7)])
        weeks = weeks[:6]

        for week in weeks:
            row = tk.Frame(self.grid_frame, bg=FIELD_BG)
            row.pack(fill="x", expand=True)
            for d in week:
                is_current = (d.month == self._displayed_month)
                is_selected = (d == self._selected)

                if is_selected:
                    bg, fg = BRAND_PRIMARY, "white"
                elif is_current:
                    bg, fg = FIELD_BG, FG
                else:
                    bg, fg = FIELD_BG, "#BBBBBB"

                cell = tk.Label(row, text=str(d.day), bg=bg, fg=fg,
                                font=make_font(11),
                                cursor="hand2", width=3)
                cell.pack(side="left", expand=True, fill="both",
                          padx=1, pady=1)
                cell.bind("<Button-1>", lambda e, dd=d: self._pick(dd))
                if not is_selected:
                    # hover - jasnoszare tlo
                    cell.bind("<Enter>", lambda e, c=cell:
                              c.config(bg=HOVER_BG_LIGHT))
                    cell.bind("<Leave>", lambda e, c=cell, b=bg:
                              c.config(bg=b))

    def _change_month(self, delta):
        m = self._displayed_month + delta
        y = self._displayed_year
        while m < 1:
            m += 12
            y -= 1
        while m > 12:
            m -= 12
            y += 1
        self._displayed_month, self._displayed_year = m, y
        self.month_lbl.config(text=self._month_year_label())
        self._build_grid()

    def _pick(self, d):
        self.on_select(d)
        self.destroy()


class DatePicker(tk.Frame):
    """Pole z data + custom popup. Wymienia tkcalendar.DateEntry na
    spojny wizualnie widget pasujacy do reszty dialogu."""

    def __init__(self, parent, initial_date):
        super().__init__(parent, bg=FIELD_BORDER, bd=0)
        self._date = initial_date

        self.inner = tk.Frame(self, bg=FIELD_BG, cursor="hand2")
        self.inner.pack(fill="both", expand=True, padx=1, pady=1)

        self.lbl = tk.Label(self.inner, text=self._format(initial_date),
                            bg=FIELD_BG, fg=FG,
                            font=make_font(14, weight="bold"),
                            anchor="w")
        self.lbl.pack(side="left", fill="x", expand=True,
                      padx=(14, 0), pady=12)

        self.arrow = tk.Label(self.inner, text="▾", bg=FIELD_BG, fg=INFO_FG,
                              font=make_font(13))
        self.arrow.pack(side="right", padx=(0, 14))

        for w in (self.inner, self.lbl, self.arrow):
            w.bind("<Button-1>", self._open)
            w.bind("<Enter>", lambda e: self._set_bg(HOVER_BG_LIGHT))
            w.bind("<Leave>", lambda e: self._set_bg(FIELD_BG))

    def _format(self, d):
        return d.strftime("%d.%m.%Y")

    def _set_bg(self, color):
        self.inner.config(bg=color)
        self.lbl.config(bg=color)
        self.arrow.config(bg=color)

    def _open(self, _e):
        self.update_idletasks()
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height() + 4
        CalendarPopup(self, self._date, on_select=self._picked, x=x, y=y)

    def _picked(self, d):
        self._date = d
        self.lbl.config(text=self._format(d))

    def get_date(self):
        return self._date


# ============================================================
# CategoryField - dropdown kategorii z kolorowa kropka
# ============================================================

class CategoryField(tk.Frame):
    def __init__(self, parent, repository, initial_id):
        super().__init__(parent, bg=FIELD_BORDER, bd=0)
        self.repository = repository
        self._selected_id = initial_id

        self.inner = tk.Frame(self, bg=FIELD_BG, cursor="hand2")
        self.inner.pack(fill="both", expand=True, padx=1, pady=1)

        # Kropka koloru kategorii (Canvas)
        self.dot = tk.Canvas(self.inner, width=16, height=16,
                             bg=FIELD_BG, highlightthickness=0)
        self.dot.pack(side="left", padx=(14, 10), pady=14)

        # Nazwa
        self.lbl = tk.Label(self.inner, text="", bg=FIELD_BG, fg=FG,
                            font=make_font(13), anchor="w")
        self.lbl.pack(side="left", fill="x", expand=True)

        # Chevron ▾
        self.arrow = tk.Label(self.inner, text="▾", bg=FIELD_BG, fg=INFO_FG,
                              font=make_font(13))
        self.arrow.pack(side="right", padx=(0, 14))

        # Bindy + hover
        for w in (self.inner, self.dot, self.lbl, self.arrow):
            w.bind("<Button-1>", self._show_menu)
            w.bind("<Enter>", lambda e: self._set_bg(HOVER_BG_LIGHT))
            w.bind("<Leave>", lambda e: self._set_bg(FIELD_BG))

        self._update_display()

    def _set_bg(self, color):
        self.inner.config(bg=color)
        self.dot.config(bg=color)
        self.lbl.config(bg=color)
        self.arrow.config(bg=color)
        self._draw_dot(color)

    def _draw_dot(self, bg_color):
        self.dot.delete("all")
        if self._selected_id is None:
            # Bez kategorii - obrysowane szare kolko
            self.dot.create_oval(2, 2, 14, 14, outline=INFO_FG, width=2,
                                 fill=bg_color)
        else:
            cat = self.repository.get_category(self._selected_id)
            color = cat.color if cat else INFO_FG
            self.dot.create_oval(2, 2, 14, 14, fill=color, outline="")

    def _update_display(self):
        if self._selected_id is None:
            self.lbl.config(text="Bez kategorii")
        else:
            cat = self.repository.get_category(self._selected_id)
            self.lbl.config(text=cat.name if cat else "Bez kategorii")
        self._draw_dot(self.inner.cget("bg"))

    def _show_menu(self, event):
        # Natywne menu Tkintera
        menu = tk.Menu(self, tearoff=0)

        # Funkcja pomocnicza do oznaczania wybranego koloru
        current_name = self._name_for(self._selected)

        def mark(label):
            return f"✓  {label}" if label == current_name else label

        # Dodawanie opcji kolorów do menu
        for name, hex_ in self.AVAILABLE_COLORS:
            # Używamy lambda z domyślnym argumentem c=hex_
            menu.add_command(
                label=mark(name),
                command=lambda c=hex_: self._select(c)
            )

        # Wyświetlenie menu w miejscu kliknięcia
        self.update_idletasks()
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height() + 4

        try:
            menu.tk_popup(x, y)
        finally:
            menu.grab_release()
    def _select(self, cat_id):
        self._selected_id = cat_id
        self._update_display()

    def get_selected_id(self):
        return self._selected_id


# ============================================================
# ColorField - dropdown koloru z kolorowa duza kropka i nazwa
# ============================================================

class ColorField(tk.Frame):
    AVAILABLE_COLORS = [
        ("Niebieski",    "#4A90D9"),
        ("Zielony",      "#5CB85C"),
        ("Fioletowy",    "#A973B5"),
        ("Pomarańczowy", "#E89C5C"),
        ("Czerwony",     "#D9534F"),
        ("Żółty",        "#E8C857"),
        ("Turkusowy",    "#5BC0DE"),
    ]

    def __init__(self, parent, initial_color):
        super().__init__(parent, bg=FIELD_BORDER, bd=0)
        self._selected = initial_color

        self.inner = tk.Frame(self, bg=FIELD_BG, cursor="hand2")
        self.inner.pack(fill="both", expand=True, padx=1, pady=1)

        # Duza kropka pokazujaca wybrany kolor
        self.swatch = tk.Canvas(self.inner, width=22, height=22,
                                bg=FIELD_BG, highlightthickness=0)
        self.swatch.pack(side="left", padx=(14, 10), pady=12)

        self.lbl = tk.Label(self.inner, text="",
                            bg=FIELD_BG, fg=FG,
                            font=make_font(13), anchor="w")
        self.lbl.pack(side="left", fill="x", expand=True)

        self.arrow = tk.Label(self.inner, text="▾", bg=FIELD_BG, fg=INFO_FG,
                              font=make_font(13))
        self.arrow.pack(side="right", padx=(0, 14))

        for w in (self.inner, self.swatch, self.lbl, self.arrow):
            w.bind("<Button-1>", self._show_menu)
            w.bind("<Enter>", lambda e: self._set_bg(HOVER_BG_LIGHT))
            w.bind("<Leave>", lambda e: self._set_bg(FIELD_BG))

        self._update_display()

    def _set_bg(self, color):
        self.inner.config(bg=color)
        self.swatch.config(bg=color)
        self.lbl.config(bg=color)
        self.arrow.config(bg=color)
        self._draw_swatch(color)

    def _draw_swatch(self, bg_color):
        self.swatch.delete("all")
        self.swatch.create_oval(2, 2, 20, 20, fill=self._selected, outline="")

    def _update_display(self):
        name = self._name_for(self._selected)
        self.lbl.config(text=name)
        self._draw_swatch(self.inner.cget("bg"))

    def _name_for(self, hex_):
        for n, h in self.AVAILABLE_COLORS:
            if h.lower() == hex_.lower():
                return n
        return "Kolor"

    def _show_menu(self, event):
        items = []
        for name, hex_ in self.AVAILABLE_COLORS:
            items.append((name, lambda c=hex_: self._select(c)))

        current_name = self._name_for(self._selected)

        self.update_idletasks()
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height() + 4

        PopupMenu(self, items=items, x=x, y=y,
                  current_path=[(None, current_name)])

    def _select(self, color):
        self._selected = color
        self._update_display()

    def get_color(self):
        return self._selected


# ============================================================
# HabitCyclePopup - wybor czestotliwosci nawyku
# ============================================================

class HabitCyclePopup(tk.Toplevel):
    """Maly modal z radio do wyboru jak czesto zadanie sie powtarza.
    Trzy presety + niestandardowy tekst. Wynik w self.result (None gdy
    Anuluj). Wynik to string ktory pojdzie jako prefix recurrence_rule."""

    OPTIONS = [
        ("Codziennie",       "co dzien"),
        ("Co tydzień",       "co tydz"),
        ("Co dwa tygodnie",  "co dwa tyg"),
    ]
    CUSTOM_KEY = "_custom"

    def __init__(self, parent, initial="co dzien"):
        super().__init__(parent)
        self.result = None
        self.title("Częstotliwość nawyku")
        self.configure(bg=DIALOG_BG)
        self.resizable(False, False)

        W, H = 360, 290
        parent.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - W) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - H) // 2
        self.geometry(f"{W}x{H}+{max(0, x)}+{max(0, y)}")

        self.transient(parent)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self.bind("<Escape>", lambda e: self._cancel())

        # Zmapuj initial na ktora opcje wybrac
        preset_val = next((v for _l, v in self.OPTIONS if v == initial), None)
        self._initial_custom = "" if preset_val else initial
        self._selected = tk.StringVar(
            value=preset_val if preset_val else self.CUSTOM_KEY)

        self._build()
        self.wait_window()

    def _build(self):
        tk.Label(self, text="Jak często się powtarza?",
                 bg=DIALOG_BG, fg=FG,
                 font=make_font(14, weight="bold"),
                 anchor="w").pack(fill="x", padx=24, pady=(18, 10))

        # Preset radios
        for label, val in self.OPTIONS:
            tk.Radiobutton(self, text=label,
                           variable=self._selected, value=val,
                           bg=DIALOG_BG, fg=FG, font=make_font(13),
                           selectcolor=FIELD_BG, anchor="w",
                           activebackground=BG).pack(fill="x", padx=24, pady=2)

        # Custom radio + entry
        custom_row = tk.Frame(self, bg=DIALOG_BG)
        custom_row.pack(fill="x", padx=24, pady=(2, 4))

        tk.Radiobutton(custom_row, text="Niestandardowe:",
                       variable=self._selected, value=self.CUSTOM_KEY,
                       bg=DIALOG_BG, fg=FG, font=make_font(13),
                       selectcolor=FIELD_BG,
                       activebackground=BG).pack(side="left")

        self.custom_entry = tk.Entry(custom_row, font=make_font(13),
                                     bg=FIELD_BG, fg=FG,
                                     bd=1, relief="solid",
                                     highlightthickness=0)
        if self._initial_custom:
            self.custom_entry.insert(0, self._initial_custom)
        self.custom_entry.pack(side="left", fill="x", expand=True, padx=(8, 0))
        # Klik w entry przelacza radio na "niestandardowe"
        self.custom_entry.bind("<FocusIn>",
                               lambda e: self._selected.set(self.CUSTOM_KEY))

        # Przyciski
        btn_row = tk.Frame(self, bg=DIALOG_BG)
        btn_row.pack(side="bottom", fill="x", padx=24, pady=(0, 18))
        HoverButton(btn_row, text="OK",
                    font=make_font(13, weight="bold"),
                    bg=BRAND_PRIMARY, fg="white",
                    hover_bg=BRAND_PRIMARY_HOVER,
                    padx=24, pady=9,
                    on_click=self._ok).pack(side="right")
        HoverButton(btn_row, text="Anuluj",
                    font=make_font(13),
                    bg=FIELD_BG, fg=FG,
                    hover_bg=HOVER_BG_LIGHT,
                    padx=20, pady=8,
                    bordered=True,
                    on_click=self._cancel).pack(side="right", padx=(0, 10))

    def _ok(self):
        val = self._selected.get()
        if val == self.CUSTOM_KEY:
            custom = self.custom_entry.get().strip()
            if not custom:
                messagebox.showwarning("Brak wartości",
                                       "Wpisz własną częstotliwość.",
                                       parent=self)
                return
            self.result = custom
        else:
            self.result = val
        self.destroy()

    def _cancel(self):
        self.result = None
        self.destroy()


# ============================================================
# Modal - baza
# ============================================================

class Modal(tk.Toplevel):
    DEFAULT_WIDTH = 500
    DEFAULT_HEIGHT = 600

    def __init__(self, parent, title="", show_delete=False):
        super().__init__(parent)
        self.parent = parent
        self.result = None
        self.deleted = False   # ustawiane gdy user klika Usun + potwierdzi
        self.show_delete = show_delete

        self.title(title)
        # Cale tlo bialy + outer Frame z 1px czarna ramka - rozwiazuje
        # niespojnosc miedzy windowed a fullscreen na macOS gdzie dekoracja
        # okna ginela i ramka popupu wygladala inaczej.
        self.configure(bg=DIALOG_BG)
        self.resizable(False, False)

        parent.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - self.DEFAULT_WIDTH) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.DEFAULT_HEIGHT) // 2
        self.geometry(f"{self.DEFAULT_WIDTH}x{self.DEFAULT_HEIGHT}+{max(0, x)}+{max(0, y)}")

        self.transient(parent)
        self.grab_set()

        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self.bind("<Escape>", lambda e: self._cancel())

        # Outer = cala zawartosc + 1px czarna ramka. Wszystko od tego momentu
        # idzie do _outer zamiast self - dzieki temu ramka opasuje cala tresc
        # nawet gdy okno systemowe nie ma swojej dekoracji.
        self._outer = tk.Frame(self, bg=DIALOG_BG, bd=1, relief="solid")
        self._outer.pack(fill="both", expand=True)

        self._build_header(title)

        self.body = tk.Frame(self._outer, bg=DIALOG_BG)
        self.body.pack(side="top", fill="both", expand=True, padx=32, pady=(4, 8))

        self.build()
        self._build_buttons()

        self.wait_window()

    def _build_header(self, title):
        tk.Label(self._outer, text=title, bg=DIALOG_BG, fg=FG,
                 font=make_font(19, weight="bold"),
                 anchor="w").pack(side="top", fill="x", padx=32, pady=(22, 0))
        # subtelna linia separujaca header od body
        tk.Frame(self._outer, bg=FIELD_BORDER, height=1).pack(
            side="top", fill="x", padx=32, pady=(14, 4))

    def _build_buttons(self):
        # subtelny separator nad przyciskami
        tk.Frame(self._outer, bg=FIELD_BORDER, height=1).pack(
            side="bottom", fill="x", padx=32, pady=(0, 16))

        btn_row = tk.Frame(self._outer, bg=DIALOG_BG)
        btn_row.pack(side="bottom", fill="x", padx=32, pady=(0, 22))

        # ---- Usun po lewej (tylko w edit mode) ----
        if self.show_delete:
            self.btn_delete = HoverButton(
                btn_row, text="Usuń",
                font=make_font(13, weight="bold"),
                bg=DIALOG_BG, fg=DANGER_FG,
                hover_bg=DANGER_HOVER_BG,
                padx=18, pady=10,
                on_click=self._on_delete_click,
            )
            self.btn_delete.pack(side="left")

        # ---- Zapisz po prawej ----
        self.btn_save = HoverButton(
            btn_row, text="Zapisz",
            font=make_font(13, weight="bold"),
            bg=BRAND_PRIMARY, fg="white",
            hover_bg=BRAND_PRIMARY_HOVER,
            padx=26, pady=10,
            on_click=self._save,
        )
        self.btn_save.pack(side="right")

        # ---- Anuluj na lewo od Zapisz ----
        self.btn_cancel = HoverButton(
            btn_row, text="Anuluj",
            font=make_font(13),
            bg=FIELD_BG, fg=FG,
            hover_bg=HOVER_BG_LIGHT,
            padx=22, pady=9,
            bordered=True,
            on_click=self._cancel,
        )
        self.btn_cancel.pack(side="right", padx=(0, 10))

    def _on_delete_click(self):
        if messagebox.askyesno(
                "Potwierdzenie",
                "Czy na pewno chcesz usunąć?",
                parent=self):
            self.deleted = True
            self.destroy()

    def build(self):
        """Subklasa nadpisuje - buduje pola w self.body."""
        pass

    def collect_data(self):
        """Subklasa nadpisuje - zwraca obiekt domenowy.
        Moze rzucic ValueError gdy walidacja nie przeszla."""
        return None

    def _save(self):
        try:
            self.result = self.collect_data()
            self.destroy()
        except ValueError:
            pass

    def _cancel(self):
        self.result = None
        self.destroy()


# ============================================================
# TaskFormDialog
# ============================================================

class TaskFormDialog(Modal):
    DEFAULT_WIDTH = 520
    DEFAULT_HEIGHT = 720

    def __init__(self, parent, repository, task=None):
        self.repository = repository
        self.task = task
        # Cykl (prefix recurrence_rule, np. "co dzien"). Tu utrzymujemy stan
        # nawet gdy chip Nawyk jest off, zeby user mogl go wlaczyc spowrotem
        # bez ponownego wpisywania. Extract z istniejacego task lub default.
        self._cycle = self._initial_cycle()
        title = "Edytuj zadanie" if task else "Nowe zadanie"
        super().__init__(parent, title=title, show_delete=task is not None)

    def _initial_cycle(self):
        if self.task and self.task.recurrence_rule:
            m = re.search(r"(\d{1,2}):(\d{2})-(\d{1,2}):(\d{2})",
                          self.task.recurrence_rule)
            if m:
                prefix = self.task.recurrence_rule[:m.start()].strip()
                return prefix or "co dzien"
            return self.task.recurrence_rule.strip() or "co dzien"
        return "co dzien"

    def build(self):
        # ---- Nazwa ----
        FieldLabel(self.body, "Nazwa").pack(fill="x", pady=(0, 4))
        self.title_field = TextField(
            self.body, placeholder="Co masz do zrobienia?",
            initial=self.task.title if self.task else "",
            font_size=15, bold=True)
        self.title_field.pack(fill="x", pady=(0, 14))

        # ---- Opis ----
        FieldLabel(self.body, "Opis").pack(fill="x", pady=(0, 4))
        self.desc_field = TextField(
            self.body, placeholder="Opcjonalny opis",
            initial=self.task.description if self.task else "",
            font_size=12)
        self.desc_field.pack(fill="x", pady=(0, 14))

        # ---- Data i czas ----
        FieldLabel(self.body, "Data i czas").pack(fill="x", pady=(0, 4))
        dt_row = tk.Frame(self.body, bg=DIALOG_BG)
        dt_row.pack(fill="x", pady=(0, 14))

        now = self.task.due_date if self.task else self._default_start()
        self.date_field = DatePicker(dt_row, now.date())
        self.date_field.pack(side="left", padx=(0, 10))

        sh, sm, eh, em = self._extract_time_parts(now, self.task)
        self.time_field = TimePicker(dt_row, sh, sm, eh, em)
        self.time_field.pack(side="left", fill="x", expand=True)

        # ---- Opcje (chips) ----
        FieldLabel(self.body, "Opcje").pack(fill="x", pady=(0, 4))
        chips_row = tk.Frame(self.body, bg=DIALOG_BG)
        chips_row.pack(fill="x", pady=(0, 14))

        self.chip_habit = ChipToggle(
            chips_row, text="Nawyk",
            initial=bool(self.task.recurrence_rule) if self.task else False,
            font=make_font(12),
            on_change=self._on_habit_toggled)
        self.chip_habit.pack(side="left", padx=(0, 8))

        self.chip_priority = ChipToggle(
            chips_row, text="Priorytet",
            initial=self.task.priority if self.task else False,
            font=make_font(12))
        self.chip_priority.pack(side="left")

        # ---- Kategoria ----
        FieldLabel(self.body, "Kategoria").pack(fill="x", pady=(0, 4))
        self.cat_field = CategoryField(
            self.body, repository=self.repository,
            initial_id=self.task.category_id if self.task else None)
        self.cat_field.pack(fill="x")

    def _default_start(self):
        """Domyslny czas startu dla nowego zadania: nastepna pelna godzina."""
        now = datetime.now()
        return (now.replace(minute=0, second=0, microsecond=0)
                + timedelta(hours=1))

    def _on_habit_toggled(self, is_on):
        """Klik chipa Nawyk: jesli wlaczane, pokaz popup wyboru czestotliwosci.
        Jesli user anuluje popup, wracamy do off (chip.set False bez fire eventu)."""
        if not is_on:
            return  # wylaczanie - nic nie pytamy
        popup = HabitCyclePopup(self, initial=self._cycle)
        if popup.result is None:
            # Anuluj - cofnij chip do off (set nie wola on_change, brak petli)
            self.chip_habit.set(False)
        else:
            self._cycle = popup.result

    def _extract_time_parts(self, dt, task=None):
        if task and task.recurrence_rule:
            m = re.search(r"(\d{1,2}):(\d{2})-(\d{1,2}):(\d{2})", task.recurrence_rule)
            if m:
                return tuple(x.zfill(2) for x in m.groups())
        start = dt
        end = dt + timedelta(hours=1)
        return (start.strftime("%H"), start.strftime("%M"),
                end.strftime("%H"), end.strftime("%M"))

    def collect_data(self):
        title = self.title_field.get_value().strip()
        if not title:
            messagebox.showerror("Błąd walidacji",
                                 "Zadanie musi mieć nazwę.", parent=self)
            raise ValueError("Brak tytułu")

        desc = self.desc_field.get_value().strip()

        try:
            sh, sm, eh, em = self.time_field.get_values()
            h1, m1, h2, m2 = int(sh), int(sm), int(eh), int(em)
        except ValueError:
            messagebox.showerror("Błąd walidacji",
                                 "Czas musi składać się z cyfr.", parent=self)
            raise ValueError("Time parsing error")

        if not (0 <= h1 <= 23 and 0 <= m1 <= 59):
            messagebox.showerror("Błąd walidacji",
                                 "Niepoprawna godzina rozpoczęcia.", parent=self)
            raise ValueError("Invalid start time")
        if not (0 <= h2 <= 23 and 0 <= m2 <= 59):
            messagebox.showerror("Błąd walidacji",
                                 "Niepoprawna godzina zakończenia.", parent=self)
            raise ValueError("Invalid end time")
        if h1 > h2 or (h1 == h2 and m1 >= m2):
            messagebox.showerror("Błąd walidacji",
                                 "Czas zakończenia musi być późniejszy niż czas rozpoczęcia.",
                                 parent=self)
            raise ValueError("End time before start time")

        sel_date = self.date_field.get_date()
        due_date = datetime(sel_date.year, sel_date.month, sel_date.day, h1, m1)

        time_range_str = f"{h1:02d}:{m1:02d}-{h2:02d}:{m2:02d}"

        if self.chip_habit.is_on():
            # _cycle pochodzi z HabitCyclePopup (klik chipa) lub _initial_cycle
            recurrence = f"{self._cycle} {time_range_str}"
        else:
            recurrence = time_range_str

        return Task(
            id=self.task.id if self.task else 0,
            title=title,
            description=desc,
            due_date=due_date,
            is_done=self.task.is_done if self.task else False,
            priority=self.chip_priority.is_on(),
            category_id=self.cat_field.get_selected_id(),
            created_at=self.task.created_at if self.task else datetime.now(),
            modified_at=datetime.now(),
            is_deleted=False,
            recurrence_rule=recurrence,
        )


# ============================================================
# CategoryFormDialog
# ============================================================

class CategoryFormDialog(Modal):
    DEFAULT_WIDTH = 460
    DEFAULT_HEIGHT = 380

    def __init__(self, parent, repository, category=None):
        self.repository = repository
        self.category = category
        title = "Edytuj kategorię" if category else "Nowa kategoria"
        super().__init__(parent, title=title, show_delete=category is not None)

    def build(self):
        # ---- Nazwa ----
        FieldLabel(self.body, "Nazwa kategorii").pack(fill="x", pady=(0, 4))
        self.name_field = TextField(
            self.body, placeholder="np. Praca, Dom, Hobby",
            initial=self.category.name if self.category else "",
            font_size=15, bold=True)
        self.name_field.pack(fill="x", pady=(0, 18))

        # ---- Kolor ----
        FieldLabel(self.body, "Kolor").pack(fill="x", pady=(0, 4))
        initial_color = (self.category.color if self.category
                         else ColorField.AVAILABLE_COLORS[0][1])
        self.color_field = ColorField(self.body, initial_color)
        self.color_field.pack(fill="x")

    def collect_data(self):
        name = self.name_field.get_value().strip()
        if not name:
            messagebox.showerror("Błąd walidacji",
                                 "Kategoria musi mieć nazwę.", parent=self)
            raise ValueError("Brak nazwy")

        return Category(
            id=self.category.id if self.category else 0,
            name=name,
            color=self.color_field.get_color(),
        )

# ============================================================
# TaskPreviewDialog - read-only podglad zadania
# ============================================================

class TaskPreviewDialog(Modal):
    """Read-only podglad zadania - tylko wyswietla informacje, brak edycji.
    Dostepny z menu zadania w kalendarzu/liscie pod opcja 'Podgląd'."""

    DEFAULT_WIDTH = 480
    DEFAULT_HEIGHT = 520

    def __init__(self, parent, repository, task):
        self.repository = repository
        self.task = task
        super().__init__(parent, title="Podgląd zadania", show_delete=False)

    def build(self):
        # Tytul
        FieldLabel(self.body, "Nazwa").pack(fill="x", pady=(0, 4))
        tk.Label(self.body, text=self.task.title,
                 bg=DIALOG_BG, fg=FG,
                 font=make_font(16, weight="bold"),
                 anchor="w", justify="left",
                 wraplength=400).pack(fill="x", pady=(0, 14))

        # Opis (tylko gdy jest)
        if self.task.description:
            FieldLabel(self.body, "Opis").pack(fill="x", pady=(0, 4))
            tk.Label(self.body, text=self.task.description,
                     bg=DIALOG_BG, fg=INFO_FG,
                     font=make_font(12), anchor="w", justify="left",
                     wraplength=400).pack(fill="x", pady=(0, 14))

        # Data + czas
        FieldLabel(self.body, "Data i czas").pack(fill="x", pady=(0, 4))
        date_str = self.task.due_date.strftime("%d.%m.%Y")
        time_str = ""
        if self.task.recurrence_rule:
            m = re.search(r"(\d{1,2}:\d{2}-\d{1,2}:\d{2})",
                          self.task.recurrence_rule)
            if m:
                time_str = "   •   " + m.group(1).replace("-", " – ")
        tk.Label(self.body, text=date_str + time_str,
                 bg=DIALOG_BG, fg=FG,
                 font=make_font(14), anchor="w").pack(fill="x", pady=(0, 14))

        # Powtarza sie (gdy nawyk)
        if self.task.recurrence_rule:
            m = re.search(r"(\d{1,2}):(\d{2})-(\d{1,2}):(\d{2})",
                          self.task.recurrence_rule)
            prefix = (self.task.recurrence_rule[:m.start()].strip()
                      if m else self.task.recurrence_rule.strip())
            if prefix:
                FieldLabel(self.body, "Powtarza się").pack(fill="x", pady=(0, 4))
                tk.Label(self.body, text=prefix,
                         bg=DIALOG_BG, fg=FG,
                         font=make_font(13), anchor="w").pack(fill="x", pady=(0, 14))

        # Kategoria
        FieldLabel(self.body, "Kategoria").pack(fill="x", pady=(0, 4))
        cat_row = tk.Frame(self.body, bg=DIALOG_BG)
        cat_row.pack(fill="x", pady=(0, 14))

        cat = self.repository.get_category(self.task.category_id) \
            if self.task.category_id else None

        dot = tk.Canvas(cat_row, width=14, height=14, bg=DIALOG_BG,
                        highlightthickness=0)
        if cat:
            dot.create_oval(2, 2, 12, 12, fill=cat.color, outline="")
        else:
            dot.create_oval(2, 2, 12, 12, outline=INFO_FG, width=2, fill=DIALOG_BG)
        dot.pack(side="left", padx=(0, 8))

        tk.Label(cat_row, text=cat.name if cat else "Bez kategorii",
                 bg=DIALOG_BG, fg=FG,
                 font=make_font(13)).pack(side="left")

        # Badge'e: Priorytet + Wykonane
        if self.task.priority or self.task.is_done:
            badges_row = tk.Frame(self.body, bg=DIALOG_BG)
            badges_row.pack(fill="x", pady=(0, 14))

            if self.task.priority:
                tk.Label(badges_row, text="Priorytet",
                         bg=DANGER_FG, fg="white",
                         font=make_font(11, weight="bold"),
                         padx=10, pady=4).pack(side="left", padx=(0, 6))

            if self.task.is_done:
                tk.Label(badges_row, text="Wykonane",
                         bg="#5CB85C", fg="white",
                         font=make_font(11, weight="bold"),
                         padx=10, pady=4).pack(side="left")

    def _build_buttons(self):
        """Nadpisuje - podglad ma tylko jeden przycisk 'Zamknij'."""
        tk.Frame(self._outer, bg=FIELD_BORDER, height=1).pack(
            side="bottom", fill="x", padx=32, pady=(0, 16))
        btn_row = tk.Frame(self._outer, bg=DIALOG_BG)
        btn_row.pack(side="bottom", fill="x", padx=32, pady=(0, 22))
        HoverButton(btn_row, text="Zamknij",
                    font=make_font(13, weight="bold"),
                    bg=BRAND_PRIMARY, fg="white",
                    hover_bg=BRAND_PRIMARY_HOVER,
                    padx=24, pady=10,
                    on_click=self._cancel).pack(side="right")