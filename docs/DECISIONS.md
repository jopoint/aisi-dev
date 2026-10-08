# AISI Decision Log

Stand: 2026-10-08

Statuses:

- **Accepted** — binding until deliberately superseded.
- **Frozen** — accepted and protected for the current Study/pilot.
- **Provisional** — current implementation or working assumption; may change after explicit review.
- **Open** — a decision is still required.

## Index

### Shared architecture and geometry
- D001 Shared metric world
- D002 Canonical polygon geometry
- D003 Table types
- D004 Format-bound assignment
- D005 Transformation strength
- D006 Maximum layout capacity

### Layout formats
- D007 Source-adaptive Rect Input
- D007a Participant-based Input preview
- D008 Rect Groupwork topology
- D008b Teilnehmendenbasierte Groupwork-Gruppen und Sitzprioritäten
- D008a Layout validation workflow
- D009 Discussion topology
- D010 Scout Groupwork semantics

### TouchDesigner and rendering
- D011 Physical calibration protection
- D012 TouchDesigner source of truth
- D012a Gemeinsame AISI-/Study-Gestaltung
- D013 Rendering backends

### Study
- D014 Study task structure
- D015 Study conditions
- D016 Active trial version
- D017 A/B transformation
- D018 Study state mappings
- D019 Objective arrival
- D019a Familiarization
- D020 Study outcome hierarchy

### Tracking and data
- D021 Tracking baseline
- D022 Runtime and participant data

## D001 — Shared metric world

Status: **Accepted**

- AISI uses a `500 × 500 cm` world/ROI.
- Center is `(250, 250) cm`.
- TouchDesigner scale is `1 cm = 0.0052 TD units`.
- Axis and rotation conversion must be traced end-to-end before changes.

## D002 — Canonical polygon geometry

Status: **Accepted**

- Collision, ROI, separation, clearance, repair, and debug rendering use canonical table polygons/supports.
- Do not add parallel hard-coded geometry.
- Legacy rectangles remain supported through explicit rectangular dimensions.

## D003 — Table types

Status: **Accepted**

- `summit`: trapezoidal Vitra Scout Summit.
- `sprint`: trapezoidal Vitra Scout Sprint.
- `rect`: `160 × 80 cm` rectangle.
- All currently relevant physical tabletop heights are `74 cm`.

## D004 — Format-bound assignment

Status: **Accepted**

- A format generator binds a semantic slot/role to a specific `table_id`.
- A second global min-cost slot permutation must not reorder those roles afterward.
- Final targets return in original scene order to preserve OSC source/target index coupling.

## D005 — Transformation strength

Status: **Accepted**

- `strength = 0` means exact source poses and no repair.
- `strength > 0` uses source/target blending followed by one final hard-constraint repair.
- Rotation interpolation follows the shortest angular path.
- Repair may override the visually requested strength when required by hard constraints.
- Invalid collision/ROI results must not be silently reported as valid.

## D006 — Maximum layout capacity

Status: **Accepted**

- The current `500 × 500 cm` layout-generation path supports at most five tables.
- Six tables must fail before synthesis/repair instead of silently using stale templates.

## D007 — Quelladaptiver Rect Input mit Präsentationsrolle

Status: **Accepted — physische Raumvalidierung offen**

- Seit Johannes' Entscheidung am 2026-10-08 hat die gemeinsame axiale Source-Orientierung Vorrang bei der automatischen Präsentationsachse. 0°/180° gelten als dieselbe Tischorientierung; die Achse wird aus dem Mittel der doppelten Winkel abgeleitet und steht senkrecht zur gemeinsamen Tischlängsachse. Bei widersprüchlichen Orientierungen ohne eindeutige Resultierende bleibt die räumliche Hauptausdehnung maßgeblich. Eine ausdrücklich gewählte Präsentationsseite hat Vorrang.
- Der an einem Endpunkt räumlich am stärksten vom Rest abgesetzte Tisch wird zur Präsentationsrolle; die übrigen Tische werden ohne ID-basierte Rollen mit minimaler Bewegung als Zuhörerformation zugeordnet.
- Der Präsentationstisch blickt zu den Zuhörenden, die Zuhörenden blicken zur Präsentation.
- Jeder Rect-Tisch besitzt genau eine `70 cm` tiefe Sitz-/Bewegungsfläche an seiner semantischen Längsseite mit abgerundeten außenliegenden Ecken.
- Footprints und Sitz-/Bewegungsflächen müssen bei `100 %` vollständig in der ROI liegen und gegenseitig frei sein.
- Für Count 5 darf eine diagonal nicht passende Formation auf die nächstliegende Raumachse ausweichen; die präsentierende Source-Seite bleibt erhalten.
- `strength = 0` behält die exakte Source-Pose; Teilstärken bleiben Source/Target-Interpolation mit Tisch-Kollisions- und ROI-Reparatur.

