# AISI Project Context

Stand: 2026-10-08

## 1. Purpose and workstreams

AISI is a research prototype for adaptive, spatially augmented learning environments. It senses and tracks room objects, represents the room in a shared metric coordinate system, generates or loads target configurations, and communicates spatial transformations through projections on the floor and on tabletops.

The repository contains three related but distinct workstreams:

1. general AISI layout generation (`input`, `groupwork`, `discussion`);
2. the controlled dual-surface Study pipeline;
3. live computer vision/tracking and TouchDesigner integration.

Do not assume that a change in one workstream should alter the others.

## 2. Evidence levels

Use these labels when reporting status:

- **Repository-confirmed:** inspected or tested in the local checkout.
- **History-reported:** reported in prior project work but not re-run in the current task.
- **Physical-room-reported:** tested in the physical setup; cannot be established from repository checks alone.

The current worktree is the source of truth for code state. Branch, HEAD, and dirty-file status must be checked live with Git rather than stored here.

## 3. Coordinate system and physical setup

Repository-confirmed:

- world/ROI: `500 × 500 cm`, X and Y each spanning `0–500`;
- world center: `(250, 250) cm`;
- TouchDesigner scale: `1 cm = 0.0052 TD units`;
- TD mapping: `tx = (x_cm - 250) * 0.0052`, `ty = -(y_cm - 250) * 0.0052`;
- the simulation-to-OSC path negates source and target rotations before transmission.

Physical-room-reported:

- two Optoma UHZ36STe ceiling projectors;
- overlapping projection footprints with edge blending;
- separate floor and tabletop homographies per projector;
- tabletop plane at `z = 74 cm`;
- floor and tabletop calibration considered complete and protected;
- a nominal projected `50 × 50 cm` square measured approximately `50 × 49 cm` after calibration.

The calibration pipeline must not be changed as collateral work.

## 4. Main runtime paths

### General simulation/layout path

```text
Room Editor
→ data/aisi/scenes/simulated/live_scene.json
→ scene interpretation
→ target structure/layout synthesis
→ constraint repair
→ OSC
→ TouchDesigner
```

Main entry points:

- `aisi.app.sim_room_editor`
- `aisi.app.learning_format_server`
- `aisi.app.sim_scene_to_osc`

State files:

- `data/aisi/scenes/simulated/live_scene.json`
- `data/aisi/state/learning_format.json`

Validate each format individually through Room Editor, Learning-Format-Interface, and OSC before a short cross-format pass.

### Study path

```text
Study trial definition
→ Study controller/state machine
→ tracking binding and live source pose
→ OSC /study channels
→ TouchDesigner Study visuals
→ append-only JSONL logging
→ study_metrics analysis
```

Key files:

- `data/aisi/study/trials.json`
- `src/aisi/app/study_trials.py`
- `src/aisi/app/study_control.py`
- `src/aisi/app/study_tracking.py`
- `src/aisi/app/study_logging.py`
- `src/aisi/analysis/study_metrics.py`

Die aktive Study-Definition ist `pilot_v8`. T1–T3, Familiarization und sämtliche Teilnehmerstartpositionen bleiben unverändert aus `pilot_v7`. Nur alle T4-Tischposen werden gemeinsam um `+11 cm` in Welt-Y verschoben; X, Rotation und A/B-Transformation bleiben erhalten. Practice bleibt aus Trial-Zählern und `study_metrics` ausgeschlossen.

### Vision/tracking path

Current code is primarily under `src/vision/`; earlier sensing/replay infrastructure remains under `src/aisi_sensing/`.

Current baseline:

- Rect tables use OBB geometry transformed to world coordinates;
- multi-table association, occlusion handling, and reacquisition were stabilized;
- tracking-only projection renders an inner tabletop contour and outer floor contour;
- adaptive smoothing is lighter during motion and stronger at rest.

Treat tracking as frozen unless a task explicitly concerns tracking.

## 5. TouchDesigner architecture

The authoritative manually maintained project is external to the repository:

`C:\Users\johan\OneDrive\Dokumente\AISI_DEV\touchdesigner\AISI_v2.toe`

Repository builders and `.toe` snapshots are references, not guaranteed representations of the active physical graph.

Aktueller Chair-Stand am 2026-10-07:

- Aktueller manuell gespeicherter Stand am 2026-10-07: `AISI_v2.141_coherent_chairs_validated.toe`, von Johannes nach erfolgreicher Radius-Reparatur bestätigt und dateisystemseitig verifiziert. In einer temporär expandierten Kopie sind Radius-Bindung und Callback für Template + 15 Instanzen nachgewiesen. Der frühere bereinigte Stand 137 wurde erneut geöffnet und geprüft; ein erneuter Öffnungscheck von 141 wird nicht behauptet. Speichern bleibt ausschließlich manuell durch Johannes.
- Der optionale Floor-Zweig unter `comp_layout_proposal` erreicht beide bestehenden Projektorpfade.
- Der bestehende `chairs`-Zweig ist auf 15 Slots erweitert. Bei Count 7 sind sieben Radien positiv und acht Null; die Positionen werden laufend gebunden.
- Debug und regulärer Floor verwenden dieselbe zentrale Chair-Geometrie. Der Floor verwendet `cam1`, 2000×2000 und addiert Chairs über den zentralen Composite.
- Der manuell ausgeführte Bildvergleich besteht: optionaler Floor Off bitgleich, beide Projektorausgänge reagieren auf On, Tabletop/Table-Mask bitgleich und Debug-/Preview-Schalter unabhängig vom regulären Zusatz.
- Die Viewer sind im laufenden Projekt nach `comp_layout_proposal/chair_debug` und `comp_layout_proposal/tables_chairs_virtual_preview` (jeweils Container COMP) kopiert. Johannes bestätigt den Migrationscheck: alle vier Viewerbilder und die sechs geprüften Floor-/Tabletop-/Masken-/Projektorbilder bitgleich. Die anschließende Bereinigung ist ebenfalls bestätigt: keine externen Referenzen, alte Top-Level-Komponenten, doppelte Debug-Geometrien und alter Chair-Zweig in `comp_output` entfernt; alle zehn geprüften Bilder bitgleich. Der bereinigte Stand ist in Version 137 gespeichert und nach erneutem Öffnen geprüft.
- Count 15 liefert vollständige OSC-Daten und 15 gültige Instanzen; Johannes bestätigt nach dem Diagnosecheck 15 sichtbare Kreise und danach reagierende Count-Wechsel. Der zunächst beobachtete Stillstand bei sieben Kreisen ist noch nicht abschließend erklärt. Johannes bestätigt auch den direkten Wechsel 3 → 15 → 3 nach erneutem Öffnen ohne Diagnose-/Force-Cook.
- Der isolierte TD-Radius-null-Test besteht: bei 15 gültigen Chairs verschwindet nur Chair 0, die anderen 14 Radien bleiben unverändert und beide Chair-Render reagieren. Callback und Chair 0 sind wiederhergestellt; keine neue Datei gespeichert. Ein Radius-null-Test über echte OSC-Nachrichten ist damit noch nicht bestätigt.
- Modussperren nach Wiederholung mit nachweislich regulären Chairs On durch Johannes bestätigt: Tracking, Study und Calibration liefern jeweils Switch-Index 0, AISI liefert 1. Der erste Durchlauf war wegen Chairs Off nicht aussagekräftig. Vollständige bildliche Modusvergleiche stehen noch aus.
- Johannes bestätigt 8 → 3 sowie die Counts 6, 9, 10, 11 und 15. Count 0 lässt sich in der bestehenden UI nicht eingeben; der vorher pauschal bestätigte Wechsel 1 → 0 wird deshalb nicht als gesicherter Count-null-Nachweis gewertet. Der Übergang 15 → 0 bleibt ungeprüft; die UI wird dafür nicht erweitert.
- Änderungen im Room Editor werden laut Johannes live in TD übernommen. Damit ist die Reaktion über die OSC-Brücke beobachtet; ein einzelner ungültiger Chair über echte OSC-Nachrichten und physische Projektionskorrektheit sind damit nicht bestätigt.
- Neue Stichprobe am 2026-10-07: neun sichtbare Kreise bei Count 9 und ebenfalls neun bei Count 10, zusätzlich auffällige Platzverteilung und links angeschnittene Kreise. Die Python-Ausgabe für dieselbe aktuelle Source enthält korrekt 9/10 Chairs; Version 140 enthält offline 15 korrekt zeilengebundene Chair-Instanzen. Der Livefehler ist damit erneut offen, ohne die bestandene Offline-Geometrieprüfung zu widerlegen. Ein manueller lesender Check ohne Force-Cook liegt in `td_builders/inspect_shared_chair_live_state.py`; Live-Ausgabe steht aus. Geschützte Kamera-/Projektionsparameter wurden nicht angepasst.
- Die anschließende manuelle Live-Ausgabe bestätigt Count 10, zehn positive DAT-Radien und vollständige Übereinstimmung OSC → DAT → Instanzparameter. Die empfangenen Positionen reproduzieren jedoch exakt den alten Python-Code (bis Float32-Rundung); der Sender lief seit 15:53 vor den Korrekturen. Gezielter Neustart um 17:48 mit aktuellem Code, genau ein Sender nachgewiesen, laufend zehn Chairs gemeldet; Study-Control unverändert. Die angeschnittenen Kreise sind durch die alten ROI-verletzenden Positionen erklärbar. Sichtbare Vollständigkeit nach Neustart ist noch von Johannes zu bestätigen; gegebenenfalls tatsächliche Ring-SOP-Geometrie prüfen.
- Nach Neustart bestätigt Johannes weiterhin neun sichtbare Kreise bei Count 10; die linken Kreise liegen jetzt vollständig innerhalb der Ansicht. Der verbleibende Fehler betrifft vermutlich die tatsächliche Ring-Geometrie, noch nicht bewiesen. Gezielter manueller Punkte-/Radius-Abgleich in `td_builders/inspect_shared_chair_ring_geometry.py` vorbereitet; keine Cook- oder Parameterreparatur vorgenommen, Live-Ausgabe offen.
- Ringpunkte-Bericht bestätigt die Ursache: nur Index 9 besitzt trotz Instanzradius 0,13 TD noch Nullradius-Geometrie mit Außenradius 0,001 TD. Manuelle Reparatur `td_builders/repair_shared_chair_radius_dependency.py` vorbereitet: explizite SOP-Radius-Bindung über den vorhandenen Custom-Parameter Valuea, gleicher Ring-Callback mit geänderter Radius-Lesezeile, Template + 15 Instanzen, rücknehmbar. Offline geprüft; Live-Ausführung, wiederholte Count-Wechsel und anschließendes manuelles Speichern noch offen. Kein Force-Cook und keine geschützten Änderungen vorgesehen.
- Johannes hat die Radius-Reparatur in Version 140 manuell ausgeführt: 16 Ringe einschließlich Template gebunden, kein Force-Cook und keine Speicherung. Danach sind bei Count 10 zehn Kreise sichtbar. Wiederholte Übergänge 9 → 10 → 9 → 10 und 3 → 15 → 3 sowie ein neuer manuell gespeicherter Stand bleiben noch zu bestätigen.
- Johannes bestätigt anschließend den Fehler als behoben und zeigt die manuell gespeicherte Version 141. Die Datei enthält nach Offline-Expansion tatsächlich die explizite Radius-Bindung und aktualisierte Callback-Lesezeile für Template + 15 Instanzen. Fehlender-Chair-Fehler abgeschlossen; erneutes Öffnen, echte OSC-Radius-null-Prüfung und aufgeschobene physische Raumprüfung bleiben getrennte Nachweise.

Detailed TD debug-node history belongs in `docs/TOUCHDESIGNER_SYNTH_CHAIR_DEBUG.md`, not here.

Physical-room-reported structure:

- modes include Calibration and Content;
- Content can switch between Tracking and AISI/Study paths;
- floor content, tabletop content, and table masks share downstream calibration/projector stages;
- floor/tabletop/mask ordering is physically consequential;
- Calibration + Floor requires a black table-mask input so the inverted mask becomes white and leaves the floor image unchanged.

Rendering/backend rules:

- the interactive Room Editor uses `tkinter` directly and avoids forcing a Matplotlib backend at import time;
- headless PNG/debug generation selects `Agg` before importing `pyplot`;
- shared plotting modules remain backend-neutral.

### Motion Design v1.5 — isolierte Vorschau technisch geprüft (2026-10-23)

Die neue Motion-Content-Komponente liegt als separater Builder mit eigenen
Floor-/Tabletop-Ausgängen vor, noch ohne Anschluss an bestehende Ausgaben.
Referenz ist das von Johannes gelieferte Remotion-Paket v1.5. Zustandslogik
und Kontaktgeometrie sind offline geprüft. Johannes hat den Aufbau und die
technische Diagnose in TouchDesigner mit Python 3.9.5 bestanden: Zustands-TOP
6 × 6, beide Oberflächenausgänge und Preview 1000 × 1000, alle fehlerfrei.
Johannes bestätigt anschließend die sichtbare Demo im Operator-Viewer als
passend. Kamera-/Live-Anschluss und Laborprüfung stehen noch aus; die
anschließenden Simulations- und Grenzfallnachweise folgen unten. Johannes
vermittelt ausschließlich Textport-Befehle, kein Bildschirmzugriff.
Anschlüsse, abweichende OSC-/Item-Positionsvorzeichen, Nachweise und die
noch offenen Preview-/Live-/Laborprüfungen stehen im
[Motion-Integrationsstand](TOUCHDESIGNER_MOTION_DESIGN.md).

