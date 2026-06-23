"""
Komponenty atomic - male, reuzywalne widgety bez logiki domenowej.
DODANO EFEKTY HOVER ORAZ WYGŁADZONO CHECKMARK.
"""

import tkinter as tk
import tkinter.font as tkfont

from front.theme import BG, FG, DEFAULT_BORDER, FONT_FAMILY


class IconButton(tk.Label):
    def __init__(self, parent, text, font=None, on_click=None,
                 bg=BG, fg=FG, wraplength=400, hover_fg="#1A73E8", hover_bg=None, **kwargs):
        super().__init__(parent, text=text, font=font, bg=bg, fg=fg,
                         cursor="hand2", wraplength=wraplength, **kwargs)
        self._default_fg = fg
        self._default_bg = bg
        self._hover_fg = hover_fg
        self._hover_bg = hover_bg if hover_bg else bg
        self._on_click = on_click or (lambda: None)
        self.bind("<Button-1>", lambda e: self._on_click())
        self.bind("<Enter>", lambda e: self.config(fg=self._hover_fg, bg=self._hover_bg))
        self.bind("<Leave>", lambda e: self.config(fg=self._default_fg, bg=self._default_bg))

    def click(self):
        self._on_click()


class CheckCircle(tk.Canvas):
    def __init__(self, parent, on_click=None, bg=BG):
        super().__init__(parent, bg=bg, highlightthickness=0, cursor="hand2")
        self._on_click = on_click or (lambda: None)
        self._size = 32
        self._done = False
        self._accent_color = FG
        self._on_dark_bg = False
        self._is_hovered = False
        self.config(width=self._size, height=self._size)
        self.bind("<Button-1>", lambda e: self._on_click())
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self._redraw()

    def _on_enter(self, e):
        self._is_hovered = True
        self._redraw()

    def _on_leave(self, e):
        self._is_hovered = False
        self._redraw()

    def set_size(self, size):
        self._size = max(16, size)
        self.config(width=self._size, height=self._size)
        self._redraw()

    def set_state(self, done, accent_color, on_dark_bg=False):
        self._done = done
        self._accent_color = accent_color
        self._on_dark_bg = on_dark_bg
        self._redraw()

    def _redraw(self):
        self.delete("all")
        s = self._size
        margin = max(2, int(s * 0.1))
        # Wygładzone proporcje ptaszka
        tick_coords = [s * 0.30, s * 0.50, s * 0.45, s * 0.65, s * 0.70, s * 0.35]
        if self._done:
            if self._on_dark_bg:
                self.create_oval(margin, margin, s - margin, s - margin,
                                 fill="white", outline="white")
                self.create_line(*tick_coords,
                                 fill=self._accent_color,
                                 width=max(2, int(s * 0.08)),
                                 capstyle="round", joinstyle="round")
            else:
                self.create_oval(margin, margin, s - margin, s - margin,
                                 fill=self._accent_color, outline=self._accent_color)
                self.create_line(*tick_coords,
                                 fill="white",
                                 width=max(2, int(s * 0.08)),
                                 capstyle="round", joinstyle="round")
        else:
            outline = "white" if self._on_dark_bg else FG
            if self._is_hovered and not self._on_dark_bg:
                outline = "#1A73E8"
            self.create_oval(margin, margin, s - margin, s - margin,
                             outline=outline, width=max(2, int(s * 0.06)))


class DropdownButton(tk.Label):
    def __init__(self, parent, text, options, font=None,
                 bg=BG, fg=FG, wraplength=400, hover_fg="#1A73E8",
                 is_selected=None, **kwargs):
        super().__init__(parent, text=text, font=font, bg=bg, fg=fg,
                         cursor="hand2", wraplength=wraplength, **kwargs)
        self._default_fg = fg
        self._hover_fg = hover_fg
        self._opts = options
        # is_selected(label, parent_label) -> bool. Gdy True, item dostaje
        # prefix '✓ ' w menu. None = brak feedbacku (stare zachowanie).
        self._is_selected = is_selected
        self.bind("<Button-1>", self._show_menu)
        self.bind("<Enter>", lambda e: self.config(fg=self._hover_fg))
        self.bind("<Leave>", lambda e: self.config(fg=self._default_fg))

    def set_is_selected(self, fn):
        """Podmien predykat selected (na wypadek gdyby view zmienilo state)."""
        self._is_selected = fn

    def _show_menu(self, event):
        menu = tk.Menu(self, tearoff=0)
        self._populate_menu(menu, self._opts, parent_label=None)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _populate_menu(self, menu, opts, parent_label=None):
        for opt in opts:
            if isinstance(opt, tuple):
                label, second = opt
                if isinstance(second, list):
                    submenu = tk.Menu(menu, tearoff=0)
                    self._populate_menu(submenu, second, parent_label=label)
                    menu.add_cascade(label=self._decorate(label, parent_label),
                                     menu=submenu)
                else:
                    menu.add_command(label=self._decorate(label, parent_label),
                                     command=second or (lambda: None))
            else:
                menu.add_command(label=self._decorate(opt, parent_label),
                                 command=lambda: None)

    def _decorate(self, label, parent_label):
        if self._is_selected is not None and self._is_selected(label, parent_label):
            return f"✓  {label}"
        return label


