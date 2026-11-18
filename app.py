"""Konforme Ursachenmenge – eine Menge statt einer Rangliste - interaktive Fall-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Lehrmodell mit erfundenen Daten, keine medizinische Beratung. Aufbau nach DEMO-PLAYBOOK §2 (Fall-Demo).

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import kfu_constants as C
import kfu_evaluation as ev
import kfu_live as L
import kfu_pdf_export as PDF
import kfu_presets as P
import kfu_results as RES
import kfu_ui_panel as UI
import kfu_visualization as V
from kfu_layout import dunkles_design, kopf_css, tabellen_css

st.set_page_config(page_title="Konforme Ursachenmenge – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner="Messe fünf Welten ...")
def _measure(settings):
    return L.measure(settings)


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in kfu_layout.py).
st.html(kopf_css(dunkles_design()))
st.html(tabellen_css())
with st.container(key="kopf"):
    st.title("🧩 Konforme Ursachenmenge – eine Menge statt einer Rangliste")
st.markdown(
    """
Statt einer Rangliste möglicher **seltener Krankheiten** nennt die Demo eine **Menge**: Sie soll die wahre Krankheit mit einer vorher gewählten Wahrscheinlichkeit enthalten, der **Ziel-Abdeckung**.
Dazu wird eine **Schwelle** an einer **Kalibriermenge** von Patienten mit bekannter Krankheit bestimmt (**Split-Konformal**). Die Demo zeigt, was dieses **Versprechen** wirklich zusagt:
es ist garantiert **im Mittel über alle Patienten**, wenn Kalibrier- und Testpatienten **austauschbar** sind; es gilt nicht für jeden Patienten und nicht für jede Gruppe.

**Lehrmodell mit erfundenen Daten, keine medizinische Beratung.** Alle Aussagen gelten für diese Welt, nicht für echte Krankheiten.

