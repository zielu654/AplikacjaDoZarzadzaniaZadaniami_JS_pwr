"""
Sidebar - nowoczesny, czysty layout.
Kategorie mają kolorowe kropki zamiast pełnych pasków.
Efekt szarego podświetlenia po najechaniu myszką.
"""

import tkinter as tk
import tkinter.font as tkfont

from front.theme import (
    BG, FG, INFO_FG, ON_COLOR_FG, PRIORYTETOWE_COLOR,
    SIZE_SIDEBAR, SIDEBAR_SCALE,
    SIDEBAR_TOP_PAD_FACTOR, SIDEBAR_BOT_PAD_FACTOR,
    SIDEBAR_HEADER_GAP_MULTIPLIER, SIDEBAR_HEADER_HEIGHT_MULTIPLIER,
    scaled,
)
from front.components import IconButton, ContextMenuButton, make_font


KEY_DZIS = "dzis"
KEY_WSZYSTKIE = "wszystkie"
KEY_NAWYKI = "nawyki"
KEY_PRIORYTETOWE = "priorytetowe"
KEY_CATEGORY_PREFIX = "kategoria_"


class SidebarHeader(tk.Label):
    def __init__(self, parent, text, font):
        super().__init__(parent, text=text, font=font, bg=BG, fg=FG,
                         anchor="center", justify="center", wraplength=400)


class SidebarKategorieHeader(tk.Frame):
    def __init__(self, parent, text, font, on_add=None):
        super().__init__(parent, bg=BG)
        self.on_add = on_add or (lambda: None)

        self.label = tk.Label(self, text=text, font=font, bg=BG, fg=FG,
                               cursor="hand2")
        self.label.bind("<Button-1>", lambda e: self.on_add())
        self.label.pack(side="left")

        self.btn_plus = tk.Label(self, text="+", font=font, bg=BG, fg=FG,
                                  cursor="hand2", padx=4)
        self.btn_plus.bind("<Button-1>", lambda e: self.on_add())
        self.btn_plus.pack(side="left", padx=(10, 0))

    def update_wraplength(self, wraplength):
        btn_font = tkfont.Font(font=self.btn_plus.cget("font"))
        plus_w = btn_font.measure("+") + 25
        label_slot = max(80, wraplength - plus_w)
        self.label.config(wraplength=label_slot)


class SidebarItem(IconButton):
    def __init__(self, parent, text, font, on_click=None):
        super().__init__(parent, text=text, font=font, on_click=on_click,
                         bg=BG, fg=FG, anchor="center", justify="center",
                         hover_bg="#F1F3F4")


class SidebarColorRow(tk.Frame):
    """Nowoczesny pasek kategorii. Posiada kolorową kropkę i efekt hover."""

    def __init__(self, parent, text, color, font, on_click=None,
                 context_options=None):
        super().__init__(parent, bg=BG)
        self._on_click = on_click or (lambda: None)

        # Kropka identyfikacyjna zamiast pełnego tła
        self.dot = tk.Canvas(self, width=24, height=24, bg=BG, highlightthickness=0)
        self.dot.create_oval(6, 6, 18, 18, fill=color, outline="")
        self.dot.pack(side="left", padx=(10, 0))

        self.menu_btn = ContextMenuButton(self, font=font, options=context_options,
                                          bg=BG, fg=INFO_FG)
        self.menu_btn.pack(side="right", padx=(5, 12))

        self.label = tk.Label(self, text=text, font=font, bg=BG, fg=FG,
                               cursor="hand2", anchor="w", justify="left",
                               wraplength=400)
        self.label.pack(side="left", fill="x", expand=True, padx=(10, 5))

        self.label.bind("<Button-1>", lambda e: self._on_click())
        self.dot.bind("<Button-1>", lambda e: self._on_click())
        self.bind("<Button-1>", lambda e: self._on_click())

        self._bind_hover(self, self.dot, self.label, self.menu_btn)

    def _bind_hover(self, *widgets):
        for w in widgets:
            w.bind("<Enter>", self._on_enter, add="+")
            w.bind("<Leave>", self._on_leave, add="+")

    def _on_enter(self, e):
        hover_bg = "#F1F3F4"
        self.config(bg=hover_bg)
        self.dot.config(bg=hover_bg)
        self.label.config(bg=hover_bg)
        self.menu_btn.config(bg=hover_bg)

    def _on_leave(self, e):
        self.config(bg=BG)
        self.dot.config(bg=BG)
        self.label.config(bg=BG)
        self.menu_btn.config(bg=BG)

    def click(self):
        self._on_click()

    def update_wraplength(self, wraplength):
        btn_font = tkfont.Font(font=self.menu_btn.cget("font"))
        menu_text_w = btn_font.measure(self.menu_btn.cget("text"))
        menu_w = menu_text_w + 17
        label_pad = 26
        label_slot = max(80, wraplength - menu_w - label_pad - 20)
        self.label.config(wraplength=label_slot)
        self.menu_btn.config(wraplength=100)


