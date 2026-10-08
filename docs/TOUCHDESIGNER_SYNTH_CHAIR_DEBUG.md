# TouchDesigner-Debuganzeige für synthetische Chairs

## Flackern am 2026-10-08 — zwei Layout-Sender

Nach dem Orientierungsfix meldet Johannes schnellen Wechsel zwischen zwei
Zuständen. Live-Prozessprüfung: PID 40517 lief seit 2026-10-07, 17:48:02;
PID 94900 seit 2026-10-08, 09:13:13. Beide stammen aus diesem Repository
und senden `aisi.app.sim_scene_to_osc` an `127.0.0.1:9000`.
Damit bedienen alte und neue Python-Synthese dieselben `/table/...`-Channels.
Alten Sender PID 40517 mit SIGINT beendet; anschließend genau eine
Layout-Senderinstanz (PID 94900) verifiziert. TD-Graph und Einstellungen
unverändert; keine Datei gespeichert. Visuelle Beruhigung noch zu bestätigen.
Beim Neuladen zuerst die bisherige Senderinstanz beenden.

Stand: 2026-10-07

## Geltungsbereich und Arbeitsdatei

Beim Beginn der Arbeit war in TouchDesigner tatsächlich diese Datei geöffnet:

`/Users/Johannes/Library/CloudStorage/OneDrive-Persönlich/Dokumente/AISI_DEV/touchdesigner/AISI_v2.119.toe`

Der vollständige Pfad des bestehenden Ein-/Ausgabe-Containers lautet
`/project1/comp_io` (`containerCOMP`). Die Implementierung wurde ausschließlich
in einer neuen Arbeitsdatei gespeichert:

`/Users/Johannes/Library/CloudStorage/OneDrive-Persönlich/Dokumente/AISI_DEV/touchdesigner/AISI_v2.121_synth_chair_debug.toe`

Die autoritative `AISI_v2.toe` und die zuvor geöffnete `AISI_v2.119.toe`
wurden nicht überschrieben. Kalibrierung, Projektor-Transforms, Homographien,
lokale Korrekturen, Edge Blending, Masken, Study-Modi, Tabellenlogik und
physische Ausgänge wurden nicht verändert.

## Tatsächlich empfangene OSC-Daten

`/project1/comp_io/oscin1` (`oscinCHOP`) empfängt auf UDP-Port `9000`.
`/project1/comp_io/null_osc_raw` (`nullCHOP`) gab beim ersten Prüfschritt
folgende resultierende TD-Kanäle aus:

- `chair/count`
- `chair/0/x`, `chair/0/y`, `chair/0/radius`
- `chair/1/x`, `chair/1/y`, `chair/1/radius`
- `chair/2/x`, `chair/2/y`, `chair/2/radius`
- `chair/3/x`, `chair/3/y`, `chair/3/radius`

Der anfängliche Live-Wert von `chair/count` war `0`, während in den Kanälen
der Indizes 0–3 noch frühere Positions- und Radiuswerte lagen. Damit ist
bestätigt, dass vorhandene Kanalwerte allein keine Sichtbarkeit begründen
dürfen. Nach Aktivierung der bereits vorhandenen AISI-Input-Vorschau trafen
über denselben OSC-Pfad `chair/count = 8` sowie die Kanäle der Indizes 0–7
ein; alle acht Radien betrugen dabei `25 cm`.

Der Sender verwendet damit nachweislich den Indexursprung `0`. Die OSC-
Adressen `/chair/count` und `/chair/{index}/{x|y|radius}` erscheinen im CHOP
ohne führenden Slash als `chair/count` und `chair/{index}/{x|y|radius}`.

## Ergänzter, isolierter Netzwerkzweig

Es wurden keine bestehenden Operatoren geändert. Ergänzt wurden:

| Vollständiger Pfad | Operator-Typ |
| --- | --- |
| `/project1/comp_synth_chair_debug` | `containerCOMP` |
| `/project1/comp_synth_chair_debug/select_synth_chair_osc` | `selectCHOP` |
| `/project1/comp_synth_chair_debug/null_synth_chair_osc_inputs` | `nullCHOP` |
| `/project1/comp_synth_chair_debug/mat_synth_chair_debug_orange` | `constantMAT` |
| `/project1/comp_synth_chair_debug/geo_synth_chair_00` bis `/project1/comp_synth_chair_debug/geo_synth_chair_07` | jeweils `geometryCOMP` |
| `/project1/comp_synth_chair_debug/geo_synth_chair_00/circle_radius_synth_chair_00` bis `/project1/comp_synth_chair_debug/geo_synth_chair_07/circle_radius_synth_chair_07` | jeweils `circleSOP` |
| `/project1/comp_synth_chair_debug/cam_synth_chair_debug_preview` | `cameraCOMP` |
| `/project1/comp_synth_chair_debug/render_synth_chair_debug_preview` | `renderTOP` |
| `/project1/comp_synth_chair_debug/constant_synth_chair_debug_off` | `constantTOP` |
| `/project1/comp_synth_chair_debug/switch_enable_synth_chair_debug` | `switchTOP` |
| `/project1/comp_synth_chair_debug/null_synth_chair_debug_preview` | `nullTOP` |
| `/project1/comp_synth_chair_debug/out_synth_chair_debug_preview` | `outTOP` |

`select_synth_chair_osc` liest ausschließlich
`/project1/comp_io/null_osc_raw` mit dem Filter `chair/*`. Der Container hat
keine ausgehende Netzwerkverbindung zu bestehenden manuellen, Tracking-,
Source-, Masken-, Kalibrierungs- oder Projektorpfaden. Der einzige Ausgang ist
der innerhalb des isolierten Containers endende virtuelle Preview-Ausgang
`out_synth_chair_debug_preview`.

## Umrechnung, Größe und Sichtbarkeit

Die Geometrien verwenden direkt:

- `tx = (x_cm - 250) * 0.0052`
- `ty = -(y_cm - 250) * 0.0052`
- `radius_td = max(radius_cm, 0) * 0.0052`

Der verwendete `circleSOP` erwartet mit `radx` und `rady` Radien, nicht den
Durchmesser. Deshalb wird `radius_td` ohne Verdopplung eingesetzt.

Jede Geometrie erhält Sichtbarkeit nur, wenn alle Bedingungen gleichzeitig
gelten: Gesamtanzeige eingeschaltet, `chair/count` vorhanden und größer als
der 0-basierte Index, X-/Y-/Radiuskanal des Index vorhanden und Radius größer
als null. Dadurch werden fehlende Kanäle nicht durch alte Werte ersetzt und
alle Indizes außerhalb eines sinkenden Counts sofort auf Skalierung null
gesetzt. Der zusätzliche `switch_enable_synth_chair_debug` schaltet den
gesamten TOP-Ausgang zwischen transparentem Off-TOP und Preview-Render um.

