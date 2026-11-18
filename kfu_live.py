"""Live-Messung: fünf Welten für eine Einstellung (Kalibriermenge und Testmenge je Welt), Auswertung über die Welten, Beispielpatienten.

`measure` ist deterministisch (Zufalls-Seed der Einstellung, SplitMix64) und hängt nicht von st.session_state ab. Das Modell (Naive Bayes mit Add-½-Glättung oder mit den
wahren Häufigkeiten, Vorab gleichverteilt) liefert den Posterior; die Kalibrierpatienten kommen aus der Welt, die Testpatienten aus der Welt oder, bei einer Verschiebung,
aus einer Welt mit anderem Vorab beziehungsweise anderem Dokumentationsverlust. Die Verschiebung wirkt nur im Test, nicht in der Kalibrierung."""

from dataclasses import dataclass, field, replace

import numpy as np

import kfu_conformal as K
import kfu_constants as C
import kfu_metrics as M
import kfu_rankers as R
import kfu_world as W
from kfu_stream import Stream, derive


@dataclass(frozen=True, kw_only=True)
class Settings:
    """Einstellung einer Messung. Nur mit Schlüsselwörtern erzeugen (ein eingefügtes Feld darf keine Werte still verschieben)."""

    target: int = C.DEFAULT["target"]
    kb: int = C.DEFAULT["kb"]
    shift: int = C.DEFAULT["shift"]
    ncal: int = C.DEFAULT["ncal"]
    seed: int = C.DEFAULT["seed"]

    def key(self) -> str:
        """Schlüssel der Zelle in data/kfu_results.json (ohne den Zufalls-Seed)."""
        return f"t{self.target}_kb{self.kb}_sh{self.shift}_n{self.ncal}"


@dataclass(frozen=True, eq=False)
class WorldRun:
    methods: dict            # Verfahren -> Kennzahlen (cov, size, cov_b, size_b, share_b) und "thresholds"
    top1: float              # feste Top-1-Liste: Anteil der Patienten in Prozent
    top5: float
    n_cal: int               # tatsächliche Zahl der Kalibrierpatienten (Patienten ohne dokumentiertes Merkmal sind entfernt)
    n_test: int
    example: dict = field(default_factory=dict)


@dataclass(frozen=True, eq=False)
class Measurement:
    settings: Settings
    runs: tuple


def shifted_world(world: W.World, shift: int, seed: int) -> W.World:
    """Testwelt: 0 unverändert, 1 anderes Vorab (Zipf statt gleichverteilt), 2 mehr Dokumentationsverlust (q 0,6 statt 0,3). Die Wissensbasis des Modells bleibt die der Kalibrierung."""
    if shift == 1:
        return replace(world, prior=W.vorab(Stream(derive(seed, 23)), world.nd, 1))
    if shift == 2:
        return replace(world, q=C.Q_SHIFT, g=W.dokumentiert(world.f, world.b, C.Q_SHIFT))
    return world


def run_world(s: Settings, i: int, n_example: int = 0) -> WorldRun:
    wseed = derive(s.seed, 10 + i)
    world = W.make_world(wseed, C.ND, C.Q_BASE, 0)
    ghat = W.knowledge_bases(world, wseed, s.kb)["lap"]
    cal = W.sample_patients(world, derive(wseed, 21), s.ncal)
    test = W.sample_patients(shifted_world(world, s.shift, wseed), derive(wseed, 22), C.N_TEST)

    def posterior(x):
        return R.posterior(R.score_naive_bayes(x, ghat, world.prior))

    p_cal, p_test = posterior(cal.x), posterior(test.x)
    k_cal, k_test = cal.x.sum(axis=1), test.x.sum(axis=1)
    methods, sets_by = {}, {}
    for method in C.METHODS:
        th = K.calibrate(method, p_cal, cal.d, k_cal, s.target)
        sets = K.predict_sets(method, p_test, th, k_test)
        methods[method] = {**K.evaluate(sets, test.d, k_test), "thresholds": np.atleast_1d(th).tolist()}
        sets_by[method] = sets
    example = {}
    if n_example:
        n = min(n_example, len(test.d))
        example = {"d": test.d[:n], "kobs": k_test[:n], "p": p_test[:n], "sets": {m: sets_by[m][:n] for m in C.METHODS}}
    return WorldRun(methods, K.fixed_top(p_test, test.d, 1), K.fixed_top(p_test, test.d, 5), len(cal.d), len(test.d), example)


def measure(s: Settings, n_worlds: int = C.N_WORLDS, n_example: int = C.N_EXAMPLE) -> Measurement:
    return Measurement(s, tuple(run_world(s, i, n_example if i == 0 else 0) for i in range(n_worlds)))


def _mean_sd(values) -> tuple:
    return M.mean_sd(values)


def summarize(m: Measurement) -> dict:
    """Verfahren -> Kennzahlen -> (Mittel, Streuung über die Welten): cov und size gesamt, cov_b / size_b / share_b je Klasse (Listen aus drei Paaren), dazu "fixed" mit top1 und top5."""
    out = {}
    for method in C.METHODS:
        runs = [r.methods[method] for r in m.runs]
        out[method] = {"cov": _mean_sd([r["cov"] for r in runs]), "size": _mean_sd([r["size"] for r in runs]),
                       "cov_b": [_mean_sd([r["cov_b"][c] for r in runs]) for c in range(3)],
                       "size_b": [_mean_sd([r["size_b"][c] for r in runs]) for c in range(3)],
                       "share_b": [_mean_sd([r["share_b"][c] for r in runs]) for c in range(3)]}
    out["fixed"] = {"top1": _mean_sd([r.top1 for r in m.runs]), "top5": _mean_sd([r.top5 for r in m.runs])}
    return out


def below_target(m: Measurement, method: str, which, target: int) -> tuple:
    """Gepaart über die Welten: Abdeckung minus Ziel in Prozentpunkten (which = "all" oder Klasse 0, 1, 2): Mittel und Standardfehler (Streuung / Wurzel der Weltenzahl)."""
    vals = [(r.methods[method]["cov"] if which == "all" else r.methods[method]["cov_b"][which]) - target for r in m.runs]
    mean, sd = _mean_sd(vals)
    return mean, sd / float(len(vals)) ** 0.5


def n_effective(m: Measurement) -> tuple:
    """Mittlere tatsächliche Zahl der Kalibrier- und der Testpatienten je Welt."""
    return float(np.mean([r.n_cal for r in m.runs])), float(np.mean([r.n_test for r in m.runs]))
