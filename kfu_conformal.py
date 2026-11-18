"""Konforme Ursachenmenge: Schwelle, drei Verfahren (LAC, APS, Mondrian-LAC), Mengen, Abdeckung und Größe.

Jede Einheit ist eine Funktion mit ausdrücklichen Eingaben, ohne Zustand und ohne Zufall. Eingabe ist immer der Posterior P (Zeilen = Patienten, Spalten = Krankheiten,
Zeilen summieren zu 1) mit der wahren Krankheit `truth` und der Zahl dokumentierter Merkmale `kobs` je Patient. Das Abdeckungsversprechen gilt im Mittel über Patienten
unter Austauschbarkeit von Kalibrier- und Testpatienten (README „Modell“); es gilt nicht je Patient und nicht je Klasse."""

import math

import numpy as np

import kfu_constants as C
import kfu_metrics as M


def threshold(scores, target: int) -> float:
    """Schwelle q̂ = das ⌈(n + 1) · Ziel⌉-te kleinste Ergebnis der Kalibrierpatienten (Ziel in ganzen Prozent, exakte Ganzzahlrechnung).

    Gibt es weniger Kalibrierpatienten, als der Rang verlangt (⌈(n + 1) · Ziel⌉ > n), ist die Schwelle unendlich: die Menge enthält dann alle Krankheiten."""
    s = np.sort(np.asarray(scores, dtype=float))
    n = len(s)
    k = ((n + 1) * target + 99) // 100
    if n == 0 or k > n:
        return math.inf
    return float(s[max(k, 1) - 1])


def bin_of(kobs) -> np.ndarray:
    """Klasse 0, 1, 2 nach der Zahl dokumentierter Merkmale (1–2, 3–4, 5 und mehr)."""
    k = np.asarray(kobs)
    return np.where(k <= C.BINS_NOBS[0][1], 0, np.where(k <= C.BINS_NOBS[1][1], 1, 2))


def lac_scores_all(P: np.ndarray) -> np.ndarray:
    """LAC-Ergebnis jeder Krankheit je Patient: 1 − Posterior (klein = plausibel)."""
    return 1.0 - P


def aps_scores_all(P: np.ndarray) -> np.ndarray:
    """APS-Ergebnis (nicht randomisiert): Masse der strikt höher gereihten Krankheiten (Rangfolge nach Posterior, bei Gleichstand nach Index)."""
    order = np.argsort(-P, axis=1, kind="stable")
    sorted_p = np.take_along_axis(P, order, axis=1)
    above = np.cumsum(sorted_p, axis=1) - sorted_p
    out = np.empty_like(above)
    np.put_along_axis(out, order, above, axis=1)
    return out


def true_scores(all_scores: np.ndarray, truth: np.ndarray) -> np.ndarray:
    return all_scores[np.arange(len(truth)), truth]


def calibrate(method: str, P: np.ndarray, truth: np.ndarray, kobs: np.ndarray, target: int):
    """Schwelle(n) aus der Kalibriermenge: eine Zahl (LAC, APS) oder drei Zahlen, eine je Merkmalsklasse (Mondrian-LAC)."""
    if method == "LAC":
        return threshold(true_scores(lac_scores_all(P), truth), target)
    if method == "APS":
        return threshold(true_scores(aps_scores_all(P), truth), target)
    if method == "MONDRIAN":
        s = true_scores(lac_scores_all(P), truth)
        b = bin_of(kobs)
        return np.array([threshold(s[b == c], target) for c in range(3)])
    raise ValueError(method)


def predict_sets(method: str, P: np.ndarray, thresholds, kobs: np.ndarray) -> np.ndarray:
    """Mengen als Wahrheitsmatrix (Patienten × Krankheiten): Krankheiten, deren Ergebnis höchstens die Schwelle ist."""
    if method == "LAC":
        return lac_scores_all(P) <= thresholds
    if method == "APS":
        return aps_scores_all(P) <= thresholds
    if method == "MONDRIAN":
        q = np.asarray(thresholds)[bin_of(kobs)]
        return lac_scores_all(P) <= q[:, None]
    raise ValueError(method)


def evaluate(sets: np.ndarray, truth: np.ndarray, kobs: np.ndarray) -> dict:
    """Abdeckung (Anteil der Patienten, deren wahre Krankheit in der Menge liegt) und mittlere Mengengröße, gesamt und je Merkmalsklasse (Prozent beziehungsweise Zahl Krankheiten)."""
    cover = sets[np.arange(len(truth)), truth].astype(float)
    size = sets.sum(axis=1).astype(float)
    b = bin_of(kobs)
    out = {"cov": 100.0 * cover.mean(), "size": float(size.mean()), "cov_b": [], "size_b": [], "share_b": []}
    for c in range(3):
        sel = b == c
        out["cov_b"].append(100.0 * float(cover[sel].mean()) if sel.any() else float("nan"))
        out["size_b"].append(float(size[sel].mean()) if sel.any() else float("nan"))
        out["share_b"].append(100.0 * float(sel.mean()))
    return out


def fixed_top(P: np.ndarray, truth: np.ndarray, k: int) -> float:
    """Anteil der Patienten (in Prozent), bei denen die wahre Krankheit unter den ersten k der Rangliste steht (Gleichstände zufällig aufgelöst): die feste Top-k-Liste als Vergleich."""
    return 100.0 * float(M.recall_at_k(P, truth, k).mean())
