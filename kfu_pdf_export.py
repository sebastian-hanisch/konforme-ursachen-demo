"""Auswertungs-PDF der aktuellen Messung (fpdf2, Kernschriften: keine Sonderzeichen außer Umlauten; Griechisch und Gedankenstrich ausgeschrieben)."""

import kfu_constants as C
import kfu_presets as P


def _ascii(text: str) -> str:
    """Kernschriften kennen nur Latin-1: Gedankenstrich, Minuszeichen, Kreuz und typografische Anführungszeichen ersetzen."""
    table = {"–": "-", "—": "-", "−": "-", "×": "x", "„": '"', "“": '"', "”": '"', "’": "'", "≥": ">=", "≤": "<=", "±": "+/-"}
    return "".join(table.get(ch, ch) for ch in text).encode("latin-1", "replace").decode("latin-1")


def build_pdf(settings, kennzahlen: dict, verdicts: tuple, n_worlds: int, n_test: int) -> bytes:
    from fpdf import FPDF  # lazy: nur beim Klick

    pdf = FPDF()
    pdf.set_auto_page_break(True, 15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(0, 9, _ascii("Konforme Ursachenmenge: Auswertung einer Messung"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(0, 5, _ascii("Lehrmodell mit erfundenen Daten, keine medizinische Beratung. Alle Zahlen gelten für diese Welt und diese Einstellung; "
                                "das Abdeckungsversprechen gilt im Mittel unter Austauschbarkeit von Kalibrier- und Testpatienten."), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "Einstellung", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    rows = [("Ziel-Abdeckung", P.label("target_select", settings.target)), ("Wissensbasis", P.label("kb_select", settings.kb)),
            ("Verschiebung im Test", P.label("shift_select", settings.shift)), ("Kalibriermenge", P.label("ncal_select", settings.ncal)),
            ("Zufalls-Seed", str(settings.seed)), ("Messung", f"{n_worlds} Welten x {n_test} Testpatienten")]
    for k, v in rows:
        pdf.cell(60, 6, _ascii(k))
        pdf.cell(0, 6, _ascii(v), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, _ascii("Abdeckung in Prozent, Menge in Krankheiten (Mittel ± Streuung über die Welten)"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "B", 8)
    heads = ((38, "Verfahren"), (38, "Abdeckung gesamt"), (38, "Abdeckung 1-2 Merkm."), (38, "Menge gesamt"), (38, "Menge 1-2 Merkm."))
    for w, h in heads:
        pdf.cell(w, 6, h, border=1)
    pdf.ln()
    pdf.set_font("Helvetica", "", 8)
    s = kennzahlen["summary"]
    for m in C.METHODS:
        v = s[m]
        vals = [C.METHOD_SHORT[m]] + [f"{a:.1f} +/- {b:.1f}".replace(".", ",") for a, b in (v["cov"], v["cov_b"][0], v["size"], v["size_b"][0])]
        for (w, _), val in zip(heads, vals):
            pdf.cell(w, 6, _ascii(val), border=1)
        pdf.ln()
    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "Verdikte", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    for _, text in verdicts:
        pdf.multi_cell(0, 5, _ascii(text), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)
    return bytes(pdf.output())
