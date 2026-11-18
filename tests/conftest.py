"""Gemeinsame Fixtures: die Mini-Welt, an der jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b)."""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Mini-Welt: 3 Krankheiten, 3 Merkmale, 8 Muster. g[d][s] = Wahrscheinlichkeit, dass Merkmal s bei Krankheit d dokumentiert wird.
MINI_G = np.array([[0.90, 0.80, 0.10],
                   [0.10, 0.60, 0.70],
                   [0.05, 0.10, 0.90]])
MINI_PRIOR = np.array([0.5, 0.3, 0.2])


def mini_muster() -> np.ndarray:
    """Alle 8 Muster dokumentierter Merkmale (Zeilen), geordnet nach der Binärzahl."""
    return np.array([[(i >> s) & 1 for s in range(3)] for i in range(8)], dtype=float)


def mini_posterior(x: np.ndarray, g: np.ndarray = MINI_G, prior: np.ndarray = MINI_PRIOR) -> np.ndarray:
    """Exakter Posterior P(d | x) der Mini-Welt (Schleife, ohne die Module der Demo)."""
    out = np.zeros((len(x), len(prior)))
    for i, row in enumerate(x):
        w = [prior[d] * np.prod([g[d][s] if row[s] else 1 - g[d][s] for s in range(len(row))]) for d in range(len(prior))]
        out[i] = np.array(w) / sum(w)
    return out


def mini_gemeinsam() -> np.ndarray:
    """Gemeinsame Verteilung (Krankheit, Muster): Matrix 3 x 8, Summe 1."""
    x = mini_muster()
    joint = np.zeros((3, 8))
    for d in range(3):
        for i, row in enumerate(x):
            joint[d, i] = MINI_PRIOR[d] * np.prod([MINI_G[d][s] if row[s] else 1 - MINI_G[d][s] for s in range(3)])
    return joint


@pytest.fixture
def mini_g():
    return MINI_G.copy()


@pytest.fixture
def mini_prior():
    return MINI_PRIOR.copy()


@pytest.fixture
def muster():
    return mini_muster()
