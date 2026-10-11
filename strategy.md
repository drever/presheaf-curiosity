# Strategie: Hat die Prägarben-Sicht einen algorithmischen Vorteil?

Stand: 11. Oktober 2026 (Zwischenfazit in Abschnitt 4a). Dieses Dokument hält fest, wie wir vorgehen, was wir bisher wissen und welche Fäden offen sind,
damit wir später wieder einsteigen können. Ergebnisse im Detail stehen in `README.md` und `results/`.

## 1. Ausgangsidee

Aus einem Gespräch mit Gemini: "Artificial Curiosity" (Schmidhuber) könnte auf Prägarben beruhen. Leinster: Jede Prägarbe ist ein
Kolimes von Repräsentierbaren (Dichtheit), analog zur Primfaktorzerlegung. Ein Agent, der Daten als Prägarbe auffasst, könnte seine
eigene Basiskategorie lernen: wiederverwendbare Teil-Kolimes ("Makros") finden, die Beschreibungslänge senken (MDL), und den
Lernfortschritt als Neugier-Belohnung nutzen.

Leitfrage: **Bringt die kategoriale Sicht einen messbaren Vorteil gegenüber dem, was man ohnehin tun würde** (Re-Pair auf Graphen,
SUBDUE, gSpan, GraphMDL)? Ein negatives Ergebnis ist ein gültiges Ergebnis.

## 2. Vorgehen bisher

1. **Demo** (Graphen, Teilgraph-Makros, Dreiecke, ein Agent, der seine Basis entdeckt): interaktive Seite als Claude-Artifact.
2. **Lerner** (`src/und.py`): MDL-Makrolerner auf vielen kleinen Komponenten. Ein Muster pro Runde. Kandidaten entstehen durch
   Verkleben zweier sich berührender Stücke der aktuellen Überdeckung (Pushout). Exakte Auswahl über die Gesamtbeschreibungslänge.
3. **Ehrliche Tests** gegen gSpan (+greedy MDL), SUBDUE (holderlb, gepatcht), GraphMDL (scikit-mine), auf Molekülen (RDKit-Löslichkeit),
   Kinships, UMLS und geplanten synthetischen Welten.
4. **Ablationen** statt Wettbewerb: Verkleben gegen Wachsen um eine Kante (`grow`), Äquivalenz an/aus, flache gegen hierarchische
   Wörterbuchkosten, mit/ohne Teilgraphen-Pool.

Methodische Regeln, die wir uns auferlegt haben:
* Ein gemeinsamer, neutraler Evaluator für alle Verfahren (`total_u`); Heimvorteil (wir optimieren, was wir messen) wird immer genannt.
* Hypothese und erwartete Richtung vorher aufschreiben; Kontrollen mit geplanter Struktur und ohne (`sym`/`nosym`).
* Mehrere Seeds, Streuung angeben; Gleichstand nicht als Sieg berichten.
* Zeitlimits und Bibliotheksfehler (GraphMDL-Abstürze) offen ausweisen, nicht stillschweigend herausrechnen.

## 3. Bisheriger Befund (Kurzfassung)

* **Auswahl nach MDL** erklärt den größten Teil des Vorsprungs gegenüber gSpan/SUBDUE.
* **Komposition (Verkleben)** gibt einen zusätzlichen Vorteil, der mit Mustergröße und Hierarchietiefe wächst
  (geplante Hierarchien: 17/48/63 Bit gegenüber `grow` bei Tiefe 1/2/3; echte Daten: 2.5-3.4 Bit auf Kinships, 7 Bit auf
  16-Atom-Molekülen, 0 auf UMLS). Teils ein Suchvorteil (`grow` bleibt in lokalen Optima hängen), teils Kodierung.
* **Hierarchische Wörterbuchkosten** (Muster als Verweise auf Teile) schrumpfen Wörterbücher 2-4x und helfen auf Molekülen (2.8-3.5 Bit).
* **Äquivalenz von Makros** (Umkehrrelationen, geschätzt per MDL) bringt viel, wenn die Daten eine saubere Symmetrie haben
  (synthetisch: ca. 17 Bit bei 40 Komponenten), nichts bis leicht negativ auf Kinships.
* **GraphMDL** ist in kleinen Mengen ein ernstzunehmender Gegner, rechnet aber in der Python-Fassung bei 700 Komponenten nicht.
  Die Java-Fassung war von hier nicht erreichbar.
* Bisher **kein Beleg**, dass die Prägarben-Sicht auf echten Graphen mehr liefert als Re-Pair mit MDL-Auswahl.

## 4. Strukturen höherer Ordnung (aktueller Faden)

Beobachtung: Unser Ansatz lebt im Fragment der Kolimes (Pushouts). Ein Prägarbentopos ist aber kartesisch abgeschlossen:
Produkte A x B, Exponentiale B^A mit (B^A)(c) = Hom(y(c) x A, B), Unterobjekt-Klassifikator. Das nutzen wir bisher nicht.

Angriffsplan, in dieser Reihenfolge:

1. **Produkte (jetzt).** Daten aus Gittern, Leitern, Zylindern = Produkte kleiner Ketten. Wörterbucheinträge dürfen Ausdrücke sein:
   `A x B` zweier früherer Einträge. Zwei Messungen:
   * Kosten: ein Produkt kostet zwei Verweise plus ein Operator-Bit statt seiner Kantenliste.
   * **Kompositionale Generalisierung:** Das Training enthält nur einen Teil der Faktorpaare; im Test kommen ungesehene Paare vor.
     Ein Wörterbuch mit Produkt-Abschluss (alle Produkte der gewählten Faktoren sind implizit enthalten) sollte sie überdecken können,
     ein reines Kolimes-Wörterbuch nicht.
   Erwartung: Vorteil des Abschlusses auf ungesehenen Paaren; kein Vorteil auf gesehenen. Widerlegt, wenn der Abstand auf
   ungesehenen Paaren nicht größer ist als auf gesehenen.