Ein-/Ausschalten erfolgt über den Custom-Parameter
`/project1/comp_synth_chair_debug.par.Enabledebug`. `0` ist aus, `1` ist ein.
Der gespeicherte Standard- und Endzustand ist `0`.

## Validierung

Für die reproduzierbare Prüfung wurden bekannte Werte als lokale OSC-
Testpakete an `127.0.0.1:9000` gesendet. Diese Werte wurden außerhalb von
TouchDesigner künstlich erzeugt, liefen aber tatsächlich durch
`comp_io/oscin1` und `comp_io/null_osc_raw`. Innerhalb von TouchDesigner wurden
keine Chair-Testkanäle künstlich gesetzt.

Testschema je Index `i`:

- `x = 50 + 50*i cm`
- `y = 100 + 30*i cm`
- `radius = 10 + 2*i cm`

| Gesendeter Count | Sichtbare Debug-Chairs | Sichtbarkeitsfolge 0–7 |
| ---: | ---: | --- |
| 0 | 0 | `0 0 0 0 0 0 0 0` |
| 1 | 1 | `1 0 0 0 0 0 0 0` |
| 3 | 3 | `1 1 1 0 0 0 0 0` |
| 4 | 4 | `1 1 1 1 0 0 0 0` |
| 6 | 6 | `1 1 1 1 1 1 0 0` |
| 8 | 8 | `1 1 1 1 1 1 1 1` |

Für Chair 0 ergaben `50, 100, 10 cm` exakt `-1.04, 0.78, 0.052 TD`.
Bei Count 4 und `chair/2/radius = 0` waren genau drei Chairs sichtbar; die
Folge lautete `1 1 0 1 0 0 0 0`. Beim Rückgang von Count 8 auf Count 3 zeigte
der Netzwerk-/Preview-Viewer nur noch die drei erlaubten Kreise; die
Count-Bedingung verhindert unabhängig von weiter vorhandenen Kanalwerten jede
alte Instanz oberhalb des neuen Counts.

Die Preview wurde ausschließlich virtuell in TouchDesigner geprüft. Eine
physische Projektionsprüfung im Raum, eine Beurteilung der Projektorflächen
oder irgendeine Freigabe der geschützten Projektionskette wurde nicht
durchgeführt.

## Gemeinsame virtuelle Vorschau für Tische und Chairs

Am 2026-10-02 wurde die getrennte Chair-Debuganzeige in einer neuen
Arbeitsversion um eine zweite, ebenfalls rein virtuelle Vorschau ergänzt:

`/Users/Johannes/Library/CloudStorage/OneDrive-Persönlich/Dokumente/AISI_DEV/touchdesigner/AISI_v2.126_tables_chairs_virtual_preview.toe`

Die älteren Dateien einschließlich `AISI_v2.121_synth_chair_debug.toe` und
die autoritative `AISI_v2.toe` wurden nicht überschrieben. TouchDesigner legte
während der Arbeit außerdem die Zwischenversion
`AISI_v2.123_synth_chair_debug.toe` an; sie wurde nicht entfernt.

Die gemeinsame Vorschau kombiniert ausschließlich zwei vorhandene virtuelle
Renderbilder:

- `/project1/comp_layout_proposal/render_tabletop` (`renderTOP`) mit
  Source-Tischen in Grün, Target-Tischen in Blau und den vorhandenen weißen
  Richtungsmarkierungen;
- `/project1/comp_synth_chair_debug/render_synth_chair_debug_preview`
  (`renderTOP`) mit den orangefarbenen synthetischen Chairs.

Ergänzt wurden folgende Operatoren:

| Vollständiger Pfad | Operator-Typ |
| --- | --- |
| `/project1/comp_tables_chairs_virtual_preview` | `containerCOMP` |
| `/project1/comp_tables_chairs_virtual_preview/select_source_target_tables` | `selectTOP` |
| `/project1/comp_tables_chairs_virtual_preview/select_synthetic_chair_render` | `selectTOP` |
| `/project1/comp_tables_chairs_virtual_preview/composite_tables_and_synth_chairs` | `compositeTOP` |
| `/project1/comp_tables_chairs_virtual_preview/constant_combined_preview_off` | `constantTOP` |
| `/project1/comp_tables_chairs_virtual_preview/switch_enable_combined_preview` | `switchTOP` |
| `/project1/comp_tables_chairs_virtual_preview/null_tables_chairs_virtual_preview` | `nullTOP` |
| `/project1/comp_tables_chairs_virtual_preview/out_tables_chairs_virtual_preview` | `outTOP` |

Der `compositeTOP` verwendet die Add-Operation, sodass beide bereits
raumgleich gerenderten Bilder ohne neue Geometrie, Kamera oder
Koordinatentransformation zusammengeführt werden. Der Container besitzt keine
Verbindung zu `comp_output`, Masken, Kalibrierung, Homographien, Projektoren
oder anderen physischen Ausgängen.

Die neue Vorschau wird über
`/project1/comp_tables_chairs_virtual_preview.par.Enablepreview` geschaltet.
Die eigenständige Chair-Vorschau bleibt weiterhin separat über
`/project1/comp_synth_chair_debug.par.Enabledebug` schaltbar. Damit Chairs in
beiden Vorschauen unabhängig erscheinen können, berücksichtigen die bereits
vorhandenen Sichtbarkeitsausdrücke von
`geo_synth_chair_00` bis `geo_synth_chair_07` (`geometryCOMP`) nun das logische
ODER beider Preview-Schalter. Count-, Kanal- und Radiusbedingungen blieben
unverändert. Der gespeicherte Stand zeigt die gemeinsame Vorschau und lässt
die eigenständige Chair-Vorschau ausgeschaltet.

### Live-Regression über den vorhandenen AISI-Sender

Die Testwerte wurden nicht in TouchDesigner gesetzt. Teilnehmerzahl,
synthetische Vorschau und der vorhandene Chairs-Schalter wurden über die
laufende Learning-Format-Oberfläche verändert; `sim_scene_to_osc` sendete die
daraus erzeugten Werte an UDP-Port `9000`. TouchDesigner las sie weiterhin aus
`/project1/comp_io/null_osc_raw`. Die Source-/Target-Tische blieben bei allen
Tests gleichzeitig im gemeinsamen Render sichtbar.

