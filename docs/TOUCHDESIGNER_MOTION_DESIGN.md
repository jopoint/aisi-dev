# AISI Motion Design — Integrationsstand

Stand: 2026-10-26 (Git-Übergabe; letzte TD-Nachweise vom 2026-10-23). Auftrag: freigegebenes Remotion Motion Design v1.5 als eigene
Content-Komponente mit getrennten Floor-/Tabletop-Ausgängen umsetzen.
TouchDesigner läuft auf macOS. Johannes führt Textport-Befehle manuell aus;
kein Bildschirmzugriff. Keine automatische Projektspeicherung.

## Git-Übergabe an den Laborrechner — 2026-10-26

Übergabe-Branch: `codex/aisi-motion-td-handoff-20261026`, auf Basis von
`4d400b6` (`vision/wip-dark-proposals`). Enthalten sind ausschließlich
Motion-Implementierung, Prüfungen, die isolierte Autosave-Pfadoption des
Room Editors und zugehörige Dokumentation. Keine `.toe`-/`.tox`-Dateien,
Kalibrierungsdateien, lokalen Laufzeit-States, Vision-/Study-Daten oder
Debug-Artefakte. Andere lokale Arbeiten auf dem Mac bleiben uncommittet.

**Letzter nachgewiesener Stand:** Motion-Preview und Fünftisch-Simulation
visuell geprüft; 25 TD-Zustands-/Shaderkriterien bestanden. Reversibler Einbau
in die produktive Ausgabekette einschließlich Originalmaske installiert und
aktiv geprüft: sechs Kriterien bestanden, Tabletop maximaler Pixelfehler 0,0.
Johannes bestätigt die Tischdarstellung und vorhandene Bodenpfeile. Die
bisherige Chair-Quelle zeigte noch das alte Layout. Der neu implementierte
Generator-/Chair-Anschluss ist offline geprüft; seine anschließenden
Textport-Befehle wurden in diesem Chat noch nicht als ausgeführt bestätigt.
Kein Speicher-/Wiederöffnungsnachweis des Mac-TD-Projekts; der gebaute Graph
wird mit diesem Git-Push nicht übertragen. Der heutige Laufzustand von TD
wurde nicht untersucht.

**Fachlich fest:** Beim expliziten Aktivieren aus aktuellen Istposen berechnen,
anschließend Tischziele und Chairs gemeinsam festhalten. Bewegung und
UI-Einstellungsänderungen dürfen keine fortlaufende Neuberechnung auslösen.
Dies ist keine Abschaltung der quelladaptiven Berechnung beim Aktivieren.
Details unter D005a in `DECISIONS.md`.

**Vor Fortsetzung im Labor:**

1. `AGENTS.md`, aktuellen Git-/TD-Stand und diesen Abschnitt lesen. Den Motion-Branch gegen den tatsächlich aktiven Labor-Branch abgleichen; vorhandene lokale Laboränderungen erhalten. Der separat gepushte Labor-Branch `codex/lab-inbetriebnahme-20261021` (`cac6365`) ist hier nicht gemergt. Seine Änderungen an Laufzeitstatus, Source-Verfügbarkeit und Labor-Dokumentation dürfen beim Zusammenführen nicht verloren gehen.
2. Plattformpfade prüfen: TD-Helfer verwenden derzeit vielfach `/Users/Johannes/dev/Promotion_Prototypen/AISI`, der Simulator-Launcher `.venv/bin/python` und `/private/tmp`. Diese Mac-Befehle sind auf Windows noch nicht direkt ausführbar. Repository-/Python-/Temp-Pfade für den Laborrechner anpassen und die Syntax/gezielten Tests prüfen, bevor ein TD-Builder ausgeführt wird. Original-Master und Kalibrierung bleiben geschützt.
3. Tatsächlichen geöffneten TD-Graph lesend mit `inspect_motion_content.py`, `inspect_motion_live.py` und `inspect_motion_routing.py` prüfen. Komponenten werden nur bei passenden Voraussetzungen angelegt; vorhandene Namen oder abweichende Verdrahtung sind kein Auftrag zum Überschreiben. Die neue Chair-/Generator-Simulation setzt die zuvor aufgebauten eigenen Motion-/Masken-/Output-Komponenten voraus.
4. Danach den Generator-/Chair-Anschluss gemäß dem Abschnitt „Layout-Generierung einmal bei Aktivierung“ isoliert in TD prüfen. Echte Trackingdaten sind weiterhin nicht angeschlossen: `motion_live_adapter.py` ist ein geprüfter Zustandskern, kein aktiver Kamerasender. Stabile IDs, Paketaktualität, explizite Layoutaktivierung und Übereinstimmung mit den tatsächlichen Masken müssen vor produktiver Live-Freigabe zusammen geprüft werden.

Die `Sourceapproved`-Freigabe für echte Daten bleibt aus. Study-/Tracking-
Modusvergleiche und physische Projektor-/Raumabnahme bleiben gesondert offen.
Keine neue TD-Datei automatisch speichern. Der erste eigenständige
Labor-Schritt ist der Windows-Pfad-/Voraussetzungsabgleich der Motion-Helfer.

Erneute Git-Übergabeprüfung am 2026-10-26: Motion-Testauswahl mit 144 Fällen,
137 bestanden und sieben optionale native GPU-Fälle ohne konfigurierten
Runner übersprungen. Zusätzlich acht Room-Editor-Tests bestanden; Diff auf
Whitespacefehler geprüft. Die früheren nativen GPU-Nachweise sind oben bzw.
im jeweiligen Prüfblock getrennt dokumentiert; heute kein neuer TD-/Raumtest.

## Referenzen und Bearbeitungsstand

- Gelesen: `AGENTS.md`, relevante Abschnitte aus `TODO.md`,
  `PROJECT_CONTEXT.md`, `DECISIONS.md` und
  `/Users/Johannes/Downloads/AISI_TD_Implementation_Handoff.md`.
- Referenzpaket erhalten und entpackt: `/Users/Johannes/Downloads/AISI_Remotion_v1_5.zip`.
  SHA-256: `35a36c7232ba8a4976ecc5470907efc80ee57d0b52437265a9b9832d35cb7b11`.
  `src/model.ts`, `src/visual.ts`, `src/Scene.tsx`, Demo-/Interaktionsanbindung
  und Referenztests gelesen; MP4-Frames zum Vergleich extrahiert.
- Isolierter Builder, Zustandslogik, gemeinsamer Shader und Diagnose sind im
  Repository vorbereitet. Johannes hat die Motion-Komponente in TD erzeugt
  und die technische Diagnose erfolgreich ausgeführt. Keine bestehenden
  Render-/Projektorverbindungen verändert; nichts gespeichert.
- `td_builders/inspect_motion_content.py` liest die laufende Struktur aus.
  Syntax, Offline-Bericht und Verhalten bei fehlenden Knoten sind geprüft;
  Johannes hat die kompakte Abfrage erfolgreich in TD ausgeführt.

## Implementierte Preview-Fassung

- `td_builders/build_motion_preview.py` erzeugt ausschließlich
  `/project1/comp_aisi_motion_v1_5` (Container COMP). Existiert der Name bereits,
  wird abgebrochen; bei einem Aufbaufehler wird nur der neue COMP entfernt.
- `motion_runtime` (Text DAT) enthält den eingebetteten Code aus
  `td_builders/motion_design.py`; die Geometrie verwendet das kanonische Rect
  und die bestehenden Polygon-/Kreisprüfungen aus `aisi.core.table_geometry`.
- Erster manueller Builder-Aufruf in TD scheiterte noch vor der COMP-Erzeugung
  an `dataclass(slots=True)`. `motion_geometry_compat.py` lädt für Python 3.9
  denselben kanonischen Geometriequelltext in einen eigenen Namensraum ohne
  die Speicheroptimierung `slots` und ohne den nur für Annotationen benötigten
  Import der Anwendungsmodelle. `frozen` und alle Geometriefunktionen bleiben
  erhalten. Keine gemeinsamen Dateien oder globalen Dataclass-Funktionen
  werden im TD-Prozess verändert. Der erneute Aufbau ist inzwischen bestanden.
- Zweiter TD-Aufruf erreichte die Ausgangserzeugung; der fälschlich verwendete
  Parameter `index` am Out TOP verursachte einen Abbruch. Der neue COMP wurde
  durch den Builder zurückgenommen. Korrigiert: `connectorder` nur verwenden,
  falls vorhanden; andernfalls bestimmen die alphabetischen Namen
  `out_floor`, `out_tabletop` die Reihenfolge. Erneuter Aufbau bestanden.
- `state` (Script TOP) transportiert eine 6 × 6 RGBA-Float32-Matrix;
  `render_floor`, `render_tabletop`, `render_preview` (jeweils GLSL TOP)
  verwenden denselben Shader aus `td_builders/motion_design.frag`.
- Zwei Oberflächenausgänge: `out_floor`, `out_tabletop` (jeweils Out TOP).
  `render_preview` (GLSL TOP) kombiniert beide mit einer grauen Tischfläche;
  diese Hilfsfläche und der grüne Raumhintergrund gehören nur zur Vorschau.
- Reale monotone Sekunden; ein eigener Layout-Zähler startet die globale
  3-s-Welle einmal. Poseänderungen lösen keinen Reveal aus. Die Zustandsmaschine
  verwaltet Guidance, Dissolve, Completed und zeitliche Kontakt-/Pulszustände
  unabhängig je `table_id`; der Shader unterstützt bis zu fünf Rect-Tische.
- Der Pfeil entspricht den drei abgerundeten Segmenten aus `Scene.tsx`.
  Kontakt wird über die abgerundeten Kerne berechnet. Ziel-/Source-Schnitt,
  Verdeckung und Clipping verwenden dieselbe Kontur. Der erste Bodenpfeil
  verankert sich an der abgerundeten Zielkante; die Referenz benutzt hier
  noch die eckige Randdistanz. Diese Präzisierung folgt dem Handoff.
- Grüne Unschärfe, Puls-/Dissolve-Kanten und Reveal-Saum sind analytische
  GPU-Näherungen der SVG-Filter; keine Pixelgleichheit behaupten. Farb- und
  Kantenvergleich in TD ist noch erforderlich.

### Manuelle Verwendung

Im TD-Textport auf dem Mac:

```python
p = '/Users/Johannes/dev/Promotion_Prototypen/AISI/td_builders/build_motion_preview.py'; exec(compile(open(p, encoding='utf-8').read(), p, 'exec'))
p = '/Users/Johannes/dev/Promotion_Prototypen/AISI/td_builders/check_motion_preview.py'; exec(compile(open(p, encoding='utf-8').read(), p, 'exec'))
```

Die Diagnose kocht ausschließlich neue Motion-Operatoren und meldet Fehler,
Auflösung und Zustandsmatrix. `passed` betrifft diese technische Diagnose,
keine visuelle Freigabe. Im Operator-Viewer `render_preview` (GLSL TOP) öffnen.
Keine Projektorfenster öffnen und nicht automatisch speichern.

```python
c = op('/project1/comp_aisi_motion_v1_5')
c.par.Demo = True
c.par.Layoutrevision = int(c.par.Layoutrevision.eval()) + 1
```

Damit startet die einmalige 22-s-Referenzbewegung. `Demo = False` erlaubt
manuelle Source-/Target-Parameter in cm und Grad. Die Referenzrotation wird
einmal um +90° in die kanonische Längsachsenkonvention umgerechnet:
Source `(110, 180, 84°)`, Target `(320, 330, 122°)`.

Für einen frischen Kontaktversuch zuerst neue Source/Target setzen und danach
`Layoutrevision` erhöhen. Nach abgeschlossenem Dissolve sind größere Bewegungen
gegenüber der gespeicherten Erfolgspose zur Reaktivierung erforderlich.

`Usedat = True` schaltet auf `poses` (Table DAT) im neuen COMP um.
Spalten: `table_id, source_x, source_y, source_r, target_x, target_y, target_r,
valid, active`. IDs müssen eindeutig und nicht leer sein; maximal fünf Zeilen.
`active = 0` erhält die Tischbelegung für Verdeckung und globale Welle, ohne
individuelle Navigation. Ungültige/Nicht-Endliche Posen werden ausgeblendet
und können keinen Erfolg auslösen. Ein gestarteter Dissolve läuft zeitlich
weiter. Dieses konservative Verhalten ist eine technische Vorschauannahme,
keine gestalterische Freigabe für längeren Trackingverlust.

Stillstandserkennung für die Vorschau: Bewegung gegenüber dem letzten
Bewegungsanker über 0,3 cm oder 0,2° setzt die Idle-Zeit zurück. Diese
reversiblen Filterwerte sind noch unter realem Tracking-Jitter zu prüfen.

### Lokal ausgeführte Nachweise

- In der laufenden TD-Instanz durch Johannes geprüft: Python 3.9.5,
  `state` (Script TOP) 6 × 6 und Zustandsmatrix `[6, 6, 4]`; beide
  Oberflächenrenderer, beide Ausgänge und `render_preview` (GLSL TOP)
  fehlerfrei bei 1000 × 1000 Pixeln. Diagnose meldet `passed: true`.
  Source `(110,180,84°)`, Target `(320,330,122°)`, Navigationsskala 1,
  Kontakt/Grün/Phase jeweils 0. Das bestätigt Aufbau und Shaderausführung,
  noch keine sichtbare Bewegungssequenz oder kontinuierliche Aktualisierung.