Weiter unten: vier **Kernfragen** und der Expander **🔧 Wie wir das erreichen – vollständiger Methodenvergleich**.
"""
)

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

P.load_permalink_settings()
P.init_session_state_defaults()


def _stufe(label_text, state_key, help_text, **kw):
    return st.select_slider(label_text, options=P.options(state_key), key=state_key, format_func=lambda v, k=state_key: P.label(k, v), help=help_text, **kw)


with st.sidebar:
    P.sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Versprechen**")
    target = _stufe("Ziel-Abdeckung", "target_select", "Anteil der Patienten, bei denen die wahre Krankheit in der Menge liegen soll (im Mittel, unter Austauschbarkeit).")
    ncal = _stufe("Kalibrierpatienten", "ncal_select", "Wie viele Patienten mit bekannter Krankheit die Schwelle bestimmen (vor dem Entfernen von Patienten ohne dokumentiertes Merkmal).")
    st.markdown("**Wissensbasis**")
    kb = _stufe("Wissensbasis: Fälle je Krankheit", "kb_select", "bekannt: die wahren Häufigkeiten. Sonst werden die Häufigkeiten aus so vielen gezogenen Fällen je Krankheit geschätzt (Add-½-Glättung).")
    st.markdown("**Verschiebung im Test**")
    shift = _stufe("Was im Test anders ist als in der Kalibrierung", "shift_select",
                   "keine: Kalibrier- und Testpatienten sind austauschbar. Vorab: im Test gilt ein Zipf-Vorab statt gleichverteilt. Dokumentation: im Test fehlen mehr Merkmale in der Akte (q 0,6 statt 0,3).")
    st.markdown("**Anzeige**")
    method = _stufe("Verfahren", "method_select", "LAC, APS oder Mondrian-LAC. Es werden immer alle drei gerechnet; der Regler wählt, welches Verfahren Kennzahlen und Beispielpatient zeigen.")
    focus = _stufe("Klasse für Kennzahlen und Beispielpatient", "focus_select", "Klassen nach der Zahl dokumentierter Merkmale. Bei „alle Patienten“ zeigen die Kennzahlen die Klasse 1–2 Merkmale.")
    st.markdown("**Zufall**")
    seed = st.number_input("Zufalls-Seed der Messung", *P.bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neue Welten würfeln", width="stretch", on_click=P.randomize_seed)

P.sync_query_params({"target_select": target, "kb_select": kb, "shift_select": shift, "ncal_select": ncal, "method_select": method, "focus_select": focus, "seed_input": int(seed)})

settings = L.Settings(target=int(target), kb=int(kb), shift=int(shift), ncal=int(ncal), seed=int(seed))
method_key = C.METHOD_OF_OPTION[int(method)]
cls = max(int(focus) - 1, 0)
m = _measure(settings)
kz = ev.kennzahlen(m, method_key, cls)
(v1_kind, v1_text), (v2_kind, v2_text) = ev.verdicts(m, kz)
n_cal_eff, n_test_eff = L.n_effective(m)

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Eine Messung (live)")
st.caption(f"Diese Messung: {len(m.runs)} Welten, je {n_cal_eff:.0f} Kalibrierpatienten und {n_test_eff:.0f} Testpatienten im Mittel (Zufalls-Seed {settings.seed}), Mittel ± Streuung über die Welten. "
           "Patienten ohne dokumentiertes Merkmal sind entfernt. Die Verdikte unter den Kennzahlen rechnen live aus dieser Messung (gepaart über die Welten); "
           "die Abbildungen der Kernfragen stammen aus der vorgerechneten Messreihe.")
UI.metrics_row(kz)
getattr(st, v1_kind)(v1_text)
getattr(st, v2_kind)(v2_text)
c_a, c_b = st.columns(2)
c_a.plotly_chart(V.fig_coverage_live(kz["summary"], settings.target), width="stretch", key="main_chart", config=V.CONFIG)
c_b.plotly_chart(V.fig_size_live(kz["summary"]), width="stretch", key="size_chart", config=V.CONFIG)
st.caption("Abdeckung: Anteil der Patienten, bei denen die wahre Krankheit in der Menge liegt. Menge: Zahl der Krankheiten in der Menge, im Mittel. Klassen: Zahl der in der Akte dokumentierten Merkmale. "
           "Die Streuung ist die Standardabweichung der Mittel der einzelnen Welten (n − 1).")

if st.button("📄 PDF der Messung erstellen", key="pdf_make"):
    st.session_state["pdf_bytes"] = PDF.build_pdf(settings, kz, ((v1_kind, v1_text), (v2_kind, v2_text)), len(m.runs), round(n_test_eff))
    st.session_state["pdf_for"] = settings
if st.session_state.get("pdf_for") == settings and st.session_state.get("pdf_bytes"):
    st.download_button("⬇️ PDF herunterladen", st.session_state["pdf_bytes"], file_name="konforme-ursachenmenge-messung.pdf", mime="application/pdf", key="pdf_download")

st.markdown("### 🧍 Ein Beispielpatient")
positions = ev.example_indices(m, int(focus))
UI.patient_panel(m, method_key, int(focus), positions)

# --- Kernfragen ----------------------------------------------------------------------------------------------------------------------------

meta = RES.meta()
vorgerechnet = (f"Vorgerechnet: {meta['cells']} Zellen, je zwei Mengen von {meta['worlds_per_set']} Welten (Zufalls-Seed {meta['sets']['A']} und {meta['sets']['B']}), "
                f"{meta['test_patients_per_world']} Testpatienten je Welt; sonst Voreinstellung (Ziel 90 Prozent, 500 Kalibrierpatienten, Wissensbasis bekannt, keine Verschiebung).")
base = RES.cell(RES.BASE)

st.markdown("---")
st.markdown("## ❓ Kernfrage 1: Hält das Versprechen auch für jede Gruppe von Patienten?")
k1_kind, k1_text = ev.kernfrage_halt(base)
getattr(st, k1_kind)(k1_text)
st.plotly_chart(V.fig_coverage_cell(base), width="stretch", key="kf1_chart", config=V.CONFIG)
st.caption(vorgerechnet)

st.markdown("## ❓ Kernfrage 2: Wann bricht das Versprechen?")
k2_kind, k2_text = ev.kernfrage_bruch(RES.cell(RES.Settings(shift=0)), RES.cell(RES.Settings(shift=1)), RES.cell(RES.Settings(shift=2)), RES.cell(RES.Settings(kb=3)))
getattr(st, k2_kind)(k2_text)
k2a, k2b = st.columns(2)
k2a.plotly_chart(V.fig_shift(), width="stretch", key="kf2_shift_chart", config=V.CONFIG)
k2b.plotly_chart(V.fig_kb(), width="stretch", key="kf2_kb_chart", config=V.CONFIG)
st.caption(vorgerechnet + " Die Garantie gilt unter Austauschbarkeit von Kalibrier- und Testpatienten; beide Verschiebungen verletzen sie, in dieser Rechenwelt bricht aber nur die verschobene Dokumentation das Versprechen.")

st.markdown("## ❓ Kernfrage 3: Was kostet das Versprechen?")
k3_kind, k3_text = ev.kernfrage_preis({t: RES.cell(RES.Settings(target=t)) for t in C.TARGET_OPTIONS}, base)
getattr(st, k3_kind)(k3_text)
st.plotly_chart(V.fig_target_size(), width="stretch", key="kf3_chart", config=V.CONFIG)
st.caption(vorgerechnet)

st.markdown("## ❓ Kernfrage 4: Wie stark streut die Abdeckung mit der Kalibriermenge?")
spread = RES.load()["spread"]
k4_kind, k4_text = ev.kernfrage_streuung(spread)
getattr(st, k4_kind)(k4_text)
k4a, k4b = st.columns(2)
k4a.plotly_chart(V.fig_spread(spread), width="stretch", key="kf4_chart", config=V.CONFIG)
rows_s = ["| Kalibrierpatienten | Ziel | Mittel | Streuung (Simulation) | Streuung (Beta) | 5-%-Quantil | kleinster Wert |", "|---|---|---|---|---|---|---|"]
rows_s += [f"| {r['n_cal']} | {r['target']} % | {ev.pct(100 * r['mean'])} % | {ev.dec(100 * r['sd'], 2)} | {ev.dec(100 * r['beta_sd'], 2)} | {ev.pct(100 * r['q05'])} % | {ev.pct(100 * r['min'])} % |" for r in spread]
k4b.markdown("Abdeckung einer einzelnen Kalibrierung (Prozent beziehungsweise Prozentpunkte, " + f"{meta['spread_reps']} Kalibrierungen je Zeile):\n\n" + "\n".join(rows_s))
pool_a, pool_b = (f"{v:,}".replace(",", ".") for v in meta["spread_pool"])   # nur die Zahlen umformatieren, nie den ganzen Satz
st.caption(f"Die Simulation zieht Kalibrierpatienten mit Zurücklegen aus einem Vorrat von {pool_a} Patienten und misst die Abdeckung an {pool_b} anderen Patienten derselben Welt; "
           "die Beta-Verteilung gilt für stetige Ergebnisse ohne Gleichstände. Beide Hälften sind endlich, darum liegt die Simulation etwas neben der Beta-Verteilung (siehe README).")

st.markdown("---")

# --- Methodenvergleich ---------------------------------------------------------------------------------------------------------------------

with st.expander("🔧 Wie wir das erreichen – vollständiger Methodenvergleich"):
    tab_v, tab_k, tab_s = st.tabs(["📏 Verfahren", "🧮 Schwelle und Rang", "📚 Alle Zellen"])
    with tab_v:
        st.markdown(UI.method_table(kz["summary"]))
        st.markdown(
            "- **LAC:** Ergebnis einer Krankheit = 1 − Posterior; die Menge enthält alle Krankheiten, deren Ergebnis höchstens die Schwelle ist. Bei richtigem Posterior die kleinsten Mengen bei gegebener Abdeckung im Mittel (in der Messreihe außer bei der dünnen Wissensbasis), aber ungleiche Abdeckung je Klasse.\n"
            "- **APS:** Ergebnis einer Krankheit = Masse aller strikt höher gereihten Krankheiten (nicht randomisiert, Gleichstände nach Index); die Menge ist ein Anfangsstück der Rangliste.\n"
            "- **Mondrian-LAC:** LAC mit je einer eigenen Schwelle für die Klassen 1–2, 3–4 und 5 und mehr dokumentierte Merkmale; die Abdeckung stimmt je Klasse, wenn die Kalibrierpatienten der Klasse austauschbar mit den Testpatienten der Klasse sind.\n"
            "- **Feste Top-k-Liste:** immer die k wahrscheinlichsten Krankheiten; die Abdeckung ist dann ein Ergebnis, kein Versprechen."
        )
        st.caption("Zahlen in Klammern: Streuung über die Welten (n − 1). Mittel dieser Messung.")
    with tab_k:
        n_cal_show = m.runs[0].n_cal
        rang = ((n_cal_show + 1) * settings.target + 99) // 100
        st.markdown(f"Mit {n_cal_show} Kalibrierpatienten und Ziel {settings.target} Prozent ist die Schwelle das **{rang}.** kleinste Ergebnis der Kalibrierpatienten "
                    "(Rang ⌈(n + 1) · Ziel⌉, exakt in ganzen Prozent gerechnet). Gibt es weniger Kalibrierpatienten, als der Rang verlangt, enthält die Menge alle Krankheiten.")
        th = m.runs[0].methods[method_key]["thresholds"]
        if method_key == "MONDRIAN":
            st.markdown("Schwellen der ersten Welt je Klasse: " + ", ".join(f"{C.BIN_NAMES[i]}: {ev.dec(t)}" for i, t in enumerate(th)) + ".")
        else:
            st.markdown(f"Schwelle der ersten Welt für {C.METHOD_SHORT[method_key]}: {ev.dec(th[0])}.")
        st.caption("Bei LAC liegt die Schwelle auf der Skala 1 − Posterior (die Menge enthält Krankheiten mit Posterior von mindestens 1 minus Schwelle), bei APS auf der Skala der Masse der höher gereihten Krankheiten.")
    with tab_s:
        zeilen = ["| Zelle | Abdeckung LAC | Abdeckung APS | Abdeckung Mondrian | Menge LAC | Menge APS | Menge Mondrian |", "|---|---|---|---|---|---|---|"]
        for s in RES.sweep_settings():
            c = RES.cell(s)
            zeilen.append(f"| {ev.cell_label(s)} | " + " | ".join(ev.pct(RES.pooled(c, mm, "cov")) for mm in C.METHODS) + " | " + " | ".join(ev.pct(RES.pooled(c, mm, "size")) for mm in C.METHODS) + " |")
        st.markdown("Vorgerechnete Messreihe (Mittel der beiden Mengen, zehn Welten; Abdeckung in Prozent, Menge in Krankheiten):\n\n" + "\n".join(zeilen))
        st.caption("Jede Zeile ist eine Zelle der Messreihe; die Zeilen der Kernfragen oben stammen aus denselben Zellen.")

with st.expander("Wie funktioniert diese Demo?"):
    st.markdown(
        f"""
