"""Einheiten der konformen Mengen, jede an einer kleinen Instanz von Hand gerechnet (DEMO-PLAYBOOK §1b)."""

import math

import numpy as np
import pytest

import kfu_conformal as K

P4 = np.array([[0.6, 0.3, 0.1], [0.5, 0.4, 0.1], [0.2, 0.7, 0.1], [0.1, 0.1, 0.8]])
TRUTH4 = np.array([0, 1, 1, 2])
KOBS4 = np.array([1, 2, 3, 6])


def test_schwelle_ist_die_ceil_n_plus_1_ziel_te_ordnungsstatistik():
    s = [0.5, 0.1, 0.3, 0.9, 0.7]                      # sortiert: 0,1  0,3  0,5  0,7  0,9
    assert K.threshold(s, 50) == 0.5                    # ⌈6 · 0,5⌉ = 3
    assert K.threshold(s, 80) == 0.9                    # ⌈6 · 0,8⌉ = ⌈4,8⌉ = 5
    assert K.threshold(s, 60) == 0.7                    # ⌈6 · 0,6⌉ = ⌈3,6⌉ = 4


def test_schwelle_unendlich_wenn_der_rang_groesser_als_n_ist():
    s = [0.5, 0.1, 0.3, 0.9, 0.7]
    assert K.threshold(s, 90) == math.inf              # ⌈6 · 0,9⌉ = 6 > 5: alle Krankheiten
    assert K.threshold(s, 100) == math.inf
    assert K.threshold([], 50) == math.inf


@pytest.mark.parametrize("n, target, rang", [(9, 90, 9), (19, 95, 19), (99, 80, 80), (499, 90, 450), (500, 90, 451), (2000, 95, 1901)])
def test_rang_ist_exakte_ganzzahlrechnung(n, target, rang):
    scores = np.arange(1, n + 1, dtype=float)           # i-tes kleinstes Ergebnis = i
    assert K.threshold(scores, target) == float(rang)   # Gleitkomma-ceil((n + 1) * 0.95) hätte bei n = 19 danebenliegen können


def test_klassen_der_merkmalszahl_an_den_grenzen():
    assert list(K.bin_of([1, 2, 3, 4, 5, 6, 40])) == [0, 0, 1, 1, 2, 2, 2]


def test_lac_ergebnis_von_hand():
    p = np.array([[0.7, 0.2, 0.1], [0.1, 0.1, 0.8]])
    assert K.lac_scores_all(p) == pytest.approx(np.array([[0.3, 0.8, 0.9], [0.9, 0.9, 0.2]]))


def test_aps_ergebnis_ist_die_masse_der_strikt_hoeher_gereihten_krankheiten():
    p = np.array([[0.7, 0.2, 0.1], [0.1, 0.1, 0.8]])
    # Zeile 1: Reihenfolge 0, 1, 2 → 0 | 0,7 | 0,9. Zeile 2: Reihenfolge 2, dann 0 und 1 (Gleichstand, nach Index) → Krankheit 2: 0 | 0: 0,8 | 1: 0,9
    assert K.aps_scores_all(p) == pytest.approx(np.array([[0.0, 0.7, 0.9], [0.8, 0.9, 0.0]]))


def test_aps_menge_ist_ein_anfangsstueck_der_rangliste():
    rng = np.random.default_rng(3)
    p = rng.dirichlet(np.ones(6), size=50)
    sets = K.predict_sets("APS", p, 0.55, np.ones(50))
    for row, prow in zip(sets, p):
        order = np.argsort(-prow, kind="stable")
        member = row[order]
        assert member[0]                                # die erste Krankheit hat Ergebnis 0 ≤ jede Schwelle
        assert (np.diff(member.astype(int)) <= 0).all()  # erst alle drin, dann alle draußen


def test_kalibrierung_lac_und_aps_von_hand():
    # wahre Ergebnisse LAC: 1 − P[i, truth[i]] = 0,4 0,6 0,3 0,2; Ziel 50, n = 4: ⌈5 · 0,5⌉ = 3 → drittes kleinstes
    assert K.calibrate("LAC", P4, TRUTH4, KOBS4, 50) == pytest.approx(0.4)
    # APS: Zeile 1 wahre Krankheit 0 (Rang 1): 0 | Zeile 2 Krankheit 1 (Rang 2): 0,5 | Zeile 3 Krankheit 1 (Rang 1): 0 | Zeile 4 Krankheit 2 (Rang 1): 0 → sortiert 0 0 0 0,5; drittes = 0
    assert K.calibrate("APS", P4, TRUTH4, KOBS4, 50) == pytest.approx(0.0)


