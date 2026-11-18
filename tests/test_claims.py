"""Jede Zahl der README wird hier nachgerechnet (DEMO-PLAYBOOK §4, §11a): die README wird von tools/make_readme.py aus data/kfu_results.json erzeugt, der Test prüft Gleichheit
mit dem Erzeugnis (Tabellen und Prosa) und stützt die Urteilssätze mit Zählungen über ALLE Zellen, nicht über eine einzelne Zelle. Die Zählungen sind hier von Hand gesetzt."""

import re
from functools import lru_cache
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
import sys  # noqa: E402

sys.path.insert(0, str(ROOT / "tools"))

import kfu_constants as C  # noqa: E402
import kfu_garantie as G  # noqa: E402
import kfu_results as RES  # noqa: E402
import make_readme as MR  # noqa: E402
from kfu_live import Settings  # noqa: E402

DATA = RES.load()
CELLS = DATA["cells"]
README = (ROOT / "README.md").read_text(encoding="utf-8").replace("\r\n", "\n")
D = MR.derived(DATA)


@lru_cache(maxsize=1)
def n_tests() -> int:
    """Testzahl der Suite per `pytest --collect-only`. NICHT beim Import berechnen: das Sammeln importiert diese Datei wieder und würde sich selbst endlos aufrufen."""
    return MR.count_tests()


def test_readme_equals_the_generated_text():
    """Jede Tabelle und jede Zahl der Prosa stammt aus der Messreihe: die README ist genau das Erzeugnis von tools/make_readme.py (inklusive Testzahl)."""
    assert README == MR.render(DATA, n_tests()), "README veraltet: python tools/make_readme.py ausführen (Text ändern nur in der Vorlage)"


def test_test_count_in_the_readme_is_the_suite_size():
    assert f"## Verifikation ({n_tests()} Tests)" in README


def test_readme_hat_die_pflichtabschnitte_und_hinweise():
    for heading in ("## Warum dieses Problem", "## Befunde und Korrekturen gegenüber einer früheren Rechnung", "## Modell", "## Methodik", "## Befunde (gemessen, keine Behauptungen)", "## Ehrliche Grenzen",
                    "## Verwandte Demos mit demselben mathematischen Modell", "## Bewusst nicht enthalten", "## Dateistruktur", "## Lokal ausführen", "## Tests ausführen"):
        assert heading in README, heading
    assert "Lehrmodell mit erfundenen Daten, keine medizinische Beratung" in README
    assert "austauschbar" in README and "im Mittel über Patienten" in README
    for demo in ("phaenotyp-ranking-demo", "forecast-interval-demo", "entscheidungs-schranke-demo", "kalibrierung-schwelle-demo", "grobe-merkmale-demo"):
        assert demo in README, demo
    assert README.rstrip().endswith(MR.FOOTER)


def test_dateistruktur_nennt_jede_datei_und_jede_genannte_datei_existiert():
    block = README.split("## Dateistruktur")[1].split("## Bewusst nicht enthalten")[0]
    genannt = set(re.findall(r"`([^`]+\.(?:py|json|yml|toml|txt))`", block))
    for name in genannt:
        assert (ROOT / name).exists(), name
    for f in ROOT.glob("kfu_*.py"):
        assert f.name in genannt, f.name
    for f in ("app.py", "data/kfu_results.json", "tools/sweep.py", "tools/report.py", "tools/make_readme.py", "requirements.txt", "requirements-dev.txt"):
        assert f in genannt, f


# --- Zählungen der Urteilssätze über das ganze Raster ---------------------------------------------------------------------------------------------------


def test_gesamtabdeckung_haelt_in_allen_zellen_ohne_verschobene_dokumentation():
    assert D["n_exch"] == 8 and D["n_sh2"] == 2
    assert D["exch"] == ["t90_kb0_sh0_n500", "t90_kb30_sh0_n500", "t90_kb3_sh0_n500", "t90_kb0_sh1_n500", "t80_kb0_sh0_n500", "t95_kb0_sh0_n500", "t90_kb0_sh0_n100", "t90_kb0_sh0_n2000"]
    for m in C.METHODS:
        assert D[m]["total_hold"] == 8, m
    assert "In 8 von 8 Zellen ohne verschobene Dokumentation liegt die Gesamtabdeckung von LAC höchstens 2 Punkte unter dem Ziel (APS 8, Mondrian 8)" in README


def test_lac_klasse_1_2_unter_dem_ziel_und_klasse_5_darueber():
    assert (D["LAC"]["c0_below"], D["LAC"]["c0_below5"], D["LAC"]["c2_above"]) == (8, 6, 8)
    assert "unter dem Ziel, in 6 um mehr als 5 Punkte; bei 5 und mehr Merkmalen liegt sie in 8 von 8 Zellen darüber" in README
    # Ausnahmen der 5-Punkte-Zählung: dünne Wissensbasis und Ziel 95 %
    c = [k for k in D["exch"] if not all(MR._gap(CELLS[k], w, "LAC", 0) < -5.0 for w in "AB")]
    assert c == ["t90_kb3_sh0_n500", "t95_kb0_sh0_n500"]


def test_gegenmittel_je_klasse():
    assert (D["APS"]["c0_below"], D["APS"]["c0_below5"]) == (8, 1)
    assert (D["MONDRIAN"]["c0_below"], D["MONDRIAN"]["within3"]) == (0, 7) and D["mond_exception_within3"] == ["t90_kb0_sh0_n100"]
    assert [round(D[m]["span"], 1) for m in C.METHODS] == [14.9, 7.9, 2.1]
    assert D["LAC"]["span"] > D["APS"]["span"] > D["MONDRIAN"]["span"]


