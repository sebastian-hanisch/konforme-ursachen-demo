"""Live-Messung: Wiederholbarkeit, Form, Zweig-Tests je Regler (jede Stufe ändert mindestens ein Verfahren), Verschiebungen, Auswertungsfunktionen."""

import dataclasses

import numpy as np
import pytest

import kfu_conformal as K
import kfu_constants as C
import kfu_live as L
import kfu_rankers as R
import kfu_world as W
from kfu_stream import derive

KLEIN = dict(n_worlds=2, n_example=40)   # kleine Messungen: schnell, nur für Zweig- und Formtests
BASIS = L.Settings(seed=11)


def _werte(s, **kw):
    sm = L.summarize(L.measure(s, **{**KLEIN, **kw}))
    return {m: (sm[m]["cov"][0], sm[m]["size"][0]) for m in C.METHODS}


def test_gleicher_zufalls_seed_gleiche_messung_anderer_seed_andere():
    a, b = _werte(BASIS), _werte(BASIS)
    assert a == b
    assert a != _werte(L.Settings(seed=12))


def test_settings_nur_mit_schluesselwoertern():
    with pytest.raises(TypeError):
        L.Settings(90, 0, 0, 500, 35)   # positional: nicht erlaubt (ein eingefügtes Feld würde Werte still verschieben)
    assert L.Settings(seed=3).key() == "t90_kb0_sh0_n500"
    assert dataclasses.is_dataclass(L.Settings)


def test_form_der_messung_und_der_kennzahlen():
    m = L.measure(BASIS, **KLEIN)
    assert len(m.runs) == 2
    for run in m.runs:
        assert set(run.methods) == set(C.METHODS)
        for v in run.methods.values():
            assert len(v["cov_b"]) == len(v["size_b"]) == len(v["share_b"]) == 3
            assert sum(v["share_b"]) == pytest.approx(100.0)
            assert 0.0 <= v["cov"] <= 100.0 and 1.0 <= v["size"] <= C.ND
    assert len(m.runs[0].example["d"]) == 40 and m.runs[0].example["p"].shape == (40, C.ND)
    assert not m.runs[1].example                       # nur die erste Welt liefert Beispielpatienten
    s = L.summarize(m)
    assert set(s) == {*C.METHODS, "fixed"} and len(s["LAC"]["cov_b"]) == 3


def test_patienten_ohne_dokumentiertes_merkmal_sind_entfernt():
    run = L.run_world(BASIS, 0)
    assert run.n_cal < BASIS.ncal and run.n_test < C.N_TEST and run.n_cal > 0.9 * BASIS.ncal
    ex = L.run_world(BASIS, 0, 30).example
    assert (ex["kobs"] >= 1).all()


@pytest.mark.parametrize("aenderung", [dict(target=80), dict(target=95), dict(kb=30), dict(kb=3), dict(shift=1), dict(shift=2), dict(ncal=100), dict(ncal=2000)])
def test_jede_stufe_aendert_mindestens_ein_verfahren(aenderung):
    """Zweig-Test (Nullspalten-Falle): jede Stufe weicht von der Voreinstellung auf mindestens einem Verfahren ab."""
    base = _werte(BASIS)
    neu = _werte(L.Settings(seed=11, **aenderung))
    assert any(abs(neu[m][0] - base[m][0]) > 1e-9 or abs(neu[m][1] - base[m][1]) > 1e-9 for m in C.METHODS), aenderung


def test_die_drei_verfahren_weichen_voneinander_ab():
    w = _werte(BASIS)
    assert len({w["LAC"], w["APS"], w["MONDRIAN"]}) == 3
    sets = L.run_world(BASIS, 0, 60).example["sets"]
    assert not np.array_equal(sets["LAC"], sets["APS"]) and not np.array_equal(sets["LAC"], sets["MONDRIAN"])


def test_ziel_ordnet_die_mengengroesse():
    sizes = [_werte(L.Settings(seed=11, target=t))["LAC"][1] for t in (80, 90, 95)]
    assert sizes[0] < sizes[1] < sizes[2]


