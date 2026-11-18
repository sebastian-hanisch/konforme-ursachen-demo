"""Konstanten: feste Annahmen der Welt, Regler-Stufen, Messung, Farben und Presets (Konforme Ursachenmenge, Lehrmodell mit erfundenen Daten)."""

# --- Welt (Annahmen des Erzeugers; dieselbe Welt wie die Rangliste aus Merkmalen) ----------------------------------------------------------------
NS = 100                      # Zahl der Merkmale (Symptome)
POP_EXP = 0.8                 # Zipf-Exponent der Beliebtheit der Merkmale: beliebte Merkmale kommen in vielen Profilen und im Hintergrund vor
FREQ = (0.95, 0.6, 0.3, 0.1)  # Häufigkeit eines Profilmerkmals bei einer Person mit der Krankheit
FREQ_P = (0.15, 0.25, 0.35, 0.25)  # Anteile dieser Häufigkeiten an den Profilmerkmalen
K_MIN_FEAT, K_MAX_FEAT = 4, 12     # Zahl der Profilmerkmale je Krankheit (gleichverteilt, beide Grenzen inklusive)
BG_BASE, BG_SLOPE, BG_POWER = 0.01, 0.2, 2   # Hintergrundrate eines Merkmals = 0,01 + 0,2 * (Beliebtheit / größte Beliebtheit)^2
PRIOR_ZIPF_EXP = 1.0          # Vorab "nach Häufigkeit": Zipf-Exponent 1 (nur für die Verschiebung des Vorab)
LAPLACE_A = 0.5               # Add-½-Glättung (je Seite 0,5) bei geschätzter Wissensbasis
PROB_FLOOR = 1e-6             # Untergrenze der Häufigkeiten im Logarithmus
SIMPLE_THRESHOLD = 0.05       # (von den kopierten Rankern gebraucht) Schwelle der Regel „Zahl Übereinstimmungen“
SHRINK_A = (3, 10)            # (von der kopierten Welt gebraucht) Pseudozählungen der Schrumpfung; diese Demo nutzt nur die Add-½-Glättung
CALIB_EDGES = (0.0, 0.5, 0.9, 0.99, 1.0000001)   # (von den kopierten Kennzahlen gebraucht) Fächer des Zuverlässigkeitsdiagramms

ND = 200                      # Zahl der Krankheiten (fest)
Q_BASE, Q_SHIFT = 0.3, 0.6    # Dokumentationsverlust in der Kalibrierung und, bei verschobener Dokumentation, im Test

# --- Konforme Mengen ----------------------------------------------------------------------------------------------------------------------
METHODS = ("LAC", "APS", "MONDRIAN")
METHOD_NAMES = {"LAC": "LAC (1 − Posterior der wahren Krankheit)", "APS": "APS (Masse der höher gereihten Krankheiten)", "MONDRIAN": "Mondrian-LAC (eine Schwelle je Merkmalsklasse)"}
METHOD_SHORT = {"LAC": "LAC", "APS": "APS", "MONDRIAN": "Mondrian"}
BINS_NOBS = ((1, 2), (3, 4), (5, 10_000))      # Klassen nach der Zahl dokumentierter Merkmale
BIN_NAMES = ("1–2 Merkmale", "3–4 Merkmale", "5 und mehr Merkmale")
BIN_DAT = ("1–2 Merkmalen", "3–4 Merkmalen", "5 und mehr Merkmalen")   # nach „bei“
N_TEST = 3000                 # Testpatienten je Welt (vor dem Entfernen von Patienten ohne dokumentiertes Merkmal)
N_EXAMPLE = 300               # gespeicherte Beispielpatienten (erste Patienten der Testmenge der ersten Welt; gezeigt werden höchstens N_EXAMPLE_SHOWN je Klasse)
N_EXAMPLE_SHOWN = 30
PARTIAL_TOL = 2.0             # Punkte: Abdeckung bis hierhin unter dem Ziel gilt als „hält“