def test_mondrian_preis_in_der_menge():
    assert (D["mond_c0_bigger15"], D["mond_c0_bigger"], D["mond_total_bigger"], D["mond_c2_smaller"], D["aps_total_bigger"]) == (6, 8, 7, 8, 7)
    assert D["mond_exception_total"] == ["t90_kb3_sh0_n500"]


def test_duenne_wissensbasis():
    base, kb3 = CELLS[RES.BASE.key()], CELLS[Settings(kb=3).key()]
    for w in "AB":
        assert MR._gap(kb3, w, "LAC") >= -C.PARTIAL_TOL
    assert RES.pooled(kb3, "LAC", "size") > 5.0 * RES.pooled(base, "LAC", "size")
    assert RES.fixed(kb3, "A", "top5")[0] < 0.6 * RES.fixed(base, "A", "top5")[0]


def test_verschobene_dokumentation_bricht_das_versprechen():
    assert [D[m]["sh2_below10"] for m in C.METHODS] == [2, 2, 2]
    for k in D["sh2"]:
        for m in C.METHODS:
            assert all(MR._gap(CELLS[k], w, m) < -10.0 for w in "AB")


def test_verschobenes_vorab_ohne_nachweis():
    """Beide Mengen: die Abweichung der Gesamtabdeckung vom Ziel liegt unter zwei Standardfehlern über die zehn Welten (und höchstens 2 Punkte unter dem Ziel)."""
    c = CELLS[Settings(shift=1).key()]
    for m in C.METHODS:
        gap = RES.pooled(c, m, "cov") - 90.0
        assert gap >= -C.PARTIAL_TOL
    assert abs(RES.pooled(c, "LAC", "cov") - 90.0) < 2 * RES.pooled_se(c, "LAC", "cov")


def test_menge_waechst_mit_dem_ziel():
    sizes = [RES.pooled(CELLS[Settings(target=t).key()], "LAC", "size") for t in C.TARGET_OPTIONS]
    assert sizes[0] < sizes[1] < sizes[2]
    assert 5.0 < sizes[2] / sizes[0] < 6.5


def test_streuung_der_abdeckung():
    rows = {(r["n_cal"], r["target"]): r for r in DATA["spread"]}
    sds = [rows[(n, 90)]["sd"] for n in (100, 500, 2000)]
    assert sds[0] > sds[1] > sds[2]
    for r in DATA["spread"]:
        assert r["sd"] == pytest.approx(G.beta_mean_sd(r["n_cal"], r["target"])[1], rel=0.15)
    assert max(abs(r["sd"] - r["beta_sd"]) for r in DATA["spread"]) * 100 < 0.1
    # Streuung der Welten einer Menge wächst mit kleinerer Kalibriermenge (beide Mengen: 100 gegen 2000)
    for w in "AB":
        assert RES.stat(CELLS[Settings(ncal=100).key()], w, "LAC", "cov")[1] > RES.stat(CELLS[Settings(ncal=2000).key()], w, "LAC", "cov")[1]


def test_pooled_se_ist_die_streuung_der_zehn_welten():
    c = CELLS[RES.BASE.key()]
    vals = np.array(RES.world_values(c, "LAC", "cov"))
    assert len(vals) == 10 and RES.pooled_se(c, "LAC", "cov") == pytest.approx(vals.std(ddof=1) / np.sqrt(10))
    assert RES.pooled_all(c, "LAC", "cov") == pytest.approx(RES.pooled(c, "LAC", "cov"))


def test_standardzelle_zahlen_der_readme_stehen_in_der_messreihe():
    c = CELLS[RES.BASE.key()]
    assert MR.f1(RES.pooled(c, "LAC", "cov")) in README and MR.f1(RES.pooled(c, "LAC", "cov_b", 0)) in README
    assert f"{MR.f1(RES.pooled(c, 'LAC', 'cov'))} ± {MR.f1(RES.pooled_se(c, 'LAC', 'cov'))}" in README


def test_neue_zaehlungen_der_gegenmittel_und_des_vorab():
    assert round(D["mond_span_n100"], 1) == 3.6      # Mittel der Spannweiten der beiden Mengen (über beide Mengen gepoolt wären es 3,1)
    assert (D["mond_c0_sets_below"], D["mond_c0_sets_total"]) == (1, 16) and round(D["mond_c0_min_gap"], 1) == -0.1
    assert D["lac_smaller"] == 7 and D["lac_smaller_exc"] == ["t90_kb3_sh0_n500"]
    mean, se, lo, hi = D["sh1_pair"]
    assert abs(mean) < 2 * se and lo < 0 < hi          # im Mittel kein Unterschied, je Welt Abweichungen in beide Richtungen


def test_readme_nennt_keine_planungsbegriffe_und_keine_externen_dateien():
    for wort in ("Vormessung", "Planungsordner", "messreihe_linie", "seltene-krankheiten-planung", "Plan §", "Phase", "AP 0"):
        assert wort not in README, wort
    assert "nicht nachprüfbar" in README and "gesetzt, nicht abgestimmt" in README and "nicht widerlegt" in README
    assert "einige Minuten" not in README


def test_garantie_wird_als_voraussetzung_formuliert_nicht_als_bedingung_des_verhaltens():
    assert "nur, wenn Kalibrier- und Testpatienten" not in README
    assert "Ohne Austauschbarkeit kann es halten (in dieser Rechenwelt bei verschobenem Vorab)" in README