## D007a — Synthetische teilnehmendenbasierte Input-Vorschau

Status: **In Entwicklung — opt-in Simulation auf gemeinsamer Rect-Input-Synthese**

- Die Teilnehmendenzahl beschreibt benötigte funktionale Sitzplätze, nicht erkannte Personen/Stühle.
- Ohne Aktivierung bleiben bestehende Input-Ziele und Chair-Quelle unverändert.
- Aktive Rect-Tische nutzen die bestehende quelladaptive Input-Synthese; inaktive Tische bleiben in stabiler Scene Order sichtbar und werden ROI-/footprint-sicher geparkt.
- Parken darf die gerichteten `70 cm` Sitz-/Bewegungsflächen aktiver Input-Tische nicht schneiden.
- Eine optionale Präsentationsseite prägt Sitzrichtung und bevorzugte Parkseite; ohne Vorgabe bleibt die quelladaptive Ausrichtung maßgeblich.
- Chair-Marker werden nur aus aktiven Tischrollen abgeleitet, liegen mittig in den gerichteten Sitzflächen und haben `25 cm` Radius.
- Zielverhältnis: zwei Personen pro aktivem Tisch. Erst wenn alle verfügbaren Tische aktiv sind, darf bis drei Personen pro Tisch verdichtet werden.
- Für fünf Rect-Tische gilt eine fachliche Input-Kapazität von `1–15`; darüber muss die Anfrage eindeutig abgelehnt werden.
- Die frühere Acht-Chair-Grenze der TD-Visualisierung ist aufgehoben: Die zentrale Struktur besitzt 15 Slots; OSC-Live-Reaktion und TD-Modussperren sind laut Handoff geprüft. Count 0 bleibt aus dem aktuellen Prüfumfang ausgenommen.
- Die physische Raumwirkung bleibt getrennt zu validieren.

Offline-Nachweis am 2026-10-07: 300/300 gemeinsame Geometriefälle bei 100 %,
300 Wiederholungen, 140 Scene-Order-Prüfungen und 60 Überkapazitätsablehnungen
bestanden. Präsentationsseite wird in der bestehenden Rect-Synthese
berücksichtigt; Chair-Richtung folgt auch bei Raumachsen-Ausweichlösung der
kanonischen Zielnormalen. Stärke 0 erhält sämtliche Source-Tischposen ohne
Parkreparatur. Details und physische Grenzen: [Prüfbericht](INPUT_GEOMETRY_VALIDATION.md).

## D008 — Rect Groupwork topology

Status: **Accepted und produktiv umgesetzt**

- Starre absolute Zielslots und orthogonale Winkelraster sind verworfen.
- `table_id` dient Identität und Wiederherstellung der ursprünglichen Scene Order, nicht Pair-Bildung oder Rollenvergabe.
- Jede Groupwork-Sitz-/Bewegungszone muss vollständig innerhalb der `500 × 500 cm` ROI liegen.
- Rect Pair-Seam: `8 cm`.
- Bisheriger table-only Stand: Ein Rect-Singleton erhält zwei mindestens `60 cm` tiefe Sitz-/Bewegungsstreifen über die vollständige Breite seiner Längsseiten, keine Stirnseiten-Sitzflächen; die zwei äußeren Ecken jedes Streifens sind mit `30 cm` Radius abgerundet. Für die neue teilnehmendenbasierte Groupwork-Planung wird der Ausschluss von Stirnseitenplätzen durch D008b abgelöst; die dafür benötigte Geometrie ist im teilnehmendenbasierten Modell umgesetzt.
- Ein Rect-Pair erhält eine elliptische, mindestens `60 cm` auskragende Clearance.
- Die Zielrotation eines Pairs erhält die axiale mittlere Orientierung seiner Source-Tische als starke Präferenz.
- Der produktive Suchkern enumeriert Counts `2–5`, prüft beide Pair-Mitgliederzuordnungen und optimiert freie lokale Gruppenmittelpunkte/Winkel.
- Auswahlpriorität: Zonenüberlappung, dann maximale und gesamte Verschiebung, Rotationsänderung, Kreuzungen und Inselabstand.
- Teilstärken werden mit derselben vollständigen Inselgeometrie repariert; eine ältere einseitige Standard-Clearance darf nicht zusätzlich als widersprüchliches Kriterium verwendet werden.

