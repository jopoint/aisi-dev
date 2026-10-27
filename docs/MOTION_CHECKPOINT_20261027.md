# Motion-Checkpoint — 2026-10-27

## Abnahme und Nachweisgrenzen

Johannes meldet: „alle Systemtest abgeschlossen. Stand sichern“.
Die reale Systemprüfung wird damit als durch Johannes abgeschlossen dokumentiert.
Zuvor einzeln gemeldet: Input 1–5 Tische, Groupwork ein Tisch sowie fünf Tische/
15 Teilnehmende/drei Gruppen, Einstellungen ohne Aktivierung, ID-Bindung,
Tracking-Wiederkehr, Modi und mehrere Grafikabnahmen. Für die zuletzt pauschal
abgeschlossenen Fälle wurden keine zusätzlichen Einzelparameter, Zeitmessungen
oder Textport-Berichte nachgereicht. Keine solchen Messwerte ergänzen und die
Gesamtbestätigung nicht als unabhängigen automatisierten Raumnachweis ausgeben.

## Gesicherter Funktionsstand

- Gemeinsamer Windows-Start: `scripts/run_aisi_motion.ps1`; integrierte Web-/
  Motion-Steuerung, keine separate Tk-Bedienung im normalen Betrieb.
- Vorschlag explizit in Learning-Format-UI aktivieren. Erst erfolgreiche Planung
  übernimmt Ziele/Chairs gemeinsam und erhöht die Revision. Laufende Bewegung
  und vorgemerkte Einstellungen verändern diese nicht (D005a).
- Automatische TD-Prüfung/Freigabe nach Quellen-/Maskenabgleich; Sperre bei
  Ausfällen. Kein Rückfall auf alte Layoutgrafik im AISI-Modus. Study und
  Tracking-only erhalten. Kameraneustart verbindet kontrolliert neu; neue
  Zielzuordnung bleibt explizit, keine stille Übernahme anderer IDs.
- Reveal erst nach abgeschlossener Freigabeprüfung, Chairs mit derselben Welle.
- Schlankere Learning-Format-UI ohne kleine Formatillustrationen;
  technische Details unter Diagnose. Groupwork-Suche anfrageintern beschleunigt,
  Kandidaten-/Geometriebedingungen unverändert.
- Abgenommene Zielkontur durchgängig, 5 cm nach innen am bisherigen Umriss,
  Boden und Tabletop gleich. Chair-Striche ebenfalls 5 cm nach innen;
  Außenradien und Positionen erhalten.
- Feedbackradius distanzabhängig: 80 % des Maximalradius bei 20 cm, Maximum
  bei 8 cm; grünes Feedback bleibt auf semantischen Ziel-Footprint begrenzt.
- Zielring/-striche als Alpha-Aussparungen; separater Source-Weiß-Patch verfügbar.
  Seine Einzellinstallation wurde nicht ausdrücklich zurückgemeldet und wird
  nicht durch den Konturpatch automatisch vorausgesetzt/erzwungen.
- Persistente Fertig-Haken bis alle Tische fertig sind, einschließlich anfangs
  passend stehender Tische. Danach 1 s gemeinsame Anzeige und 0,32 s Reverse-Pop.
  Bestehende Erfolgs-/Wiederaufnahmegrenzen erhalten; Ausfälle pausieren Anzeige.

## Tatsächlicher TD-Graph und Reproduzierbarkeit

Die Grafikänderungen wurden über reversible Helfer in den tatsächlich geöffneten
Graph installiert und durch Johannes geprüft. Repository-Grundshader/Builder
sind weiterhin Ausgangsstände, kein vollständiger Export des aktiven Graphen.
Nicht aus ihnen die physische Datei neu generieren. Eigene Shader-Sicherungen
und Snapshot-Hashes bleiben im Graphen; spätere Änderungen blockieren bewusst
einen unpassenden älteren Rollback.

Installationsfolge der jüngsten eigenen Helfer, nur als Referenz für fehlende
Patches, nicht blind erneut auf vorhandene Komponenten anwenden:
`update_motion_visual_reveal`, `update_motion_chair_reveal`,
`update_motion_target_dashes`, `update_motion_feedback_size_cutouts`,
`update_motion_group_success`, optional `update_motion_source_bars_white`,
`update_motion_continuous_contours`. Alle jeweils mit separatem Prepare und
GPU-Installnachweis. Frühere Designexperimente bleiben als rücknehmbare Historie.

TD wird nur durch Johannes manuell gespeichert. Neuester genauer Dateiname und
erneute Speicherung nach den letzten Änderungen sind nicht gemeldet; die
Git-Sicherung umfasst keine `.toe`-Datei. Master `AISI_v2.toe` unberührt lassen.
Homographien, Kalibrierung, Projektortransforms, Grids/Shaderkorrekturen,
Edge Blending, Maßstab, Footprints und Maskenreihenfolge bleiben geschützt.

## Letzter lesender Laufzeitstatus

Sitzung 2730811, Revision 27, Input, 13 Chairs, fünf frische IDs
`table_00`, `table_03`, `table_04`, `table_05`, `table_06`, TD automatisch
freigegeben, kein Fehler/ausstehender Auftrag. Letzte Berechnung 0,004690 s.
Das ist eine Momentaufnahme, kein rückwirkender Nachweis sämtlicher Raumfälle.

## Offline-Abschlussprüfung vor Git-Sicherung

- Motion-Suite: 433 Fälle, 426 bestanden, sieben optionale GPU-Fälle übersprungen.
- Groupwork-Optioncache, Teilnehmer-/Sitzplanung, adaptiver Rect-Prototyp,
  Groupwork-Vorschau und Learning-Format-UI: weitere 59 Fälle bestanden.
- Zusammen 485 bestandene Tests, sieben übersprungene. `git diff --check` sauber.
  Native GPU-/Raumbefunde stammen separat aus den manuellen TD-Installationen
  und Johannes' Rückmeldungen, nicht aus diesen Offline-Tests.

## Nächster unabhängiger Block

Motion nach dem gemeldeten Systemtestabschluss als regulären AISI-Standard
abschließend konsolidieren; dabei gespeicherten TD-Checkpoint und bestehenden
Startpfad prüfen. Dieser Sicherungsauftrag ändert keine weiteren Start-/
Projektoreinstellungen. Untertisch-Versuch bleibt ausdrücklich pausiert.
Laufzeit-/Debug-/Trainings- und Kalibrierungsdaten bleiben lokal erhalten und
werden nicht mit der Codesicherung versioniert.
