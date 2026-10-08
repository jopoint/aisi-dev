# AISI TODO

Stand: 2026-10-08

Use this file to choose the next coherent task. Do not execute all items automatically. Completed implementation history belongs in Git and the handoff documents, not in this checklist.

## NOW — Participant-based Input / TouchDesigner integration

**Source-Rotation im Rect Input — Auftrag vom 2026-10-07, offline behoben am 2026-10-08:**
- [x] Beobachtung am 2026-10-08 offline reproduziert: Alle fünf Source-Tische stehen horizontal (0°/180°), die Automatik erzeugt vertikale Ziele (±90°). Ursache ist die positionsbasierte Präsentationsachse mit Ost-Ausweichlösung, kein zusätzlicher Darstellungsversatz. Nord und Süd erhalten die horizontale Orientierung und bestehen die gemeinsame Geometrieprüfung. Source-/Target-Winkel im lokalen OSC-Recorder und 18 gespeicherte Geo-Bindungen aus Version 141 geprüft; kein neuer Live-Nachweis.
- [x] Nach Johannes' Zustimmung bevorzugt die gemeinsame Rect-Input-Synthese die axiale Source-Orientierung; Positionen bestimmen Präsentationsende und Rollen, explizite Seiten bleiben verbindlich. Die konkrete Live-Quelle ergibt jetzt fünf horizontale Ziele, 0° statt 450° gesamter axialer Rotation. D007 aktualisiert.
- [x] ROI, Kapazität, Chairs und gerichtete Sitz-/Bewegungsflächen erneut abgesichert: 300/300 gespeicherte Geometriefälle, 300 deterministische Wiederholungen, 140 Scene-Order-Prüfungen, 60 Überkapazitätsablehnungen sowie 57 fokussierte Tests bestanden. [Prüfbericht](docs/INPUT_GEOMETRY_VALIDATION.md).
- [x] Johannes bestätigt am 2026-10-08 die neue Rotationswahl in der Live-Stichprobe als sinnvoll. Zuvor wurde der doppelte alte Sender beendet; Bild anschließend ruhig. Diese Bestätigung betrifft die virtuelle Anzeige, keine physische Raumprüfung; keine zusätzliche Behauptung zu vollständigen Count-/Seitenkombinationen.

Neuer expliziter Auftrag: AISI-Zieltischkonturen müssen auf dem Floor
erscheinen; AISI-Elemente sollen gestalterisch dem bestehenden Study-Modus
entsprechen. Vorhandene AISI-Geometrien erweitern, keine parallele
Tischpipeline. Chairs bleiben vorerst unverändert, da ihre Study-Gestaltung
noch nicht spezifiziert ist. Aktuellen Livegraph gezielt lesen, danach
AISI-Auswahl des Floor-Renderers und betroffene Darstellung anpassen;
Study/Tracking, Masken und physische Projektion bleiben geschützt.
Umgesetzt im laufenden Projekt auf Basis von Version 138:
`apply_aisi_study_visual_style.py` meldet `passed: true`; Johannes bestätigt
Floor-/Tabletop-Ansicht. Geschützte Einstellungen, Chair-Bild und Table-Mask
unverändert; fünf Rect-Instanzen haben korrekte Konturprimitive. Drei
fokussierte Tests und Erhalt der Tracking-/Study-Floor-Pfade offline geprüft.
Aktueller manuell gespeicherter und dateisystemseitig verifizierter Stand:
`AISI_v2.141_coherent_chairs_validated.toe`. Johannes bestätigt den
fehlenden-Chair-Fehler nach expliziter Ring-Radius-Bindung als behoben;
Template + 15 Instanzen enthalten die Reparatur nachweislich in der Datei.
Ein erneuter Öffnungscheck von Version 141 bleibt ein separater Nachweis.