- Anschließend Demo im Operator-Viewer gestartet; Johannes bestätigt
  „ja sieht richtig aus“. Damit ist die sichtbare Demo qualitativ bestätigt.
  Keine zusätzliche Behauptung zu einzelnen Grenzfällen, Trackingverlust,
  unabhängigen Mehrtisch-Abschlüssen oder realer Projektion.
- 14 fokussierte Tests in `tests/test_motion_design.py`: Python-3.9-kompatibler
  Geometrieimport mit weiterhin unveränderlichen Datenklassen, Kontakt einschließlich
  gedrehter Ecken, keine Freigabe vor Kontakt, erneuter Kontakt, Ausblendung,
  Verschlechterung, positiver Navigationsradius außerhalb der Toleranz,
  direkter/verriegelter Dissolve, Reaktivierung, ungültige Posen,
  Puls-Abbruch, globale Aktivierung und unabhängige IDs.
- Die 22-s-Demo läuft im Zustandsmodell bei 24, 60 und 97 Hz bis Completed.
- Alle 12 unveränderten Tests des gelieferten Remotion-Pakets bestehen.
- 1200 deterministische zufällige Posepaare: Kontaktentscheidung stimmt mit
  dem originalen `model.ts` aus v1.5 überein.
- Shader offline in einem macOS-CGL-Kontext kompiliert und gelinkt (Apple
  Software Renderer, GLSL 4.10); acht Zeitpunkte als Bilder gerendert.
  Beim Vergleich mit der gelieferten MP4 wurde ein undefinierter Richtungswinkel
  bei Distanz null erkannt und entsprechend der Referenz auf null gesetzt.
  Das ist kein Nachweis der Kompilierung in der laufenden TD-Version.

Reproduzierbare fokussierte Repository-Prüfung:

```bash
PYTHONPATH=src:. .venv/bin/python -m unittest discover -s tests -p test_motion_design.py -v
```

## Im laufenden Projekt durch Textport-Ausgabe nachgewiesen

Die von Johannes übermittelten Ausgaben stammen aus der laufenden Instanz;
sie belegen Anschlüsse und Parameter, keine korrekte physische Projektion.
Der Anfang des ersten langen Berichts fehlt. Die kompakte zweite Ausgabe
enthält Renderauswahl, Kamera und ausgewählte OSC-Werte vollständig.

Alle folgenden Pfade liegen unter `/project1/`:

| Funktion | Tatsächlicher Anschluss |
| --- | --- |
| Floor-Quelle | `comp_layout_proposal/null_floor_with_optional_synth_chairs` (Null TOP), gespeist von `switch_enable_synth_chairs_regular` (Switch TOP) |
| Floor-Auswahl | `comp_output/select_central_floor` (Select TOP) referenziert diese Floor-Quelle; Eingang 0 von `switch_floor` (Switch TOP) |
| Tabletop-Quelle | `comp_layout_proposal/null_tabletop_masked` (Null TOP), gespeist von `mask_tabletop` (Composite TOP, Multiply) |
| Tabletop-Auswahl | `comp_output/select_tabletop` (Select TOP) referenziert diese Tabletop-Quelle; Eingang 0 von `switch_tabletop` (Switch TOP) |
| Maskenquelle | `comp_layout_proposal/null_table_mask` (Null TOP), gespeist von `reorder_table_mask` (Reorder TOP) |
| Maskenauswahl | `comp_output/select_table_mask` (Select TOP) → Eingang 0 von `switch_table_mask` (Switch TOP) |
| Projektor 0 | `comp_output/comp_projector_0` (Base COMP), Eingänge: `layer_floor_switch`, `layer_tabletop_switch`, `switch_table_mask` (jeweils Switch TOP) |
| Projektor 1 | `comp_output/comp_projector_1` (Base COMP), Eingänge: `rotate_180_floor`, `rotate_180_tabletop`, `rotate_180_table_mask` (jeweils Transform TOP) |

`switch_floor`, `switch_tabletop` und `switch_table_mask` (jeweils Switch TOP)
wählen über `int(op('panel_mode')['state'][0])` zwischen Content und
Kalibrierungsquelle. Diese Umschaltung bleibt erhalten. Homographien,
Projektortransformationen und Maskenreihenfolge bleiben geschützt.

`render_floor` und `render_tabletop` (jeweils Render TOP) unter
`comp_layout_proposal` verwenden `cam1` (Camera COMP), orthografisch,
Breite 2,6 TD-Einheiten, Z = 5, keine Kamerarotation, 2000 × 2000 Pixel.
Ihre Geometry-Expressions enthalten getrennte Tracking-/Study-/AISI-Zweige.
Im gemeldeten AISI-Modus enthalten die aufgelösten Listen Tischgeometrien
doppelt; Ursache und Wirkung sind noch nicht untersucht. Keine Bereinigung
als Nebenänderung vornehmen.

## Pose-Schnittstelle und offene Umrechnung

Die Meldung enthält `study/mode = 2`, `table/count = 5`,
`table/0/source_available = 1`, Rect-Typ-ID 2 und Maße 160 × 80 cm.
`comp_io/null_osc_raw` (Null CHOP) enthält Source-/Target-Pose je Index.
Das Repository sendet Winkel über diesen allgemeinen Tischpfad negiert;
der separate Vision-Pfad verwendet Weltwinkel. Die Pfade nicht vermischen.

Gleichzeitig gemeldete Werte für Slot 0 und `item1` (Base COMP):

| Größe | OSC | Item-Parameter |
| --- | --- | --- |
| Source X | 162,442993 cm | +0,455296 TD |
| Source Y | 229,960999 cm | −0,104203 TD |
| Source Rotation | 178,576004° | 178,576004° |
| Target X | 152,662994 cm | +0,506152 TD |
| Target Y | 198,401993 cm | −0,268310 TD |
| Target Rotation | 178,638000° | 178,638000° |

Die Positionswerte entsprechen in dieser Stichprobe
`X = (250 − world_x) * 0.0052`, `Y = (world_y − 250) * 0.0052`.
Das ist gegenüber der dokumentierten Standardumrechnung auf beiden Achsen
umgekehrt. Die zuständige Aktualisierungslogik ist noch nicht ausgelesen;
eine allgemeine Transformationsregel oder Fehlerursache ist damit nicht
nachgewiesen. Vor dem Live-Anschluss an bekannten Posen prüfen und an einer
einzigen Content-Schnittstelle abbilden. Keine Kalibrierung kompensierend ändern.

`source_available` allein belegt keine Aktualität: Empfangszeit, stabile
`table_id`-/Slot-Bindung und Layout-Aktivierungsereignis sind vor Livebetrieb
noch zu prüfen. Eine Pose-Aktualisierung darf keinen Reveal auslösen.

## Room-Editor-/OSC-Simulation — Einzel-Tisch-Abnahme bestätigt

Johannes wählt ausdrücklich zuerst die Room-Editor-/OSC-Simulation. Bei der
Prüfung lief auf dem Mac kein Python-Sender. Der bestehende Empfänger ist
`comp_io/oscin1` (OSC In CHOP), Port 9000, `protocol = msging`,
`netaddress = localhost`, `timeslice = True`; diese Einstellungen bleiben
unverändert. Der Raw-CHOP enthält aufbewahrte Werte: Bei Vision-Count 5 sind
auch Slots 5/6 noch als verfügbar markiert. Keine Aktualität daraus ableiten.

`aisi.app.motion_preview_sim` verwendet den bestehenden Room Editor mit einem
optionalen separaten Szenenpfad. Standard-Editor und seine bisherige Szene
bleiben erhalten. Für die Motion-Simulation werden ein einzelner Rect-Tisch,
die Referenzzielpose und eigene Bedienelemente für Aktivierung, Zielpose und
Übertragungspause eingerichtet. Wahlweise sind jetzt 1, 3 oder 5 Tische
über `--tables` möglich; ohne CLI-Option bleibt es beim Einzel-Tisch-Fall.
Szene und Prozesslog liegen ausschließlich
unter `/private/tmp/aisi-motion-sim/`.

Der Simulator sendet alle 50 ms ein OSC-Bundle an den bestehenden Empfänger,
ausschließlich unter dem neuen Präfix `/aisi_motion/`. Keine bisherigen
`/table/...`, `/vision/...` oder `/study/...`-Adressen werden gesendet oder
geändert. Kein weiterer Netzwerkempfänger wird angelegt. Die neue Vorschau
liest Tischdaten anhand URL-kodierter `table_id` im Kanalpfad; Source und
Target bleiben unter derselben ID. Globale Session-, Frame-, Layoutzähler
und Count begrenzen die aktuellen Daten. Diese Zähler bleiben Float32-exakt.

`td_builders/motion_osc.py` prüft vollständige Frames und zählt alte
Tischkanäle nicht als aktuelle Belegung. Gespeicherte Startwerte werden erst
nach einem weiteren Frame derselben Session gültig. Ohne neuen Frame für
0,5 s wird die gesamte neue Content-Ausgabe transparent. Ungültige Daten,
zurücklaufende Frames und Zieländerungen ohne Layoutaktivierung werden
abgelehnt. Neue Posen starten keinen Reveal. Die Zielpose wird im Simulator
getrennt von den beweglichen Source-Posen gehalten; „Vorschlag aktivieren“
erhöht den Layoutzähler. Laufzeitobjekte erhalten leere TD-Startup-Werte,
damit monotone Zeiten oder alte Streamzustände nicht aus einer .toe fortleben.

Manuell nacheinander im TD-Textport ausführen. Der Launcher startet nach dem
Mehrtisch-Auftrag standardmäßig drei Tische. Bei einem Count-Wechsel startet
er den eindeutig zugeordneten Motion-Simulator neu; das TD-Preview bleibt offen:

```python
p = '/Users/Johannes/dev/Promotion_Prototypen/AISI/td_builders/connect_motion_sim_preview.py'; exec(compile(open(p, encoding='utf-8').read(), p, 'exec'))
p = '/Users/Johannes/dev/Promotion_Prototypen/AISI/td_builders/start_motion_simulation.py'; exec(compile(open(p, encoding='utf-8').read(), p, 'exec'))
```

Der erste Befehl aktualisiert ausschließlich die neue Motion-Komponente.
Der zweite startet den Room Editor mit dem vorhandenen Repository-Python
statt TD-Python 3.9; doppelte Starts desselben gestarteten Prozesses werden
vermieden. Das bestehende Motion-Preview-Fenster weiterverwenden.
Tisch ziehen, mit Q/E drehen; Zielkontur ist im Room Editor grün gestrichelt.
Bei Übertragungspause muss das TD-Preview nach 0,5 s nur den Raumhintergrund
zeigen. Nach Fortsetzen darf keine neue Welle starten. Mit „Auf Zielpose“
direkten Dissolve prüfen; mit „Vorschlag aktivieren“ eine neue Welle.
Beenden über ESC oder das Schließen des Room-Editor-Fensters.

Technische Diagnose danach erneut mit `check_motion_preview.py` ausführen;
`live_stream` meldet Aktualität, Grund, Session/Frame, IDs und Layoutkennung.
Zurück zur vorherigen Demo: `Useosc = False`, `Demo = True`, anschließend
`Layoutrevision` erhöhen.

Nachweise: 26 Motion-/Transporttests und acht bestehende Room-Editor-Tests
bestanden. Dazu gehören OSC-Bundle-Kodierung/-Dekodierung, Tischidentität,
alte Kanäle bei sinkendem Count, Senderneustart, Timeout, explizite
Layoutaktivierung, tatsächliche TD-Matrixausgabe mit simuliertem Raw-CHOP
und ein separater Szenenspeicherpfad. Keine echten Netzwerkpakete oder
GUI-Bedienung sind durch diese Offline-Tests nachgewiesen. Der aktualisierte
Shader kompiliert offline auf macOS. Der manuelle Anschluss in TD und das
Room-Editor-Fenster waren zunächst offen. Johannes hat danach den Anschluss
und Start ausgeführt (Simulator-PID 82544) und bestätigt: „das preview reagiert
korrekt“. Damit ist die Reaktion auf die Room-Editor-/OSC-Simulation
qualitativ bestätigt. Der Bericht des Anschlussskripts bestätigt unveränderte
Empfängereinstellungen und keine neuen Projektorverbindungen. Eine explizite
Einzelbestätigung von Pause/Fortsetzung oder sämtlichen Grenzfällen wird
daraus nicht abgeleitet. Kamera-/Live-Tracking und die produktive
Content-Umschaltung bleiben eigene folgende Schritte.

### Deterministische TD-Grenzfall-Abnahme

`td_builders/check_motion_acceptance.py` erstellt einen eigenen temporären
`comp_aisi_motion_acceptance` (Container COMP) mit kontrollierter Testzeit,
gleichem Zustandsmodell und gleichem Shader. Der bestehende Motion-COMP,
OSC-Empfänger, Kalibrierung und Ausgabe werden nicht verändert. Nach dem
Test wird ausschließlich der temporäre COMP entfernt; bei einem bereits
vorhandenen gleichnamigen COMP wird vorab abgebrochen.

Die Prüfung misst Kontakt-/Navigationszustände und echte TOP-Pixel: kein
Grün vor Kontakt trotz verbessertem Winkel; Kontaktbeginn und weitere
Annäherung; gehaltene Formgröße und sichtbares Ausfaden nach Kontaktverlust;
neuer Kontakt ohne alten Fortschritt; positiver Radius bei 6° Winkelfehler;
sofort grüne Platte, Kreis null und direkter Dissolve; Verriegelung bei
Poseänderung; beide Ausgänge nach 1 s transparent; unabhängiger zweiter Tisch;
Reaktivierung; Pulsstart und 180-ms-Abbruch; globale Welle auf inaktivem Tisch;
kein Erfolg bei ungültiger Pose. Physische Projektion und tatsächliche
Netzwerkausfälle sind damit nicht geprüft.

