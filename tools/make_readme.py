"""Erzeugt README.md aus der Vorlage unten und data/kfu_results.json: jede Zahl der README kommt aus der Messreihe, nicht aus dem Gedächtnis.

    python tools/make_readme.py            # schreibt README.md
    python tools/make_readme.py --check    # prüft, dass README.md dem Erzeugnis entspricht (tests/test_claims.py ruft render() ebenfalls auf)

Die Testzahl wird per `pytest --collect-only` gezählt und der Vorlage übergeben. Eine Änderung des Textes gehört in diese Vorlage, nicht in die README."""

import json
import math
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import kfu_constants as C  # noqa: E402
import kfu_results as RES  # noqa: E402
import report as REP  # noqa: E402
from kfu_live import Settings  # noqa: E402

FOOTER = ("Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning "
          "([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).")

METHODS = C.METHODS
LABEL = {"base": "Wissensbasis bekannt, gleiche Verteilung", "kb3": "Wissensbasis aus 3 Fällen je Krankheit", "kb30": "Wissensbasis aus 30 Fällen je Krankheit",
         "sh1": "bekannt, Vorab im Test verschoben (Zipf statt gleichverteilt)", "sh2": "bekannt, Dokumentation im Test verschoben (q 0,6 statt 0,3)",
         "kb3sh2": "3 Fälle, Dokumentation im Test verschoben"}


def f1(x: float) -> str:
    """Eine Nachkommastelle, Dezimalkomma, Tausenderpunkt (nur an der Zahl)."""
    return f"{x:,.1f}".replace(",", "#").replace(".", ",").replace("#", ".")


def f2(x: float) -> str:
    return f"{x:.2f}".replace(".", ",")


def sgn2(x: float) -> str:
    """Zwei Nachkommastellen mit Vorzeichen und typografischem Minus."""
    return f"{x:+.2f}".replace(".", ",").replace("-", "−")


def cell_name(key: str) -> str:
    """Lesbare Beschreibung einer Zelle (die Abweichung von der Voreinstellung)."""
    c = RES.cell_settings(key)
    parts = []
    if c["target"] != C.DEFAULT["target"]:
        parts.append(f"Ziel {c['target']} %")
    if c["kb"] != C.DEFAULT["kb"]:
        parts.append(f"Wissensbasis aus {c['kb']} Fällen")
    if c["shift"] != C.DEFAULT["shift"]:
        parts.append({1: "Vorab verschoben", 2: "Dokumentation verschoben"}[c["shift"]])
    if c["ncal"] != C.DEFAULT["ncal"]:
        parts.append(f"{c['ncal']} Kalibrierpatienten")
    return ", ".join(parts) or "Voreinstellung"


def f3(x: float) -> str:
    return f"{x:.3f}".replace(".", ",")


def sgn1(x: float) -> str:
    """Eine Nachkommastelle mit Vorzeichen und typografischem Minus."""
    return f"{x:+.1f}".replace(".", ",").replace("-", "−")


def de(n: int) -> str:
    """Tausenderpunkt nur an der Zahl, nie am ganzen Satz."""
    return f"{n:,}".replace(",", ".")


def table(headers: list, rows: list) -> str:
    out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    out += ["| " + " | ".join(r) + " |" for r in rows]
    return "\n".join(out)


def count_tests() -> int:
    out = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider", "tests"], cwd=ROOT, capture_output=True, text=True).stdout
    m = re.search(r"(\d+) tests? collected", out) or re.search(r"^(\d+) tests", out, re.M)
    return int(m.group(1))


def _gap(c, w, m, cls=None):
    v = RES.stat(c, w, m, "cov")[0] if cls is None else RES.stat(c, w, m, "cov_b", cls)[0]
    return v - c["settings"]["target"]


def _both(c, f) -> bool:
    return all(f(c, w) for w in ("A", "B"))


def derived(res: dict) -> dict:
    """Alle Zahlen, die in der Prosa stehen: Zählungen über die Zellen ohne verschobene Dokumentation (austauschbar) und über die mit verschobener Dokumentation."""
    cells = res["cells"]
    exch = [k for k, c in cells.items() if c["settings"]["shift"] != 2]
    sh2 = [k for k, c in cells.items() if c["settings"]["shift"] == 2]

    def count(keys, f):
        return sum(1 for k in keys if _both(cells[k], f))

    d = {"exch": exch, "sh2": sh2, "n_exch": len(exch), "n_sh2": len(sh2)}
    for m in METHODS:
        d[m] = {
            "total_hold": count(exch, lambda c, w, m=m: _gap(c, w, m) >= -C.PARTIAL_TOL),
            "c0_below": count(exch, lambda c, w, m=m: _gap(c, w, m, 0) < 0),
            "c0_below5": count(exch, lambda c, w, m=m: _gap(c, w, m, 0) < -5.0),
            "c2_above": count(exch, lambda c, w, m=m: _gap(c, w, m, 2) > 0),
            "within3": count(exch, lambda c, w, m=m: all(abs(_gap(c, w, m, j)) <= 3.0 for j in range(3))),
            "sh2_below10": count(sh2, lambda c, w, m=m: _gap(c, w, m) < -10.0),
            "span": sum(max(_gap(cells[k], w, m, j) for j in range(3)) - min(_gap(cells[k], w, m, j) for j in range(3)) for k in exch for w in ("A", "B")) / (2 * len(exch)),
        }
    st = RES.stat
    d["mond_total_bigger"] = count(exch, lambda c, w: st(c, w, "MONDRIAN", "size")[0] > st(c, w, "LAC", "size")[0])
    d["mond_c0_bigger15"] = count(exch, lambda c, w: st(c, w, "MONDRIAN", "size_b", 0)[0] > 1.5 * st(c, w, "LAC", "size_b", 0)[0])
    d["mond_c0_bigger"] = count(exch, lambda c, w: st(c, w, "MONDRIAN", "size_b", 0)[0] > st(c, w, "LAC", "size_b", 0)[0])
    d["mond_c2_smaller"] = count(exch, lambda c, w: st(c, w, "MONDRIAN", "size_b", 2)[0] < st(c, w, "LAC", "size_b", 2)[0])
    d["aps_total_bigger"] = count(exch, lambda c, w: st(c, w, "APS", "size")[0] > st(c, w, "LAC", "size")[0])
    d["mond_exception_total"] = [k for k in exch if not _both(cells[k], lambda c, w: st(c, w, "MONDRIAN", "size")[0] > st(c, w, "LAC", "size")[0])]
    d["mond_exception_within3"] = [k for k in exch if not _both(cells[k], lambda c, w: all(abs(_gap(c, w, "MONDRIAN", j)) <= 3.0 for j in range(3)))]
    d["max_cov_shift"] = max(abs(RES.pooled(RES.cell(s), "LAC", "cov") - REP.FRUEHER[f]["cov"]) for f, s in REP.FALL_SETTINGS.items())
    d["pool_se"] = 100.0 * math.sqrt(0.9 * 0.1 / res["meta"]["spread_pool"][1])
    n100 = cells[Settings(ncal=100).key()]
    d["mond_span_n100"] = sum(max(_gap(n100, w, "MONDRIAN", j) for j in range(3)) - min(_gap(n100, w, "MONDRIAN", j) for j in range(3)) for w in ("A", "B")) / 2.0
    pairs = [_gap(cells[k], w, "MONDRIAN", 0) for k in exch for w in ("A", "B")]
    d["mond_c0_sets_below"], d["mond_c0_sets_total"], d["mond_c0_min_gap"] = sum(1 for g in pairs if g < 0), len(pairs), min(pairs)
    diffs = [b - a for a, b in zip(RES.world_values(cells[RES.BASE.key()], "LAC", "cov"), RES.world_values(cells[Settings(shift=1).key()], "LAC", "cov"))]
    mean_d = sum(diffs) / len(diffs)
    sd_d = math.sqrt(sum((x - mean_d) ** 2 for x in diffs) / (len(diffs) - 1))
    d["sh1_pair"] = (mean_d, sd_d / math.sqrt(len(diffs)), min(diffs), max(diffs))
    lac_smaller = lambda c, w: st(c, w, "LAC", "size")[0] < min(st(c, w, "APS", "size")[0], st(c, w, "MONDRIAN", "size")[0])  # noqa: E731
    d["lac_smaller"] = count(exch, lac_smaller)
    d["lac_smaller_exc"] = [k for k in exch if not _both(cells[k], lac_smaller)]
    return d