## D008b — Teilnehmendenbasierte Groupwork-Gruppen und Sitzprioritäten

Status: **Fachlich bestätigt durch Johannes am 2026-10-08 — Vorschau-/OSC-Anbindung im Code, Live-Prüfung offen**

- Primäre Eingaben sind `participants` und `number_of_groups`. Die Teilnehmenden werden möglichst gleichmäßig verteilt; Gruppengrößen unterscheiden sich höchstens um eine Person.
- Teilnehmergruppe und Tischcluster sind unterschiedliche Entitäten. Der Generator bestimmt die benötigten Tische; eine Teilnehmergruppe muss nicht genau einer zusammenhängenden Tischfläche entsprechen.
- Eine größere Teilnehmergruppe darf mehrere räumlich zusammengehörige Tischcluster nutzen, sofern ihre gemeinsame Gruppenzuordnung eindeutig bleibt. Die bestehende Inselzuordnung des Tischgenerators ersetzt diese Teilnehmergruppenzuordnung nicht.
- Zulässiges Beispiel, keine verpflichtende Aufteilung: Eine Gruppe mit sieben Personen nutzt ein Cluster aus zwei Tischen für vier Personen und ein weiteres Cluster aus einem Tisch für drei Personen.
- Allgemeine Sitzplatzpräferenz: zwei Personen pro nutzbarer Längsseite sind das Optimum; drei Plätze gelten als Verdichtung. Bei Groupwork zuerst reguläre Längsseitenplätze, danach geometrisch nutzbare Stirnseiten der Gruppe, erst danach verdichtete Längsseitenbelegung. Bei fünf Personen an einem Einzel-Rect sind `2 + 2` an den Längsseiten und ein Stirnseitenplatz gegenüber `3 + 2` an den Längsseiten zu bevorzugen.
- Kapazität muss aus tatsächlich freien Sitzplätzen, Footprints und Bewegungsflächen folgen. Weder eine fixe Tischzahl pro Teilnehmergruppe noch die Input-Grenze von 15 definiert die fachliche Groupwork-Kapazität. Die vorhandenen 15 TD-Chair-Slots sind eine separate technische Ausgabegrenze.
- Nächste Umsetzung: Teilnehmergruppen und Cluster getrennt zuordnen, Stirnseiten-Sitzflächen in die kanonische Geometrie aufnehmen und aktive/parkende Tische sowie sämtliche Chairs gemeinsam prüfen. Kriterien für eindeutige räumliche Gruppenzugehörigkeit und zulässige Verdichtung sind dabei konkret zu validieren; keine neuen Abstandsgrenzen allein aus dem Beispiel ableiten.

