# Gemeinsame Rect-Input-Geometrie — Offline-Validierung

Stand: 2026-10-07. Branch `vision/wip-dark-proposals`, geprüfte Ausgangsbasis
`9f822ce6919419cf38c21e9ce8a953045f64f713`. Die parallele Input-Bearbeitung wurde übernommen
und unabhängig nachgeprüft; bestehende Änderungen bleiben erhalten.

## Ergebnis und Prüfumfang

**300/300 Fälle bestanden:** jeweils fünf Rect-Tische, Counts `1–15`,
Editor-Startszene, aktuelle simulierte Live-Szene, um 35° gedrehte Startszene
und asymmetrische Quelle. Jede Quelle wurde mit automatischer Ausrichtung
sowie `north`, `east`, `south`, `west` bei `100 %` geprüft.

Geprüft wurden kanonische Tisch-Footprints, vollständige Chair-Kreise mit
`25 cm` Radius und gerichtete, außen abgerundete `70 cm` Sitz-/Bewegungsflächen:
ROI-Einhaltung, Tisch-/Tisch-, Tisch-/Chair- und Chair-/Chair-Kollisionen,
gegenseitige Blockierung der Flächen und Parktische. Die Prüfung betrifft
den Endzustand; Bewegungspfade und globale Raumerschließung werden nicht
als kollisionsfrei behauptet. Die gedrehte Quelle enthält bewusst auch
über die ROI ragende Source-Konturen; alle erzeugten Ziele liegen darin.

Kapazität: `min(5, ceil(Count / 2))` aktive Tische; höchstens zwei Plätze
pro Tisch, bis alle fünf aktiv sind, danach höchstens drei. Rollen und
Chairs bleiben an die Tisch-ID gebunden, Ausgabe folgt der Source Scene
Order. **300 Wiederholungen** sind exakt deterministisch; **140 Prüfungen**
mit umgekehrter Scene Order ergeben identische Ziele pro ID und Chair-Reihenfolge.
**60 Anfragen** mit Count `16`, `17`, `30` werden ausdrücklich abgelehnt.
Count 0 ist ausgenommen. Änderungen der aktiven Teilmenge bei wechselndem
Count bleiben quelladaptiv; daraus folgt keine Zusage minimaler Umverteilung
über unterschiedliche Counts hinweg.

## Belegte Fehler und Korrekturen

- Der frühere Vorschaupfad ersetzte Count 16 still durch fünf normale
  Input-Tischziele ohne Chairs. Er propagiert jetzt `LayoutConstraintError`.
- Chairs verwendeten bei der Raumachsen-Ausweichlösung weiterhin die
  Quellachse. Für die diagonale Quelle mit Count 15 wurden **29 Verletzungen
  vorher, keine danach** unabhängig nachgewiesen. Chair-Richtung folgt jetzt
  derselben gerichteten Zielnormalen wie die kanonische Sitzfläche.
- Die optionale Präsentationsseite wird bis in die bestehende Rect-Synthese
  weitergegeben; sie bestimmt Präsentationsrolle und Ausrichtung.
- Stabile ID-Sortierung und präzise Summierung verhindern Änderungen durch
  eine andere Scene Order; Ziele werden danach in Source-Reihenfolge ausgegeben.
- Bei Transformationsstärke 0 wurden Parktische trotzdem verschoben.
  Alle Tischposen bleiben jetzt exakt an der Source, ohne Parkreparatur.
  Volle Sitzflächenvalidität wird ausschließlich für den 100-%-Endzustand geprüft.

## Nachweise und Wiederholung

Bericht und drei visuell geprüfte Übersichten liegen unter
`data/aisi/debug/input_geometry_validation_2026-10-07/`:
`validation.json`, `kapazitaet.png`, `quelladaptiv.png`, `praesentationsseiten.png`.
Der Bericht enthält die tatsächlich verwendeten synthetischen Quellen.

```sh
MPLBACKEND=Agg MPLCONFIGDIR=/private/tmp/aisi-mpl .venv/bin/python scripts/validate_input_geometry.py --output data/aisi/debug/input_geometry_validation_2026-10-07
# Dieselben gespeicherten Quellen später erneut prüfen:
MPLBACKEND=Agg MPLCONFIGDIR=/private/tmp/aisi-mpl .venv/bin/python scripts/validate_input_geometry.py --fixtures data/aisi/debug/input_geometry_validation_2026-10-07/validation.json --output /private/tmp/aisi-input-recheck
```

**59 fokussierte Tests bestanden:** `test_polygon_layout_pipeline.py` (10),
`test_synthetic_input_geometry.py` (8), `test_input_offline_validation.py` (2),
`test_table_geometry.py` (15), `test_tracking_only_osc.py` (24).
OSC wurde mit einem lokalen Nachrichtenrecorder geprüft: 45 Float-Nachrichten
für `/chair/0…14/{x,y,radius}`; Überkapazität scheitert bereits vor Ausgabe.
Kein Sender gestartet. `git diff --check` bestanden.

## TD-Handoff und offene Grenzen

Laut Johannes sind zentrale 15-Chair-Struktur, OSC-Live-Reaktion und
TD-Modussperren geprüft; AISI zeigt Zieltischkonturen und Bodenpfeile,
Rect-Konturen entsprechen dem Study-Stil. Letzter Stand manuell gespeichert.
Dateisystemseitig verifiziert im OneDrive-Projektordner:
`AISI_v2.139_aisi_floor_study_style.toe` und der Zwischenstand
`AISI_v2.140_coherent_chairs_validated.toe`. Version 140 und
`AISI_v2_coherent_chairs_validated.toe` sind SHA-256-identisch:
`280fcfa5be898e60c9d7ad747d910fa64f641cc9eb90c7dff60c2b3e63805616`.
Das belegt die Datei, keinen erneuten Öffnungs- oder Raumcheck.

Nach der manuellen Stichprobe wurde die Ring-Radius-Abhängigkeit repariert
und von Johannes als behoben bestätigt. Neuester manuell gespeicherter Stand:
`AISI_v2.141_coherent_chairs_validated.toe`, SHA-256
`ca3e69a26ba284c55102a53330a78e759cca27f223c8df0fb9eb81956a6f6d0e`.
Template und alle 15 Instanzen enthalten die Bindung nachweislich in der
Datei; der Wiederöffnungscheck bleibt offen. Details stehen im
[Chair-Debug-Handoff](TOUCHDESIGNER_SYNTH_CHAIR_DEBUG.md).

Keine TD-Fernsteuerung, kein automatisches Speichern; Study, Tracking,
Kalibrierung, Masken und Projektorkonfiguration nicht geändert.
Groupwork/Discussion nicht erweitert. Physische Raumprüfung bleibt
aufgeschoben. Echte OSC-Radius-null-Prüfung und Wiederöffnungscheck des
neuesten TD-Stands bleiben getrennte Live-Aufgaben.
