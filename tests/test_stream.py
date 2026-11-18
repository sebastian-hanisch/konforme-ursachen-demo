"""Zufallsstrom: die vektorisierte Fassung liefert dieselben Zahlen wie die Skalarklasse SplitMix64 (kfu_rng.py), und kfu_rng.py ist die geprüfte Kopie der Vorlage."""

from pathlib import Path

import numpy as np
import pytest

from kfu_rng import SplitMix64
from kfu_stream import Stream, derive

VORLAGE = Path(__file__).resolve().parent.parent.parent / "sebastianhanisch-website" / "tools" / "templates" / "rng_splitmix64_exact.py"


@pytest.mark.parametrize("seed", [0, 1, 35, 123456789, 2**63 + 5, 2**64 - 1])
def test_vektorfassung_gleich_skalarklasse(seed):
    ref = SplitMix64(seed)
    expected = np.array([ref.random() for _ in range(300)])
    assert np.array_equal(Stream(seed).uniform(300), expected)   # bitgleich


def test_zwei_aufrufe_setzen_den_strom_fort():
    a, b = Stream(9), Stream(9)
    assert np.array_equal(np.concatenate([a.uniform(7), a.uniform(5)]), b.uniform(12))


def test_form_wird_zeilenweise_gefuellt():
    st = Stream(3)
    arr = st.uniform((4, 5))
    assert arr.shape == (4, 5)
    assert np.array_equal(arr.ravel(), Stream(3).uniform(20))


def test_gleichverteilt_im_halboffenen_intervall():
    u = Stream(11).uniform(100000)
    assert 0.0 <= u.min() and u.max() < 1.0
    assert abs(u.mean() - 0.5) < 0.005


def test_gewichtete_indizes_wie_skalar_choice():
    probs = np.array([0.2, 0.5, 0.3])
    ref = SplitMix64(4)
    expected = [ref.choice(list(probs)) for _ in range(200)]
    assert list(Stream(4).weighted_index(probs, 200)) == expected


def test_abgeleitete_zufalls_seeds_sind_getrennt_und_stabil():
    seeds = {derive(35, salt) for salt in range(1, 6)}
    assert len(seeds) == 5
    assert derive(35, 1) == derive(35, 1)
    assert derive(35, 1) != derive(36, 1)


@pytest.mark.skipif(not VORLAGE.exists(), reason="Vorlage nicht vorhanden (Repo einzeln geklont)")
def test_kfu_rng_ist_die_unveraenderte_kopie_der_vorlage():
    assert (Path(__file__).resolve().parent.parent / "kfu_rng.py").read_bytes() == VORLAGE.read_bytes()


PHN = Path(__file__).resolve().parent.parent.parent / "phaenotyp-ranking-demo"


@pytest.mark.skipif(not PHN.exists(), reason="Vorlage nicht vorhanden (Repo einzeln geklont)")
@pytest.mark.parametrize("name", ["stream", "world", "rankers", "metrics"])
def test_kopierte_module_gleich_den_phn_modulen_bis_auf_das_praefix(name):
    """Die kopierten Hilfsmodule werden nicht verändert: bis auf das Präfix sind sie gleich denen von phaenotyp-ranking-demo (Docstrings eingeschlossen)."""
    kopie = (Path(__file__).resolve().parent.parent / f"kfu_{name}.py").read_text(encoding="utf-8")
    vorlage = (PHN / f"phn_{name}.py").read_text(encoding="utf-8").replace("phn_", "kfu_")
    assert kopie.replace("\r\n", "\n") == vorlage.replace("\r\n", "\n")
