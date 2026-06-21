"""
Header i Toolbar - elementy gornej czesci widoku, NAD scrollowalnym kontentem.

Header to po prostu tytul widoku ("Nawyki", "Wszystkie", "Kategoria 1"...).
Toolbar jest konfigurowalny:
  - left:   opcjonalny DropdownButton "Sortuj" z lista opcji
  - center: opcjonalny IconButton "+" (dodawanie zadania w kontekscie widoku)
  - right:  do dwoch DropdownButtonow: "Widok" i "Filtruj"

W roznych widokach toolbar wyglada inaczej:
  - Nawyki:    Sortuj  +  Filtruj
  - Kategoria: Sortuj  +  Filtruj
  - Dzis:           +  Filtruj  Widok   (BEZ Sortuj)
"""

import tkinter as tk

from front.theme import (
    BG, FG,
    SIZE_LZ_HEADER, SIZE_LZ_TOOLBAR, SIZE_LZ_PLUS,
    LZ_HEADER_SCALE, LZ_TOOLBAR_SCALE, LZ_PLUS_SCALE,
    scaled,
)
from front.components import IconButton, DropdownButton, make_font


# ============================================================
# Header - tytul widoku
# ============================================================

class Header(tk.Label):
    """Tytul widoku - duzy bold tekst nad toolbarem."""

    HEADER_TOP_PADY = 20
    HEADER_BOT_PADY = 10

    def __init__(self, parent, text):
        self.font = make_font(SIZE_LZ_HEADER)
        super().__init__(parent, text=text, font=self.font, bg=BG, fg=FG,
                         wraplength=600)

    def set_text(self, text):
        self.config(text=text)

    def update_fonts(self, width, height=None):
        self.font.config(size=scaled(width, LZ_HEADER_SCALE))
        self.config(wraplength=max(150, width - 40))


# ============================================================
# Toolbar - konfigurowalny pasek narzedzi
# ============================================================

class Toolbar(tk.Frame):
    """Pasek narzedzi pod naglowkiem widoku.

    Konstruktor:
      parent
      sort_options    - lista stringow (Sortuj). None => brak Sortuj.
      filter_options  - lista stringow (Filtruj). None => brak Filtruj.
      view_options    - lista stringow (Widok). None => brak Widok.
      show_add        - czy pokazac "+" (dodawanie zadania). default True.
      on_sort         - callback(opcja: str) gdy user wybierze opcje z menu Sortuj
      on_filter       - analogicznie
      on_view         - analogicznie
      on_add          - callback bez argumentow (klik na "+")

    Wszystkie callbacki sa opcjonalne (default pass). Klikalnosc jest, logika
    domeny (co znaczy "sortuj po dacie") nie jest w toolbarze - to widok
    decyduje.
    """

    LIST_PADX = 20
    TOOLBAR_PLUS_PADX = 20
    TOOLBAR_BOT_PADY = 20

    def __init__(self, parent,
                 sort_options=None, filter_options=None, view_options=None,
                 show_add=True,
                 on_sort=None, on_filter=None, on_view=None, on_add=None):
        super().__init__(parent, bg=BG)

        self.on_sort = on_sort or (lambda opt: None)
        self.on_filter = on_filter or (lambda opt: None)
        self.on_view = on_view or (lambda opt: None)
        self.on_add = on_add or (lambda: None)

        # Fonty
        self.toolbar_font = make_font(SIZE_LZ_TOOLBAR)
        self.plus_font = make_font(SIZE_LZ_PLUS, weight="bold")

        self._widgets = []  # lista (widget, font) do skalowania

        # LEWO: Sortuj
        if sort_options is not None:
            self.lbl_sortuj = DropdownButton(
                self, text="Sortuj", font=self.toolbar_font,
                options=[(opt, lambda o=opt: self.on_sort(o)) for opt in sort_options],
            )
            self.lbl_sortuj.pack(side="left")
            self._widgets.append((self.lbl_sortuj, self.toolbar_font))
        else:
            self.lbl_sortuj = None

        # PRAWO (pakowane w kolejnosci: Filtruj najpierw, Widok pozniej -
        # side='right' wpycha najpierw spakowane najbardziej w prawo).
        if filter_options is not None:
            self.lbl_filtruj = DropdownButton(
                self, text="Filtruj", font=self.toolbar_font,
                options=[(opt, lambda o=opt: self.on_filter(o)) for opt in filter_options],
            )
            self.lbl_filtruj.pack(side="right")
            self._widgets.append((self.lbl_filtruj, self.toolbar_font))
        else:
            self.lbl_filtruj = None

        if view_options is not None:
            self.lbl_widok = DropdownButton(
                self, text="Widok", font=self.toolbar_font,
                options=[(opt, lambda o=opt: self.on_view(o)) for opt in view_options],
            )
            self.lbl_widok.pack(side="right", padx=(0, 20))
            self._widgets.append((self.lbl_widok, self.toolbar_font))
        else:
            self.lbl_widok = None

        # SRODEK: "+"
        if show_add:
            self.lbl_plus = IconButton(self, text="+", font=self.plus_font,
                                       on_click=self.on_add)
            # Padx 20 zeby + nie kleil sie do "Filtruj" / "Widok"
            self.lbl_plus.pack(side="right", padx=self.TOOLBAR_PLUS_PADX)
            self._widgets.append((self.lbl_plus, self.plus_font))
        else:
            self.lbl_plus = None

    def update_fonts(self, width, height=None):
        self.toolbar_font.config(size=scaled(width, LZ_TOOLBAR_SCALE))
        self.plus_font.config(size=scaled(width, LZ_PLUS_SCALE))

        wraplength = max(80, width - 40)
        for widget, _ in self._widgets:
            try:
                widget.config(wraplength=wraplength)
            except tk.TclError:
                pass
