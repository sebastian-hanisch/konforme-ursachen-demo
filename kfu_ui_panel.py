"""Darstellung einzelner Bausteine der Seite (Streamlit): Kennzahlen, Beispielpatient, Tabellen der Verfahren. Rechnet nichts selbst."""

import streamlit as st

import kfu_constants as C
import kfu_evaluation as ev
import kfu_visualization as V


def metrics_row(k: dict):
    """Vier Kennzahlen im 2 x 2-Raster für das gewählte Verfahren; Deltas immer „mein Wert minus Referenz“."""
    s = k["summary"][k["method"]]
    cls = k["cls"]
    target = k["target"]
    name = C.METHOD_SHORT[k["method"]]
    c1, c2 = st.columns(2)
    c1.metric(f"Abdeckung {name} (alle Patienten)", f"{ev.pct(s['cov'][0])} %", delta=f"{ev.spct(k['gap_all'][0])} Punkte gegen das Ziel {target} %", delta_color="normal")
    c2.metric(f"Mittlere Menge {name}", f"{ev.pct(s['size'][0])} Krankheiten", delta=f"von {C.ND} Krankheiten insgesamt", delta_color="off")
    c3, c4 = st.columns(2)
    c3.metric(f"Abdeckung {name} bei {C.BIN_DAT[cls]}", f"{ev.pct(s['cov_b'][cls][0])} %", delta=f"{ev.spct(k['gap_cls'][0])} Punkte gegen das Ziel {target} %", delta_color="normal")
    c4.metric(f"Mittlere Menge {name} bei {C.BIN_DAT[cls]}", f"{ev.pct(s['size_b'][cls][0])} Krankheiten", delta=f"{ev.pct(s['share_b'][cls][0])} % der Patienten", delta_color="off")


def method_table(summary: dict) -> str:
    """Markdown-Tabelle: je Verfahren Abdeckung gesamt und je Klasse, mittlere Menge gesamt und je Klasse (Mittel über die Welten, Streuung in Klammern)."""
    head = ["Verfahren", "Abdeckung gesamt"] + [f"Abdeckung {n}" for n in C.BIN_NAMES] + ["Menge gesamt"] + [f"Menge {n}" for n in C.BIN_NAMES]
    rows = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for m in C.METHODS:
        v = summary[m]
        cells = [f"{ev.pct(v['cov'][0])} ({ev.pct(v['cov'][1])})"] + [f"{ev.pct(v['cov_b'][c][0])} ({ev.pct(v['cov_b'][c][1])})" for c in range(3)]
        cells += [f"{ev.pct(v['size'][0])} ({ev.pct(v['size'][1])})"] + [f"{ev.pct(v['size_b'][c][0])} ({ev.pct(v['size_b'][c][1])})" for c in range(3)]
        rows.append(f"| {C.METHOD_NAMES[m]} | " + " | ".join(cells) + " |")
    f = summary["fixed"]
    rows.append(f"| feste Top-1-Liste (eine Krankheit) | {ev.pct(f['top1'][0])} ({ev.pct(f['top1'][1])}) | | | | 1 | | | |")
    rows.append(f"| feste Top-5-Liste (fünf Krankheiten) | {ev.pct(f['top5'][0])} ({ev.pct(f['top5'][1])}) | | | | 5 | | | |")
    return "\n".join(rows)


def patient_panel(m, method: str, focus: int, positions: list):
    """Beispielpatient: dokumentierte Merkmale, die obersten Krankheiten nach Posterior mit der Menge des gewählten Verfahrens; die wahre Krankheit erst nach „Auflösen“."""
    n = len(positions)
    if n == 0:
        st.caption("In den gespeicherten Beispielpatienten dieser Messung gibt es keinen in dieser Klasse.")
        return
    if st.session_state.get("patient_idx", 1) > n:
        st.session_state["patient_idx"] = n   # die Klasse wechselt: der gewählte Patient darf nicht hinter der letzten Position liegen
    idx = (st.slider("Patient", 1, n, 1, key="patient_idx", help="Die ersten Patienten der gewählten Klasse aus der Testmenge der ersten Welt.") if n > 1 else 1) - 1
    reveal = st.toggle("Wahre Krankheit zeigen", key="patient_reveal", value=False)
    v = ev.example_view(m, positions, idx)
    row = v["methods"][method]
    st.markdown(f"**Dokumentierte Merkmale:** {v['kobs']} (Klasse {C.BIN_NAMES[0 if v['kobs'] <= 2 else 1 if v['kobs'] <= 4 else 2]}). "
                f"**Menge {C.METHOD_SHORT[method]}:** {row['size']} von {C.ND} Krankheiten.")
    true_id = v["true"] if reveal else None
    st.plotly_chart(V.fig_patient(v["top_ids"], v["top_p"], row["member"], true_id), width="stretch", key=f"patient_chart_{idx}_{reveal}_{method}_{focus}", config=V.CONFIG)
    if reveal:
        treffer = "; ".join(f"{C.METHOD_SHORT[mm]}: {'ja' if v['methods'][mm]['hit'] else 'nein'} ({v['methods'][mm]['size']} Krankheiten)" for mm in C.METHODS)
        st.caption(f"Wahre Krankheit: K{v['true'] + 1}, Rang {v['rank_true']} nach Posterior ({ev.dec(v['p_true'])}). Liegt sie in der Menge? {treffer}.")
    else:
        st.caption("Gezeigt werden nur die obersten acht Krankheiten; die Menge kann mehr enthalten. Ein einzelner Patient belegt nichts.")