Johannes wählt als nächsten Schritt die Room-Editor-/OSC-Simulation.
Der separate Simulator und ein Anschluss ausschließlich an das neue
Motion-Preview sind vorbereitet, mit stabilen Tisch-IDs, expliziter
Layoutaktivierung und Timeout. Nur das neue OSC-Präfix `/aisi_motion/`
wird an den vorhandenen Empfänger gesendet. 26 Motion-/Transporttests und
acht bestehende Room-Editor-Tests bestehen; Johannes hat den manuellen
Simulationsanschluss ausgeführt und die korrekte Preview-Reaktion bestätigt.
Anschließend hat Johannes alle 19 deterministischen Grenzfall-Prüfungen
im temporären TD-Prüfzweig bestanden, einschließlich echter TOP-Pixel und
unabhängigem zweitem Tischzustand; der Prüfzweig wurde entfernt und nichts
gespeichert. Johannes bestätigt außerdem Übertragungspause/-fortsetzung und
erneute Aktivierung genau wie beschrieben. Drei- und Fünftisch-Szenarien
sind vorbereitet und offline auf Identität, unabhängigen Abschluss sowie
kollisionsfreie Source-/Ziel-Endzustände und deren Mischungen geprüft.
Die anschließende Dreitisch-Simulation zeigte einen Resetfehler der
Kontakt-Historie bei Reaktivierung. Korrigiert entsprechend der separaten
Visual-Historie in Remotion v1.5; 31 fokussierte Offline-Tests bestehen.
Johannes bestätigt alle 22 erweiterten TD-Zustands-/Pixelprüfungen und
korrekt wachsendes Grün bei allen drei Tischen. Auch nach Abschluss und
erneutem Verdrehen bleibt der Kontaktfortschritt erhalten. Temporärer
Prüfzweig entfernt, nichts gespeichert. Anschließend bestätigt Johannes auch
fünf sichtbare Tische, globale Reveal-Welle und unabhängige Abschlüsse im
Fünftisch-Simulator. Der Launcher ersetzt nur den zugeordneten Dreitisch-Sender;
das TD-Projekt wurde nicht gespeichert. Auf diesem Mac stehen laut Johannes
keine echten Trackingdaten zur Verfügung. Als nächster Schritt wird die
bestehende Content-Umschaltung mit Simulation vorbereitet; Kameraanschluss
und physische Raumvalidierung bleiben separate Laborschritte.
Die aktuelle Routing-Abfrage bestätigt `mask_tabletop` als Composite TOP
mit Multiply: Content an Eingang 0, bestehende Maske an Eingang 1. Die
Ausgabe-/Kalibrierungsschalter bleiben dahinter. Ein isolierter
`comp_aisi_motion_routing_preview` ist inzwischen in TD aufgebaut und
geprüft; sieben Offline-Routing-Tests bestehen. Der erste Aufbauversuch
brach vor Änderungen wegen dynamischer `resolutionw`/`resolutionh` der
Chair-Komposition ab. Die Kopie referenziert diese nun ausdrücklich über
absolute Pfade auf die ausgewerteten Originalparameter; andere dynamische
Parameter bleiben gesperrt. Die TD-Wiederholung hat alle sieben Prüfungen
bestanden: deaktiviert pixelgleich zu bisherigen Floor-/Tabletop-Bildern,
Maskenreihenfolge und Auflösungsreferenzen korrekt, aktuelle Moduswahl und
Chair-Auswahl korrekt; lokaler Enable-Wert wiederhergestellt. Er kopiert ausschließlich
Masken-/Chair-Kompositionen in einen neuen Prüfzweig und verändert keine
bestehenden Ausgaben. Die separate Motion-Simulation und die bestehende
Tischmaske beziehen ihre Posen bisher aus unterschiedlichen Datenpfaden;
daraus darf noch kein produktiver oder physisch korrekter Anschluss abgeleitet
werden. Die folgenden statischen Pose-/Pixelnachweise ersetzen keine
tatsächlichen Study-/Tracking-Bildvergleiche oder Raumprüfung.
Der anschließende Geometriebericht bestätigt fünf Rect-Zeilen in
`tables_active` mit numerischen Legacy-Slots und die bekannte orthografische
Kamera (2,6 TD-Einheiten). Entscheidend: Der aktive Maskenrenderer referenziert
`rect_setup_mask_geo_00` bis `05` unter `comp_study_visualization`, jeweils
doppelt; die untersuchte `item1/table_mask_geo` ist keine aktive Quelle dieses
Renderers. Die doppelte Auswahl wird nicht geändert. Ein weiterer Helfer
`build_motion_aligned_snapshot.py` prüft die tatsächlichen Maskentransformationen
gegen die aktive Tischliste und erstellt nur bei übereinstimmenden Posen eine
separate statische Motion-Probe. Er verwendet die vorhandene Umrechnung
`td_pose`, verändert keine alten Knoten und schaltet kein Routing um.
Der erste TD-Versuch brach bei fünf geringfügig abweichenden gespeicherten
Source-Posen ab (maximal 0,046 cm / 0,0171°). Die statische Probe nutzt nun
direkt die exakten Maskenposen; zuvor wird die Slot-Zuordnung rasterbezogen
innerhalb eines Pixels geprüft (0,25 cm bei 2000 Pixeln über 500 cm).
Translation und rotationsbedingter Randversatz werden gemeinsam begrenzt.
Bestehende Posen, Masken und Erfolgstoleranzen werden nicht verändert.
Zehn Offline-Tests bestehen, einschließlich der fünf gemeldeten Posen und
des vollständigen Preflights; die TD-Wiederholung ist bestanden. Der neue
`comp_aisi_motion_aligned_snapshot` wurde mit fünf exakt übernommenen Masken-
Sources, unveränderten Legacy-Targets und 2000 × 2000 Pixeln erstellt.
Keine Probleme gemeldet, bestehende Knoten und Routing unverändert, nichts
gespeichert. Numerische
Slots belegen weder dauerhafte Tracking-IDs noch Aktualität.
Der nächste Helfer `check_motion_aligned_routing.py` prüft eine temporäre
weiße Tischflächenprobe durch die vorhandene Masken-Komposition und misst
Formbeschnitt sowie helles RGB außerhalb der Maske. Nur bei technischer
Erfüllung schaltet er die beiden Select TOPs des isolierten Routing-COMPs
auf den statischen Snapshot und aktiviert dessen lokale Motion-Vorschau.
Produktive Outputs bleiben unverändert; bei Fehlern wird der lokale Zustand
wiederhergestellt. Der erste TD-Versuch brach vor den Prüfungen ab: Beim
Python-Import des Snapshot-Helfers löste dessen bisheriger Textport-Einstieg
erneut den Builder aus; der vorhandene Snapshot verhinderte die Erzeugung.
Import und Textport-Start sind nun über den Python-Importspec getrennt,
auch wenn TD `op` in Builtins bereitstellt. Die nächste übermittelte TD-
Ausgabe bestätigt beide Poseprüfungen; die Pixelprobe scheiterte anschließend
an einem direkten TOP-Kabel vom Routing-COMP in den Snapshot-COMP.
Korrigiert über einen temporären lokalen Select TOP, der die bestehende Maske
per Pfad liest; beide Composite-Eingänge liegen damit im Snapshot-Netzwerk
und werden vor dem Kochen geprüft. Elf fokussierte Offline-Tests und die
abgeleitete GLSL-Kompilation bestehen. Die anschließende TD-Wiederholung
hat alle sieben Prüfungen bestanden: 2000 × 2000 Pixel, 1.010.626 geprüfte
Tisch-Innenpixel vollständig erhalten (`interior_retained_fraction: 1.0`),
kein helles RGB außerhalb der Maske. 2024 Maskenpixel liegen außerhalb der
nominalen Source-Kontur; daraus wird keine Änderung abgeleitet. Die beiden
Snapshot-Ausgänge sind nun ausschließlich im isolierten Routing-COMP aktiv.
Temporäre Proben entfernt, nichts gespeichert und keine produktiven Outputs
geändert. Johannes hat anschließend Screenshots beider Ausgänge übermittelt.
Die optische Prüfung ist für diesen statischen Snapshot plausibel: Floor-
Targets werden von Source-Flächen ausgespart, am Tabletop sind vier grüne
Kontaktanzeigen und ein Navigationskreis ohne Grün sichtbar. Die weißen
Teilflächen entsprechen der Source-/Target-Überlappung; der ausgesparte
Pfeil zeigt den darunterliegenden grünen bzw. schwarzen Untergrund.
Johannes bemängelt anschließend zu Recht die identischen grünen Anfangsformen:
Der statische Snapshot startet bei bereits bestehendem Kontakt, setzt jeweils
`P0 = P` und zeigt damit `A = 0`. Seine fehlende Annäherungsgeschichte kann
Wachstum oder Zentrierung nicht nachweisen. Die vorherige positive Bewertung
gilt nur für statischen Maskendurchlass und Schnittflächen, nicht für grünes
Fortschrittsfeedback. Die Motion-Formel wird deshalb nicht verändert.
Ein dynamischer maskierter Simulationsprüfzweig ist vorbereitet:
`build_motion_dynamic_mask_preview.py` erzeugt einen neuen COMP, liest den
fortlaufenden State-TOP der bereits geprüften Room-Editor-Motion-Komponente
und steuert damit ausschließlich kopierte Maskengeometrien. Die lokale
Kopie des Maskenrenderers verwendet die ursprüngliche Kamera, aufgelöste
Licht-/Materialreferenzen und dieselbe aufgelöste Select-SOP-Fläche. Reorder
und Multiply werden ebenfalls nur kopiert. Originale und produktive
Ausgaben bleiben unverändert. Sechs neue Offline-Tests bestätigen unter
anderem den Unterschied zwischen Snapshot und Annäherungsgeschichte,
unabhängigen Fortschritt und die inverse Poseabbildung. Johannes hat den
TD-Aufbau anschließend ausgeführt und bestätigt ausdrücklich „jetzt ist es
richtig“. Der Screenshot zeigt rechts unten großflächiges, zentriertes Grün
und einen kleinen Navigationskreis, während andere Tische ihren Anfangszustand
behalten. Die Ausgabe bestätigt fünf frische Tisch-IDs, Maskenrenderer,
Reorder, maskiertes Tabletop und Out TOP jeweils 2000 × 2000 sowie Floor
1000 × 1000, alle im Builder fehlerfrei gekocht. Die Maskenfläche ist
`comp_study_visualization/rect_tabletop_inner_geo/table_surface`.
Originalknoten und Produktionsoutputs wurden nicht verändert, nichts durch
das Skript gespeichert. Diese Bestätigung betrifft dynamische maskierte
Simulation; statische Snapshot-Bilder bleiben kein Wachstumsnachweis.
Johannes meldet anschließend einen weiteren Grenzfall: Ohne Überschneidung
mit dem Target verschwindet im dynamisch maskierten Prüfzweig auch der
Navigationskreis. Die frühere Bestätigung betrifft somit Wachstum/Zentrierung,
keine vollständige Freigabe des maskierten Vor-Kontakt-Zustands. Ein gezielter
Offline-GPU-Render mit gültiger aktiver Source ohne Kontakt zeigt den Kreis
im unmaskierten Shader korrekt (2336 Alpha-Pixel über 0,5 im 500²-Testbild).
Der Helfer `inspect_motion_navigation.py` vergleicht für die tatsächliche
Fehlerstellung State/Phase/Aktivierung, unmaskiertes Bild, Maskenbild und
maskiertes Bild sowie kopierte SOP-Grenzen. Er verändert keine Knoten oder
Parameter. Kontrollierte TD-Proben mit/ohne Kontakt bestehen mit praktisch
vollständigem Flächenerhalt durch die Maske. Die folgende Live-Abfrage
zeigt den Kreis auch ohne Kontakt; Johannes bestätigt jedoch, dass er erst
nach dem erzwungenen Diagnose-Cook sichtbar wurde. Die indirekten
Pose-Abfragen per DAT-Modul/`numpyArray()` erhalten deshalb eine explizite
`absTime.frame`-Abhängigkeit. `update_motion_mask_dependencies.py` hat alle
20 Pose-Ausdrücke ausschließlich der kopierten Simulationsmasken aktualisiert,
ohne Engine-Reset, Force-Cook, Original-/Produktionsänderung oder Speicherung.
Johannes bestätigt danach die angefragte Bewegung ohne Diagnosebefehl als
funktionierend. Neun fokussierte Offline-Tests und Python-3.9-Syntaxprüfung
bestanden; dieser virtuelle Grenzfall ist damit abgeschlossen.
Johannes fordert danach eine rundere grüne Form nahe der Zielmitte, damit
beim Überfahren kein Richtungsumschlag sichtbar wird. Der Shader blendet
alle gerichteten Verformungen zwischen 29 und 8 cm weich aus; innerhalb
der bestehenden 8-cm-Positionstoleranz ist die Form zentriert/rund, auch
bei verbleibendem Winkelfehler. Diese gewünschte visuelle Weiterentwicklung
von v1.5 verändert keine Kontakt-/Erfolgsschwelle oder Fortschrittsgeschichte.
Acht GPU-/Installer-Tests bestehen; `update_motion_halo_shape.py` erhält
den laufenden Zustand und andere lokale Shaderänderungen. Johannes hat den
Shader im laufenden TD erfolgreich installiert/kompiliert und bestätigt den
angefragten Mittelpunktdurchgang anschließend mit „ja jetzt stimmt es“.
Kein Engine-Reset, keine Masken-/Produktionsänderung, nichts gespeichert.
Diese visuelle Simulationsabnahme ersetzt keine physische Raumprüfung.
Die abschließende erweiterte TD-Regressionsabnahme besteht anschließend bei
Johannes mit allen 25 Kriterien, einschließlich Halosymmetrie,
Richtungsunabhängigkeit beim Mittelpunktdurchgang und stetigem Formübergang.
Temporäre Prüfkomponente entfernt, nichts gespeichert, physische Validierung
nicht ausgeführt. 77 fokussierte Offline-Tests und vier separat ausgeführte
native GPU-Tests bestanden. Der bestätigte Simulationsstand bleibt vom noch
ausstehenden echten Trackinganschluss getrennt.
Der neue, noch nicht angeschlossene Zustandskern
`aisi.app.motion_live_adapter.MotionLiveAdapter` konsumiert kalibrierte
FrameEvents direkt. Dadurch werden fehlende IDs nicht aus dem 15-Frame-Cache
der bestehenden Szenenbrücke übernommen. Zwei fortschreitende Kamera-Frames,
Zeitstempel und Kalibrierungsidentität sichern den Eingang; gleiche Frames
verlängern das 0,5-s-Zeitlimit nicht. Ziele und Aktivflags werden nur durch
explizite Aktivierung mit neuer Revision eingefroren. Kamera-Neustart oder
Kalibrierungswechsel verlangen Reset und erneute Aktivierung. AISI-Weltachsen
bleiben unverändert; der Abgleich zur tatsächlich gerenderten TD-Maske und
der produktive Anschluss sind ausdrücklich noch nicht durchgeführt.
16 neue Offline-Tests einschließlich synthetischem OSC-Durchlauf sowie zehn
bestehende Vision-Brückentests bestanden. Die rein lesende Modul-CLI prüft
nur neu angehängte Kamera-Frames, sendet nichts und aktiviert kein Layout.
Johannes beauftragt danach die technische produktive Umschaltung bereits
vor dem Laboranschluss. Der aktuelle Graph ist erneut ausgelesen.
`build_motion_output_routing.py` bereitet zwei reversible Content-Einfügepunkte
vor: Floor-Basis-Select vor der vorhandenen Chair-Komposition und Tabletop-
Null vor der unveränderten Originalmaske. Zehn Offline-Modelltests bestehen;
separater Prüfer und Rückbau verfügbar. Beide Freigabeschalter starten aus,
der Builder verlangt drei pixelgleiche Legacy-Ausgabebilder sowie unveränderte
Originalparameter/-verbindungen außerhalb der zwei erlaubten Stellen.
Johannes hat die Einbindung anschließend im laufenden TD installiert:
`installed: true`, drei Pixel-Bypass-Prüfungen und Vergleich des geschützten
Graphen bestanden. Der separate Prüfer besteht mit allen sieben Kriterien,
einschließlich pixelgleichem Floor-/Tabletop-Bypass, Originalauflösungen
und fehlerfreien Floor-/Tabletop-/Masken-Ausgabeschaltern. `Enablemotion`
und `Sourceapproved` bleiben aus. Die produktive Verdrahtung ist damit
vorhanden, weiterhin mit Legacy-Bild. Originalmaske, Chair-Komposition,
Kalibrierung und Projektortransforms unverändert, nichts gespeichert.
Johannes beauftragt anschließend einen Simulationstest durch diese produktive
Kette. Start-/Prüf-/Stop-Skripte ergänzen einen temporären gemeinsamen Schalter
für Content und das passende dynamische Simulationsmaskenbild vor dem
unveränderten Originalmaskenoperator. Ein zusätzlicher Maskenbild-Eingang
wird zeitweilig umgeschaltet; Originalgeometrien, Kalibrierung, Reihenfolge
und Projektorparameter bleiben erhalten. Echte Quellenfreigabe bleibt aus,
Tracking/Study/Kalibrierung wählen Legacy und Originalmaske. Der Stop stellt
den zuvor geprüften deaktivierten Router wieder her. 20 fokussierte
Routing-/Simulationstests zunächst bestanden. Der erste TD-Start meldet
danach fehlende frische Simulationsframes und bricht vor jeder Umschaltung
ab; keine Testsitzung registriert, Legacy-Bild bleibt erhalten. Die reine
Quellen-Diagnose `check_motion_simulation_source.py` grenzt Sender-/Frische-
zustand ein. Start/Stop behandeln diesen Zustand jetzt ohne Traceback;
21 Routing-/Simulationstests und vier Launcher-Tests bestanden. Die direkte
Quellendiagnose bestätigt nach Öffnen des isolierten Previews frische Frames
aller fünf Tisch-IDs, aktive OSC-Eingabe und laufenden eigenen Sender;
kein Neustart erforderlich. Ein erneuter kombinierter Start läuft dennoch
in den Timeout. Die umfangreichen synchronen GPU-Prüfungen vor dem erneuten
State-Cook sind die plausible Ursache einer im selben TD-Frame gecachten
OSC-Quelle. Vorbereitung und Aktivierung sind daher getrennt: erst
deaktivierter GPU-/Bypass-Aufbau, dann in späterem TD-Frame gezielt OSC-In,
Raw-CHOP und State aktualisieren. Aktivierung verlangt eine neue frische
Signatur gegenüber der Vorbereitung und enthält keine GPU-Pixelabfragen.
Timeout bleibt 0,5 s; Pixelprüfung folgt separat und setzt bei Abweichung
den geprüften Test zurück. 25 Routing-/Simulationstests bestanden.
Die zweiphasige Aktivierung ist im laufenden TD bestanden: Vorbereitung mit
drei Bypass-Pixelprüfungen in Frame 1378043, Aktivierung in Frame 1379345
mit frischer Signatur (2548711, 279512) und fünf Tisch-IDs. Floor, Tabletop
und Simulationsmaske stehen gemeinsam auf Index 1; Johannes bestätigt
sichtbaren neuen Content. Die temporäre Testsitzung ist aktiv. Die separate
aktive Ausgabeprüfung hat alle sechs Kriterien bestanden: aktiver Maskeneingang
pixelgleich zur dynamischen Simulationsmaske und Tabletop durch die Originalmaske
pixelgleich zum dynamischen Prüfzweig (maximaler Pixelfehler 0,0). Kalibrierung,
Chair-Komposition und Projektorparameter laut Strukturprüfung unverändert.
Bewegung durch die produktive Kette ist noch manuell zu bestätigen.
Die reale Quelle bleibt nicht freigegeben. Keine automatische Speicherung und
keine physische Validierung.
Aktive reale Quelle, tatsächliche Modus-Bildvergleiche
und Raumabnahme bleiben offen. Der lokale
TD-Stand ist weiterhin ungespeichert; eine neue benannte Arbeitskopie manuell
sichern. Nächster unabhängiger Block ist die Anbindung echter Trackingdaten
im Labor, mit stabilen IDs,
Paketaktualität und explizitem Layout-Ereignis.
Die normale Szene wird nicht überschrieben.

