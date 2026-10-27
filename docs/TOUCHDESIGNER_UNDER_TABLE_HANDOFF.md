# Untertisch-Bodenzielgrafik — pausierter Arbeitsstand

Stand: 2026-10-27. **Auf ausdrücklichen Wunsch von Johannes pausiert.**
Keine automatische Fortsetzung, keine Hintergrundarbeit und keine Freigabe
oder Installation aus diesem Dokument ableiten.

## Ziel und unveränderte Produktion

Nur die Motion-Bodenzielgrafik soll den frühen senkrechten Tisch-Footprint-
Ausschluss umgehen. Bestehende projektorabhängige Tischmasken, Tabletop-
Darstellung, Kalibrierung und Maskenreihenfolge bleiben erhalten. Pfeile und
Reveal-Welle sollen ihren bisherigen Footprint-Ausschluss behalten.

Der Untertischversuch wurde **nicht produktiv installiert**. Der produktive
Shader blendet den Boden weiterhin über `(1.0-occupied)` aus. Der alternative
Shader existiert ausschließlich in isolierten Prüfzweigen und als Patchfunktion
in den unten genannten Helfern; der Repository-Standardshader wurde für diesen
Versuch nicht umgestellt. Frühere akzeptierte Grafikänderungen bleiben erhalten.
D005a gilt unverändert: Ziele und Chairs bleiben bis zur nächsten erfolgreichen
expliziten Aktivierung gemeinsam fest.

Letzte tatsächlich per Textport gemeldete Arbeitsdatei:
`C:/Users/johan/OneDrive/Dokumente/AISI_DEV/touchdesigner/AISI_v3.2_motion_lab_checkpoint_20261026.12.toe`.
Keine automatische TD-Speicherung. Der Speicherstand der letzten Haken-Grafik
wurde nicht gesondert bestätigt. Die geschützte Masterdatei `AISI_v2.toe` bleibt
unangetastet. Keine Dienste wegen der Pause starten, stoppen oder umstellen.
Kein Bildschirmzugriff; weitere TD-Interaktion nur durch manuelle Textport-Befehle.

## Tatsächlich bestanden

1. **Lesende Graphprüfung im laufenden TD:** Zwei Projektoren mit separater
   Floor-/Tabletop-/Tischmasken-Abbildung. Tabletop und Maske verwenden je
   Projektor dieselben neun aktiven Uniformwerte und dieselbe lokale
   Korrekturfunktion. Nach Warps: invertierte Tischmaske × Floor, danach
   Tabletop per Over. Daher kann die bestehende Projektormaske die Grundlage
   des Versuchs bleiben; nicht durch neue idealisierte Builder-Masken ersetzen.
2. **Isolierter Weltbild-GPU-Test:** zwölf Prüfgruppen bestanden, darunter neun
   Fälle für 0/33/90 Grad, ein/fünf Tische und Reveal. Nur erwarteter Zielanteil
   innerhalb gemeinsamer Source-Footprints ergänzt. Maximaler Musterfehler
   `5.960464477539063e-08`, RGBA8-Abweichung 0; Tabletop exakt unverändert.
   Invalidität, Inaktivität, Completed, Fade, Nichtüberlappung, Erfolg und
   Wiedereinblendung geprüft.
3. **Isolierte kalibrierte Float32-Floorzweige:** beide Projektoren mit je sechs
   Posefällen bestanden, nach Projektormaske und vor finalem Tabletop-Composite.
   Projektor 0: zusätzliche Pixel 49109–192815, maximaler RGB-Gleichungsfehler
   `6.705522537231445e-08`. Projektor 1: 103279–238112 Pixel, Fehler maximal
   `8.195638656616211e-08`. In tatsächlich vorhandenen vollständig gesperrten
   Bereichen maximaler Zusatz `7.748603820800781e-07`, unter Toleranz `1e-06`.
   Einige Fälle enthalten keine vollständig gesperrten Pixel und liefern dafür
   keinen Sperrnachweis. Beide Modelle zeigen zusätzlichen durchgelassenen
   Zielanteil; das ist noch **kein physischer Untertischnachweis**.