**Die Welt.** {C.ND} Krankheiten und {C.NS} Merkmale mit Zipf-verteilter Beliebtheit: beliebte Merkmale kommen in vielen Krankheitsprofilen und im Hintergrund vor (Konstruktion der Welt, ihr Informationsgehalt ist nicht gemessen). Jede Krankheit hat
{C.K_MIN_FEAT} bis {C.K_MAX_FEAT} Profilmerkmale mit Häufigkeit 0,95, 0,6, 0,3 oder 0,1. Ein vorhandenes Merkmal wird mit Wahrscheinlichkeit 1 − q aufgeschrieben (q = {str(C.Q_BASE).replace('.', ',')}), dazu kommt eine Hintergrundrate je Merkmal.

**Patienten.** Krankheit gleichverteilt, Merkmale unabhängig gegeben die Krankheit. Patienten ohne jedes dokumentierte Merkmal werden entfernt (Kalibrierung wie Test). Das Modell ist Naive Bayes mit den wahren Häufigkeiten
oder mit Häufigkeiten aus gezogenen Fällen (Add-½-Glättung); sein Posterior ist die Grundlage aller drei Verfahren.

**Versprechen.** Aus der Kalibriermenge wird die Schwelle bestimmt, so dass die wahre Krankheit eines weiteren Patienten im Mittel mit mindestens der Ziel-Abdeckung in der Menge liegt, wenn dieser Patient und die
Kalibrierpatienten austauschbar sind. Das ist eine Aussage über den Mittelwert über Patienten und über die Ziehung der Kalibriermenge, nicht über einen einzelnen Patienten und nicht über eine Gruppe.