| Empfangenes `chair/count` | Sichtbare Chairs 0–7 |
| ---: | --- |
| 0 | `0 0 0 0 0 0 0 0` |
| 1 | `1 0 0 0 0 0 0 0` |
| 3 | `1 1 1 0 0 0 0 0` |
| 6 | `1 1 1 1 1 1 0 0` |
| 8 | `1 1 1 1 1 1 1 1` |

Der direkte Rückgang von Count 8 auf Count 3 blendete die Indizes 3–7 sofort
aus. Für den Radius-0-Test blieb Count 3 bestehen und der vorhandene
Interface-Schalter `Chairs: off` setzte die drei empfangenen Radien auf `0`;
alle acht Chair-Geometrien waren daraufhin unsichtbar. Anschließend wurde der
Ausgangszustand wiederhergestellt: synthetische Vorschau an, `Chairs: on`,
sieben Teilnehmende, `chair/count = 7` und Radien von jeweils `25 cm`.

Die gemeinsame Vorschau wurde nur als virtuelles TouchDesigner-Bild geprüft.
Es fand weiterhin keine physische Raum-, Projektor-, Masken-, Kalibrierungs-
oder Edge-Blending-Prüfung statt.

## Zuschaltbare Chairs im regulären Floor-Ausgang

### Manuelle Reparatur über Textport — gespeichert und erneut geöffnet

Johannes führt die Befehle selbst aus; die GUI-Fernsteuerung wird nicht mehr
verwendet. `td_builders/repair_shared_chair_data.py` wurde ausgeführt und die
Textport-Ausgabe bestätigt 15 bestehende Instanzen `chairs/item1…item15`.
Bei empfangenem `chair/count = 7` enthält `chairs_active` sieben positive
Radien und acht Nullradien; der Script DAT meldet keine Fehler. Die vorhandenen
Spalten `id/x/y/radius` und die Koordinatenumrechnung bleiben erhalten.
Positions- und Radiusparameter sind jetzt laufend an die Tabelle gebunden.
Der gemeinsame Renderanschluss wurde anschließend mit
`td_builders/connect_shared_chair_render.py` ausgeführt. Debug-Render und
regulärer Floor-Render verwenden nun dieselben 15 Instanzen unter
`/project1/comp_layout_proposal/chairs/item*/chair_geo` mit dem zentralen
`mat_chair_orange` (Constant MAT). Die bestehende Ringgeometrie bleibt erhalten.
Der Floor-Render verwendet `cam1`, 2000×2000 Pixel und der zentrale Composite
den Operand `add`; Debug behält seine Vorschaukamera und 1000×1000 Pixel.
Johannes bestätigt sichtbare orange Kreise in den geprüften Views.

`td_builders/check_shared_chair_output.py` wurde über Textport ausgeführt und
meldet `passed: true`: ausgeschalteter optionaler Floor bitgleich zu
`select_floor`, regulärer Zusatz trotz ausgeschaltetem Debug und Preview
aktiv, orange Renderpixel vorhanden, Tabletop und Table-Mask bitgleich,
beide Projektorausgänge verändert. Auch bei eingeschaltetem Debug und Preview
bleibt der ausgeschaltete reguläre Floor bitgleich. Der Check stellt die
ursprünglichen Schalterwerte wieder her. Ergebnisprotokoll:
`/private/tmp/aisi_shared_chair_output_check.json`.

Johannes hat den Stand als `AISI_v2.134_shared_chairs_floor.toe` gespeichert
und erneut geöffnet. Der danach wiederholte Check bestätigt alle oben
genannten Ergebnisse mit `passed: true`. Counts bis 15, Moduswechsel, alte
Referenzen und Entfernung der Top-Level-Komponenten bleiben separat zu
prüfen; die Raumprüfung bleibt offen.

### Zentrale Viewer-Migration — im laufenden Projekt geprüft

Johannes hat `td_builders/migrate_shared_chair_viewers.py` über Textport
in Version 134 ausgeführt. Die neuen Pfade sind:

- `/project1/comp_layout_proposal/chair_debug` (Container COMP), mit
  `Enabledebug`, eigener Kamera und Render TOP auf die gemeinsame Geometrie.
- `/project1/comp_layout_proposal/tables_chairs_virtual_preview` (Container COMP),
  mit `Enablepreview` und Select TOP auf den ungefilterten zentralen Debug-Render.

Der Migrationscheck meldet `passed: true`: ungefilterter und geschalteter
Debug-Render sowie kombinierte und geschaltete virtuelle Vorschau sind
bitgleich mit den Originalen. Bestehender Floor, optionaler Floor, Tabletop,
Table-Mask und beide Projektorausgänge bleiben ebenfalls bitgleich.
Protokoll: `/private/tmp/aisi_shared_chair_migration.json`.
Die anschließende Bereinigung mit `td_builders/cleanup_shared_chair_structure.py`
ist durch Johannes im Textport bestätigt: `external_references: []`,
`removed: true`, `passed: true`; alle zehn verglichenen Bilder bitgleich.
Entfernt sind beide alten Top-Level-Container, die acht kopierten alten
Chair-Geometrien und ihre CHOP-/Materialquelle im zentralen Debug-Container
sowie der alte fünfteilige Chair-Zweig in `comp_output`.
Die aktiven zentralen Render und der Floor-Übergabepunkt bleiben erhalten.

Protokoll: `/private/tmp/aisi_shared_chair_cleanup.json`.
Die vor der Entfernung angelegten COMP-Sicherungen liegen unter
`/var/folders/32/jlhkn9z930b7jhmfvmdd6j1m0000gn/T/aisi_chair_cleanup_5tcl13bc`.
Johannes hat den bereinigten Stand manuell als
`AISI_v2.137_coherent_chairs.toe` gespeichert und erneut geöffnet. Der
anschließend ausgeführte Ausgabecheck meldet erneut `passed: true`:
Floor Off bitgleich, regulärer Zusatz trotz Debug/Preview Off aktiv, orange
Renderpixel, Tabletop/Table-Mask bitgleich, beide Projektorausgänge reagieren
und Floor Off auch mit Debug/Preview On bitgleich.

Beim vorherigen automatischen Speicherversuch bestand der Ausgabecheck,
aber die unmittelbar anschließende Dateiprüfung schlug fehl. Die Ursache
ist nicht abschließend geklärt. Johannes verlangt seitdem ausschließlich
manuelles Speichern; `td_builders/save_coherent_chair_structure.py` ist
deshalb deaktiviert und enthält keinen Speicheraufruf mehr.
Counts bis 15, Moduswechsel und physische Raumvalidierung bleiben offen.