def case_table(res: dict) -> str:
    rows = []
    for fall, s in REP.FALL_SETTINGS.items():
        c = RES.cell(s)
        top5 = (RES.fixed(c, "A", "top5")[0] + RES.fixed(c, "B", "top5")[0]) / 2.0
        rows.append([LABEL[fall], f"{f1(RES.pooled(c, 'LAC', 'cov'))} ± {f1(RES.pooled_se(c, 'LAC', 'cov'))}", f1(RES.pooled(c, "LAC", "size")),
                     " / ".join(f1(RES.pooled(c, "LAC", "cov_b", k)) for k in range(3)), " / ".join(f1(RES.pooled(c, "LAC", "size_b", k)) for k in range(3)), f1(top5)])
    return table(["Fall (LAC, Ziel 90 %)", "Abdeckung gesamt (%)", "Menge gesamt", "Abdeckung bei 1–2 / 3–4 / 5+ Merkmalen (%)", "Menge bei 1–2 / 3–4 / 5+ Merkmalen", "feste Top-5-Liste (%)"], rows)


def old_new_table(res: dict) -> str:
    rows = []
    for fall, s in REP.FALL_SETTINGS.items():
        c, old = RES.cell(s), REP.FRUEHER[fall]
        rows.append([LABEL[fall], f"{f1(old['cov'])} → {f1(RES.pooled(c, 'LAC', 'cov'))}", f"{f1(old['size'])} → {f1(RES.pooled(c, 'LAC', 'size'))}",
                     f"{f1(old['cov_b'][0])} → {f1(RES.pooled(c, 'LAC', 'cov_b', 0))}", f"{f1(old['cov_b'][2])} → {f1(RES.pooled(c, 'LAC', 'cov_b', 2))}"])
    return table(["Fall (LAC, Ziel 90 %)", "Abdeckung gesamt (%)", "Menge gesamt", "Abdeckung bei 1–2 Merkmalen (%)", "Abdeckung bei 5+ Merkmalen (%)"], rows)


def method_table(res: dict) -> str:
    c = RES.cell(RES.BASE)
    rows = []
    for m in METHODS:
        rows.append([C.METHOD_NAMES[m], f"{f1(RES.pooled(c, m, 'cov'))} ± {f1(RES.pooled_se(c, m, 'cov'))}", f1(RES.pooled(c, m, "size")),
                     " / ".join(f1(RES.pooled(c, m, "cov_b", k)) for k in range(3)), " / ".join(f1(RES.pooled(c, m, "size_b", k)) for k in range(3))])
    return table(["Verfahren (Ziel 90 %, Wissensbasis bekannt)", "Abdeckung gesamt (%)", "Menge gesamt", "Abdeckung bei 1–2 / 3–4 / 5+ Merkmalen (%)", "Menge bei 1–2 / 3–4 / 5+ Merkmalen"], rows)


def old_new_methods(res: dict) -> str:
    c = RES.cell(RES.BASE)
    rows = []
    for m in ("APS", "MONDRIAN"):
        old = REP.FRUEHER_GEGENMITTEL[m]
        rows.append([C.METHOD_NAMES[m], f"{f1(old['cov'])} → {f1(RES.pooled(c, m, 'cov'))}", f"{f1(old['size'])} → {f1(RES.pooled(c, m, 'size'))}",
                     " / ".join(f"{f1(o)} → {f1(RES.pooled(c, m, 'cov_b', k))}" for k, o in enumerate(old["cov_b"])),
                     " / ".join(f"{f1(o)} → {f1(RES.pooled(c, m, 'size_b', k))}" for k, o in enumerate(old["size_b"]))])
    return table(["Verfahren", "Abdeckung gesamt (%)", "Menge gesamt", "Abdeckung 1–2 / 3–4 / 5+ (%)", "Menge 1–2 / 3–4 / 5+"], rows)


def shift_table(res: dict) -> str:
    rows = []
    for label, s in (("keine Verschiebung", Settings()), ("Vorab verschoben", Settings(shift=1)), ("Dokumentation verschoben", Settings(shift=2)), ("3 Fälle, Dokumentation verschoben", Settings(kb=3, shift=2))):
        c = RES.cell(s)
        rows.append([label] + [f"{f1(RES.pooled(c, m, 'cov'))} ± {f1(RES.pooled_se(c, m, 'cov'))}" for m in METHODS])
    return table(["Im Test", "Abdeckung LAC (%)", "Abdeckung APS (%)", "Abdeckung Mondrian (%)"], rows)


def target_table(res: dict) -> str:
    rows = []
    for t in C.TARGET_OPTIONS:
        c = RES.cell(Settings(target=t))
        rows.append([f"{t} %"] + [f"{f1(RES.pooled(c, m, 'cov'))}" for m in ("LAC",)] + [f1(RES.pooled(c, m, "size")) for m in METHODS] + [" / ".join(f1(RES.pooled(c, "LAC", "cov_b", k)) for k in range(3))])
    return table(["Ziel", "Abdeckung LAC (%)", "Menge LAC", "Menge APS", "Menge Mondrian", "Abdeckung LAC bei 1–2 / 3–4 / 5+ Merkmalen (%)"], rows)


