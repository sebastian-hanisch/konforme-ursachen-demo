"""AppTest-Rauchtests (DEMO-PLAYBOOK §1d Eckfall-Matrix): Standard, jedes Preset, jede Stufe jedes Reglers am Minimum und Maximum, Kombination aller Extremwerte, Seed, Patient, PDF."""

import os
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import kfu_constants as C
import kfu_presets as P

APP_PATH = str(Path(__file__).resolve().parent.parent / "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))
STUFEN = [k for k, s in P.SETTING_SPECS.items() if s.options is not None]


def _fresh() -> AppTest:
    at = AppTest.from_file(APP_PATH, default_timeout=TIMEOUT)
    at.run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    return at


def test_app_laedt_ohne_ausnahme():
    at = _fresh()
    assert len(at.metric) >= 4


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_jedes_preset_laeuft_durch(name):
    at = _fresh()
    at.sidebar.button(key=f"preset_{name}").click().run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    preset = C.PRESETS[name]
    for key, state_key in P.PRESET_KEYS.items():
        assert at.session_state[state_key] == preset[key]


@pytest.mark.parametrize("state_key", STUFEN)
@pytest.mark.parametrize("kante", ["lo", "hi"])
def test_jede_stufe_am_rand_laeuft_durch(state_key, kante):
    at = _fresh()
    spec = P.SETTING_SPECS[state_key]
    at.sidebar.select_slider(key=state_key).set_value(spec.lo if kante == "lo" else spec.hi).run(timeout=TIMEOUT)
    assert not at.exception, (state_key, kante, [str(e) for e in at.exception])


def test_jede_stufe_jedes_reglers_laeuft_durch():
    at = _fresh()
    for state_key in STUFEN:
        for o in P.options(state_key):
            at.sidebar.select_slider(key=state_key).set_value(o)
            at.run(timeout=TIMEOUT)
            assert not at.exception, (state_key, o, [str(e) for e in at.exception])
        at.sidebar.select_slider(key=state_key).set_value(P.SETTING_SPECS[state_key].default)


def test_kombination_aller_minima_und_aller_maxima():
    for kante in ("lo", "hi"):
        at = _fresh()
        for state_key in STUFEN:
            spec = P.SETTING_SPECS[state_key]
            at.sidebar.select_slider(key=state_key).set_value(spec.lo if kante == "lo" else spec.hi)
        at.run(timeout=TIMEOUT)
        assert not at.exception, (kante, [str(e) for e in at.exception])


def test_duenne_wissensbasis_mit_kleiner_kalibriermenge_und_verschiebung():
    at = _fresh()
    at.sidebar.select_slider(key="kb_select").set_value(3)
    at.sidebar.select_slider(key="ncal_select").set_value(100)
    at.sidebar.select_slider(key="shift_select").set_value(2)
    at.sidebar.select_slider(key="target_select").set_value(95)
    at.run(timeout=TIMEOUT)
    assert not at.exception


def test_seed_und_patient_regler_am_rand():
    at = _fresh()
    at.sidebar.number_input(key="seed_input").set_value(0).run(timeout=TIMEOUT)
    assert not at.exception
    at = _fresh()
    at.sidebar.number_input(key="seed_input").set_value(C.SEED_MAX).run(timeout=TIMEOUT)
    assert not at.exception
    for wert in (1, C.N_EXAMPLE_SHOWN):
        at = _fresh()
        at.slider(key="patient_idx").set_value(wert).run(timeout=TIMEOUT)
        assert not at.exception


def test_patientenwechsel_beim_klassenwechsel_bleibt_im_bereich():
    at = _fresh()
    at.slider(key="patient_idx").set_value(C.N_EXAMPLE_SHOWN).run(timeout=TIMEOUT)
    for focus in (1, 2, 3, 0):
        at.sidebar.select_slider(key="focus_select").set_value(focus).run(timeout=TIMEOUT)
        assert not at.exception, (focus, [str(e) for e in at.exception])


def test_beispielpatient_aufloesen_fuer_jedes_verfahren():
    at = _fresh()
    at.toggle(key="patient_reveal").set_value(True).run(timeout=TIMEOUT)
    assert not at.exception
    assert any("Wahre Krankheit: K" in c.value for c in at.caption)
    for method in C.METHOD_OPTIONS:
        at.sidebar.select_slider(key="method_select").set_value(method).run(timeout=TIMEOUT)
        assert not at.exception


def test_pdf_wird_erst_nach_dem_klick_erzeugt():
    at = _fresh()
    assert not [b for b in at.get("download_button")]
    at.button(key="pdf_make").click().run(timeout=TIMEOUT)
    assert not at.exception
    assert at.session_state["pdf_bytes"][:4] == b"%PDF"


def test_verdikte_kernfragen_und_hinweise_stehen_auf_der_seite():
    at = _fresh()
    texte = [m.value for m in at.markdown]
    assert all(any(f"Kernfrage {i}" in t for t in texte) for i in (1, 2, 3, 4))
    assert any("keine medizinische Beratung" in t for t in texte)
    assert len(at.success) + len(at.warning) + len(at.info) >= 6
    assert any("Das Versprechen hält" in s.value for s in at.success)           # Standard: Gesamtabdeckung hält, die erste Klasse nicht
    assert any("In dieser Klasse liegt die Abdeckung unter dem Ziel" in w.value for w in at.warning)


def test_verschobene_dokumentation_zeigt_das_gebrochene_versprechen():
    at = _fresh()
    at.sidebar.button(key="preset_Verschobene Dokumentation").click().run(timeout=TIMEOUT)
    assert any("Das Versprechen hält hier nicht" in w.value for w in at.warning)
