"""Reproduziert data/kfu_results.json: Messreihe über alle Zellen (zwei Mengen von je fünf Welten) und die Streuung der Abdeckung gegen die Kalibriermenge.

Aufruf (im Demo-Ordner): python tools/sweep.py [--check]   (nicht in der CI; 10 bis 80 Sekunden je nach Rechner und Last)
Mit --check wird nichts geschrieben, sondern die Datei gegen eine Neurechnung der Voreinstellung verglichen."""

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")

import kfu_constants as C  # noqa: E402
import kfu_garantie as G  # noqa: E402
import kfu_live as L  # noqa: E402
import kfu_results as RES  # noqa: E402

SPREAD_SEED = 51
SPREAD_CELLS = ((100, 90), (500, 90), (2000, 90), (500, 80), (500, 95))   # (Kalibrierpatienten, Ziel in Prozent)


def _run_dict(r: L.WorldRun) -> dict:
    return {"methods": {m: {k: (v if not isinstance(v, float) else round(v, 6)) for k, v in vals.items()} for m, vals in r.methods.items()},
            "top1": round(r.top1, 6), "top5": round(r.top5, 6), "n_cal": r.n_cal, "n_test": r.n_test}


def cell_result(s: L.Settings) -> dict:
    m = L.measure(s, n_example=0)
    summ = L.summarize(m)

    def lst(v):
        return [list(x) for x in v] if isinstance(v, list) else list(v)

    summary = {meth: {k: lst(v) for k, v in vals.items()} for meth, vals in summ.items() if meth != "fixed"}
    summary["fixed"] = {k: list(v) for k, v in summ["fixed"].items()}
    return {"worlds": [_run_dict(r) for r in m.runs], "summary": summary}


def main(check: bool = False):
    t0 = time.perf_counter()
    cells = {}
    for s in RES.sweep_settings():
        row = {"settings": {"target": s.target, "kb": s.kb, "shift": s.shift, "ncal": s.ncal}}
        for name, seed in C.SWEEP_SEEDS.items():
            row[name] = cell_result(L.Settings(target=s.target, kb=s.kb, shift=s.shift, ncal=s.ncal, seed=seed))
        cells[s.key()] = row
        a = row["A"]["summary"]["LAC"]["cov"][0]
        b = row["B"]["summary"]["LAC"]["cov"][0]
        print(f"{s.key():<26} LAC Abdeckung A {a:5.1f} B {b:5.1f}", flush=True)
    pool = G.true_score_pool(SPREAD_SEED)
    spread = [G.spread(SPREAD_SEED, n, t, pool=pool) for n, t in SPREAD_CELLS]
    data = {"meta": {"worlds_per_set": C.N_WORLDS, "test_patients_per_world": C.N_TEST, "sets": C.SWEEP_SEEDS, "cells": len(cells), "methods": list(C.METHODS),
                     "nd": C.ND, "q_base": C.Q_BASE, "q_shift": C.Q_SHIFT, "spread_seed": SPREAD_SEED, "spread_reps": C.SPREAD_REPS,
                     "spread_pool": [len(pool[0]), len(pool[1])], "seconds": round(time.perf_counter() - t0, 1)},
            "cells": cells, "spread": spread}
    if check:
        old = json.loads(RES.DATA.read_text(encoding="utf-8"))
        a_old = old["cells"][L.Settings().key()]["A"]["summary"]["LAC"]["cov"][0]
        a_new = cells[L.Settings().key()]["A"]["summary"]["LAC"]["cov"][0]
        print("Prüfung Voreinstellung Menge A, LAC-Abdeckung:", a_old, a_new, "gleich" if abs(a_old - a_new) < 1e-6 else "ABWEICHUNG")
        return
    RES.DATA.parent.mkdir(exist_ok=True)
    RES.DATA.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"geschrieben: {RES.DATA} ({len(cells)} Zellen, {data['meta']['seconds']} s)")


if __name__ == "__main__":
    main("--check" in sys.argv)
