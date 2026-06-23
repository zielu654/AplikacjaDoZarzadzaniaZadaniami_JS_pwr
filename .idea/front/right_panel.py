"""
RightPanel - prawy panel aplikacji (20% szerokosci okna).

Trzyma elementy ktore wizualnie sa wyciagniete poza srodkowy widok:
  - Widok    - na wysokosci tytulu View (srodek wysokosci Header)
  - Filtruj  - na wysokosci toolbara View (Sortuj+)

Pozycje Widoku i Filtruja sa USTAWIANE DYNAMICZNIE wzgledem rzeczywistych
pozycji elementow w View (przez `sync_with_view()`). To eliminuje rozjazd
ktory wystepowal przy stalych pady - przy roznych rozmiarach fontow
Header i toolbar w View mialy rozne wysokosci niz odpowiadajace im
"sloty" w RightPanel.

Aplikacja powinna wolac `sync_with_view()` po inicjalizacji oraz po
kazdej zmianie skali fontu w View (po update_fonts).
"""

import tkinter as tk

from front.theme import (
    BG, SIZE_LZ_TOOLBAR, LZ_TOOLBAR_SCALE, scaled,
)
from front.components import DropdownButton, make_font
from front.header_toolbar import Toolbar


class RightPanel(tk.Frame):

    HORIZONTAL_PADX = 20  # padding Widok/Filtruj od krawedzi panelu

    def __init__(self, parent,
                 display_mode_options=None, filter_options=None,
                 on_display_mode=None, on_filter=None,
                 is_filter_selected=None, is_display_selected=None):
        super().__init__(parent, bg=BG)

        self.toolbar_font = make_font(SIZE_LZ_TOOLBAR)
        self._widgets = []  # do skalowania wraplength
        self._view = None   # ustawiane w from_view() lub bezposrednio przed sync_with_view()

        # Widok - prawy gorny rog (pozycja Y dyktowana przez Header View, sync_with_view)
        if display_mode_options is not None:
            self.lbl_widok = DropdownButton(
                self, text="Widok", font=self.toolbar_font,
                options=Toolbar._wrap_options(display_mode_options,
                                              on_display_mode or (lambda o: None)),
                is_selected=is_display_selected,
            )
            # place tymczasowo poza widocznym obszarem - sync_with_view ustawi pozycje
            self.lbl_widok.place(relx=1.0, x=-self.HORIZONTAL_PADX, y=0, anchor="ne")
            self._widgets.append(self.lbl_widok)
        else:
            self.lbl_widok = None

        # Filtruj - lewa strona, na wysokosci Toolbar View (pozycja Y przez sync_with_view)
        if filter_options is not None:
            self.lbl_filtruj = DropdownButton(
                self, text="Filtruj", font=self.toolbar_font,
                options=Toolbar._wrap_options(filter_options,
                                              on_filter or (lambda o: None)),
                is_selected=is_filter_selected,
            )
            self.lbl_filtruj.place(x=self.HORIZONTAL_PADX, y=0, anchor="nw")
            self._widgets.append(self.lbl_filtruj)
        else:
            self.lbl_filtruj = None

    @classmethod
    def from_view(cls, parent, view):
        """Factory - tworzy RightPanel z konfiguracji View i podlacza
        view jako referencje do synchronizacji pozycji.

        Predykaty is_*_selected sa zamknieciami nad view - czytaja zywy stan
        (filter_state, display_mode) przy KAZDYM otwarciu menu, wiec ✓ przy
        opcjach pojawia sie/znika automatycznie po kazdym wyborze."""
        instance = cls(parent,
                       display_mode_options=view.display_mode_options,
                       filter_options=view.filter_options,
                       on_display_mode=view.on_display_mode_callback,
                       on_filter=view.on_filter_callback,
                       is_filter_selected=view._filter_is_selected,
                       is_display_selected=view._display_is_selected)
        instance._view = view
        return instance

    def sync_with_view(self, view=None):
        """Pozycjonuje Widok i Filtruj na wysokosci odpowiednich elementow View:
          - Widok    -> srodek wysokosci Header View (na poziomie tytulu)
          - Filtruj  -> srodek wysokosci Toolbar View (na poziomie Sortuj+)

        Wolac po inicjalizacji i po kazdym update_fonts (po renderingu - najlepiej
        przez window.after_idle(right_panel.sync_with_view), zeby winfo_* zwrocilo
        aktualne wartosci po przeskalowaniu fontu)."""
        view = view or self._view
        if view is None:
            return

        view.update_idletasks()
        self.update_idletasks()

        # Wspolny punkt odniesienia: rooty (pozycja absolutna na ekranie),
        # potem odejmujemy rooty RightPanel zeby otrzymac pozycje LOKALNA w RightPanel.
        self_root_y = self.winfo_rooty()

        if self.lbl_widok is not None:
            header = view.header
            header_center_y_screen = header.winfo_rooty() + header.winfo_height() // 2
            widok_y = header_center_y_screen - self_root_y
            self.lbl_widok.place_configure(y=widok_y, anchor="e")

        if self.lbl_filtruj is not None:
            toolbar = view.toolbar
            toolbar_center_y_screen = toolbar.winfo_rooty() + toolbar.winfo_height() // 2
            filtruj_y = toolbar_center_y_screen - self_root_y
            self.lbl_filtruj.place_configure(y=filtruj_y, anchor="w")

    def update_fonts(self, view_width, height=None):
        """view_width: szerokosc View - skalowanie wzgledem niej, zeby fonty
        w RightPanel byly tego samego rozmiaru co w toolbarze View."""
        self.toolbar_font.config(size=scaled(view_width, LZ_TOOLBAR_SCALE))

        wraplength = max(80, self.winfo_width() - 40)
        for w in self._widgets:
            try:
                w.config(wraplength=wraplength)
            except tk.TclError:
                pass