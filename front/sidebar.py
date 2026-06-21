"""
Sidebar - lewa kolumna aplikacji.

Struktura:
  - "Dodaj zadanie" + klikalny "+"    (na gorze, akcja globalna)
  - Pozycje nawigacyjne: Dzis / Wszystkie / Nawyki  (klikalne, biale tlo)
  - Naglowek "Kategorie"
  - "Priorytetowe" + "..."   (czerwony pasek pelny, hardcoded)
  - Kategorie z repozytorium: kazda kolorowy pasek + "..."  (dynamicznie)

Klasy:
  - SidebarItem        - bialy klikalny tekst (Dzis/Wszystkie/Nawyki)
  - SidebarHeader      - bold tekst (Dodaj zadanie / Kategorie)
  - SidebarColorRow    - kolorowy pasek z tekstem + "..." po prawej
  - Sidebar            - kontener skladajacy wszystko z repozytorium

Wszystkie kliki przyjmuja callbacki - na razie pass na zewnatrz, mechanika
podmiany widokow nie jest implementowana w tej iteracji.
"""

import tkinter as tk

from front.theme import (
    BG, FG, ON_COLOR_FG, PRIORYTETOWE_COLOR,
    SIZE_SIDEBAR, SIDEBAR_SCALE,
    SIDEBAR_TOP_PAD_FACTOR, SIDEBAR_BOT_PAD_FACTOR,
    SIDEBAR_HEADER_GAP_MULTIPLIER, SIDEBAR_HEADER_HEIGHT_MULTIPLIER,
    scaled,
)
from front.components import IconButton, ContextMenuButton, make_font


# klucze przekazywane do on_select callbackow
KEY_DZIS = "dzis"
KEY_WSZYSTKIE = "wszystkie"
KEY_NAWYKI = "nawyki"
KEY_PRIORYTETOWE = "priorytetowe"
KEY_CATEGORY_PREFIX = "kategoria_"


# ============================================================
# Pojedyncze rzedy sidebara - 3 odmiany
# ============================================================

class SidebarHeader(tk.Label):
    """Niemodyfikowalny, niemajacy kursora bold tekst (Dodaj zadanie / Kategorie).

    'Dodaj zadanie' tez jest "headerem" stylem (bold, wieksze od pozycji
    nawigacyjnych), ale ma obok klikalny "+". To jest sklad robiony przez
    Sidebar.__init__, nie samej tej klasy."""

    def __init__(self, parent, text, font):
        super().__init__(parent, text=text, font=font, bg=BG, fg=FG,
                         anchor="center", justify="center", wraplength=400)


class SidebarItem(IconButton):
    """Klikalna pozycja nawigacyjna na bialym tle (Dzis/Wszystkie/Nawyki)."""

    def __init__(self, parent, text, font, on_click=None):
        super().__init__(parent, text=text, font=font, on_click=on_click,
                         bg=BG, fg=FG, anchor="center", justify="center")


class SidebarColorRow(tk.Frame):
    """Kolorowy pasek z tekstem (klikalny) + "..." po prawej (klikalne menu).

    Cala lewa czesc (tekst i tlo) dziala jako klik nawigujacy do widoku
    kategorii / Priorytetowych. Prawa czesc to przycisk menu kontekstowego
    z "Edytuj/Dodaj/Usun".
    """

    def __init__(self, parent, text, color, font, on_click=None,
                 context_options=None):
        super().__init__(parent, bg=color)
        self._on_click = on_click or (lambda: None)
        # Pakujemy menu_btn pierwszy (side=right), zeby label z tekstem
        # rozpychal sie wypelniajac wszystko po lewej.
        self.menu_btn = ContextMenuButton(self, font=font, options=context_options,
                                          bg=color, fg=ON_COLOR_FG)
        self.menu_btn.pack(side="right", padx=(5, 12))

        self.label = tk.Label(self, text=text, font=font, bg=color,
                               fg=ON_COLOR_FG, cursor="hand2",
                               anchor="center", justify="center",
                               wraplength=400)
        self.label.pack(side="left", fill="x", expand=True, padx=(12, 5))
        self.label.bind("<Button-1>", lambda e: self._on_click())

    def click(self):
        """Programowe wywolanie on_click (jak IconButton.click())."""
        self._on_click()

    def update_wraplength(self, wraplength):
        # label dzieli szerokosc z menu_btn (•••). Bez tego odejmowania label
        # dostaje za duzo i nie zawija sie - tekst "Priorytetowe"/"Kategoria 1"
        # przy duzym foncie nie miesci sie w jego realnym slocie i widac
        # symetryczne obciecie z lewej i prawej (anchor=center).
        # update_idletasks zeby winfo_reqwidth zwrocil aktualny rozmiar
        # po ewentualnej zmianie fontu.
        self.update_idletasks()
        menu_w = self.menu_btn.winfo_reqwidth() + 17    # + padx menu_btn (5+12)
        label_pad = 17                                   # padx label (12+5)
        label_slot = max(80, wraplength - menu_w - label_pad)
        self.label.config(wraplength=label_slot)
        self.menu_btn.config(wraplength=100)             # ••• mieści się w 100px na każdym foncie


# ============================================================
# Sidebar - kontener
# ============================================================