### Layout-Anschluss der Motion-Simulation — 2026-10-23

Johannes präzisiert die Labor-Abschaltung: Ziele sollen während Bewegung
nicht nachberechnet werden; beim Aktivieren ist quelladaptive Berechnung aus
den Istposen erlaubt (D005a). `motion_layout_proposal.py` verwendet die
bestehenden Generatoren in Scene Order und übernimmt Tischziele und Chairs
zusammen. Berechnung läuft im Worker; OSC sendet währenddessen weiter den
bisherigen Vorschlag. Commit erfolgt im Editor-Thread, nur bei unveränderter
Tischmenge. Keine automatische Neuberechnung durch Bewegung oder UI-Änderung.

`motion_preview_sim --generated-layouts` liest beim Klick die vorhandene
Learning-Format-State-Datei; Opt-in, Format, Teilnehmende, Gruppen,
Präsentationsseite, Chairs und Umbauintensität werden erhalten. Ohne
Teilnehmenden-Opt-in bleibt die Ausgabe ohne synthetische Chairs. Start ohne
aktivierten Vorschlag ist leer. Fehler ändern weder Ziele noch Revision.
Alle neuen Nachrichten bleiben unter `/aisi_motion/`; alte `/table`, `/chair`
und `/study` werden nicht beschrieben. Chair-Daten gehören zu derselben
Session, Frame und Revision wie die Tische; veraltete/unvollständige Pakete
werden ausgeblendet.

