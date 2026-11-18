"""Vorgerechnete Messreihe: Aufbau, Stimmigkeit der Zusammenfassungen, Zugriffsfunktionen, Reproduktion einer Zelle und Beta-Zeilen."""

import numpy as np
import pytest

import kfu_constants as C
import kfu_garantie as G
import kfu_live as L
import kfu_results as RES

DATEN = RES.load()


def test_zellen_der_messreihe_sind_die_sweep_einstellungen():
    keys = [s.key() for s in RES.sweep_settings()]
    assert len(keys) == len(set(keys)) == DATEN["meta"]["cells"] == len(DATEN["cells"])
    assert set(keys) == set(DATEN["cells"])
    assert RES.BASE.key() in keys


def test_messreihe_deckt_alle_stufen_der_messregler_ab():
    keys = {s.key() for s in RES.sweep_settings()}
    for t in C.TARGET_OPTIONS:
        assert L.Settings(target=t).key() in keys
    for kb in C.KB_OPTIONS:
        assert L.Settings(kb=kb).key() in keys
    for sh in C.SHIFT_OPTIONS:
        assert L.Settings(shift=sh).key() in keys
    for n in C.NCAL_OPTIONS:
        assert L.Settings(ncal=n).key() in keys


def test_jede_zelle_hat_zwei_mengen_mit_fuenf_welten():
    for key, c in DATEN["cells"].items():
        assert L.Settings(**c["settings"]).key() == key
        for w in ("A", "B"):
            assert len(c[w]["worlds"]) == DATEN["meta"]["worlds_per_set"] == C.N_WORLDS
            assert set(c[w]["summary"]) == {*C.METHODS, "fixed"}
            for r in c[w]["worlds"]:
                assert set(r["methods"]) == set(C.METHODS) and r["n_test"] > 0 and r["n_cal"] > 0


def test_zusammenfassung_ist_mittel_und_streuung_der_welten():
    for c in DATEN["cells"].values():
        for w in ("A", "B"):
            for m in C.METHODS:
                covs = [r["methods"][m]["cov"] for r in c[w]["worlds"]]
                mean, sd = RES.stat(c, w, m, "cov")
                assert mean == pytest.approx(np.mean(covs), abs=1e-6) and sd == pytest.approx(np.std(covs, ddof=1), abs=1e-6)
                b0 = [r["methods"][m]["size_b"][0] for r in c[w]["worlds"]]
                assert RES.stat(c, w, m, "size_b", 0)[0] == pytest.approx(np.mean(b0), abs=1e-6)


def test_anteile_der_klassen_summieren_zu_hundert_und_sind_gleich_in_allen_verfahren():
    for c in DATEN["cells"].values():
        for w in ("A", "B"):
            for r in c[w]["worlds"]:
                shares = [r["methods"][m]["share_b"] for m in C.METHODS]
                assert shares[0] == shares[1] == shares[2] and sum(shares[0]) == pytest.approx(100.0, abs=1e-4)


def test_zugriff_cell_nearest_und_pooled():
    assert RES.cell(RES.BASE) is DATEN["cells"][RES.BASE.key()]
    assert RES.cell(L.Settings(target=80, kb=3, shift=1, ncal=100)) is None
    c, gleich = RES.nearest_cell(L.Settings(target=80, kb=3, shift=1, ncal=100))
    assert gleich is False and c["settings"]["target"] == 80
    c, gleich = RES.nearest_cell(RES.BASE)
    assert gleich is True and c is RES.cell(RES.BASE)
    base = RES.cell(RES.BASE)
    assert RES.pooled(base, "LAC", "cov") == pytest.approx((RES.stat(base, "A", "LAC", "cov")[0] + RES.stat(base, "B", "LAC", "cov")[0]) / 2)
    assert RES.sets_agree(base, "LAC") == pytest.approx(abs(RES.stat(base, "A", "LAC", "cov")[0] - RES.stat(base, "B", "LAC", "cov")[0]))
    assert len(RES.fixed(base, "A", "top5")) == 2 and RES.fixed(base, "A", "top5")[0] > RES.fixed(base, "A", "top1")[0]


def test_abstand_zum_ziel_gepaart():
    base = RES.cell(RES.BASE)
    mean, se = RES.below_target(base, "A", "LAC")
    covs = [r["methods"]["LAC"]["cov"] for r in base["A"]["worlds"]]
    assert mean == pytest.approx(np.mean(covs) - 90.0, abs=1e-6) and se == pytest.approx(np.std(covs, ddof=1) / np.sqrt(5), abs=1e-6)


def test_streuungszeilen_gegen_formel_und_reihenfolge():
    rows = DATEN["spread"]
    assert {(r["n_cal"], r["target"]) for r in rows} >= {(100, 90), (500, 90), (2000, 90)}
    for r in rows:
        mean, sd = G.beta_mean_sd(r["n_cal"], r["target"])
        assert r["beta_mean"] == pytest.approx(mean) and r["beta_sd"] == pytest.approx(sd)
        assert r["reps"] == DATEN["meta"]["spread_reps"] and r["min"] <= r["q05"] <= r["mean"]
        assert r["sd"] == pytest.approx(r["beta_sd"], rel=0.15)


def test_reproduktion_der_voreinstellung_menge_a():
    """Die Live-Messung mit dem Zufalls-Seed der Menge A liefert die gespeicherten Zahlen (SplitMix64: plattformfest; Toleranz für Gleitkomma-Rundung)."""
    gespeichert = RES.cell(RES.BASE)["A"]["summary"]
    neu = L.summarize(L.measure(L.Settings(seed=C.SWEEP_SEEDS["A"]), n_example=0))
    for m in C.METHODS:
        assert neu[m]["cov"][0] == pytest.approx(gespeichert[m]["cov"][0], abs=0.3)
        assert neu[m]["size"][0] == pytest.approx(gespeichert[m]["size"][0], abs=0.3)
        for c in range(3):
            assert neu[m]["cov_b"][c][0] == pytest.approx(gespeichert[m]["cov_b"][c][0], abs=0.5)
