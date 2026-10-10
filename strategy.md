# Strategie: Hat die Prägarben-Sicht einen algorithmischen Vorteil?

Stand: 10. Oktober 2026. Dieses Dokument hält fest, wie wir vorgehen, was wir bisher wissen und welche Fäden offen sind,
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