```python
p = '/Users/Johannes/dev/Promotion_Prototypen/AISI/td_builders/check_motion_acceptance.py'; exec(compile(open(p, encoding='utf-8').read(), p, 'exec'))
```

Johannes hat die Prüfung in der laufenden TD-Instanz ausgeführt:
`passed: true`, `check_count: 19`, `temporary_component_removed: true`,
`saved: false`. Alle 19 aufgeführten Zustands-/Pixelprüfungen bestehen.
Das umfasst insbesondere den positiven Navigationsradius bei 6° Winkelfehler,
den nicht abgeschnittenen grünen Kontaktverlust-Fade, die direkte grüne
Erfolgsfläche, beide vollständig transparenten Ausgänge nach dem Dissolve
und die unabhängige Navigation eines zweiten Tisches.

Diese synthetische TD-Abnahme ergänzt die qualitative Demo- und
Room-Editor-Bestätigung. Sie ersetzt weder den sichtbaren Netzwerk-Test
über „Übertragung pausieren“/„Übertragung fortsetzen“ noch eine physische
Prüfung. Johannes hat danach alle drei sichtbaren Punkte ausdrücklich bestätigt:
Timeout nach 0,5 s, Fortsetzung ohne neue Welle und genau eine neue Welle nur
bei „Vorschlag aktivieren“.

### Mehrtisch-Simulation — Drei- und Fünftisch-Prüfung bestätigt

`make_scenario()` im bestehenden Simulationsmodul enthält deterministische
Testposen. Studien-Trials und Lernformatvorlagen werden nicht geändert.

- Drei Tische: `table_0` von `(100,110,90°)` nach `(100,370,90°)`;
  `table_1` von `(250,110,70°)` nach `(250,370,90°)`;
  `table_2` bleibt bei `(400,250,90°)`. Die ersten beiden sind aktiv,
  der dritte erhält ausschließlich die gemeinsame Reveal-Welle.
- Fünf Tische: vier aktive Tische und ein unveränderter Tisch. Diese
  Kapazitätsstichprobe hat bereits überlappende eigene Source-/Target-Flächen.
  Source-/Ziel-Endzustände verschiedener Tische und sämtliche Mischungen
  abgeschlossener/unabgeschlossener Tische sind mit kanonischen Polygonen
  offline auf ROI und Kollisionsfreiheit geprüft. Freies Ziehen beliebiger
  Zwischenposen ist damit nicht als kollisionsfreie Bewegung geplant.
- OSC-IDs und zugehörige Targets bleiben bei umgekehrter Scene Order erhalten.
  Ein einzelner Abschluss verändert den zweiten aktiven Tisch nicht.
  Entfernte Tische bleiben trotz alter Empfangskanäle keine aktuelle Belegung.

Der TD-Launcher nutzt für drei Tische
`/private/tmp/aisi-motion-sim/multitable_3.json`; die alte Einzel-Tisch-Datei
bleibt erhalten. Beim ersten Wechsel blieb der alte Einzel-Tisch-Prozess
sichtbar. Der Launcher startet jetzt bei anderem Count ausschließlich den
im Motion-COMP gespeicherten Prozess neu, sofern dessen Programm und
Modul eindeutig dem Motion-Simulator entsprechen. Bei gleichem Count wird
die Instanz weiterverwendet; unbekannte Prozesse werden nicht beendet.
Drei fokussierte Launcher-Tests bestehen. Für eine spätere Fünftisch-Prüfung
kann direkt nach dem Laden des Launchers
`print(start(op, table_count=5))` im Textport ausgeführt werden.

Sichtbare Prüffolge: Reveal auf allen drei Tischen beobachten; `table_0`
auswählen und „Auf Zielpose“ betätigen. Danach muss dessen Content verschwinden,
während `table_1` weiter navigiert. Anschließend `table_1` auswählen und
abschließen; `table_2` bleibt ohne Navigationsgrafik. Kein Abschluss darf
eine neue Welle auslösen.

## Nächster Arbeitsschritt und Abnahme

Johannes meldet in der Dreitisch-Ansicht zwei grüne Feedbackformen, die trotz
Annäherung im Anfangszustand bleiben. Offline ist eine Referenzabweichung
reproduziert und im Quelltext korrigiert: Reaktivierung nach Abschluss darf
die separate Kontakt-Historie nicht zurücksetzen; sie läuft auch während
Dissolve/Completed weiter. Zwei neue Regressionstests sichern fortbestehenden
Kontakt und Kontaktverlust während des Dissolves ab. Die Navigationswerte
nach Reaktivierung stimmen im nachgespielten Fall mit `model.ts` und
`visual.ts` der Referenz überein. Alle 31 Motion-Tests bestehen.

Vor dem Laden der Korrektur las `inspect_motion_feedback.py` ohne Cook oder Schreibzugriff die aktuellen
Posen, Tisch-IDs, Kontakt-Baselines, Phasen und Fortschrittswerte aus. Die
Abfrage von Johannes bestätigt frische Daten für alle drei IDs:
`table_0` hat Baseline 0,6200 und Fortschritt 0,8333, also Navigation 0,5614;
`table_1` hat Baseline 0,9725 über Fortschritt 0,9167 und `table_2` Baseline
0,8854 über Fortschritt 0,7492. Die beiden letzteren bleiben deshalb bei
Navigation/Halo 0. Alle befinden sich in Guidance mit Kontakt; Erfolg-Anker
sind bereits gelöscht. Die Abfrage belegt die unmittelbare Ursache, kann
aber die vorherige Folge aus Kontakt, Aktivierung und Abschluss nicht
rekonstruieren. Insbesondere beginnt der unveränderte dritte Tisch bereits auf
seinem Ziel: Kontakt-Baseline 1 ist auch in der Referenz möglich und muss von
einem irrtümlichen Reset nach einem zuvor durchgeführten Anlauf unterschieden
werden. Dafür keine neue Fortschrittsformel einführen.

Zum Laden dient der bestehende `connect_motion_sim_preview.py`; dieser setzt
ausschließlich die eigene Motion-/Empfangshistorie zurück. Danach betroffene
Tische vollständig von ihrer Zielkontur wegziehen und wieder annähern, ohne
zwischendurch einen neuen Vorschlag zu aktivieren. Das erzeugt einen neuen
geometrischen Erstkontakt statt einer erfundenen rückwirkenden Baseline.
`check_motion_acceptance.py` enthält jetzt 22 statt 19 Prüfungen; die drei
zusätzlichen TD-Prüfungen betreffen fortbestehenden Kontakt bei Reaktivierung
und Kontaktverlust/-wiedereintritt während/nach Dissolve. Diese aktualisierte
TD-Abnahme ist inzwischen durch Johannes ausgeführt: alle 22 Prüfungen
bestanden, temporärer COMP entfernt und nichts gespeichert. Johannes
bestätigt korrekt wachsendes Grün bei allen drei Tischen sowie erhaltenen
Fortschritt nach Abschluss und erneutem Verdrehen. Damit ist die Korrektur
im laufenden Preview nachgewiesen, keine physische Raumprüfung.

Aufbau, Diagnose, sichtbare Demo, Simulationsreaktion, die 22 synthetischen
TD-Grenzfallprüfungen sowie Pause/Fortsetzung/Neuaktivierung sind bestätigt.
Das Dreitisch-Feedback samt Reaktivierung ist sichtbar bestätigt.
Die anschließende Fünftisch-Kapazitätsprüfung mit vier unabhängigen
Abschlüssen und einem unveränderten Tisch wurde durch Johannes ausgeführt.
Dazu den bestehenden Launcher
laden und `print(start(op, table_count=5))` ausführen. Dieser ersetzt
ausschließlich den zugeordneten Dreitisch-Simulator; der neue Session-Zähler
startet eine eigene Vorschau-Historie. Beim unveränderten Tisch
`table_2` muss die gemeinsame Reveal-Welle erscheinen, anschließend kein
Navigationscontent. Die vier aktiven Tische nacheinander über „Auf Zielpose“
abschließen; jeder Abschluss darf nur den eigenen Content entfernen und
keine neue Welle starten. Johannes bestätigt alle fünf sichtbaren Tische,
Reveal und unabhängige Abschlüsse wie beschrieben. Die Startausgabe bestätigt
den Wechsel von PID 89229 (drei Tische) auf PID 91706 (fünf Tische), eigene
Szenendatei `multitable_5.json`, keine TD-Projektspeicherung.

Johannes stellt klar: Auf diesem Mac gibt es keine echten Trackingdaten.
Kamera-/Live-Abnahme wird deshalb nicht aus Simulation abgeleitet. Als
nächster lokaler Schritt wird der Anschluss an die bestehende
Content-Umschaltung mit Simulationsdaten vorbereitet. Der neue Helfer
`inspect_motion_routing.py` liest dafür aktuelle Inputs/Outputs,
Select-/Switch-Parameter, Masken und einen vorgelagerten Verbindungsschritt.
Er erzwingt keine Cooks und ändert keine Operatoren. Johannes hat die Abfrage
ausgeführt: `mask_tabletop` ist ein Composite TOP mit Multiply, Eingang 0
`null_tabletop`, Eingang 1 `null_table_mask`. Floor läuft durch den vorhandenen
optionalen Chair-Zweig, die drei Ausgabe-Switches schalten unverändert über
`panel_mode` auf Kalibrierung. Aktueller `study/mode` ist 2 (AISI).

### Isolierte Routing-Vorprüfung — in TD bestanden

Die Motion-Simulation verwendet eigene Source-Posen. Die bestehende
Tabletop-Maske folgt weiterhin dem alten Tischdatenpfad. Deshalb darf deren
räumliche Deckung mit der neuen Simulation nicht vorausgesetzt werden.
Die bestehende Maskierung wird weder umgestellt noch durch eine neue
Produktionsmaske ersetzt.

`build_motion_routing_preview.py` erzeugt ausschließlich
`/project1/comp_aisi_motion_routing_preview` (Container COMP), anfänglich
deaktiviert. Zwei Select TOPs lesen die bisherigen endgültigen Floor-/Tabletop-
Quellen, zwei weitere die neuen Motion-Ausgänge. Der Motion-Tabletop-Zweig
verwendet eine Kopie des vorhandenen Multiply-Operators mit unveränderter
Input-Reihenfolge und einem Select auf die bestehende Maske. Der Floor-Zweig
kopiert die vorhandene Chair-Komposition und folgt deren bestehendem
Enable-Schalter. Originalknoten und deren Verbindungen bleiben unverändert;
der neue COMP wird nicht mit Projektoren oder Ausgabe-Selects verbunden.

Der lokale Schalter `Enablemotion` wird nur bei `study/mode == 2` wirksam;
fehlender Modus, Tracking und Study wählen den bisherigen Content. Vor dem
Kopieren werden aktuelle Masken-/Chair-Verbindungen geprüft. Dynamische
Composite-Parameter führen grundsätzlich zum Abbruch, damit relative Ausdrücke
oder Exports nicht versehentlich anders ausgewertet werden. Einzige Ausnahme:
Expressions für `resolutionw`/`resolutionh` werden in der Kopie durch absolute
Referenzen auf die ausgewerteten Originalparameter ersetzt. Originalausdrücke
bleiben unverändert; Auflösungsänderungen werden weiterhin übernommen.
Exports und Bindings bleiben auch für diese Parameter gesperrt. Bei Aufbaufehlern
wird nur der neue COMP entfernt. Sieben fokussierte Offline-Tests prüfen
Modusfälle, Preflight, getrennte Verbindungen und Rollback; Python-3.9-Syntax
der neuen TD-Helfer ist geprüft.

Johannes' erster Aufbauversuch brach in der Vorprüfung wegen der dynamischen
Chair-Parameter `resolutionw` und `resolutionh` ab, noch vor Erzeugung des
Prüfzweigs. Der anschließende Checker meldete deshalb erwartungsgemäß einen
fehlenden COMP. Die oben beschriebene explizite Auflösungsreferenz korrigiert
diese zu strenge Vorprüfung; die erneute Ausführung in TD ist bestanden. Tests
prüfen auch weitergereichte Auflösungsänderungen und unveränderte
Originalausdrücke. Die TD-Prüfung vergleicht zusätzlich beide
Auflösungsparameter der Kopien mit den Originalen.

```python
p = '/Users/Johannes/dev/Promotion_Prototypen/AISI/td_builders/build_motion_routing_preview.py'; exec(compile(open(p, encoding='utf-8').read(), p, 'exec'))
p = '/Users/Johannes/dev/Promotion_Prototypen/AISI/td_builders/check_motion_routing_preview.py'; exec(compile(open(p, encoding='utf-8').read(), p, 'exec'))
```

Die TD-Prüfung vergleicht im deaktivierten Prüfzweig Bildgröße und Pixelhash
mit den bisherigen Quellen, prüft Maskenreihenfolge, aktuelle Moduswahl,
fehlerfreies Kochen und Chair-Auswahl. Sie stellt den lokalen Enable-Wert
wieder her. Änderungen am globalen Modus oder an bestehenden Ausgabewegen
nimmt sie nicht vor. Johannes hat Aufbau und Prüfung erfolgreich ausgeführt:
alle sieben TD-Prüfungen bestehen, deaktiviert sind beide Ausgänge pixelgleich,
die Kopien übernehmen korrekte Auflösungswerte und die Chair-Auswahl folgt
dem Original. `production_outputs_changed: false`, `saved: false`,
`local_enable_restored: true`. Globale Study-/Tracking-Bildvergleiche sind
damit nicht ersetzt. Wegen unterschiedlicher Posen kann
das Motion-Bild im Prüfzweig an der alten Maske abgeschnitten erscheinen;
das ist noch kein Nachweis einer fehlerhaften Maske. Nächster Schritt nach
der technischen TD-Prüfung ist die gemeinsame Posequelle für Content und
bestehende Maske, bevor ein produktiver Anschluss aktiviert wird.

