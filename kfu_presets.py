"""Permalink (Begrenzen, auf Stufen einrasten), Presets und Zufalls-Seed-Button (Standardmuster aus dem Demo-Portfolio).

Alle Regler außer dem Zufalls-Seed sind Stufen-Regler (`st.select_slider`): die Stufen der Messregler sind die gemessenen Zellen der Messreihe; Verfahren und Klasse
sind Anzeigeregler (gerechnet werden immer alle drei Verfahren)."""

import random
from dataclasses import dataclass

import streamlit as st

import kfu_constants as C


@dataclass(frozen=True)
class SettingSpec:
    url_param: str
    caster: type
    default: object
    lo: float | None = None
    hi: float | None = None
    options: tuple | None = None   # Stufen eines Stufen-Reglers; lo und hi sind dann die kleinste und die größte Stufe


def _opt(url_param, caster, options, default):
    return SettingSpec(url_param, caster, default, min(options), max(options), tuple(options))


SETTING_SPECS = {
    "target_select": _opt("target", int, C.TARGET_OPTIONS, C.DEFAULT["target"]),
    "kb_select": _opt("kb", int, C.KB_OPTIONS, C.DEFAULT["kb"]),
    "shift_select": _opt("shift", int, C.SHIFT_OPTIONS, C.DEFAULT["shift"]),
    "ncal_select": _opt("ncal", int, C.NCAL_OPTIONS, C.DEFAULT["ncal"]),
    "method_select": _opt("method", int, C.METHOD_OPTIONS, C.DEFAULT["method"]),
    "focus_select": _opt("focus", int, C.FOCUS_OPTIONS, C.DEFAULT["focus"]),
    "seed_input": SettingSpec("seed", int, C.DEFAULT["seed"], 0, C.SEED_MAX),
}
PRESET_KEYS = {"target": "target_select", "kb": "kb_select", "shift": "shift_select", "ncal": "ncal_select", "method": "method_select", "focus": "focus_select",
               "seed": "seed_input"}

# Beschriftungen der Stufen
LABELS = {
    "target_select": {80: "80 Prozent", 90: "90 Prozent", 95: "95 Prozent"},
    "kb_select": {0: "bekannt", 30: "30 Fälle", 3: "3 Fälle"},
    "shift_select": {0: "keine", 1: "Vorab", 2: "Dokumentation"},
    "ncal_select": {100: "100 Patienten", 500: "500 Patienten", 2000: "2000 Patienten"},
    "method_select": {0: "LAC", 1: "APS", 2: "Mondrian"},
    "focus_select": {0: "alle Patienten", 1: "1–2 Merkmale", 2: "3–4 Merkmale", 3: "5 und mehr Merkmale"},
}


def label(state_key, value):
    return LABELS[state_key].get(value, str(value))


def init_session_state_defaults():
    for state_key, spec in SETTING_SPECS.items():
        if state_key not in st.session_state:
            st.session_state[state_key] = spec.default


def bounds(state_key):
    spec = SETTING_SPECS[state_key]
    return spec.lo, spec.hi


def options(state_key):
    return list(SETTING_SPECS[state_key].options)


def _snap(spec, value):
    """Auf die nächstliegende Stufe einrasten (Permalink mit einem Wert zwischen den Stufen)."""
    return min(spec.options, key=lambda o: abs(o - value))


def load_permalink_settings():
    """Einmal je Sitzung: Werte aus der Adresszeile übernehmen, auf die Reglergrenzen begrenzt und auf Stufen eingerastet."""
    if "permalink_loaded" in st.session_state:
        return
    qp = st.query_params
    for state_key, spec in SETTING_SPECS.items():
        if spec.url_param in qp:
            try:
                value = spec.caster(qp[spec.url_param])
            except (ValueError, TypeError):
                continue
            if spec.options is not None:
                value = _snap(spec, value)
            else:
                value = max(spec.lo, min(spec.hi, value))
            st.session_state[state_key] = value
    st.session_state["permalink_loaded"] = True


def sync_query_params(values):
    """`values`: {state_key: aktueller Wert}; die Adresszeile spiegelt die Konfiguration."""
    try:
        for state_key, value in values.items():
            st.query_params[SETTING_SPECS[state_key].url_param] = str(value)
    except Exception:
        pass


def apply_preset(name):
    for key, state_key in PRESET_KEYS.items():
        if key in C.PRESETS[name]:
            st.session_state[state_key] = C.PRESETS[name][key]


def aktives_preset():
    """Name des Presets, dessen Werte GENAU den aktuellen Einstellungen entsprechen, sonst None.

    Zustandslos: verglichen wird jeder Regler aus SETTING_SPECS (ein Preset ohne Eintrag für einen Regler meint dessen Standardwert) mit dem
    Session State. Ein später ergänzter Regler braucht nur seinen Eintrag in SETTING_SPECS (tests/test_layout.py prüft das für jeden Regler)."""
    preset_key_of = {state_key: key for key, state_key in PRESET_KEYS.items()}
    for name, preset in C.PRESETS.items():
        if all(
            st.session_state.get(state_key, spec.default) == preset.get(preset_key_of.get(state_key), spec.default)
            for state_key, spec in SETTING_SPECS.items()
        ):
            return name
    return None


def sidebar_presets():
    """Schnellstart oben in der Seitenleiste; das aktive Preset ist hervorgehoben (`type="primary"`)."""
    st.header("🎯 Schnellstart")
    st.caption("Ein Beispielszenario laden:")
    aktiv = aktives_preset()
    for name in C.PRESETS:
        st.button(
            name, width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP.get(name, ""), key=f"preset_{name}",
            type="primary" if aktiv == name else "secondary",
        )


def randomize_seed():
    st.session_state["seed_input"] = random.randint(0, C.SEED_MAX)