2. **Parametrisierte Makros** (Löcher): Pushout entlang einer Schnittstelle H -> P, ähnlich den Abstraktionen in DreamCoder/Stitch.
   Test auf den geplanten Hierarchien.
3. **Relationskomposition** als Redundanz in den Daten (Tante = Schwester o Mutter), analog zum Regelmining (AMIE) auf Kinships/UMLS.
4. **Exponentiale im engeren Sinn:** Zustände S, Aktionen A, Übergang S x A -> S, curryfiziert zu A -> S^S. Das ist die Brücke zurück zum
   Agenten (Neugier über die Vorhersagbarkeit von Verhaltensräumen). Am weitesten entfernt, am nächsten an der Ausgangsidee.

### Ergebnis Schritt 1 (Produkte), `src/e17.py`, `src/und4.py`, `results/e17_*`

Welt: 5 horizontale + 5 vertikale Ketten (Relationsklassen 0-5 / 6-11), 25 mögliche Paare, davon 15 im Training, 10 nie gesehen;
jede Komponente enthält 2 Gitter (kartesisches Produkt eines Paares) plus 4 Rauschkanten. Testbits pro Komponente, Mittel über 5 Seeds.

| Methode | n=20 ges. | n=20 unges. | n=50 ges. | n=50 unges. | n=150 ges. | n=150 unges. |
|---|---|---|---|---|---|---|
| Kleben (glue_hier) | 306.7 | 384.7 | 301.9 | 368.0 | 304.3 | 368.8 |
| Wachsen (grow_hier) | 326.1 | 370.0 | 331.9 | 353.2 | 328.1 | 347.2 |
| Abschluss, Faktoren aus Kleben-Wörterbuch (nur Kreuzprodukte) | 289.2 | 365.1 | 278.3 | 344.1 | 272.8 | 352.9 |
| Abschluss, Pfad-Faktoren, Klassen vorgegeben | 263.7* | 341.0* | 260.2 | 329.8 | 247.4 | 317.2 |
| **Abschluss, voll datengetrieben (`prod_auto`)** | 236.1 | 329.2 | 214.1 | 257.3 | 204.5 | 230.3 |
| Orakel (wahre Ketten als Faktoren) | 210.6 | 229.6 | 212.0 | 225.6 | 211.1 | 224.6 |

(*Zeile "Klassen vorgegeben" ist hier die mit gelernten Klassen, `prod_data_learnedcls`; mit vorgegebenen Klassen ähnlich.)

Voll datengetrieben (`prod_auto`) heißt: (1) Relationsklassen aus **Quadraten** (4-Zyklen mit gleichen Gegenkanten) lernen, die Gegenüber-Beziehung der Labels
wird gewichtet 2-gefärbt; (2) Faktor-Kandidaten sind die **Fasern**, also die Zusammenhangskomponenten des auf eine Klasse eingeschränkten Graphen,
mindestens in 2 Komponenten vorhanden; (3) Auswahl per MDL, Einzelschritte vor Paarschritten (ein Faktor allein erzeugt mit Kreuzprodukten nichts).

Lesart, ehrlich:
* **Hypothese bestätigt:** Mit Produkt-Abschluss verschwindet der Abstand zwischen gesehenen und ungesehenen Faktorpaaren fast. Bei n=150 liegt die
  automatische Methode auf ungesehenen Paaren bei 230 gegenüber 225 (Orakel) und 369 (Kleben): rund 140 Bit weniger, ohne Klassen-Vorwissen.
* **Das ist kompositionale Generalisierung, die ein reines Kolimes-Wörterbuch nicht leistet.** Kleben bleibt bei 304 vs 369 (gesehen/ungesehen).
* **Abhängigkeit von n:** Bei n=20 fehlen die Fasern (die Schwelle von 2 Komponenten und seltene Ketten); Gewinn auf ungesehenen Paaren dort 55 Bit,
  bei n=50 111, bei n=150 138. Das ist die erwartete Richtung (mehr Daten, mehr Kompositionalität).
* **Fehler auf dem Weg, korrigiert:** (a) Quadrat-Erkennung hatte Kanten falsch verglichen; (b) BFS-Färbung ließ ein Rauschquadrat ein Label falsch färben und
  entfernte damit alle Ketten mit diesem Label (n=50, Seed 3: 348 statt 244); (c) 10%-Häufigkeitsschwelle verwarf seltene Ketten.
* **Einschränkungen:** Die Welt ist von uns gebaut und genau die Struktur, die der Algorithmus sucht (Produkt aus zwei Relationsklassen, Ketten als
  Faktoren, Gegenkanten gleich beschriftet). Lerner und Auswertung teilen die Kostenfunktion. Die Methode wählt 12-14 Faktoren, davon 8-10 echte; die
  übrigen sind harmlose Zusatzfaktoren (Maximum maxf=14 wird bei n=150 erreicht). Rauschen: nur 4 Kanten pro Komponente.
* **Nicht gemessen:** gSpan/SUBDUE auf dieser Welt, echte Daten mit Produktstruktur (Gitter, Moleküle mit Ringen), mehr Rauschen,
  Faktoren mit mehr als zwei Klassen, nicht-kartesische Verklebungen von Produkten.

