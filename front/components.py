"""
Komponenty atomic - male, reuzywalne widgety bez logiki domenowej.

Te klasy nie wiedza nic o zadaniach, kategoriach ani widokach.
Operuja tylko na tekstach, kolorach i callbackach.
"""

import tkinter as tk
import tkinter.font as tkfont

from front.theme import BG, FG, FONT_FAMILY

# ============================================================
# IconButton - klikalna etykieta tekstowa
# ============================================================


class IconButton(tk.Label):
    """Klikalny Label - uzywany dla Sortuj/Filtruj/Widok/+/...

    wraplength=400 baseline: bez tego, przy bardzo duzych fontach (fullscreen)
    Label bez wraplength potrafi byc renderowany przyciety - zaobserwowane
    empirycznie. Z wraplength (nawet szerokim, ktory w praktyce nigdy nie
    zawinie krotkiego tekstu) renderowanie idzie "bezpieczna sciezka" w Tk.
    """

    def __init__(self, parent, text, font=None, on_click=None, bg=BG, fg=FG, wraplength=400, **kwargs):
        super().__init__(parent, text=text, font=font, bg=bg, fg=fg, cursor="hand2", wraplength=wraplength, **kwargs)
        self._on_click = on_click or (lambda: None)
        self.bind("<Button-1>", lambda e: self._on_click())

    def click(self):
        """Programowe wywolanie on_click - uzyteczne w testach i automatyzacji,
        gdzie event_generate bywa zawodny (np. headless Xvfb na niezapakowanych
        widgetach)."""
        self._on_click()


# ============================================================
# CheckCircle - rysowany checkbox (Canvas zamiast Label)
# ============================================================


class CheckCircle(tk.Canvas):
    """Kolko-checkbox narysowane na Canvasie (create_oval/create_line) zamiast
    znakiem unicode '○' w Labelu. Powod: glif '○' renderowal sie niespojnie
    miedzy srodowiskami (np. jako 'C', bo brakujacy font podstawial cos
    innego). Canvas rysuje wlasny ksztalt - zero zaleznosci od fontu."""

    def __init__(self, parent, on_click=None, bg=BG):
        super().__init__(parent, bg=bg, highlightthickness=0, cursor="hand2")
        self._on_click = on_click or (lambda: None)
        self._size = 32
        self._done = False
        self._accent_color = FG
        self._bg = bg
        self.config(width=self._size, height=self._size)
        self.bind("<Button-1>", lambda e: self._on_click())
        self._redraw()

    def set_size(self, size):
        self._size = max(16, size)
        self.config(width=self._size, height=self._size)
        self._redraw()

    def set_state(self, done, accent_color):
        self._done = done
        self._accent_color = accent_color
        self._redraw()

    def _redraw(self):
        self.delete("all")
        s = self._size
        margin = max(2, int(s * 0.1))
        if self._done:
            # wypelnione kolko w kolorze kategorii + bialy ptaszek
            self.create_oval(
                margin, margin, s - margin, s - margin, fill=self._accent_color, outline=self._accent_color
            )
            self.create_line(
                s * 0.27,
                s * 0.52,
                s * 0.44,
                s * 0.70,
                s * 0.75,
                s * 0.30,
                fill="white",
                width=max(2, int(s * 0.09)),
                capstyle="round",
                joinstyle="round",
            )
        else:
            self.create_oval(margin, margin, s - margin, s - margin, outline=FG, width=max(2, int(s * 0.06)))


# ============================================================
# DropdownButton - klikalny tekst -> rozwijane menu z opcjami
# ============================================================


class DropdownButton(tk.Label):
    """Klikalna etykieta typu Sortuj/Filtruj/Widok. Po klikniecu otwiera
    natywne tk.Menu z lista opcji. Kazda opcja moze miec wlasny callback.

    options: lista stringow (krotka label -> automatyczny pusty callback)
             ALBO lista krotek (label, callback) jesli chcesz callbacki rozne
             per opcja.
    """

    def __init__(self, parent, text, options, font=None, bg=BG, fg=FG, wraplength=400, **kwargs):
        super().__init__(parent, text=text, font=font, bg=bg, fg=fg, cursor="hand2", wraplength=wraplength, **kwargs)
        self._opts = options
        self.bind("<Button-1>", self._show_menu)

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


# ============================================================
# ContextMenuButton - klikalne "..." z menu Edytuj/Dodaj/Usun
# ============================================================


class ContextMenuButton(tk.Label):
    """Klikalne '...' z menu kontekstowym. Domyslne opcje to "Edytuj, Dodaj,
    Usun" (zgodnie z legenda ze szkicow: "Edytuj, Dodaj, Usun zawsze bazowo").

    Mozesz podac wlasne opcje przez `options=[(label, callback), ...]`."""

    DEFAULT_OPTIONS = ("Edytuj", "Dodaj", "Usun")
    ICON_TEXT = "\u2022\u2022\u2022"  # •••

    def __init__(self, parent, font=None, options=None, bg=BG, fg=FG, **kwargs):
        super().__init__(parent, text=self.ICON_TEXT, font=font, bg=bg, fg=fg, cursor="hand2", wraplength=100, **kwargs)
        self._opts = options if options is not None else [(opt, None) for opt in self.DEFAULT_OPTIONS]
        self.bind("<Button-1>", self._show_menu)

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


# ============================================================
# ScrollableContent - canvas + scrollbar + frame, hermetyzuje boilerplate
# ============================================================


class ScrollableContent(tk.Frame):
    """Scrollowalny kontener. Wystawia `.container` (Frame), do ktorego
    pakujesz/grid-ujesz dzieci. Scrollbar po prawej, canvas po lewej,
    mousewheel podlaczony globalnie (do okna), z aktywnoscia przelaczana
    na ten kontener gdy mysz nad nim.

    Uzycie:
        scroll = ScrollableContent(parent)
        scroll.pack(fill='both', expand=True)
        for x in items:
            tk.Label(scroll.container, text=x).pack()
    """

    def __init__(self, parent, bg=BG):
        super().__init__(parent, bg=bg)

        self._canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0)
        scrollbar = tk.Scrollbar(self, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self.container = tk.Frame(self._canvas, bg=bg)
        self._window_id = self._canvas.create_window((0, 0), window=self.container, anchor="nw")

        self.container.bind("<Configure>", lambda e: self._canvas.configure(scrollregion=self._canvas.bbox("all")))
        self._canvas.bind("<Configure>", lambda e: self._canvas.itemconfig(self._window_id, width=e.width))

        # Mousewheel - aktywne gdy mysz nad tym kontenerem
        self.bind("<Enter>", self._bind_mousewheel)
        self.bind("<Leave>", self._unbind_mousewheel)

    def _bind_mousewheel(self, _event):
        self._canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self._canvas.bind_all("<Button-4>", self._on_mousewheel_linux)
        self._canvas.bind_all("<Button-5>", self._on_mousewheel_linux)

    def _unbind_mousewheel(self, _event):
        self._canvas.unbind_all("<MouseWheel>")
        self._canvas.unbind_all("<Button-4>")
        self._canvas.unbind_all("<Button-5>")

    def _on_mousewheel(self, event):
        self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_mousewheel_linux(self, event):
        if event.num == 4:
            self._canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self._canvas.yview_scroll(1, "units")


# ============================================================
# Helper - tworzenie obiektu Font ze wspolnym fallbackiem rodziny
# ============================================================


def make_font(size, weight="normal"):
    return tkfont.Font(family=FONT_FAMILY, size=size, weight=weight)
