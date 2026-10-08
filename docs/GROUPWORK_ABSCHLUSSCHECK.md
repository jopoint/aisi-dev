# Gemeinsamer Groupwork-Offline-Abschlusscheck (2026-10-08)

## Ergebnis

**130/130 Anfragen bestanden**, jeweils vollständige kanonische Geometrie,
deterministische Wiederholung und umgekehrte Scene Order. Zunächst bestanden
127 Fälle; nur die drei Editor-Ablehnungen wurden nach der gezielten Korrektur
mit denselben gespeicherten Quellen erneut geprüft und zusammengeführt. Die
bisher erfolgreichen 127 Fälle erreichen den neuen Reparaturpfad nicht.
Die spezifizierten Beispiele und beide Plots wurden separat geprüft.

## Umfang und Grenzen

Geprüft werden vollständige virtuelle Ziele bei 100 %: fünf Rect-Tische in
500 × 500 cm, Counts 1–15 und alle zulässigen Gruppenzahlen 1–5, jeweils mit
Editor-Standardquelle und eingefrorener aktueller Live-Quelle. Das sind 130
fachliche Anfragen. Der bestehende Generator, seine Synthese und die kanonischen
Geometrieprüfungen werden verwendet. Die Quellen und vollständigen Pläne sind im
lokalen Bericht gespeichert; keine Live-Szene wird verändert.

Gemeinsam geprüft: physische Tisch-Footprints und ROI, getrennte Bodenkonturen,
Pair-Achse/8-cm-Seam, Chair-Kreise und Kollisionen, freie Sitz-/Bewegungsflächen,
Clusterflächen, 60-cm-Park-/Aktivabstand und Randlage der physischen Längsseite.
Zusätzlich: gleichmäßige Gruppengrößen, vollständige Gruppenzuordnung und
Tischidentität, eindeutige Seat-IDs, deterministische Wiederholung und Ausgabe
in ursprünglicher beziehungsweise umgekehrter Scene Order.

Räumliche Gruppenzugehörigkeit bleibt das bestehende relative Kriterium:
Verbindungskanten innerhalb einer Gruppe müssen kürzer sein als alle
Clusterzentrum-Abstände zwischen Gruppen. Positive und absichtlich ineinander
verschachtelte negative Beispiele prüfen dieses Kriterium. Es beweist keine
wahrnehmungspsychologische oder physische Eindeutigkeit; dafür ist weiterhin
visuelle beziehungsweise räumliche Prüfung nötig. Es wird kein neuer absoluter
Gruppenabstand eingeführt.

## Kapazität und spezifizierte Beispiele

- Fünf Personen am tatsächlich einzelnen Tisch: vier reguläre Längsseitenplätze
  und ein regulärer Stirnseitenplatz (`2 + 2 + 1`), keine Verdichtung. Das Beispiel
  wird separat aufgebaut; die Standard-Tischwahl darf bei verfügbaren Tischen
  weiterhin ein Pair bevorzugen.
- Eine Gruppe mit sieben Personen: Pair mit vier Chairs und Singleton mit drei
  Chairs; alle gehören derselben Teilnehmergruppe an. Die zulässige Aufteilung
  wird explizit geprüft, ist aber kein verpflichtendes Generatorziel.
- Einzel-Tisch: Counts 1–8 geometrisch geprüft, Stirnseiten vor verdichteten
  Längsseiten. Pair: Counts 1–8 gültig; neun und zehn passen mit aktuellen
  25-cm-Chairs nicht in die bestehende Sitzellipse und werden ausdrücklich
  abgelehnt. Elf überschreitet bereits die theoretische Sitzpositions-Obergrenze.
  Zehn ist damit keine zugesicherte Pair-Kapazität.
- 16 Personen/fünf Gruppen werden im Offline-Modell gültig erzeugt. Der
  Vorschau-/TD-Adapter lehnt 16, 20 und 40 ausdrücklich wegen seiner 15
  technischen Chair-Slots ab. Fachliche Kapazität und Ausgabegrenze bleiben
  getrennt. Keine Kürzung von Personen.

## Gefundene und gezielt behobene Sackgasse

Die Editor-Quelle lieferte bei `13/4`, `14/4` und `15/4` zunächst einen
quellnahen Kandidaten, dessen überlappende Bodenkonturen die anschließende
Entzerrung nicht auflösen konnte. Es existieren jedoch gültige Alternativen.
Nach einem belegten Reparaturfehlschlag wird dasselbe Belegungsprofil nochmals
mit vollständiger Konturprüfung im Kandidatenfilter gesucht. Vorher gültige
Suchpfade bleiben unverändert; sämtliche harten Bedingungen gelten weiter.
Keine nachträgliche globale Zielpermutation, keine neue Gruppensemantik.

## Fokussierte Regressionen

52 Tests für Groupwork-Teilnehmerplanung, Vorschau-/OSC-Adapter und den
bestehenden Rect-Prototyp bestanden. Dazu gehören die neuen Editor-Fälle
`13/4`–`15/4`, Pair-Kapazität, positive/negative relative Gruppenzuordnung und
die Trennung von geometrischer Kapazität und technischen TD-Slots.

## Wiederholung und Artefakte

```sh
PYTHONPATH=src .venv/bin/python scripts/validate_groupwork_participants.py \
  --complete --output data/aisi/debug/groupwork_participant_preview_2026-10-08/abschlusscheck
```

Mit `--fixtures <validation.json>` werden gespeicherte Quellen wiederverwendet.
`--retry-failures` prüft ausschließlich zuvor abgelehnte Fälle erneut und führt
sie mit den erhaltenen erfolgreichen Ergebnissen zusammen. `--examples-only`
prüft die Kapazitäts-/Spezifikationsbeispiele separat. Debug-Berichte und Plots
bleiben lokal und werden nicht in Git aufgenommen.

Keine echten OSC-Pakete, TD-Fernsteuerung oder automatische Speicherung.
Study, Tracking, Kalibrierung, Masken und Projektoren bleiben unberührt.
Gemessene Sender-Laufzeit, vollständige interaktive Einzelvalidierung und
physische Raumprüfung sind weiterhin getrennt offen.