Der neue reine Lesehelfer `inspect_motion_mask_alignment.py` erfasst dazu
die vorhandene aktive Tischliste, Source-/Target-Parameter der bis zu fünf
Instanzen, Maskenrenderer und Kamera. Für die erste Instanz werden außerdem
Source-/Target-/Maskentransformationen und Grenzen der gerenderten SOP-Punkte
ausgelesen. So lassen sich Achsen und Maße anhand der tatsächlichen Geometrie
zuordnen. Es gibt keinen erzwungenen Cook und keine Änderungen. Johannes hat
die Ausgabe übermittelt. Sie bestätigt fünf Rect-Zeilen mit Legacy-Slots 0–4,
Source-/Target-Paaren und unveränderter orthografischer Kamera (Breite 2,6).
Die Source-Kontur hat lokale Maße 150 × 70 cm, die Zielkontur 170 × 90 cm;
das sind Gestaltungskonturen, keine neuen Maße für das kanonische Rect.
Die untersuchte Instanzmaske hat lokale Grenzen ±1 TD-Einheit, ist aber
überhaupt nicht in der aktiven Masken-Geometrieliste enthalten.

Der Maskenrenderer referenziert tatsächlich die sechs
`comp_study_visualization/rect_setup_mask_geo_00` bis `05`, jeweils doppelt.
Im Repository erzeugt `study_setup_masks.py` diese als Vision-Occupancy-
Masken; ihre tatsächlichen Transformationen im laufenden Graph waren im
Bericht noch nicht enthalten. Aus Namen allein wird keine Fehlfunktion
abgeleitet. Weder Liste noch geschützte Geometrien werden bereinigt.

### Statischer Poseabgleich mit der aktiven Maske — in TD bestanden

`build_motion_aligned_snapshot.py` liest unmittelbar die tatsächlich vom
Maskenrenderer referenzierten Geometrien. Er prüft deren sichtbare Slotmenge,
Translation, axiale Rotation, Skalierung und Neigung gegen `tables_active`.
Bestehende Source-/Target-Posen werden nicht geändert. Doppelte Maskenreferenzen
werden nur für die Prüfung zusammengefasst und im Bericht gezählt; die
Originalauswahl bleibt unverändert. Bei abweichenden Posen meldet der Helfer
die tatsächlichen Werte und legt nichts an.

Johannes' erster Versuch meldete Abweichungen für alle fünf Slots und legte
korrekt nichts an. Die tatsächlichen Differenzen sind jedoch sehr klein:
maximal 0,046001 cm Translation und 0,017014° axiale Rotation. Die bisherige
Gleichheitsprüfung war für die getrennten gespeicherten Werte zu streng.
Ihre zeitliche Entstehung ist nicht nachgewiesen; daraus keine Live-Aktualität
ableiten.

Die Slot-Zuordnung wird jetzt mit dem Rastermaß geprüft: ein Pixel über dem
500-cm-ROI, also 0,25 cm bei 2000 Pixeln. Die konservative obere Schranke
`Translation + 2 × halbe Tischdiagonale × sin(Winkelfehler / 2)` muss innerhalb
dieses Pixels liegen. Tischmaße kommen aus der gemeinsamen Motion-/Geometrie-
Implementierung. Das ist ausschließlich ein Zuordnungskriterium für die
statische Probe, keine Änderung der Erfolgs- oder Trackingtoleranzen.
Skalierung, Neigung, Slotmenge und Sichtbarkeit werden weiterhin geprüft.

Nur bei erfolgreichem rasterbezogenem Abgleich erzeugt der vorhandene Motion-Builder
einen separaten `comp_aisi_motion_aligned_snapshot` (Container COMP), gespeist
aus den **exakten eingefrorenen Maskenposen** als Sources und den unveränderten
Legacy-Targets desselben Slots. So bleibt zwischen Masken- und Content-Source
keine tolerierte Restabweichung innerhalb der Probe. Die bestehende Umrechnung
`td_pose` wird wiederverwendet. Kameraabbildung und quadratisches Raster
werden vorher geprüft. Die Original-Simulation, Routing-Selects und
Produktionsausgaben bleiben unverändert; nichts wird gespeichert.

Die Schlüssel `legacy_slot_0` usw. bezeichnen ausschließlich diesen Snapshot.
Sie ersetzen keine echten Tracking-IDs. Aktualität, kontinuierliches Tracking
und geometrische Maskenform sind durch den Posevergleich nicht nachgewiesen.
Zehn fokussierte Offline-Tests bestehen: bekannte Koordinaten, Paarung bei
anderer Reihenfolge, ungültige Zeilen, Sichtbarkeit, Pose-/Skalenabweichungen,
axiale Symmetrie und Abbruch ohne Erzeugung bei Fehlzuordnung. Hinzu kommen
die fünf tatsächlich gemeldeten Posen, exakte Übernahme der Masken-Sources
bei unveränderten Targets, kombinierter Rotations-/Translationsversatz,
ungültige Pixelbudgets und Preflight mit tatsächlichem Renderer-Raster.
Python-3.9-Syntax ist geprüft. Johannes hat den erneuten Aufbau erfolgreich
ausgeführt: `pose_alignment_passed: true`, keine Probleme, Snapshot bei
2000 × 2000, exakt übernommene Masken-Sources und unveränderte Legacy-Targets.
Maximaler konservativer Randversatz zur alten Source-Liste: 0,049122 cm,
Zuordnungsbudget 0,25 cm. Keine alten Knoten oder Routing geändert, nichts
gespeichert. Die Maskenform bleibt separat zu prüfen.

```python
p = '/Users/Johannes/dev/Promotion_Prototypen/AISI/td_builders/build_motion_aligned_snapshot.py'; exec(compile(open(p, encoding='utf-8').read(), p, 'exec'))
```

### Pixelprobe und statischer Routing-Anschluss — in TD bestanden

`check_motion_aligned_routing.py` prüft zuerst, ob der Snapshot noch zu den
aktuellen Maskenposen gehört. Eine temporäre GLSL-Probe verwendet die Kontur-
und Koordinatenfunktionen aus dem eingebetteten Motion-Shader, rendert aber
alle gültigen Source-Flächen weiß, unabhängig von Reveal, Navigation und
Abschluss. Eine temporäre Kopie der bestehenden Masken-Komposition
multipliziert diese Fläche mit der unveränderten Maske. Ein temporärer Select
TOP im Snapshot-Netzwerk liest die externe Maskenquelle per absolutem Pfad;
beide Composite-Eingänge bleiben dadurch im selben Netzwerk. Alle Probe-Knoten
liegen unter dem neuen Snapshot-COMP und werden anschließend entfernt.

Der Bericht misst den erhaltenen Anteil der nominalen Tisch-Innenfläche,
Maskenfläche außerhalb der nominalen Kontur und helles RGB außerhalb der
bestehenden Maske. Der erhaltene Anteil wird ausdrücklich berichtet, nicht
als geometrische oder physische Freigabe interpretiert. Ein absichtlicher
Masken-Inset kann Beschneidung ergeben. Leere oder unterschiedliche Raster,
fehlender Durchlass und RGB-Leckage führen zum Abbruch.

Bei bestandener technischer Prüfung werden nur `floor_motion` und
`tabletop_motion` (Select TOP) im isolierten Routing-COMP auf die Snapshot-
Ausgänge gestellt und dessen lokaler Schalter aktiviert. Andere lokale
Quelländerungen werden nicht überschrieben. Vorherige Werte werden im eigenen
COMP hinterlegt und bei Fehlern sofort wiederhergestellt. Produktions-
Selects, Projektoren, Masken und Simulation werden nicht verändert, nichts
gespeichert. Die Modussperre gilt weiter; AISI muss bereits aktiv sein.

Elf fokussierte Offline-Tests bestehen: Durchlass, Formbeschnitt, RGB-
Leckage, ungültige Raster, Shader-Ableitung und lokaler Rollback sowie
nebenwirkungsfreier Import beider Helfer bei vorhandenem TD-`op` und
weiterhin funktionierender Textport-Start, lokaler Select statt
netzwerkübergreifendem TOP-Kabel sowie Verbindungsprüfung vor dem Cook. Der
abgeleitete Shader kompiliert und linkt auf dem macOS Apple Software Renderer.
Die Offline-Kompilation ersetzt keine TD- oder Raumabnahme; der folgende
Absatz dokumentiert den späteren TD-Nachweis. Die visuelle Prüfung steht aus.

Der erste TD-Aufruf scheiterte noch vor der Pixelprobe mit „project1 fehlt
oder Snapshot existiert“. Ursache war ein versehentlicher zweiter Builder-
Aufruf beim Import von `build_motion_aligned_snapshot`: Der ursprüngliche
Einstieg prüfte lediglich, ob TD-`op` verfügbar war. Die Einstiegspunkte
beider Helfer prüfen nun zusätzlich, dass kein regulärer Python-Importspec
vorliegt. Ein Import definiert damit ausschließlich Funktionen, während
der manuelle Textport-`exec` den jeweiligen Einstieg weiter ausführt.
Keine Prüfung wurde ausgeführt, kein vorhandener Snapshot geändert;
lokales Routing wurde wiederhergestellt, keine Probe blieb zurück.
Wiederholung nur des Checkers mit dem vorhandenen Snapshot steht aus.

Johannes' folgende Nachricht enthält zunächst nochmals den Importfehler und
danach einen weiterlaufenden Versuch: Beide Poseprüfungen sind bestanden,
doch `alignment_probe_masked` meldet „Not enough sources specified“.
Ursache im Checker war der direkte Anschluss von `mask_existing` aus dem
Routing-COMP an die Probe im Snapshot-COMP. Dieser Anschluss ist jetzt durch
den oben beschriebenen lokalen Select TOP ersetzt; vor dem Cook wird die
vollständige Input-Liste geprüft. Zwei neue Regressionstests bilden die
Netzwerkgrenze und einen fehlgeschlagenen Anschluss ab. Die Probe-Knoten
wurden nach dem Fehler entfernt und das lokale Routing wiederhergestellt;
keine produktiven Ausgaben geändert. Die anschließende Wiederholung ist
inzwischen bestanden:

- `passed: true`, alle sieben aufgeführten Prüfungen bestanden;
- Raster 2000 × 2000, 1.010.626 nominale Innenpixel geprüft;
- `interior_retained_fraction: 1.0`: alle geprüften Innenpixel bleiben über
  der Helligkeitsschwelle, keine Aussage über identische Kanten-Antialiasingwerte;
- `lit_pixels_outside_mask: 0`;
- 2024 Maskenpixel außerhalb der nominalen Kontur und 1.018.806 helle Pixel
  in der maskierten Probe; Rand-/Formursachen nicht separat aufgelöst;
- lokale Snapshot-Vorschau aktiviert, temporäre Proben entfernt;
- keine produktiven Ausgaben geändert, nichts gespeichert, keine Raumprüfung.

Nur im isolierten Routing-COMP verweisen `floor_motion` und `tabletop_motion`
jetzt auf den statischen Snapshot. Johannes hat beide Ausgänge
`out_floor` und `out_tabletop` (jeweils Out TOP) im Operator-Viewer gezeigt.
Die Screenshot-Prüfung ergibt eine plausible statische Darstellung: Floor-
Zielreste außerhalb der Source-Flächen, am Tabletop vier grüne Kontaktanzeigen
und unten ein Navigationskreis ohne Grün. Die geraden weißen Schnittkanten
entsprechen der geometrischen Source-/Target-Überlappung. Der Pfeil ist eine
Aussparung im weißen Kreis und erscheint daher auf grünem Untergrund grün,
auf unbeleuchtetem Untergrund schwarz. Keine neue technische Abweichung ist
anhand dieser Bilder erkennbar; daraus keine Labor-/Projektionsfreigabe
oder Freigabe aller Bewegungsfälle ableiten. Die Probe enthält eingefrorene Posen;
Änderungen im separaten Room Editor bewegen diesen Snapshot nicht.
Zum Zurückschalten des lokalen Prüfzweigs genügt
`op('/project1/comp_aisi_motion_routing_preview').par.Enablemotion = False`.
Die bestehenden Produktionsausgaben wurden auch beim Aktivieren nicht umgestellt.

Der lokale statische Maskendurchlass ist damit technisch und anhand der beiden
Screenshots geprüft. Die spätere Beanstandung von Johannes begrenzt diese
Aussage ausdrücklich: Grünes Wachstum und Zentrierung sind durch diese
statischen Bilder nicht nachgewiesen. Es wurde weiterhin keine `.toe` gespeichert. Den
aktuellen Stand manuell über „Save As“ als neue benannte Arbeitskopie sichern,
beispielsweise `AISI_motion_v1_5_preview_validated.toe`; keine vorhandene
Datei überschreiben. Dieser Hinweis ist keine Behauptung einer erfolgten
Speicherung. Die unten beschriebene dynamische maskierte Prüfung wurde
anschließend bestätigt. Als Nächstes echte Trackingdaten, explizite
Layoutaktivierung und stabile Source-/Target-Identität anbinden; produktiven
Anschluss, Moduserhalt und Raumabnahme separat prüfen.