class ContextMenuButton(tk.Label):
    ICON_TEXT = "\u2022\u2022\u2022"

    def __init__(self, parent, font=None, options=None,
                 bg=BG, fg=FG, **kwargs):
        super().__init__(parent, text=self.ICON_TEXT, font=font, bg=bg, fg=fg,
                         cursor="hand2", wraplength=100, **kwargs)
        self._opts = options if options is not None else [("Edytuj", None), ("Usuń", None)]
        self._default_fg = fg
        self._hover_fg = "#1A73E8" if bg == BG else "#E8EAED"
        self.bind("<Button-1>", self._show_menu)
        self.bind("<Enter>", lambda e: self.config(fg=self._hover_fg))
        self.bind("<Leave>", lambda e: self.config(fg=self._default_fg))

    def _show_menu(self, event):
        menu = tk.Menu(self, tearoff=0)
        for opt in self._opts:
            if isinstance(opt, tuple):
                label, callback = opt
            else:
                label, callback = opt, None
            menu.add_command(label=label, command=callback or (lambda: None))
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()


class ScrollableContent(tk.Frame):
    def __init__(self, parent, bg=BG):
        super().__init__(parent, bg=bg)
        self._canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0)
        scrollbar = tk.Scrollbar(self, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)
        self.container = tk.Frame(self._canvas, bg=bg)
        self._window_id = self._canvas.create_window((0, 0), window=self.container, anchor="nw")
        self.container.bind("<Configure>",
                            lambda e: self._canvas.configure(scrollregion=self._canvas.bbox("all")))
        self._canvas.bind("<Configure>",
                          lambda e: self._canvas.itemconfig(self._window_id, width=e.width))
        self.bind("<Enter>", self._bind_mousewheel)
        self.bind("<Leave>", self._unbind_mousewheel)

    def _bind_mousewheel(self, e):
        self._canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self._canvas.bind_all("<Button-4>", self._on_mousewheel_linux)
        self._canvas.bind_all("<Button-5>", self._on_mousewheel_linux)

    def _unbind_mousewheel(self, e):
        self._canvas.unbind_all("<MouseWheel>")
        self._canvas.unbind_all("<Button-4>")
        self._canvas.unbind_all("<Button-5>")

    def _on_mousewheel(self, e):
        self._canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

    def _on_mousewheel_linux(self, e):
        if e.num == 4:
            self._canvas.yview_scroll(-1, "units")
        elif e.num == 5:
            self._canvas.yview_scroll(1, "units")

    def inner_width(self):
        return self._canvas.winfo_width()


def make_font(size, weight="normal"):
    return tkfont.Font(family=FONT_FAMILY, size=size, weight=weight)


class ChipToggle(tk.Label):
    def __init__(self, parent, text, initial=False, on_change=None, font=None):
        self._on = initial
        self._on_change = on_change or (lambda v: None)
        super().__init__(parent, text=text,
                          font=font or make_font(12),
                          bd=1, relief="solid",
                          padx=14, pady=6,
                          cursor="hand2")
        self.bind("<Button-1>", lambda e: self.toggle())
        self._update_style()

    def _update_style(self):
        if self._on:
            self.config(bg="#1A73E8", fg="white", highlightbackground="#1A73E8")
        else:
            self.config(bg=BG, fg=FG, highlightbackground=DEFAULT_BORDER)

    def toggle(self):
        self._on = not self._on
        self._update_style()
        self._on_change(self._on)

    def set(self, on):
        self._on = bool(on)
        self._update_style()

    def is_on(self):
        return self._on