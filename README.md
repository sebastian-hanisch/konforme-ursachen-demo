# Konforme Ursachenmenge – eine Menge statt einer Rangliste – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-konforme-ursachen-demo.streamlit.app/)** -->

Konzept-Demo der Linie **Erkennen unter Unsicherheit** auf der Website „Sebastian Hanisch – Operations Research und Machine Learning“ (Bereich Lernen). Statt einer Rangliste möglicher **seltener Krankheiten** nennt die Demo eine **Menge**, die die wahre Krankheit mit einer vorgegebenen **Ziel-Abdeckung** enthalten soll (**Split-Konformal**: eine Schwelle aus einer Kalibriermenge von Patienten mit bekannter Krankheit). Sie zeigt, **was dieses Versprechen zusagt, was es hält und wo es bricht**: Drei Verfahren (LAC, APS, Mondrian-LAC) werden auf derselben erfundenen Welt gemessen, mit einer festen Top-5-Liste als Vergleich. **Lehrmodell mit erfundenen Daten, keine medizinische Beratung** und keine Diagnoseempfehlung. Alle Aussagen gelten für diese Welt, diese Einstellungen und die gemessene Regel jedes Verfahrens.

**Voraussetzung der Garantie:** Das Versprechen ist garantiert **im Mittel über Patienten und über die Ziehung der Kalibriermenge**, wenn Kalibrier- und Testpatienten **austauschbar** sind (gleiche Verteilung). Ohne Austauschbarkeit kann es halten (in dieser Rechenwelt bei verschobenem Vorab) oder brechen (bei verschobener Dokumentation); die Garantie sagt darüber nichts. Es gilt nicht für einen einzelnen Patienten und nicht für jede Gruppe von Patienten. Einheiten: Abdeckung in Prozent der Patienten (gezählt werden Patienten mit mindestens einem dokumentierten Merkmal), Menge in Zahl der genannten Krankheiten (von 200).

**Bezug zu OR:** Eine Menge statt einer Entscheidung ist eine mögliche Form einer Prognose als Eingabe einer Planung: Sie sagt, wie viele Möglichkeiten offenbleiben (bei dünner Wissensbasis 79,2 von 200 Krankheiten, siehe Befunde). Die Frage, was ein Abdeckungsversprechen zusagt, ähnelt der bei Sicherheitsbeständen aus Quantilen (gleiche Quantil-Logik, in der Demo nicht gerechnet).

## Warum dieses Problem

Eine reine Rangliste sagt „die wahrscheinlichste Ursache ist X“ und schweigt darüber, wie sicher das ist. Eine konforme Menge verspricht stattdessen im Mittel (unter Austauschbarkeit): in mindestens Ziel Prozent der Fälle ist die wahre Ursache dabei; eine einzelne Kalibrierung kann darunter liegen (Kernfrage 4). Kernfragen: **Hält das Versprechen auch für jede Gruppe von Patienten? Wann bricht es? Was kostet es an Größe der Menge? Wie stark streut die Abdeckung mit der Kalibriermenge?** Die Antworten stehen vorgerechnet in den Befunden unten (10 Zellen, je zwei Mengen von 5 Welten); die Messung oben auf der Seite rechnet fünf Welten live nach.

## Befunde und Korrekturen gegenüber einer früheren Rechnung

Dieser Demo ging eine frühere Rechnung mit dem Zufallsgenerator von NumPy voraus (fünf Welten, ± Standardfehler). Ihre Zahlen stehen hier als Text und sind **nicht nachprüfbar** (anderer Generator, keine Datei im Repo). Die Messreihe der Demo rechnet mit dem eigenen SplitMix64 neu: je Zelle zwei Mengen von 5 Welten (Zufalls-Seed 1000 und 2000), 3.000 Testpatienten je Welt vor dem Entfernen von Patienten ohne dokumentiertes Merkmal. **Die Befunde bleiben der Richtung nach bestehen; die Gesamtabdeckung von LAC verschiebt sich in den sechs Fällen um höchstens 1,9 Punkte, und zwei Aussagen der früheren Rechnung gelten so nicht mehr.** Frühere Rechnung → Messreihe (zehn Welten):

| Fall (LAC, Ziel 90 %) | Abdeckung gesamt (%) | Menge gesamt | Abdeckung bei 1–2 Merkmalen (%) | Abdeckung bei 5+ Merkmalen (%) |
|---|---|---|---|---|
| Wissensbasis bekannt, gleiche Verteilung | 89,4 → 90,4 | 13,2 → 14,4 | 79,8 → 81,2 | 96,0 → 96,6 |
| Wissensbasis aus 3 Fällen je Krankheit | 90,7 → 90,8 | 82,5 → 79,2 | 85,7 → 85,8 | 94,4 → 94,8 |
| Wissensbasis aus 30 Fällen je Krankheit | 90,1 → 90,8 | 22,4 → 23,2 | 82,8 → 83,5 | 95,8 → 96,0 |
| bekannt, Vorab im Test verschoben (Zipf statt gleichverteilt) | 88,6 → 90,2 | 13,4 → 14,6 | 79,5 → 81,0 | 95,7 → 96,2 |
| bekannt, Dokumentation im Test verschoben (ρ 0,6 statt 0,3) | 70,0 → 71,9 | 19,0 → 21,1 | 60,9 → 62,6 | 84,9 → 86,4 |
| 3 Fälle, Dokumentation im Test verschoben | 77,4 → 76,8 | 89,2 → 85,8 | 73,3 → 72,2 | 84,7 → 84,7 |