### Ergebnis Schritt 1b: Robustheit gegen Rauschen und gSpan als Gegner (`src/e18.py`, `results/e18_*`)

Gleiche Welt, Rauschkanten pro Komponente 4 / 12 / 24 (Gitter belegen 20-40 Kanten); Testbits, ungesehene Paare (gesehene in Klammern), Mittel über 3 Seeds
(Rauschen 4: nur 1 Seed, n=50).

| Rauschen | n | Kleben | prod_auto | Orakel | gSpan+MDL |
|---|---|---|---|---|---|
| 4 | 50 | 324 (272) | 210 (195) | 187 (192) | 410 (369) |
| 12 | 50 | 473 (409) | 375 (324) | 337 (310) | 633 (525), 2 von 3 Seeds |
| 12 | 150 | 478 (400) | 330 (304) | 332 (309) | 597 (510) |
| 24 | 50 | 612 (538) | 560 (499) | 466 (449) | Timeout (400 s) |
| 24 | 150 | 606 (534) | 491 (465) | 471 (446) | 649 (626), 1 von 3 Seeds |

Lesart: Bei mittlerem Rauschen (12) hält der Vorteil des Abschlusses (ungesehen 100-150 Bit unter Kleben), bei n=150 liegt er auf dem Orakel.
Bei starkem Rauschen (24) schrumpft er auf 45-115 Bit und bleibt ein gutes Stück vom Orakel entfernt, bei n=50 ist die Faktorfindung dann der Engpass
(Fasern werden durch Rauschkanten verändert, Quadrate seltener). gSpan mit MDL-Auswahl findet hier fast nichts Brauchbares (große Gitter überschreiten
Knotenlimit und Laufzeit, bei Rauschen 24 Timeouts); auf ungesehenen Paaren liegt es bei oder über dem leeren Wörterbuch. Das ist ein Vergleich mit einem
Gegner, der für diese Welt schlecht passt (kein Produkt-Abschluss, Grenzen für Knoten und Laufzeit), kein Beweis, dass kein Miner es kann. SUBDUE und GraphMDL
wurden hier nicht gemessen.

### Ergebnis Schritt 1c: echte Straßendaten (negativ), `src/streets.py`, `e19*.py`, `results/e19*`

Daten: Das GitHub-Repo `amoraschi/spain-cities-geojson` (OSM-Straßen der spanischen Provinzhauptstädte, `highway`-Tag je Weg). Direkter OSM-Zugriff
(Overpass, Geofabrik, Nominatim) und SNAP sind aus dem Container nicht erreichbar, nur GitHub und PyPI. Das Valencia-File im Repo ist leer.
Aufbereitung: Kreuzungsgraph (Knoten = Endpunkte und gemeinsam genutzte Punkte), nur Fahrstraßen (ohne Fuß-/Radwege, die sonst 70% der Kanten ausmachen),
Kantenlabel = Straßenklasse (groß / mittel / Wohn- / Service). Komponenten = räumliche Fenster (0,004 Grad, ca. 26 Kanten im Mittel, höchstens 40 Knoten).
Training: 60-100 Fenster aus Barcelona; Test: 100 Fenster aus Barcelona (ausgelassen) sowie Madrid, Zaragoza, Sevilla.

* **Straßen sind komprimierbar:** Testbits 372 (leer) -> 258 (Kleben), Muster bis 7-10 Kanten. Kleben und Wachsen sind gleich gut (258,3 vs 257,3 in Barcelona).
* **Gitterstruktur gibt es:** 45-60% der Fenster enthalten 4-Zyklen, rund 25% mehrere.
* **Produkt-Abschluss bringt nichts:** mit Straßenklassen als Labels (Faktoren: einfarbige Pfade, 3 Seeds, n=60) 260,1 vs 259,8 / 251,1 vs 251,1 / 256,9 vs 256,6 (Barcelona);
  in der reinen Geometrie (alle Kanten gleiches Label, 3 Seeds, n=100) 223,2 vs 222,7 / 221,3 vs 221,4 / 217,5 vs 217,5. Auf den anderen Städten ebenso (Differenz höchstens 1,6 Bit).
* **Deutung (nicht getestet, nur plausibel):** (1) Die Gitter in den Fenstern sind klein und unregelmäßig (nicht-induzierte Einbettung, fehlende Kanten, gemischte Klassen),
  exakte Produkte großer Pfade kommen selten vor; (2) kleine Gitterbausteine (Quadrat, Leiter) werden vom Kleben bereits billig abgedeckt. (3) In echten Rastern hängt die
  Straßenklasse an der Reihe (Straße), nicht an der Position entlang der Straße; das ist kein Produkt mit Faktor-Labels, wie es unsere synthetische Welt baut. Ein passenderes
  Modell wäre Gitterform x Beschriftungsfunktion. Das haben wir nicht gebaut.
* **Konsequenz:** Der Vorteil des Produkt-Abschlusses ist bisher nur auf der von uns konstruierten Welt belegt. Auf echten Straßen hat er sich nicht gezeigt.

### Ergebnis Schritt 1d: Modell "Gitterform x Beschriftungsfunktion" auf Straßen, `src/e20.py`, `e20b.py`, `results/e20*`

Modell: Zwei Schichten. (1) Form: Graph ohne Labels (R=1), Wörterbuch wie bisher. (2) Beschriftung: Label jeder Kante, bedingt auf Labels bereits codierter Nachbarkanten
(BFS-Reihenfolge; Kontext = Labelpaar der ersten codierten Kante an jedem Endpunkt; Tabelle aus dem Training, Laplace 0,5). Vergleich mit dem bisherigen markierten Kleben.
Straßenfenster wie in 1c (n=100, 3 Seeds, Test auf Barcelona-Ausgelassenen und drei anderen Städten).

