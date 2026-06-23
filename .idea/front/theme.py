"""
Stale wizualne - nowoczesna paleta (Notion-style), białe karty na szarym tle.
"""
import platform

# Paleta
BG = "#F8F9FA"                  # Tło aplikacji
CARD_BG = "#FFFFFF"             # Tło kart zadań
FG = "#202124"                  # Główny tekst
INFO_FG = "#70757A"             # Tekst drugoplanowy
DONE_FG = "#BDC1C6"             # Wyszarzony tekst
DEFAULT_BORDER = "#DADCE0"      # Ramka kart
SEPARATOR_COLOR = "#DADCE0"     # <--- DODANO: brakujący kolor linii
PRIORYTETOWE_COLOR = "#D93025"  # Czerwony
ON_COLOR_FG = "#FFFFFF"         # Tekst na kolorowych elementach

# Czcionki
FONT_FAMILY = "Segoe UI" if platform.system() == "Windows" else "Helvetica Neue"

SIZE_SIDEBAR       = 20
SIZE_LZ_HEADER     = 28
SIZE_LZ_TOOLBAR    = 18
SIZE_LZ_PLUS       = 26
SIZE_TASK_TITLE    = 18
SIZE_TASK_INFO     = 14

# Skalowanie
SIDEBAR_SCALE       = (0.1,   (12, 36))
LZ_HEADER_SCALE     = (0.08,  (22, 48))
LZ_TOOLBAR_SCALE    = (0.045, (16, 30))
LZ_PLUS_SCALE       = (0.065, (22, 42))
TASK_TITLE_SCALE    = (0.05,  (16, 30))
TASK_INFO_SCALE     = (0.038, (14, 24))
TASK_CHECKBOX_SCALE = (0.08,  (34, 54))

SIDEBAR_TOP_PAD_FACTOR = 0.05
SIDEBAR_BOT_PAD_FACTOR = 0.02
SIDEBAR_HEADER_GAP_MULTIPLIER = 1.5
SIDEBAR_HEADER_HEIGHT_MULTIPLIER = 1.3

LEFT_RELWIDTH = 0.3
LIST_RELWIDTH = 0.5

def scaled(width, scale):
    factor, (lo, hi) = scale
    return max(lo, min(hi, int(width * factor)))