"""Abnahmekriterien der Presets: jedes Preset muss an der vorgerechneten Messreihe zeigen, wofür es steht (DEMO-PLAYBOOK §7, Preset-Disziplin).

Ein Kriterium ist eine Zeile (Text, Aussage über eine Zelle, die Voreinstellungs-Zelle und eine Menge von Welten). Es gilt nur, wenn es in BEIDEN Mengen (A und B) gilt."""

import kfu_constants as C
import kfu_results as RES

TOL = C.PARTIAL_TOL


def _cov(c, w, method="LAC", cls=None):
    return RES.stat(c, w, method, "cov")[0] if cls is None else RES.stat(c, w, method, "cov_b", cls)[0]


def _gap(c, w, method="LAC", cls=None):
    return _cov(c, w, method, cls) - c["settings"]["target"]


def _size(c, w, method="LAC", cls=None):
    return RES.stat(c, w, method, "size")[0] if cls is None else RES.stat(c, w, method, "size_b", cls)[0]


def criteria_standard(c, base, w):
    return [("Die Gesamtabdeckung von LAC liegt höchstens 2 Punkte unter dem Ziel", _gap(c, w) >= -TOL),
            ("Die Abdeckung von LAC bei 1–2 Merkmalen liegt mehr als 5 Punkte unter dem Ziel", _gap(c, w, cls=0) < -5.0),
            ("Die Abdeckung von LAC bei 5 und mehr Merkmalen liegt über dem Ziel", _gap(c, w, cls=2) > 0.0)]


def criteria_duenn(c, base, w):
    return [("Die Gesamtabdeckung von LAC liegt höchstens 2 Punkte unter dem Ziel", _gap(c, w) >= -TOL),
            ("Die mittlere Menge von LAC ist mehr als dreimal so groß wie in der Voreinstellung", _size(c, w) > 3.0 * _size(base, w))]


def criteria_schwierig(c, base, w):
    return [("Die Abdeckung von LAC bei 1–2 Merkmalen liegt mehr als 5 Punkte unter dem Ziel", _gap(c, w, cls=0) < -5.0),
            ("Mindestens ein Fünftel der Patienten hat nur 1–2 Merkmale", RES.stat(c, w, "LAC", "share_b", 0)[0] >= 20.0)]


def criteria_verschoben(c, base, w):
    return [("Die Gesamtabdeckung von LAC liegt mehr als 10 Punkte unter dem Ziel", _gap(c, w) < -10.0),
            ("Auch die Abdeckung von APS und von Mondrian liegt mehr als 10 Punkte unter dem Ziel", _gap(c, w, "APS") < -10.0 and _gap(c, w, "MONDRIAN") < -10.0)]


def criteria_mondrian(c, base, w):
    return [("Die Abdeckung von Mondrian liegt in jeder Klasse höchstens 3 Punkte neben dem Ziel", all(abs(_gap(c, w, "MONDRIAN", k)) <= 3.0 for k in range(3))),
            ("Die Menge von Mondrian bei 1–2 Merkmalen ist mehr als 1,5-mal so groß wie die von LAC", _size(c, w, "MONDRIAN", 0) > 1.5 * _size(c, w, "LAC", 0))]


def criteria_klein(c, base, w):
    sd_small, sd_base = RES.stat(c, w, "LAC", "cov")[1], RES.stat(base, w, "LAC", "cov")[1]
    return [("Die Gesamtabdeckung von LAC liegt höchstens 2 Punkte unter dem Ziel", _gap(c, w) >= -TOL),
            ("Die Streuung der Abdeckung über die Welten ist mindestens das 1,5-fache der Voreinstellung", sd_small >= 1.5 * sd_base)]


CRITERIA = {
    "Standard": criteria_standard,
    "Dünne Wissensbasis": criteria_duenn,
    "Schwierige Fälle": criteria_schwierig,
    "Verschobene Dokumentation": criteria_verschoben,
    "Mondrian": criteria_mondrian,
    "Kleine Kalibriermenge": criteria_klein,
}


def check_preset(name: str, c: dict, base: dict) -> list:
    """Alle Kriterien des Presets an einer Zelle: Liste (Text, Menge, erfüllt) über die Mengen A und B."""
    return [(text, w, bool(ok)) for w in ("A", "B") for text, ok in CRITERIA[name](c, base, w)]


def check_all() -> dict:
    """Preset -> Liste der Kriterien; die Zelle ist die Einstellung des Presets (ohne Zufalls-Seed)."""
    base = RES.cell(RES.BASE)
    out = {}
    for name, preset in C.PRESETS.items():
        s = RES.Settings(**{k: v for k, v in preset.items() if k in ("target", "kb", "shift", "ncal")})
        out[name] = check_preset(name, RES.cell(s), base)
    return out
