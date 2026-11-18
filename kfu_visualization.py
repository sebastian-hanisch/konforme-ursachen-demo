"""Plotly-Abbildungen (alle Achsen gesperrt, transparenter Hintergrund). Zahlen kommen aus der Messung, nie aus dem Text."""

import plotly.graph_objects as go

import kfu_constants as C
import kfu_results as RES

CONFIG = {"displayModeBar": False}
_LAYOUT = dict(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=50, r=20, t=40, b=60), legend=dict(orientation="h", y=-0.25))
_TARGET_LINE = dict(line_dash="dash", line_color="rgba(128,128,128,0.8)")


def _lock(fig: go.Figure) -> go.Figure:
    fig.update_layout(title_font_size=14)   # lange Titel werden auf dem Telefon sonst abgeschnitten
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _class_labels(shares) -> list:
    return ["alle Patienten"] + [f"{name}<br>({s:.0f} % der Patienten)" for name, s in zip(C.BIN_NAMES, shares)]


def fig_coverage_live(summary: dict, target: int) -> go.Figure:
    """Abdeckung gesamt und je Merkmalsklasse, drei Verfahren, Mittel ± Streuung über die Welten (diese Messung); gestrichelt das Ziel."""
    shares = [summary["LAC"]["share_b"][c][0] for c in range(3)]
    xs = _class_labels(shares)
    fig = go.Figure()
    for m in C.METHODS:
        v = summary[m]
        ys = [v["cov"][0]] + [v["cov_b"][c][0] for c in range(3)]
        err = [v["cov"][1]] + [v["cov_b"][c][1] for c in range(3)]
        fig.add_bar(name=C.METHOD_SHORT[m], x=xs, y=ys, error_y=dict(type="data", array=err, visible=True), marker_color=C.METHOD_COLORS[m],
                    hovertemplate="%{y:.1f} %<extra>" + C.METHOD_SHORT[m] + "</extra>")
    fig.add_hline(y=target, annotation_text=f"Ziel {target} %", annotation_position="top left", **_TARGET_LINE)
    fig.update_layout(barmode="group", yaxis_title="Abdeckung in % der Patienten", yaxis_range=[0, 105], title="Abdeckung der wahren Krankheit", **_LAYOUT)
    return _lock(fig)


def fig_size_live(summary: dict, n_diseases: int = C.ND) -> go.Figure:
    """Mittlere Größe der Menge gesamt und je Merkmalsklasse (Zahl Krankheiten), Mittel ± Streuung über die Welten."""
    shares = [summary["LAC"]["share_b"][c][0] for c in range(3)]
    xs = _class_labels(shares)
    fig = go.Figure()
    for m in C.METHODS:
        v = summary[m]
        ys = [v["size"][0]] + [v["size_b"][c][0] for c in range(3)]
        err = [v["size"][1]] + [v["size_b"][c][1] for c in range(3)]
        fig.add_bar(name=C.METHOD_SHORT[m], x=xs, y=ys, error_y=dict(type="data", array=err, visible=True), marker_color=C.METHOD_COLORS[m],
                    hovertemplate="%{y:.1f} Krankheiten<extra>" + C.METHOD_SHORT[m] + "</extra>")
    fig.update_layout(barmode="group", yaxis_title=f"Mittlere Menge (Krankheiten von {n_diseases})", title="Größe der Menge", **_LAYOUT)
    return _lock(fig)


def fig_coverage_cell(c: dict) -> go.Figure:
    """Abdeckung gesamt und je Klasse aus einer vorgerechneten Zelle (Mittel der beiden Mengen, zehn Welten)."""
    target = c["settings"]["target"]
    shares = [RES.pooled(c, "LAC", "share_b", k) for k in range(3)]
    xs = _class_labels(shares)
    fig = go.Figure()
    for m in C.METHODS:
        ys = [RES.pooled(c, m, "cov")] + [RES.pooled(c, m, "cov_b", k) for k in range(3)]
        fig.add_bar(name=C.METHOD_SHORT[m], x=xs, y=ys, marker_color=C.METHOD_COLORS[m], hovertemplate="%{y:.1f} %<extra>" + C.METHOD_SHORT[m] + "</extra>")
    fig.add_hline(y=target, annotation_text=f"Ziel {target} %", annotation_position="top left", **_TARGET_LINE)
    fig.update_layout(barmode="group", yaxis_title="Abdeckung in % der Patienten", yaxis_range=[0, 105], title="Abdeckung gesamt und je Klasse", **_LAYOUT)
    return _lock(fig)


