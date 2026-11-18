"""Orakel-Tests (unabhängiger Rechenweg, DEMO-PLAYBOOK §11a):
(a) Schwelle gegen eine schleifenweise Einfügesortierung; (b) Eigenschaftstest der Garantie über viele Zufalls-Seeds, auch bei schlechtem Posterior (3 Fälle je Krankheit);
(c) Beta-Verteilung gegen scipy, gegen eine Simulation mit gleichverteilten Ergebnissen und gegen die Simulation der Demo; (d) Mondrian-Abdeckung je Klasse; (e) Monotonie in der Ziel-Abdeckung."""

import math

import numpy as np
import pytest

import kfu_conformal as K
import kfu_constants as C
import kfu_garantie as G
import kfu_live as L
import kfu_rankers as R
import kfu_world as W
from kfu_stream import derive

SE4 = 4.0   # Schranken der Eigenschaftstests: vier Standardfehler des Mittels über die Welten


def _schwelle_schleife(werte, ziel):
    """Unabhängiger Rechenweg: Einfügesortierung, Rang ⌈(n + 1) · Ziel / 100⌉ in Ganzzahlrechnung."""
    out = []
    for w in werte:
        pos = 0
        while pos < len(out) and out[pos] <= w:
            pos += 1
        out.insert(pos, w)
    n = len(out)
    k = -(-((n + 1) * ziel) // 100)
    return math.inf if (n == 0 or k > n) else out[k - 1]


@pytest.mark.parametrize("n", [1, 2, 5, 19, 20, 99, 100, 250])
@pytest.mark.parametrize("ziel", [50, 80, 90, 95])
def test_a_schwelle_gleich_schleifenweise_sortierung(n, ziel):
    rng = np.random.default_rng(1000 * n + ziel)
    s = rng.random(n)
    assert K.threshold(s, ziel) == _schwelle_schleife(list(s), ziel)


def test_a_schwelle_mit_gleichstaenden_gleich_schleife():
    s = [0.1, 0.1, 0.1, 0.4, 0.4, 0.9, 0.9, 0.9, 0.9, 1.0]
    for ziel in (10, 50, 75, 90):
        assert K.threshold(s, ziel) == _schwelle_schleife(s, ziel)


def _worlds(kb, ncal, seed, n_worlds):
    s = L.Settings(kb=kb, ncal=ncal, seed=seed)
    return [L.run_world(s, i) for i in range(n_worlds)]


@pytest.fixture(scope="module")
def welten_duenn():
    """Zwanzig Welten mit aus 3 Fällen geschätzter Wissensbasis: der Posterior ist schlecht, die Garantie soll trotzdem im Mittel halten."""
    return _worlds(3, 500, 7000, 20)


@pytest.mark.parametrize("methode", ["LAC", "APS", "MONDRIAN"])
def test_b_garantie_im_mittel_auch_bei_schlechtem_posterior(welten_duenn, methode):
    cov = np.array([r.methods[methode]["cov"] for r in welten_duenn])
    se = cov.std(ddof=1) / len(cov) ** 0.5
    assert cov.mean() >= 90.0 - SE4 * se


def test_b_garantie_gilt_auch_fuer_andere_ziele_und_gut_gelernte_modelle():
    for target in (80, 95):
        s = L.Settings(target=target, kb=0, seed=7100)
        cov = np.array([L.run_world(s, i).methods["LAC"]["cov"] for i in range(20)])
        se = cov.std(ddof=1) / len(cov) ** 0.5
        assert cov.mean() >= target - SE4 * se


def test_b_garantie_bricht_bei_verschobener_dokumentation():
    """Negativkontrolle: die Eigenschaft ist nicht trivial, sie verletzt sich, wenn Austauschbarkeit fehlt."""
    s = L.Settings(shift=2, seed=7200)
    cov = np.array([L.run_world(s, i).methods["LAC"]["cov"] for i in range(10)])
    assert cov.mean() < 90.0 - 10.0


@pytest.mark.parametrize("n, ziel", [(100, 90), (500, 90), (2000, 90), (500, 80), (500, 95), (19, 95), (9, 90)])
def test_c_beta_parameter_gegen_scipy_formel(n, ziel):
    stats = pytest.importorskip("scipy.stats")
    a, b = G.beta_params(n, ziel)
    mean, sd = G.beta_mean_sd(n, ziel)
    ref = stats.beta(a, b)
    assert mean == pytest.approx(ref.mean(), rel=1e-12) and sd == pytest.approx(ref.std(), rel=1e-12)
    k = math.ceil((n + 1) * ziel / 100 - 1e-9)          # Rang der Ordnungsstatistik: Beta(k, n + 1 − k)
    assert (a, b) == (k, n + 1 - k)


@pytest.mark.parametrize("n, ziel", [(100, 90), (500, 90), (50, 80)])
def test_c_beta_gegen_simulation_mit_gleichverteilten_ergebnissen(n, ziel):
    """Unabhängig von der Demo: Ergebnisse gleichverteilt, dann ist die Abdeckung der Kalibrierung die k-te Ordnungsstatistik selbst."""
    rng = np.random.default_rng(n + ziel)
    k = -(-((n + 1) * ziel) // 100)
    cov = np.sort(rng.random((20000, n)), axis=1)[:, k - 1]
    mean, sd = G.beta_mean_sd(n, ziel)
    assert cov.mean() == pytest.approx(mean, abs=4 * sd / 20000 ** 0.5)
    assert cov.std(ddof=1) == pytest.approx(sd, rel=0.04)


@pytest.fixture(scope="module")
def vorrat():
    return G.true_score_pool(5)


@pytest.mark.parametrize("n", [100, 500, 2000])
def test_c_streuung_der_demo_stimmt_mit_beta_ueberein(vorrat, n):
    r = G.spread(5, n, 90, pool=vorrat)
    assert r["sd"] == pytest.approx(r["beta_sd"], rel=0.15)
    assert r["mean"] == pytest.approx(r["beta_mean"], abs=0.005)
    assert r["min"] < r["q05"] < r["mean"]


def test_c_streuung_waechst_mit_kleinerer_kalibriermenge(vorrat):
    sds = [G.spread(5, n, 90, pool=vorrat)["sd"] for n in (100, 500, 2000)]
    assert sds[0] > sds[1] > sds[2]


@pytest.fixture(scope="module")
def welten_gross():
    return _worlds(0, 2000, 7300, 20)


def test_d_mondrian_abdeckung_je_klasse(welten_gross):
    for c in range(3):
        cov = np.array([r.methods["MONDRIAN"]["cov_b"][c] for r in welten_gross])
        se = cov.std(ddof=1) / len(cov) ** 0.5
        assert cov.mean() >= 90.0 - SE4 * se, c


def test_d_lac_verfehlt_die_erste_klasse_deutlich(welten_gross):
    """Negativkontrolle zu (d): ohne Mondrian liegt die Abdeckung bei 1–2 Merkmalen unter dem Ziel."""
    cov = np.array([r.methods["LAC"]["cov_b"][0] for r in welten_gross])
    se = cov.std(ddof=1) / len(cov) ** 0.5
    assert cov.mean() < 90.0 - SE4 * se


@pytest.mark.parametrize("methode", ["LAC", "APS", "MONDRIAN"])
def test_e_menge_ist_monoton_in_der_ziel_abdeckung(methode):
    wseed = derive(11, 10)
    world = W.make_world(wseed, C.ND, C.Q_BASE, 0)
    cal = W.sample_patients(world, derive(wseed, 21), 400)
    test = W.sample_patients(world, derive(wseed, 22), 300)
    p_cal = R.posterior(R.score_naive_bayes(cal.x, world.g, world.prior))
    p_test = R.posterior(R.score_naive_bayes(test.x, world.g, world.prior))
    k_cal, k_test = cal.x.sum(axis=1), test.x.sum(axis=1)
    sets = {t: K.predict_sets(methode, p_test, K.calibrate(methode, p_cal, cal.d, k_cal, t), k_test) for t in (50, 80, 90, 95, 99)}
    ts = sorted(sets)
    for lo, hi in zip(ts, ts[1:]):
        assert (sets[lo] <= sets[hi]).all()                 # jede Menge wächst mit dem Ziel (Teilmenge)
        assert sets[lo].sum() <= sets[hi].sum()
    assert sets[50].sum() < sets[99].sum()