### Fehlerstand geprüft: `AISI_v2.133_regular_floor_chair_render.toe`

Am 2026-10-07 wurde die gespeicherte Version 133 mit `toeexpand` in einer
temporären Kopie geprüft. Der neue `render_synth_chairs_regular_floor`
(Render TOP) verwendet `cam1` und 2000×2000 Pixel, enthält aber ausschließlich
`/project1/comp_layout_proposal/chairs/item1/chair_geo`. Der sichtbare rote
Kreis stammt aus diesem alten Zweig; er ist kein Nachweis der synthetischen
orangefarbenen Chairs.

`composite_floor_with_synth_chairs` (Composite TOP) steht weiterhin auf
`multiply`. Die zuvor dokumentierten Angaben zu `add`, zehn Geometrien und
einer gespeicherten Version 134 waren nicht verifiziert und sind hiermit
korrigiert. Version 134 wurde im Arbeitsverzeichnis nicht gefunden.
Die aktuelle Reparatur muss die synthetische Geometrie mit der Floor-Kamera
rendern, additiv einblenden und anschließend die Bilddaten beider
Projektorausgänge prüfen. Noch keine erfolgreiche Abnahme dieses Standes.

Zentrale Operatoren:

| Vollständiger Pfad | Operator-Typ |
| --- | --- |
| `/project1/comp_layout_proposal/select_floor_for_synth_chairs` | `selectTOP` |
| `/project1/comp_layout_proposal/select_synth_chairs_regular` | `selectTOP` |
| `/project1/comp_layout_proposal/render_synth_chairs_regular_floor` | `renderTOP` |
| `/project1/comp_layout_proposal/composite_floor_with_synth_chairs` | `compositeTOP` |
| `/project1/comp_layout_proposal/switch_enable_synth_chairs_regular` | `switchTOP` |
| `/project1/comp_layout_proposal/null_floor_with_optional_synth_chairs` | `nullTOP` |
| `/project1/comp_output/select_central_floor` | `selectTOP` |

`comp_output` führt nur noch den vorbereiteten Floor-Strom in den bestehenden
`select_central_floor`/`switch_floor`; Calibration, Tabletop, Table-Mask, Homographien und Projektor-
Composites wurden nicht geändert. Die Erweiterung des gemeinsamen Chair-Containers
auf 15 Instanzen und die Entfernung der alten Top-Level-Komponenten bleiben als
separater nächster Integrationsschritt offen. Die physische Raumprüfung bleibt offen.

Am 2026-10-07 wurde die tatsächlich geöffnete
`AISI_v2.127_tables_chairs_virtual_preview.toe` erweitert. Die gespeicherte
und erneut geöffnete Arbeitsdatei lautet:

`/Users/Johannes/Library/CloudStorage/OneDrive-Persönlich/Dokumente/AISI_DEV/touchdesigner/AISI_v2.129_synth_chairs_regular_floor.toe`

TouchDesigner erhöhte die angefragte Versionsnummer `128` beim Speichern
automatisch auf `129`. Zusätzlich entstand
`AISI_v2_synth_chairs_regular_floor.toe`; sie ist nicht der abgenommene Stand.
SHA-256-Vergleiche bestätigen unveränderte Dateien `AISI_v2.toe` und
`AISI_v2.127_tables_chairs_virtual_preview.toe`.

### Bestandsprüfung und bestätigte Plananpassung

Die bestehende Chair-Preview verwendet eine Perspektivkamera und
`1000 × 1000 px`. Der reguläre Floor verwendet die orthografische
`/project1/comp_layout_proposal/cam1` (`cameraCOMP`), `2.6 TD` Bildbreite und
`2000 × 2000 px`. Direktes Addieren des Preview-Bildes wäre nicht räumlich
deckungsgleich. Johannes bestätigte einen separaten Chair-Render mit der
vorhandenen Floor-Kamera und die Beibehaltung des bisherigen Floor-Inhalts.
Die bestehenden acht Chair-Geometrien, World-Posen und Radien werden
wiederverwendet; die alte Preview-Kamera bleibt unverändert.

Source-/Target-Tische bleiben im vorhandenen Tabletop-Zweig; sie wurden nicht
zusätzlich in `render_floor` aufgenommen. Die Projektor-Composites zeigen
Tische und optionale Floor-Chairs gemeinsam mit der bestehenden Maskierung.
Die geplante Erweiterung der gemeinsamen Preview auf fünfzehn Chairs ist
weiterhin offen und war nicht Bestandteil dieses auf Indizes `0–7`
begrenzten Integrationsauftrags.

### Operatoren und Bedienung

| Vollständiger Pfad | Operator-Typ |
| --- | --- |
| `/project1/comp_output/render_synth_chairs_regular_floor` | `renderTOP` |
| `/project1/comp_output/select_synth_chairs_regular` | `selectTOP` |
| `/project1/comp_output/composite_floor_with_synth_chairs` | `compositeTOP` |
| `/project1/comp_output/switch_enable_synth_chairs_regular` | `switchTOP` |
| `/project1/comp_output/null_floor_with_optional_synth_chairs` | `nullTOP` |

Der neue Render verwendet dieselbe Kamera wie
`/project1/comp_layout_proposal/render_floor` (`renderTOP`) und übernimmt
Breite und Höhe dynamisch von `select_floor` (`selectTOP`). Sein Hintergrund
ist transparent. Der neue Select TOP liest diesen ungefilterten Render. Das
Add-Composite übernimmt Auflösung und ersten Eingang von `select_floor`.
Der neue Switch wählt zwischen unverändertem Floor und Composite; der neue
Null TOP ersetzt ausschließlich Eingang 0 von
`/project1/comp_output/switch_floor` (`switchTOP`). Dessen Indexausdruck und
Kalibrierungseingang bleiben unverändert. Die Operator-Inventuren bestätigen
unveränderte Verbindungen und Parameter in beiden Projektor-COMPs sowie
unveränderte Tabletop-, Table-Mask-, Layer- und Kalibrierungsparameter.

Auf `/project1/comp_output` (`containerCOMP`) liegt auf der Custom-Seite
„Synthetic Chairs“ der Parameter `Enablesyntheticchairs`, beschriftet mit
„Enable Synthetic Chairs in Regular Floor Output“. Standardwert und
gespeicherter Endzustand sind **Off**. Der effektive Switch ist nur `1`, wenn:

- der neue Parameter eingeschaltet ist;
- `/project1/comp_output/panel_mode` (`panelCHOP`) Content meldet (`state = 0`);
- `/project1/comp_layout_proposal/panel_mode` (`panelCHOP`) AISI meldet (`state = 0`);
- `/project1/comp_io/null_osc_raw` (`nullCHOP`) `study/mode` enthält und dessen
  Wert exakt `2` (AISI) ist.

