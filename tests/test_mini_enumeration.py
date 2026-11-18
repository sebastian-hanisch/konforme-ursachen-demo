"""Mini-Instanz-Test: 3 Krankheiten, 3 Merkmale, 8 Muster. Aufgezählt werden ALLE Kalibriermengen der Größe 3 (24 Zellen aus Krankheit und Muster, 24³ = 13 824 geordnete
Tripel mit ihrer exakten Wahrscheinlichkeit) und alle Testpatienten; die exakte Abdeckung wird gegen die Formel „⌈(n + 1) · Ziel⌉-te Ordnungsstatistik“ und gegen einen unabhängigen
Rechenweg (Schleifen, Einfügesortierung, Ganzzahlrechnung) geprüft.

Die Ergebnisse haben Gleichstände (dieselbe Zelle kann mehrfach gezogen werden): dann gilt nur die untere Schranke ⌈(n + 1) · Ziel⌉ / (n + 1), nicht die obere."""

import itertools
import math

import numpy as np
import pytest

import kfu_conformal as K
from conftest import mini_gemeinsam, mini_muster, mini_posterior

N = 3
JOINT = mini_gemeinsam()
X = mini_muster()
P8 = mini_posterior(X)
KOBS8 = X.sum(axis=1).astype(int)
CELLS = [(d, i) for d in range(3) for i in range(8)]
PROB = np.array([JOINT[d, i] for d, i in CELLS])


def _einfuegesortierung(werte):
    out = []
    for w in werte:
        pos = 0
        while pos < len(out) and out[pos] <= w:
            pos += 1
        out.insert(pos, w)
    return out


def _orakel_schwelle(werte, ziel):
    """Unabhängiger Rechenweg: ⌈(n + 1) · Ziel / 100⌉ per Ganzzahlrechnung, k-tes Element der eingefügt sortierten Liste, sonst unendlich."""
    n = len(werte)
    k = -(-((n + 1) * ziel) // 100)
    s = _einfuegesortierung(werte)
    return math.inf if (k > n or n == 0) else s[k - 1]


def _orakel_ergebnisse(methode, cal):
    """Ergebnis der wahren Krankheit je Kalibrierpatient, Zelle für Zelle ohne die Module der Demo."""
    out = []
    for d, i in cal:
        p = list(P8[i])
        if methode == "LAC":
            out.append(1.0 - p[d])
        else:                                         # APS: Masse der strikt höher gereihten Krankheiten (Gleichstand nach Index)
            order = sorted(range(3), key=lambda j: (-p[j], j))
            out.append(sum(p[j] for j in order[: order.index(d)]))
    return out


def _exakt(methode, ziel):
    """Exakte Abdeckung, Abdeckung je Klasse (0: höchstens 2 Merkmale, 1: genau 3) und ob Schwelle und Menge mit dem Orakel übereinstimmen."""
    cover = 0.0
    cover_cls = np.zeros(2)
    cells_cls = np.array([[JOINT[:, i].sum() for i in range(8) if (KOBS8[i] <= 2) == (c == 0)] for c in range(2)], dtype=object)
    weight_cls = np.array([sum(c) for c in cells_cls], dtype=float)
    stimmt = True
    for tripel in itertools.product(range(len(CELLS)), repeat=N):
        pr = float(np.prod(PROB[list(tripel)]))
        cal = [CELLS[t] for t in tripel]
        idx = [i for _, i in cal]
        truth = np.array([d for d, _ in cal])
        th = K.calibrate(methode, P8[idx], truth, KOBS8[idx], ziel)
        sets = K.predict_sets(methode, P8, th, KOBS8)
        if methode == "MONDRIAN":
            sc = _orakel_ergebnisse("LAC", cal)
            klassen = [0 if KOBS8[i] <= 2 else 1 for i in idx]
            orakel = [_orakel_schwelle([s for s, c in zip(sc, klassen) if c == k], ziel) for k in range(3)]
            stimmt &= all(a == b or (math.isinf(a) and math.isinf(b)) or math.isclose(a, b) for a, b in zip(th, orakel))
        else:
            orakel = _orakel_schwelle(_orakel_ergebnisse(methode, cal), ziel)
            stimmt &= (math.isinf(orakel) and math.isinf(th)) or math.isclose(th, orakel)
        for i in range(8):
            c_i = 0 if KOBS8[i] <= 2 else 1
            for d in range(3):
                if sets[i, d]:
                    cover += pr * JOINT[d, i]
                    cover_cls[c_i] += pr * JOINT[d, i]
    return cover, cover_cls / weight_cls, stimmt


@pytest.fixture(scope="module")
def exakt():
    return {(m, t): _exakt(m, t) for m in ("LAC", "APS", "MONDRIAN") for t in (50, 75, 90)}


def test_wahrscheinlichkeiten_summieren_zu_eins():
    assert PROB.sum() == pytest.approx(1.0) and P8.sum(axis=1) == pytest.approx(np.ones(8))


@pytest.mark.parametrize("methode", ["LAC", "APS", "MONDRIAN"])
@pytest.mark.parametrize("ziel", [50, 75, 90])
def test_schwelle_stimmt_mit_dem_unabhaengigen_rechenweg_ueberein(exakt, methode, ziel):
    assert exakt[(methode, ziel)][2]


@pytest.mark.parametrize("methode", ["LAC", "APS"])
@pytest.mark.parametrize("ziel", [50, 75, 90])
def test_exakte_abdeckung_ist_mindestens_die_formel(exakt, methode, ziel):
    k = -(-((N + 1) * ziel) // 100)
    untere = 1.0 if k > N else k / (N + 1)         # Rang über n: Schwelle unendlich, Abdeckung 1
    cover = exakt[(methode, ziel)][0]
    assert cover >= untere - 1e-12
    assert cover >= ziel / 100 - 1e-12              # das Versprechen selbst


def test_obere_schranke_braucht_stetige_ergebnisse(exakt):
    # Dokumentiert die Voraussetzung der oberen Grenze 1 − α + 1/(n + 1) = 0,75 bei Ziel 50: APS hat viele Ergebnisse gleich 0 (Gleichstände), seine Abdeckung liegt bei 0,808 darüber
    assert exakt[("APS", 50)][0] > 0.5 + 1 / (N + 1) + 0.05
    assert exakt[("LAC", 50)][0] <= 0.5 + 1 / (N + 1)        # LAC hat hier weniger Gleichstände und bleibt unter der Grenze


@pytest.mark.parametrize("ziel", [50, 75, 90])
def test_mondrian_je_klasse_mindestens_das_ziel(exakt, ziel):
    """Je Klasse gilt die Garantie bedingt auf die Zahl der Kalibrierpatienten dieser Klasse, also auch im Mittel darüber."""
    _, je_klasse, _ = exakt[("MONDRIAN", ziel)]
    assert (je_klasse >= ziel / 100 - 1e-12).all()


def test_lac_verfehlt_in_mindestens_einer_klasse_das_ziel_mondrian_nicht(exakt):
    """Zweig-Test: an dieser Mini-Instanz ist die Abdeckung von LAC nicht in jeder Klasse mindestens das Ziel."""
    assert any((exakt[("LAC", t)][1] < t / 100 - 1e-9).any() for t in (50, 75))
    assert all((exakt[("MONDRIAN", t)][1] >= t / 100 - 1e-12).all() for t in (50, 75, 90))