* **Zerlegung:** Form (R=1) kostet ca. 223 Bit (leer 299), Beschriftung ca. 48 Bit (iid) bzw. 31 Bit (Nachbarkontext). Der Produkt-Abschluss auf der Form bringt nichts (1c).
  Alles, was zu holen ist, liegt in der Beschriftungsschicht, höchstens ca. 17-20 Bit von ca. 255.
* **Nachbarkontext hilft:** Label-Kosten 48 -> 31 Bit pro Fenster (Barcelona, ähnlich in den anderen Städten). Straßen wechseln ihre Klasse selten mitten im Verlauf.
* **Gesamt (Testbits pro Fenster), markiertes Kleben vs Form+Beschriftung (Nachbarkontext), Mittel über 3 Seeds:**
  Barcelona 256,2 vs 251,5 | Madrid 237,4 vs 229,7 | Zaragoza 208,3 vs 201,8 | Sevilla 250,9 vs 243,6. Gewinn 3,6-8,4 Bit pro Fenster (1,5-3,5%) in jedem der 12 Fälle (4 Städte x 3 Seeds).
  Form+Beschriftung mit iid-Labels (ohne Kontext) ist **schlechter** als markiertes Kleben (ca. 268 vs 256 in Barcelona): Die markierten Muster fangen Labelkorrelationen schon teilweise ab.
* **Kosten:** Wörterbuch- plus Parameterbits sind höher (Kontexttabelle ca. 400-430 Bit gegen ca. 30 Bit bei iid, bei insgesamt 100 Trainingsfenstern, also ca. 4 Bit pro Fenster
  bei vollem Ansatz; netto bleibt auf den Trainingsdaten ein Gewinn von ca. 0,5-3 Bit pro Fenster, auf Testdaten, wo Wörterbuch nicht zählt, 3,6-8,4).
* **Produktgedanke geprüft und verworfen:** Kontext "Label der Gegenkante im Quadrat" (Beschriftung hängt an der Reihe): 47,6 vs 48,3 (iid) bzw. 31,2 vs 30,9 (mit Nachbarkontext).
  Die Beschriftung hängt an der Kontinuität der Straße (Nachbarschaft), nicht an Produktstruktur.
* **Einordnung:** Das ist ein generischer Kontextmodell-Gewinn (jede Methode könnte Nachbarlabels als Kontext nutzen), kein Vorteil der Prägarbensicht. Es zeigt nur, dass unsere
  markierten Muster Labelkontinuität nicht optimal ausnutzen.
* **Offen:** gSpan/SUBDUE/GraphMDL auf Straßen nicht gemessen; ein Gegner mit demselben Beschriftungsmodell würde den Gewinn ebenfalls erhalten.

## 4a. Zwischenfazit (11. Oktober 2026)

**Frage:** Hat die Prägarben-Sicht (Graph als Kolimes repräsentierbarer Stücke, Makros als Pushouts, jetzt auch Produkte) einen messbaren algorithmischen Vorteil
gegenüber dem, was man ohnehin täte (Re-Pair/gSpan/SUBDUE/GraphMDL mit MDL-Auswahl)?

**Kurzantwort, Stand heute:** Auf unseren synthetischen Welten ja, auf echten Daten bisher nein oder nur klein und nicht spezifisch.

### Was belegt ist, nach Stärke des Belegs

| Aussage | Beleg | Einschränkung |
|---|---|---|
| MDL-Auswahl erklärt den Großteil des Vorsprungs vor gSpan/SUBDUE | mehrere Datensätze, Seeds | nicht prägarben-spezifisch (jeder Miner kann MDL-Auswahl) |
| Verkleben (Pushout) schlägt Wachsen um eine Kante, Vorsprung wächst mit Hierarchietiefe | synthetische Hierarchien: 17/48/63 Bit bei Tiefe 1/2/3 | zum Teil Suchvorteil gegen ein lokal hängendes `grow` |
| Verkleben auf echten Daten | Kinships 2,5-3,4 Bit, Moleküle bis 7 Bit, UMLS 0 | klein (ca. 1-3%), abhängig vom Datensatz |
| Hierarchische Wörterbuchkosten | Moleküle 2,8-3,5 Bit | nur dort |
| Äquivalenz (Umkehrrelation) | synthetisch bis ca. 17 Bit bei sauberer Symmetrie | Kinships: nichts bis leicht negativ |
| **Produkt-Abschluss ermöglicht kompositionale Generalisierung** | synthetische Gitterwelt, 5 Seeds: ungesehene Faktorpaare 230 vs 369 Bit (n=150), Orakel 225; hält bei mittlerem Rauschen | Welt ist genau die gesuchte Struktur gebaut; Faktoren nur mit Klassenlernen aus Quadraten und Fasern gefunden |
| Beschriftung bedingt auf Nachbarlabels (Straßen) | 3,6-8,4 Bit pro Fenster, 12 von 12 Fällen | **generisch**, kein Prägarben-Vorteil |

### Was widerlegt oder nicht gezeigt ist

* **Produkt-Abschluss auf echten Straßen: kein Gewinn** (höchstens 1,6 Bit Unterschied, markiert wie unmarkiert, 3 Seeds). Gründe vermutlich: kleine unregelmäßige Gitter,
  Quadrate und Leitern deckt das Kleben schon billig ab, Straßenklasse hängt an der Straße, nicht an der Position.
