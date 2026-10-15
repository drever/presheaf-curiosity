# Standortbestimmung, RePair-Claims und Argumente für die Garbenperspektive

Stand: 15. Oktober 2026. Etiketten wie in `review-makros.md`: **[belegt]** (in einer gelesenen Quelle), **[Standard]** (Lehrbuchwissen, nicht neu geprüft), **[Beweisskizze]** (eigene Herleitung, nicht von anderen geprüft), **[Deutung]**, **[ungeprüft]**.

---

## 1. Welche Effekte untersuchen wir?

| Effekt | Operation | Was wir testen | Stand der Evidenz |
|---|---|---|---|
| **E1 Verkleben** | Kolimes/Pushout (Interface = Cospan) | Muster aus Mustern; Instanzen zahlen nur Randknoten | c6288: glue ≫ grow (23–25 %, mit Interface 31 % vor gRePair-artiger Baseline); Straßen: glue ≈ grow, beide ≈ 12–14 % vor der Baseline (strategy.md 1e, 4c–4e) |
| **E2a Produkt** | Limes (Box-Produkt, abgeschlossen monoidal) | Produktabschluss des Wörterbuchs | nur synthetisch (e17), auf echten Daten ≈ 0 (1c, 1e, 1f); theoretisches Argument: Baumweiten-Separation (3.2) |
| **E2b Exponentialobjekt B^A** (= höherstufig: Makro mit Loch, Currying, Einsetzen = Evaluation) | interne Hom | Label-Loch (Anti-Unifikation), Loch mit Teilgraph-Füllung (Tiefe 1), **Loch in Loch (Tiefe 2)** | Label-Loch: synthetisch 22–92 Bit, echt nichts (4f/4g). Teilgraph-Füllung Tiefe 1: synthetisch 28–35 Bit/Fenster, echt kaum Löcher (4h). **Tiefe 2: strategy.md 4j** |
| **E3 Rekursion = Fixpunkt** | Initialalgebra / W-Typ (X ≅ F(X)) | bisher nichts | **nicht getestet.** Mehr als E2b: das Exponentialobjekt gibt höherstufige, aber terminierende Makros (wie SL-Grammatiken mit Parametern); Selbstbezug braucht einen Fixpunkt |

Du hast zwei Ziele benannt: (a) Verkleben als Stärkung der Garbenperspektive (E1), (b) einen Higher-Order-Effekt. Klarstellung vom 15.10.: Mit „rekursiv" ist hier das **Exponentialobjekt** gemeint (E2b: Makros als Elemente von B^A, Makros in Makros durch Currying). Echte Rekursion über einen Fixpunkt (E3) ist mehr als das Exponentialobjekt und ein eigener, noch nicht getesteter Effekt. RePair (SL-HR-Grammatiken) sucht Rekursion nur als *Verschachtelung* (Nichtterminale, die Nichtterminale benutzen, kein echter Selbstbezug).

---

## 2. Wo behauptet die RePair-Community ihren Vorteil?

Gelesen: gRePair (Maneth/Peternek, arXiv 1704.05254), ITR (arXiv 2306.01028v3), gRDF (PMC 9003471), Claude/Navarro (Abstract, TWEB 2010), TreeRePair (arXiv 1007.5406).

| Datenfamilie | Quelle | Aussage **[belegt]** | Einschränkung |
|---|---|---|---|
| **RDF-Graphen mit wenigen Prädikaten** (DBpedia-Auszüge, Identica, Jamendo) | gRePair | Gegenüber k²-Bäumen „durchgängig besser, teils um Faktor mehrere Hundert". Mittel bei maxRank 4: RDF 4.85 bit/Kante (Netzwerkgraphen 11.44, Versionsgraphen 5.57) | Vergleich gegen Adjazenzmatrix-Strukturen (k²), nicht gegen Musterminer |
| **RDF mit Stern-/Baum-Mustern** (LUBM, ArchivesHub, ScholarlyData) | gRDF | Wirkt am besten, wenn Subjekt-Prädikat- und Objekt-Prädikat-Paare oft wiederkehren und es wenige Prädikate gibt; Stern-/Baummuster halbieren die Kantenzahl. Bei realen Daten (viele Prädikate) schwach; Wörterbücher machen ≈ 75 % der komprimierten Größe aus | gRDF-Vorsprung gegenüber bestem Konkurrenten bei realen Daten nur 1.9–3.3 % |
| **Versionsgraphen** (Tic-Tac-Toe 5 634 Knoten / 10 016 Kanten, Chess-legal 76 272 / 113 039, DBLP-Schnappschüsse) | gRePair, ITR | Hochgradig regelmäßig (ttt: 3 Labels); ITR+ erreicht auf ttt-win 14.23 % der Rohgröße und schlägt „alle anderen" | auf Netzwerk-/Versionsgraphen sind andere Verfahren teils besser (ITR-Autoren) |
| **Webgraphen** | Claude/Navarro | Re-Pair erreicht nicht die Kompressionsrate von WebGraph, navigiert aber bei gleichem Platz schneller | Vorteil ist Navigation, nicht Größe |
| **XML-Bäume** | TreeRePair | SLCF-Grammatiken teilen *wiederholte Baummuster mit Parametern* (= Makros mit Löchern!), DAGs nur identische Teilbäume; SLCF können exponentiell kleiner als DAGs sein (zitiert, [LM06]) | Korpusnamen im gelesenen Auszug nicht genannt |
| **Soziale/Netzwerk-/Kooperationsgraphen** (CA-AstroPh, Enron, Wiki-Vote …) | gRePair | Höchste bit/Kante; gRePair+DSR meist am besten, aber Vorsprung gering | kein Struktur-Claim |