Offline-Prototyp am 2026-10-08: getrennte Teilnehmergruppen und Cluster,
Stirnseitenstreifen aus der vorhandenen abgerundeten 60-cm-Geometrie und
vollständige Chair-Kreisprüfung umgesetzt. Räumliche Zuordnung vorläufig
relativ geprüft: Verbindungskanten zwischen Clustern derselben Gruppe müssen
kürzer als sämtliche gruppenübergreifenden Clusterzentrum-Abstände sein.
Das ersetzt keinen visuellen oder physischen Nachweis eindeutiger Gruppenzugehörigkeit.
Tischwahl aktualisiert nach Johannes' Live-Stichprobe: optimal drei Personen
an einem einzelnen Tisch. Bei mehr als drei Personen pro Teilnehmergruppe
zuerst versuchen, einen weiteren Tisch zu einem Pair dazuzustellen.
Die neue Standardpriorität `group_capacity` vermeidet zuerst Einzel-Cluster
mit mehr als drei Personen, bevorzugt für größere Gruppen ein Pair, dann
geringe Verdichtung, wenige Tische und wenige Stirnseitenplätze.
Geometrisch unpassende Pairs werden nicht ausgegeben; drei bleibt ein Optimum,
keine harte Kapazitätsgrenze. Die frühere Standardwahl `few_tables` ist damit
abgelöst und bleibt nur als explizite Offline-Vergleichsoption verfügbar.
`2 + 2 + 1` gilt weiterhin als Sitzregel, wenn fünf Personen tatsächlich einen
Einzel-Tisch nutzen müssen; bei verfügbaren passenden Tischen wird nun ein Pair
versucht. Stirnseiten werden weiterhin vor verdichteten Längsseiten belegt.
Zusätzliche Darstellungskorrektur: getrennte Cluster und Parktische dürfen
auch mit ihren bestehenden 170 × 90 cm Bodenkonturen nicht überlappen.
Die physischen Rect-Footprints bleiben 160 × 80 cm; Sitzflächen und physische
ROI-Prüfung bleiben kanonisch. Innerhalb eines Pairs bleibt die 8-cm-Seam
unverändert, einschließlich der bewusst übergreifenden 5-cm-Konturränder.
Nach der Auswahl werden bestehende Cluster starr verschoben, um Konturkonflikte
zu lösen und den kleinsten Abstand zwischen Teilnehmergruppen zu verbessern.
Kein neuer Slotplan, keine neue Tischpermutation, keine Änderung der TD-Konturen.
Am 2026-10-08 nach visueller Kontrolle ergänzt: Unnötige Source-Positionswechsel
vermeiden. Im teilnehmendenbasierten Suchpfad werden gültige Kandidaten zuerst
nach maximaler und gesamter Source-Verschiebung, danach Rotation bewertet.
Singletons dürfen zusätzlich die axial nächstgelegenen Orientierungen der
vorhandenen Source-Tische verwenden. Kein festes Winkelraster und keine
nachträgliche globale Zielpermutation; Rollen werden bei der Clusterbildung
gebunden und bleiben danach erhalten. Die spätere Entzerrung beseitigt zuerst
Konturkonflikte, minimiert anschließend Source-Wege; zusätzlicher Gruppenabstand
ist nachrangig. Kanonische Sitz-/Bewegungsflächen bleiben harte Bedingungen.
Die bisherigen table-only Auswahlprofile bleiben unverändert.
Nach der Fünf-Gruppen-Live-Stichprobe vom 2026-10-08 ergänzt: Der
Singleton-Reparaturpfad nähert Source-Winkel bei Platzmangel schrittweise an
ROI-Achsen an und führt individuelle Winkel soweit möglich zur Source zurück;
kein unmittelbarer gemeinsamer 0°/90°-Fallback. Kanonische abgerundete Flächen
und Bodenkonturen entscheiden über die Zulässigkeit. Unveränderte Tischziele
bei wechselnden Counts sind zulässig, wenn Tischzahl und benötigte Sitzflächen
gleich bleiben. Geparkte Groupwork-Tische liegen im vollständigen Ziel mit
einer physischen Längsseite am ROI-Rand; die Entzerrung darf sie nicht wieder
nach innen schieben. Teilstärken und Stärke 0 behalten ihre bestehenden Regeln.
Johannes ergänzt nach der verbesserten Live-Stichprobe: Geparkte Groupwork-Tische
müssen mindestens 60 cm Abstand zu jedem aktiven Tisch haben, gemessen als
kürzeste Distanz zwischen physischen kanonischen Footprints. Dies gilt zusätzlich
zu freien Sitz-/Bewegungsflächen und Chair-Kollisionsfreiheit. Die Auswahl
minimiert zuerst maximale und gesamte Verschiebung aktiver Tische, erst danach
maximale und gesamte Parkverschiebung. Größere Parkwege sind damit ausdrücklich
akzeptabel. Parkplatzsuche und abschließende Validierung prüfen denselben
Mindestabstand; Stärke 0 bleibt ohne Reparatur ausgenommen.
Nach der `10/4`-Stichprobe ergänzt Johannes: Wenn vier Einzel-Tische mit einem
gültigen Parktisch nicht passen, soll der fünfte Tisch zu einem vorhandenen
Tisch geschoben werden. Bevorzugter Fallback ist ein Pair plus drei Singletons,
mit weiterhin vier Teilnehmergruppen und ohne Parktisch. Eine kleine Gruppe
auf zwei getrennte Singletons aufzuteilen ist nachrangig. Mehrere Cluster pro
Teilnehmergruppe bleiben für größere Gruppen oder geometrische Ausnahmen erlaubt.
Für die Topologie `2 + 1 + 1 + 1` wird bei erfolgloser Source-Winkelsuche dieselbe
begrenzte Annäherung an ROI-Achsen versucht; tatsächliche Source-Winkel bleiben
in den Ausgabedaten erhalten. Pair-Seam und sämtliche harten Grenzen gelten weiter.
Die opt-in Vorschau ist an den bestehenden OSC-Adapter angebunden; über 15
Teilnehmende werden dort wegen der technischen TD-Slots ausdrücklich abgelehnt.
Das Offline-Modell behält seine separate geometrische Kapazität.
Nachweise und nächste Prüfung: [Groupwork-Handoff](GROUPWORK_PARTICIPANTS.md).

