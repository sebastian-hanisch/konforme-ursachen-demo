"""Verdikte (reine Funktionen): jede Bedingung einzeln gekippt, Zahlformate, Beispielpatient, Kernfragen aus der Messreihe."""

import pytest

import kfu_constants as C
import kfu_evaluation as ev
import kfu_live as L
import kfu_results as RES


def test_zahlformate_mit_dezimalkomma():
    assert ev.pct(89.54) == "89,5" and ev.spct(-0.5) == "-0,5" and ev.spct(1.25) == "+1,2" and ev.dec(0.12345) == "0,123"


@pytest.mark.parametrize("gap, se, erwartet", [
    (0.0, 1.0, True),             # genau auf dem Ziel
    (-1.9, 0.1, True),            # unter dem Ziel, aber innerhalb der Toleranz von 2 Punkten
    (-2.1, 0.1, False),           # außerhalb der Toleranz und mehr als zwei Standardfehler
    (-2.1, 1.2, True),            # außerhalb der Toleranz, aber unter zwei Standardfehlern: nicht gedeutet
    (-5.0, 2.4, False),           # genau über zwei Standardfehler (2 · 2,4 = 4,8)
    (3.0, 0.1, True),             # über dem Ziel
])
def test_hält_bedingung_beide_zweige_einzeln(gap, se, erwartet):
    assert ev.holds(gap, se) is erwartet


def test_verdikt_abdeckung_drei_zustaende():
    kind, text = ev.verdict_abdeckung("LAC", 90, 89.5, -0.5, 0.7, 0)
    assert kind == "success" and "hält im Mittel" in text and "89,5 %" in text and "Ziel 90 %" in text and "Standardfehler 0,7" in text
    kind, text = ev.verdict_abdeckung("LAC", 90, 71.3, -18.7, 1.0, 2)
    assert kind == "warning" and "hält hier nicht" in text and "fehlen mehr Merkmale" in text
    kind, text = ev.verdict_abdeckung("APS", 90, 70.0, -20.0, 1.0, 1)
    assert kind == "warning" and "Vorab" in text and "APS" in text
    kind, text = ev.verdict_abdeckung("MONDRIAN", 90, 90.0, 0.0, 0.5, 2)
    assert kind == "success" and "Verschiebung im Test" in text                  # die Verschiebung wird auch beim Halten erwähnt


def test_verdikt_abdeckung_ohne_verschiebung_nennt_keine_verschiebung():
    _, text = ev.verdict_abdeckung("LAC", 90, 90.0, 0.0, 0.5, 0)
    assert "Verschiebung" not in text


def test_verdikt_klasse_zwei_zustaende():
    kind, text = ev.verdict_klasse("LAC", 0, 90, 79.5, -10.5, 1.2, 23.7, 13.7, 25.1)
    assert kind == "warning" and "1–2 Merkmale" in text and "25,1 %" in text and "79,5 %" in text and "23,7 Krankheiten gegen 13,7" in text
    kind, text = ev.verdict_klasse("MONDRIAN", 2, 90, 90.5, 0.5, 0.8, 2.1, 20.1, 32.0)
    assert kind == "success" and "5 und mehr Merkmale" in text


def test_kennzahlen_und_verdikte_einer_messung():
    m = L.measure(L.Settings(seed=11), n_worlds=2, n_example=30)
    k = ev.kennzahlen(m, "LAC", 0)
    assert set(k) == {"summary", "method", "cls", "target", "gap_all", "gap_cls"}
    (k1, t1), (k2, t2) = ev.verdicts(m, k)
    assert k1 in ("success", "warning") and k2 in ("success", "warning") and t1 and t2
    s = k["summary"]["LAC"]
    assert k["gap_all"][0] == pytest.approx(s["cov"][0] - 90.0)
    assert k["gap_cls"][0] == pytest.approx(s["cov_b"][0][0] - 90.0)