**Verschiebung.** Wird im Test das Vorab oder der Dokumentationsverlust geändert (die Kalibrierung bleibt unverändert), sind Kalibrier- und Testpatienten nicht mehr austauschbar.

**Messung.** Je Einstellung {C.N_WORLDS} Welten mit je {C.N_TEST} Testpatienten (SplitMix64: der ganzzahlige Zufallsstrom ist auf jeder Plattform derselbe). Die Streuung über die Welten ist ausgewiesen; Verdikte nennen ihre Bedingung (Toleranz oder zwei Standardfehler); „hält“ heißt „nicht widerlegt“, Toleranz und Einteilung in zwei Verdikte sind gesetzt, nicht abgestimmt.
"""
    )
    st.markdown("#### 🚧 Wo die Annahmen enden")
    st.markdown(
        "| Annahme der Demo | Was in der Wirklichkeit anders ist |\n|---|---|\n"
        "| Kalibrier- und Testpatienten sind austauschbar | Kliniken, Jahre und Dokumentationsgewohnheiten verschieben sich; dann gilt das Versprechen nicht |\n"
        "| Merkmale unabhängig gegeben die Krankheit | echte Merkmale sind abhängig und haben Hierarchien (Ontologie) |\n"
        "| Die wahre Krankheit jedes Kalibrierpatienten ist bekannt | echte Diagnosen sind unsicher und verspätet |\n"
        f"| {C.ND} Krankheiten, {C.NS} Merkmale | echte Wissensbasen haben mehrere Tausend Krankheiten und Merkmale |\n"
        "| Eine Krankheit je Patient | echte Patienten haben mehrere Diagnosen |\n"
        "| Klassen nach der Zahl dokumentierter Merkmale | andere Gruppen (Alter, Herkunft, Klinik) können schlechter abgedeckt sein; die Demo misst sie nicht |"
    )

with st.expander("⚠️ Annahmen, Grenzen und bekannte Probleme"):
    st.markdown(
        """