4. **Offline:** zur beauftragten Sicherung vollständigen Motion-Lauf erneut
   ausgeführt: 352 Fälle, 345 bestanden, sieben optionale GPU-Fälle übersprungen.
   Zuvor auch 17 fokussierte native Prüftests bestanden. Diese Zahlen ersetzen
   keine native TD-GPU-Prüfung.

## Prüfzweige und Dateien

Weltbild- und Float32-Projektorproben wurden entfernt; nachfolgende Cleanup-
Aufrufe bestätigten jeweils fehlende Proben. Fehlgeschlagene native Vorbereitungen
entfernen ihren eigenen Teilzweig im Ausnahmeweg. Es gibt keine installierte
native Probe und keine Verbindung zu Projektorfenstern. Bei Wiederaufnahme
Existenz der drei Pfade zuerst nur lesen, nicht blind überschreiben:

- `/project1/comp_aisi_motion_under_table_probe`
- `/project1/comp_aisi_motion_under_table_projector_probe`
- `/project1/comp_aisi_motion_under_table_native_probe`

Helfer und entsprechende Tests sind lokal vorhanden:

- `td_builders/prepare_motion_under_table_probe.py`: synthetischer Weltbild-
  Vergleich, `prepare/check/cleanup`, keine Installationsfunktion.
- `td_builders/prepare_motion_under_table_projector_probe.py`: bereits geprüfte
  Float32-Projektorkopien, je ein Projektor, `prepare/check/cleanup`.
- `td_builders/prepare_motion_under_table_native_probe.py`: noch unvollständiger
  nativer Vergleich einschließlich Quelle/Resampling/Chair-Snapshot/Masken/
  Warps/Blending/finalem Over; `inspect_stages` rein lesend.
- `tests/test_motion_under_table_probe.py`,
  `tests/test_motion_under_table_projector_probe.py`,
  `tests/test_motion_under_table_native_probe.py`.

Git vor der beauftragten Sicherung: Branch `vision/wip-dark-proposals`, HEAD `a9cb57a`
(`Integrate and validate Windows Motion lab checkpoint`), gleich Remote-Stand.
Johannes beauftragt anschließend ausdrücklich Commit und Push des aktuellen
Standes einschließlich dieser Übergabe; **der Untertisch-Versuch bleibt pausiert**.
Der zugehörige Sicherungscommit versioniert die heutigen Grafikänderungen,
reversiblen Helfer, Tests, isolierten Proben und Übergabedokumente auf diesem
Branch. Der native Untertischhelfer wird ausdrücklich als unvollständiger,
nicht produktiv freigegebener Zwischenstand gesichert. Vorhandene Änderungen
an Simulationsdaten und ungetrackte Laufzeit-/Debug-/Kalibrierungsdaten bleiben
lokal erhalten und außerhalb des Commits. Keine `.toe`-Datei wird gespeichert
oder aufgenommen. Sicherung ist kein Auftrag zur Fortsetzung des Versuchs.

## Native Folgestufe: konkreter offener Stand

Noch kein erfolgreicher nativer `prepare`, daher auch kein nativer GPU-Nachweis.
Bisherige Schutzabbrüche haben keine produktiven Parameter geändert:

1. Rohe Masken-Alpha-Konvention wurde zunächst falsch eingegrenzt. Tatsächliche
   Diagnose: Raw-RGB innen ca. 0,098–0,102, Alpha innen 1 und Hintergrund 0.
   Reorder nimmt `input1/alpha` für R/G/B und `input1/one` für A, `chanmask=15`.
   Helfer inzwischen korrigiert: Zuordnung und Roh-/Reorder-Pixel streng prüfen,
   nur Coverage in A nachbilden; ignorierte Raw-RGB-Lichtwerte nicht nachbauen.