Eine eigene Chair-Komponente zeichnet die weißen Marker mit 2,5 cm Stärke
und erhält ihre Außenradien. Sie wird im registrierten Simulationstest über
einen zusätzlichen reversiblen Eingang vor die bestehende Chair-Komposition
geschaltet. Umschaltung folgt demselben AISI-/Kalibrierungsgatter wie Content
und Simulationsmaske. Study-/Tracking-/Kalibrierungsmodus verwendet die alte
Chair-Quelle; Rückbau stellt den ursprünglichen Composite-Eingang wieder her.
Kalibrierung, Originalmasken, Projektoren und die bestehenden Generatorregeln
werden nicht geändert. Der bestehende Chair-Ein-/Ausschalter bleibt erhalten.

Vorbereitung: `td_builders/prepare_motion_layout_simulation.py` beendet den
registrierten Ausgabetest, baut/reverwendet die geprüfte eigene Chair-Komponente,
ersetzt ausschließlich den eindeutig zugeordneten Simulator durch den
Fünf-Tisch-Modus mit generierten Layouts und bereitet den deaktivierten
Ausgabetest vor. Aktivierung in späterem TD-Frame, anschließend Vorschlag im
Room Editor aktivieren und separat `output_test.verify(op)` ausführen.
Offline mit echten Generatoren alle drei Formate bei fünf Tischen/acht
Teilnehmenden/100 % und die aktuellen lokalen Discussion-Einstellungen
(13 Teilnehmende/88 %) berechnet. Insgesamt 62 fokussierte Prüfungen bestanden,
einschließlich drei nativer Zwei-Textur-GPU-Prüfungen.
Installation/Pixelprüfung und Format-/Bewegungsabnahme dieses neuen
Anschlusses im laufenden TD sowie physische Raumvalidierung stehen noch aus.