**Annahmen.** Erfundene Welt mit Naive-Bayes-Struktur. Parameter (Häufigkeiten, Hintergrund, Dokumentationsverlust) sind gesetzt, nicht aus Daten geschätzt. Die Wissensbasis wird, wenn sie nicht bekannt ist, aus Fällen derselben Welt geschätzt.

**Grenzen.** Das Versprechen gilt im Mittel über Patienten, über die Ziehung der Kalibriermenge und nur unter Austauschbarkeit. Für eine einzelne Kalibrierung streut die Abdeckung (Kernfrage 4). Fünf Welten je Messung: die Streuung über die
Welten ist ausgewiesen, Unterschiede unter der Toleranz oder unter zwei Standardfehlern werden nicht gedeutet. Mondrian gilt nur für die gewählte Klasseneinteilung; die Demo prüft keine anderen Gruppen.

**Bekannte Probleme und Unsicherheiten.** Nur an erfundenen Welten geprüft; keine echten Patientendaten, keine echte Wissensbasis (HPO, Orphanet), keine Ontologie. APS ist nicht randomisiert gerechnet. Die Aussagen gelten für die gemessenen Zellen
und die gemessene Regel jedes Verfahrens, nicht für die Methodenklasse. **Keine medizinische Beratung, keine Diagnoseempfehlung.**
"""
    )

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Lesehilfe.** Gegeben: der Posterior $P(d \mid x)$ eines Modells für einen Patienten mit dokumentierten Merkmalen $x$, dazu Kalibrierpatienten $(x_i, d_i)$, $i = 1, \dots, n$. Gesucht: eine Menge $\mathcal{C}(x)$ von Krankheiten.

| Symbol | Bedeutung |
|---|---|
| $d$, $x$ | Krankheit, dokumentierte Merkmale |
| $s(x, d)$ | Nichtkonformität: klein = plausibel |
| $n$ | Zahl der Kalibrierpatienten |
| $\hat q$ | Schwelle |
| $1 - \alpha$ | Ziel-Abdeckung |
| $\ell$ | $\lfloor (n + 1)\alpha \rfloor$ |
| $k_x$ | Klasse des Patienten nach der Zahl dokumentierter Merkmale |
        """
    )
    st.markdown("Nichtkonformität (LAC beziehungsweise APS, nicht randomisiert; bei gleichem Posterior ordnet die Rechnung stabil nach Index, die Summe läuft dann über die davor gereihten Krankheiten):")
    st.latex(r"s_{\mathrm{LAC}}(x, d) = 1 - P(d \mid x), \qquad s_{\mathrm{APS}}(x, d) = \sum_{d' :\, P(d' \mid x) > P(d \mid x)} P(d' \mid x)")
    st.markdown("Schwelle und Menge (Rang $\\lceil (n + 1)(1 - \\alpha) \\rceil$ in den sortierten Ergebnissen der wahren Krankheiten der Kalibrierpatienten; ist der Rang größer als $n$, ist die Schwelle unendlich):")
    st.latex(r"\hat q = s_{(\lceil (n + 1)(1 - \alpha) \rceil)}, \qquad \mathcal{C}(x) = \{\, d : s(x, d) \le \hat q \,\}")
    st.markdown("Garantie (Austauschbarkeit von Kalibrier- und Testpatient, Mittel über die Ziehung der Kalibriermenge und des Testpatienten; die obere Grenze gilt für stetige Ergebnisse ohne Gleichstände):")
    st.latex(r"1 - \alpha \;\le\; \mathbb{P}\bigl(d_{\mathrm{test}} \in \mathcal{C}(x_{\mathrm{test}})\bigr) \;\le\; 1 - \alpha + \frac{1}{n + 1}")
    st.markdown("Mondrian-LAC: eine Schwelle je Klasse $k$, aus den Kalibrierpatienten dieser Klasse (Austauschbarkeit je Klasse):")
    st.latex(r"\hat q_k = s^{(k)}_{(\lceil (n_k + 1)(1 - \alpha) \rceil)}")
    st.markdown("Abdeckung einer festen Kalibrierung (stetige Ergebnisse ohne Gleichstände, $\\ell = \\lfloor (n + 1)\\alpha \\rfloor$):")
    st.latex(r"\mathrm{Abd.} \sim \mathrm{Beta}(n + 1 - \ell,\; \ell), \qquad \mathbb{E} = \frac{n + 1 - \ell}{n + 1}")
    st.caption("Der Formelblock zeigt Nichtkonformität, Schwelle, Garantie, Mondrian-Schwelle und die Verteilung der Abdeckung. Nicht in den Gleichungen stehen: der Erzeuger der Welt und die Schätzung der Häufigkeiten (Add-½-Glättung); sie stehen im README und im Code.")

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
