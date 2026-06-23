"""
System powiadomień - na razie ConflictNotification.

ConflictNotification - Toplevel pokazujący konflikty czasowe zadań.
Pojawia sie w prawym-dolnym rogu okna rodzica, nie blokuje (nie ma grab_set).
Zamkniecie: przycisk "OK" lub klik X.

Wykrywanie konfliktu:
  Dwa zadania kolidują jesli sa tego samego dnia i ich zakresy godzinowe
  nakladaja sie. Zakres pochodzi z _task_time_range (recurrence_rule parsuje
  HH:MM-HH:MM, fallback = start + 30min).

Uzycie:
    conflicts = find_conflicts(tasks, repository)
    if conflicts:
        ConflictNotification(parent_window, conflicts)
    # else: mozna wyswietlic krotki toast "Brak konfliktow"
"""

import tkinter as tk
from front.theme import BG, FG, INFO_FG, ON_COLOR_FG, PRIORYTETOWE_COLOR
from front.components import make_font
from front.views.time_blocks import _task_time_range, _accent_color_for_task


# ============================================================
# Wykrywanie konfliktow
# ============================================================

def find_conflicts(tasks, repository):
    """Zwraca liste tupli (task_a, task_b) gdzie zakresy czasowe sie nakladaja
    i oba zadania sa tego samego dnia. Tylko nieusniete i nieukonczone zadania.

    Nakladanie sie = start_a < end_b AND start_b < end_a (klasyczny overlap).
    """
    active = [t for t in tasks if not t.is_done and not t.is_deleted]
    conflicts = []
    for i, a in enumerate(active):
        for b in active[i + 1:]:
            # Musza byc tego samego dnia
            if a.due_date.date() != b.due_date.date():
                continue
            a_start, a_end = _task_time_range(a)
            b_start, b_end = _task_time_range(b)
            # Overlap: a zaczyna sie przed koncem b I b zaczyna sie przed koncem a
            if a_start < b_end and b_start < a_end:
                conflicts.append((a, b))
    return conflicts


# ============================================================
# ConflictNotification
# ============================================================

class ConflictNotification(tk.Toplevel):
    """Powiadomienie o konfliktach czasowych. Nieblokujace, pojawia sie
    w prawym-dolnym rogu okna rodzica."""

    WIDTH = 320

    def __init__(self, parent, conflicts, repository=None):
        super().__init__(parent)
        self.repository = repository
        self.overrideredirect(False)  # rama okna (X jest dostepny)
        self.configure(bg="white")
        self.resizable(False, False)
        self.title("Konflikty czasowe")

        # Pozycjonowanie - prawy dolny rog rodzica (tymczasowo y=0, po build poprawiamy)
        parent.update_idletasks()
        px = parent.winfo_rootx() + parent.winfo_width() - self.WIDTH - 20
        self.geometry(f"{self.WIDTH}x400+{max(0, px)}+20")

        self._build(conflicts)

        # Po zbudowaniu - finalna pozycja (znamy juz wysokosc)
        self.update_idletasks()
        actual_h = self.winfo_reqheight()
        py = parent.winfo_rooty() + parent.winfo_height() - actual_h - 20
        px = parent.winfo_rootx() + parent.winfo_width() - self.WIDTH - 20
        self.geometry(f"{self.WIDTH}x{actual_h}+{max(0, px)}+{max(0, py)}")

        # Nie blokujemy rodzica - powiadomienie moze byc obok
        self.transient(parent)
        self.lift()

    def _build(self, conflicts):
        # Naglowek
        header = tk.Frame(self, bg=PRIORYTETOWE_COLOR)
        header.pack(fill="x")

        icon_lbl = tk.Label(header, text="⚠", font=make_font(16),
                             bg=PRIORYTETOWE_COLOR, fg="white", padx=10, pady=8)
        icon_lbl.pack(side="left")

        title_lbl = tk.Label(header, text="Konflikty czasowe",
                              font=make_font(13, weight="bold"),
                              bg=PRIORYTETOWE_COLOR, fg="white", pady=8)
        title_lbl.pack(side="left")

        count_lbl = tk.Label(header, text=f"  {len(conflicts)}",
                              font=make_font(13, weight="bold"),
                              bg=PRIORYTETOWE_COLOR, fg="white")
        count_lbl.pack(side="left")

        # Lista konfliktow
        body = tk.Frame(self, bg="white")
        body.pack(fill="both", expand=True, padx=12, pady=8)

        if not conflicts:
            tk.Label(body, text="Brak konfliktów ✓",
                      font=make_font(12), bg="white", fg="#5CB85C",
                      pady=8).pack()
        else:
            for a, b in conflicts:
                self._add_conflict_row(body, a, b)

        # Przycisk OK
        btn_row = tk.Frame(self, bg="white")
        btn_row.pack(fill="x", padx=12, pady=(0, 12))

        ok_btn = tk.Label(btn_row, text="OK",
                           font=make_font(12, weight="bold"),
                           bg=FG, fg="white",
                           padx=28, pady=8,
                           cursor="hand2")
        ok_btn.bind("<Button-1>", lambda e: self.destroy())
        ok_btn.pack(side="right")

    def _add_conflict_row(self, parent, a, b):
        """Jeden wiersz konfliktu: data + czas + nazwy zadań z kolorowymi paskami."""
        from front.views.time_blocks import _task_time_range
        a_start, a_end = _task_time_range(a)
        b_start, b_end = _task_time_range(b)

        row = tk.Frame(parent, bg="white", bd=1, relief="solid")
        row.pack(fill="x", pady=3)

        # Data i czas nakladania
        date_str = a.due_date.strftime("%d.%m  ")
        time_str = f"{max(a_start, b_start).strftime('%H:%M')} – {min(a_end, b_end).strftime('%H:%M')}"
        tk.Label(row, text=f"  {date_str}{time_str}",
                  font=make_font(10), bg="white", fg=INFO_FG,
                  anchor="w").pack(fill="x", padx=4, pady=(4, 2))

        # Pasek z nazwa zadania A
        color_a = _accent_color_for_task(a, self.repository) if self.repository else "#888"
        ta = tk.Label(row, text=f"  {a.title}",
                       font=make_font(11), bg=color_a, fg=ON_COLOR_FG,
                       anchor="w", pady=3)
        ta.pack(fill="x", padx=4, pady=(0, 2))

        # Vs separator
        tk.Label(row, text="  nakłada się z",
                  font=make_font(9), bg="white", fg=INFO_FG,
                  anchor="w").pack(fill="x", padx=4)

        # Pasek z nazwa zadania B
        color_b = _accent_color_for_task(b, self.repository) if self.repository else "#888"
        tb = tk.Label(row, text=f"  {b.title}",
                       font=make_font(11), bg=color_b, fg=ON_COLOR_FG,
                       anchor="w", pady=3)
        tb.pack(fill="x", padx=4, pady=(2, 4))