### Korrektur der statischen Sichtbewertung und dynamischer Maskentest

Johannes beanstandet vier identische grüne Anfangsformen und fehlende
Zentrierung beim nahen Tisch. Ursache des Prüfaufbaus: Der eingefrorene
Snapshot initialisiert jede Kontakt-Baseline mit dem bereits aktuellen
Fortschritt. Damit ist `A = (P − P0)/(1 − P0) = 0` für alle erstmals
eingelesenen Kontaktposen. Die identischen Formen sind kein Beleg einer
korrekten Fortschrittsanzeige. Die vorige optische Plausibilitätsbewertung
war insoweit zu weitgehend; ihre Masken-/Pixelnachweise bleiben gültig.
Keine Annäherungsgeschichte erfinden und keine Baseline aus der bloßen
aktuellen Zieldistanz rückrechnen.

`build_motion_dynamic_mask_preview.py` erzeugt deshalb ausschließlich einen
neuen `comp_aisi_motion_dynamic_mask_preview` (Container COMP). Content
und Maskenkopien lesen denselben fortlaufenden Float-State der ursprünglichen
Room-Editor-Komponente `comp_aisi_motion_v1_5`. Fünf Kopien der vorhandenen
Maskengeometrie behalten ihre Select-SOP-Fläche; relative Quellen werden vor
dem Kopieren absolut aufgelöst. Nur die Transformationen der Kopien folgen
dem State. `motion_sim_mask.py` bildet die inverse bestehende `td_pose`-
Schnittstelle ab; ungültige, entfernte oder veraltete Source-Zeilen blenden
die Maskenkopie aus. Auch abgeschlossene/inaktive gültige Tische behalten
ihre räumliche Maske für die globale Welle.

Maskenrenderer, Reorder und Multiply werden in denselben neuen COMP kopiert.
Kamera/Lichter/Materialien werden auf die Originalreferenzen aufgelöst;
alle Kabel bleiben lokal. Der Floor-Ausgang zeigt ausschließlich den
Motion-Simulationscontent, ohne die alten, anders positionierten Chairs.
Der alte Chair-Zweig bleibt erhalten. Die vorhandene statische Probe und
das alte Routing werden nicht umgestellt. Originalmasken, Kalibrierung,
Study-/Tracking-Pfade und Produktionsoutputs werden nicht verändert.

Sechs fokussierte Offline-Tests bestehen: inverse Poseabbildung, fortlaufende
Transformation auch nach Abschluss, Ausblenden bei ungültigen/stalen Daten,
absolut aufgelöste OP-Referenzen, unabhängige Tischfortschritte und der
reproduzierte Unterschied zwischen statischer Endpose (`A = 0`) und echter
Annäherung zur selben Pose (`A > 0,9`). Die Motion-Zustandsformel und der
Shader wurden nicht geändert. Python-3.9-Syntax ist geprüft. Johannes hat
Aufbau und sichtbaren Bewegungsablauf anschließend erfolgreich ausgeführt
und bestätigt ausdrücklich „jetzt ist es richtig“. Der Screenshot zeigt
unabhängigen Fortschritt: Rechts unten hat sich das Grün groß und annähernd
zentriert ausgedehnt, der Navigationskreis ist klein; die anderen aktiven
Tische behalten ihre eigene Anfangsform.

Die TD-Ausgabe bestätigt fünf frische Tisch-IDs `table_0` bis `table_4`,
keine Änderungen an Originalknoten/Produktionsoutputs und keine Speicherung.
Maskenrenderer, Reorder, Multiply und Tabletop-Out kochen fehlerfrei bei
2000 × 2000, Floor-Out bei 1000 × 1000. Aufgelöste gemeinsame Maskenfläche:
`/project1/comp_study_visualization/rect_tabletop_inner_geo/table_surface`.
Damit ist das dynamische maskierte Feedback in Simulation sichtbar bestätigt.
Reale Tracking-Aktualität, Projektionsleistung und Raumkorrektheit sind nicht
nachgewiesen. Die frühere statische Pixelprüfung und diese dynamische
Bestätigung bleiben getrennte Nachweise.

```python
p = '/Users/Johannes/dev/Promotion_Prototypen/AISI/td_builders/build_motion_dynamic_mask_preview.py'; exec(compile(open(p, encoding='utf-8').read(), p, 'exec'))
op('/project1/comp_aisi_motion_dynamic_mask_preview/out_tabletop').openViewer(unique=True)
```

Prüffolge im bestehenden Fünftisch-Room-Editor: mit `R` auf Ausgangsposen
zurücksetzen und einmal „Vorschlag aktivieren“. `table_4` unten rechts von
seinem Ziel nach rechts wegziehen, bis kein Kontakt mehr besteht. Danach
langsam zum Ziel zurückführen: ab Kontakt zunächst Anfangsform, bei weiterer
Annäherung größer und zunehmend um den Navigationskreis zentriert; dieser
wird kleiner. Ein anderer Tisch muss seinen eigenen Fortschritt behalten.
Während der Annäherung nicht erneut den Vorschlag aktivieren.

### Neuer Auftrag: produktive Umschaltung vor dem Laboranschluss

Johannes beauftragt ausdrücklich die Einbindung in die produktive
Ausgabekette bereits jetzt, bei Erhalt der bestehenden Maskierung und
Kalibrierung. Dies zieht die technische Umschaltung vor den noch offenen
echten Trackinganschluss; eine aktive reale Projektion wird damit nicht
als geprüft freigegeben. Die neue Umschaltung soll zunächst deaktiviert
bleiben und den bisherigen Content durchlassen.

Bevor produktive Verbindungen geändert werden, liest der erweiterte
`inspect_motion_routing.py` zusätzlich die Floor-Chair-Auswahl,
deren Basis-Select und das unmaskierte Tabletop aus. Die angestrebten
Einfügepunkte liegen vor der unveränderten Tabletop-Multiply-Maske und
vor der bestehenden Chair-Komposition. Die konkrete Verdrahtung wird
am aktuellen laufenden Graph geprüft, nicht aus älteren Buildern abgeleitet.
Die anschließende Installation und ihr Prüfer sind unten dokumentiert;
die aktive neue Quelle ist dabei weiterhin ausgeschaltet.

```python
p = '/Users/Johannes/dev/Promotion_Prototypen/AISI/td_builders/inspect_motion_routing.py'; exec(compile(open(p, encoding='utf-8').read(), p, 'exec'))
```

#### Produktive Einbindung installiert und Bypass geprüft

Johannes' aktueller Graph bestätigt:

- `select_floor_for_synth_chairs` (Select TOP) liest bislang
  `/project1/comp_output/select_floor`; sein Bild geht sowohl direkt in die
  Chair-Umschaltung als auch in die additive Chair-Komposition.
- `null_tabletop` (Null TOP) liest `render_tabletop` (Render TOP). Erst danach
  multipliziert `mask_tabletop` (Composite TOP) mit `null_table_mask` (Null TOP).
- Die Floor-/Tabletop-/Masken-Ausgabeschalter und ihre Kalibrierungszweige
  folgen unverändert hinter diesen Pfaden.

`build_motion_output_routing.py` erstellt
`/project1/comp_aisi_motion_output_routing` mit zwei lokalen Content-Schaltern
und einer neuen Select-TOP-Brücke im Layout. Genau zwei bestehende Stellen
werden geändert: Der Floor-Basis-Select liest den neuen Floor-Ausgang, und
`null_tabletop` liest über die lokale Brücke den neuen Tabletop-Ausgang.
Die Legacy-Eingänge des neuen Routers lesen die zuvor verwendeten Produzenten,
nicht ihre neu angeschlossenen Verbraucher; dadurch entsteht kein Rückkopplungspfad.
Die ursprüngliche Tabletop-Maske mit beiden Eingängen/Reihenfolge bleibt
vollständig erhalten. Es wird keine Ersatzmaske/-Chair-Komposition eingeführt.

`Enablemotion` und `Sourceapproved` starten beide ausgeschaltet. Motion wird
nur bei beiden Schaltern an, AISI-Modus (`study/mode == 2`) und beiden
Kalibrierungspanels aus ausgewählt. Ein unbekannter/fehlender Modus bleibt
auf Legacy. `Sourceapproved` ist eine manuelle Konfiguration für den späteren
nachgewiesenen Quellen-/Maskenabgleich, kein automatischer Trackingnachweis.
Die Simulationsquelle ist durch die Installation ausdrücklich nicht freigegeben.
Beide neuen Motion-Eingänge werden vor dem vorhandenen Masken-/Projektorpfad
auf die jeweilige Legacy-Auflösung gebracht. Die Ausdrücke der Umschaltung
haben eine explizite Frame-Abhängigkeit.

Der Builder prüft den vorgefundenen Graph, erstellt einen Snapshot aller
vorhandenen Parameter-/Eingangsverbindungen unter Layout, Output und Study-
Visualisierung und erlaubt danach ausschließlich die beiden genannten
Content-Änderungen. Text-DAT-Code wird zusätzlich per Hash verglichen.
Bei ausgeschaltetem Motion müssen Floor-, Tabletop- und Masken-Ausgabebild
vor/nach Einbau pixelgleich sein. Fehler führen zum Rückbau; bei Fehlern
während des Rückbaus werden die neuen Knoten zur Wiederherstellung erhalten
und der unvollständige Rückbau ausdrücklich gemeldet. Nichts wird gespeichert.

Zehn Offline-Tests bestehen: Einbau mit Bypass/Maskenerhalt, alle relevanten
Flag-/Modus-/Kalibrierungskombinationen, Rückbau, Fehler nach Neuverdrahtung,
abweichende Ausgangsgraphen, wiederholter Einbau, Erhalt späterer lokaler
Änderungen und Python-3.9-Syntax. Modelltests ersetzen keine TD-Pixelprüfung.
Johannes hat Installation und Prüfer im laufenden TD anschließend bestanden:
`installed: true`, drei pixelgleiche Ausgabebilder beim Einbau, geschützter
Graph verifiziert. Nur `select_floor_for_synth_chairs` und `null_tabletop`
wurden an den vorgesehenen Content-Stellen umverbunden. Originalmaske,
Chair-Komposition, Kalibrierung und Projektortransforms bleiben erhalten.
Der separate Prüfer besteht mit allen sieben Kriterien: zwei strukturelle
Nachweise, je Oberfläche Pixelgleichheit und Originalauflösung sowie
fehlerfreie zentrale Ausgabeschalter. Motion und Quellenfreigabe bleiben
aus, `active_motion_output_tested: false`, nichts gespeichert und keine
physische Validierung. Die technische Einbindung ist damit installiert;
ein aktiver neuer Projektionsinhalt ist daraus nicht als geprüft abzuleiten.

```python
p = '/Users/Johannes/dev/Promotion_Prototypen/AISI/td_builders/build_motion_output_routing.py'; exec(compile(open(p, encoding='utf-8').read(), p, 'exec'))
p = '/Users/Johannes/dev/Promotion_Prototypen/AISI/td_builders/check_motion_output_routing.py'; exec(compile(open(p, encoding='utf-8').read(), p, 'exec'))
```

Nur für einen ausdrücklich gewünschten Rückbau der neuen Einbindung:

```python
p = '/Users/Johannes/dev/Promotion_Prototypen/AISI/td_builders/remove_motion_output_routing.py'; exec(compile(open(p, encoding='utf-8').read(), p, 'exec'))
```

Der Prüfer aktiviert den neuen Content nicht. Er prüft den installierten
Bypass, unveränderte Originalknoten, Auflösungen und fehlerfreie zentrale
Ausgabeschalter. Spätere lokale Änderungen an neuen Routing-Knoten werden
vor Prüfung/Rückbau erkannt und nicht überschrieben. Eine aktive Ausgabe
der neuen Quelle, tatsächliche Modus-Bildvergleiche und Raumabnahme bleiben
separate Nachweise. Die `.toe`-Speicherung bleibt manuell.

#### Simulationstest durch die produktive Kette vorbereitet

Johannes möchte den neuen Content mit der Room-Editor-Simulation in der
produktiven Kette aktiv testen. Dafür müssen Tisch-Content und Maskenbild
dieselben simulierten Posen verwenden; die bisherigen gecachten Vision-Posen
sind hierfür ungeeignet. `motion_output_simulation_test.py` implementiert
einen temporären, getrennten `Simulationtest`-Schalter im installierten Router.
Die vorhandenen `Enablemotion`-/`Sourceapproved`-Freigaben bleiben aus.

Der Testschalter aktiviert gleichzeitig beide Motion-Content-Zweige und
eine neue Auswahl vor `null_table_mask` (Null TOP). Deren Legacy-Eingang
bleibt der bisherige `reorder_table_mask` (Reorder TOP); der Testeingang liest
`comp_aisi_motion_dynamic_mask_preview/reorder_simulation_mask` (Reorder TOP)
mit den bereits geprüften expliziten Frame-Bindungen an denselben Motion-State.
Es ändert sich vorübergehend nur der Bild-Eingang von `null_table_mask`.
Der originale Multiply-Maskenoperator, die Maskengeometrie/-parameter,
Floor-/Tabletop-Maskenreihenfolge und alle Kalibrierungs-/Projektorparameter
bleiben erhalten. Auch `select_table_mask` (Select TOP) erhält so das passende
Simulationsmaskenbild über seinen unveränderten bisherigen Quellpfad.
Die Chair-Komposition verwendet weiterhin ihre bisherige Datenquelle;
deren Zuordnung zu simulierten Tischen ist kein Nachweis dieses Tests.

