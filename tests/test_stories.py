"""Abnahmekriterien der Presets an der vorgerechneten Messreihe; jedes Kriterium kippt einzeln an einer künstlichen Zelle (Preset-Disziplin)."""

import kfu_constants as C
import kfu_results as RES
import kfu_stories as ST

STANDARD = dict(cov=(90.0, 1.0), cb=(80.0, 91.0, 96.0), size=14.0, sb=(25.0, 13.0, 6.0), share0=25.0)


def _verfahren(cov=90.0, sd=1.0, cb=(80.0, 91.0, 96.0), size=14.0, sb=(25.0, 13.0, 6.0), share0=25.0):
    return {"cov": [cov, sd], "size": [size, 1.0], "cov_b": [[v, 1.0] for v in cb], "size_b": [[v, 1.0] for v in sb], "share_b": [[share0, 1.0], [40.0, 1.0], [35.0 - (share0 - 25.0), 1.0]]}


def _zelle(target=90, lac=None, aps=None, mond=None):
    s = {"LAC": lac or _verfahren(), "APS": aps or _verfahren(), "MONDRIAN": mond or _verfahren()}
    return {"settings": {"target": target, "kb": 0, "shift": 0, "ncal": 500}, "A": {"summary": s}, "B": {"summary": s}}


def _ok(name, c, base=None, zeile=None):
    rows = ST.check_preset(name, c, base or _zelle())
    return [ok for _, w, ok in rows if w == "A"] if zeile is None else [ok for _, w, ok in rows if w == "A"][zeile]


def test_alle_kriterien_aller_presets_gelten_in_beiden_mengen():
    for name, rows in ST.check_all().items():
        assert rows and {w for _, w, _ in rows} == {"A", "B"}, name
        assert all(ok for _, _, ok in rows), [(t, w) for t, w, ok in rows if not ok]


def test_jedes_preset_hat_kriterien():
    assert set(ST.CRITERIA) == set(C.PRESETS)


def test_standard_kippt_einzeln():
    gut = _zelle(lac=_verfahren(cov=88.0, cb=(84.9, 91.0, 90.1)))
    assert _ok("Standard", gut) == [True, True, True]
    assert _ok("Standard", _zelle(lac=_verfahren(cov=87.9, cb=(84.9, 91.0, 90.1))), zeile=0) is False
    assert _ok("Standard", _zelle(lac=_verfahren(cov=88.0, cb=(85.0, 91.0, 90.1))), zeile=1) is False          # genau 5 Punkte: nicht mehr als 5
    assert _ok("Standard", _zelle(lac=_verfahren(cov=88.0, cb=(84.9, 91.0, 90.0))), zeile=2) is False          # genau auf dem Ziel: nicht darüber


def test_duenne_wissensbasis_kippt_einzeln():
    base = _zelle(lac=_verfahren(size=14.0))
    assert _ok("Dünne Wissensbasis", _zelle(lac=_verfahren(size=42.1)), base) == [True, True]
    assert _ok("Dünne Wissensbasis", _zelle(lac=_verfahren(size=42.0)), base, 1) is False                      # genau dreimal: nicht mehr als dreimal
    assert _ok("Dünne Wissensbasis", _zelle(lac=_verfahren(cov=87.9, size=42.1)), base, 0) is False


def test_schwierige_faelle_kippt_einzeln():
    assert _ok("Schwierige Fälle", _zelle(lac=_verfahren(cb=(84.9, 91.0, 96.0), share0=20.0))) == [True, True]
    assert _ok("Schwierige Fälle", _zelle(lac=_verfahren(cb=(85.0, 91.0, 96.0), share0=20.0)), zeile=0) is False
    assert _ok("Schwierige Fälle", _zelle(lac=_verfahren(cb=(84.9, 91.0, 96.0), share0=19.9)), zeile=1) is False


def test_verschobene_dokumentation_kippt_einzeln():
    schlecht = dict(cov=79.9)
    assert _ok("Verschobene Dokumentation", _zelle(lac=_verfahren(**schlecht), aps=_verfahren(**schlecht), mond=_verfahren(**schlecht))) == [True, True]
    assert _ok("Verschobene Dokumentation", _zelle(lac=_verfahren(cov=80.0), aps=_verfahren(**schlecht), mond=_verfahren(**schlecht)), zeile=0) is False
    assert _ok("Verschobene Dokumentation", _zelle(lac=_verfahren(**schlecht), aps=_verfahren(cov=80.0), mond=_verfahren(**schlecht)), zeile=1) is False
    assert _ok("Verschobene Dokumentation", _zelle(lac=_verfahren(**schlecht), aps=_verfahren(**schlecht), mond=_verfahren(cov=80.0)), zeile=1) is False


def test_mondrian_kippt_einzeln():
    lac = _verfahren(sb=(25.0, 13.0, 6.0))
    gut = _verfahren(cb=(93.0, 87.0, 90.0), sb=(37.6, 13.0, 6.0))
    assert _ok("Mondrian", _zelle(lac=lac, mond=gut)) == [True, True]
    assert _ok("Mondrian", _zelle(lac=lac, mond=_verfahren(cb=(93.1, 87.0, 90.0), sb=(37.6, 13.0, 6.0))), zeile=0) is False
    assert _ok("Mondrian", _zelle(lac=lac, mond=_verfahren(cb=(93.0, 86.9, 90.0), sb=(37.6, 13.0, 6.0))), zeile=0) is False   # Klasse 2: 3,1 Punkte unter dem Ziel
    assert _ok("Mondrian", _zelle(lac=lac, mond=_verfahren(cb=(93.0, 87.0, 86.9), sb=(37.6, 13.0, 6.0))), zeile=0) is False
    assert _ok("Mondrian", _zelle(lac=lac, mond=_verfahren(cb=(93.0, 87.0, 90.0), sb=(37.5, 13.0, 6.0))), zeile=1) is False   # genau das 1,5-fache: nicht mehr


def test_kleine_kalibriermenge_kippt_einzeln():
    base = _zelle(lac=_verfahren(sd=1.0))
    assert _ok("Kleine Kalibriermenge", _zelle(lac=_verfahren(cov=88.0, sd=1.5)), base) == [True, True]
    assert _ok("Kleine Kalibriermenge", _zelle(lac=_verfahren(cov=87.9, sd=1.5)), base, 0) is False
    assert _ok("Kleine Kalibriermenge", _zelle(lac=_verfahren(cov=88.0, sd=1.49)), base, 1) is False


def test_ein_kriterium_gilt_nur_wenn_es_in_beiden_mengen_gilt():
    gut, schlecht = _verfahren(cb=(84.9, 91.0, 96.0), share0=25.0), _verfahren(cb=(90.0, 91.0, 96.0), share0=25.0)
    c = {"settings": {"target": 90}, "A": {"summary": {"LAC": gut}}, "B": {"summary": {"LAC": schlecht}}}
    rows = ST.check_preset("Schwierige Fälle", c, c)
    assert [(w, ok) for _, w, ok in rows if "unter dem Ziel" in _] == [("A", True), ("B", False)]


def test_presets_der_messreihe_sind_gemessen():
    for name, preset in C.PRESETS.items():
        s = RES.Settings(**{k: v for k, v in preset.items() if k in ("target", "kb", "shift", "ncal")})
        assert RES.cell(s) is not None, name