class Sidebar(tk.Frame):
    SPACER_ROW = 1

    def __init__(self, parent, repository,
                 on_dodaj_zadanie=None, on_select=None,
                 on_category_menu=None, on_dodaj_kategoria=None):
        super().__init__(parent, bd=0, bg=BG, padx=10, pady=10)
        self.repository = repository
        self.on_dodaj_zadanie = on_dodaj_zadanie or (lambda: None)
        self.on_select = on_select or (lambda key: None)
        self.on_category_menu = on_category_menu or (lambda cat, action: None)
        self.on_dodaj_kategoria = on_dodaj_kategoria or (lambda: None)

        self.header_font = make_font(SIZE_SIDEBAR, weight="bold")
        self.item_font = make_font(SIZE_SIDEBAR)

        self.columnconfigure(0, weight=1, minsize=80)
        self.entries = []
        self._build()

    def refresh(self):
        for e in self.entries:
            e["widget"].destroy()
        self.entries = []
        self._build()
        if self.winfo_width() > 1:
            self.update_fonts(self.winfo_width(), self.winfo_height())

    def _build(self):
        self._add_dodaj_zadanie_row(row=0)
        row = self.SPACER_ROW + 1

        for text, key in (("Dziś", KEY_DZIS),
                          ("Wszystkie", KEY_WSZYSTKIE),
                          ("Nawyki", KEY_NAWYKI)):
            self._add_item(text, key, row)
            row += 1

        self._add_kategorie_header(row=row, extra_gap=True)
        row += 1

        self._add_color_row(text="Priorytetowe", color=PRIORYTETOWE_COLOR,
                            row=row, key=KEY_PRIORYTETOWE, category=None)
        row += 1

        for category in self.repository.get_categories():
            self._add_color_row(text=category.name, color=category.color,
                                row=row,
                                key=f"{KEY_CATEGORY_PREFIX}{category.id}",
                                category=category)
            row += 1

    def _add_dodaj_zadanie_row(self, row):
        widget = IconButton(self, text="Dodaj zadanie  +",
                            font=self.header_font,
                            on_click=self.on_dodaj_zadanie,
                            bg=BG, fg=FG,
                            anchor="center", justify="center",
                            hover_bg="#F1F3F4")
        widget.grid(row=row, column=0, sticky="nsew", pady=(10, 5))
        self.entries.append({"widget": widget, "row": row, "kind": "dodaj",
                             "color_row": False, "extra_gap": False})

    def _add_header(self, text, row, extra_gap=False):
        widget = SidebarHeader(self, text, self.header_font)
        widget.grid(row=row, column=0, sticky="nsew", pady=(10, 5))
        self.entries.append({"widget": widget, "row": row, "kind": "header",
                             "color_row": False, "extra_gap": extra_gap})

    def _add_kategorie_header(self, row, extra_gap=False):
        widget = SidebarKategorieHeader(self, "Kategorie", self.header_font,
                                         on_add=self.on_dodaj_kategoria)
        widget.grid(row=row, column=0, pady=(10, 5))
        self.entries.append({"widget": widget, "row": row, "kind": "kategorie_header",
                             "color_row": False, "extra_gap": extra_gap})

    def _add_item(self, text, key, row):
        widget = SidebarItem(self, text, self.item_font,
                             on_click=lambda k=key: self.on_select(k))
        widget.grid(row=row, column=0, pady=(10, 5))
        self.entries.append({"widget": widget, "row": row, "kind": "item",
                             "color_row": False, "extra_gap": False})

    def _add_color_row(self, text, color, row, key, category):
        widget = SidebarColorRow(
            self, text=text, color=color, font=self.item_font,
            on_click=lambda k=key: self.on_select(k),
            context_options=[
                ("Edytuj", lambda c=category: self.on_category_menu(c, "edit")),
                ("Usuń",   lambda c=category: self.on_category_menu(c, "delete")),
            ],
        )
        widget.grid(row=row, column=0, sticky="ew", pady=(8, 4))
        self.entries.append({"widget": widget, "row": row, "kind": "color",
                             "color_row": True, "extra_gap": False})

    def update_fonts(self, width, height=None):
        new_size = scaled(width, SIDEBAR_SCALE)
        self.header_font.config(size=new_size)
        self.item_font.config(size=new_size)

        top_pad = max(10, int(width * SIDEBAR_TOP_PAD_FACTOR))
        bot_pad = max(5, int(width * SIDEBAR_BOT_PAD_FACTOR))
        item_wraplength = max(150, width - 20)

        for entry in self.entries:
            w = entry["widget"]
            actual_top = int(top_pad * SIDEBAR_HEADER_GAP_MULTIPLIER) if entry["extra_gap"] else top_pad
            w.grid_configure(pady=(actual_top, bot_pad))

            if entry["color_row"] or entry["kind"] == "kategorie_header":
                w.update_wraplength(item_wraplength)
            else:
                try:
                    w.config(wraplength=item_wraplength)
                except tk.TclError:
                    pass

        self.rowconfigure(self.SPACER_ROW,
                          minsize=max(10, int(width * SIDEBAR_TOP_PAD_FACTOR)))

        row_height = new_size + top_pad + bot_pad + 6
        for entry in self.entries:
            if entry["kind"] == "kategorie_header" and entry["extra_gap"]:
                minsize = int(row_height * SIDEBAR_HEADER_HEIGHT_MULTIPLIER)
            else:
                minsize = row_height
            self.rowconfigure(entry["row"], minsize=minsize)