## D008a — Validierung über die Simulationspipeline

Status: **Accepted**

- Jedes Layoutformat wird nach produktiver Umsetzung einzeln über Learning-Format-Interface, Simulationsadapter und OSC geprüft.
- Die interaktive Room-Editor-/TouchDesigner-Sichtprüfung bleibt ein eigener Schritt, wenn sie nicht automatisiert ausführbar ist.
- Ein kurzer formatübergreifender Durchlauf folgt erst nach den Einzelprüfungen.

## D009 — Discussion topology

Status: **Accepted**

- Discussion verwendet einen zentrierten, nach innen gerichteten Ring.
- Die absolute globale Ringrotation ist semantisch nicht relevant.
- Die Source-Winkelreihenfolge bleibt erhalten und stabilisiert Slotbindung sowie Teilbewegungspfade.
- Die freie globale Ringrotation minimiert lexikographisch maximale, dann gesamte Bewegung; Count 5 bleibt auf clearance-zulässige Phasen beschränkt.
- Jeder Rect-Discussion-Tisch erhält zwei außen abgerundete Längsseiten-Sitz-/Bewegungsflächen mit `50 cm` Tiefe.
- Diese Flächen müssen im fertigen `100-%`-Ziel vollständig in der ROI liegen und dürfen dort keinen anderen Tisch blockieren.
- Für Count 5 darf der gemeinsame Mittelpunkt geringfügig von der ROI-Mitte abweichen, damit Ring und Flächen passen.

## D010 — Scout Groupwork semantics

Status: **Deferred/Open**

- Do not hard-code a universal wide-wide, narrow-narrow, or wide-narrow Scout pairing rule.
- The geometry layer must support arbitrary later side pairings.
- Scout-specific seating and layout grammar require a dedicated design decision.

## D011 — Physical calibration protection

Status: **Frozen**

- Floor and tabletop homographies, local corrections, edge blend, projector transforms, masks/order, scale, and footprints are protected.
- Tabletop plane is `z = 74 cm`.
- Do not edit calibration as part of unrelated feature work.
- Physical correctness must be tested in the running authoritative `.toe` project and room.

## D012 — TouchDesigner source of truth

Status: **Accepted**

- The authoritative project is the manually maintained external `AISI_v2.toe`.
- Repository builders and `.toe` snapshots are references/reconstruction aids only.
- Never overwrite the master from builders without explicit instruction.

## D012a — Gemeinsame AISI-/Study-Gestaltung

Status: **Accepted — expliziter Auftrag von Johannes am 2026-10-07**

- Im AISI-Modus müssen Zieltischkonturen auf dem Floor erscheinen.
- Rect-Tische übernehmen den bestehenden Study-Stil: blaue durchgehende
  Source-Kontur, weiße gestrichelte Zielkontur und weiße Bewegungspfeile.
- Vorhandene AISI-Item-Geometrien und gemeinsame Study-Konturfunktionen
  verwenden; keine parallele Tischpipeline aufbauen.
- Die Chair-Gestaltung bleibt unverändert, bis sie separat spezifiziert wird.
- Study-/Tracking-Zweige, Masken, Kalibrierung und Projektorkonfiguration
  bleiben geschützt; physische Raumvalidierung bleibt separat.

## D013 — Rendering backends

Status: **Accepted**