Calibration, Tracking (`0`), Study (`1`) und fehlendes `study/mode` sperren
den Zusatz. Die bisherigen Count-/Kanal-/Radiusbedingungen bleiben erhalten.
Die `sx`-/`sy`-Ausdrücke der acht Geometrien berücksichtigen zusätzlich zum
bisherigen ODER beider Preview-Schalter den effektiven regulären Switch.
Der neue Ausgang funktioniert deshalb auch bei `Enabledebug = Off` und
`Enablepreview = Off`. OSC-Vertrag und nullbasierte Indizes bleiben erhalten.

### Virtuelle Abnahme

Verglichen wurden vor und nach der Integration die GPU-Array-Hashes und
Dimensionen von `select_floor`, `switch_floor`, `switch_tabletop`,
`switch_table_mask`, `out_projector_0` und `out_projector_1`, jeweils unter
`/project1/comp_output`:

| Modus | Neuer Schalter Off | Neuer Schalter On |
| --- | --- | --- |
| AISI | Alle sechs Bilder bitgleich zum Ausgangsstand | Nur Floor und Projektorausgänge ändern sich; Tabletop und Table-Mask bleiben bitgleich |
| Tracking | Alle sechs Bilder bitgleich | Alle sechs Bilder bitgleich; effektiver Switch `0` |
| Study, Phase Active (`2`) | Alle sechs Bilder bitgleich | Alle sechs Bilder bitgleich; effektiver Switch `0` |
| Calibration | Alle sechs Bilder bitgleich | Alle sechs Bilder bitgleich; effektiver Switch `0` |

Auch der Content-Schalter auf Tracking sperrt den Zusatz bei weiterhin
empfangenem `study/mode = 2`. Der neue Floor-Übergabepunkt und die beiden
bestehenden `composite_final` (`compositeTOP`) wurden ausschließlich in
Operator-Viewern betrachtet. Beide Projektor-Window-COMPs blieben geschlossen.

Die Live-Tests änderten Teilnehmendenzahl, synthetische Vorschau und
Chair-Schalter über die vorhandene Learning-Format-HTTP-Schnittstelle. Der
laufende AISI-Sender erzeugte die Daten; der Empfang lief tatsächlich durch
`comp_io/oscin1` und `null_osc_raw`. Einmalige zusätzliche OSC-Testpakete
wurden vom laufenden Sender überschrieben und deshalb nicht als Count-Nachweis
verwendet. Die Abnahme wartete auf vollständige Count- und Radiuswerte nach
der Layoutberechnung.

| Empfangenes Count | Sichtbarkeit der Instanzen 0–7 |
| ---: | --- |
| 0 | `0 0 0 0 0 0 0 0` |
| 1 | `1 0 0 0 0 0 0 0` |
| 3 | `1 1 1 0 0 0 0 0` |
| 6 | `1 1 1 1 1 1 0 0` |
| 8 | `1 1 1 1 1 1 1 1` |

Beim Rückgang `8 → 3` verschwanden die Instanzen 3–7. Bei Count `1` und
`radius = 0` waren sämtliche Instanzen unsichtbar und der Chair-Render leer.
Der Hintergrund war transparent; das Composite war pixelgenau die auf den
Wertebereich begrenzte Summe seiner Eingangsbilder. Die acht gemessenen
Mittelpunkte stimmen innerhalb eines Pixels mit den World-Koordinaten im
Floor-Raster überein. `25 cm` Radius ergeben `100 px`; gemessen wurden
`100–100.5 px`. Die alte Perspektiv-Preview und der orthografische Floor zeigen
dieselben World-Posen mit jeweils ihrer Kamera; ihre Bildschirmkoordinaten
sind deshalb nicht identisch.

Nach erneutem Öffnen von Version `129` wurden alle fünf Nodepfade,
Fehlerfreiheit, Standardwert und gespeicherter Schalterzustand **Off** sowie
geschlossene Projektorfenster bestätigt. Die reguläre Chair-Anzeige war bei
ausgeschalteten beiden Preview-Schaltern separat aktivierbar; die Live-Reaktion
`7 → 3 → 7` funktionierte. Wiederhergestellter Endzustand: sieben Teilnehmende,
synthetische Vorschau und Chairs an, gemeinsame virtuelle Preview an,
eigenständige Debuganzeige aus und reguläre Floor-Chairs aus.

Die physische Raumprüfung bleibt offen. Sichtbarkeit, räumliche Deckung und
die Wirkung der bestehenden Maskierung, Homographien, Projektorflächen und
des Edge Blendings sind erst in einem separaten Raumtest zu bestätigen.

### Offener Aktualisierungsfehler bei Count-Wechseln in Version 137

Johannes berichtet zunächst weiterhin sieben sichtbare Kreise bei Counts
8–15. Der anschließend ausgeführte Diagnosecheck bestätigt bei Count 15
alle vollständigen OSC-Kanäle, 15 positive DAT-Radien schon vor dem
erzwungenen Cook, unveränderten DAT-Inhalt danach und 15 Instanzen mit
Radius 0.13, Skalierung 1 und Render On. Beide Render lösen die gemeinsame
Geometrie für alle 15 Instanzen auf. Nach der Diagnose sieht Johannes
15 Kreise. Eine fehlende automatische Aktualisierung ist weiterhin zu
untersuchen; ein Fehler der DAT-Werte ist damit nicht nachgewiesen.
Ring-Callback und Cook-Einstellungen werden als nächstes gezielt geprüft.

Johannes bestätigt anschließend, dass der Output ohne weiteren erzwungenen
Cook auf unterschiedliche Teilnehmendenzahlen reagiert. Der lesende Check
zeigt: Der Ring-Callback liest `parent(2).par.Radius`; die vorhandenen
Script-SOP-Parameter `Valuea`/`Valueb` sind ungebunden. Es wurde keine
Cook-Reparatur vorgenommen und kein eindeutiger Callback-Fehler belegt.
Der Wechsel nach erneutem Öffnen von Version 137 ohne vorausgehenden
Diagnose-/Force-Cook muss noch geprüft werden; erst danach ist die
Aktualisierung als dauerhaft bestätigt zu bewerten.