## 6. Canonical geometry

Repository-confirmed table types:

| Type | Physical reference | Shape |
| --- | --- | --- |
| `summit` | approximately `157 × 70 × 74 cm` | trapezoidal |
| `sprint` | approximately `82 × 60 × 74 cm` | trapezoidal |
| `rect` | `160 × 80 × 74 cm` | rectangular |

The polygon-aware geometry migration is complete. Canonical footprints/supports are used for collision, ROI, clearance, repair, and debug rendering.

Important implementation invariants:

- format roles remain bound to `table_id`;
- target output returns to original scene order;
- `strength = 0` yields exact source poses without repair;
- `strength > 0` blends before one final hard-constraint repair;
- overall layout-generation capacity is five tables.

For binding design rules, seating/clearance semantics, and format-specific constraints, see the relevant entries in `docs/DECISIONS.md`.

## 7. Current Rect layout-generation state

### Input

The fixed Rect Input slots have been replaced by a source-adaptive presentation-plus-audience formation.

Current state:

- Automatische Präsentationsachse seit 2026-10-08: gemeinsame axiale Source-Orientierung bevorzugt, Positionen bestimmen Präsentationsende und Rollen. Ohne eindeutige Orientierungsresultierende gilt die räumliche Hauptausdehnung; eine explizite Präsentationsseite bleibt verbindlich (D007).
- presentation role is inferred spatially rather than from `table_id`;
- active Rect tables use one semantic long-side seating/movement surface;
- Die gemeinsame Rect-Input-Synthese berücksichtigt diese Orientierungspräferenz im normalen und im Vorschaupfad; teilnehmendenbasierte Teilmenge, Parken und Chairs bleiben opt-in.
- virtual Room Editor / Learning-Format / OSC / TouchDesigner checks have been accepted;
- physical room validation remains open.

### Participant-based Input preview

Johannes bestätigt am 2026-10-15 Input für den Moment als passend. Qualitative
Rückmeldung zur aktuellen Anzeige; keine zusätzliche vollständige Count-/Seiten-
oder physische Raumprüfung. Gemeinsamer Formatwechsel-Check bleibt offen.

Der explizit aktivierte Simulationspfad plant aktive und geparkte Rect-Tische
nach Teilnehmendenzahl und leitet Chair-Marker aus ihren gerichteten Sitzflächen ab.

- Zielverhältnis: zwei Teilnehmende pro aktivem Tisch; erst mit allen verfügbaren Tischen bis zu drei pro Tisch, damit `1–15` bei fünf Rect-Tischen.
- Überkapazität scheitert ausdrücklich mit `LayoutConstraintError` vor Ausgabe; kein stilles Ersatzlayout.
- Parktische bleiben sichtbar, Ziele folgen der Source Scene Order; interne Auswahl und Chair-Reihenfolge sind ID-stabil.
- Chair-Kreise haben `25 cm` Radius und liegen vollständig in den kanonischen gerichteten `70 cm` Sitzflächen. Ihre Richtung folgt der Zielnormalen auch nach Raumachsen-Ausweichlösung.
- Die optionale Präsentationsseite wird in der bestehenden Rect-Synthese berücksichtigt; ohne Vorgabe bleibt die Source maßgeblich.
- Transformationsstärke 0 erhält auch geparkte Tischposen exakt, ohne Reparatur. Die vollständige gemeinsame Sitzflächenprüfung gilt für 100 %.
- Offline am 2026-10-07: 300/300 Fälle bestanden (vier Quellen × fünf Ausrichtungen × Counts 1–15), 300 deterministische Wiederholungen, 140 Scene-Order-Prüfungen, 60 Überkapazitätsablehnungen und 59 fokussierte Tests. Nachweise und Grenzen: [Prüfbericht](INPUT_GEOMETRY_VALIDATION.md).
- Zentrale TD-Struktur mit 15 Slots, OSC-Live-Reaktion und Modussperren sind laut Handoff geprüft. Count 0 ist ausgenommen; echte OSC-Radius-null-Prüfung und physische Raumvalidierung bleiben offen.
- Ohne Vorschau bleiben normale Chair-Daten und andere Formate unverändert.

Bei späteren Live-Prüfungen darf genau eine `sim_scene_to_osc`-Instanz auf
Port `9000` senden. Diese Validierung hat keinen Sender gestartet.

### Groupwork