* **"Beschriftung hängt an der Reihe" (Produktgedanke für Labels):** Kontext Gegenkante im Quadrat bringt nichts.
* Kein Vorteil gegenüber GraphMDL/SUBDUE/gSpan **mit denselben Zusatzmodellen** gemessen; auf der Gitterwelt und den Straßen war gSpan+MDL nur eingeschränkt vergleichbar (Knotenlimit, Zeitlimit),
  GraphMDL und SUBDUE dort gar nicht gelaufen.
* Höhere Ordnung über Produkte hinaus (parametrisierte Makros, Exponentiale, Simplizes) ist **ungetestet**.

### Ehrliche Einordnung

1. Der Kern "Kolimes aus Stücken, MDL-Auswahl" ist ein solides, aber bekanntes Verfahren; der Prägarben-Rahmen liefert dafür die Sprache, bisher keinen nachweisbaren Zusatzgewinn.
2. Der einzige Befund, der **nur** mit einer kategorialen Idee zu erklären ist (Abschluss unter Produkten, damit Generalisierung auf ungesehene Kombinationen), gilt bisher nur dort, wo die Daten
   exakt diese Struktur haben. Das ist ein Machbarkeitsbeleg, kein Beleg für Nutzen in der Praxis.
3. Alle Tests teilen Kostenfunktion von Lerner und Auswertung (Heimvorteil), die Welten sind von uns gebaut, Seeds sind wenige (3-10).
4. Die Kernfrage hängt jetzt an **Daten mit exakter, großer Produkt- oder Parametrisierungsstruktur**; Straßenfenster sind dafür offenbar zu klein und zu unregelmäßig.

### Mögliche nächste Schritte (zur Entscheidung)

* **A. Echte Daten mit exakter Produktstruktur suchen** (Schaltpläne/Chip-Layouts, Gitter-Simulationen, Zellularautomaten-Raumzeit, Netzwerk-Topologien wie Torus/Hypercube); nur GitHub und PyPI sind von hier erreichbar.
* **B. Parametrisierte Makros** (Schritt 2, Löcher/Schnittstellen): ein anderer Mechanismus, könnte auf Molekülen und Wissensgraphen tragen, wo Produkte nicht vorkommen.
* **C. Relationskomposition** auf Kinships/UMLS (Schritt 3), Vergleich mit AMIE-artigen Regelminern: ein Gegner, der die Frage direkt trifft.
* **D. Gegner gleichstellen:** Beschriftungs- und Äquivalenzmodelle auch an SUBDUE/GraphMDL/gSpan anbauen, damit der Vergleich nicht an Zusatzmodellen hängt.
* **E. Abbruchkriterium festlegen:** wenn A-C auf echten Daten ebenfalls keinen Vorsprung liefern, das Projekt als "Rahmen ja, Vorteil nein" dokumentieren.

### Ergebnis Schritt 1e: Chip-Netzlisten (Datensuche und erste Messung), `src/netlist.py`, `src/e21.py`, `results/e21_*`

**Datenfund** (nur GitHub und PyPI sind erreichbar): `ispras/hdl-benchmarks` (ISCAS85 `.bench` inkl. c6288 = 16x16-Array-Multiplizierer, LGSynth91, IWLS05, Quip-Designs wie
Barrel-Shifter, Crossbar, Multiplexer) und `lsils`/`nbulsi` EPFL-Benchmarks (`arithmetic/*.blif`: adder, bar, multiplier, max, sin, square, sqrt, div, log2).
Aufbereitung: Knoten = Signale/Gatter, Kante = Verdrahtung (ungerichtet), Label = Typpaar (Treiber, Senke) bzw. bei AIG (Quelle ist Eingang?, Eingang invertiert?).
Komponenten = BFS-Fenster um zufällige Gatter (20 Knoten, mindestens 8 Kanten, mehrfache Überlappung möglich).

**Produktstruktur auf Gatterebene:** Rohe 4-Zyklen sind selten und liegen meist **in** Zellen (z.B. XOR aus 4 NANDs in c1355, Gegenkanten fast immer gleich beschriftet),
nicht zwischen Zellen. c6288: im Mittel 2,6 Quadrate pro 40-Kanten-Fenster. Das Gitter des Array-Multiplizierers (Volladdierer in einem Schrägraster, in
schiefen Koordinaten ein Produkt zweier Pfade) existiert erst auf **Zellebene**, nicht auf Gatterebene.

**Messung auf c6288** (n=40 Trainingsfenster, 3 Seeds, Test = 100 ausgelassene Fenster derselben Schaltung; Testbits pro Fenster).
*Korrektur:* Die erste Fassung orientierte die Kanten nach Knotennamen statt Treiber -> Senke; da das Framework gerichtet rechnet, passten gleiche Zellen mit
verschiedener Namensreihenfolge nicht aufeinander. Die Zahlen unten sind mit korrekter Orientierung neu gemessen (frühere Zahlen: Kleben 169,5/152,9/170,7, Wachsen 222,6/209,1/221,1).

| Seed | leer | Kleben (unser Lerner) | Wachsen um 1 Kante | SUBDUE (MDL-Abschnitt) | gSpan (maxv 11, Muster bis 6 Kanten) |
|---|---|---|---|---|---|
| 0 | 422,5 | 153,6 | 199,8 | 219,8 | 257,5 |
| 1 | 427,8 | 158,2 | 205,9 | 200,7 | 233,2 |
| 2 | 433,7 | 159,4 | 212,2 | 209,0 | 258,5 |