**Lesart.** Der Vorteil wird behauptet, wo (i) sehr wenige verschiedene Labels/Prädikate, (ii) hochgradig regelmäßige lokale Wiederholung (Sterne, Pfade, Baumstücke, Versionen) und (iii) hierarchische Wiederholung vorliegen. Es gibt in diesen Quellen **keinen** Claim für gitter- oder produktartige Strukturen. Der Rang-Parameter ist kritisch: bestes maxRank = 4; die Autoren zeigen theoretisch (Lemma 8/9), dass zu kleiner Rang Kompression verhindern kann [belegt].

**Mögliche Datensätze.** Aus den Quellen: LUBM (Generator), ArchivesHub, ScholarlyData, Jamendo, DBpedia-Auszüge, Wikidata (RDF); Tic-Tac-Toe/Chess/DBLP (Versionsgraphen); CA-AstroPh, NotreDame, Wiki-Talk (SNAP). **[ungeprüft]**, ob aus der Sandbox erreichbar (nur GitHub und Paketregister sind sicher); die Herkunft von „ttt-win"/„chess-legal" ist in den gelesenen Auszügen nicht angegeben. Tic-Tac-Toe-Spielgraph lässt sich lokal erzeugen (nicht identisch mit ttt-win). Für *unsere* Fragestellung (hohe Baumweite plus Produkt-/Hierarchiestruktur) passen eher: Schaltungs-Arithmetik (EPFL, c6288 – vorhanden), FEM-Netze, Gitter/Tori/Hyperwürfel (erzeugbar), Zustandsraumgraphen von Puzzles.

---

## 3. Theorie: Argumente für die Garbenperspektive

### 3.1 Box-Produkt vs. kategorielles Produkt (Präzisierung)
Unser Produktabschluss (`prod_pattern`) ist das **Box-Produkt** (kartesisches Produkt der Graphentheorie), nicht das kategorielle Produkt des Graphentopos. **[belegt]** (TAC 41-23, arXiv 2310.00493): Die Kategorie der (reflexiven) Graphen hat genau zwei abgeschlossene symmetrisch-monoidale Produkte, das Box-Produkt und das kategorielle Produkt. Beide haben also eine interne Hom (Currying). Das Gitter = Pfad □ Pfad ist ein Produkt im ersten, nicht im zweiten. **[Deutung]** Das heißt: die „richtige" kategorielle Heimat des Produktabschlusses ist die box-monoidale Struktur, und die Curry-Lesart der Makros mit Loch (Review 1a, 5) gilt für beide Strukturen.