Neue Spezifikation vom 2026-10-08, als Offline-Prototyp umgesetzt: `participants`
und `number_of_groups` bestimmen möglichst gleich große Teilnehmergruppen.
Eine Teilnehmergruppe darf mehrere räumlich zugehörige Tischcluster nutzen.
Die bisherigen Insel-`groups` des Geometriegenerators sind keine vollständige
Teilnehmergruppenzuordnung. Reguläre Stirnseitenplätze erhalten Vorrang vor
verdichteten Längsseitenplätzen; zusätzliche kanonische Stirnseitenstreifen
werden im neuen Offline-Modell bei Belegung geprüft. 65 fokussierte Tests und
zehn Integrationsfälle bestanden. Johannes aktualisiert die Tischwahl nach
der Live-Stichprobe: drei Personen optimal am Einzel-Tisch, darüber bevorzugt
ein Pair, sofern passend. Standard `group_capacity` ersetzt `few_tables`;
nutzbare Stirnseiten bleiben vor verdichteten Längsseiten bevorzugt. Die opt-in
Vorschau/OSC-Anbindung ist im Code ergänzt; Stärke 0 ohne Chairs/Reparatur,
positive Teilstärken mit Blend-before-repair und gebundenen Rollen. Über 15
Chairs werden im Adapter als technische Ausgabegrenze abgelehnt.
Getrennte Cluster werden zusätzlich auf überlappende 170 × 90 cm
Bodenkonturen geprüft und anschließend ohne Rollenwechsel räumlich entzerrt.
Die physische Geometrie und Pair-Seam bleiben unverändert.
Die Clusterwahl minimiert weiterhin den Gesamtweg. Die abschließende starre
Entzerrung nutzt freie Fläche für ein weiches 60-cm-Ziel zwischen Bodenkonturen
verschiedener Teilnehmergruppen (bestehende Sitzflächentiefe); zusätzliche Wege
sind bis dahin zulässig, danach wieder nachrangig. Das Ziel ist keine harte
Ablehnungsbedingung. In der aktuellen `15/4`-Quelle steigt der kleinste
Gruppenabstand von 0,5 auf 60,4 cm bei rund 2,4 s Offline-Laufzeit.
Pair-Seam, Sitzflächen, ROI und Parkregeln bleiben erhalten;
Singletons erhalten zusätzliche Source-abgeleitete Winkelkandidaten.
Der Vier-/Fünf-Singleton-Reparaturpfad nutzt inzwischen begrenzte Winkelannäherung
statt eines direkten gemeinsamen orthogonalen Fallbacks und prüft abgerundete
kanonische Flächen. Geparkte Groupwork-Tische stehen bei 100 % mit ihrer physischen
Längsseite am ROI-Rand und bleiben von der anschließenden Entzerrung ausgenommen.
Zusätzlich halten Parktische mindestens 60 cm physischen Kantenabstand zu aktiven
Tischen. Bei gleicher fachlicher Topologie-/Belegungspriorität minimiert die Zielauswahl
den Gesamtweg aller Tische; aktive Wege dienen danach als Gleichstandsentscheidung.
Groupwork-Parken darf mehrere ROI-Ränder nutzen, wenn dies den Parkweg verkürzt.
Bei fehlendem Parkplatz erhält ein zusammenhängendes Pair mit drei Singletons
Vorrang vor fünf getrennten aktiven Tischclustern für nur vier Gruppen.
Die Topologie `2 + 1 + 1 + 1` erhält dafür eine begrenzte Winkelannäherung als
Fallback; Rollen, ursprüngliche Source-Winkel und Scene Order bleiben erhalten.
Eine neue lokal festgefahrene `15/5`-Source wird nach erfolgloser normaler Suche
mit zusätzlichen Source-abgeleiteten Mittelpunkt-/radialen Startpositionen repariert.
Alle kanonischen Geometriebedingungen bleiben unverändert; kein Parkabstandsproblem.
Bei gleicher Tischzahl/Topologie wird das Pair bevorzugt stärker belegt;
`10/4` soll eine Dreiergruppe am Pair und `3 + 2 + 2` an Singletons erhalten,
sofern die vollständige Geometrie passt.
Rollen bleiben nach der Clusterbildung gebunden; keine globale Zielpermutation.
Johannes bestätigt die aktuelle `10/4`-Vorschau visuell als passend.
Der gemeinsame Offline-Abschlusscheck besteht 130/130 Anfragen (Counts 1–15,
zulässige Gruppen 1–5, Editor-/Live-Quelle), einschließlich gemeinsamer Geometrie,
Identität, Scene Order und Determinismus. Kapazitätsbeispiele und technische
15-Slotgrenze sind separat geprüft. Eine Editor-Sackgasse bei `13/4`–`15/4` wird
nach Reparaturfehlschlag durch erneute Kandidatensuche mit voller Konturprüfung
gelöst; zuvor gültige Pfade bleiben unverändert. 52 fokussierte Tests bestanden.
[Abschlussbericht](GROUPWORK_ABSCHLUSSCHECK.md); Live-Stichprobe der neuen
Konturreparatur, vollständige interaktive Einzelvalidierung und gemessene
Live-Laufzeit bleiben offen. Die Offline-Suche ist inzwischen durch frühe
kanonische Konfliktprüfung, unveränderte Bestwert-Auswahl und auf einen Aufruf
begrenzte Chair-Prüfcaches beschleunigt; Vergleichspläne bleiben exakt gleich.
Die zweite Stufe ergänzt sichere Weggrenzen in der Entzerrung sowie kanonische
Hüllrechteck-Vorprüfung und begrenzte, vollständig koordinatenabhängige
Geometriecaches.
Die dritte Stufe zieht im Teilnehmerpfad Sitzflächenkonflikte vor und bricht
unmögliche Teilkombinationen vor weiteren Anhängen ab. Konkreter `10/4`-Fallback
31,9 → 5,9 s offline, vollständiger Plan unverändert; 46 Tests bestanden.
Siehe [Laufzeit-Handoff](GROUPWORK_PERFORMANCE.md). Details: D008b und
[Groupwork-Handoff](GROUPWORK_PARTICIPANTS.md).

Source-adaptive Rect Groupwork for counts `2–5` is productively implemented.

Current state:

- all Pair/Singleton partitions are derived from source geometry;
- fixed slots, ID-based pairing, and orthogonal target-angle grids are obsolete;
- Pair seam is `8 cm`;
- Singleton and Pair clearance geometry follows the accepted rules in `D008`;
- source orientation strongly influences Pair target orientation;
- focused repository and OSC/simulation checks have passed;
- interactive Room Editor, TouchDesigner, and physical room validation remain open.

### Discussion

Stand der teilnehmerabhängigen Opt-in-Chair-Vorschau: 2026-10-15.

- 1–4 Personen: zwei parallele Rect-Tische mit 10 cm Spalt zwischen den Längskanten, bis zu zwei gegenüberliegende Plätze je äußerer Längsseite. 5–6: zusätzliche gemeinsame Stirnplätze, bei fünf nur ein Ende.
- 7–12: nach innen gerichtetes Vier-Tisch-Rechteck, maximal zwei Chairs je äußerer Längsseite. Für 9–12 zusätzliche äußere Eckplätze zwischen Nachbartischen, bei zwölf acht Längs- plus vier Eckplätze. 13–15: Fünf-Tisch-Pentagon mit zehn Längsplätzen und drei bis fünf Zwischenplätzen; höchstens zwei direkt je Längsseite.
- Zweiergruppe am 2026-10-15 auf Johannes’ Wunsch auf 10 cm physischen Spalt umgestellt (90 cm Mittelpunktabstand). Ursprüngliche 170 × 90 cm Floor-Konturen sollen vollständig bleiben; ihre Außenkanten treffen sich im Spalt. Gemeinsame Stirnflächen überspannen nun 170 cm statt 160 cm. 31 fokussierte Tests und 30 Offline-Fälle bestanden. Rücknahme der angewandten Kontur-Reparatur und erneute Generierung mit aktualisiertem Sender manuell erforderlich. [Anleitung](TOUCHDESIGNER_JOINED_FLOOR_CONTOURS.md).
- Eckflächen aus kanonischen Kontur-Stützpunkten und bestehenden 50-cm-Streifen abgeleitet, vollständig für ROI und Parkplanung reserviert. Maximal ein Chair je Ecke/Zwischenraum, bei zehn zunächst gegenüberliegende Eckplätze. Im Pentagon entstehen die Zwischenflächen an den Mittelpunkten der einander zugewandten kanonischen Stirnkanten. Zwischen-Chairs und ihre vollständigen Sitzflächen werden nach außen auf den Kreis der zehn Längsseiten-Chairs verschoben (nominal rund 26,5 cm; gemeinsamer Mittelpunktabstand rund 225,5 cm). Die bestehende Phasen-/Mittelpunktsuche wahrt die ROI; in der aktuellen Live-Ausgangsszene maximal 3,2 cm Tischverschiebung und 1° gemeinsame Drehung gegenüber dem vorherigen Ziel.
- Tischidentitäten und Posen bleiben innerhalb jeder Teilnehmerstufe stabil; nur die Chair-Belegung ändert sich. Die jeweilige Maximalbelegung 6/12/15 wird vorgeplant und begrenzt zwischengespeichert.
- Überzählige Tische werden mit einer Längsseite am ROI-Rand geparkt, mindestens 60 cm von aktiven Tischen entfernt; alle Tischidentitäten und die ursprüngliche Scene Order bleiben erhalten. Die Auswahl berücksichtigt den Gesamtbewegungsweg.
- Chair-Radius 25 cm; kanonische Sitzflächen 50 cm tief. Eigene Kantentangenz und höchstens 0,51 cm Rundungsüberstand sind zugelassen. Vollständige ROI- und Fremdkollisionsprüfung einschließlich Parktischen.
- Ohne expliziten Count bleibt `2 × verfügbare Tischanzahl` der Standardwert; die aktive Topologie folgt anschließend der Teilnehmerstufe. Bei zu wenigen Tischen oder mehr als 15 Personen klare Ablehnung.
- Bisherige Ring-/Geometriefunktionen und kompakte Parkplanung werden wiederverwendet. Begrenzte Ergebnis-Caches und Wiederverwendung identischer Parkgeometrie innerhalb einer Suche; kein Netzwerkversand in Offline-Checks.
- Umbauintensität am 2026-10-15 nach Johannes’ Freigabe: Stärke 0 erhält exakte Source ohne Chairs; positive Teilstärken dürfen von der festen Discussion-Zielform abweichen. Einzelne Tische folgen der Interpolation; kanonische Chair-/Sitzgeometrie wird pro gebundenem Tisch transportiert. Begrenzte Reparatur einzelner Posen statt starrer Gesamtform. Maximale Stufenbelegung, beide Ring-Bewegungsstreifen, volle ROI, Tisch-/Chair-Kollisionsfreiheit, freie Sitzflächen und Randparken mit 60 cm bleiben geprüft. 100 % unverändert, Rollen/Scene Order erhalten. Cache weiterhin 32 unabhängige Ergebniskopien. 26 fokussierte Tests und 210 Offline-Fälle aus zwei Szenen, Counts 1–15 bei 0/1/25/50/75/99/100 % bestanden; zusätzlich relative Tischabstände statt bloßer gemeinsamer Drehung geprüft. Quellen, Checks und Vergleich lokal unter `data/aisi/debug/discussion_relaxed_strength_2026-10-15/`; reproduzierbar mit `scripts/validate_discussion_strength.py`. Live-Reglerprüfung nach Sender-Neustart offen.
- Offline: 30 Fälle aus zwei Ausgangsszenen, alle Counts 1–15; Übergänge, Parkabstände, Identität/Scene Order, Determinismus und lokale OSC-Ausgabe geprüft. Kontrollplots und eingefrorene Quellen lokal unter `data/aisi/debug/discussion_pentagon_chair_circle_2026-10-15/`.
- Aktualisierung des gemeinsamen Pentagon-Chair-Kreises: 22 fokussierte Discussion-/Rect-Template-Tests bestanden; Input und Groupwork unverändert. Interaktive Chair-Einzelvalidierung und physische Prüfung bleiben offen.
- Der bisherige Tischring ohne Opt-in-Vorschau bleibt unverändert; seine frühere virtuelle Bestätigung gilt nicht automatisch für die neuen Chair-Stufen.