Johannes bestätigt den direkten Wechsel 3 → 15 → 3 nach erneutem Öffnen
ohne Diagnose-/Force-Cook. Eine weitere Cook-Reparatur ist deshalb derzeit
nicht begründet. Für den nächsten Radius-null-Check ist
`td_builders/check_shared_chair_zero_radius.py` syntaktisch geprüft und
vorbereitet, aber noch nicht live ausgeführt. Er übersteuert temporär nur
den Radius von Chair 0 im bestehenden DAT-Callback und stellt den Callback
im `finally`-Block wieder her; keine OSC-Nachrichten oder neuen Operatoren.
Dies prüft die TD-Verarbeitung isoliert und ersetzt keinen echten OSC-Test.

### Radius-null-Verarbeitung in Version 137 — isoliert geprüft

Johannes hat `td_builders/check_shared_chair_zero_radius.py` ausgeführt:
`passed: true`. Bei 15 gültigen Chairs wird nur Chair 0 am Eingang des
DAT-Callbacks temporär mit Radius null übersteuert. Sein gebundener Radius
und beide Geometrieskalierungen werden null; die anderen 14 Radien bleiben
unverändert. Beide ungefilterten Chair-Render ändern ihr Bild. Callback
und Chair 0 sind anschließend wiederhergestellt. Keine Operatoren angelegt,
keine OSC-Nachrichten gesendet, keine Projektdatei gespeichert.
Der Nachweis betrifft die TD-Verarbeitung; der Radius-null-Test über echte
OSC-Nachrichten, die vollständige Count-Matrix, Modussperren und physische
Raumvalidierung bleiben offen.

Johannes bestätigt die Tracking-Modussperre mit eingeschaltetem
`comp_output.par.Enablesyntheticchairs`: Der zentrale
`switch_enable_synth_chairs_regular` (Switch TOP) liefert Index `0.0`.
Damit ist der optionale reguläre Chair-Zusatz im Tracking-Modus gesperrt.
Study- und Calibration-Sperre sowie der bildliche Vergleich dieser Modi
bleiben offen.

Johannes bestätigt anschließend auch die Study- und Calibration-Sperre:
Bei regulären Chairs On liefert der zentrale Chair-Floor-Switch in beiden
Modi Index 0. Calibration wurde über `comp_output/toggle_mode`
(Button COMP) aktiviert. Damit sind alle drei Modussperren funktional
per Switch-Index geprüft; ein vollständiger bildlicher Vergleich dieser
Modi gegen die Ausgangsdatei ist damit nicht ersetzt. Die erneute Freigabe
nach Rückkehr zu AISI bleibt als letzter Schritt dieses Moduschecks offen.

### Moduscheck nach korrigierter Vorbedingung bestätigt

Beim Rückwechsel zu AISI zeigte die Diagnose
`Enablesyntheticchairs: False`, Output-Modus 0, Layout-Modus 0 und
OSC-Study-Modus 2. Damit war der erste Sperrdurchlauf nicht aussagekräftig:
Chairs Off allein erklärt Index 0. Nach explizitem Einschalten des Parameters
hat Johannes alle Modi erneut geprüft und bestätigt: Tracking, Study und
Calibration jeweils Index 0, ausschließlich AISI Index 1. Dies ist der
maßgebliche funktionale Nachweis der Modussperren. Ein bildlicher Vergleich
aller Modi gegen die Ausgangsdatei sowie die physische Raumprüfung bleiben
separat offen. Es wurde keine Änderung an der Schalterlogik benötigt.

Johannes bestätigt anschließend die Count-Wechsel 8 → 3 und 1 → 0:
Die sichtbare Anzahl folgt den Daten; überzählige Chairs verschwinden.
Zusammen mit 3 → 15 → 3 nach erneutem Öffnen sind diese Übergänge
virtuell geprüft. Der gezielte Durchlauf für Counts 6, 9, 10, 11 und
15 → 0 ist noch separat zu bestätigen; echte OSC-Radius-null-Prüfung,
bildliche Modusvergleiche und physische Raumvalidierung bleiben offen.

### Höhere Counts und Live-Reaktion der OSC-Brücke bestätigt

Johannes bestätigt den Durchlauf mit Counts 6, 9, 10, 11 und 15:
Die sichtbare Anzahl passt sich jeweils an. Count 0 ist in der vorhandenen
UI nicht einstellbar; 15 → 0 bleibt deshalb ungeprüft. Die zuvor pauschale
Bestätigung von 1 → 0 wird durch diese Klarstellung nicht als gesicherter
Count-null-Nachweis gewertet. Die UI wird dafür auf Nutzerwunsch nicht erweitert.

Zusätzlich bestätigt Johannes, dass Änderungen im Room Editor unmittelbar
in TD übernommen werden. Dies belegt die beobachtete Live-Reaktion über
die OSC-Brücke, ersetzt aber keinen gezielten Test eines einzelnen
Radius-null-Chairs über echte OSC-Nachrichten. Vollständige bildliche
Modusvergleiche und die physische Raumprüfung bleiben offen. Der
Arbeitsstand bleibt Version 137; keine weitere Projektdatei gespeichert.

## AISI-Zieltischkonturen und Study-Gestaltung — neuer Auftrag

Die aktuelle manuell gespeicherte Ausgangsdatei laut Livebericht ist
`AISI_v2.138_coherent_chairs_validated.toe`. Johannes verlangt ausdrücklich
Zieltischkonturen auf dem AISI-Floor und eine grafische Anpassung an Study.
Dies ersetzt die frühere Beschränkung, keine Tischinhalte hinzuzufügen.
Die Chairs bleiben unverändert, da keine Study-Gestaltung dafür festgelegt ist.

Der lesende Bericht `/private/tmp/aisi_study_visual_style.json` bestätigt,
dass die Floor-Expression bisher keinen eigenen AISI-Zweig enthält.
Das vorbereitete Textport-Skript `td_builders/apply_aisi_study_visual_style.py`
ergänzt diesen Zweig mit den bestehenden `table_target_floor_geo` und
`table_motion_line_floor_geo` (Geometry COMPs) pro aktivem Item.
Study-/Tracking-Auswahl bleibt als bisherige Expression im anderen Zweig.

Die vorhandenen Rect-Kontur-SOPs und ihre Callbacks werden weiterverwendet.
Ein zentraler `aisi_table_visual_style` (Text DAT) enthält die bestehenden
kanonischen Study-Konturfunktionen als selbstständigen Code. Rect-Source
auf Tabletop: blaue, durchgehende 150 × 70 cm Kontur; Rect-Ziele: weiße
gestrichelte 170 × 90 cm Floor- und 150 × 70 cm Tabletop-Konturen,
jeweils 2,5 cm Strichstärke. Das Source-Material wird aus Study wiederverwendet;
Ziele verwenden wie Study das Standardmaterial und einen Tiefenversatz von
0,001 TD. Posen, Achsen und Skalierung der Items bleiben erhalten.
Scout-Konturfunktionen und bisherige Materialien bleiben als Fallback
erhalten; eine fachliche Scout-Study-Gestaltung wird nicht erfunden.
Die vorhandenen weißen Bewegungspfeile haben bereits 0,012 TD Strichstärke
und werden gestalterisch nicht geändert.