### 3.2 Argument A (stärkstes): Erzeugbarkeit hoher Baumweite — eine Separation zu SL-HR-Grammatiken
**Satz [Beweisskizze].** Sei Γ eine straight-line-HR-Grammatik, deren Regeln rechte Seiten mit höchstens s Knoten haben (externe Knoten eingeschlossen), und G der erzeugte Graph. Dann gilt tw(G) ≤ s − 1.
*Skizze.* Der Ableitungsbaum von Γ ist ein Baum; ordne jedem Regelanwendungsknoten als Tasche die Knotenmenge seiner rechten Seite zu. Terminalkanten liegen in der Tasche ihrer Regel; ein Knoten kommt in der Regel vor, die ihn erzeugt, und in allen Kindern, an die er als externer Knoten weitergegeben wird, also in einem zusammenhängenden Teilbaum. Das ist eine Baumzerlegung der Weite ≤ s − 1. Die Aussage „HR-Grammatiken erzeugen Graphen beschränkter Baumweite" steht als Einleitungssatz in der Literatur **[belegt]** (Chimes/Iosif/Zuleger, arXiv 2402.17015); die Schranke pro Grammatik ist meine Ausformulierung.
**Folgerung.** Jede SL-HR-Grammatik für G hat eine Regel mit ≥ tw(G) + 1 Knoten, also Größe ≥ tw(G) + 1 (Größenmaß: Knoten der rechten Seiten). Das n×n-Gitter hat tw = n [Standard]; jede Grammatik hat daher Größe ≥ n + 1.
**Dagegen.** Mit einem Wörterbuch, das das Box-Produkt als Operation hat: Pfad P_n durch Verdopplung mit O(log n) Einträgen, Gitter = P_n □ P_n, insgesamt O(log n) Einträge. Das ist eine **exponentielle Lücke** in der Beschreibungsgröße (log n gegen n). Dasselbe gilt für Tori, Hyperwürfel (tw wächst exponentiell in der Dimension) und alle Produkte von Familien mit wachsender Baumweite.
**Grenzen, ehrlich.**
- Der Vergleich „Modell mit zusätzlicher Operation gegen Modell ohne" ist für sich genommen erwartbar. Der Gehalt ist: Das Box-Produkt ist **nicht** aus Klebeoperationen mit Schnittstellen beschränkter Größe erzeugbar. Genau das ist der Unterschied zwischen Kolimes-Fragment (E1) und dem Rest des Topos (E2).
- Mit unbeschränktem Rang kann eine SL-HR-Grammatik das Gitter zeilenweise bauen; ich vermute O(n log n) [ungeprüft], also keine exponentielle, aber eine polynomielle Lücke zu O(log n). Praktisch ist der Rang klein (gRePair: bestes maxRank = 4), dann ist die Lücke nicht zu überbrücken.
- Für **unsere realen Daten** zeigt sich der Effekt nicht: Produktabschluss bringt auf c6288, Zellebene und Straßen ≈ 0 (strategy.md 1c, 1e, 1f). Das Argument sagt *wo* ein Effekt möglich ist (Familien mit hoher Baumweite und Produktstruktur), nicht dass die geprüften Daten solche Familien sind.
- Das Argument ist gegenüber RePair-Grammatiken *im Gitter-Fall* stark, gegenüber der Praxis von RePair (Sterne, wenige Labels, kleine Baumweite) irrelevant.

### 3.3 Argument B: Eine Algebra statt drei Heuristiken (Distributivität)
In Toposen kommutieren Kolimites mit Produkten (Universalität von Kolimites) **[Standard]**; für abgeschlossene monoidale Strukturen (Box-Produkt) folgt das aus der Adjunktion (linker Adjungierter bewahrt Kolimites in jedem Argument) **[Standard]**. Konkret: (A ∪_C B) □ D = (A □ D) ∪_{C □ D} (B □ D). Konsequenz für das Wörterbuch: Es gibt algebraische Umformungen zwischen „erst kleben, dann multiplizieren" und „erst multiplizieren, dann kleben"; kanonische Normalformen und Gleichheitstests für Wörterbucheinträge sind möglich. Grammatik-Sicht hat dafür keine Entsprechung (es gibt nur Syntax). **Stärke:** schön, aber bisher ohne Kompressionsgewinn belegt. **[Deutung]**

### 3.4 Argument C: Substitution als Evaluation — gemeinsame Semantik für Makros mit Loch
HR-Ersetzung und SLCF-Tree-Grammatiken (TreeRePair-Muster mit Parametern **[belegt]**) sind Spezialfälle von „Makro mit Loch = Pfeil A → B, Einsetzen = Evaluation" (Review 5). Die Cospan-Kategorie (Fong–Spivak) liefert die HR-Algebra; Presheaf-Topoi fügen Limiten und interne Homs hinzu. **[Deutung]**, die Identifikation „SL-HR = Programme über Cospan-Signatur" folgt Bauderon–Courcelle **[ungeprüft]**.

### 3.5 Argument D: Fixpunkt (E3) und Größenextrapolation (offen)
Rekursive Makros μX. F(X) (z. B. Ripple-Carry-Kette: Zelle, die sich selbst als Füllung eines Lochs enthält) sind in Toposen mit Natürliche-Zahlen-Objekt Initialalgebren polynomialer Funktoren (W-Typen) **[Standard, nicht neu geprüft]**. SL-Grammatiken haben keinen Selbstbezug: eine Kette der Länge n braucht entweder n Regeln oder Verdopplung (O(log n)), jeweils für ein festes n. Ein rekursives Makro mit Parameter hat Kosten O(log n) für die *Anwendung*, aber das Makro selbst ist größenunabhängig. **Testbare Hypothese [Deutung]:** Ein rekursives Makro *extrapoliert* auf Größen, die im Training nicht vorkamen (z. B. Training 4-/8-bit-Addierer, Test 16-bit); eine Grammatik für einen festen Graphen kann das nicht. Das wäre ein Effekt des Fixpunkts (E3), nicht des Exponentialobjekts allein, und er wird nicht von „RePair kann das auch (mit mehr Regeln)" aufgefressen. **Nicht getestet.**