class Sidebar(tk.Frame):
    """Lewy panel aplikacji.

    Konstruktor:
      parent              - rodzic tk
      repository          - obiekt z get_categories() (TaskRepository)
      on_dodaj_zadanie    - callback bez argumentow (klik na "+")
      on_select           - callback(key) gdy user klika pozycje nawigacyjna;
                            klucze: KEY_DZIS, KEY_WSZYSTKIE, KEY_NAWYKI,
                            KEY_PRIORYTETOWE, KEY_CATEGORY_PREFIX + str(id)
      on_category_menu    - callback(category_or_None) gdy user klika "..."
                            na pozycji kategorii (None = Priorytetowe)
    """

    SPACER_ROW = 1  # pusty wiersz odstepnik miedzy "Dodaj zadanie" a Dzis

    def __init__(self, parent, repository,
                 on_dodaj_zadanie=None, on_select=None, on_category_menu=None):
        super().__init__(parent, bd=1, bg=BG, padx=10, pady=10)
        self.repository = repository
        self.on_dodaj_zadanie = on_dodaj_zadanie or (lambda: None)
        self.on_select = on_select or (lambda key: None)
        self.on_category_menu = on_category_menu or (lambda cat: None)

        # Fonty (skalowane pozniej przez update_fonts)
        self.header_font = make_font(SIZE_SIDEBAR, weight="bold")
        self.item_font = make_font(SIZE_SIDEBAR)

        self.columnconfigure(0, weight=1, minsize=80)

        # Lista wpisow: {widget, row, kind: 'header'|'item'|'color',
        #                color_row: bool (czy potrzebuje update_wraplength),
        #                extra_gap: bool}
        self.entries = []
        self._build()

    # -------- budowa --------

    def _build(self):
        # Wiersz "Dodaj zadanie" + "+"
        self._add_dodaj_zadanie_row(row=0)

        # Spacer
        row = self.SPACER_ROW + 1

        # Pozycje nawigacyjne
        for text, key in (("Dziś", KEY_DZIS),
                          ("Wszystkie", KEY_WSZYSTKIE),
                          ("Nawyki", KEY_NAWYKI)):
            self._add_item(text, key, row)
            row += 1

        # Naglowek "Kategorie"
        self._add_header("Kategorie", row=row, extra_gap=True)
        row += 1

        # "Priorytetowe" - hardcoded pseudokategoria
        self._add_color_row(text="Priorytetowe", color=PRIORYTETOWE_COLOR,
                            row=row, key=KEY_PRIORYTETOWE, category=None)
        row += 1

        # Kategorie z repozytorium
        for category in self.repository.get_categories():
            self._add_color_row(text=category.name, color=category.color,
                                row=row,
                                key=f"{KEY_CATEGORY_PREFIX}{category.id}",
                                category=category)
            row += 1

    def _add_dodaj_zadanie_row(self, row):
        # "Dodaj zadanie  +" jako jeden klikalny IconButton (calosc otwiera
        # dialog tworzenia zadania - to ta sama akcja co osobny "+"). Dwie
        # spacje przed plusem dla wizualnego oddzielenia.
        widget = IconButton(self, text="Dodaj zadanie  +",
                            font=self.header_font,
                            on_click=self.on_dodaj_zadanie,
                            bg=BG, fg=FG,
                            anchor="center", justify="center")
        widget.grid(row=row, column=0, sticky="nsew", pady=(10, 5))
        self.entries.append({"widget": widget, "row": row, "kind": "dodaj",
                             "color_row": False, "extra_gap": False})

    def _add_header(self, text, row, extra_gap=False):
        widget = SidebarHeader(self, text, self.header_font)
        widget.grid(row=row, column=0, sticky="nsew", pady=(10, 5))
        self.entries.append({"widget": widget, "row": row, "kind": "header",
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
                ("Edytuj", lambda c=category: self.on_category_menu(c)),
                ("Dodaj",  lambda c=category: self.on_category_menu(c)),
                ("Usun",   lambda c=category: self.on_category_menu(c)),
            ],
        )
        widget.grid(row=row, column=0, sticky="ew", pady=(8, 4))
        self.entries.append({"widget": widget, "row": row, "kind": "color",
                             "color_row": True, "extra_gap": False})

    # -------- responsywnosc --------

    def update_fonts(self, width, height=None):
        new_size = scaled(width, SIDEBAR_SCALE)
        self.header_font.config(size=new_size)
        self.item_font.config(size=new_size)

        top_pad = max(10, int(width * SIDEBAR_TOP_PAD_FACTOR))
        bot_pad = max(5, int(width * SIDEBAR_BOT_PAD_FACTOR))

        # Wraplength wszystkich pozycji = niemal cala szerokosc panelu
        # (bezpieczenstwo renderowania - patrz IconButton).
        item_wraplength = max(150, width - 20)

        for entry in self.entries:
            w = entry["widget"]
            actual_top = int(top_pad * SIDEBAR_HEADER_GAP_MULTIPLIER) if entry["extra_gap"] else top_pad
            w.grid_configure(pady=(actual_top, bot_pad))

            # Wraplength: w SidebarColorRow trzeba zejsc do labela i menu,
            # w pozostalych (IconButton/SidebarItem/SidebarHeader) to zwykly Label.
            if entry["color_row"]:
                w.update_wraplength(item_wraplength)
            else:
                try:
                    w.config(wraplength=item_wraplength)
                except tk.TclError:
                    pass

        # Spacer
        self.rowconfigure(self.SPACER_ROW,
                          minsize=max(10, int(width * SIDEBAR_TOP_PAD_FACTOR)))

        # Minimalna wysokosc wierszy (grid sam nie przelicza po zmianie fontu)
        row_height = new_size + top_pad + bot_pad + 6
        for entry in self.entries:
            if entry["kind"] == "header" and entry["extra_gap"]:
                minsize = int(row_height * SIDEBAR_HEADER_HEIGHT_MULTIPLIER)
            else:
                minsize = row_height
            self.rowconfigure(entry["row"], minsize=minsize)