| Verfahren | Abdeckung gesamt (%) | Menge gesamt | Abdeckung 1–2 / 3–4 / 5+ (%) | Menge 1–2 / 3–4 / 5+ |
|---|---|---|---|---|
| APS (Masse der höher gereihten Krankheiten) | 90,1 → 90,1 | 17,3 → 17,2 | 87,4 → 86,5 / 89,1 → 89,5 / 93,5 → 93,7 | 40,0 → 40,3 / 13,0 → 13,2 / 4,4 → 4,2 |
| Mondrian-LAC (eine Schwelle je Merkmalsklasse) | 89,8 → 90,9 | 17,4 → 20,9 | 88,7 → 92,0 / 89,5 → 90,3 / 91,0 → 90,7 | 44,5 → 58,4 / 11,7 → 12,3 / 2,6 → 2,4 |

- **Das verschobene Vorab senkt die Abdeckung im Mittel dieser Welt nicht nachweisbar (einzelne Welten weichen in beide Richtungen ab).** Die frühere Rechnung maß 88,6 ± 1,0 % (rund 1,4 Standardfehler unter dem Ziel, nicht deutbar), die Messreihe 90,6 % (Menge A) und 89,9 % (Menge B). Gepaart über die zehn Welten (dieselben Welten und Kalibrierungen wie im Standard) ist der Unterschied der Gesamtabdeckung von LAC −0,2 ± 0,3 Punkte (Standardfehler), je Welt von −1,5 bis +1,5 Punkten. Eine unabhängige Nachrechnung mit 200 weiteren Welten fand im Mittel +0,08 ± 0,09 Punkte und je Welt −4,8 bis +2,9 Punkte (nicht im Repo nachprüfbar). Ein Einfluss des Vorab auf die Abdeckung ist im Mittel nicht gezeigt; im Test ändert sich auch nur das Vorab der Patienten, nicht das des Modells.
- **Mondrian liegt im Standard im Mittel über zehn Welten in jeder Klasse beim Ziel oder darüber (92,0 / 90,3 / 90,7 %; in Menge A bei 3–4 und 5+ Merkmalen knapp darunter: 89,5 / 88,9 %), und die Menge bei wenigen Merkmalen ist größer als in der früheren Rechnung.** Die frühere Rechnung hatte bei 1–2 und 3–4 Merkmalen knapp unter dem Ziel gelegen: 88,7 % bei 1–2 Merkmalen und eine Menge von 44,5 statt 22,8 Krankheiten (das 2,0-fache); Messreihe: 92,0 % und 58,4 statt 25,5 (das 2,3-fache).
- **Die Gesamtmenge von LAC ist etwas größer als in der früheren Rechnung** (13,2 → 14,4 Krankheiten im Standard); die Abdeckung gesamt liegt in der Messreihe knapp über dem Ziel (90,4 ± 0,4 %, Standardfehler über zehn Welten), in der früheren Rechnung knapp darunter (89,4 ± 0,6 %); beide Abstände liegen unter zwei Standardfehlern.
- **Rechenzeit:** Die Messreihe (100 Welten) lief am 2026-11-18 in 78 s auf der Entwicklungsmaschine (unter Last durch parallele Läufe); eine unabhängige Nachrechnung am selben Tag brauchte rund 9 s, eine Live-Messung der App (5 Welten) unter Last 2 bis 7 s. Die Zeit schwankt stark mit Rechner und Last, ist kein Befund und steht in keinem Test.

## Modell

**Welt.** 200 Krankheiten und 100 Merkmale mit Zipf-verteilter Beliebtheit (Exponent 0,8); jede Krankheit hat 4 bis 12 Profilmerkmale mit Häufigkeit 0,95, 0,6, 0,3 oder 0,1. Ein vorhandenes Merkmal wird mit Wahrscheinlichkeit 1 − ρ aufgeschrieben (Dokumentationsverlust ρ =0,3), dazu kommt eine Hintergrundrate je Merkmal. Die Welt ist dieselbe wie in `phaenotyp-ranking-demo` (kopierte Module, Kopier-Test).

**Patienten und Modell.** Krankheit gleichverteilt, Merkmale unabhängig gegeben die Krankheit. Patienten ohne jedes dokumentierte Merkmal werden entfernt (Kalibrierung wie Test). Das Modell ist Naive Bayes mit den wahren Häufigkeiten oder mit Häufigkeiten aus gezogenen Fällen (Add-½-Glättung: zu jeder Zählung wird 0,5 addiert); sein Posterior ist die Eingabe aller drei Verfahren.

