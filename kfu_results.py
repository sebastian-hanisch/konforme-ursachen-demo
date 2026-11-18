"""Vorgerechnete Messreihe (data/kfu_results.json, erzeugt von tools/sweep.py): Zellen, Zugriff, gepoolte Kennzahlen.

Eine Zelle = eine Einstellung (ohne Zufalls-Seed); je Zelle zwei Mengen von je fünf Welten (A: Zufalls-Seed 1000, B: 2000). Kennzahlen sind Mittel ± Streuung über die
fünf Welten: Abdeckung in Prozent der Patienten, Menge in Zahl Krankheiten; die Streuung ist die Standardabweichung der Mittel der Welten (n − 1)."""

import json
from functools import lru_cache
from pathlib import Path

from kfu_live import Settings

DATA = Path(__file__).resolve().parent / "data" / "kfu_results.json"
BASE = Settings()


def sweep_settings() -> list:
    """Alle gemessenen Zellen: Voreinstellung und je eine Änderung (einfaktorielle Abweichungen) sowie die dünne Wissensbasis mit verschobener Dokumentation."""
    cells = [BASE]
    cells += [Settings(kb=kb) for kb in (30, 3)]
    cells += [Settings(shift=sh) for sh in (1, 2)]
    cells += [Settings(kb=3, shift=2)]
    cells += [Settings(target=t) for t in (80, 95)]
    cells += [Settings(ncal=n) for n in (100, 2000)]
    seen, out = set(), []
    for s in cells:
        if s.key() not in seen:
            seen.add(s.key())
            out.append(s)
    return out


@lru_cache(maxsize=1)
def load() -> dict:
    return json.loads(DATA.read_text(encoding="utf-8"))


def cell(settings: Settings) -> dict | None:
    """Die gemessene Zelle zur Einstellung oder None, wenn sie nicht gemessen ist."""
    return load()["cells"].get(settings.key())


def nearest_cell(settings: Settings) -> tuple:
    """(Zelle, ist_gleich): die gemessene Zelle zur Einstellung, sonst die nächstliegende (gleiche Ziel-Abdeckung bevorzugt) mit dem Hinweis, dass sie abweicht."""
    c = cell(settings)
    if c is not None:
        return c, True
    cells = load()["cells"]
    best = min(cells.values(), key=lambda row: (row["settings"]["target"] != settings.target, row["settings"]["kb"] != settings.kb,
                                                row["settings"]["shift"] != settings.shift, row["settings"]["ncal"] != settings.ncal))
    return best, False


def stat(c: dict, which: str, method: str, key: str, index: int | None = None) -> tuple:
    """(Mittel, Streuung) einer Kennzahl aus Menge `which` ("A" oder "B"); key: cov, size, cov_b, size_b, share_b (mit index 0 bis 2)."""
    v = c[which]["summary"][method][key]
    m, sd = v if index is None else v[index]
    return m, sd


def pooled(c: dict, method: str, key: str, index: int | None = None) -> float:
    """Mittel der beiden Mengen (je fünf Welten): zehn Welten insgesamt."""
    return (stat(c, "A", method, key, index)[0] + stat(c, "B", method, key, index)[0]) / 2.0


def fixed(c: dict, which: str, key: str) -> tuple:
    """Feste Top-1- oder Top-5-Liste (key "top1" oder "top5"): (Mittel, Streuung) in Prozent der Patienten."""
    return tuple(c[which]["summary"]["fixed"][key])


def below_target(c: dict, which: str, method: str, index: int | str = "all") -> tuple:
    """Abdeckung minus Ziel in Prozentpunkten, Mittel über die Welten und Standardfehler (Streuung der Welten / Wurzel der Weltenzahl); index "all" oder Klasse 0 bis 2."""
    target = c["settings"]["target"]
    worlds = c[which]["worlds"]
    vals = [(w["methods"][method]["cov"] if index == "all" else w["methods"][method]["cov_b"][index]) - target for w in worlds]
    n = len(vals)
    mean = sum(vals) / n
    sd = (sum((v - mean) ** 2 for v in vals) / (n - 1)) ** 0.5
    return mean, sd / n ** 0.5


def sets_agree(c: dict, method: str, key: str = "cov", index: int | None = None) -> float:
    """Unterschied der beiden Mengen in Einheiten der Kennzahl (Betrag), ein Maß für die Stabilität der Zahl."""
    return abs(stat(c, "A", method, key, index)[0] - stat(c, "B", method, key, index)[0])


def meta() -> dict:
    return load()["meta"]


def world_values(c: dict, method: str, key: str, index: int | None = None) -> list:
    """Die Werte einer Kennzahl aller zehn Welten (Menge A, dann Menge B): key cov, size, cov_b, size_b oder share_b (mit index 0 bis 2)."""
    out = []
    for which in ("A", "B"):
        for w in c[which]["worlds"]:
            v = w["methods"][method][key]
            out.append(v if index is None else v[index])
    return out


def pooled_se(c: dict, method: str, key: str, index: int | None = None) -> float:
    """Standardfehler des Mittels über die zehn Welten (Streuung der Welten, n − 1, durch Wurzel aus zehn)."""
    vals = world_values(c, method, key, index)
    m = sum(vals) / len(vals)
    return (sum((v - m) ** 2 for v in vals) / (len(vals) - 1)) ** 0.5 / len(vals) ** 0.5


def pooled_all(c: dict, method: str, key: str, index: int | None = None) -> float:
    """Mittel über die zehn Welten (gleich dem Mittel der beiden Mengen, da jede fünf Welten hat)."""
    vals = world_values(c, method, key, index)
    return sum(vals) / len(vals)


def cell_settings(key: str) -> dict:
    """Einstellung einer Zelle (Ziel, Wissensbasis, Verschiebung, Kalibriermenge) aus ihrem Schlüssel."""
    return load()["cells"][key]["settings"]