Nur AISI und beide Kalibrierungspanels aus erlauben den Simulationstest.
Tracking, Study, Kalibrierung und unbekannte Modi bleiben auf Legacy-Content
und ursprünglichem Maskenbild. Die separate Quellenfreigabe für echtes
Tracking wird nicht gesetzt. Die Vorbereitung bleibt ausgeschaltet und
verlangt unverändertes Routing und korrekte Simulationsmasken-Bindungen.
Aktivierung folgt separat bei frischen, seit der Vorbereitung fortgeschrittenen
OSC-Frames; die blockierenden GPU-Abfragen gehören nicht in diesen Schritt.

Vor Aktivierung müssen die drei zentralen Ausgabebilder beim vorbereiteten,
noch ausgeschalteten Test pixelgleich bleiben. Danach werden unveränderte
Originalparameter/-verbindungen außerhalb der einen erlaubten zusätzlichen
Maskenbild-Verbindung, gemeinsame Content-/Maskenauswahl, fehlerfreie zentrale
Ausgaben sowie die aktive Maske geprüft. Das Tabletop-Bild durch die echte
Originalmaske wird gegen den geprüften dynamischen isolierten Prüfzweig
verglichen (maximal zwei RGBA8-Rundungsstufen Differenz). Beim Startfehler
wird der Test zurückgebaut; ein unvollständiger Rückbau wird ausdrücklich
gemeldet. Keine automatische Speicherung.

25 fokussierte Tests bestanden: zehn bestehende Produktionsrouting-Tests
und 15 Simulationstests einschließlich aktiver Pixelpfade, Schutz der
anderen Modi, veralteter Quelle, unveränderter Frame-Bindung, Rückbau nach
Pixelabweichung, vollständiger Wiederherstellung und Erhalt lokaler Änderungen.
Python-3.9-Syntax aller Testskripte geprüft. Aktivierung, Vergleich und
sichtbare Bewegung im laufenden TD sind noch auszuführen; kein Raumtest.

Vorbereitung, danach Aktivierung als neue Textport-Eingabe, separate
Pixelprüfung und Beenden:

```python
p = '/Users/Johannes/dev/Promotion_Prototypen/AISI/td_builders/start_motion_output_simulation_test.py'; exec(compile(open(p, encoding='utf-8').read(), p, 'exec'))
```

```python
p = '/Users/Johannes/dev/Promotion_Prototypen/AISI/td_builders/activate_motion_output_simulation_test.py'; exec(compile(open(p, encoding='utf-8').read(), p, 'exec'))
```

```python
p = '/Users/Johannes/dev/Promotion_Prototypen/AISI/td_builders/check_motion_output_simulation_test.py'; exec(compile(open(p, encoding='utf-8').read(), p, 'exec'))
```

```python
p = '/Users/Johannes/dev/Promotion_Prototypen/AISI/td_builders/stop_motion_output_simulation_test.py'; exec(compile(open(p, encoding='utf-8').read(), p, 'exec'))
```

Viewer sind jetzt `comp_output/switch_floor` und `comp_output/switch_tabletop`
(jeweils Switch TOP), also die vorhandenen produktiven zentralen Ausgaben.
Im Room Editor einmal Vorschlag aktivieren und danach Bewegung, Kontakt,
Mittelpunktdurchgang und unabhängigen Abschluss prüfen. Der Stop entfernt
nur die temporären Testknoten/-parameter, stellt den ursprünglichen
Maskenbild-Eingang und die zwei ursprünglichen Router-Ausdrücke wieder her
und führt den bisherigen deaktivierten Routing-Prüfer erneut aus. Der Test
ist vor Sicherung einer normalen Arbeitskopie zu beenden. Während des Tests
den eigenen Simulationsprüfer verwenden; der normale Router-Prüfer erkennt
die temporäre Erweiterung absichtlich als abweichenden lokalen Graph.

##### Erster Aktivierungsversuch ohne frische Simulationsframes

Johannes' erster Start bricht vor dem Erstellen/Umschalten der Testknoten
an `fresh == false` ab. Die anschließende Stop-Meldung „Kein registrierter
Simulationstest“ bestätigt, dass keine Testsitzung vorlag. Der Screenshot
von `comp_output/switch_floor` (Switch TOP) zeigt weiterhin die bisherige
Darstellung. Die zuvor bestandene produktive Installation/Bypass-Prüfung
bleibt erhalten; keine neue Aktivierungs- oder Raumabnahme ableiten.

Die Ursache ist damit noch nicht auf gestoppten/pausierten Sender oder
ausstehende Bestätigung fortschreitender Frames eingegrenzt.
`check_motion_simulation_source.py` liest den Zustand vor/nach einem Cook
des eigenen State-TOP, OSC-Empfängerparameter, rohe Session-/Frame-Metadaten
und den gespeicherten eigenen Sender-Prozesshandle aus. Er verändert keine
Produktionsverbindung oder Parameter und startet keinen Sender.

```python
op('/project1/comp_aisi_motion_v1_5/render_preview').openViewer(unique=True)
p = '/Users/Johannes/dev/Promotion_Prototypen/AISI/td_builders/check_motion_simulation_source.py'; exec(compile(open(p, encoding='utf-8').read(), p, 'exec'))
```

Der offene isolierte Viewer hält die zeitabhängige Quelle auch bei noch
deaktiviertem produktivem Routing im regulären Cook-Pfad. Erst die folgenden
Live-Metadaten belegen, ob tatsächlich neue Frames ankommen. Der Start gibt
bei fehlender Frische jetzt einen klaren Status inklusive Stream-Diagnose aus;
Stop ohne Sitzung prüft den unveränderten deaktivierten Router und meldet
„nichts geändert“. Die Textport-Wrapper laden das eigene Testmodul erneut,
damit Korrekturen im bereits laufenden TD wirksam werden. Der Launcher ist
beim normalen Modulimport nun ohne Start-Nebeneffekt, damit explizite
Fünftisch-Aufrufe nicht vorher versehentlich drei Tische starten.
21 fokussierte Routing-/Simulationstests und vier Launcher-Tests bestanden.
Die nach Öffnen des isolierten Previews direkt aufgerufene Diagnose
bestätigt anschließend frische Daten bereits vor und nach ihrem Cook:
Session 2548711, Frame 259368 → 259485, Revision 7, fünf IDs. Der Empfänger
ist aktiv auf Port 9000, eigener Sender PID 91706 läuft mit fünf Tischen.
Damit ist aktuell kein Senderneustart nötig. Die Ursache der anfänglichen
fehlenden Frische ist nicht abschließend isoliert. Aktive Umschaltung und
Bewegung durch die produktive Kette stehen noch aus; der direkte Modulaufruf
mit Reload umgeht die zuvor ohne Ausgabe gebliebene Textport-Startbedingung.

##### Korrektur des Startablaufs nach erneutem Timeout

Der nächste direkte Start meldet trotz zuvor nachgewiesen frischer Quelle
erneut `waiting for advancing frame / timeout` bei Frame 262645. Die
kombinierte Funktion führte umfangreiche GPU-Readbacks aus und kochte danach
den State im selben blockierten TD-Frame erneut. Ein gecachter OSC-CHOP-Wert
kann dadurch das 0,5-s-Zeitlimit überschreiten, obwohl der Sender läuft.
Diese Ursache folgt aus Ablauf und Symptomen; ein natives TD-Profilergebnis
liegt nicht vor.

`start` bereitet nun ausschließlich den deaktivierten Zweig samt drei
Bypass-Pixelprüfungen vor. Die registrierte Sitzung erhält Phase `prepared`,
TD-Framenummer und letzte Quellsignatur. `activate` muss in einem späteren
TD-Frame aufgerufen werden; es kocht zuerst den bestehenden OSC-In und Raw-
CHOP, dann den eigenen State. Es verlangt unverändert den 0,5-s-Frischetest
und eine neue Signatur. Nur dann werden Content und Simulationsmaske gemeinsam
aktiviert. Dieser leichte Schritt führt keine GPU-Digests/-Readbacks aus.
Die schwere aktive Pixelprüfung erfolgt separat über den Prüfer; bei einer
Pixelabweichung wird die unverändert registrierte Testsitzung zurückgebaut.
Zwischenzeitliche lokale Änderungen werden dabei weiter geschützt.

25 Routing-/Simulationstests bestanden, darunter neue Fälle für
Vorbereitung/Aktivierung in unterschiedlichen Frames, unveränderte
Quellsignatur trotz TD-Framefortschritt, keine GPU-Abfrage während Aktivierung
und Reihenfolge OSC-In → Raw-CHOP → State. Python-3.9-Syntax geprüft.
Die Textport-Wrapper erlauben den expliziten `p`-/`exec`-Aufruf auch bei
geerbtem `__spec__`, ohne beim normalen Modulimport automatisch zu laufen.
Die zweiphasige Aktivierung ist im laufenden TD erfolgreich ausgeführt:
Vorbereitung in Frame 1378043 mit drei Bypass-Pixelprüfungen, Aktivierung in
Frame 1379345 mit frischer Signatur (2548711, 279512), Revision 7 und fünf
Tisch-IDs. Floor-/Tabletop-Content und Simulationsmaske stehen jeweils auf
Index 1. Johannes bestätigt sichtbaren neuen Content. Die temporäre
Testsitzung ist derzeit aktiv; die reale Quelle ist weiterhin nicht
freigegeben. Die separate Prüfung über `output_test.verify(op)` hat alle
sechs Kriterien bestanden: Originalmaskenoperator erhalten, Kalibrierung,
Chair-Komposition und Projektorparameter unverändert, gemeinsame Modussteuerung,
drei zentrale Ausgabeschalter fehlerfrei, aktiver Maskeneingang pixelgleich
zur dynamischen Simulationsmaske sowie Tabletop durch die Originalmaske
pixelgleich zum dynamischen Prüfzweig (maximaler Pixelfehler 0,0).
Kontinuierliche Bewegung, Feedback und unabhängige Abschlüsse durch die
produktiven Ausgänge bleiben manuell zu bestätigen. Nichts gespeichert,
keine physische Validierung.

### Abschlussprüfung nach den visuellen Korrekturen

Nach Johannes' Freigabe des runden Grüns wird die deterministische
TD-Abnahme erweitert: Die bisherigen 22 Kriterien bleiben erhalten,
drei neue Formprüfungen bringen die Gesamtzahl auf 25. Am Ende der
Zustandsprüfungen verwendet ausschließlich die temporäre Prüfkomponente
einen Probe-Einstieg zur tatsächlichen GLSL-Funktion `feedbackHalo`, ohne
Tischbeschnitt. Geprüft werden Symmetrie/Zentrierung, Richtungsunabhängigkeit
beim Mittelpunktdurchgang und Stetigkeit am 8-cm-Übergang. Das ersetzt weder
die bestätigte dynamische Masken-Bewegungsprobe noch eine Raumabnahme.
Die Hauptkomponente und ihre Kontakthistorie werden nicht verändert.

77 fokussierte Offline-Tests bestanden; vier optionale native GPU-Tests
werden ohne konfigurierten Runner übersprungen und sind für die neue
Kreisform bereits separat bestanden. Syntax der erweiterten TD-Abnahme
auf Python 3.9 geprüft. Johannes hat die erweiterte Abnahme anschließend
im laufenden TD ausgeführt: `passed: true`, alle 25 Kriterien bestanden,
temporäre Prüfkomponente entfernt, nichts gespeichert. `physical_validation`
bleibt ausdrücklich `not performed`. Damit ist der Simulationsstand nach
beiden visuellen Korrekturen technisch und durch die zuvor bestätigten
Bewegungsproben geprüft. Echter Trackinganschluss, produktive Integration,
Study-/Tracking-Bildvergleiche und physische Raumabnahme stehen weiter aus.

```python
p = '/Users/Johannes/dev/Promotion_Prototypen/AISI/td_builders/check_motion_acceptance.py'; exec(compile(open(p, encoding='utf-8').read(), p, 'exec'))
```

### Vorbereitung des echten Trackinganschlusses

Die aktuelle Repository-Kette ist
`vision_live_to_aisi_scene.py` → eigene `vision_live_scene.json` →
`sim_scene_to_osc.py` → vorhandener TD-Empfänger. Der Vision-Adapter führt
stabile Track-IDs sowie `vision_live.frame_id` und `timestamp_iso` in der
Szenendatei. `send_tables` sendet hingegen Source-/Target-Daten nach Index;
die Track-ID wird dort nur für Debugtexte verwendet. `send_live_rect_tables`
liefert die separate indexbasierte Vision-Maskenquelle. Die bisher in TD
ausgelesenen Werte enthalten keine hinreichenden Frame-/Identitätsnachweise
für den Motion-Anschluss. Außerdem werden Targets im bestehenden Sender
wiederholt aus der aktuellen Szene berechnet; dies ersetzt keine explizite
Layoutaktivierung mit eingefrorenen Zielen.

Der spätere Live-Adapter muss deshalb die echte Track-ID-/Index-Zuordnung,
aktuelle Kamera-Frames und explizite Layoutaktivierung gemeinsam erhalten.
Ein laufender OSC-Sendetakt allein darf keine eingefrorene Kameraquelle
als frisch bestätigen. Die tatsächlichen gerenderten Maskenposen bleiben
die Grenze für den TD-Koordinatenabgleich. Kein Umbau der bestehenden
OSC-/Study-Kanäle, keine produktive Umschaltung und kein echter Live-Test
aus dieser Codeinspektion ableiten. Auf diesem Mac fehlt die echte Quelle.