**Konforme Menge.** Aus 500 Kalibrierpatienten (Standard) mit bekannter Krankheit wird für jeden die Nichtkonformität der wahren Krankheit bestimmt; die Schwelle ist das ⌈(n + 1) · Ziel⌉-te kleinste Ergebnis (exakte Ganzzahlrechnung in ganzen Prozent; ist der Rang größer als n, ist die Schwelle unendlich und die Menge enthält alle Krankheiten). Die Menge eines Patienten enthält alle Krankheiten, deren Ergebnis höchstens die Schwelle ist. **Garantie:** sind Kalibrier- und Testpatient austauschbar, liegt die wahre Krankheit des Testpatienten mit Wahrscheinlichkeit mindestens Ziel in der Menge; bei stetigen Ergebnissen ohne Gleichstände höchstens um 1/(n + 1) darüber. Das gilt für jeden Posterior, auch einen schlechten; ein schlechter Posterior macht die Mengen in dieser Welt groß (3 Fälle je Krankheit: 79,2 statt 14,4 Krankheiten).

**Verschiebungen (im Test, nie in der Kalibrierung).** Vorab: im Test gilt ein Zipf-Vorab statt gleichverteilt, das Modell bleibt bei gleichverteilt. Dokumentation: im Test ist ρ = 0,6 statt 0,3, es fehlen also mehr Merkmale in der Akte. Beides verletzt die Austauschbarkeit.

**Messung.** Je Einstellung 5 Welten (SplitMix64: der ganzzahlige Zufallsstrom ist auf jeder Plattform derselbe; die Kennzahlen darüber können sich im letzten Bit unterscheiden, gemessen wurde unter Windows); Kalibrierpatienten und Testpatienten werden getrennt gezogen. Im Standard bleiben von 500 gezogenen Kalibrierpatienten im Mittel 490,9 und von 3.000 Testpatienten 2.934,9 (Patienten ohne dokumentiertes Merkmal entfallen). Vollständige Formeln: Expander **📐 Mathematische Formulierung** der App. Alle Parameter sind angenommen.

## Methodik

| Verfahren | Nichtkonformität eines Patienten und einer Krankheit | Grenze |
|---|---|---|
| **LAC** | 1 − Posterior der Krankheit | bei richtigem Posterior die kleinsten Mengen bei gegebener Abdeckung im Mittel (Messreihe: außer bei der dünnen Wissensbasis); die Abdeckung hängt an der Merkmalsklasse |
| **APS** (nicht randomisiert) | Masse aller strikt höher gereihten Krankheiten (Gleichstand nach Index) | die Menge ist ein Anfangsstück der Rangliste; ohne Zufallsrundung gilt die obere Schranke der Abdeckung nur ohne Gleichstände (die untere gilt weiter) |
| **Mondrian-LAC** | wie LAC, mit einer eigenen Schwelle je Klasse (1–2, 3–4, 5 und mehr dokumentierte Merkmale) | Abdeckung je Klasse nur für diese Klassen; keine Aussage über andere Gruppen |
| **feste Top-k-Liste** | (Vergleich, kein Versprechen) die k wahrscheinlichsten Krankheiten | die Abdeckung ist ein Ergebnis, kein Versprechen |

**Zählung der Messreihe.** Zellen sind Einstellungen (Ziel, Wissensbasis, Verschiebung, Kalibriermenge); je Zelle zwei Mengen von 5 Welten. **Standardfehler** = Streuung der Welten (n − 1) durch Wurzel aus der Zahl der Welten. **Verdikte** der App: „hält“, wenn die Abdeckung höchstens 2,0 Punkte unter dem Ziel liegt oder der Abstand unter 2,0 Standardfehlern bleibt (gepaart über die Welten); sonst „hält nicht“. Die Toleranz ist gesetzt, nicht abgestimmt; „hält“ heißt „nicht widerlegt“ (bei fünf Welten und großem Standardfehler gilt auch ein größerer Abstand als „hält“). Die App zeigt zwei Verdikte (Gesamtabdeckung und gewählte Klasse); diese Einteilung und die Toleranz sind gesetzt, nicht abgestimmt. Je Preset prüft `kfu_stories.py`, dass die Messreihe zeigt, wofür das Preset steht, in beiden Mengen. **Streuung der Abdeckung einer Kalibrierung** (Kernfrage 4): 1.000 Kalibrierungen werden mit Zurücklegen aus einem Vorrat von 19.632 Patienten einer Welt gezogen und die Abdeckung an 19.632 anderen Patienten derselben Welt gemessen; die Beta-Verteilung ist die exakte Verteilung für stetige Ergebnisse.

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen: Messreihe `data/kfu_results.json` (10 Zellen, je zwei Mengen von 5 Welten, Mittel über die 10 Welten; Standardfehler über dieselben Welten; Einheit: Abdeckung in Prozent der Patienten, Menge in Krankheiten je Patient). Jede Tabelle wird beim Erzeugen der README aus der Datei geschrieben (`tools/make_readme.py`) und von `tests/test_claims.py` auf Gleichheit geprüft. **Zählungen** nennen ihre Bezugsmenge: „8 Zellen ohne verschobene Dokumentation“ sind alle Zellen, in denen Kalibrier- und Testpatienten austauschbar sind oder nur das Vorab verschoben ist; „in 8 von 8“ heißt: in beiden Mengen.

