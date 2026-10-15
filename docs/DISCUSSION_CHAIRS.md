# Discussion-Chairs

Stand: 2026-10-15. Die Opt-in-Teilnehmervorschau verwendet die von Johannes
gewünschte Staffelung statt eines stets vollständigen Fünf-Tisch-Rings.

| Personen | Aktive Tische | Belegung |
| --- | --- | --- |
| 1–4 | Zwei, mit gemeinsamer Längskante | Äußere Längsseiten, bei vier `2 + 2` gegenüber |
| 5 | Dieselbe Zweiergruppe | Vier Längsplätze und ein gemeinsamer Stirnplatz |
| 6 | Dieselbe Zweiergruppe | Vier Längsplätze und je ein Stirnplatz an beiden Enden |
| 7–12 | Vier als nach innen gerichtetes Rechteck | Gleichmäßig auf äußere Längsseiten, bei zwölf drei je Tisch |
| 13–15 | Fünf als nach innen gerichtetes Pentagon | Gleichmäßig auf äußere Längsseiten |

Überzählige Tische werden mit einer Längsseite an den ROI-Rand geschoben.
Sie halten mindestens 60 cm Abstand zu aktiven Tischen und blockieren keine
Sitz-/Bewegungsflächen oder Chair-Kreise. Alle Tisch-IDs bleiben vorhanden;
Ausgabe erfolgt in ursprünglicher Scene Order. Die aktive Auswahl und Parkwege
werden gemeinsam nach Gesamtbewegung bewertet. Innerhalb einer Teilnehmerstufe
bleiben Tischidentitäten und Posen stabil: Geplant wird einmal mit der
Maximalbelegung 6, 12 beziehungsweise 15, danach ändern sich nur die Chairs. Die aktive Source-Winkelreihenfolge
im Vierer-/Fünferring bleibt gebunden; kein nachträglicher globaler Slottausch.

Aktivierung: `adaptive_layout_preview=True`, optional ganzzahlige positive
`participants`. Ohne Count gilt weiterhin `2 × verfügbare Tischanzahl`;
anschließend bestimmt die Tabelle oben die benötigte Topologie. Beispielsweise
führt der Standard zehn bei fünf verfügbaren Tischen zu vier aktiven Tischen
mit `3 + 3 + 2 + 2` und einem Parktisch. Explizite Interface-Counts bleiben
maßgeblich. Zu wenige Tische für eine Stufe oder mehr als 15 Personen führen
zur ausdrücklichen Ablehnung, ohne Kürzung oder Rückfall auf ein anderes Layout.

## Gemeinsame Geometrie

Der bestehende Chair-Durchmesser bleibt 50 cm. Die Zweiergruppe teilt exakt
eine Längskante, ohne positive Tischüberlappung. Die äußeren Sitzflächen sind
kanonische, 50 cm tiefe Streifen. Gemeinsame Stirnflächen werden mit derselben
Geometriefunktion über beide Tischhälften erzeugt. Ein Stirn-Chair darf beide
Tischhälften rein tangieren. Zwischen den verbundenen Tischen liegt keine
Sitz-/Bewegungsfläche. Vierer-/Fünferringe behalten beide bestehenden
Längsseiten-Sitz-/Bewegungsstreifen; Chairs liegen außen.

Bei drei Chairs auf einer Längsseite beträgt der Mittelpunktabstand 52 cm,
mit 2 cm zwischen den Kreisen. Johannes akzeptiert den geplotteten Überstand
von maximal 0,51 cm ausschließlich an den abgerundeten Sitzflächenecken.
Gerade Flächengrenzen, vollständige Tisch-/Chair-ROI und fremde Tisch-/Chair-
Kollisionen bleiben strikt. Die eigene Tischkante darf vorläufig tangiert werden.

Für die Ringstufen werden bestehende Synthese-/Ringfunktionen wiederverwendet.
Bei vier aktiven und einem Parktisch prüft die begrenzte Suche zusätzlich
Rotationen in 15°-Schritten mit gemeinsamem Mittelpunktversatz; der bisherige
bewegungsoptimierte Ring bleibt ebenfalls Kandidat. Alle Kandidaten durchlaufen
die gemeinsame Geometrieprüfung. Der Fünferring nutzt die bestehende feinere
Phasen-/Mittelpunktsuche einschließlich Chair-Grenzen. Die Parkplanung nutzt
den vorhandenen kompakten Parkhelfer. Begrenzte Caches liefern unabhängige
Ergebniskopien; gleiche Parkgeometrie innerhalb einer Suche wird wiederverwendet.

Stärke 0 erhält exakte Source-Posen ohne Chairs. Teilstärken blenden die bereits
gebundenen aktiven/geparkten Rollen entlang des kürzesten Rotationswegs und
prüfen die gemeinsame Geometrie. Ungültige Teilposen werden ausdrücklich
abgelehnt; kein Rollenwechsel als Reparatur. Für die Zielprüfung 100 % verwenden.
Der normale Modus ohne Opt-in und isoliertes Tracking behalten ihre bisherigen Wege.

## Offline-Nachweis

- 30 Fälle: Editor- und aktuelle Live-Ausgangsszene, jeweils fünf Rect-Tische
  und alle Teilnehmerzahlen 1–15. Quellen beim Lauf lokal eingefroren.
- Gemeinsame ROI-/Kollisionsprüfung einschließlich Parktischen, 60-cm-Abstand,
  Übergänge 6→7 und 12→13, deterministische Wiederholung und umgekehrte Scene Order.
- 37 fokussierte Tests: Discussion-Chairs, unveränderte Rect-Templates,
  Input-Geometrie und Groupwork-Vorschau. Auch fehlende Tische, Kapazität,
  Tangenz versus Durchdringung, Cache-Kopien, Stärke 0 und Teilstärken geprüft.
- OSC-Ausgabe lokal aufgezeichnet, ohne Netzwerkversand. Bestehende Adressen,
  Chair-Radius 25 als Float, Tischanzahl und Source-/Target-Reihenfolge beibehalten.
- Kontrollplots mit 4, 6, 12 und 15 Personen für beide Ausgangsszenen visuell geprüft.
  Lokale Artefakte: `data/aisi/debug/discussion_participants_2026-10-15/`.

Reproduktion:

```sh
MPLCONFIGDIR=/tmp/aisi-mpl PYTHONPATH=src .venv/bin/python \
  scripts/validate_discussion_participants.py \
  --scene data/aisi/scenes/simulated/live_scene.json \
  --output data/aisi/debug/discussion_participants_2026-10-15
```

Der frühere 90-Fälle-Nachweis vom 2026-10-09 betraf den vorherigen festen Ring.
Der Größenvergleich bleibt über `scripts/plot_discussion_chair_fit.py`
reproduzierbar; die 45-cm-Alternative wurde verworfen.

## Offene Prüfung

Discussion-Chairs bei 100 % einzeln in Room Editor, Learning-Format-Interface
und TouchDesigner prüfen, besonders 4/5/6 Personen, beide Topologieübergänge
und die Parktische. Anschließend kurzer Formatwechsel-Check. Eigene
Tischkantentangenz und Rundungsüberstand physisch beurteilen.
Keine TD-Fernsteuerung, automatische Speicherung oder physische
Projektionsvalidierung erfolgt.