### Live-Zustandskern und rein lesende Kameraprobe

`src/aisi/app/motion_live_adapter.py` implementiert den noch nicht
angeschlossenen `MotionLiveAdapter`. Er liest direkt kalibrierte FrameEvents
über dieselbe kanonische Posekonvertierung wie die bestehende Vision-Brücke.
Die Brücke hält fehlende Tische bis zu 15 Frames vor; dieser Cache wird für
Motion ausdrücklich nicht als Nachweis aktueller Tischsichtbarkeit verwendet.

Der Zustandskern verlangt zwei fortschreitende Frames. Wiederholtes Lesen
derselben Frame-ID verlängert das 0,5-s-Zeitlimit nicht. Zeitstempel benötigen
eine Zeitzone; alte/future Capture-Zeitstempel werden verworfen. Die bestehende
Vision-Uhr schreibt volle UTC-Sekunden: Die Capture-Altersprüfung berücksichtigt
eine zusätzliche Sekunde Quantisierung, während der monotone Empfangs-Timeout
weiter 0,5 s beträgt. Es handelt sich um eine Prüfung auf demselben Host;
abweichende Rechneruhren sind damit nicht automatisch synchronisiert.

Stabile Track-IDs halten Source und Target bei geänderter Reihenfolge
zusammen. Fehlende Tische werden sofort ungültig; neue IDs erben keine alten
Ziele. Nur `activate(revision, targets, active_ids, now)` übernimmt eine
vollständig geprüfte Zielmenge mit expliziten Aktivflags. Poseänderungen
erzeugen weder Ziele noch Layoutrevisionen. Neustart/Rücksprung der Kamera
oder Kalibrierungswechsel verlangen expliziten Stream-Reset und danach eine
neue Aktivierung. Reset setzt die bisherige Revision nicht zurück.

Die Ausgabe bleibt in AISI-Weltzentimetern/Grad, ohne zusätzliche Achsen- oder
Vorzeichenannahmen. Es gibt noch keine Verbindung zum laufenden TD, keinen
neuen Netzwerksender und keine produktive Umschaltung. Ein späterer Sender
muss das Frischeflag des Kameraadapters erhalten; ein eigener Sendetakt darf
keine eingefrorene Kamera als frisch ausgeben. Die tatsächliche TD-Masken-
und Slotzuordnung ist vor einer Verbindung im Labor abzugleichen.

16 neue Tests bestanden: wiederholte/alte Frames, UTC-Sekundenauflösung,
fehlende Kalibrierung, ID-Reihenfolge, fehlende/neue Tische, eingefrorene
Ziele, ungültige Aktivierungen, Kamera-/Kalibrierungswechsel, fehlerhafte
Posen/Counts sowie ein synthetischer Durchlauf über `frame_values` und
`MotionOSCReader` im bestehenden neuen Präfix. Außerdem bestanden zehn
bestehende Vision-Brückentests. Kein echter Kamera- oder Raumtest.

Die Modul-CLI überspringt vorhandene JSONL-Historie und beobachtet nur neu
angehängte Frames. Sie liest ausschließlich, sendet nichts und aktiviert
kein Layout. Im Repository-Terminal mit dem vorhandenen Python-Environment:

```sh
python -m aisi.app.motion_live_adapter --input data/vision/live/current_room_rect.jsonl --duration 2
```

`ready_for_mapping_check: true` besagt ausschließlich, dass am Ende aktuelle,
gültige, fortschreitende Frames vorliegen; `td_alignment_verified` bleibt
`false`. Die lokale Mac-Probe liefert erwartungsgemäß keine Quelle und keine
Freigabe. Der tatsächliche Labor-Startbefehl für Kamera/AISI/OSC ist noch zu
benennen, bevor dieser Zustandskern in die dort aktive Kette integriert wird.

### Neue visuelle Korrektur: rundes Grün nahe der Zielmitte

Johannes meldet nach der Bewegungsprüfung einen sichtbaren Umschlag der
grünen Form beim Überfahren der Zielmitte. Die ursprüngliche v1.5-Form in
`Scene.tsx` enthält auch bei hohem Fortschritt zeitabhängige Ellipsenachsen
und einen seitlichen Mittelpunktversatz. Außerdem hängt die Asymmetrie am
gemeinsamen Translations-/Rotationsfortschritt; nahe der Positionsmitte kann
bei verbleibendem Winkelfehler somit noch deutliche Richtungsform bestehen.
Dieser Abschnitt dokumentiert eine ausdrücklich von Johannes gewünschte
visuelle Weiterentwicklung der Referenz, keine Änderung der Erfolgskriterien.

`motion_design.frag` berechnet die Halodeckung nun in `feedbackHalo`.
Ein zusätzlicher Distanzfaktor `smoothstep(8,29,distance)` schwächt sämtliche
gerichteten Formanteile ab: Mittelpunktversatz, Ellipsenstreckung und
zeitabhängige Achsen-/Mittelpunktvariation. Innerhalb der bestehenden
8-cm-Positionstoleranz bleibt eine zentrierte Kreisform, auch wenn die
Rotation noch keinen Abschluss erlaubt. Ab 29 cm bleibt die bisherige
v1.5-Form unverändert; 29 cm entsprechen dem bestehenden vollen
Navigationsradius. Größe, Kontakt-/Fortschrittsgeschichte und Erfolgsschwellen
bleiben unverändert. Die Kreisform gilt vor dem Beschnitt durch die Maske;
die reale Tischfläche kann weiterhin Teile des Kreises abschneiden.

`update_motion_halo_shape.py` ersetzt im laufenden eigenen Shader nur den
bekannten Haloblock und ergänzt die neue Hilfsfunktion. Andere lokale
Shaderänderungen bleiben erhalten, abweichender Halocode führt zum Abbruch.
Bei Compile-Fehler wird der vorige Shader wiederhergestellt. Kein
Engine-/Kontakt-Reset, keine Änderung an Masken oder produktiven Ausgaben,
keine Speicherung. Johannes hat den Installer im laufenden TD ausgeführt:
Shader aktualisiert und kompiliert, kein Engine-Reset, keine Masken- oder
Produktionsänderung, nichts gespeichert. Den angefragten Mittelpunktdurchgang
bestätigt er anschließend mit „ja jetzt stimmt es“. Die visuelle Korrektur
im dynamischen Simulationsviewer ist damit abgenommen.

Verifikation: Acht fokussierte Tests in `test_motion_halo_shape.py` bestanden.
Vier native GPU-Prüfungen führen die tatsächliche GLSL-Halofunktion ohne
Tischbeschnitt aus: zentrierte Symmetrie und Richtungsunabhängigkeit bei
unterschiedlichem Fortschritt/Zeitpunkt, identische Form vor/nach dem
Mittelpunkt, stetiger Übergang an der Positionstoleranz und pixelgleiche
bisherige Form ab 29 cm. Symmetrie erlaubt eine RGBA8-Rundungsstufe.
Vier Installer-Prüfungen sichern Python-3.9-Syntax, Rollback bei
Compile-Fehler, Erhalt anderer lokaler Shaderänderungen und Abbruch bei
abweichendem Halocode. Der vollständige Content-Shader kompiliert/linkt
zusätzlich auf dem Apple Software Renderer. Keine TD- oder Laborabnahme
aus diesen Offline-Nachweisen ableiten.

```python
p = '/Users/Johannes/dev/Promotion_Prototypen/AISI/td_builders/update_motion_halo_shape.py'; exec(compile(open(p, encoding='utf-8').read(), p, 'exec'))
```

Sichtprüfung: Einen noch aktiven Tisch ausreichend verdreht lassen, damit
er nicht bereits beim Zentrieren abschließt. Langsam mehrfach durch die
Zielmitte schieben. Das Grün soll nahe der Mitte rund bleiben und beim
Überfahren nicht umschlagen; weiter außen soll die bisherige Richtungsform
zurückkehren. Johannes bestätigt diese Sichtprüfung; sie ist keine physische
Raumabnahme.

### Behobener Grenzfall: Navigation ohne Kontakt im dynamischen Maskenprüfzweig

Nach der Wachstumsbestätigung meldet Johannes: Beim Wegziehen eines Tisches
ohne Zielüberlappung verschwindet auch der Navigationskreis. Dieser muss bei
gültiger aktiver Guidance sichtbar bleiben. Die vorherige positive Abnahme
ist auf Wachstum/Zentrierung begrenzt, nicht auf alle Zustände des kopierten
Maskenpfads.

Ein gezielter Offline-GPU-Test des unveränderten Shaders mit Source
`(400,400,90°)`, Target `(250,350,90°)`, aktivem gültigem Tisch und beendetem
Reveal rendert den weißen Navigationskreis korrekt: 2336 Alpha-Pixel über
0,5 im 500 × 500 Testbild, GLSL kompiliert/linkt und GL-Status 0. Das grenzt
die Laufzeitursache noch nicht auf Aktivierungs-/Phasenstatus oder Maskierung
ein. Keine Formel oder geschützte Geometrie auf Verdacht ändern.

`inspect_motion_navigation.py` liest/kocht nur die eigenen Prüfoperatoren und
vergleicht Source-/Target-State, Aktivierungsflag, Navigation, Kontakt und
Phase sowie Pixelregionen um nicht überlappende Sources vor/nach der Maske.
Beide möglichen Array-Y-Konventionen werden separat berichtet. Die kopierten
Maskentransformationen und lokalen Select-SOP-Grenzen werden mit ausgegeben.
Keine Parameter-/Knotenänderungen, keine Speicherung. Python-3.9-Syntax ist
geprüft. Johannes' Abfrage erfasste bei allen Tischen noch Kontakt; bei
`table_4` Source `(297,857;371,429;90°)` zu Target `(250;350;90°)`,
Navigationsradiusfaktor 0,609 und Halo 0,391. Das ist noch kein Nachweis des
gemeldeten Zustands ohne Überlappung.

```python
p = '/Users/Johannes/dev/Promotion_Prototypen/AISI/td_builders/inspect_motion_navigation.py'; exec(compile(open(p, encoding='utf-8').read(), p, 'exec'))
```

`check_motion_navigation_isolation.py` prüft deshalb zwei deterministische
GPU-Zustände durch den vorhandenen kopierten Maskenpfad: nur Tisch-Slot 4
sichtbar, ohne Kontakt Source `(400,400,90°)` zu Target `(250,350,90°)` mit
vollem Navigationskreis; danach Kontakt Source `(270,350,90°)` mit kleinem
Kreis und fortgeschrittenem Grün. Diese expliziten Shader-Zustände sind
keine simulierte Bewegungshistorie. Der Test misst helle RGB-Flächen vor
und nach der Maske, auf die jeweilige Auflösung normiert. Er ersetzt kurz
ausschließlich die zwei lokalen Select-TOP-Quellen `motion_state` und
`motion_tabletop`, stellt sie im `finally` wieder her und entfernt seine
drei temporären Operatoren. Haupt-Engine, OSC-Sender, bestehende Geometrien
und produktive Ausgaben bleiben unverändert; keine Speicherung.
Fünf Offline-Tests bestanden: geometrisch eindeutige Kontaktzustände,
Auflösungsnormalisierung, ungültige Pixel, Wiederherstellung bei Fehler und
Python-3.9-Syntax. Johannes hat den Test anschließend im laufenden TD
bestanden: Ohne Kontakt 9327 helle Pixel bei 1000² vor der Maske und 37291
bei 2000² danach (normierter Flächenerhalt 99,954 %); mit Kontakt 47456
bzw. 189841 (100,009 %). Beide Proben bestanden. Lokale Eingänge
wiederhergestellt, temporäre Operatoren entfernt, Haupt-Engine nicht
zurückgesetzt, nichts gespeichert. Damit ist der Kreis im kontrollierten
Zustand auch durch den kopierten Maskenpfad nachgewiesen. Die konkrete
gemeldete Fehlerstellung im laufenden OSC-Betrieb bleibt noch offen;
aus diesem Test folgt keine Fehlerbehebung oder physische Raumabnahme.

Die folgende Live-Abfrage erfasste `table_4` tatsächlich ohne Kontakt:
Source `(423,571;365;90°)`, Target `(250;350;90°)`, gültig und aktiv,
Guidance, Navigationsradiusfaktor 1, Kontakt-Alpha 0. Der gespeicherte
Halo-Radius 0,630 ist bei Kontakt-Alpha 0 unsichtbar und kein Restkontakt.
Die Source-Maske folgt korrekt mit `tx=0,90257`, `ty=-0,598`, `rz=-90°`.
Am Source-Zentrum (NumPy-Y 0,27) liegen vor und nach der Maske helle Pixel:
Maximalwert jeweils 1, helle Fensterfläche 81,37 % bzw. 82,48 % bei
unterschiedlicher Auflösung. Stream frisch, alle drei TOPs fehlerfrei.
Damit wird der Navigationskreis zum Diagnosezeitpunkt auch im echten
OSC-Zustand ohne Kontakt gerendert. Die Abfrage erzwingt allerdings Cooks;
Johannes bestätigt anschließend, dass der Kreis erst durch diesen Befehl
sichtbar wurde. Damit ist ein Aktualisierungsproblem belegt; die genaue
Abhängigkeitsstelle lässt sich aus den erzwungenen Cooks allein nicht
isolieren.

