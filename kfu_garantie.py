"""Streuung der Abdeckung gegen die Kalibriermenge: Beta-Verteilung (exakt) gegen Simulation.

Wird die Schwelle aus n Kalibrierpatienten bestimmt, ist die Abdeckung für diese eine Kalibrierung (bedingt auf sie) eine Zufallszahl: bei stetigen Ergebnissen und
Austauschbarkeit ist sie Beta(n + 1 − l, l)-verteilt mit l = ⌊(n + 1)(1 − Ziel)⌋. Ihr Mittel ist (n + 1 − l) / (n + 1) und liegt bei Ziel · 100 Prozent bis auf die Rundung
von l; die Streuung wächst, wenn die Kalibriermenge klein ist. Die Simulation zieht die Kalibrierpatienten mit Zurücklegen aus einem Vorrat (Hälfte A) und misst die
Abdeckung an der anderen Hälfte B, beide aus derselben Welt; Mittel und Streuung hängen darum auch an der Endlichkeit von A und B (siehe README)."""

import math

import numpy as np

import kfu_conformal as K
import kfu_constants as C
import kfu_rankers as R
import kfu_world as W
from kfu_stream import Stream, derive


def beta_params(n: int, target: int) -> tuple:
    """(a, b) = (n + 1 − l, l) mit l = ⌊(n + 1)(100 − Ziel) / 100⌋ in exakter Ganzzahlrechnung (Ziel in ganzen Prozent)."""
    el = ((n + 1) * (100 - target)) // 100
    return n + 1 - el, el


def beta_mean_sd(n: int, target: int) -> tuple:
    """Mittel und Standardabweichung der Beta-Verteilung der Abdeckung (Anteil, nicht Prozent)."""
    a, b = beta_params(n, target)
    return a / (a + b), math.sqrt(a * b / ((a + b) ** 2 * (a + b + 1.0)))


def true_score_pool(seed: int):
    """LAC-Ergebnisse der wahren Krankheit für zwei Hälften je SPREAD_POOL Patienten einer Welt mit bekannter Wissensbasis (Vorrat A und Testhälfte B)."""
    wseed = derive(seed, 41)
    world = W.make_world(wseed, C.ND, C.Q_BASE, 0)
    pat = W.sample_patients(world, derive(wseed, 42), 2 * C.SPREAD_POOL)
    P = R.posterior(R.score_naive_bayes(pat.x, world.g, world.prior))
    s = K.true_scores(K.lac_scores_all(P), pat.d)
    half = len(s) // 2
    return s[:half], s[half:]


def spread(seed: int, n_cal: int, target: int, reps: int = C.SPREAD_REPS, pool=None) -> dict:
    """Abdeckung (Anteil) von `reps` Kalibrierungen der Größe n_cal: Mittel, Streuung, 5-%-Quantil und kleinster Wert, daneben Mittel und Streuung der Beta-Verteilung."""
    a_pool, b_pool = pool if pool is not None else true_score_pool(seed)
    st = Stream(derive(seed, 43 + n_cal))
    idx = np.minimum((st.uniform((reps, n_cal)) * len(a_pool)).astype(int), len(a_pool) - 1)
    cal = np.sort(a_pool[idx], axis=1)
    k = ((n_cal + 1) * target + 99) // 100
    q = cal[:, k - 1]
    cov = (b_pool[None, :] <= q[:, None]).mean(axis=1)
    mean_t, sd_t = beta_mean_sd(n_cal, target)
    return {"n_cal": n_cal, "target": target, "reps": reps, "mean": float(cov.mean()), "sd": float(cov.std(ddof=1)), "q05": float(np.quantile(cov, 0.05)),
            "min": float(cov.min()), "beta_mean": mean_t, "beta_sd": sd_t}