**Die sechs Fälle** (LAC, Ziel 90 %, 500 Kalibrierpatienten; Anteil der Patienten in den Klassen 1–2 / 3–4 / 5+ Merkmale im Standard: 25,4 / 42,6 / 32,0 %):

| Fall (LAC, Ziel 90 %) | Abdeckung gesamt (%) | Menge gesamt | Abdeckung bei 1–2 / 3–4 / 5+ Merkmalen (%) | Menge bei 1–2 / 3–4 / 5+ Merkmalen | feste Top-5-Liste (%) |
|---|---|---|---|---|---|
| Wissensbasis bekannt, gleiche Verteilung | 90,4 ± 0,4 | 14,4 | 81,2 / 91,2 / 96,6 | 25,5 / 13,7 / 6,4 | 77,1 |
| Wissensbasis aus 3 Fällen je Krankheit | 90,8 ± 0,3 | 79,2 | 85,8 / 90,6 / 94,8 | 90,2 / 81,5 / 67,4 | 44,8 |
| Wissensbasis aus 30 Fällen je Krankheit | 90,8 ± 0,4 | 23,2 | 83,5 / 91,2 / 96,0 | 39,5 / 22,6 / 11,3 | 72,4 |
| bekannt, Vorab im Test verschoben (Zipf statt gleichverteilt) | 90,2 ± 0,5 | 14,6 | 81,0 / 91,2 / 96,2 | 25,7 / 13,9 / 6,7 | 76,6 |
| bekannt, Dokumentation im Test verschoben (ρ 0,6 statt 0,3) | 71,9 ± 0,9 | 21,1 | 62,6 / 77,0 / 86,4 | 27,9 / 17,2 / 10,7 | 49,8 |
| 3 Fälle, Dokumentation im Test verschoben | 76,8 ± 0,5 | 85,8 | 72,2 / 79,0 / 84,7 | 91,2 / 83,9 / 74,3 | 23,3 |

- **Das Versprechen hält im Mittel.** In 8 von 8 Zellen ohne verschobene Dokumentation liegt die Gesamtabdeckung von LAC höchstens 2 Punkte unter dem Ziel (APS 8, Mondrian 8); im Standard 90,4 ± 0,4 % bei Ziel 90 %.
- **Es hält nicht für jede Gruppe.** Bei 1–2 dokumentierten Merkmalen liegt die Abdeckung von LAC in 8 von 8 Zellen unter dem Ziel, in 6 um mehr als 5 Punkte; bei 5 und mehr Merkmalen liegt sie in 8 von 8 Zellen darüber. Im Standard sind es 81,2 % bei 1–2 und 96,6 % bei 5 und mehr Merkmalen (Ziel 90 %): Das Versprechen gleicht sich über die Klassen aus.
- **Eine dünne Wissensbasis macht die Menge groß, die Abdeckung hält.** Mit Häufigkeiten aus 3 Fällen je Krankheit liegt die Abdeckung bei 90,8 ± 0,3 %, die mittlere Menge bei 79,2 statt 14,4 Krankheiten (das 5,5-fache); die feste Top-5-Liste deckt 44,8 statt 77,1 % ab. Bei 30 Fällen: 90,8 % und 23,2 Krankheiten.
- **Eine verschobene Dokumentation bricht das Versprechen.** Mit ρ = 0,6 statt 0,3 im Test sinkt die Abdeckung von LAC auf 71,9 ± 0,9 % (Ziel 90 %); in 2 von 2 Zellen mit verschobener Dokumentation liegt sie um mehr als 10 Punkte unter dem Ziel (APS 2, Mondrian 2). Die Schwelle kommt aus der Kalibrierung und kennt die Verschiebung nicht; die mittlere Menge liegt bei 21,1 statt 14,4 Krankheiten. Mit der dünnen Wissensbasis und verschobener Dokumentation liegt die Abdeckung bei 76,8 %.

**Gegenmittel** (Ziel 90 %, Wissensbasis bekannt, 500 Kalibrierpatienten):

| Verfahren (Ziel 90 %, Wissensbasis bekannt) | Abdeckung gesamt (%) | Menge gesamt | Abdeckung bei 1–2 / 3–4 / 5+ Merkmalen (%) | Menge bei 1–2 / 3–4 / 5+ Merkmalen |
|---|---|---|---|---|
| LAC (1 − Posterior der wahren Krankheit) | 90,4 ± 0,4 | 14,4 | 81,2 / 91,2 / 96,6 | 25,5 / 13,7 / 6,4 |
| APS (Masse der höher gereihten Krankheiten) | 90,1 ± 0,3 | 17,2 | 86,5 / 89,5 / 93,7 | 40,3 / 13,2 / 4,2 |
| Mondrian-LAC (eine Schwelle je Merkmalsklasse) | 90,9 ± 0,4 | 20,9 | 92,0 / 90,3 / 90,7 | 58,4 / 12,3 / 2,4 |