2. TD 2022.29850/Python 3.9.5 stellt neuere Format-Eigenschaften nicht bereit.
   Resolver unterstützt eindeutige `useinput`-Vererbung und nichtblendende
   Switches mit gültigem ganzzahligem Index. Unklare Mischfälle bleiben gesperrt.
3. Letzter Vorbereitungsabbruch an
   `composite_floor_with_synth_chairs` (Composite TOP). Die anschließende
   Sammeldiagnose hat **41 Knoten gefunden, keine fehlen**. Sie klärt alle
   dynamischen Parameter der vorgesehenen Kopierstufen:
   - Motion-Renderer: `resolutionw/h = 1000` aus `parent().par.Resolution`.
   - Routing-Floor-/Tabletop-Selects: `resolutionw/h = 2000` aus Legacy-Größe.
   - **Noch zu ergänzen:** Chair-Composite `resolutionw/h = 2000`, Ausdruck
     `op('/project1/comp_layout_proposal/select_floor_for_synth_chairs').width`
     bzw. `.height`. Es sind Auflösungsabhängigkeiten, keine unbekannte
     Masken-/Geometrieoperation. Nur diese bestätigten Werte in der eigenen
     Kopie einfrieren; Originalausdrücke erhalten.
   - Sechs bekannte Index-Ausdrücke: optionale Chairs 1; Floor/Tabletop/
     Table-Mask-Content-Switches jeweils 0; beide Layer-Switches 1.
4. Die 16 Format-Fehlereinträge sind überwiegend Folgefehler weniger Ursachen:
   - `mask_tabletop` (Composite TOP): `useinput` mit gemischten Eingangsformaten;
     davon abhängige Null-/Select-/Switch-/Warp-Stufen.
   - Blend-Rampen ohne Kabelinput mit `useinput`; davon abhängige Blend-/
     Floor-Mask-/Final-Composite-Stufen. Formatwahl nicht pauschal erraten.
   - Speicherhinweise aus echter Diagnose: `mask_tabletop` bei 2000²
     `16000000` Bytes; Tabletop-Warps bei 3840×2160 `33177600` Bytes;
     finale Composites und Floor-Multiply-Stufen `132710400` Bytes.
     Hinweise mit aktiven Formateinstellungen/Storage-Verhalten abgleichen,
     nicht allein aus Bytes ungesicherte Formatzusagen ableiten.

Die vollständige letzte Sammeldiagnose liegt zusätzlich im Chat-Anhang
`C:/Users/johan/.codex/attachments/08e05775-d8d3-4cee-83cc-77f83f30f1f2/Pasted text.txt`.
Die wesentlichen Befunde sind oben festgehalten, nicht allein auf diesen
rechnerlokalen Anhang als Projektgedächtnis verlassen.

## Wiederaufnahme — erst auf neuen Auftrag

**Erster kleiner Block:** native Vorbereitung fertigstellen: bestätigte
Chair-Auflösungsparameter gezielt behandeln und die verbleibende Formatwahl
für Masken-Composite/Blend-Rampen auf TD 2022 belastbar bestimmen. Vor weiterer
Vorbereitung vollständige lesende Vorprüfung nutzen; keine weiteren blinden
Einzelversuche oder pauschale Freigabe dynamischer Parameter.

Danach native Probe separat für Projektor 0 und 1 im laufenden TD prüfen,
einschließlich finaler Tabletop-Komposition. Erst bei bestandenem Nachweis
eine gesonderte reversible Raum-Testumschaltung vorbereiten. Tatsächliche
Untertisch-Erreichbarkeit, Tischbeine/Untergestell und unerwünschtes Licht auf
der Tischplatte sind physisch noch ungeprüft. Keine Kalibrierung verändern,
keine `.toe` automatisch speichern. Bis dahin normale Motion-Ausgabe beibehalten.