### 3.6 Argument E: Garbenbedingung als Dekodierbarkeit (schwach)
Matching-Familien lokaler Abschnitte, die auf Überlappungen übereinstimmen, verkleben eindeutig (Garbenbedingung). In unserer Kodierung ist das genau die Konsistenz „Instanzen identifizieren dieselben Randknoten". **[Deutung]** Das erklärt Dekodierbarkeit, gibt aber keine Kompressionsvorteile; reine Formalisierung.

### 3.7 Argument F: Yoneda/Dichte — Muster als Merkmale
Einbettungen eines Musters P in G sind Elemente von Hom(P, G) (Yoneda); Homomorphismenzahlen bestimmen den Graphen bis auf Isomorphie (Lovász) **[Standard]**. Kompression als Wahl einer kleineren Diagramm-Präsentation mit gleichem Kolimes (kofinal) **[Deutung]**. Fachlich sauber, bisher ohne Algorithmus.

---

## 4. Was die Garbenperspektive *nicht* geliefert hat (Gegenargumente)

- E1 (Verkleben) steckt in HR/gRePair bereits (Cospan, Nichtterminal mit Rang). Unser Vorteil gegenüber der gRePair-artigen Baseline auf c6288 liegt in der Musterfamilie (größere Bausteine, globale MDL-Auswahl), nicht in der Prägarbenstruktur; auf Straßen ist `grow` ohne Verkleben genauso gut.
- E2: Produkt-/Loch-Gewinne nur in konstruierten Welten. Der Treewidth-Satz (3.2) benennt die Datenfamilie, auf der das tragen könnte; wir haben dort noch nicht gemessen.
- E3 (Rekursion): nicht getestet.
- RePair ist auf Sternen/wenigen Labels/Versionsgraphen sehr stark; unsere Muster gewinnen dort nichts bewiesen.

## 5. Vorschlag (theorieseitig, geordnet nach Aufwand)
1. **Satz 3.2 sauber ausarbeiten** (Beweis schreiben; Größenmaß festlegen; obere Schranke O(n log n) für unbeschränkten Rang prüfen; Literatur: Courcelle/Engelfriet, HR und Baumweite). Das ist das klarste theoretische Argument.
2. **Distributivität 3.3 an einem Beispiel durchrechnen** (Wörterbuch mit Normalform, Beweis, dass erst-kleben-dann-multiplizieren und umgekehrt dieselben Bitkosten ergeben).
3. **Tiefe-2-Test (E2b)**: Loch, dessen Füllung selbst ein Loch hat (Hom(A, B^C)); Ergebnis in strategy.md 4j. Danach erst **Größenextrapolation (3.5, E3)**: Training auf kleinen Arithmetik-Schaltungen, Test auf größeren, mit einem Makro, das sich selbst enthält.
4. Datensatzseitig: Gitter/Tori/Hyperwürfel (erzeugbar) und Arithmetik-Schaltungen verschiedener Breite (EPFL, vorhanden); Versionsgraphen (Tic-Tac-Toe lokal erzeugen) nur zur Einordnung gegenüber RePair.

## Quellen
- Maneth, Peternek: Grammar-Based Graph Compression, [arXiv 1704.05254](https://arxiv.org/pdf/1704.05254)
- ITR: Grammar-based Graph Compression Supporting Fast Triple Queries, [arXiv 2306.01028](https://arxiv.org/html/2306.01028v3)
- gRDF, [PMC 9003471](https://pmc.ncbi.nlm.nih.gov/articles/PMC9003471)
- Claude, Navarro: Fast and Compact Web Graph Representations, [Abstract](https://users.dcc.uchile.cl/~gnavarro/abstracts/tweb10.html)
- Lohrey, Maneth, Mennicke: Tree structure compression with RePair, [arXiv 1007.5406](https://arxiv.org/pdf/1007.5406)
- Closed symmetric monoidal structures on the category of graphs, [arXiv 2310.00493](https://arxiv.org/abs/2310.00493)
- Chimes, Iosif, Zuleger: Tree-Verifiable Graph Grammars, [arXiv 2402.17015](https://arxiv.org/html/2402.17015v2)