* **Kleben liegt 46-53 Bit (23-25%) unter Wachsen und 41-66 unter SUBDUE** und 75-105 unter gSpan; der Kompositionsvorteil bleibt auf echten Daten bestehen und ist hier der größte bisher.
* **SUBDUE liegt im Bereich von Wachsen** (Streuung von Lauf zu Lauf ca. 10 Bit: bei Seed 0 gaben zwei Läufe 205,5, 219,8 und 225,2). Es findet Muster bis 26 Kanten, aber deren Auswahl und Instanzzählung sind schlechter.
* **gSpan ist auf diesen Fenstern praktisch nicht anwendbar:** Mit Knotenlimit 26 und 17 (bond-as-node: ca. 12 bzw. 8 Kanten) und Support 20% brach der Lauf in jedem Seed nach 500-900 s ab (Zeitlimit); nur mit Knotenlimit 11 (Muster bis 6 Kanten) ergeben sich Zahlen. Das ist ein
  Vergleich mit gSpan unter eingeschränkten Bedingungen; mit Limit-Muster bis 6 Kanten kann es die Zellen von bis zu 12 Kanten prinzipiell nicht abbilden.
* **Produkt-Abschluss auf Gatterebene: kein Faktor gewählt**, also kein Effekt (erwartet, siehe oben).
* **Kein Transfer auf andere Schaltungen** (c1355, c499, c880, c1908: Kleben 0-30 Bit besser als leer, ähnlich Wachsen): c6288-Zellen kommen dort nicht vor.
* **Einschränkungen:** Eine einzige, extrem regelmäßige, von Hand entworfene Schaltung; BFS-Fenster überlappen (Trainings- und Testfenster derselben Schaltung teilen Zellen); Obergrenze 12 Kanten für unseren Lerner schneidet die Zelle vermutlich;
  die Gegner wurden mit den vorhandenen Wrappern betrieben (greedy MDL-Auswahl der gSpan-Kandidaten, SUBDUE mit 20 Iterationen), ohne Parameter-Tuning; wir optimieren dieselbe Kostenfunktion, mit der wir messen (Heimvorteil).
  Der AIG-Multiplizierer (nur 4 Labels) war für den Lerner zu langsam (über 20 Minuten, abgebrochen).
* **Straßen-Ergebnisse (1c, 1d):** Orientierungsproblem inzwischen behoben und mit symmetrischen Labels wiederholt, siehe Korrektur-Abschnitt nach 1d; die Schlussfolgerungen bleiben.
* **Nächster Schritt (Vorschlag):** Zellebene. (1) Zell-Makro lernen (größeres `maxe`), (2) Netzliste mit dem Makro überdecken, (3) Quotientengraph (Knoten = Zellinstanz, Kante = Verdrahtung mit
  Port-Paar als Label), (4) darauf Klassen aus Quadraten, Fasern und Produkt-Abschluss wie in e17. Das wäre der eigentliche Test "Produkt von Zellen".

### Ergebnis Schritt 1f: Zellebene von c6288 (Quotientengraph), `src/cells*.py`, `quotient.py`, `e23.py`, `results/e23_*`, `results/cells_D*.json`

**Aufbau (alles gelernt, keine Handarbeit an der Zellstruktur):**
1. Muster (bis 12 Kanten) aus 30 BFS-Fenstern lernen (17 Einträge) und damit die **ganze** c6288-Netzliste (2448 Gatter, 4800 Kanten) überdecken: nur 81 Kanten bleiben roh.
   Drei Muster tauchen je ca. 225-240-mal auf (12, 5 und 3 Kanten) und bilden zusammen die Zelle (ca. 240 Volladdierer).
2. Zwei MDL-getriebene Verklebungsrunden auf dem Gesamtgraphen (Gewinn 5089 und 2425 Bit) ergeben die **Zelle mit 20 Kanten, 195 vollständige Instanzen**, daneben Randzellen.
3. **Quotientengraph:** Knoten = Zellinstanz (361 Knoten); Kanten = von zwei Instanzen geteilte Gatter und freie Drähte; Label = Port-Paar (86 Labels). Die 32 Primäreingänge
   (Bus, je 16 Zellen) sind aus dem Quotienten herausgenommen (sonst Cliquen); welcher Eingang in welche Zelle geht, wäre die Beschriftung.
4. Auf dem Quotienten gibt es echte **kommutierende Quadrate** (259 Quadrate, 155 je Port-Paar): in der einen Richtung ein Bündel aus 3 parallelen Verdrahtungen zwischen benachbarten Zellen,
   in der anderen eine Verdrahtung. Das ist der Gitterfaktor "Bündel x Kante". (Der Fenster-Lader verlor zunächst parallele Kanten; behoben.)

**Messung** (n=40 Trainingsfenster à 16 Zellknoten, 100 Testfenster, 3 Seeds; Testbits pro Fenster, Mittel):
leer 627,6 | Kleben 243,1 | Wachsen 257,4 (Differenz 3,5 / 25,3 / 14,3 je Seed) | **Produkt-Abschluss 242,9** (Faktoren gewählt: 0 / 2 / 0; Gewinn gegenüber Kleben 0,0 / 0,6 / 0,0 Bit).

* **Der Produkt-Abschluss bringt auch auf Zellebene nichts.** Klassen werden korrekt gelernt (Bündel-Labels gegen die Einzelkante), Faktoren (Bündel, Bündelketten, Einzelkanten) sind Kandidaten, aber
  die Auswahl nimmt sie nicht: Das erweiterte Wörterbuch kostet mehr Zeigerbits (ca. +12,7 Bit über 40 Fenster im Test mit Paarschritt) als es spart.