**Gesamtabdeckung bei verschobenen Verteilungen im Test** (Ziel 90 %):

| Im Test | Abdeckung LAC (%) | Abdeckung APS (%) | Abdeckung Mondrian (%) |
|---|---|---|---|
| keine Verschiebung | 90,4 ± 0,4 | 90,1 ± 0,3 | 90,9 ± 0,4 |
| Vorab verschoben | 90,2 ± 0,5 | 90,1 ± 0,2 | 90,6 ± 0,4 |
| Dokumentation verschoben | 71,9 ± 0,9 | 74,3 ± 0,7 | 76,6 ± 0,7 |
| 3 Fälle, Dokumentation verschoben | 76,8 ± 0,5 | 76,6 ± 0,6 | 79,3 ± 0,7 |

- **APS gleicht die Klassen etwa zur Hälfte aus, Mondrian weitgehend.** Die Spannweite der Abdeckung über die drei Klassen (größte minus kleinste Abweichung vom Ziel, Mittel über die 8 Zellen und beide Mengen) beträgt bei LAC 14,9, bei APS 7,9 und bei Mondrian 2,1 Punkte (bei Mondrian in der Zelle mit 100 Kalibrierpatienten 3,6). Bei 1–2 Merkmalen liegt Mondrian in 0 von 8 Zellen in beiden Mengen unter dem Ziel (LAC 8, APS 8); in einzelnen Mengen liegt er in 1 von 16 Fällen darunter (um höchstens 0,1 Punkte). Alle drei Klassen liegen bei Mondrian in 7 von 8 Zellen höchstens 3 Punkte neben dem Ziel (Ausnahme: 100 Kalibrierpatienten).
- **Mondrian verschiebt die Fehlabdeckung in größere Mengen.** Bei 1–2 Merkmalen ist die Menge von Mondrian in 6 von 8 Zellen mehr als das 1,5-fache der Menge von LAC (in 8 von 8 größer); gesamt ist sie in 7 von 8 Zellen größer (Ausnahme: Wissensbasis aus 3 Fällen); bei 5 und mehr Merkmalen ist sie in 8 von 8 Zellen kleiner. APS hat gesamt in 7 von 8 Zellen eine größere Menge als LAC. **LAC hat die kleinsten Mengen, wenn der Posterior stimmt:** in 7 von 8 Zellen ist die Gesamtmenge von LAC kleiner als die von APS und die von Mondrian (Ausnahme: Wissensbasis aus 3 Fällen, dort mit schlechtem Posterior).
- **Bei verschobener Dokumentation bricht auch Mondrian** (Abdeckung 76,6 % bei Ziel 90 %): Die Klassen nach Merkmalszahl sichern die Austauschbarkeit nur innerhalb jeder Klasse, und die ist durch die Verschiebung verletzt (Deutung: bei ρ 0,6 hat ein Patient mit wenigen dokumentierten Merkmalen mehr vorhandene, aber nicht aufgeschriebene Merkmale als bei ρ 0,3; nicht getrennt gemessen).

**Menge gegen Ziel-Abdeckung** (Wissensbasis bekannt, 500 Kalibrierpatienten):

| Ziel | Abdeckung LAC (%) | Menge LAC | Menge APS | Menge Mondrian | Abdeckung LAC bei 1–2 / 3–4 / 5+ Merkmalen (%) |
|---|---|---|---|---|---|
| 80 % | 80,8 | 5,2 | 7,0 | 9,4 | 63,1 / 82,1 / 93,1 |
| 90 % | 90,4 | 14,4 | 17,2 | 20,9 | 81,2 / 91,2 / 96,6 |
| 95 % | 95,5 | 29,9 | 32,3 | 35,1 | 92,0 / 95,5 / 98,1 |

- Von Ziel 80 % auf 95 % wächst die mittlere Menge von LAC auf das 5,8-fache (5,2 → 29,9 Krankheiten). Eine feste Top-5-Liste deckt im Standard 77,1 % ab; die Menge für Ziel 90 % hat im Mittel 14,4 Krankheiten (das ist ein Ergebnis dieser Welt, keine Regel).

**Streuung der Abdeckung gegen die Kalibriermenge** (Ziel 90 %, Wissensbasis bekannt; Streuung der Welten: Standardabweichung der Gesamtabdeckung über die 5 Welten einer Menge; aus nur zehn Welten, die beiden Mengen weichen voneinander ab, die Ordnung stimmt mit der Beta-Verteilung unten überein):