Geprüfter TD-Zwischenstand: `AISI_v2.137_coherent_chairs.toe` ist manuell
gespeichert und erneut geöffnet; der Ausgabecheck besteht. Gemeinsame
Chair-Geometrie mit 15 Slots und Count 7 ist geprüft. Die zentralen Viewer
unter `comp_layout_proposal` bleiben erhalten; alte externe Komponenten,
doppelte Debug-Geometrien und der alte Chair-Zweig in `comp_output` sind
entfernt. Referenzprüfung ohne Treffer und zehn Bilder bitgleich bei der
Bereinigung. Nach erneutem Öffnen: Floor Off bitgleich, beide Projektorpfade
reagieren auf On, Tabletop/Table-Mask bitgleich, regulärer Zusatz unabhängig
von Debug/Preview. Speichern erfolgt künftig ausschließlich manuell durch
Johannes. Count 15 und danach reagierende Count-Wechsel sind durch Johannes
beobachtet; der direkte Wechsel 3 → 15 → 3 nach erneutem Öffnen ohne Force-Cook
ist ebenfalls durch Johannes bestätigt. Der isolierte TD-Radius-null-Test
besteht (15 → 14 gültige Chairs, nur Chair 0 ausgeblendet, danach restauriert);
der entsprechende echte OSC-Test bleibt offen. Der Moduscheck wurde mit nachweislich regulären Chairs On wiederholt:
Tracking/Study/Calibration liefern Index 0, AISI liefert 1. Vollständige
bildliche Modusvergleiche bleiben offen. Verbleibende Livetests und die
aufgeschobene Raumprüfung sind getrennt von der bestandenen Offline-Prüfung.

1. [x] Zentrale gemeinsame 15-Chair-Struktur laut aktuellem Handoff geprüft; die frühere Acht-Slot-Grenze ist aufgehoben. Source, Target, Parktische und Chairs werden gemeinsam offline geprüft; keine zusätzliche TD-Bearbeitung in diesem Block.
2. [x] Wiederkehrenden Chair-Aktualisierungsfehler behoben und von Johannes nach den angefragten Count-Wechseln bestätigt.
   - Veralteten Python-Sender neu gestartet; veraltete Nullradius-Geometrie an Index 9 durch explizite SOP-Radius-Bindung für Template + 15 Instanzen korrigiert. Count 10 zeigt zehn Kreise; Stand manuell als Version 141 gespeichert und offline auf gespeicherte Bindungen geprüft.
   - Bisherige Counts 6, 9, 10, 11, 15 und Room-Editor-/OSC-Live-Reaktion sind bestätigt. Diagnose und Reparatur im [Chair-Debug-Handoff](docs/TOUCHDESIGNER_SYNTH_CHAIR_DEBUG.md).
   - Count 0 ist ausgenommen. Echte OSC-Radius-null-Prüfung und erneutes Öffnen von Version 141 bleiben getrennte Live-Aufgaben.
3. [x] Input-Kapazitäts-/Fehlervertrag offline geprüft: über `15` explizite Ablehnung vor Ausgabe, kein Ersatzlayout; bestehende `/chair/0…14/{x,y,radius}`-Float-Nachrichten mit lokalem Recorder geprüft. Echte OSC-Radius-null-Prüfung bleibt offen.
4. [x] Gemeinsame Table–Chair–Park-Geometrie offline validiert.
   - 300/300 Fälle: fünf Rect-Tische, Counts 1–15, vier Quellen und automatische/vier vorgegebene Präsentationsseiten, 100 %.
   - ROI, Tisch-/Chair-Kollisionen, Chair-Abstände und freie gerichtete Sitz-/Bewegungsflächen bestanden.
   - 300 deterministische Wiederholungen, 140 Scene-Order-Prüfungen und 60 explizite Überkapazitätsablehnungen bestanden; 59 fokussierte Tests bestanden.
   - Drei Plotübersichten und reproduzierbare Quellen im [Prüfbericht](docs/INPUT_GEOMETRY_VALIDATION.md). Count 0 ausgenommen, physische Raumprüfung aufgeschoben.
5. [x] Johannes bestätigt am 2026-10-08 die Chair-Umverteilung im Input bei Count-Wechseln als sinnvoll; qualitative Live-Stichprobe, keine Garantie minimaler Umverteilung für alle Quellen.
6. [ ] Physically validate the optional regular Floor-Chair output for visibility, position, size, masking, and projection behavior.
7. [x] Senderprüfung am 2026-10-08 nach gemeldetem Flackern: alter Sender PID 40517 und heutiger Sender PID 94900 liefen gleichzeitig auf Zielport 9000. Alten Sender beendet; danach genau eine Layout-Senderinstanz (PID 94900) verifiziert. Johannes bestätigt anschließend das ruhige Bild. Befunde im [Chair-Debug-Handoff](docs/TOUCHDESIGNER_SYNTH_CHAIR_DEBUG.md); beim Neuladen bestehenden Sender beenden statt eine zweite Instanz daneben starten.

