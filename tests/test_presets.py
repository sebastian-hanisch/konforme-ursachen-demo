"""Presets: Vollständigkeit, gültige Stufen, Standard-Preset = Standardeinstellungen, jede Zelle der Presets ist gemessen; Permalink rastet auf Stufen ein."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

import kfu_constants as C
import kfu_presets as P
import kfu_results as RES

APP = str(Path(__file__).resolve().parent.parent / "app.py")
MESSREGLER = ("target", "kb", "shift", "ncal")


def test_jedes_preset_hat_hilfe_und_alle_schluessel():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_werte_liegen_auf_den_stufen_der_regler():
    for name, preset in C.PRESETS.items():
        for key, state_key in P.PRESET_KEYS.items():
            spec = P.SETTING_SPECS[state_key]
            if spec.options is not None:
                assert preset[key] in spec.options, (name, key)
            else:
                assert spec.lo <= preset[key] <= spec.hi


def test_erstes_preset_ist_die_voreinstellung():
    assert next(iter(C.PRESETS.values())) == C.DEFAULT


def test_setting_specs_decken_jeden_preset_schluessel_ab():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)
    for state_key, spec in P.SETTING_SPECS.items():
        assert spec.default in (spec.options or (spec.default,))


def test_jedes_preset_unterscheidet_sich_in_hoechstens_einem_regler_von_der_voreinstellung():
    for name, preset in C.PRESETS.items():
        diff = [k for k in C.DEFAULT if preset[k] != C.DEFAULT[k]]
        assert len(diff) <= 1, (name, diff)


def test_jede_preset_zelle_ist_in_der_messreihe_gemessen():
    for name, preset in C.PRESETS.items():
        s = RES.Settings(**{k: v for k, v in preset.items() if k in MESSREGLER})
        assert RES.cell(s) is not None, name


def test_jedes_preset_aendert_etwas_gegenueber_dem_standard_ausser_dem_standard_selbst():
    for name, preset in list(C.PRESETS.items())[1:]:
        assert preset != C.DEFAULT, name


def test_beschriftungen_gibt_es_fuer_jede_stufe():
    for state_key, spec in P.SETTING_SPECS.items():
        for o in spec.options or ():
            assert o in P.LABELS[state_key], (state_key, o)


def test_snap_rastet_auf_die_naechste_stufe_ein():
    spec = P.SETTING_SPECS["target_select"]
    assert P._snap(spec, 91) == 90 and P._snap(spec, 93) == 95 and P._snap(spec, 0) == 80 and P._snap(spec, 99) == 95


def test_permalink_rastet_ein_und_begrenzt():
    at = AppTest.from_file(APP, default_timeout=180)
    at.query_params["target"] = "92"
    at.query_params["kb"] = "20"
    at.query_params["ncal"] = "1300"
    at.query_params["seed"] = "99999999"
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    assert at.session_state["target_select"] == 90                  # 92 liegt zwischen 90 und 95: näher an 90
    assert at.session_state["kb_select"] == 30                      # 20 liegt zwischen 3 und 30: näher an 30
    assert at.session_state["ncal_select"] == 2000                  # 1300: Abstand 700 zu 2000, 800 zu 500
    assert at.session_state["seed_input"] == C.SEED_MAX


def test_permalink_ungueltiger_wert_wird_ignoriert():
    at = AppTest.from_file(APP, default_timeout=180)
    at.query_params["target"] = "abc"
    at.run()
    assert not at.exception
    assert at.session_state["target_select"] == C.DEFAULT["target"]