| Kalibrierpatienten gezogen | davon im Mittel gerankt | Abdeckung LAC (%) | Streuung der Welten (Punkte, Mittel der beiden Mengen) | Menge LAC | Menge Mondrian |
|---|---|---|---|---|---|
| 100 | 98,7 | 90,1 ± 0,9 | 2,8 | 15,0 | 26,1 |
| 500 | 490,9 | 90,4 ± 0,4 | 1,3 | 14,4 | 20,9 |
| 2000 | 1.957,7 | 90,7 ± 0,2 | 0,6 | 14,7 | 19,0 |

**Abdeckung einer einzelnen Kalibrierung, Simulation gegen Beta-Verteilung** (1.000 Kalibrierungen je Zeile):

| Kalibrierpatienten | Ziel | Streuung in Punkten (Simulation / Beta) | Mittel in % (Simulation / Beta) | 5-%-Quantil der Simulation (%) | kleinster Wert der Simulation (%) |
|---|---|---|---|---|---|
| 100 | 90 % | 2,88 / 2,96 | 90,39 / 90,10 | 85,2 | 77,5 |
| 500 | 90 % | 1,34 / 1,34 | 90,17 / 90,02 | 88,0 | 84,3 |
| 2000 | 90 % | 0,71 / 0,67 | 90,21 / 90,00 | 89,0 | 88,3 |
| 500 | 80 % | 1,81 / 1,78 | 79,91 / 80,04 | 77,2 | 72,8 |
| 500 | 95 % | 0,99 / 0,97 | 95,15 / 95,01 | 93,4 | 91,1 |

- Die Abdeckung einer einzelnen Kalibrierung streut bei 100 Kalibrierpatienten mit 2,88 Punkten (Beta-Verteilung 2,96), bei 500 mit 1,34 (1,34) und bei 2000 mit 0,71 (0,67). Bei 100 Kalibrierpatienten lag die Abdeckung in 5 % der Kalibrierungen unter 85,2 % und im ungünstigsten von 1.000 Fällen bei 77,5 %. Das Versprechen gilt im Mittel über die Kalibrierungen; eine einzelne Kalibrierung kann darunter liegen.
- Die Simulation stimmt mit der Beta-Verteilung überein: die Streuungen weichen um höchstens 0,073 Punkte ab. Das Mittel der Simulation weicht um −0,13 bis +0,29 Punkte vom Mittel der Beta-Verteilung ab; der Standardfehler eines Anteils von 90 % bei 19.632 Patienten beträgt 0,21 Punkte (Deutung: Der Unterschied liegt in der Größenordnung des Stichprobenfehlers der beiden Hälften des Vorrats; nicht getrennt gemessen).

## Ehrliche Grenzen

- **Die Messreihe gilt für diese Welt:** 200 Krankheiten, 100 Merkmale, Naive-Bayes-Struktur, die gemessenen Reglerstufen; die Abbildungen der Kernfragen stammen aus den gemessenen Zellen, die Messung oben auf der Seite rechnet jede Kombination der Regler live (fünf Welten).
- **Das Versprechen ist eine Aussage im Mittel über Patienten und über die Ziehung der Kalibriermenge**, unter Austauschbarkeit von Kalibrier- und Testpatienten. Es sagt nichts über einen einzelnen Patienten und über Gruppen außer den drei Klassen nach Merkmalszahl, die Mondrian ausdrücklich bedient; andere Gruppen (Alter, Herkunft, Klinik) sind nicht gemessen.
- **Nur drei Verfahren:** gemessen sind LAC, APS (ohne Zufallsrundung) und Mondrian-LAC; Aussagen über andere Verfahren (verlustorientierte Mengen, Rückwärts-Konformal, adaptive Verfahren) sind keine Messung.
- **Fünf Welten je Menge und Messung:** Unterschiede unter der Toleranz oder unter zwei Standardfehlern werden nicht gedeutet; die Toleranz der Verdikte ist gesetzt, nicht abgestimmt.
- **Die Garantie braucht die wahre Krankheit der Kalibrierpatienten** und Austauschbarkeit; echte Diagnosen sind unsicher und verspätet, echte Verteilungen verschieben sich.
- **Die Merkmale sind in dieser Welt unabhängig gegeben die Krankheit gezogen;** bei abhängigen Merkmalen wäre Naive Bayes ein schlechteres Modell (nicht gemessen). Das Versprechen hängt nicht vom Modell ab, die Größe der Menge schon (Wissensbasis aus 3 Fällen: Abdeckung hält, Menge das 5,5-fache).
- **Nur an erfundenen Welten geprüft;** keine echten Patientendaten, keine echte Wissensbasis (HPO, Orphanet), keine Ontologie, keine medizinische Beratung.

## Verwandte Demos mit demselben mathematischen Modell