def ncal_table(res: dict) -> str:
    rows = []
    for n in C.NCAL_OPTIONS:
        c = RES.cell(Settings(ncal=n))
        n_eff = sum(w["n_cal"] for w in c["A"]["worlds"] + c["B"]["worlds"]) / 10.0
        sd = (RES.stat(c, "A", "LAC", "cov")[1] + RES.stat(c, "B", "LAC", "cov")[1]) / 2.0
        rows.append([str(n), f1(n_eff), f"{f1(RES.pooled(c, 'LAC', 'cov'))} ± {f1(RES.pooled_se(c, 'LAC', 'cov'))}", f1(sd), f1(RES.pooled(c, "LAC", "size")), f1(RES.pooled(c, "MONDRIAN", "size"))])
    return table(["Kalibrierpatienten gezogen", "davon im Mittel gerankt", "Abdeckung LAC (%)", "Streuung der Welten (Punkte, Mittel der beiden Mengen)", "Menge LAC", "Menge Mondrian"], rows)


def spread_table(res: dict) -> str:
    rows = []
    for r in res["spread"]:
        rows.append([str(r["n_cal"]), f"{r['target']} %", f"{f2(100 * r['sd'])} / {f2(100 * r['beta_sd'])}", f"{f2(100 * r['mean'])} / {f2(100 * r['beta_mean'])}", f1(100 * r["q05"]), f1(100 * r["min"])])
    return table(["Kalibrierpatienten", "Ziel", "Streuung in Punkten (Simulation / Beta)", "Mittel in % (Simulation / Beta)", "5-%-Quantil der Simulation (%)", "kleinster Wert der Simulation (%)"], rows)