Offline geprüft: drei fokussierte Regressionstests für die kanonischen
Konturfunktionen im serialisierten DAT, den Erhalt der Render-Auswahl
und Scout-Fallback. Zusätzlich liefert die exakt aus TD gelesene
Floor-Expression vor/nach Erweiterung für Tracking und Study in allen
vier Phasen dieselben Pfade. Syntax und `git diff --check` bestanden.
Live-Ausführung steht noch aus. Das Skript prüft geschützte Einstellungen,
Table-Mask- und Chair-Bilder sowie sichtbare Floor-Pixel; bei Fehlern
rollt es die eigenen Änderungen zurück. Es speichert keine .toe und
öffnet keine Projektorfenster.

### AISI-Study-Gestaltung live bestätigt

Johannes hat das vorbereitete Anpassungsskript in der offenen Version 138
ausgeführt und bestätigt die Darstellung anhand beider Operator-Viewer:
Floor mit weißen gestrichelten Zielen und Bodenpfeilen; Tabletop mit blauen
Source-Konturen, weißen gestrichelten Zielen und Pfeilen. Der Livebericht
`/private/tmp/aisi_floor_study_style_check.json` meldet `passed: true`:
geschützte Einstellungen, Chair-Bild und Table-Mask unverändert; fünf
Rect-Items mit je vier Source-Primitiven und zwölf Zielprimitiven sowohl
auf Floor als auch Tabletop. Ein manueller Save-As in neuer Version und
der Check nach erneutem Öffnen sind noch ausstehend. Version 139 ist zum
Prüfzeitpunkt im Projektordner frei. Keine Datei automatisch gespeichert.

### Wiederkehrende Count-Auffälligkeit bei der manuellen Stichprobe

Am 2026-10-07 zeigt Johannes zwei Bilder von
`null_floor_with_optional_synth_chairs` (Null TOP): bei Count 9 neun sichtbare
Kreise, bei Count 10 ebenfalls neun und eine geänderte Verteilung links.
Die linke Kreiskante ist in beiden Bildern angeschnitten. Die anfängliche
Zählung von acht Kreisen wurde nach genauem Bildabgleich korrigiert.

Die aktuelle gespeicherte Simulationsquelle liefert offline exakt neun bzw.
zehn Chairs mit positivem Radius. Beim Wechsel 9 → 10 bleiben Tischziele
und Chair-Indizes 0–7 unverändert; am Tisch `table_4` wird der einzelne Platz
durch zwei Plätze ersetzt. Die auffällige Verteilung im zweiten Bild lässt
sich damit nicht durch die aktuelle Synthese erklären. UDP-Port 9000 ist
durch TouchDesigner belegt; das belegt weder vollständige Empfangsdaten
noch die Zahl laufender Sender.

Version `AISI_v2.140_coherent_chairs_validated.toe` wurde ausschließlich in
einer temporären Kopie mit `toeexpand` untersucht. Alle 15 Instanzen
`item1…item15` (Base COMP) referenzieren für X/Y/Radius ihre eigene DAT-Zeile;
`render_synth_chairs_regular_floor` (Render TOP) verwendet den gemeinsamen
Wildcard-Pfad zu allen `chair_geo` (Geometry COMP). Kein struktureller
Acht-Slot-Cutoff nachgewiesen. Die laufende Projektdatei ist damit nicht
ausgelesen und die Live-Ursache nicht bestimmt.

Nächster Nachweis: bei sichtbar fehlerhaftem Count 10 den neuen lesenden
Textport-Check `td_builders/inspect_shared_chair_live_state.py` manuell
ausführen. Er nimmt zuerst OSC/DAT-Werte auf, dann Instanzparameter und
Renderer-Pfade; kein Force-Cook, keine Parameteränderung, keine Dateiablage
oder Speicherung. Lesende Parameterabfragen können dennoch TD-Abhängigkeiten
auswerten; deshalb auch eine mögliche Bildänderung durch den Check melden.
Der bisherige `diagnose_shared_chair_count.py` erzwingt einen Cook und wird
vor dieser Aufnahme nicht verwendet. Drei fokussierte Diagnose-Tests
bestanden: Counts 9/10, veraltete DAT-/fehlende OSC-Daten und falsche
Instanzposition werden getrennt erkannt. Live-Ausgabe steht aus; keine
Kamera-, Masken-, Study-, Tracking- oder Kalibrierungsänderungen.

Der erste manuelle Aufruf blieb ohne Ausgabe: Die Startbedingung suchte
`op` und `project` nur in `globals()`. TD kann diese Namen als Builtins
bereitstellen. Der Einstieg löst die Namen jetzt direkt auf; ein zusätzlicher
Test simuliert genau diesen Textport-Kontext. Vier Diagnose-Tests bestanden.
Johannes soll denselben Aufruf wiederholen; Live-Ausgabe weiterhin offen.

### Livebericht ausgewertet: Sender hatte noch den alten Python-Code geladen

Johannes liefert den Bericht aus `AISI_v2.140_coherent_chairs_validated.toe`:
Count 10, zehn positive DAT-Radien, keine OSC/DAT- oder DAT/Instanz-Abweichung,
alle zehn Geometrien mit Skalierung 1 und Render On. Der Renderer löst alle
15 Chair-Geometrien auf (in der gelieferten Liste jeweils doppelt);
keine gemeldeten DAT-/Geometry-/Render-Fehler. Johannes erkennt keine
sichtbare Bildänderung durch die lesende Diagnose.

Ein Vergleich derselben aktuellen Source mit dem vor der Korrektur
gesicherten Python-Code reproduziert die empfangenen Chair-Positionen bis
auf Float32-Rundung (`max. 0,0000131 cm`). Der aktuelle Code weicht dagegen
bis `40,8933 cm` ab. Beispielsweise erhält TD Chair 0 bei
`x = 15,0495 cm, y = 234,0363 cm`, statt aktuell
`x = 35 cm, y = 193,143 cm`. Mit Radius 25 cm erklärt die alte X-Position
die angeschnittenen linken Kreise. Die fehlende sichtbare Instanz wird
dadurch allein noch nicht abschließend erklärt.