* **Warum vermutlich:** Das geklebte Wörterbuch enthält schon die kleinen Gitterstücke bis 16 Kanten (Bündel x Kante hat 8, Bündelpaar x Pfad 15). Die Testfenster (16 Zellknoten, ca. 38 Kanten) sind nur
  2-4 Zellen breit; größere Produkte würden helfen, aber gerade die kann der Einbettungs-Suchalgorithmus (backtracking) nicht mehr bezahlbar abdecken. Mit Obergrenze 32 für Produkte änderte sich nichts.
* **Kompositionsvorteil auf Zellebene kleiner als auf Gatterebene:** 3,5-25 Bit gegen Wachsen (Gatterebene: 46-53 Bit), weil Zellen schon die große Struktur tragen.
* **Einschränkungen:** Eine Schaltung, überlappende Fenster (Trainings-/Testfenster teilen Zellen), Fenstergröße begrenzt durch den Matcher, Zelle in Windows nur bis 12 Kanten gelernt und erst auf dem Gesamtgraphen
  verklebt, Primäreingänge ausgeklammert, 3 Seeds; die Port-Paar-Labels sind eine Kodierungsentscheidung von uns.
* **Fazit zu Chips:** Der einzige Kompositionseffekt auf echten Daten mit klarer Größe (c6288, Gatterebene) kommt vom **Kleben**, nicht von Produkten. Ein Produkt-Vorteil auf echten Daten
  ist weiterhin nicht belegt (Straßen: Null; Chips: Null). Der Befund bleibt: Produkte wirken nur dort, wo die Daten viele große, exakt gleiche Gitter in vielen Formen enthalten.

### Korrektur Schritt 1c/1d: Straßen mit symmetrischen Kanten (`SYM=1`, Ergebnisdateien `*_sym.json`)

Die ersten Straßenläufe (1c, 1d) hatten Kanten nach Koordinatenreihenfolge orientiert und nicht als symmetrisch behandelt; Straßen sind ungerichtet. Wiederholt mit `und.SYMS` = alle Labels
und ungerichteter Kanonisierung (`und4.UND`). Gleiche Fenster und Seeds wie zuvor. Testbits pro Fenster (Mittel über 3 Seeds, außer wo vermerkt):

| Messung | Barcelona | Madrid | Zaragoza | Sevilla |
|---|---|---|---|---|
| leer | 369,3 | 337,6 | 301,9 | 361,6 |
| Kleben, gerichtet (alt) | 258,3 | 240,8 | 218,5 | 247,7 (Seed 0) |
| **Kleben, symmetrisch** | 239,2 | 219,4 | 193,0 | 233,5 |
| **Wachsen, symmetrisch** | 238,6 | 217,6 | 191,6 | 231,4 |
| Form+Beschriftung (Nachbarkontext), symmetrisch | 233,1 | 210,3 | 186,1 | 225,1 |
| Form+Beschriftung (nur iid-Labels), symmetrisch | 250,3 | 230,8 | 205,4 | 246,6 |

* **Absolute Kompression besser** (ca. 15-18 Bit gegenüber dem gerichteten Lauf, Mittel über 3 Seeds), die Orientierung war also eine reale Erschwernis.
* **Kleben ≈ Wachsen bleibt** (Differenz Kleben minus Wachsen: -0,6 bis +5,0 Bit, im Mittel +1,5 zugunsten von Wachsen). Die Aussage "kein Kompositionsvorteil auf Straßen" gilt auch symmetrisch.
* **Form+Beschriftung mit Nachbarkontext schlägt markiertes Kleben weiterhin**, in allen 12 Fällen (4 Städte x 3 Seeds) um 4,7-9,8 Bit pro Fenster (vorher 3,6-8,4). Das ist ein generischer Kontextmodell-Gewinn.
* **Produkt-Abschluss, unmarkiert (Geometrie, alle Kanten gleiches Label):** Seed 0: Faktor gefunden, Gewinn 1,5-2,5 Bit (Barcelona 203,4 -> 201,3; Madrid 186,3 -> 184,8; Zaragoza 174,3 -> 172,6; Sevilla 193,0 -> 190,5);
  Seed 1: kein Faktor, Gewinn 0,2-0,4 Bit. Seed 2 nach über 75 Minuten abgebrochen (die symmetrische Faktorsuche ist deutlich langsamer). **Zwei Seeds, kleiner Gewinn von bis zu 1% (Seed 0), nicht belastbar.**
* **Produkt-Abschluss, markiert (Straßenklassen):** Differenz (Produkt minus Kleben) Barcelona +3,1 / -2,2 / +0,1, Madrid +2,2 / -1,4 / +1,4, Zaragoza +1,3 / -2,5 / +0,6, Sevilla +3,3 / -2,3 / +2,2: gemischte Vorzeichen, im Mittel leicht negativ. **Kein Effekt.**
* **Fazit unverändert, aber jetzt sauber:** Auf echten Straßen gibt es keinen belastbaren Produktvorteil; der Beschriftungsgewinn bleibt, ist aber nicht prägarbenspezifisch.

## 4b. Literaturreview zu Makros mit Löchern

Siehe `review-makros.md` (Makros/Interfaces in der Graphkompression, Cospans, Exponentialobjekt; Testvorschläge A–C).

## 4c. Test A: Makros mit Interface (Instanzkosten nur für Randknoten) – 11. Oktober 2026

