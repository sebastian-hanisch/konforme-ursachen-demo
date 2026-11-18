"""Kennzahlen und Verdikte (reine Funktionen: Art, Text), dazu der Beispielpatient. Jede Zahl im Text kommt aus der Messung."""

import numpy as np

import kfu_conformal as K
import kfu_constants as C
from kfu_live import Measurement, Settings, below_target, n_effective, summarize  # noqa: F401  (Settings für die App)


def pct(x: float) -> str:
    return f"{x:.1f}".replace(".", ",")


def spct(x: float) -> str:
    """Mit Vorzeichen (für Deltas: Streamlit färbt nach dem ersten Zeichen)."""
    return f"{x:+.1f}".replace(".", ",")


def dec(x: float, nd: int = 3) -> str:
    """Zahl mit Dezimalkomma; nur die Zahl wird umformatiert, nie ein ganzer Satz."""
    return f"{x:.{nd}f}".replace(".", ",")


def cell_label(s) -> str:
    """Lesbare Beschreibung einer Einstellung (Zelle der Messreihe) für Tabellen: Ziel, Wissensbasis, Verschiebung, Kalibriermenge."""
    kb = "Wissensbasis bekannt" if s.kb == 0 else f"Wissensbasis aus {s.kb} Fällen"
    shift = {0: "keine Verschiebung", 1: "Vorab verschoben", 2: "Dokumentation verschoben"}[s.shift]
    return f"Ziel {s.target} %, {kb}, {shift}, {s.ncal} Kalibrierpatienten"


def holds(gap: float, se: float) -> bool:
    """Abdeckung minus Ziel (Punkte) gilt als „hält“, wenn sie nicht mehr als PARTIAL_TOL Punkte unter dem Ziel liegt oder der Abstand unter zwei Standardfehlern bleibt."""
    return gap >= -C.PARTIAL_TOL or gap > -C.SD_FACTOR * se


def verdict_abdeckung(method: str, target: int, cov: float, gap: float, se: float, shift: int):
    """Verdikt zur Gesamtabdeckung (alle gerankten Patienten, gepaart über die Welten): hält das Versprechen im Mittel?"""
    name = C.METHOD_SHORT[method]
    kern = f"{name}: Abdeckung {pct(cov)} % bei Ziel {target} % (Unterschied {spct(gap)} Punkte, Standardfehler {pct(se)})."
    if holds(gap, se):
        extra = " Die Verschiebung im Test hat hier keinen Unterschied hervorgebracht, der über der Toleranz oder über zwei Standardfehlern liegt." if shift else ""
        return "success", f"Das Versprechen hält im Mittel über alle Patienten dieser Messung. {kern}{extra}"
    grund = {1: " Im Test gilt ein anderes Vorab als in der Kalibrierung; in der Messreihe ist daraus im Mittel kein Abdeckungsverlust entstanden.", 2: " Im Test fehlen mehr Merkmale in der Akte als in der Kalibrierung."}.get(shift, "")
    return "warning", f"Das Versprechen hält hier nicht. {kern}{grund}"


def verdict_klasse(method: str, cls: int, target: int, cov_c: float, gap_c: float, se_c: float, size_c: float, size_all: float, share_c: float):
    """Verdikt zur Abdeckung in einer Merkmalsklasse: das Versprechen gilt im Mittel über alle Patienten, nicht je Klasse."""
    name = C.METHOD_SHORT[method]
    klasse = C.BIN_NAMES[cls]
    kern = (f"{name}, {klasse} ({pct(share_c)} % der Patienten): Abdeckung {pct(cov_c)} % bei Ziel {target} % (Unterschied {spct(gap_c)} Punkte, Standardfehler {pct(se_c)}), "
            f"Menge im Mittel {pct(size_c)} Krankheiten gegen {pct(size_all)} über alle Patienten.")
    if holds(gap_c, se_c):
        return "success", f"In dieser Klasse hält das Versprechen. {kern}"
    return "warning", f"In dieser Klasse liegt die Abdeckung unter dem Ziel, obwohl das Versprechen im Mittel über alle Patienten gelten kann. {kern}"


def kennzahlen(m: Measurement, method: str, cls: int) -> dict:
    """Alle Kennzahlen der Hauptansicht aus einer Messung für ein Verfahren und eine Klasse (cls 0 bis 2)."""
    s = summarize(m)
    target = m.settings.target
    return {"summary": s, "method": method, "cls": cls, "target": target, "gap_all": below_target(m, method, "all", target),
            "gap_cls": below_target(m, method, cls, target)}


def verdicts(m: Measurement, k: dict):
    s = k["summary"][k["method"]]
    cov, size = s["cov"][0], s["size"][0]
    cls = k["cls"]
    v1 = verdict_abdeckung(k["method"], k["target"], cov, k["gap_all"][0], k["gap_all"][1], m.settings.shift)
    v2 = verdict_klasse(k["method"], cls, k["target"], s["cov_b"][cls][0], k["gap_cls"][0], k["gap_cls"][1], s["size_b"][cls][0], size, s["share_b"][cls][0])
    return v1, v2


def example_indices(m: Measurement, focus: int) -> list:
    """Positionen der Beispielpatienten (aus Welt 0) der Klasse `focus` (0 alle, 1 bis 3 die Klassen), höchstens N_EXAMPLE_SHOWN."""
    ex = m.runs[0].example
    b = K.bin_of(ex["kobs"])
    idx = np.arange(len(ex["d"])) if focus == 0 else np.flatnonzero(b == focus - 1)
    return [int(i) for i in idx[: C.N_EXAMPLE_SHOWN]]