## 8. Study state

### Active trials

Repository-confirmed:

- `trials.json`: `pilot_v8`, `frozen_for_study`;
- zugehöriger eingefrorener Snapshot: `trials_pilot_v8.json`; `pilot_v7` bleibt erhalten;
- T1–T3 und Familiarization einschließlich Teilnehmerstarts unverändert aus `pilot_v7`;
- T4A/T4B: Source, Target und beide Statiktische um exakt `+11 cm` in Welt-Y verschoben, bei unverändertem X und unveränderter Rotation;
- Anlass: natürlicherer Referenzweg mit vorangehendem kurzen Tischende ohne künstliches anfängliches Zurücksetzen; physische Raumvalidierung bleibt offen;
- eight experimental trials: T1–T4 × A/B;
- T1/T2 use one active table and no distractors;
- T3/T4 use one active table and two static distractors;
- exact coordinates, A/B transforms, participant positions, ROI safety, and snapshot metadata are covered by tests.

Task logic:

| | low/limited occlusion | increased occlusion |
| --- | --- | --- |
| simpler layout | T1 | T2 |
| denser layout | T3 | T4 |

This is a deliberate 2×2 task-creation logic; physical factors may not be perfectly orthogonal, so factorial claims require methodological justification.

### Conditions and mappings

- modes: Tracking `0`, Study `1`, AISI `2`;
- conditions: Floor-only `0`, Dual-surface `1`;
- phases: Home `0`, Ready `1`, Active `2`, Complete `3`.

Dual-surface may spatially redistribute guidance rather than merely add tabletop graphics to otherwise identical floor guidance.

### Arrival and logging

- translation tolerance: `8 cm`;
- rotation tolerance: `5°`;
- confirmation duration: `0.5 s` continuously inside tolerance;
- objective arrival and participant-declared completion are distinct;
- arrival entered/confirmed/exited events are logged;
- tracking loss and post-arrival behavior are represented in analysis metrics;
- session metadata includes the active trial-definition SHA-256;
- logs are append-only and participant/session/attempt aware.

## 9. Documentation risks

Known drift outside these handoff files:

- the root `README.md` still describes older prototype status and layout/vision assumptions;
- `docs/PROJECT_STATE_2026-05.md` is historical;
- some human-readable notes in `trials.json` may not literally match the numeric poses and should be reviewed before the next pilot.

Do not change frozen trial geometry merely to resolve prose drift; determine first whether only the notes are wrong.

## 10. Validation principle

Keep repository-confirmed, history-reported, and physical-room-reported claims separate. A local test or virtual TouchDesigner check does not establish physical projection correctness.

### Floor-Renderer in Chair-Arbeitsdatei 137

Die gespeicherte Version 137 wurde am 2026-10-07 in einer temporären Kopie
mit `toeexpand` untersucht. `comp_layout_proposal/render_floor` (Render TOP)
hat eine aktive Geometry-Expression: Im Tracking-Modus werden Tracking-
Floor-Geometrien gewählt, ansonsten phasenabhängige Study-Geometrien.
Der als konstanter Parameterwert gespeicherte ältere Pfad zu
`item*/table_target_floor_geo` ist bei dieser Expression nicht maßgeblich.
Study-Geometrien sind zusätzlich nach Modus/Phase auf Sichtbarkeit begrenzt.
Ein leerer ursprünglicher Floor im AISI-Modus ist deshalb erklärbar und
belegt keinen Fehler der Chair-Integration: Chairs werden erst im zentralen
Composite hinzugefügt. Eine dauerhaft leere Darstellung auch im passenden
Tracking-/Study-Zustand wäre separat im laufenden Projekt zu untersuchen.
Johannes nimmt Count 0 aus dem aktuellen Prüfumfang; die physische
Raumprüfung ist derzeit nicht möglich und bleibt aufgeschoben.

### AISI-Floor und Study-Gestaltung — Live-Zwischenstand

Auf Basis von `AISI_v2.138_coherent_chairs_validated.toe` hat Johannes
`apply_aisi_study_visual_style.py` ausgeführt und die Darstellung bestätigt.
AISI rendert nun vorhandene Zieltischkonturen und Bodenpfeile in
`render_floor` (Render TOP); Tracking/Study behalten ihre bisherigen Zweige.
Rect-Ziele verwenden die weißen gestrichelten Study-Konturen (Floor
170 × 90 cm, Tabletop 150 × 70 cm, Strichstärke 2,5 cm), Rect-Source
die blaue durchgehende Tabletop-Kontur. Zentraler gemeinsamer Style-Code
liegt in `comp_layout_proposal/aisi_table_visual_style` (Text DAT);
vorhandene Item-Geometrien und Template werden weiterverwendet.
Chairs und Scout-Fallback bleiben unverändert.

Der Livebericht meldet `passed: true`: geschützte Einstellungen unverändert,
Chair- und Table-Mask-Bilder bitgleich, sichtbare Floor-Pixel, fünf Rect-Items
mit je vier Source- und zwölf Zielprimitiven je Oberfläche. Der Stand
ist laut Johannes manuell gespeichert. Die Dateien
`AISI_v2.139_aisi_floor_study_style.toe` und
`AISI_v2.140_coherent_chairs_validated.toe` sind am 2026-10-07 im
Projektordner verifiziert; Version 140 stimmt per SHA-256 mit der
unnumerierten Datei `AISI_v2_coherent_chairs_validated.toe` überein.
Kein TD-Zugriff, automatisches Speichern oder erneutes Öffnen während der
Offline-Validierung. Die physische Raumprüfung bleibt aufgeschoben.
