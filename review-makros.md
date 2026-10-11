# Kleines Review: Makros (mit Löchern) in der Graphkompression – und ihre kategorientheoretische Lesart

Stand: 11. Oktober 2026. Zweck: Theorie/Literatur klären, bevor wir „Makros mit Loch" numerisch testen.

**Kennzeichnung.** Jede Aussage trägt eine Etikette:
- **[belegt]** – in einer von mir gelesenen Quelle (Abstract/Volltext/Suchtreffer) so gesagt.
- **[Deutung]** – meine eigene Brücke; plausibel, aber nicht von den Autoren behauptet.
- **[ungeprüft]** – aus dem Gedächtnis, nicht verifiziert.

Zugriffsprobleme: die HAL-Seite von GraphMDL+ (Zugriff verweigert) konnte ich nicht lesen; Aguiñaga et al. (arXiv 1608.03192) wurde gefunden, aber nicht gelesen.

---

## 1. Was ist ein „Makro mit Loch"?

Ein Makro ohne Loch ist ein festes Teilgraph-Muster, das mehrfach vorkommt; man speichert es einmal und verweist darauf. Das ist, was unser `glue`-Lerner tut (Muster = Verklebung kleinerer Muster, Kosten pro Instanz = Zeiger + Anbindungsknoten).

Ein Makro **mit Löchern** hat zusätzlich *Parameter*: Stellen, an denen bei jeder Verwendung etwas anderes eingesetzt wird. Bei Graphen gibt es dafür drei übliche Gestalten:
1. **Externe Knoten** (Interface): das Muster hat k ausgezeichnete Knoten, über die es mit dem Rest verklebt wird.
2. **Nichtterminal-Kanten**: ein Platzhalter (Hyperkante vom Rang k), der später durch ein Teilgraph-Muster ersetzt wird.
3. **Unterspezifizierte Labels/Teile**: Anti-Unifikation – das Muster ist die gemeinsame Verallgemeinerung mehrerer Vorkommen, die Unterschiede sind die Löcher.

## 2. Grammatikbasierte Graphkompression (Hyperkanten-Ersetzung)

- **[belegt]** Kompression via *Straight-Line Hyperedge-Replacement (SL-HR)-Grammatiken* (gRePair, Maneth et al.): Digramme (Paare benachbarter Kanten) werden iterativ durch eine Nichtterminal-Hyperkante ersetzt, deren Regel das Digramm erzeugt. Eine Nichtterminal-Kante hat einen *Rang* = Zahl der angehängten (externen) Knoten. Das ist genau ein Makro mit k Löchern im Sinn von (1)+(2): die externen Knoten sind die Schnittstelle zum Rest.
- **[Deutung]** Unser `glue`-Lerner entspricht einem gRePair mit größeren Bausteinen und MDL-Auswahl statt Häufigkeits-Heuristik; der Unterschied zu „Makro mit Loch" ist, dass wir die Schnittstelle *nicht* als erstklassiges Objekt führen – wir speichern pro Instanz die vollen Knotenbezüge (`#vertices·log2 n`). Ein Makro mit Interface würde nur die externen Knoten pro Instanz kosten, interne Knoten wären „frei".
- **[belegt]** Kukluk–Holder–Cook: Inferenz rekursiver Knoten-/Kantenersetzungs-Grammatiken mit überlappenden Instanzen (auf SUBDUE-Basis). Rekursion = Makro, das sich selbst als Loch enthält.
- **[belegt]** SUBDUE selbst komprimiert iterativ durch Ersetzen der besten Teilstruktur durch einen Knoten (MDL); der ersetzende Knoten hat die Verbindungen der Instanz → implizit ein Makro mit Interface, aber ohne Typisierung der Löcher.

## 3. MDL-Miner mit Vokabular und Ports