Der verifizierte Senderprozess PID 55018 lief seit 15:53:44 aus dem
AISI-Repository und hatte die späteren Änderungen nicht neu geladen.
Er wurde gezielt beendet und um 17:48:02 mit demselben Ziel neu gestartet:

```sh
.venv/bin/python -u -m aisi.app.sim_scene_to_osc --host 127.0.0.1 --port 9000
```

Neuer Sender PID 40517, Codex-Terminalsitzung 42655; regelmäßig `input`,
fünf Tische und zehn Chairs bei sichtbaren Chairs On gemeldet. Genau ein
`sim_scene_to_osc`-Prozess verifiziert; Study-Control PID 68593 blieb erhalten.
Kein TD-Textport-Fernzugriff, keine TD-Parameteränderung und kein Speichern.
Visuelle Bestätigung nach Senderneustart steht aus. Falls weiterhin ein
Kreis fehlt, ist als Nächstes die tatsächliche Ring-SOP-Geometrie gegenüber
den bereits bestätigten Instanzparametern zu prüfen. Nach Python-Änderungen
muss ein lang laufender Sender neu gestartet werden.

### Nach Senderneustart weiterhin neun statt zehn Kreise

Johannes' neues Bild zeigt neun Kreise; die linken Kreise sind nun vollständig
innerhalb der Ansicht. Der Neustart korrigiert somit die alte Positionierung,
behebt aber den fehlenden Chair nicht. In der unveränderten aktuellen
Zuordnung fehlt der obere Platz von `table_4`, also Index 9 bzw.
`item10` (Base COMP). Der zuvor bestätigte Instanzradius allein belegt
nicht den aktuellen Punktinhalt von `chair_ring` (Script SOP).

Gezielter lesender Nachweis vorbereitet:
`td_builders/inspect_shared_chair_ring_geometry.py` vergleicht den angeforderten
Instanzradius mit dem äußeren Radius der tatsächlichen SOP-Punkte für alle
15 Slots. Keine Änderung, kein Force-Cook und kein Speichern. Das Lesen der
Punkte kann eine reguläre Abhängigkeitsauswertung auslösen; etwaige Bildänderung
mitmelden. Zwei fokussierte Tests unterscheiden passende Geometrie von einem
veralteten Nullradius-Ring bei aktivem zehntem Chair. Die Live-Ausgabe steht
aus; eine Änderung der Radius-Abhängigkeit ist noch nicht vorgenommen.

### Veraltete Nullradius-Geometrie an Index 9 nachgewiesen

Johannes' Ringpunkte-Bericht bestätigt den verbleibenden Fehler eindeutig:
Index 9 (`item10`, Base COMP) verlangt Radius `0,13 TD`, enthält aber
128 Punkte mit Außenradius nur `0,001 TD`. Indizes 0–8 haben korrekt
`0,130000005 TD`; Indizes 10–14 sind per Instanzradius null ausgeblendet.
`active_mismatch_indices = [9]`, keine Ringfehler. Die Ring-Geometrie wurde
beim Übergang von ungültigem zu gültigem Chair somit nicht aktualisiert.

Gezielte manuelle Reparatur vorbereitet:
`td_builders/repair_shared_chair_radius_dependency.py` bindet den vorhandenen
Custom-Parameter `Valuea` jedes `chair_ring` (Script SOP) an den Radius des
zugehörigen Chair-COMPs. Der bestehende Callback liest diesen eigenen
SOP-Parameter statt indirekt den Parent-Radius. Template und 15 bestehende
Instanzen werden berücksichtigt, damit spätere Replikation die Bindung erbt.
Ringform, 64 Segmente, Strichstärke, Farben, Koordinaten, Scale-/Modussperren,
OSC-Vertrag, Kameras und Masken bleiben unverändert.

Alle Ziele werden vorab geprüft; unbekannte Callbacks oder Export-/Bind-Modi
führen vor Änderungen zum Abbruch. Rückfallkopie im bestehenden Chair-COMP,
automatische Rücknahme bei Reparaturfehler; manuelle Rücknahme per
`restore_radius_dependency(op)`. Kein Force-Cook, keine Neuanlage einer
parallelen Chair-Struktur und keine Speicherung. Drei fokussierte Tests
bestanden (Radiuswechsel, erneute Ausführung/Rücknahme, Vorab-Abbruch).
Zusätzlich wurde der originale Callback aus der gespeicherten Version 140
offline mit der einzigen geänderten Radius-Lesezeile für `0 → 0,13 → 0 → 0,13`
ausgeführt: jeweils 128 Punkte, erwartete Außenradien; übriger Text identisch.

Live-Ausführung und nachhaltige Count-Wechsel noch offen. Johannes soll
die Reparatur manuell ausführen und zunächst `9 → 10 → 9 → 10`, anschließend
`3 → 15 → 3` ohne Force-Cook prüfen. Erst nach Abnahme manuell speichern.

Johannes hat die Reparatur in Version 140 manuell ausgeführt. Bericht:
`bound_rings = 16`, Template enthalten, `forced_cook = false`,
`saved = false`. Anschließend bestätigt Johannes zehn sichtbare Kreise
bei Count 10. Die fehlende Instanz wird damit nach der expliziten
Radius-Bindung wieder korrekt dargestellt. Wiederholte Count-Wechsel
`9 → 10 → 9 → 10` und `3 → 15 → 3` bleiben noch zu bestätigen;
kein neuer gespeicherter Dateistand behauptet.

### Reparatur abgenommen und manuell in Version 141 gespeichert

Johannes bestätigt nach den angefragten Count-Wechseln: „ist jetzt behoben“.
Der Screenshot zeigt `AISI_v2.141_coherent_chairs_validated.toe`;
die Datei wurde im Projektordner lesend verifiziert (manuell gespeichert
am 2026-10-07, 18:02). SHA-256:
`ca3e69a26ba284c55102a53330a78e759cca27f223c8df0fb9eb81956a6f6d0e`.

Eine ausschließlich temporäre Kopie wurde mit `toeexpand` untersucht:
Template und alle 15 Instanzen enthalten die gespeicherte Valuea-Expression
`parent(2).par.Radius.eval()` sowie die Callback-Lesezeile
`r_outer = float(scriptOp.par.Valuea.eval())`. Die Reparatur ist damit auch
in der gespeicherten Datei nachgewiesen. Kein automatisches Speichern und
kein TD-Fernzugriff. Ein erneuter Öffnungscheck wird dadurch nicht behauptet.
Der aktuelle fehlende-Chair-Fehler ist abgeschlossen; Count 0 bleibt
ausgenommen, echte OSC-Radius-null-Prüfung und physische Raumprüfung offen.