Die kopierten Geo-Pose-Ausdrücke rufen bislang ein DAT-Modul auf, das den
State per `numpyArray()` liest. Diese indirekte GPU-Abfrage stellt keine
zuverlässige explizite Frame-Abhängigkeit der Geo-Parameter her. Der Builder
ergänzt deshalb `absTime.frame` als ausgewertete Abhängigkeit, ohne den
berechneten Transformationswert zu verändern. Keine Änderung an Footprint,
Koordinaten, Shader oder bestehender physischer Maske.

`update_motion_mask_dependencies.py` überträgt diese Korrektur auf den
bereits vorhandenen eigenen Prüfzweig: Vorabprüfung aller 20 Ausdrücke,
Abbruch bei abweichenden lokalen Bindungen, Rücksetzen bei Fehler,
wiederholbar ohne zusätzliche Änderungen. Kein Engine-Reset, keine neuen
Knoten, kein erzwungener Cook und keine Speicherung. Neun fokussierte
Offline-Tests bestehen, darunter Wertgleichheit mit explizitem Uhrzugriff,
Installation/Wiederholung und Erhalt abweichender lokaler Änderungen.
Python-3.9-Syntax separat geprüft. Johannes hat den Installer ausgeführt:
20 Ausdrücke aktualisiert, keine Original-/Produktionsänderung, kein
Engine-Reset, kein erzwungener Cook, nichts gespeichert. Anschließend
bestätigt er den angefragten Bewegungstest ohne Diagnosebefehl mit
„ja funktioniert“. Die Laufzeitkorrektur im dynamischen Simulationsviewer
ist damit bestätigt; keine Raumabnahme.

```python
p = '/Users/Johannes/dev/Promotion_Prototypen/AISI/td_builders/update_motion_mask_dependencies.py'; exec(compile(open(p, encoding='utf-8').read(), p, 'exec'))
```

Danach ausschließlich im offenen dynamischen Tabletop-Viewer prüfen:
`table_4` wiederholt aus dem Zielkontakt herausziehen und zurückführen,
ohne Diagnosebefehl oder Force-Cook. Der volle Kreis muss ohne Überlappung
mitwandern; bei erneuter Annäherung muss das grüne Feedback weiter korrekt
wachsen. Diese Prüffolge ist durch Johannes bestätigt.

```python
p = '/Users/Johannes/dev/Promotion_Prototypen/AISI/td_builders/check_motion_navigation_isolation.py'; exec(compile(open(p, encoding='utf-8').read(), p, 'exec'))
```

```python
p = '/Users/Johannes/dev/Promotion_Prototypen/AISI/td_builders/check_motion_aligned_routing.py'; exec(compile(open(p, encoding='utf-8').read(), p, 'exec'))
```

Kalibrierung, Maskenreihenfolge, Edge Blending und Study-/Tracking-Modi
bleiben geschützt.
Stabile ID-Zuordnung, Paketaktualität und Layoutaktivierung müssen für den
späteren Kameradatenpfad separat nachgewiesen werden.
Die vorhandene Maskierung muss beim späteren Anschluss
weiterverwendet werden; `select_tabletop` (Select TOP) liegt bereits hinter
der bestehenden Tabletop-Maskierung und ist deshalb kein ungeprüfter
Anschlusspunkt für unmaskierten neuen Content.

Offline-Tests und die 22 synthetischen TD-Zustands-/Pixelprüfungen bestehen.
Der sichtbare Pause-/Fortsetzungs-/Aktivierungstest im OSC-Simulator ist
bestätigt. Unabhängige Tischzustände sind in TD synthetisch geprüft;
Dreitisch-Feedback und Kontaktfortschritt nach Reaktivierung sind sichtbar
bestätigt; außerdem ist die sichtbare Fünftisch-Kapazitätsprüfung bestanden.
Der Kamera-/Live-Adapter ist
noch nicht angeschlossen: stabile ID-/Slot-Zuordnung, Aktivierungsereignis
und Aktualität sind für dessen tatsächlichen Datenpfad separat zu prüfen.
Tracking-/Study-Erhalt ist bisher nur strukturell vorbereitet; Bildvergleiche
der bestehenden Modi und Labortests sind nicht ausgeführt. Reale Projektion,
Jitter, Kontaktzeitpunkt, Wahrnehmung und Leistung benötigen eigene Labortests.


### Abgleich vor dem Anschluss der Layout-Generierung — 2026-10-23

Johannes bestätigt die sichtbaren Tischdarstellungen und Boden-Bewegungspfeile
in der produktiven Simulationsausgabe. Die Stühle stehen noch am alten Layout;
Tischziele und Chairs sollen künftig aus demselben explizit aktivierten
Vorschlag übernommen werden. Die bisherige Motion-Simulation verwendet
weiterhin Testziele und ist nicht mit der Layout-Generierung verbunden.

Johannes berichtet, die quelladaptive Generierung auf dem Laborrechner
deaktiviert zu haben. Diese Einstellung ist vor dem Generatoranschluss zu
klären: Gemeint sein kann das fortlaufende Nachberechnen während Bewegung
oder bereits die Berechnung eines Vorschlags aus den Istposen. Keine der
beiden Bedeutungen wird stillschweigend angenommen oder wieder aktiviert.

GitHub wurde lesend abgefragt und der Branch
`origin/codex/lab-inbetriebnahme-20261021` zum Vergleich abgerufen; kein Merge,
Checkout-Wechsel oder Überschreiben lokaler Änderungen. Sein Stand `cac6365`
enthält die Laborintegration. Die Generator-Dateien `sim_layout_rules.py` und
`layout_synthesizer.py` unterscheiden sich dort nicht vom lokalen HEAD
`4d400b6`; quelladaptive Synthese ist weiterhin enthalten. Der Labor-Handoff
`docs/LAB_INBETRIEBNAHME.md` dokumentiert weiterhin kontinuierliche Anpassung
und keine ergänzte Latch-/Freeze-Funktion. Eine spätere lokale Abschaltung im
Labor ist damit weder widerlegt noch auf diesem Branch nachgewiesen.
Laufzeit-State und die Labor-TOE wurden laut Handoff nicht über Git übertragen.
Bis zur Klärung wird keine Generatorvariante neu angeschlossen; die aktive
TD-Simulation und alle bestehenden Layout-/Study-/Kalibrierungspfade bleiben
unverändert.


### Layout-Generierung einmal bei Aktivierung — 2026-10-23

Johannes klärt den obigen Labor-Abgleich: Deaktiviert ist das fortlaufende
Nachberechnen während Tischbewegung. Beim Aktivieren darf aus den aktuellen
Istposen berechnet werden. Diese Präzisierung ist als D005a festgehalten.

Implementiert, noch nicht im laufenden TD installiert:

- `src/aisi/app/motion_layout_proposal.py`: bestehende Generatoren, maximal fünf Rect-Tische, stabile IDs/Scene Order, gemeinsame unveränderliche Ziel-/Chair-Menge. Keine Übernahme unvollständiger, nicht endlicher oder kollidierender Tischziele. Sitz-/Kontaktregeln bleiben in den bestehenden Formatplanern; Discussion-Chairs dürfen deren vorgesehene Tischkante berühren. Ohne Teilnehmenden-Opt-in nur Tischziele; kein stiller Fallback bei Planerfehlern.
- `motion_preview_sim.py --generated-layouts`: beim Klick aktuelles `learning_format.json` und Istposen erfassen, einmal im Worker berechnen. Währenddessen sendet der bisherige Vorschlag weiter. Nur erfolgreicher Commit im Editor-Thread erhöht die Revision. Geänderte Tischmenge während Berechnung oder Planerfehler erhalten den bisherigen Vorschlag. Verschieben und UI-Einstellungsänderungen lösen keine Aktivierung aus. Start ist bis zum ersten erfolgreichen Klick leer.
- `motion_chairs.py` und `.frag`: additive `/aisi_motion/chairs/...`-Nachrichten im selben Bundle wie die Tischposen. Session/Frame/Revision binden Stühle an den Vorschlag; Count-Schrumpfung, fehlende/alte/unvollständige Pakete und Timeout erzeugen keine alten Stuhlmarker. Weiße Ringe, 2,5 cm Stärke nach innen bei erhaltenem Außenradius; Reveal und aktuelle Tisch-Footprints werden berücksichtigt. Die beiden Texturen werden gemäß [GLSL-TOP-Dokumentation](https://docs.derivative.ca/Write_a_GLSL_TOP) über `sTD2DInputs[0]`/`[1]` gelesen.
- `build_motion_layout_chairs.py`: isolierte eigene Chair-Komponente. Der erweiterte registrierte Ausgabetest schaltet den zweiten Bild-Eingang der vorhandenen `composite_floor_with_synth_chairs` (Composite TOP) reversibel auf diese Quelle. Composite-Operation und bestehender Chair-Schalter bleiben erhalten. Gleiches Simulation-/AISI-/Kalibrierungsgatter wie für Content und Maske; Study, Tracking und Kalibrierung verwenden die alte Quelle. Stop stellt den Originaleingang wieder her; lokale Fremdänderungen werden geschützt.
- `prepare_motion_layout_simulation.py`: bisherigen registrierten Test zurückbauen, isolierte Chairs bauen oder unverändert wiederverwenden, nur den eigenen Fixture-Sender durch die Fünf-Tisch-Simulation mit Generator ersetzen, anschließend deaktivierte GPU-/Bypass-Vorbereitung. Keine automatische TD-Speicherung und kein Merge des Labor-Branches.

**Ausgeführt:** 62 fokussierte Prüfungen bestanden: zehn Vorschlags-/OSC-
Integrationstests mit echten Generatoren aller drei Lernformate, sechs
Chair-Tests (einschließlich drei nativer Zwei-Textur-GPU-Prüfungen),
29 Routing-/Simulationstests, fünf Launcher-Tests und zwölf bestehende
Motion-Transporttests. Getestet: eingefrorene Ziele/Chairs trotz Source-Bewegung
und Reihenfolgeänderung, genau einmaliger Commit, Fehlererhalt, explizites
Opt-in, alte Chair-Pakete, gemeinsamer Modusschalter, Rückbau und Schutz
lokaler Änderungen. Python-3.9-Syntax der TD-Skripte geprüft.

Echte Generatorprobe offline: Input, Groupwork, Discussion jeweils fünf Tische,
acht Teilnehmende, 100 %, bei Groupwork zwei Gruppen. Zusätzlich aktueller
lokaler State erfolgreich berechnet: Discussion, 13 Teilnehmende, 88 %, fünf
Tischziele/13 Chairs. Laufzeit-State nicht verändert. Native GPU-Prüfung
verwendet den echten Chair-Shader mit zwei Texturen; sie ersetzt keine
Kompilierung im laufenden TD und keine Projektor-/Raumabnahme.

**Manuell in TD ausführen:**

1. Den bisherigen Test und eigenen Simulator kontrolliert ersetzen sowie den neuen Ausgabetest vorbereiten:

```python
p = '/Users/Johannes/dev/Promotion_Prototypen/AISI/td_builders/prepare_motion_layout_simulation.py'
exec(compile(open(p, encoding='utf-8').read(), p, 'exec'))
```

2. Nach Rückkehr zum Textport als neue Eingabe aktivieren:

```python
import importlib, json
from td_builders import motion_output_simulation_test as output_test
output_test = importlib.reload(output_test)
print(json.dumps(output_test.activate(op), ensure_ascii=False, indent=2))
```

3. In der vorhandenen Learning-Format-Oberfläche gewünschte Einstellungen wählen. Für vergleichbare Abnahme: „Synthetische Tischplanung testen“ an, acht Teilnehmende, 100 %, bei Groupwork zwei Gruppen; Chairs an. Diese Einstellung aktiviert noch keinen Vorschlag. Im neuen Room Editor „Vorschlag aktivieren“ klicken und die erfolgreiche Statusmeldung abwarten. Dann erscheinen generierte Tischziele und Stühle.
4. Anschließend den aktiven Ausgabepfad prüfen:

```python
print(json.dumps(output_test.verify(op), ensure_ascii=False, indent=2))
```

Erwartet: `chair_index = 1`, gemeinsam mit beiden Content-Indizes und
`mask_index = 1`; Chair-Quelle im selben Gatter und fehlerfreie zentrale
Ausgänge. `chair_stream` zeigt die unabhängige Empfangsdiagnose und sichtbare
Chair-Anzahl. Bei Pixelabweichung baut der Prüfer eine unverändert registrierte
Sitzung zurück. Das bestehende Stop bleibt gültig:

```python
print(json.dumps(output_test.stop(op), ensure_ascii=False, indent=2))
```

**Noch in TD abzunehmen:** Für jedes Format einzeln einmal aktivieren,
Tisch bewegen/verdrehen und Ziel-/Stuhlpositionen unverändert beobachten;
Feedback und unabhängige Abschlüsse prüfen. Lernformat-Einstellungen ändern:
Bis zum nächsten Klick bleibt der Vorschlag stehen. Nach erneutem Klick
entsteht genau eine Reveal-Welle und die vollständige neue Ziel-/Chair-Menge.
Ungültige Anfrage muss Fehler anzeigen und bisherigen Vorschlag erhalten.
Danach kurzer formatübergreifender Durchlauf und tatsächlicher
Study-/Tracking-/Kalibrierungsmodusvergleich mit Rückkehr zu den alten Quellen.
Installation und aktive Pixelprüfung dieses erweiterten Anschlusses stehen
noch aus. Physische Raumvalidierung sowie Anschluss echter Trackingframes
bleiben Labortests; kein entsprechender Nachweis auf diesem Mac.