def test_kalibrierung_mondrian_je_klasse_von_hand():
    th = K.calibrate("MONDRIAN", P4, TRUTH4, KOBS4, 50)
    # Klassen nach kobs 1, 2, 3, 6 → 0, 0, 1, 2. Klasse 0: Ergebnisse 0,4 und 0,6, ⌈3 · 0,5⌉ = 2 → 0,6; Klasse 1: 0,3 (⌈2 · 0,5⌉ = 1); Klasse 2: 0,2
    assert th == pytest.approx(np.array([0.6, 0.3, 0.2]))


def test_mondrian_leere_klasse_hat_unendliche_schwelle():
    th = K.calibrate("MONDRIAN", P4[:2], TRUTH4[:2], KOBS4[:2], 50)
    assert th[0] == pytest.approx(0.6) and th[1] == math.inf and th[2] == math.inf


def test_mengen_enthalten_die_schwelle_selbst():
    for method in ("LAC", "APS"):
        th = K.calibrate(method, P4, TRUTH4, KOBS4, 50)
        sets = K.predict_sets(method, P4, th, KOBS4)
        allscores = K.lac_scores_all(P4) if method == "LAC" else K.aps_scores_all(P4)
        s_true = K.true_scores(allscores, TRUTH4)
        assert sets[np.argmax(s_true == th), TRUTH4[np.argmax(s_true == th)]]   # der Kalibrierpatient mit dem Ergebnis der Schwelle liegt in seiner Menge (≤, nicht <)


def test_mondrian_mengen_nutzen_die_schwelle_der_eigenen_klasse():
    th = K.calibrate("MONDRIAN", P4, TRUTH4, KOBS4, 50)    # [0,6 0,3 0,2], aus denselben Ausdrücken wie die Ergebnisse (Gleichheit an der Schwelle ist dann exakt)
    sets = K.predict_sets("MONDRIAN", P4, th, KOBS4)
    # 1 − P: Zeile 1 [0,4 0,7 0,9] Schwelle 0,6 → {0}; Zeile 2 [0,5 0,6 0,9] Schwelle 0,6 → {0, 1}; Zeile 3 [0,8 0,3 0,9] Schwelle 0,3 → {1}; Zeile 4 [0,9 0,9 0,2] Schwelle 0,2 → {2}
    assert sets.tolist() == [[True, False, False], [True, True, False], [False, True, False], [False, False, True]]


def test_auswertung_von_hand():
    sets = np.array([[1, 0, 0], [1, 1, 0], [0, 1, 0], [0, 0, 1]], dtype=bool)
    out = K.evaluate(sets, np.array([0, 1, 1, 2]), KOBS4)
    assert out["cov"] == pytest.approx(100.0) and out["size"] == pytest.approx(1.25)
    assert out["cov_b"] == pytest.approx([100.0, 100.0, 100.0]) and out["size_b"] == pytest.approx([1.5, 1.0, 1.0])
    assert out["share_b"] == pytest.approx([50.0, 25.0, 25.0])
    out2 = K.evaluate(sets, np.array([1, 1, 1, 2]), KOBS4)      # Patient 1 verfehlt
    assert out2["cov"] == pytest.approx(75.0) and out2["cov_b"][0] == pytest.approx(50.0)


def test_auswertung_leere_klasse_ist_nan_und_anteil_null():
    sets = np.ones((2, 3), dtype=bool)
    out = K.evaluate(sets, np.array([0, 1]), np.array([1, 2]))
    assert math.isnan(out["cov_b"][1]) and math.isnan(out["size_b"][2]) and out["share_b"] == pytest.approx([100.0, 0.0, 0.0])


def test_feste_top_liste_von_hand():
    # Top-1: Zeilen 1 (Krankheit 0, Rang 1) und 3 (Krankheit 1, Rang 1) treffen, Zeile 2 (Rang 2) und 4 (Krankheit 2, Rang 1) → 3 von 4
    assert K.fixed_top(P4, TRUTH4, 1) == pytest.approx(75.0)
    assert K.fixed_top(P4, TRUTH4, 2) == pytest.approx(100.0)


def test_unbekanntes_verfahren_wird_abgelehnt():
    with pytest.raises(ValueError):
        K.calibrate("XYZ", P4, TRUTH4, KOBS4, 90)
    with pytest.raises(ValueError):
        K.predict_sets("XYZ", P4, 0.5, KOBS4)