- **[belegt]** VoG (Koutra et al.): MDL-Auswahl aus einem *festen* Strukturvokabular (Cliquen, Sterne, Ketten, Bipartite …). Kein Lernen neuer Makros, aber Beleg, dass parametrisierte Grundformen (Stern mit n Blättern) sehr wirksam sind: ein Stern ist ein Makro, dessen Loch „Anzahl Blätter" ist.
- **[belegt, nur Erwähnung]** GraphMDL+ / KG-MDL kennt *Ports* (Knoten, an denen Muster mit anderen verbunden werden dürfen) – das ist das Interface-Konzept in Mining-Sprache. **[ungeprüft]**: Details der Kostenformel, da die HAL-Seite nicht lesbar war.
- **[Deutung]** Unser Befund „Produktabschluss bringt nur auf synthetischen Gittern etwas" passt dazu: Produkte sind *ein* spezielles parametrisiertes Makro (Interface = die beiden Faktoren), kein allgemeines.

## 4. Bibliothekslernen und Anti-Unifikation (die Programm-Schwester)

- **[belegt]** DreamCoder (Ellis et al.), Stitch (Bowers et al.), Babble (Cao et al.): *Abstraktionen* sind λ-Terme mit Löchern („Makros"), gefunden durch Anti-Unifikation (Babble: auf E-Graphen) und per Kompression/MDL bewertet. Das ist das nächste Analogon: Abstraktion = Makro mit Parametern; Anwendung = Einsetzen.
- **[belegt]** Term-Graph-Anti-Unifikation (Baumgartner et al., FSCD 2018) berechnet die speziellste gemeinsame Verallgemeinerung von Termgraphen – formal unser „Muster aus zwei Vorkommen mit Löchern an den Unterschieden".
- **[belegt, jetzt im Volltext gelesen]** ten Cate–Dalmau–Funk–Lutz, *Extremal Fitting Problems for Conjunctive Queries* (arXiv 2206.05080v3): Das direkte (kategorielle) Produkt zweier Instanzen ist die größte untere Schranke in der Homomorphismen-Präordnung (Prop. 2.7: Projektionen + universelle Eigenschaft). Existiert überhaupt eine passende Anfrage, so ist die kanonische Anfrage des Produkts aller positiven Beispiele eine passende (Thm 3.3); sie ist die (stark/schwach) *most-specific fitting* Anfrage (Intro-Charakterisierung: q ist most-specific genau dann, wenn das Produkt der positiven Beispiele auf I_q abbildet). Das ist die bekannte Rolle des Produkts als *least general generalization*. Dual dazu ist die disjunkte Vereinigung die kleinste obere Schranke (Koprodukt).
- **Grenzen/Vorbehalte [belegt]:** (i) Es geht um *Homomorphismen*-Semantik auf relationalen Strukturen/CQs, nicht um unsere Einbettungs-/Teilgraph-Semantik. (ii) Das Produkt muss ein „data example" sein (ausgezeichnete Elemente müssen vorkommen; Bsp. 2.6). (iii) Die Größe wächst multiplikativ (exponentiell im Produkt vieler Beispiele); das Paper merkt selbst an, dass die naive Kandidaten-UCQ nicht „komprimiert oder generalisiert" (S. 15) – für Kompression wäre also der *Kern* (core) des Produkts relevant, nicht das Produkt selbst.
- **[Deutung, Korrektur zu meiner ersten Fassung]** Unser Produktabschluss ist *kein* Spezialfall davon: dieselbe Operation (× in der Prägarbenkategorie), aber andere Rolle. Wir multiplizieren *Faktor-Muster* (Gitter = Pfad × Pfad), um ein größeres Muster zu erzeugen; ten Cate et al. multiplizieren *Beispiele*, um ihre Gemeinsamkeit zu extrahieren. Für Makros mit Loch ist letzteres das Relevante: lgg(Fenster₁, Fenster₂) = das Muster, in das beide Vorkommen abbilden, die Abweichungen sind die Löcher. Pushout = „Unifikation" bleibt meine Dualitäts-Lesart (die Quelle spricht von Koprodukt/Produkt, nicht von Pushouts).

## 5. Kategorientheorie

**Rewriting.**
- **[belegt]** Double-Pushout-(DPO)-Ersetzung auf adhäsiven Kategorien: Regel L ← K → R; K ist die *Schnittstelle*, die erhalten bleibt. Anwendung = zwei Pushouts. Hyperkanten-Ersetzung ist der Spezialfall in Hypergraphen (Pshenitsyn nutzt das für die Hypergraph-Lambek-Grammatiken).
- **[belegt]** *Structured cospans* (Cicala): offene Systeme/Graphen als Cospans A → X ← B mit Rand A, B; Komposition = Pushout. Ein Makro mit k Löchern ist ein Objekt mit k Randpunkten, Einsetzen ist Komposition.
- **[belegt]** Hypergraph-Kategorien / Cospan-Algebren (Fong–Spivak): Cospans von endlichen Mengen bilden die frei erzeugte hypergraph category; Graph mit Interface = Morphismus. Kompaktes Vokabular für „Glue": die Pushout-Komposition, die wir implementiert haben, ist Komposition in Cospan(FinSet)-artigen Kategorien.

**Exponentialobjekte.**
- **[Fakt, Standard]** Prägarben-Topoi sind kartesisch abgeschlossen: (B^A)(c) = Hom(y(c) × A, B). Genau dieses Produkt × taucht in unserem Produktabschluss auf.
- **[belegt]** Vigna: explizite Beschreibung von Exponentialen im Topos der (gerichteten, Multi-)Graphen (Prägarben auf der Kategorie • ⇉ •). Ein Element von B^A ist ein „Graph-Homomorphismus mit Parameter c". Vigna verknüpft das *nicht* mit Makros/Kompression.
- **[belegt]** Fiore–Plotkin–Turi (Abstract Syntax and Variable Binding): Prägarben-Kategorie Set^F mit Kontext-Erweiterung δ (Adjungierte), Exponentiale für Bindung. Dort *ist* ein „Term mit freier Variable" ein Element von δ(X) – also das mathematische Original von „Makro mit Loch" in der Syntax.
- **[belegt]** Pshenitsyn: Hypergraph-Lambek-Kalkül HL mit Residuen (÷) und einer „!"-Modalität. **Beachte:** er formuliert das nicht kategorientheoretisch (kein CCC-Bezug); die Residuen spielen die Rolle von „Hypergraph mit Loch, das ergänzt werden muss".
- **[Deutung, Kernthese]** *Currying-Lesart von Makros*: Ein Makro mit Loch der Sorte A in einer Umgebung B entspricht einem Pfeil A → B (bzw. Element von B^A); Einsetzen = Evaluation ev: B^A × A → B. Ein Makro *ohne* Loch ist ein Punkt 1 → B. Die Lernaufgabe „finde gute Makros" wird zu „finde eine Familie von Pfeilen, mit der sich die Daten als Evaluations-Komposition schreiben lassen". Das Pushout-Verkleben (unser Stand) ist der *kolimes-Teil*; der Exponentialteil kommt erst, wenn Interfaces typisiert und Einsetzungen höherstufig (Makros in Makros) werden.
- **[Deutung, Vorsicht]** Die Cospan-Lesart (Interface = Rand) und die Exponential-Lesart (Interface = Argument) sind **nicht identisch**. Cospans leben in einer kompakt abgeschlossenen/Hypergraph-Struktur (Argument und Ergebnis symmetrisch, keine echte Funktionalität); Exponentiale sind asymmetrisch. Für Graphkompression ist die Cospan-Lesart die direkt anwendbare; die Exponential-Lesart ist die elegantere, aber bisher nicht in der Kompressionsliteratur ausgenutzt (**nichts gefunden**).

## 6. Fazit: Welche Rolle spielt die Makro-Idee?

1. In der Kompressionspraxis (gRePair, SUBDUE, Bibliothekslernen) sind Makros mit Interface Standard. Rein „löcherlose" Muster sind die Ausnahme. Insofern ist der Schritt zu Makros mit Löchern kein Alleinstellungsmerkmal, sondern Aufholen auf den Stand der Technik – der Gewinn ist also eher *gegenüber unserem aktuellen glue* zu erwarten als gegenüber gRePair.
2. Mögliches Alleinstellungsmerkmal: ein *einheitlicher* Rahmen (Prägarben: Kolimes für Verkleben, × und Exponential für Parametrisieren und Einsetzen) statt getrennter Heuristiken. Das ist Theorie-Hypothese; ich habe **keine** Quelle gefunden, die Graphkompression in dieser Sprache formuliert.
3. Bezug zu den bisherigen Ergebnissen: c6288-Gate-Ebene (Verkleben schlägt Wachsen um 23–25 %) und Zellebene sind Fälle, wo Instanzen sich in *Anschlüssen* unterscheiden, nicht in Form – genau dort sollte ein Interface-Makro sparen (Zellen mit k Ports, Instanzkosten k statt n_Knoten Zeiger).

## 7. Vorschlag für den ersten Test (noch nicht gestartet, Bestätigung abwarten)

- **Test A (Interface-Kosten):** gleicher `glue`-Lerner, aber Muster mit Interface: Instanzkosten nur externe Knoten (Rest wird implizit „frisch" vergeben, Verbindung nur über Ports). Frage: Wie viele Bits spart das auf c6288 (Gate- und Zellebene) und Straßen? Das testet, ob der Gewinn aus Interface-Typisierung kommt. Billig, nutzt vorhandenen Code.
- **Test B (Anti-Unifikation):** Muster = lgg zweier Fenster (Produkt zweier Fenster, dann Kern bilden; Hom-Semantik beachten); Löcher = gelöschte/unterschiedliche Knotenlabels. Frage: Gewinn bei verrauschten Wiederholungen (e18-Rauschsweep).
- **Test C (höherstufig):** Makro enthält Nichtterminal (Rekursion à la Kukluk et al.), z.B. n-Bit-Adderkette. Teuerster Test, erst nach A/B.

## 8. Verifikationsstatus (kurz)

| Aussage | Status |
|---|---|
| gRePair = SL-HR, Digramm-Ersetzung, Rang | Abstract/Suche gelesen; Details der Digramm-Auswahl **[ungeprüft]** |
| DreamCoder/Stitch/Babble = Abstraktion via (Anti-)Unifikation | belegt (Abstracts); MDL-Details von DreamCoder **[ungeprüft]** |
| Produkt = glb in Hom-Ordnung = most-specific fitting CQ (ten Cate et al.) | **belegt** (Volltext: Prop. 2.7, Thm 3.3, Intro); Übertragung auf Einbettungssemantik/Kompression ist Deutung |
| GraphMDL+ Ports | nur erwähnt gelesen |
| Aguiñaga et al. (CIKM 2016) | nur Treffer, nicht gelesen |
| Pshenitsyn: kein CCC-Bezug | belegt |
| Makro ≈ Cospan / Evaluation ≈ ev | **eigene Deutung** |

## Quellen
- gRePair / SL-HR-Grammatikkompression (Maneth et al.), via Suche
- Pshenitsyn, Hypergraph Lambek calculus (HL), Ausdrucksstärke/DPO-Bezug
- Fong & Spivak, Hypergraph Categories
- Cicala, Rewriting structured cospans
- Vigna, A guided tour in the topos of graphs
- Fiore, Plotkin, Turi, Abstract Syntax and Variable Binding (über arXiv 2505.24812 als Sekundärquelle)
- Ellis et al., DreamCoder; Bowers et al., Stitch; Cao et al., Babble
- Baumgartner et al., Anti-unification for term graphs (FSCD 2018)
- Koutra et al., VoG
- Kukluk, Holder, Cook, Inference of node replacement recursive graph grammars
- ten Cate & Dalmau (arXiv 2206.05080v3, Volltext gelesen)
- Aguiñaga et al., arXiv 1608.03192 (nicht gelesen)
