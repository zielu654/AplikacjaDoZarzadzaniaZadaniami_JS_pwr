"""
Stale wizualne (kolory, czcionki) i parametry skalowania.

Wszystkie magic numbers w jednym miejscu. Plik nie ma kodu UI, tylko stale
i jednego helpera (scaled) do liczenia rozmiaru czcionki z szerokoscia.
"""

# ============================================================
# KOLORY
# ============================================================
BG = "white"                  # tlo paneli i labeli
FG = "black"                  # glowny kolor tekstu
INFO_FG = "#555555"           # drugorzedny tekst (powtarzalnosc, godziny)
DONE_FG = "#999999"           # tytul wykonanego zadania (wyszarzony)
SEPARATOR_COLOR = "#1a1a1a"   # cienka linia oddzielajaca sidebar od reszty
DEFAULT_BORDER = "#cccccc"    # ramka zadania bez kategorii

PRIORYTETOWE_COLOR = "#D9534F"  # czerwony stonowany - dla "Priorytetowe" w sidebarze
                                 # i dla ramek zadan z priority=True (override koloru kategorii)
ON_COLOR_FG = "white"           # tekst na kolorowych pasach sidebara


# ============================================================
# CZCIONKI - rodzina + rozmiary bazowe (przed skalowaniem)
# ============================================================
FONT_FAMILY = "Arial"

SIZE_SIDEBAR       = 20  # naglowki i pozycje sidebara
SIZE_LZ_HEADER     = 28  # tytul widoku
SIZE_LZ_TOOLBAR    = 18  # "Sortuj", "Filtruj", "Widok"
SIZE_LZ_PLUS       = 26  # "+"
SIZE_TASK_TITLE    = 18  # tytul zadania w wierszu
SIZE_TASK_INFO     = 14  # "co pon  20:00 - 21:15"


# ============================================================
# SKALOWANIE - rozmiar = clamp(int(width * factor), lo, hi)
# (factor, (lo, hi)) per element
# ============================================================
SIDEBAR_SCALE       = (0.1,   (12, 36))
LZ_HEADER_SCALE     = (0.08,  (22, 48))
LZ_TOOLBAR_SCALE    = (0.045, (16, 30))
LZ_PLUS_SCALE       = (0.065, (22, 42))
TASK_TITLE_SCALE    = (0.05,  (16, 30))
TASK_INFO_SCALE     = (0.038, (14, 24))
TASK_CHECKBOX_SCALE = (0.08,  (34, 54))

# Mnozniki paddingow sidebara
SIDEBAR_TOP_PAD_FACTOR = 0.05
SIDEBAR_BOT_PAD_FACTOR = 0.02
SIDEBAR_HEADER_GAP_MULTIPLIER = 1.5     # naglowki sekcji maja x1.5 wiekszy gorny gap
SIDEBAR_HEADER_HEIGHT_MULTIPLIER = 1.3  # ...i wiekszy minsize wiersza


# ============================================================
# LAYOUT
# ============================================================
LEFT_RELWIDTH = 0.3      # szerokosc sidebara (% szerokosci body)
LIST_RELWIDTH = 0.5      # szerokosc widoku (50%, 20% to celowy margines z prawej)


def scaled(width, scale):
    """Liczenie rozmiaru czcionki ze skalowaniem.
    scale: tuple (factor, (lo, hi)) - np. theme.SIDEBAR_SCALE."""
    factor, (lo, hi) = scale
    return max(lo, min(hi, int(width * factor)))