## NEXT — Extend participant-based planning to other formats

Synthetische Chairs sind bisher nur für Input umgesetzt. Nächster Implementierungsblock ist Groupwork; danach Discussion. Der gemeinsame Formatwechsel-Check folgt erst nach der jeweiligen Chair-Implementierung und Einzelvalidierung. Physische Input-Raumprüfung und verbleibende isolierte TD-/OSC-Nachweise bleiben separat offen.

### Groupwork

- [x] Spezifikation vom 2026-10-08 aufgenommen: Teilnehmergruppe von Tischclustern trennen; mehrere räumlich eindeutig zusammengehörige Cluster pro Gruppe zulässig. Sitzpriorität: zwei Personen je nutzbarer Längsseite optimal → geometrisch nutzbare Stirnseiten → drei Plätze an einer Längsseite; fünf Personen am Einzel-Rect bevorzugt `2 + 2 + 1`. [D008b](docs/DECISIONS.md#d008b--teilnehmendenbasierte-groupwork-gruppen-und-sitzprioritäten).
- [x] Offline-Prototyp ergänzt: gleichmäßige Teilnehmergruppen, separate Cluster-/Chair-Zuordnung, kanonische Stirnseitenflächen, vollständige Table-/Chair-/Sitzflächen-/Parkprüfung. 65 fokussierte Tests und zehn Integrationsfälle bestanden; [Handoff](docs/GROUPWORK_PARTICIPANTS.md).
- [x] Tischwahl nach Live-Stichprobe aktualisiert: optimal drei Personen am Einzel-Tisch; größere Gruppen erhalten bevorzugt ein Pair aus zwei Tischen, sofern vollständig geometrisch gültig. Neuer Standard `group_capacity` ersetzt `few_tables`; Stirnseiten vor Verdichtung bleiben erhalten.
- [x] `participants` und `number_of_groups` möglichst gleichmäßig auf Teilnehmergruppen verteilen; benötigte Tischzahl und Cluster je Gruppe geometrisch bestimmen statt Teilnehmergruppe mit Insel gleichzusetzen.
- [x] Chairs mit getrennten Teilnehmergruppen-/Clusterzuordnungen aus freien Sitzflächen ableiten. Bestehende Singleton-Geometrie um die nun erlaubten Stirnseitenplätze ergänzen; Sitzprioritäten prüfen.
- [x] Offline-Modell an die opt-in Vorschau und den bestehenden OSC-Adapter angebunden; über 15 technische TD-Slots ausdrücklich ablehnen. Stärke 0 erhält exakte Source ohne Chairs/Reparatur; positive Teilstärken blenden vor vollständiger Reparatur bei gebundenen Gruppen-/Cluster-/Tischrollen.
- [x] Vorschau-/Adapter-Meilenstein offline geprüft: 52 fokussierte Tests, sechs Vorschautests nach Cache-Ergänzung erneut, 18/18 Adapterfälle (0/50/100 %, Editor-/Live-Quelle), lokale OSC-Aufzeichnung ohne echte Netzwerkpakete.
- [x] Aktualisierte Pair-Priorität offline geprüft: 16 Groupwork-Tests und zwölf Integrationsfälle, einschließlich 15 Personen/zwei Gruppen mit zwei Pairs; aktuelle Live-Quelle zusätzlich offline geprüft.
- [x] Bodenkontur-Überlappung der `14/4`-Live-Stichprobe offline behoben: bestehende 170 × 90 cm Darstellungsränder prüfen, getrennte Cluster ohne Rollenwechsel räumlich verbessern; 17 Tests und zwölf Integrationsfälle bestanden. Live-Bestätigung nach Neuladen noch offen.
- [x] Unnötigen Source-Positionswechsel der `14/4`-Stichprobe offline behoben: Source-Wege bei Clusterbildung/Entzerrung priorisieren, zusätzliche Source-abgeleitete Singleton-Winkel. Oben links bleibt am Ort; Gesamtweg rund 567 → 142 cm; 32 fokussierte Tests und zwölf Integrationsfälle bestanden. Live-Nachweis nach Neuladen offen.
- [x] Groupwork-Laufzeit offline optimiert: konkrete `14/4`-Quelle 70,7 → 10,4 s (6,8×), exakter Plan erhalten. Frühe kanonische Konfliktprüfung, sichere Bestwert-Grenzen, Wiederverwendung identischer Sitzprüfungen. 35 fokussierte Tests und zwölf Integrationsfälle bestanden; alle Vergleichspläne exakt erhalten. [Messung und Handoff](docs/GROUPWORK_PERFORMANCE.md).
- [x] Weitere Groupwork-Beschleunigung geprüft: konkrete `14/4`-Quelle 9,6 → 5,6 s (42 % weniger Zeit), exakter Plan erhalten. Weggrenze in der Entzerrung, kanonische Hüllrechteck-Vorprüfung, begrenzte reine Geometriecaches. 37 Tests bestanden; zwölf vollständige Vergleichspläne exakt erhalten.
- [x] Fünf-Gruppen-Fallback nach Live-Stichprobe korrigiert: Source-abgeleitete Winkel schrittweise annähern statt sofort alle Tische orthogonal auszurichten; kanonische abgerundete Flächen und Bodenkonturen gemeinsam reparieren. Geparkte Tische bei 100 % mit physischer Längsseite am ROI-Rand halten, von der Entzerrung ausnehmen. Einzelne Count-Änderungen müssen bei gleicher Tisch-/Sitzflächenzahl keine neuen Tischposen erzeugen. 34 fokussierte Tests und zwölf Integrationsfälle bestanden; zwei Vergleichsplots im Handoff vermerkt. Live-Nachweis nach manuellem Neuladen offen.
- [ ] Neue Groupwork-Laufzeit im laufenden Sender nach manuellem Neuladen prüfen; allgemeine Laufzeitgrenze und weitere Optimierung getrennt behandeln.
- [ ] Neue Groupwork-Vorschau einzeln im Room Editor, Lernformat-Interface und laufenden TD-Projekt prüfen; danach physische Prüfung. Bestehenden Sender beim manuellen Neuladen ersetzen, keine zweite Instanz starten.
- [ ] Kapazität, eindeutige räumliche Gruppenzuordnung, freie Bewegungsflächen, Clusterabstände, Chair-Geometrie und Parken gemeinsam offline validieren. Sieben-Personen-Beispiel mit zwei zusammengehörigen Clustern sowie Fünf-Personen-Beispiel `2 + 2 + 1` prüfen; TD-Slotlimit getrennt behandeln.

### Discussion

- [ ] Derive Chairs from the outward seating sides of the inward-facing ring tables.
- [ ] Define presentation/audience roles only if required by the format.
- [ ] Determine Discussion capacity from its geometry rather than copying the Input limit of `15`.

## Kontrollansicht für Layout-Stichproben

- [x] Manueller Helfer für `comp_layout_proposal/floor_tabletop_control` vorbereitet: Floor inkl. optionaler Chairs + bestehende blaue Tabletop-Source-Konturen + Tabletop-Motion-Pfeile. Syntax/Struktur offline geprüft, keine bestehenden Ausgaben geändert. [Anleitung](docs/TOUCHDESIGNER_LAYOUT_CONTROL.md).
- [x] Kontroll-COMP laut Johannes' Screenshot angelegt. Geometrieauswahl auf konkrete Slots `item1` bis `item5` begrenzt; Aktualisierung bestehender Kontrollansicht offline geprüft. Overlay übernimmt nun `render_tabletop`-Einstellungen mit ausschließlich Source-/Motion-Geometrien.
- [x] Johannes bestätigt die kombinierte Floor-/Tabletop-Kontrollansicht am 2026-10-08 als passend; kein physischer Projektionsnachweis.
- [ ] Reduktion der Referenzlinien im Network Editor separat bestätigen. Keine automatische Speicherung.

## NEXT — Manual layout validation

- [ ] Rect Groupwork: complete interactive Room Editor and TouchDesigner validation.
- [ ] Run one short cross-format pass for Input / Groupwork / Discussion covering format changes, Scene Order, full `100 %` targets, and OSC coupling.
- [ ] Perform remaining physical room validation for Input, Groupwork, and Discussion after virtual checks are stable.

## NEXT — Pilot / Study readiness

- [ ] Validate Familiarization in the authoritative TouchDesigner project and physical room, including live switching between Floor-only and Dual-surface.
- [ ] Physically run all eight `pilot_v7` experimental trials in both conditions.
- [ ] Verify HOME, READY, ACTIVE, and COMPLETE transitions in the authoritative TouchDesigner project.
- [ ] Verify Floor-only and Dual-surface visuals match the written method description.
- [ ] Verify active-table and distractor binding for T3/T4 under real tracking.
- [ ] Verify objective arrival (`8 cm`, `5°`, `0.5 s`) under real tracking jitter.
- [ ] Verify participant-declared completion remains independent from objective arrival.
- [ ] Verify logs, session manifest, attempt/run indices, tracking-loss intervals, and trial-definition hash.
- [ ] Review human-readable `trials.json` notes against numeric poses without changing frozen geometry casually.

Done when a participant-like session runs without manual data repair and visuals, tracking, controller state, and logs stay synchronized.

## NEXT — Freeze analysis plan before data collection

- [ ] State one primary research question comparing Floor-only and Dual-surface.
- [ ] State a secondary/exploratory question about task-specific differences.
- [ ] Describe T1–T4 as a 2×2 design structure without claiming unverified orthogonality.
- [ ] Define exactly what information appears on each surface in each condition.
- [ ] Choose primary, secondary, and exploratory outcomes.
- [ ] Decide whether the sample is framed as pilot/exploratory.
- [ ] Predefine treatment of aborted trials, tracking loss, missing objective arrival, and repeated attempts.
- [ ] Document apparatus accuracy, tracking frequency/latency, projection, and calibration sufficiently for the paper.

## OPEN DECISIONS — Johannes

- [ ] Is `pilot_v7` ready for data collection, or still a pre-pilot configuration?
- [ ] Which Study measures are formally primary versus secondary/exploratory?

## DEFERRED — Documentation

- [ ] Update the root `README.md`; current prototype-status, vision, geometry, and priority sections are outdated.
- [ ] Mark `docs/PROJECT_STATE_2026-05.md` clearly as historical or replace it with a dated current state.
- [ ] Link `docs/PROJECT_CONTEXT.md`, `docs/DECISIONS.md`, and `TODO.md` from the README.
- [ ] Ensure macOS and Windows launch instructions reflect actual supported workflows.
- [ ] Document current Study controller, active trial version, logging, and metrics commands.
- [ ] Keep physically confirmed facts separate from repository-only verification.

## DEFERRED — Focused regression commands

There is no canonical repository-wide command. Confirm and document the narrowest working commands for:

- Rect layout/geometry;
- Study trial definitions;
- Study control/state transitions;
- Study tracking/binding;
- Study logging/metrics;
- TouchDesigner builder structure tests;
- vision table association and tracking-only OSC.

Do not install optional dependencies merely to expand test scope.

## DEFERRED — General layout follow-up

- [ ] Verify mixed Summit/Sprint/Rect layouts after current Rect-specific work is stable.
- [ ] Design Scout-specific seating and Groupwork semantics as a dedicated task.
- [ ] Decide which Summit/Sprint sides may pair and how seating zones are derived.
- [ ] Preserve generic polygon support so the decision does not require a geometry rewrite.

## DEFERRED — Tracking

- [ ] Keep the current tracking baseline frozen until a reproducible failure is recorded.
- [ ] If tuning resumes, capture the failing scene/log first and compare against the successful reacquisition baseline.
- [ ] Separate detection, association, smoothing, projection alignment, and Study binding when diagnosing failures.

## DEFERRED — Repository hygiene

- [ ] Decide whether `.gitignore` should cover recurring debug/runtime folders.
- [ ] Never blanket-ignore intentionally versioned data such as frozen trial definitions.
- [ ] Keep model files, calibration captures, run logs, and generated plots under explicit policy rather than ad hoc staging.