- Interactive Room Editor: do not force a Matplotlib backend at import time; it uses `tkinter` directly.
- Headless plot generation: `Agg`, selected before importing `pyplot`.
- Shared plotting modules remain backend-neutral.

## D014 — Study task structure

Status: **Accepted as design intent**

T1–T4 are arranged as:

| | low/limited occlusion | increased occlusion |
| --- | --- | --- |
| simpler layout | T1 | T2 |
| denser layout | T3 | T4 |

This is a deliberate 2×2 design structure, not a single linear complexity scale. Whether density and occlusion are sufficiently orthogonal for factorial inference remains a methodological question.

## D015 — Study conditions

Status: **Frozen for current pilot**

- Floor-only and Dual-surface are within-study guidance conditions.
- The paper/method description must match actual rendering behavior.
- Do not characterize Dual-surface as “identical floor guidance plus extra tabletop information” if guidance is spatially redistributed between surfaces.

## D016 — Active trial version

Status: **Frozen**

- Active trial definition: `pilot_v7`.
- Matching snapshot: `trials_pilot_v7.json`.
- T1–T4 einschließlich A/B-Geometrie sind aus `pilot_v6` übernommen; `pilot_v7` ergänzt nur die Familiarization-Konfiguration.
- Any geometry change creates a new named snapshot before replacing `trials.json`.
- Session metadata records the active definition SHA-256.

## D017 — A/B transformation

Status: **Frozen**

- B preserves relative task geometry while changing viewpoint.
- T1/T3 use viewing axis `x = 250`.
- T2/T4 use viewing axis `y = 250`.
- Tests enforce the task-specific transformation and involution behavior.

## D018 — Study state mappings

Status: **Frozen**

- Mode: Tracking `0`, Study `1`, AISI `2`.
- Condition: Floor-only `0`, Dual-surface `1`.
- Phase: Home `0`, Ready `1`, Active `2`, Complete `3`.
- Preserve OSC addresses and numeric mappings.

## D019 — Objective arrival

Status: **Frozen for current implementation**

- translation error threshold: `≤ 8 cm`;
- rotation error threshold: `≤ 5°`;
- confirmation requires `0.5 s` continuously inside tolerance;
- objective arrival and participant-declared completion are distinct events.

## D019a — Familiarization vor der Study

Status: **Frozen for current pilot**

- Vor Block 1 liegt eine zeitlich offene Familiarization mit genau einem Rect-Tisch.
- Source: `(160, 250, 0°)`; Target: `(260, 250, 25°)`; neutraler Teilnehmerstart: `(250, 440)` mit `40 cm` Radius.
- `FLOOR_ONLY` und `DUAL_SURFACE` verwenden dieselbe Geometrie; Live-Wechsel ist erlaubt.
- Practice zählt nicht als T1–T4, erhöht `run_index` und `attempt` nicht und erscheint nicht in `study_metrics`.
- Practice-Rohdiagnostik bleibt zulässig und wird mit `study_workflow=FAMILIARIZATION`, `trial_role=PRACTICE`, `is_practice=true`, `task_id=FAMILIARIZATION` markiert.
- Familiarization ist eine TASK-Auswahl ohne eigene Workflow-, Reset- oder Finish-Schaltflächen.
- Auswahl von T1–T4 führt zu `READY_FOR_STUDY`, lädt den Trial und startet ihn nicht; der Start bleibt separat.

## D020 — Study outcome hierarchy

Status: **Proposed; not yet binding**

Recommended hierarchy:

- Primary: completion time plus a movement/efficiency measure.
- Secondary: position/rotation accuracy and objective arrival.
- Exploratory: initial action latency, corrections, arrival-to-completion behavior, and qualitative strategies.

Finalize before data collection/analysis claims. For a small pilot, emphasize effect sizes, uncertainty, and task-specific patterns over strong interaction claims.

## D021 — Tracking baseline

Status: **Frozen unless tracking work is explicitly requested**

- Current-room OBB tracking, table association, occlusion/reacquisition behavior, tracking-only projection, and adaptive smoothing form the present baseline.
- Do not tune thresholds or smoothing incidentally during layout or Study UI work.

## D022 — Runtime and participant data

Status: **Accepted**

- Runtime state, calibration captures, debug outputs, training artifacts, and Study run logs are not staged by default.
- No new participant-data storage, telemetry, upload, or network service without explicit approval.