- [`phaenotyp-ranking-demo`](https://github.com/sebastian-hanisch/phaenotyp-ranking-demo): dieselbe Welt und derselbe Posterior von Naive Bayes; dort die **Rangliste** und ihr Recall@5 gegen das Orakel, hier die **Menge** mit Abdeckungsversprechen. Kopierte Module (`kfu_rng.py`, `kfu_stream.py`, `kfu_world.py`, `kfu_rankers.py`, `kfu_metrics.py`).
- [`forecast-interval-demo`](https://github.com/sebastian-hanisch/forecast-interval-demo): konforme Kalibrierung an den Fehlern einer Zeitreihen-Prognose (Nennabdeckung im Mittel, je Wochentag, im Zeitverlauf); gleiche Schwelle aus einer Kalibriermenge, dort für ein **Intervall** einer Zahl, hier für eine **Menge von Klassen**.
- [`entscheidungs-schranke-demo`](https://github.com/sebastian-hanisch/entscheidungs-schranke-demo): eine konforme Schranke auf die Kosten einer gewählten Entscheidung; gleiches Prinzip der Schwelle aus Kalibrierfehlern, dort mit der Entscheidung als Gegenstand.
- [`kalibrierung-schwelle-demo`](https://github.com/sebastian-hanisch/kalibrierung-schwelle-demo): aus einer Wahrscheinlichkeit eine Entscheidung; dort muss die Wahrscheinlichkeit als Häufigkeit stimmen, hier nicht: auch mit einer Wissensbasis aus 3 Fällen hält die Abdeckung im Mittel (Befunde), nur die Menge wird größer.
- [`grobe-merkmale-demo`](https://github.com/sebastian-hanisch/grobe-merkmale-demo): dieselbe Welt, Merkmale nur als Oberbegriff dokumentiert; dort die **Rangliste** mit Oberbegriffen, hier die **Menge** mit Abdeckungsversprechen (gleiche Linie Erkennen unter Unsicherheit).

## Verifikation (272 Tests)

- **Mini-Instanz** (`tests/test_mini_enumeration.py`): 3 Krankheiten, 3 Merkmale, 8 Muster; alle 13.824 geordneten Kalibriertripel der Größe 3 und alle Testpatienten werden aufgezählt; die exakte Abdeckung liegt bei LAC und APS mindestens bei ⌈(n + 1) · Ziel⌉ / (n + 1), bei Mondrian je Klasse mindestens beim Ziel; die Schwelle stimmt mit einem unabhängigen Rechenweg (Einfügesortierung, Ganzzahlrechnung) überein, die Mengen gehen in die exakte Abdeckung ein. Die obere Schranke gilt bei APS wegen der Gleichstände nicht, das ist ein Test.
- **Einheiten gegen Handrechnung** (`tests/test_conformal.py`): Schwelle (auch unendlich), Klassen, Nichtkonformität LAC und APS, Mondrian-Schwellen, Mengen, Auswertung.
- **Orakel** (`tests/test_oracle_konforme_ursachen.py`): (a) Schwelle gegen Einfügesortierung; (b) Eigenschaftstest der Garantie über 20 Welten je Einstellung, auch mit dünner Wissensbasis (3 Fälle), mit einer Negativkontrolle bei verschobener Dokumentation; (c) Beta-Verteilung gegen scipy, gegen eine Simulation mit gleichverteilten Ergebnissen und gegen die Simulation der Demo; (d) Mondrian-Abdeckung je Klasse (und die Verfehlung bei LAC als Negativkontrolle); (e) Monotonie der Menge im Ziel.
- **Zweige und Live** (`tests/test_live.py`): jede Stufe jedes Messreglers ändert mindestens ein Verfahren; die drei Verfahren weichen voneinander ab; die Verschiebungen ändern die Abdeckung; die Wissensbasis ändert die Mengengröße.
- **Messreihe** (`tests/test_results.py`): Aufbau, innere Stimmigkeit (Zusammenfassung gleich Mittel der Welten), Reproduktion der Voreinstellung (Menge A) mit Toleranz, Beta-Zeilen gegen die Formel.
- **Presets und Verdikte:** Abnahmekriterium je Preset gegen die Messreihe und jedes Kriterium an seiner Schwelle mit künstlichen Werten (`tests/test_stories.py`); jedes Verdikt in beiden Zweigen (`tests/test_evaluation.py`).
- **Oberfläche:** AppTest (jeder Preset-Button, jede Stufe jedes Reglers am Minimum und Maximum, Kombinationen, Permalink mit Einrasten und Begrenzen, Beispielpatient, PDF), Layout (Schnellstart, fester Kopf, aktives Preset hervorgehoben; jede Regleränderung hebt die Markierung auf), Footer, Laufzeit-Importe.
- **Kopierte Module:** `tests/test_stream.py`, `tests/test_world.py` und `tests/test_metrics.py` prüfen Zufallsstrom, Welt und Kennzahlen. Zwei Tests vergleichen die Kopien mit Dateien außerhalb dieses Repos (der Vorlage des Zufallsgenerators, byte-gleich, und den Modulen von `phaenotyp-ranking-demo`, bis auf das Präfix gleich) und überspringen sich, wenn diese Dateien fehlen; in der CI laufen sie deshalb nicht.
- **README:** wird aus `data/kfu_results.json` erzeugt; `tests/test_claims.py` prüft, dass sie dem Erzeugnis entspricht, die Testzahl stimmt und jede Zählung der Befunde der Messreihe entspricht. Zahl zu Test:

| Aussage der README | Test in `tests/test_claims.py` |
|---|---|
| Gesamtabdeckung hält in 8 von 8 Zellen (LAC, APS, Mondrian) | `test_gesamtabdeckung_haelt_in_allen_zellen_ohne_verschobene_dokumentation` |
| LAC bei 1–2 Merkmalen unter dem Ziel in 8, um mehr als 5 Punkte in 6; bei 5 und mehr darüber in 8 | `test_lac_klasse_1_2_unter_dem_ziel_und_klasse_5_darueber` |
| APS: Spannweite 7,9; Mondrian: Spannweite 2,1, 7 Zellen höchstens 3 Punkte neben dem Ziel | `test_gegenmittel_je_klasse` |
| Mondrian: Menge 6 / 7 / 8 von 8 | `test_mondrian_preis_in_der_menge` |
| dünne Wissensbasis: Abdeckung hält, Menge das 5,5-fache | `test_duenne_wissensbasis` |
| verschobene Dokumentation: Abdeckung mehr als 10 Punkte unter dem Ziel in 2 von 2 Zellen | `test_verschobene_dokumentation_bricht_das_versprechen` |
| verschobenes Vorab: kein Unterschied über zwei Standardfehlern | `test_verschobenes_vorab_ohne_nachweis` |
| Menge wächst von Ziel 80 % auf 95 % auf das 5,8-fache | `test_menge_waechst_mit_dem_ziel` |
| Streuung der Abdeckung nimmt mit der Kalibriermenge ab; Simulation gleich Beta-Verteilung | `test_streuung_der_abdeckung` |

- Keine Mutationstests (seit 2026-10-28 nicht mehr Teil der Demo-Prüfung). Nicht in der CI läuft die Messreihe selbst (`tools/sweep.py`; gespeicherte Laufzeit 78 s, siehe Rechenzeit oben).

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore`, `.streamlit/config.toml` | Git-Ausnahmen, Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App (Seitenaufbau nach DEMO-PLAYBOOK §2) |
| `kfu_constants.py` | Reglerstufen, feste Annahmen, Presets |
| `kfu_rng.py` | SplitMix64 (`decimal`-Ersatz für Logarithmus und Kosinus), wörtliche Kopie der Vorlage |
| `kfu_stream.py`, `kfu_world.py`, `kfu_rankers.py`, `kfu_metrics.py` | Zufallsstrom, Welt und Patienten, Naive Bayes, Recall (Kopien aus `phaenotyp-ranking-demo`) |
| `kfu_conformal.py` | Schwelle, LAC, APS, Mondrian-LAC, Mengen, Abdeckung und Größe |
| `kfu_garantie.py` | Streuung der Abdeckung gegen die Kalibriermenge, Beta-Verteilung |
| `kfu_live.py` | Live-Messung (fünf Welten), Verschiebungen, Zusammenfassung |
| `kfu_results.py` | Messreihe laden, Zellen, gepoolte Kennzahlen |
| `kfu_evaluation.py` | Verdikte und Kernfragen als reine Funktionen, Beispielpatient |
| `kfu_stories.py` | Abnahmekriterien der Presets |
| `kfu_presets.py`, `kfu_layout.py` | Permalink, Presets, fester Kopf |
| `kfu_visualization.py`, `kfu_ui_panel.py`, `kfu_pdf_export.py` | Abbildungen, Tabellen und Textbausteine, PDF-Auswertung |
| `data/kfu_results.json` | vorgerechnete Messreihe (10 Zellen) |
| `tools/sweep.py`, `tools/report.py`, `tools/make_readme.py` | Messreihe reproduzieren, berichten (mit den Zahlen der früheren Rechnung), README erzeugen |
| `requirements.txt`, `requirements-dev.txt` | Laufzeit-Bibliotheken, plus pytest und scipy |
| `tests/` | siehe Verifikation |

## Bewusst nicht enthalten

- **Verlustorientierte Mengen, gruppenbedingte Garantien über Mondrian hinaus, Zufallsrundung beim APS, Rückwärts-Konformal, verzögerte oder zensierte Daten:** gemessen sind nur LAC, APS (nicht randomisiert) und Mondrian-LAC.
- **Andere Gruppen als die Klassen nach Merkmalszahl** (Alter, Herkunft, Klinik): die Welt hat sie nicht.
- **Echte Daten, echte Wissensbasis, Ontologie:** erfundene Welt.
- **Eine Empfehlung oder Diagnose:** Lehrmodell, keine medizinische Beratung.

## Lokal ausführen

```bash
python -m venv venv
venv\Scripts\activate           # Linux/macOS: source venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly, NumPy und fpdf2 (scipy nur als Gegenprobe im Test).

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zur Reihe: [Erkennen unter Unsicherheit: Hinweis und Ursache](https://sebastianhanisch.net/konzepte-erkennen-unsicherheit.html).