def example_view(m: Measurement, positions: list, idx: int, top: int = 8) -> dict:
    """Beispielpatient Nummer idx (0-basiert in `positions`): wahre Krankheit, Zahl dokumentierter Merkmale, die obersten `top` Krankheiten nach Posterior,
    Rang der wahren Krankheit und je Verfahren Mengengröße und Treffer."""
    ex = m.runs[0].example
    idx = int(min(max(idx, 0), len(positions) - 1))
    i = positions[idx]
    p = ex["p"][i]
    true = int(ex["d"][i])
    order = np.argsort(-p, kind="stable")[:top]
    out = {"true": true, "kobs": int(ex["kobs"][i]), "top_ids": [int(j) for j in order], "top_p": [float(p[j]) for j in order],
           "p_true": float(p[true]), "rank_true": int(1 + (p > p[true]).sum()), "methods": {}}
    for meth in C.METHODS:
        row = ex["sets"][meth][i]
        out["methods"][meth] = {"size": int(row.sum()), "hit": bool(row[true]), "member": [bool(row[j]) for j in order]}
    return out


# --- Kernfragen aus der vorgerechneten Messreihe (Zahlen aus data/kfu_results.json, nie von Hand) -------------------------------------------------

def kernfrage_halt(c: dict):
    """Kernfrage 1: hält das Versprechen im Mittel, und je Klasse? Standardzelle, Mittel der beiden Mengen (zehn Welten)."""
    import kfu_results as RES
    t = c["settings"]["target"]
    cov, c0, c2 = RES.pooled(c, "LAC", "cov"), RES.pooled(c, "LAC", "cov_b", 0), RES.pooled(c, "LAC", "cov_b", 2)
    text = (f"LAC deckt im Mittel {pct(cov)} % der Patienten ab (Ziel {t} %, zehn Welten): das Versprechen gilt über alle Patienten. Je Klasse gilt es nicht: bei 1–2 dokumentierten Merkmalen "
            f"sind es {pct(c0)} %, bei 5 und mehr {pct(c2)} %.")
    return ("warning" if c0 < t - C.PARTIAL_TOL else "info"), text


def kernfrage_bruch(c0: dict, c1: dict, c2: dict, c_thin: dict):
    """Kernfrage 2: wann bricht das Versprechen? Keine Verschiebung, Vorab, Dokumentation und dünne Wissensbasis (LAC, zehn Welten)."""
    import kfu_results as RES
    t = c0["settings"]["target"]
    v0, v1, v2, vt = (RES.pooled(c, "LAC", "cov") for c in (c0, c1, c2, c_thin))
    s0, st_ = RES.pooled(c0, "LAC", "size"), RES.pooled(c_thin, "LAC", "size")
    text = (f"Mit verschobener Dokumentation im Test sinkt die Abdeckung von LAC auf {pct(v2)} % (Ziel {t} %, ohne Verschiebung {pct(v0)} %); mit verschobenem Vorab liegt sie bei {pct(v1)} %. "
            f"Mit einer aus 3 Fällen je Krankheit geschätzten Wissensbasis hält sie ({pct(vt)} %), die mittlere Menge wächst aber von {pct(s0)} auf {pct(st_)} Krankheiten.")
    return ("warning" if v2 < t - C.PARTIAL_TOL else "info"), text


def kernfrage_preis(cells: dict, c_base: dict):
    """Kernfrage 3: was kostet das Versprechen? Mittlere Menge je Ziel und Vergleich mit der festen Top-5-Liste; Preis von Mondrian bei wenigen Merkmalen."""
    import kfu_results as RES
    sizes = {t: RES.pooled(c, "LAC", "size") for t, c in cells.items()}
    top5 = (RES.fixed(c_base, "A", "top5")[0] + RES.fixed(c_base, "B", "top5")[0]) / 2.0
    m0, l0 = RES.pooled(c_base, "MONDRIAN", "size_b", 0), RES.pooled(c_base, "LAC", "size_b", 0)
    teile = " / ".join(f"{pct(sizes[t])}" for t in sorted(sizes))
    ziele = " / ".join(str(t) for t in sorted(sizes))
    text = (f"Die mittlere Menge von LAC ist bei Ziel {ziele} % im Mittel {teile} Krankheiten groß; eine feste Liste der fünf wahrscheinlichsten Krankheiten deckt dagegen {pct(top5)} % ab. "
            f"Mondrian gleicht die Abdeckung je Klasse an und braucht dafür bei 1–2 Merkmalen im Mittel {pct(m0)} statt {pct(l0)} Krankheiten.")
    return "info", text


def kernfrage_streuung(rows: list):
    """Kernfrage 4: Streuung der Abdeckung einer einzelnen Kalibrierung gegen die Kalibriermenge (Ziel 90 Prozent), Simulation gegen Beta-Verteilung."""
    sel = {r["n_cal"]: r for r in rows if r["target"] == 90}
    a, b, c = sel[100], sel[500], sel[2000]
    text = (f"Die Abdeckung einer einzelnen Kalibrierung streut bei 100 Kalibrierpatienten mit {pct(100 * a['sd'])} Prozentpunkten, bei 500 mit {pct(100 * b['sd'])} und bei 2000 mit {pct(100 * c['sd'])}; "
            f"die Beta-Verteilung gibt {pct(100 * a['beta_sd'])}, {pct(100 * b['beta_sd'])} und {pct(100 * c['beta_sd'])} (je 1000 Kalibrierungen aus einem Vorrat). "
            f"Bei 100 Kalibrierpatienten lag der kleinste Wert bei {pct(100 * a['min'])} %.")
    return "info", text