def fig_shift() -> go.Figure:
    """Gesamtabdeckung ohne Verschiebung, mit verschobenem Vorab und mit verschobener Dokumentation (vorgerechnet, zehn Welten, Ziel 90 %)."""
    xs = ["keine Verschiebung", "Vorab verschoben", "Dokumentation verschoben"]
    cells = [RES.cell(RES.Settings(shift=s)) for s in (0, 1, 2)]
    fig = go.Figure()
    for m in C.METHODS:
        fig.add_bar(name=C.METHOD_SHORT[m], x=xs, y=[RES.pooled(c, m, "cov") for c in cells], marker_color=C.METHOD_COLORS[m], hovertemplate="%{y:.1f} %<extra>" + C.METHOD_SHORT[m] + "</extra>")
    fig.add_hline(y=90, annotation_text="Ziel 90 %", annotation_position="top left", **_TARGET_LINE)
    fig.update_layout(barmode="group", yaxis_title="Abdeckung in % der Patienten", yaxis_range=[0, 105], title="Abdeckung bei verschobenem Test", **_LAYOUT)
    return _lock(fig)


def fig_kb() -> go.Figure:
    """Mittlere Größe der Menge bei bekannter, bei aus 30 Fällen und bei aus 3 Fällen geschätzter Wissensbasis (vorgerechnet, zehn Welten, Ziel 90 %)."""
    xs = ["bekannt", "30 Fälle je Krankheit", "3 Fälle je Krankheit"]
    cells = [RES.cell(RES.Settings(kb=k)) for k in (0, 30, 3)]
    fig = go.Figure()
    for m in C.METHODS:
        fig.add_bar(name=C.METHOD_SHORT[m], x=xs, y=[RES.pooled(c, m, "size") for c in cells], marker_color=C.METHOD_COLORS[m],
                    hovertemplate="%{y:.1f} Krankheiten<extra>" + C.METHOD_SHORT[m] + "</extra>")
    fig.update_layout(barmode="group", yaxis_title=f"Mittlere Menge (Krankheiten von {C.ND})", title="Größe der Menge nach Wissensbasis", **_LAYOUT)
    return _lock(fig)


def fig_target_size() -> go.Figure:
    """Mittlere Größe der Menge bei Ziel 80, 90 und 95 Prozent (vorgerechnet, zehn Welten)."""
    xs = [f"Ziel {t} %" for t in C.TARGET_OPTIONS]
    cells = [RES.cell(RES.Settings(target=t)) for t in C.TARGET_OPTIONS]
    fig = go.Figure()
    for m in C.METHODS:
        fig.add_bar(name=C.METHOD_SHORT[m], x=xs, y=[RES.pooled(c, m, "size") for c in cells], marker_color=C.METHOD_COLORS[m],
                    hovertemplate="%{y:.1f} Krankheiten<extra>" + C.METHOD_SHORT[m] + "</extra>")
    fig.update_layout(barmode="group", yaxis_title=f"Mittlere Menge (Krankheiten von {C.ND})", title="Größe der Menge nach Ziel-Abdeckung", **_LAYOUT)
    return _lock(fig)


def fig_spread(rows: list) -> go.Figure:
    """Streuung der Abdeckung einer einzelnen Kalibrierung (Standardabweichung in Prozentpunkten): Simulation gegen Beta-Verteilung, Ziel 90 Prozent."""
    rows = [r for r in rows if r["target"] == 90]
    xs = [f"{r['n_cal']} Kalibrierpatienten" for r in rows]
    fig = go.Figure()
    fig.add_bar(name="Simulation", x=xs, y=[100 * r["sd"] for r in rows], marker_color=C.COLOR_LAC, hovertemplate="%{y:.2f} Punkte<extra>Simulation</extra>")
    fig.add_bar(name="Beta-Verteilung (exakt)", x=xs, y=[100 * r["beta_sd"] for r in rows], marker_color=C.COLOR_FIXED, hovertemplate="%{y:.2f} Punkte<extra>Beta</extra>")
    fig.update_layout(barmode="group", yaxis_title="Streuung der Abdeckung (Prozentpunkte)", title="Streuung der Abdeckung je Kalibrierung", **_LAYOUT)
    return _lock(fig)


def fig_patient(top_ids: list, top_p: list, member: list, true_id: int | None) -> go.Figure:
    """Posterior der obersten Krankheiten eines Beispielpatienten; gefüllt, wenn die Krankheit in der Menge des gewählten Verfahrens liegt; die wahre Krankheit ist hervorgehoben, wenn sie aufgelöst ist."""
    colors = [C.COLOR_TRUE if (true_id is not None and i == true_id) else (C.COLOR_LAC if mem else C.COLOR_FIXED) for i, mem in zip(top_ids, member)]
    fig = go.Figure(go.Bar(x=top_p, y=[f"Krankheit {i + 1}" + (" (in der Menge)" if mem else "") for i, mem in zip(top_ids, member)], orientation="h", marker_color=colors,
                           hovertemplate="%{x:.3f}<extra></extra>"))
    fig.update_layout(xaxis_title="Posterior (Naive Bayes)", xaxis_range=[0, 1], yaxis_autorange="reversed", title="Oberste Krankheiten nach Posterior", **{**_LAYOUT, "legend": None})
    return _lock(fig)