# --- Messung ------------------------------------------------------------------------------------------------------------------------------
N_WORLDS = 5                  # Welten je Messung
SWEEP_SEEDS = {"A": 1000, "B": 2000}   # zwei Mengen von je N_WORLDS Welten; nie ein einzelner Zufalls-Seed als Befund
SPREAD_REPS = 1000            # Wiederholungen der Kalibrierung für die Streuung der Abdeckung
SPREAD_POOL = 20000           # Patienten je Hälfte (Kalibrier-Vorrat und Testhälfte) für die Streuung der Abdeckung
SD_FACTOR = 2.0               # Unterschiede unter dieser Zahl von Standardfehlern werden nicht gedeutet

# --- Regler (Stufen = gemessene Zellen) ---------------------------------------------------------------------------------------------------
TARGET_OPTIONS = (80, 90, 95)        # Ziel-Abdeckung in Prozent (α = 1 − Ziel)
KB_OPTIONS = (0, 30, 3)              # 0 = Wissensbasis bekannt, sonst Fälle je Krankheit
SHIFT_OPTIONS = (0, 1, 2)            # 0 keine, 1 Vorab (Zipf statt gleich), 2 Dokumentation (q 0,6 statt 0,3); wirkt nur im Test
NCAL_OPTIONS = (100, 500, 2000)      # Kalibrierpatienten (vor dem Entfernen von Patienten ohne dokumentiertes Merkmal)
METHOD_OPTIONS = (0, 1, 2)           # Anzeige: 0 LAC, 1 APS, 2 Mondrian; es werden immer alle drei gerechnet
FOCUS_OPTIONS = (0, 1, 2, 3)         # Anzeige: 0 alle Patienten, 1 bis 3 die Klassen 1–2, 3–4, 5+ Merkmale
SEED_MAX, DEFAULT_SEED = 999999, 35
DEFAULT = {"target": 90, "kb": 0, "shift": 0, "ncal": 500, "method": 0, "focus": 0, "seed": DEFAULT_SEED}
METHOD_OF_OPTION = {0: "LAC", 1: "APS", 2: "MONDRIAN"}

COLOR_LAC = "#2a7de1"
COLOR_APS = "#c77700"
COLOR_MONDRIAN = "#34a89c"
COLOR_FIXED = "#8a96a8"
COLOR_TRUE = "#1f2733"
METHOD_COLORS = {"LAC": COLOR_LAC, "APS": COLOR_APS, "MONDRIAN": COLOR_MONDRIAN}

# --- Presets (je eine Änderung gegenüber der Voreinstellung; die Zellen stehen in data/kfu_results.json) -------------------------------------
PRESETS = {
    "Standard": {**DEFAULT},
    "Dünne Wissensbasis": {**DEFAULT, "kb": 3},
    "Schwierige Fälle": {**DEFAULT, "focus": 1},
    "Verschobene Dokumentation": {**DEFAULT, "shift": 2},
    "Mondrian": {**DEFAULT, "method": 2},
    "Kleine Kalibriermenge": {**DEFAULT, "ncal": 100},
}
PRESET_HELP = {
    "Standard": "Die wahren Häufigkeiten sind bekannt, Ziel 90 Prozent, Kalibriermenge 500 Patienten, keine Verschiebung. Das Versprechen hält im Mittel; schwierige Fälle liegen darunter.",
    "Dünne Wissensbasis": "Die Häufigkeiten sind aus nur 3 Fällen je Krankheit geschätzt: die Abdeckung hält weiter, die Menge wird groß.",
    "Schwierige Fälle": "Zeigt die Patienten mit höchstens zwei dokumentierten Merkmalen: Bei LAC und APS bekommt, wer wenig Merkmale hat, weniger Abdeckung, als versprochen ist.",
    "Verschobene Dokumentation": "Im Test wird mehr Merkmalsverlust unterstellt (0,6 statt 0,3) als bei der Kalibrierung: das Versprechen bricht.",
    "Mondrian": "Je Merkmalsklasse eine eigene Schwelle: die Abdeckung stimmt je Klasse, dafür werden die Mengen bei wenigen Merkmalen größer.",
    "Kleine Kalibriermenge": "Nur 100 Kalibrierpatienten: die Abdeckung hält im Mittel, streut aber von Kalibrierung zu Kalibrierung stärker.",
}
