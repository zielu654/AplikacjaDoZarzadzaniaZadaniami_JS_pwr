"""
Header i Toolbar - elementy gornej czesci widoku, NAD scrollowalnym kontentem.
"""

import tkinter as tk

from front.theme import (
    BG, FG,
    SIZE_LZ_HEADER, SIZE_LZ_TOOLBAR, SIZE_LZ_PLUS,
    LZ_HEADER_SCALE, LZ_TOOLBAR_SCALE, LZ_PLUS_SCALE,
    scaled,
)
from front.components import IconButton, DropdownButton, make_font


class Header(tk.Label):
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


class Toolbar(tk.Frame):
    LIST_PADX = 20
    TOOLBAR_PLUS_PADX = 20
    TOOLBAR_BOT_PADY = 20

    def __init__(self, parent,
                 sort_options=None, filter_options=None, view_options=None,
                 show_add=True, on_sort=None, on_filter=None,
                 on_view=None, on_add=None, on_conflict_check=None,
                 on_sync=None, is_sort_selected=None):
        super().__init__(parent, bg=BG)

        self.on_sort = on_sort or (lambda p, o: None)
        self.on_filter = on_filter or (lambda p, o: None)
        self.on_view = on_view or (lambda p, o: None)
        self.on_add = on_add or (lambda: None)
        self.on_conflict_check = on_conflict_check
        self.on_sync = on_sync

        self.toolbar_font = make_font(SIZE_LZ_TOOLBAR)
        self.plus_font = make_font(SIZE_LZ_PLUS, weight="bold")
        self._widgets = []

        if show_add:
            self.lbl_plus = IconButton(self, text="+", font=self.plus_font,
                                       on_click=self.on_add)
            self.lbl_plus.pack(side="right")
            self._widgets.append((self.lbl_plus, self.plus_font))
        else:
            self.lbl_plus = None

        if sort_options is not None:
            self.lbl_sortuj = DropdownButton(
                self, text="Sortuj", font=self.toolbar_font,
                options=self._wrap_options(sort_options, self.on_sort),
                is_selected=is_sort_selected,
            )
            self.lbl_sortuj.pack(side="right", padx=(0, self.TOOLBAR_PLUS_PADX))
            self._widgets.append((self.lbl_sortuj, self.toolbar_font))
        else:
            self.lbl_sortuj = None

        if self.on_conflict_check is not None:
            self.lbl_conflict = IconButton(
                self, text="Konflikty ⚠",
                font=self.toolbar_font,
                on_click=self.on_conflict_check,
                bg=BG, fg="#C0392B",
            )
            self.lbl_conflict.pack(side="left", padx=(0, 15))
            self._widgets.append((self.lbl_conflict, self.toolbar_font))
        else:
            self.lbl_conflict = None

        if self.on_sync is not None:
            self.lbl_sync = IconButton(
                self, text="↻ Sync",
                font=self.toolbar_font,
                on_click=self.on_sync,
                bg=BG, fg=FG,
            )
            self.lbl_sync.pack(side="left")
            self._widgets.append((self.lbl_sync, self.toolbar_font))
        else:
            self.lbl_sync = None

        self.lbl_filtruj = None
        self.lbl_widok = None

    @staticmethod
    def _wrap_options(options, callback, parent_label=None):
        result = []
        for opt in options:
            if isinstance(opt, tuple) and len(opt) == 2 and isinstance(opt[1], list):
                label, sub = opt
                result.append((label, Toolbar._wrap_options(sub, callback, parent_label=label)))
            elif isinstance(opt, tuple):
                result.append(opt)
            else:
                result.append((opt, lambda o=opt, p=parent_label: callback(p, o)))
        return result

    def update_fonts(self, width, height=None):
        self.toolbar_font.config(size=scaled(width, LZ_TOOLBAR_SCALE))
        self.plus_font.config(size=scaled(width, LZ_PLUS_SCALE))

        wraplength = max(80, width - 40)
        for widget, _ in self._widgets:
            try:
                widget.config(wraplength=wraplength)
            except tk.TclError:
                pass