def render(res: dict, n_tests: int) -> str:
    d = derived(res)
    meta = res["meta"]
    base = RES.cell(RES.BASE)
    kb3, kb30, sh1, sh2, kb3sh2 = (RES.cell(s) for s in (Settings(kb=3), Settings(kb=30), Settings(shift=1), Settings(shift=2), Settings(kb=3, shift=2)))
    t80, t95 = RES.cell(Settings(target=80)), RES.cell(Settings(target=95))
    old_sh1 = REP.FRUEHER["sh1"]
    old_mond = REP.FRUEHER_GEGENMITTEL["MONDRIAN"]
    top5 = lambda c: (RES.fixed(c, "A", "top5")[0] + RES.fixed(c, "B", "top5")[0]) / 2.0  # noqa: E731
    n_cal_base = sum(w["n_cal"] for w in base["A"]["worlds"] + base["B"]["worlds"]) / 10.0
    n_test_base = sum(w["n_test"] for w in base["A"]["worlds"] + base["B"]["worlds"]) / 10.0
    sp = {(r["n_cal"], r["target"]): r for r in res["spread"]}
    share = [RES.pooled(base, "LAC", "share_b", k) for k in range(3)]
    ratio_kb3 = RES.pooled(kb3, "LAC", "size") / RES.pooled(base, "LAC", "size")
    ratio_target = RES.pooled(t95, "LAC", "size") / RES.pooled(t80, "LAC", "size")
    mond0_ratio = RES.pooled(base, "MONDRIAN", "size_b", 0) / RES.pooled(base, "LAC", "size_b", 0)
    old_mond0_ratio = old_mond["size_b"][0] / REP.FRUEHER["base"]["size_b"][0]
    lac, aps, mond = d["LAC"], d["APS"], d["MONDRIAN"]
    return f"""# Konforme Ursachenmenge – eine Menge statt einer Rangliste – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-konforme-ursachen-demo.streamlit.app/)** -->

Fall-Demo für die Website „Sebastian Hanisch – Operations Research und Machine Learning“ (Entscheidungsanalyse und Machine Learning). Statt einer Rangliste möglicher **seltener Krankheiten** nennt die Demo eine **Menge**, die die wahre Krankheit mit einer vorgegebenen **Ziel-Abdeckung** enthalten soll (**Split-Konformal**: eine Schwelle aus einer Kalibriermenge von Patienten mit bekannter Krankheit). Sie zeigt, **was dieses Versprechen zusagt, was es hält und wo es bricht**: Drei Verfahren (LAC, APS, Mondrian-LAC) werden auf derselben erfundenen Welt gemessen, mit einer festen Top-5-Liste als Vergleich. **Lehrmodell mit erfundenen Daten, keine medizinische Beratung** und keine Diagnoseempfehlung. Alle Aussagen gelten für diese Welt, diese Einstellungen und die gemessene Regel jedes Verfahrens.

**Voraussetzung der Garantie:** Das Versprechen ist garantiert **im Mittel über Patienten und über die Ziehung der Kalibriermenge**, wenn Kalibrier- und Testpatienten **austauschbar** sind (gleiche Verteilung). Ohne Austauschbarkeit kann es halten (in dieser Rechenwelt bei verschobenem Vorab) oder brechen (bei verschobener Dokumentation); die Garantie sagt darüber nichts. Es gilt nicht für einen einzelnen Patienten und nicht für jede Gruppe von Patienten. Einheiten: Abdeckung in Prozent der Patienten (gezählt werden Patienten mit mindestens einem dokumentierten Merkmal), Menge in Zahl der genannten Krankheiten (von {C.ND}).

**Bezug zu OR:** Eine Menge statt einer Entscheidung ist eine mögliche Form einer Prognose als Eingabe einer Planung: Sie sagt, wie viele Möglichkeiten offenbleiben (bei dünner Wissensbasis {f1(RES.pooled(kb3, 'LAC', 'size'))} von {C.ND} Krankheiten, siehe Befunde). Die Frage, was ein Abdeckungsversprechen zusagt, ähnelt der bei Sicherheitsbeständen aus Quantilen (gleiche Quantil-Logik, in der Demo nicht gerechnet).

## Warum dieses Problem

Eine reine Rangliste sagt „die wahrscheinlichste Ursache ist X“ und schweigt darüber, wie sicher das ist. Eine konforme Menge verspricht stattdessen im Mittel (unter Austauschbarkeit): in mindestens Ziel Prozent der Fälle ist die wahre Ursache dabei; eine einzelne Kalibrierung kann darunter liegen (Kernfrage 4). Kernfragen: **Hält das Versprechen auch für jede Gruppe von Patienten? Wann bricht es? Was kostet es an Größe der Menge? Wie stark streut die Abdeckung mit der Kalibriermenge?** Die Antworten stehen vorgerechnet in den Befunden unten ({meta['cells']} Zellen, je zwei Mengen von {meta['worlds_per_set']} Welten); die Messung oben auf der Seite rechnet fünf Welten live nach.

## Befunde und Korrekturen gegenüber einer früheren Rechnung

Dieser Demo ging eine frühere Rechnung mit dem Zufallsgenerator von NumPy voraus (fünf Welten, ± Standardfehler). Ihre Zahlen stehen hier als Text und sind **nicht nachprüfbar** (anderer Generator, keine Datei im Repo). Die Messreihe der Demo rechnet mit dem eigenen SplitMix64 neu: je Zelle zwei Mengen von {meta['worlds_per_set']} Welten (Zufalls-Seed {meta['sets']['A']} und {meta['sets']['B']}), {de(meta['test_patients_per_world'])} Testpatienten je Welt vor dem Entfernen von Patienten ohne dokumentiertes Merkmal. **Die Befunde bleiben der Richtung nach bestehen; die Gesamtabdeckung von LAC verschiebt sich in den sechs Fällen um höchstens {f1(d['max_cov_shift'])} Punkte, und zwei Aussagen der früheren Rechnung gelten so nicht mehr.** Frühere Rechnung → Messreihe (zehn Welten):

{old_new_table(res)}

{old_new_methods(res)}

- **Das verschobene Vorab senkt die Abdeckung im Mittel dieser Welt nicht nachweisbar (einzelne Welten weichen in beide Richtungen ab).** Die frühere Rechnung maß {f1(old_sh1['cov'])} ± {f1(old_sh1['cov_se'])} % (rund 1,4 Standardfehler unter dem Ziel, nicht deutbar), die Messreihe {f1(RES.stat(sh1, 'A', 'LAC', 'cov')[0])} % (Menge A) und {f1(RES.stat(sh1, 'B', 'LAC', 'cov')[0])} % (Menge B). Gepaart über die zehn Welten (dieselben Welten und Kalibrierungen wie im Standard) ist der Unterschied der Gesamtabdeckung von LAC {sgn1(d['sh1_pair'][0])} ± {f1(d['sh1_pair'][1])} Punkte (Standardfehler), je Welt von {sgn1(d['sh1_pair'][2])} bis {sgn1(d['sh1_pair'][3])} Punkten. Eine unabhängige Nachrechnung mit 200 weiteren Welten fand im Mittel +0,08 ± 0,09 Punkte und je Welt −4,8 bis +2,9 Punkte (nicht im Repo nachprüfbar). Ein Einfluss des Vorab auf die Abdeckung ist im Mittel nicht gezeigt; im Test ändert sich auch nur das Vorab der Patienten, nicht das des Modells.
- **Mondrian liegt im Standard im Mittel über zehn Welten in jeder Klasse beim Ziel oder darüber ({' / '.join(f1(RES.pooled(base, 'MONDRIAN', 'cov_b', k)) for k in range(3))} %; in Menge A bei 3–4 und 5+ Merkmalen knapp darunter: {f1(RES.stat(base, 'A', 'MONDRIAN', 'cov_b', 1)[0])} / {f1(RES.stat(base, 'A', 'MONDRIAN', 'cov_b', 2)[0])} %), und die Menge bei wenigen Merkmalen ist größer als in der früheren Rechnung.** Die frühere Rechnung hatte bei 1–2 und 3–4 Merkmalen knapp unter dem Ziel gelegen: {f1(old_mond['cov_b'][0])} % bei 1–2 Merkmalen und eine Menge von {f1(old_mond['size_b'][0])} statt {f1(REP.FRUEHER['base']['size_b'][0])} Krankheiten (das {f1(old_mond0_ratio)}-fache); Messreihe: {f1(RES.pooled(base, 'MONDRIAN', 'cov_b', 0))} % und {f1(RES.pooled(base, 'MONDRIAN', 'size_b', 0))} statt {f1(RES.pooled(base, 'LAC', 'size_b', 0))} (das {f1(mond0_ratio)}-fache).
- **Die Gesamtmenge von LAC ist etwas größer als in der früheren Rechnung** ({f1(REP.FRUEHER['base']['size'])} → {f1(RES.pooled(base, 'LAC', 'size'))} Krankheiten im Standard); die Abdeckung gesamt liegt in der Messreihe knapp über dem Ziel ({f1(RES.pooled(base, 'LAC', 'cov'))} ± {f1(RES.pooled_se(base, 'LAC', 'cov'))} %, Standardfehler über zehn Welten), in der früheren Rechnung knapp darunter ({f1(REP.FRUEHER['base']['cov'])} ± {f1(REP.FRUEHER['base']['cov_se'])} %); beide Abstände liegen unter zwei Standardfehlern.
- **Rechenzeit:** Die Messreihe ({meta['cells'] * 2 * meta['worlds_per_set']} Welten) lief am 2026-11-18 in {meta['seconds']:.0f} s auf der Entwicklungsmaschine (unter Last durch parallele Läufe); eine unabhängige Nachrechnung am selben Tag brauchte rund 9 s, eine Live-Messung der App (5 Welten) unter Last 2 bis 7 s. Die Zeit schwankt stark mit Rechner und Last, ist kein Befund und steht in keinem Test.

## Modell

**Welt.** {C.ND} Krankheiten und {C.NS} Merkmale mit Zipf-verteilter Beliebtheit (Exponent {str(C.POP_EXP).replace('.', ',')}); jede Krankheit hat {C.K_MIN_FEAT} bis {C.K_MAX_FEAT} Profilmerkmale mit Häufigkeit 0,95, 0,6, 0,3 oder 0,1. Ein vorhandenes Merkmal wird mit Wahrscheinlichkeit 1 − q aufgeschrieben (q = {str(C.Q_BASE).replace('.', ',')}), dazu kommt eine Hintergrundrate je Merkmal. Die Welt ist dieselbe wie in `phaenotyp-ranking-demo` (kopierte Module, Kopier-Test).

**Patienten und Modell.** Krankheit gleichverteilt, Merkmale unabhängig gegeben die Krankheit. Patienten ohne jedes dokumentierte Merkmal werden entfernt (Kalibrierung wie Test). Das Modell ist Naive Bayes mit den wahren Häufigkeiten oder mit Häufigkeiten aus gezogenen Fällen (Add-½-Glättung: zu jeder Zählung wird 0,5 addiert); sein Posterior ist die Eingabe aller drei Verfahren.

**Konforme Menge.** Aus {C.NCAL_OPTIONS[1]} Kalibrierpatienten (Standard) mit bekannter Krankheit wird für jeden die Nichtkonformität der wahren Krankheit bestimmt; die Schwelle ist das ⌈(n + 1) · Ziel⌉-te kleinste Ergebnis (exakte Ganzzahlrechnung in ganzen Prozent; ist der Rang größer als n, ist die Schwelle unendlich und die Menge enthält alle Krankheiten). Die Menge eines Patienten enthält alle Krankheiten, deren Ergebnis höchstens die Schwelle ist. **Garantie:** sind Kalibrier- und Testpatient austauschbar, liegt die wahre Krankheit des Testpatienten mit Wahrscheinlichkeit mindestens Ziel in der Menge; bei stetigen Ergebnissen ohne Gleichstände höchstens um 1/(n + 1) darüber. Das gilt für jeden Posterior, auch einen schlechten; ein schlechter Posterior macht die Mengen in dieser Welt groß (3 Fälle je Krankheit: {f1(RES.pooled(kb3, 'LAC', 'size'))} statt {f1(RES.pooled(base, 'LAC', 'size'))} Krankheiten).

**Verschiebungen (im Test, nie in der Kalibrierung).** Vorab: im Test gilt ein Zipf-Vorab statt gleichverteilt, das Modell bleibt bei gleichverteilt. Dokumentation: im Test ist q = {str(C.Q_SHIFT).replace('.', ',')} statt {str(C.Q_BASE).replace('.', ',')}, es fehlen also mehr Merkmale in der Akte. Beides verletzt die Austauschbarkeit.

**Messung.** Je Einstellung {C.N_WORLDS} Welten (SplitMix64: der ganzzahlige Zufallsstrom ist auf jeder Plattform derselbe; die Kennzahlen darüber können sich im letzten Bit unterscheiden, gemessen wurde unter Windows); Kalibrierpatienten und Testpatienten werden getrennt gezogen. Im Standard bleiben von {C.NCAL_OPTIONS[1]} gezogenen Kalibrierpatienten im Mittel {f1(n_cal_base)} und von {de(meta['test_patients_per_world'])} Testpatienten {f1(n_test_base)} (Patienten ohne dokumentiertes Merkmal entfallen). Vollständige Formeln: Expander **📐 Mathematische Formulierung** der App. Alle Parameter sind angenommen.

## Methodik

| Verfahren | Nichtkonformität eines Patienten und einer Krankheit | Grenze |
|---|---|---|
| **LAC** | 1 − Posterior der Krankheit | bei richtigem Posterior die kleinsten Mengen bei gegebener Abdeckung im Mittel (Messreihe: außer bei der dünnen Wissensbasis); die Abdeckung hängt an der Merkmalsklasse |
| **APS** (nicht randomisiert) | Masse aller strikt höher gereihten Krankheiten (Gleichstand nach Index) | die Menge ist ein Anfangsstück der Rangliste; ohne Zufallsrundung ist die Abdeckung bei Gleichständen nicht scharf |
| **Mondrian-LAC** | wie LAC, mit einer eigenen Schwelle je Klasse (1–2, 3–4, 5 und mehr dokumentierte Merkmale) | Abdeckung je Klasse nur für diese Klassen; keine Aussage über andere Gruppen |
| **feste Top-k-Liste** | (Vergleich, kein Versprechen) die k wahrscheinlichsten Krankheiten | die Abdeckung ist ein Ergebnis, kein Versprechen |

**Zählung der Messreihe.** Zellen sind Einstellungen (Ziel, Wissensbasis, Verschiebung, Kalibriermenge); je Zelle zwei Mengen von {meta['worlds_per_set']} Welten. **Standardfehler** = Streuung der Welten (n − 1) durch Wurzel aus der Zahl der Welten. **Verdikte** der App: „hält“, wenn die Abdeckung höchstens {str(C.PARTIAL_TOL).replace('.', ',')} Punkte unter dem Ziel liegt oder der Abstand unter {str(C.SD_FACTOR).replace('.', ',')} Standardfehlern bleibt (gepaart über die Welten); sonst „hält nicht“. Die Toleranz ist gesetzt, nicht abgestimmt; „hält“ heißt „nicht widerlegt“ (bei fünf Welten und großem Standardfehler gilt auch ein größerer Abstand als „hält“). Die App zeigt zwei Verdikte (Gesamtabdeckung und gewählte Klasse); diese Einteilung und die Toleranz sind gesetzt, nicht abgestimmt. Je Preset prüft `kfu_stories.py`, dass die Messreihe zeigt, wofür das Preset steht, in beiden Mengen. **Streuung der Abdeckung einer Kalibrierung** (Kernfrage 4): {de(meta['spread_reps'])} Kalibrierungen werden mit Zurücklegen aus einem Vorrat von {de(meta['spread_pool'][0])} Patienten einer Welt gezogen und die Abdeckung an {de(meta['spread_pool'][1])} anderen Patienten derselben Welt gemessen; die Beta-Verteilung ist die exakte Verteilung für stetige Ergebnisse.

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen: Messreihe `data/kfu_results.json` ({meta['cells']} Zellen, je zwei Mengen von {meta['worlds_per_set']} Welten, Mittel über die {2 * meta['worlds_per_set']} Welten; Standardfehler über dieselben Welten; Einheit: Abdeckung in Prozent der Patienten, Menge in Krankheiten je Patient). Jede Tabelle wird beim Erzeugen der README aus der Datei geschrieben (`tools/make_readme.py`) und von `tests/test_claims.py` auf Gleichheit geprüft. **Zählungen** nennen ihre Bezugsmenge: „{d['n_exch']} Zellen ohne verschobene Dokumentation“ sind alle Zellen, in denen Kalibrier- und Testpatienten austauschbar sind oder nur das Vorab verschoben ist; „in {d['n_exch']} von {d['n_exch']}“ heißt: in beiden Mengen.

**Die sechs Fälle** (LAC, Ziel 90 %, {C.NCAL_OPTIONS[1]} Kalibrierpatienten; Anteil der Patienten in den Klassen 1–2 / 3–4 / 5+ Merkmale im Standard: {' / '.join(f1(s) for s in share)} %):

{case_table(res)}

- **Das Versprechen hält im Mittel.** In {lac['total_hold']} von {d['n_exch']} Zellen ohne verschobene Dokumentation liegt die Gesamtabdeckung von LAC höchstens 2 Punkte unter dem Ziel (APS {aps['total_hold']}, Mondrian {mond['total_hold']}); im Standard {f1(RES.pooled(base, 'LAC', 'cov'))} ± {f1(RES.pooled_se(base, 'LAC', 'cov'))} % bei Ziel 90 %.
- **Es hält nicht für jede Gruppe.** Bei 1–2 dokumentierten Merkmalen liegt die Abdeckung von LAC in {lac['c0_below']} von {d['n_exch']} Zellen unter dem Ziel, in {lac['c0_below5']} um mehr als 5 Punkte; bei 5 und mehr Merkmalen liegt sie in {lac['c2_above']} von {d['n_exch']} Zellen darüber. Im Standard sind es {f1(RES.pooled(base, 'LAC', 'cov_b', 0))} % bei 1–2 und {f1(RES.pooled(base, 'LAC', 'cov_b', 2))} % bei 5 und mehr Merkmalen (Ziel 90 %): Das Versprechen gleicht sich über die Klassen aus.
- **Eine dünne Wissensbasis macht die Menge groß, die Abdeckung hält.** Mit Häufigkeiten aus 3 Fällen je Krankheit liegt die Abdeckung bei {f1(RES.pooled(kb3, 'LAC', 'cov'))} ± {f1(RES.pooled_se(kb3, 'LAC', 'cov'))} %, die mittlere Menge bei {f1(RES.pooled(kb3, 'LAC', 'size'))} statt {f1(RES.pooled(base, 'LAC', 'size'))} Krankheiten (das {f1(ratio_kb3)}-fache); die feste Top-5-Liste deckt {f1(top5(kb3))} statt {f1(top5(base))} % ab. Bei 30 Fällen: {f1(RES.pooled(kb30, 'LAC', 'cov'))} % und {f1(RES.pooled(kb30, 'LAC', 'size'))} Krankheiten.
- **Eine verschobene Dokumentation bricht das Versprechen.** Mit q = 0,6 statt 0,3 im Test sinkt die Abdeckung von LAC auf {f1(RES.pooled(sh2, 'LAC', 'cov'))} ± {f1(RES.pooled_se(sh2, 'LAC', 'cov'))} % (Ziel 90 %); in {lac['sh2_below10']} von {d['n_sh2']} Zellen mit verschobener Dokumentation liegt sie um mehr als 10 Punkte unter dem Ziel (APS {aps['sh2_below10']}, Mondrian {mond['sh2_below10']}). Die Schwelle kommt aus der Kalibrierung und kennt die Verschiebung nicht; die mittlere Menge liegt bei {f1(RES.pooled(sh2, 'LAC', 'size'))} statt {f1(RES.pooled(base, 'LAC', 'size'))} Krankheiten. Mit der dünnen Wissensbasis und verschobener Dokumentation liegt die Abdeckung bei {f1(RES.pooled(kb3sh2, 'LAC', 'cov'))} %.

**Gegenmittel** (Ziel 90 %, Wissensbasis bekannt, {C.NCAL_OPTIONS[1]} Kalibrierpatienten):

{method_table(res)}

**Gesamtabdeckung bei verschobenen Verteilungen im Test** (Ziel 90 %):

{shift_table(res)}

- **APS gleicht die Klassen etwa zur Hälfte aus, Mondrian weitgehend.** Die Spannweite der Abdeckung über die drei Klassen (größte minus kleinste Abweichung vom Ziel, Mittel über die {d['n_exch']} Zellen und beide Mengen) beträgt bei LAC {f1(lac['span'])}, bei APS {f1(aps['span'])} und bei Mondrian {f1(mond['span'])} Punkte (bei Mondrian in der Zelle mit 100 Kalibrierpatienten {f1(d['mond_span_n100'])}). Bei 1–2 Merkmalen liegt Mondrian in {mond['c0_below']} von {d['n_exch']} Zellen in beiden Mengen unter dem Ziel (LAC {lac['c0_below']}, APS {aps['c0_below']}); in einzelnen Mengen liegt er in {d['mond_c0_sets_below']} von {d['mond_c0_sets_total']} Fällen darunter (um höchstens {f1(-d['mond_c0_min_gap'])} Punkte). Alle drei Klassen liegen bei Mondrian in {mond['within3']} von {d['n_exch']} Zellen höchstens 3 Punkte neben dem Ziel (Ausnahme: {', '.join(cell_name(k) for k in d['mond_exception_within3'])}).
- **Mondrian verschiebt die Fehlabdeckung in größere Mengen.** Bei 1–2 Merkmalen ist die Menge von Mondrian in {d['mond_c0_bigger15']} von {d['n_exch']} Zellen mehr als das 1,5-fache der Menge von LAC (in {d['mond_c0_bigger']} von {d['n_exch']} größer); gesamt ist sie in {d['mond_total_bigger']} von {d['n_exch']} Zellen größer (Ausnahme: {', '.join(cell_name(k) for k in d['mond_exception_total'])}); bei 5 und mehr Merkmalen ist sie in {d['mond_c2_smaller']} von {d['n_exch']} Zellen kleiner. APS hat gesamt in {d['aps_total_bigger']} von {d['n_exch']} Zellen eine größere Menge als LAC. **LAC hat die kleinsten Mengen, wenn der Posterior stimmt:** in {d['lac_smaller']} von {d['n_exch']} Zellen ist die Gesamtmenge von LAC kleiner als die von APS und die von Mondrian (Ausnahme: {', '.join(cell_name(k) for k in d['lac_smaller_exc'])}, dort mit schlechtem Posterior).
- **Bei verschobener Dokumentation bricht auch Mondrian** (Abdeckung {f1(RES.pooled(sh2, 'MONDRIAN', 'cov'))} % bei Ziel 90 %): Die Klassen nach Merkmalszahl sichern die Austauschbarkeit nur innerhalb jeder Klasse, und die ist durch die Verschiebung verletzt (Deutung: bei q 0,6 hat ein Patient mit wenigen dokumentierten Merkmalen mehr vorhandene, aber nicht aufgeschriebene Merkmale als bei q 0,3; nicht getrennt gemessen).

**Menge gegen Ziel-Abdeckung** (Wissensbasis bekannt, {C.NCAL_OPTIONS[1]} Kalibrierpatienten):

{target_table(res)}

- Von Ziel 80 % auf 95 % wächst die mittlere Menge von LAC auf das {f1(ratio_target)}-fache ({f1(RES.pooled(t80, 'LAC', 'size'))} → {f1(RES.pooled(t95, 'LAC', 'size'))} Krankheiten). Eine feste Top-5-Liste deckt im Standard {f1(top5(base))} % ab; die Menge für Ziel 90 % hat im Mittel {f1(RES.pooled(base, 'LAC', 'size'))} Krankheiten (das ist ein Ergebnis dieser Welt, keine Regel).

**Streuung der Abdeckung gegen die Kalibriermenge** (Ziel 90 %, Wissensbasis bekannt; Streuung der Welten: Standardabweichung der Gesamtabdeckung über die {meta['worlds_per_set']} Welten einer Menge; aus nur zehn Welten, die beiden Mengen weichen voneinander ab, die Ordnung stimmt mit der Beta-Verteilung unten überein):

{ncal_table(res)}

**Abdeckung einer einzelnen Kalibrierung, Simulation gegen Beta-Verteilung** ({de(meta['spread_reps'])} Kalibrierungen je Zeile):

{spread_table(res)}

- Die Abdeckung einer einzelnen Kalibrierung streut bei 100 Kalibrierpatienten mit {f2(100 * sp[(100, 90)]['sd'])} Punkten (Beta-Verteilung {f2(100 * sp[(100, 90)]['beta_sd'])}), bei 500 mit {f2(100 * sp[(500, 90)]['sd'])} ({f2(100 * sp[(500, 90)]['beta_sd'])}) und bei 2000 mit {f2(100 * sp[(2000, 90)]['sd'])} ({f2(100 * sp[(2000, 90)]['beta_sd'])}). Bei 100 Kalibrierpatienten lag die Abdeckung in 5 % der Kalibrierungen unter {f1(100 * sp[(100, 90)]['q05'])} % und im ungünstigsten von {de(meta['spread_reps'])} Fällen bei {f1(100 * sp[(100, 90)]['min'])} %. Das Versprechen gilt im Mittel über die Kalibrierungen; eine einzelne Kalibrierung kann darunter liegen.
- Die Simulation stimmt mit der Beta-Verteilung überein: die Streuungen weichen um höchstens {f3(max(abs(r['sd'] - r['beta_sd']) for r in res['spread']) * 100)} Punkte ab. Das Mittel der Simulation weicht um {sgn2(min(r['mean'] - r['beta_mean'] for r in res['spread']) * 100)} bis {sgn2(max(r['mean'] - r['beta_mean'] for r in res['spread']) * 100)} Punkte vom Mittel der Beta-Verteilung ab; der Standardfehler eines Anteils von 90 % bei {de(meta['spread_pool'][1])} Patienten beträgt {f2(d['pool_se'])} Punkte (Deutung: Der Unterschied liegt in der Größenordnung des Stichprobenfehlers der beiden Hälften des Vorrats; nicht getrennt gemessen).

## Ehrliche Grenzen

- **Die Messreihe gilt für diese Welt:** {C.ND} Krankheiten, {C.NS} Merkmale, Naive-Bayes-Struktur, die gemessenen Reglerstufen; die Abbildungen der Kernfragen stammen aus den gemessenen Zellen, die Messung oben auf der Seite rechnet jede Kombination der Regler live (fünf Welten).
- **Das Versprechen ist eine Aussage im Mittel über Patienten und über die Ziehung der Kalibriermenge**, unter Austauschbarkeit von Kalibrier- und Testpatienten. Es sagt nichts über einen einzelnen Patienten und über Gruppen außer den drei Klassen nach Merkmalszahl, die Mondrian ausdrücklich bedient; andere Gruppen (Alter, Herkunft, Klinik) sind nicht gemessen.
- **Nur drei Verfahren:** gemessen sind LAC, APS (ohne Zufallsrundung) und Mondrian-LAC; Aussagen über andere Verfahren (verlustorientierte Mengen, Rückwärts-Konformal, adaptive Verfahren) sind keine Messung.
- **Fünf Welten je Menge und Messung:** Unterschiede unter der Toleranz oder unter zwei Standardfehlern werden nicht gedeutet; die Toleranz der Verdikte ist gesetzt, nicht abgestimmt.
- **Die Garantie braucht die wahre Krankheit der Kalibrierpatienten** und Austauschbarkeit; echte Diagnosen sind unsicher und verspätet, echte Verteilungen verschieben sich.
- **Die Merkmale sind in dieser Welt unabhängig gegeben die Krankheit gezogen;** bei abhängigen Merkmalen wäre Naive Bayes ein schlechteres Modell (nicht gemessen). Das Versprechen hängt nicht vom Modell ab, die Größe der Menge schon (Wissensbasis aus 3 Fällen: Abdeckung hält, Menge das {f1(ratio_kb3)}-fache).
- **Nur an erfundenen Welten geprüft;** keine echten Patientendaten, keine echte Wissensbasis (HPO, Orphanet), keine Ontologie, keine medizinische Beratung.

## Verwandte Demos mit demselben mathematischen Modell

- [`phaenotyp-ranking-demo`](https://github.com/sebastian-hanisch/phaenotyp-ranking-demo): dieselbe Welt und derselbe Posterior von Naive Bayes; dort die **Rangliste** und ihr Recall@5 gegen das Orakel, hier die **Menge** mit Abdeckungsversprechen. Kopierte Module (`kfu_rng.py`, `kfu_stream.py`, `kfu_world.py`, `kfu_rankers.py`, `kfu_metrics.py`).
- [`forecast-interval-demo`](https://github.com/sebastian-hanisch/forecast-interval-demo): konforme Kalibrierung an den Fehlern einer Zeitreihen-Prognose (Nennabdeckung im Mittel, je Wochentag, im Zeitverlauf); gleiche Schwelle aus einer Kalibriermenge, dort für ein **Intervall** einer Zahl, hier für eine **Menge von Klassen**.
- [`entscheidungs-schranke-demo`](https://github.com/sebastian-hanisch/entscheidungs-schranke-demo): eine konforme Schranke auf die Kosten einer gewählten Entscheidung; gleiches Prinzip der Schwelle aus Kalibrierfehlern, dort mit der Entscheidung als Gegenstand.
- [`kalibrierung-schwelle-demo`](https://github.com/sebastian-hanisch/kalibrierung-schwelle-demo): aus einer Wahrscheinlichkeit eine Entscheidung; dort muss die Wahrscheinlichkeit als Häufigkeit stimmen, hier nicht: auch mit einer Wissensbasis aus 3 Fällen hält die Abdeckung im Mittel (Befunde), nur die Menge wird größer.
- Nachbar, im Bau: `grobe-merkmale-demo` (gleiche Welt, Merkmale nur als Oberbegriff dokumentiert).

## Verifikation ({n_tests} Tests)

- **Mini-Instanz** (`tests/test_mini_enumeration.py`): 3 Krankheiten, 3 Merkmale, 8 Muster; alle 13.824 geordneten Kalibriertripel der Größe 3 und alle Testpatienten werden aufgezählt; die exakte Abdeckung liegt bei LAC und APS mindestens bei ⌈(n + 1) · Ziel⌉ / (n + 1), bei Mondrian je Klasse mindestens beim Ziel; die Schwelle stimmt mit einem unabhängigen Rechenweg (Einfügesortierung, Ganzzahlrechnung) überein, die Mengen gehen in die exakte Abdeckung ein. Die obere Schranke gilt bei APS wegen der Gleichstände nicht, das ist ein Test.
- **Einheiten gegen Handrechnung** (`tests/test_conformal.py`): Schwelle (auch unendlich), Klassen, Nichtkonformität LAC und APS, Mondrian-Schwellen, Mengen, Auswertung.
- **Orakel** (`tests/test_oracle_konforme_ursachen.py`): (a) Schwelle gegen Einfügesortierung; (b) Eigenschaftstest der Garantie über 20 Welten je Einstellung, auch mit dünner Wissensbasis (3 Fälle), mit einer Negativkontrolle bei verschobener Dokumentation; (c) Beta-Verteilung gegen scipy, gegen eine Simulation mit gleichverteilten Ergebnissen und gegen die Simulation der Demo; (d) Mondrian-Abdeckung je Klasse (und die Verfehlung bei LAC als Negativkontrolle); (e) Monotonie der Menge im Ziel.
- **Zweige und Live** (`tests/test_live.py`): jede Stufe jedes Messreglers ändert mindestens ein Verfahren; die drei Verfahren weichen voneinander ab; die Verschiebungen ändern die Abdeckung; die Wissensbasis ändert die Mengengröße.
- **Messreihe** (`tests/test_results.py`): Aufbau, innere Stimmigkeit (Zusammenfassung gleich Mittel der Welten), Reproduktion der Voreinstellung (Menge A) mit Toleranz, Beta-Zeilen gegen die Formel.
- **Presets und Verdikte:** Abnahmekriterium je Preset gegen die Messreihe und jedes Kriterium an seiner Schwelle mit künstlichen Werten (`tests/test_stories.py`); jedes Verdikt in beiden Zweigen (`tests/test_evaluation.py`).
- **Oberfläche:** AppTest (jeder Preset-Button, jede Stufe jedes Reglers am Minimum und Maximum, Kombinationen, Permalink mit Einrasten und Begrenzen, Beispielpatient, PDF), Layout (Schnellstart, fester Kopf, aktives Preset hervorgehoben; jede Regleränderung hebt die Markierung auf), Footer, Laufzeit-Importe.
- **Kopierte Module:** `tests/test_stream.py`, `tests/test_world.py` und `tests/test_metrics.py` prüfen Zufallsstrom, Welt und Kennzahlen. Zwei Tests vergleichen die Kopien mit Dateien außerhalb dieses Repos (der Vorlage des Zufallsgenerators, byte-gleich, und den Modulen von `phaenotyp-ranking-demo`, bis auf das Präfix gleich) und überspringen sich, wenn diese Dateien fehlen; in der CI laufen sie deshalb nicht.
- **README:** wird aus `data/kfu_results.json` erzeugt; `tests/test_claims.py` prüft, dass sie dem Erzeugnis entspricht, die Testzahl stimmt und jede Zählung der Befunde der Messreihe entspricht. Zahl zu Test:

| Aussage der README | Test in `tests/test_claims.py` |
|---|---|
| Gesamtabdeckung hält in {lac['total_hold']} von {d['n_exch']} Zellen (LAC, APS, Mondrian) | `test_gesamtabdeckung_haelt_in_allen_zellen_ohne_verschobene_dokumentation` |
| LAC bei 1–2 Merkmalen unter dem Ziel in {lac['c0_below']}, um mehr als 5 Punkte in {lac['c0_below5']}; bei 5 und mehr darüber in {lac['c2_above']} | `test_lac_klasse_1_2_unter_dem_ziel_und_klasse_5_darueber` |
| APS: Spannweite {f1(aps['span'])}; Mondrian: Spannweite {f1(mond['span'])}, {mond['within3']} Zellen höchstens 3 Punkte neben dem Ziel | `test_gegenmittel_je_klasse` |
| Mondrian: Menge {d['mond_c0_bigger15']} / {d['mond_total_bigger']} / {d['mond_c2_smaller']} von {d['n_exch']} | `test_mondrian_preis_in_der_menge` |
| dünne Wissensbasis: Abdeckung hält, Menge das {f1(ratio_kb3)}-fache | `test_duenne_wissensbasis` |
| verschobene Dokumentation: Abdeckung mehr als 10 Punkte unter dem Ziel in {lac['sh2_below10']} von {d['n_sh2']} Zellen | `test_verschobene_dokumentation_bricht_das_versprechen` |
| verschobenes Vorab: kein Unterschied über zwei Standardfehlern | `test_verschobenes_vorab_ohne_nachweis` |
| Menge wächst von Ziel 80 % auf 95 % auf das {f1(ratio_target)}-fache | `test_menge_waechst_mit_dem_ziel` |
| Streuung der Abdeckung nimmt mit der Kalibriermenge ab; Simulation gleich Beta-Verteilung | `test_streuung_der_abdeckung` |

- Keine Mutationstests (seit 2026-10-28 nicht mehr Teil der Demo-Prüfung). Nicht in der CI läuft die Messreihe selbst (`tools/sweep.py`; gespeicherte Laufzeit {meta['seconds']:.0f} s, siehe Rechenzeit oben).

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore`, `.streamlit/config.toml` | Git-Ausnahmen, Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App (Seitenaufbau nach DEMO-PLAYBOOK §2) |
| `kfu_constants.py` | Reglerstufen, feste Annahmen, Presets |
| `kfu_rng.py` | SplitMix64 (`decimal`-Ersatz für Logarithmus und Kosinus), wörtliche Kopie der Vorlage |
| `kfu_stream.py`, `kfu_world.py`, `kfu_rankers.py`, `kfu_metrics.py` | Zufallsstrom, Welt und Patienten, Naive Bayes, Recall (Kopien aus `phaenotyp-ranking-demo`) |
| `kfu_conformal.py` | Schwelle, LAC, APS, Mondrian-LAC, Mengen, Abdeckung und Größe |
| `kfu_garantie.py` | Streuung der Abdeckung gegen die Kalibriermenge, Beta-Verteilung |
| `kfu_live.py` | Live-Messung (fünf Welten), Verschiebungen, Zusammenfassung |
| `kfu_results.py` | Messreihe laden, Zellen, gepoolte Kennzahlen |
| `kfu_evaluation.py` | Verdikte und Kernfragen als reine Funktionen, Beispielpatient |
| `kfu_stories.py` | Abnahmekriterien der Presets |
| `kfu_presets.py`, `kfu_layout.py` | Permalink, Presets, fester Kopf |
| `kfu_visualization.py`, `kfu_ui_panel.py`, `kfu_pdf_export.py` | Abbildungen, Tabellen und Textbausteine, PDF-Auswertung |
| `data/kfu_results.json` | vorgerechnete Messreihe ({meta['cells']} Zellen) |
| `tools/sweep.py`, `tools/report.py`, `tools/make_readme.py` | Messreihe reproduzieren, berichten (mit den Zahlen der früheren Rechnung), README erzeugen |
| `requirements.txt`, `requirements-dev.txt` | Laufzeit-Bibliotheken, plus pytest und scipy |
| `tests/` | siehe Verifikation |

## Bewusst nicht enthalten

- **Verlustorientierte Mengen, gruppenbedingte Garantien über Mondrian hinaus, Zufallsrundung beim APS, Rückwärts-Konformal, verzögerte oder zensierte Daten:** gemessen sind nur LAC, APS (nicht randomisiert) und Mondrian-LAC.
- **Andere Gruppen als die Klassen nach Merkmalszahl** (Alter, Herkunft, Klinik): die Welt hat sie nicht.
- **Echte Daten, echte Wissensbasis, Ontologie:** erfundene Welt.
- **Eine Empfehlung oder Diagnose:** Lehrmodell, keine medizinische Beratung.

## Lokal ausführen

```bash
python -m venv venv
venv\\Scripts\\activate           # Linux/macOS: source venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly, NumPy und fpdf2 (scipy nur als Gegenprobe im Test).

---

{FOOTER}
"""


def main():
    res = json.loads((ROOT / "data" / "kfu_results.json").read_text(encoding="utf-8"))
    text = render(res, count_tests())
    target = ROOT / "README.md"
    if "--check" in sys.argv:
        ok = target.read_text(encoding="utf-8").replace("\r\n", "\n") == text
        print("README stimmt" if ok else "README weicht ab")
        sys.exit(0 if ok else 1)
    target.write_text(text, encoding="utf-8", newline="\n")
    print("README.md geschrieben")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