def test_duenne_wissensbasis_vergroessert_die_menge_und_senkt_die_feste_liste():
    voll, duenn = L.summarize(L.measure(BASIS, **KLEIN)), L.summarize(L.measure(L.Settings(seed=11, kb=3), **KLEIN))
    assert duenn["LAC"]["size"][0] > 2 * voll["LAC"]["size"][0]
    assert duenn["fixed"]["top5"][0] < voll["fixed"]["top5"][0]


def test_verschiebung_der_dokumentation_senkt_die_abdeckung():
    voll, vers = L.summarize(L.measure(BASIS, **KLEIN)), L.summarize(L.measure(L.Settings(seed=11, shift=2), **KLEIN))
    for m in C.METHODS:
        assert vers[m]["cov"][0] < voll[m]["cov"][0] - 5.0, m


def test_testwelt_der_verschiebungen():
    wseed = derive(11, 10)
    world = W.make_world(wseed, C.ND, C.Q_BASE, 0)
    assert L.shifted_world(world, 0, wseed) is world
    w1, w2 = L.shifted_world(world, 1, wseed), L.shifted_world(world, 2, wseed)
    assert np.array_equal(w1.g, world.g) and not np.array_equal(w1.prior, world.prior)                  # Vorab verschoben, Dokumentation unverändert
    assert np.array_equal(w2.prior, world.prior) and (w2.g <= world.g + 1e-12).all() and (w2.g < world.g).any()   # mehr Verlust: kleinere Häufigkeiten
    assert w2.q == C.Q_SHIFT and w1.q == world.q
    assert np.array_equal(w2.f, world.f)                                                                   # die Profile bleiben


def test_modell_prior_bleibt_gleichverteilt_auch_bei_verschobenem_vorab():
    """Das Modell kennt die Verschiebung nicht: sein Vorab ist die Welt der Kalibrierung (gleichverteilt)."""
    wseed = derive(11, 10)
    world = W.make_world(wseed, C.ND, C.Q_BASE, 0)
    assert np.allclose(world.prior, 1.0 / C.ND)


def test_kalibrierung_und_test_nutzen_getrennte_ziehungen():
    wseed = derive(11, 10)
    world = W.make_world(wseed, C.ND, C.Q_BASE, 0)
    cal = W.sample_patients(world, derive(wseed, 21), 200)
    test = W.sample_patients(world, derive(wseed, 22), 200)
    assert not np.array_equal(cal.x, test.x)


def test_gepaarte_abweichung_vom_ziel():
    m = L.measure(BASIS, **KLEIN)
    mean, se = L.below_target(m, "LAC", "all", 90)
    covs = [r.methods["LAC"]["cov"] for r in m.runs]
    assert mean == pytest.approx(np.mean(covs) - 90.0)
    assert se == pytest.approx(np.std(covs, ddof=1) / np.sqrt(2))
    mean0, _ = L.below_target(m, "LAC", 0, 90)
    assert mean0 == pytest.approx(np.mean([r.methods["LAC"]["cov_b"][0] for r in m.runs]) - 90.0)


def test_mittel_und_streuung_der_zusammenfassung_sind_die_der_welten():
    m = L.measure(BASIS, **KLEIN)
    covs = [r.methods["APS"]["cov"] for r in m.runs]
    mean, sd = L.summarize(m)["APS"]["cov"]
    assert mean == pytest.approx(np.mean(covs)) and sd == pytest.approx(np.std(covs, ddof=1))


def test_n_effective_ist_das_mittel_der_welten():
    m = L.measure(BASIS, **KLEIN)
    cal, test = L.n_effective(m)
    assert cal == pytest.approx(np.mean([r.n_cal for r in m.runs])) and test == pytest.approx(np.mean([r.n_test for r in m.runs]))


def test_modell_posterior_summiert_zu_eins_und_alle_verfahren_nutzen_ihn():
    wseed = derive(11, 10)
    world = W.make_world(wseed, C.ND, C.Q_BASE, 0)
    ghat = W.knowledge_bases(world, wseed, 3)["lap"]
    pat = W.sample_patients(world, derive(wseed, 22), 100)
    p = R.posterior(R.score_naive_bayes(pat.x, ghat, world.prior))
    assert p.sum(axis=1) == pytest.approx(np.ones(len(pat.d)))
    th = K.calibrate("LAC", p, pat.d, pat.x.sum(axis=1), 90)
    assert 0.0 < th < 1.0