def test_beispielpatient_filter_und_sicht():
    m = L.measure(L.Settings(seed=11), n_worlds=1, n_example=C.N_EXAMPLE)
    alle = ev.example_indices(m, 0)
    assert alle == list(range(C.N_EXAMPLE_SHOWN))
    for focus in (1, 2, 3):
        pos = ev.example_indices(m, focus)
        assert len(pos) <= C.N_EXAMPLE_SHOWN
        import kfu_conformal as K
        assert (K.bin_of(m.runs[0].example["kobs"][pos]) == focus - 1).all()
    v = ev.example_view(m, alle, 0)
    assert set(v["methods"]) == set(C.METHODS) and len(v["top_ids"]) == 8
    assert v["top_p"] == sorted(v["top_p"], reverse=True) and v["rank_true"] >= 1
    assert all(len(r["member"]) == 8 for r in v["methods"].values())
    # Indizes außerhalb werden begrenzt
    assert ev.example_view(m, alle, 999)["true"] == ev.example_view(m, alle, len(alle) - 1)["true"]
    assert ev.example_view(m, alle, -4)["true"] == ev.example_view(m, alle, 0)["true"]


def test_beispielpatient_treffer_stimmt_mit_der_menge():
    m = L.measure(L.Settings(seed=11), n_worlds=1, n_example=60)
    ex = m.runs[0].example
    pos = ev.example_indices(m, 0)
    for j in range(len(pos)):
        v = ev.example_view(m, pos, j)
        for meth in C.METHODS:
            assert v["methods"][meth]["hit"] == bool(ex["sets"][meth][pos[j]][v["true"]])
            assert v["methods"][meth]["size"] == int(ex["sets"][meth][pos[j]].sum())


def test_kernfrage_texte_nennen_nur_gemessene_zahlen():
    base = RES.cell(RES.BASE)
    kind, text = ev.kernfrage_halt(base)
    assert kind == "warning"
    assert ev.pct(RES.pooled(base, "LAC", "cov")) in text and ev.pct(RES.pooled(base, "LAC", "cov_b", 0)) in text and ev.pct(RES.pooled(base, "LAC", "cov_b", 2)) in text
    kind, text = ev.kernfrage_bruch(RES.cell(RES.Settings(shift=0)), RES.cell(RES.Settings(shift=1)), RES.cell(RES.Settings(shift=2)), RES.cell(RES.Settings(kb=3)))
    assert kind == "warning" and ev.pct(RES.pooled(RES.cell(RES.Settings(shift=2)), "LAC", "cov")) in text
    kind, text = ev.kernfrage_preis({t: RES.cell(RES.Settings(target=t)) for t in C.TARGET_OPTIONS}, base)
    assert kind == "info" and "fünf wahrscheinlichsten Krankheiten" in text
    kind, text = ev.kernfrage_streuung(RES.load()["spread"])
    assert kind == "info" and "Beta" in text


def test_kernfrage_halt_info_wenn_klasse_nicht_unter_dem_ziel():
    c = {"settings": {"target": 90}, "A": {"summary": {"LAC": {"cov": [90.0, 1.0], "cov_b": [[89.5, 1.0], [90.0, 1.0], [90.5, 1.0]]}}},
         "B": {"summary": {"LAC": {"cov": [90.0, 1.0], "cov_b": [[89.5, 1.0], [90.0, 1.0], [90.5, 1.0]]}}}}
    kind, _ = ev.kernfrage_halt(c)
    assert kind == "info"


def test_kernfrage_bruch_info_wenn_verschiebung_nichts_aendert():
    def cell(v):
        return {"settings": {"target": 90}, "A": {"summary": {"LAC": {"cov": [v, 1.0], "size": [10.0, 1.0]}}}, "B": {"summary": {"LAC": {"cov": [v, 1.0], "size": [10.0, 1.0]}}}}
    kind, _ = ev.kernfrage_bruch(cell(90.0), cell(90.0), cell(89.0), cell(90.0))
    assert kind == "info"
    kind, _ = ev.kernfrage_bruch(cell(90.0), cell(90.0), cell(70.0), cell(90.0))
    assert kind == "warning"


def test_zellbeschriftung_ist_lesbar_und_enthaelt_alle_stufen():
    assert ev.cell_label(L.Settings()) == "Ziel 90 %, Wissensbasis bekannt, keine Verschiebung, 500 Kalibrierpatienten"
    assert ev.cell_label(L.Settings(target=95, kb=3, shift=2, ncal=100)) == "Ziel 95 %, Wissensbasis aus 3 Fällen, Dokumentation verschoben, 100 Kalibrierpatienten"
    assert len({ev.cell_label(s) for s in RES.sweep_settings()}) == len(RES.sweep_settings())     # jede Zelle hat ihre eigene Beschriftung