Code: `src/iface.py`, `src/e24.py` (c6288), `src/e24s.py` (Straßen, symmetrisch). Kostenmodell: Eine Instanz zahlt Musterindex + Zähler k + Teilmenge der k *Randknoten* (Knoten mit Kanten außerhalb der Instanz; `log C(|V_p|,k)`) + k Zeiger; innere Knoten vergibt der Dekoder frisch. Sicherheitshalber `min` mit dem alten Schema + 1 Flagbit je Instanz. Wörterbuchkosten nicht enthalten (wie bisher in den Pro-Fenster-Zahlen); gleiche Wörterbücher, nur anders kodiert, plus Lerner, die direkt auf das Interface-Ziel optimieren.

**c6288 (Gate-Ebene), 40 Trainingsfenster, in-sample Bits/Fenster, Mittel über 3 Seeds (Umkodierung der alten Wörterbücher):**

| | alt | mit Interface | Gewinn |
|---|---|---|---|
| glue | 156.9 | 116.2 | 40.7 (26 %) |
| grow | 196.7 | 176.8 | 19.9 (10 %) |

Der Abstand glue–grow wächst von 39.8 auf 60.6 Bit: große Muster haben mehr innere Knoten und profitieren stärker. Mittlere Muster-/Instanzgröße: glue |V| ≈ 5.4, k ≈ 2.3 Randknoten; grow |V| ≈ 3.3, k ≈ 2.1. Lerner mit Interface-Ziel (nur Seeds 1, 2; Seed 0 war beim Schreiben noch nicht fertig): glue 113.0 (vs. 119.9 umkodiert), grow 198.3 (vs. 175.4 – hier lernt der Lerner *schlechter*, Ausreißer durch Seed 2; ein Hinweis auf Rauschen bei n=2, nicht auf ein Ergebnis). Auf fremden Schaltungen (c1355, c499, c880, c1908) ändert sich fast nichts (≤ 4 Bit von ~310–430): das Wörterbuch überträgt kaum.

**Straßen (Barcelona → Madrid/Zaragoza/Sevilla, symmetrisch, 50 Fenster, 3 Seeds):** glue spart 21–25 Bit, grow 21–26 Bit; Abstand glue–grow bleibt ≈ 0–2 Bit. Der Gewinn ist hier ein *allgemeiner* Kodierungsgewinn (innere Knoten gratis), kein Vorteil für Verkleben.

**Lesart.** (1) Das Interface-Kostenmodell ist ein echter, aber bescheidener Hebel: ~10–26 % auf c6288. (2) Es verstärkt den schon bekannten Vorteil des Verklebens auf c6288 (glue schlägt grow nun um ~61 statt ~40 Bit), aber nicht auf Straßen. (3) Vorbehalt: Das alte Schema (`#Knoten · log n` je Instanz) ist besonders großzügig gegenüber einem fairen Baseline-Kodierer, der innere Knoten ebenfalls implizit lässt; der Gewinn gilt also relativ zu *unserem* alten Modell, nicht relativ zu gRePair/SUBDUE (die Interfaces ohnehin haben). Ein fairer Vergleich mit einem Interface-fähigen Baseline-Miner fehlt. (4) Test A prüft nur Interface-Kosten; *echte Löcher* (Muster, in deren Loch verschiedene Teilmuster passen) sind weiter Test B/C im Review.
Rohdaten: `results/e24*.json|log`.

## 5. Offener Faden: Simplizes (für später)

Warum: Bei Graphen kann man Stücke nur an Knoten verkleben (Knoten sind die einzigen echten Teilobjekte einer Kante). In
simplizialen Mengen (Prägarben auf Delta) gibt es Gesichter: Dreiecke lassen sich an einer gemeinsamen **Kante**, Tetraeder an
**Flächen** verkleben. Hier gibt die Dichtheits-/Pushout-Sicht tatsächlich mehr her als Re-Pair auf Graphen. Außerdem: Ein gefülltes
Dreieck unterscheidet sich von einem hohlen 3-Zyklus, obwohl beide dieselben Kanten haben; Graphverfahren sehen den Unterschied nicht.

Geplanter Test:
* Daten: Komplexe aus gefüllten und hohlen Dreiecken, Tetraedern, Paaren, die eine Kante teilen; Rauschen; mehrere Größen/Tiefen.
* Lerner umbauen: Muster = Mengen von Simplizes; Einbettungen müssen Ränder respektieren; Kosten pro Simplex neu definieren
  (ein 2-Simplex ist ein Element, nicht drei Kanten plus Flag).
* Vergleich: einfachste Graph-Kodierung (nur Kanten) gegen simpliziale Kodierung, und Verkleben entlang von Kanten gegen nur an Knoten.
* Erwartung: Vorteil wächst mit der Größe der geteilten Ränder. Widerlegt, wenn simpliziale Kodierung nicht besser ist als
  Graph-Kodierung mit Zusatzkante für "gefüllt".
* Größter Umbauaufwand aller Fäden; deshalb nach den Produkten.

## 6. Weitere offene Punkte

* Flexibleres Äquivalenzmodell für Kinships (Relation als Komposition anderer, nicht nur genau ein Partner).
* Besserer Schätzer für Äquivalenzen bei kleinen Datenmengen (dort die größte Lücke zum Oracle); strengeres Annahmekriterium gegen falsche Paare.
* n-stellige Relationen (Hypergraph-Schema): zeigt Schemaunabhängigkeit, ist aber nicht simplizial.
* Neugier-Teil selbst: aktive Auswahl der nächsten Daten nach erwartetem Lernfortschritt gegen zufällige Reihenfolge (Bandit auf dem Kompressionssignal).
* GraphMDL-Java-Fassung (Inria-GitLab war nicht erreichbar) oder GraphMDL auf größeren Mengen mit längerem Zeitlimit.
* Moleküle und Wissensgraphen mit Produkten/Parametrisierung, sobald die synthetischen Tests tragen.
