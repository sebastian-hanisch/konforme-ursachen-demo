"""Bericht über die Messreihe: die Zahlen einer früheren Rechnung (NumPy-Generator, fünf Welten, Standardfehler) und die Messreihe nebeneinander.

    python tools/report.py

Die frühere Rechnung ist nicht nachprüfbar (anderer Zufallsgenerator, keine Datei im Repo); ihre Zahlen stehen hier als Konstanten. make_readme.py nutzt sie für die Tabellen
in „Befunde und Korrekturen gegenüber einer früheren Rechnung“."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")

import kfu_live as L  # noqa: E402
import kfu_results as RES  # noqa: E402

# Frühere Rechnung: (Gesamtabdeckung, mittlere Menge, Abdeckung bei 1–2, 3–4, 5+ Merkmalen); Ziel 90 %, 500 Kalibrierpatienten, fünf Welten, Mittel (± Standardfehler der Gesamtabdeckung).
FRUEHER = {
    "base": {"cov": 89.4, "cov_se": 0.6, "size": 13.2, "cov_b": (79.8, 90.2, 96.0), "size_b": (22.8, 12.5, 6.3), "top5": 75.9},
    "kb3": {"cov": 90.7, "cov_se": 0.9, "size": 82.5, "cov_b": (85.7, 90.8, 94.4), "size_b": (94.3, 84.5, 70.2), "top5": 44.5},
    "kb30": {"cov": 90.1, "cov_se": 0.5, "size": 22.4, "cov_b": (82.8, 90.2, 95.8), "size_b": (37.4, 21.8, 11.0), "top5": 70.9},
    "sh1": {"cov": 88.6, "cov_se": 1.0, "size": 13.4, "cov_b": (79.5, 89.0, 95.7), "size_b": (22.5, 12.9, 6.3), "top5": 75.2},
    "sh2": {"cov": 70.0, "cov_se": 1.1, "size": 19.0, "cov_b": (60.9, 74.8, 84.9), "size_b": (24.8, 15.6, 9.9), "top5": 48.7},
    "kb3sh2": {"cov": 77.4, "cov_se": 1.8, "size": 89.2, "cov_b": (73.3, 79.4, 84.7), "size_b": (95.3, 87.0, 76.2), "top5": 22.8},
}
FRUEHER_GEGENMITTEL = {
    "APS": {"cov": 90.1, "size": 17.3, "cov_b": (87.4, 89.1, 93.5), "size_b": (40.0, 13.0, 4.4)},
    "MONDRIAN": {"cov": 89.8, "size": 17.4, "cov_b": (88.7, 89.5, 91.0), "size_b": (44.5, 11.7, 2.6)},
}
FALL_SETTINGS = {
    "base": L.Settings(), "kb3": L.Settings(kb=3), "kb30": L.Settings(kb=30), "sh1": L.Settings(shift=1), "sh2": L.Settings(shift=2), "kb3sh2": L.Settings(kb=3, shift=2),
}


def main():
    meta = RES.meta()
    print(f"Messreihe: {meta['cells']} Zellen, {meta['worlds_per_set']} Welten je Menge, Rechenzeit {meta['seconds']} s")
    for fall, s in FALL_SETTINGS.items():
        c, old = RES.cell(s), FRUEHER[fall]
        print(f"\n{fall}: frühere Rechnung -> Messreihe (zehn Welten)")
        print(f"  Abdeckung LAC {old['cov']} -> {RES.pooled(c, 'LAC', 'cov'):.1f} (SE {RES.pooled_se(c, 'LAC', 'cov'):.2f})")
        print(f"  Menge LAC {old['size']} -> {RES.pooled(c, 'LAC', 'size'):.1f}")
        print(f"  Abdeckung 1-2/3-4/5+ {old['cov_b']} -> {[round(RES.pooled(c, 'LAC', 'cov_b', k), 1) for k in range(3)]}")
        print(f"  Menge 1-2/3-4/5+ {old['size_b']} -> {[round(RES.pooled(c, 'LAC', 'size_b', k), 1) for k in range(3)]}")
    base = RES.cell(RES.BASE)
    for m, old in FRUEHER_GEGENMITTEL.items():
        print(f"\n{m}: {old} -> cov {RES.pooled(base, m, 'cov'):.1f}, size {RES.pooled(base, m, 'size'):.1f}, "
              f"cov_b {[round(RES.pooled(base, m, 'cov_b', k), 1) for k in range(3)]}, size_b {[round(RES.pooled(base, m, 'size_b', k), 1) for k in range(3)]}")
    print("\nStreuung der Abdeckung:")
    for r in RES.load()["spread"]:
        print(f"  n {r['n_cal']} Ziel {r['target']}: Simulation sd {100 * r['sd']:.2f} Beta {100 * r['beta_sd']:.2f} Mittel {100 * r['mean']:.2f} / {100 * r['beta_mean']:.2f} min {100 * r['min']:.1f}")


if __name__ == "__main__":
    main()
