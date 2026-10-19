# Discussion-Chairs

Stand: 2026-10-15. Die Opt-in-Teilnehmervorschau verwendet die von Johannes
gewünschte Staffelung statt eines stets vollständigen Fünf-Tisch-Rings.
Die folgende Tabelle beschreibt die vollständige Zielform bei 100 %;
positive Zwischenwerte dürfen davon abweichen.

| Personen | Aktive Tische | Belegung |
| --- | --- | --- |
| 1–4 | Zwei, mit 10 cm Spalt an den Längskanten | Äußere Längsseiten, bei vier `2 + 2` gegenüber |
| 5 | Dieselbe Zweiergruppe | Vier Längsplätze und ein gemeinsamer Stirnplatz |
| 6 | Dieselbe Zweiergruppe | Vier Längsplätze und je ein Stirnplatz an beiden Enden |
| 7–8 | Vier als nach innen gerichtetes Rechteck | Höchstens zwei direkt je äußerer Längsseite |
| 9–12 | Dasselbe Vier-Tisch-Rechteck | Acht Längsplätze plus ein bis vier äußere Eckplätze |
| 13–15 | Fünf als nach innen gerichtetes Pentagon | Zehn Längsplätze plus drei bis fünf Zwischenplätze |

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

Der bestehende Chair-Durchmesser bleibt 50 cm. Die Zweiergruppe hält 10 cm Spalt
zwischen parallelen Längskanten (90 cm Mittelpunktabstand), ohne Tischüberlappung. Die äußeren Sitzflächen sind
kanonische, 50 cm tiefe Streifen. Gemeinsame Stirnflächen werden mit derselben
Geometriefunktion über beide Tischhälften und den Spalt erzeugt (170 cm Gesamtbreite). Ein Stirn-Chair darf beide
Tischhälften rein tangieren. Zwischen den verbundenen Tischen liegt keine
Sitz-/Bewegungsfläche. Vierer-/Fünferringe behalten beide bestehenden
Längsseiten-Sitz-/Bewegungsstreifen; Chairs liegen außen.

Die vier äußeren Eckplätze liegen zwischen benachbarten Tischen und sind jeweils
einem Tisch fest zugeordnet. Ihre Sitzflächen entstehen aus den äußeren
Stützpunkten der kanonischen Tischkonturen: Auf deren virtueller Verbindungskante
liegt ein bestehender 50-cm-Sitzstreifen. Es entsteht kein zusätzlicher physischer
Tisch. Reine Randkontakte dieser Fläche an den beiden Stützpunkten sind erlaubt;
positive Flächenüberlappung mit Tischen und Chair-/Tischkollisionen bleiben verboten.
Alle vier Eckflächen werden schon für die ganze Stufe 7–12 innerhalb der ROI und
gegen Parktische geprüft. Bei zehn Personen werden zuerst gegenüberliegende Ecken
belegt, anschließend die übrigen. Keine Längsseite erhält in dieser Stufe drei Chairs.
Bei zwölf: acht Längs- und vier Eckplätze; Tischidentitäten und Posen bleiben innerhalb
der Stufe stabil. Die zusätzlichen Eckrollen werden ausschließlich in der
Discussion-Vorschau verwendet.

Im Pentagon bleiben zwei reguläre Plätze je äußerer Längsseite. Die übrigen
drei bis fünf Personen sitzen zwischen Nachbartischen. Die Zwischenflächen
werden aus den Mittelpunkten der einander zugewandten kanonischen Stirnkanten
und demselben nach außen gerichteten 50-cm-Streifen erzeugt. Diese Öffnung definiert zunächst die freie Sitzfläche. Auf Johannes’ Wunsch
werden Zwischen-Chair und vollständige Sitzfläche anschließend gemeinsam nach
außen verschoben, bis der Chair-Mittelpunkt auf dem Kreis der regulären
Längsseiten-Chairs liegt. Dessen Radius wird aus der kanonischen Sitzgeometrie
abgeleitet; nominal rund 225,5 cm bei rund 26,5 cm zusätzlicher Verschiebung.
Die bestehende Phasen-/Mittelpunktsuche prüft die mitverschobenen Flächen und
vollen Chair-Kreise erneut innerhalb der ROI. Gegenüber dem vorherigen Ziel
benötigt die aktuelle Live-Ausgangsszene dafür eine gemeinsame Anpassung von
höchstens 3,2 cm Tischverschiebung und 1° Drehung. Bei 15 Personen sind alle fünf Zwischenplätze
belegt; bei 13/14 werden die Plätze zunächst über den Ring verteilt. Identitäten,
Tischposen und die zehn Längsplätze bleiben innerhalb 13–15 stabil.

Die bestehende, von Johannes akzeptierte Toleranz von maximal 0,51 cm gilt
weiterhin ausschließlich für abgerundete Sitzflächenecken. Die neuen
Pentagon-Zwischenplätze überschreiten die polygonalisierte Rundung in der
nominalen Probe um rund 0,12 cm. Gerade Grenzen, vollständige Tisch-/Chair-ROI
und fremde Tisch-/Chair-Kollisionen bleiben strikt. Die eigene Tischkante darf
vorläufig tangiert werden.

Für die Ringstufen werden bestehende Synthese-/Ringfunktionen wiederverwendet.
Bei vier aktiven und einem Parktisch prüft die begrenzte Suche zusätzlich
Rotationen in 15°-Schritten mit gemeinsamem Mittelpunktversatz; der bisherige
bewegungsoptimierte Ring bleibt ebenfalls Kandidat. Alle Kandidaten durchlaufen
die gemeinsame Geometrieprüfung. Der Fünferring nutzt die bestehende feinere
Phasen-/Mittelpunktsuche einschließlich Chair-Grenzen. Die Parkplanung nutzt
den vorhandenen kompakten Parkhelfer. Begrenzte Caches liefern unabhängige
Ergebniskopien; gleiche Parkgeometrie innerhalb einer Suche wird wiederverwendet.

Stärke 0 erhält exakte Source-Posen ohne Chairs. Johannes erlaubt am 2026-10-15
lockerere Zwischenformen: Positive Teilstärken interpolieren einzelne Tischposen
entlang des kürzesten Rotationswegs. Die vollständige Zweier-/Rechteck-/Pentagonform
gilt bei 100 %. Die zuvor starre Reparatur der Gesamtform ist abgelöst.

Die bereits kanonisch abgeleitete maximale Stufenbelegung 6/12/15 wird pro Tisch
mitgeführt. Long-, Stirn- und Eck-Chairs behalten Tisch-/Seat-ID und lokale
Position zur zugeordneten Tischhälfte; die vollständigen Sitzpolygone werden
mit demselben Einzeltransform transportiert. Gemeinsame Stirn-/Eckflächen
müssen in Zwischenformen dadurch nicht mehr beide bisherigen Nachbartische
verbinden. Ihre nutzbare Geometrie am Besitzer bleibt erhalten. Die zuvor
vereinbarte Rundungstoleranz wird weder erweitert noch neu angewandt.

Jede positive Ausgabe prüft alle reservierten Chair-Kreise, Sitzflächen und
Tischkonturen auf ROI und Fremdkollisionen. Beide kanonischen Längsseiten-
Bewegungsstreifen der Ringstufen bleiben frei. Parktische behalten ihre bereits
zugeordnete ROI-Randseite und mindestens 60 cm Abstand. Die Reparatur nähert
zuerst die Zwischenposen an; falls nötig beginnt sie von einer gültigen Form
und verbessert einzelne Tischpositionen und Drehungen in zwei begrenzten
Durchläufen. Bewertet wird die Abweichung kanonischer Tischkonturpunkte von
der angefragten Pose. Keine neue Slotzuordnung oder neue aktive/geparkte Auswahl.

Die harten Sitz-/Bewegungsflächen begrenzen die Wirkung insbesondere bei hoher
Belegung weiterhin. Der Regler ist keine Garantie linearer Bewegung; physische
Umbauwege sind damit nicht kollisionsfrei nachgewiesen. Wiederholte Anfragen
verwenden den bestehenden Cache mit maximal 32 unabhängigen Ergebniskopien.
Der normale Modus ohne Opt-in und isoliertes Tracking behalten ihre bisherigen Wege.

## Offline-Nachweis

Aktualisierung lockerer Zwischenformen am 2026-10-15: 26 fokussierte Tests
(Discussion-Chairs und Rect-Templates) sowie 210 Fälle aus zwei Ausgangsszenen
bestanden: Counts 1–15 bei 0/1/25/50/75/99/100 %. Gemeinsame Geometrie, volle
reservierte Belegung, Rollen/Seat-IDs, Scene Order einschließlich umgekehrter
Eingabe, Determinismus, Cache-Kopien und exakte Source bei 0 geprüft.
Regressionen prüfen ausdrücklich veränderte relative Tischabstände in allen
drei Stufen; eine reine gemeinsame Drehung/Verschiebung würde den Test nicht
bestehen. Manipulierte Chairs, Sitzpolygone, ROI- und Tischkollisionen werden
weiter abgelehnt. Die 100-%-Ausgabe bleibt identisch.

Lokale Quellen, Checks und visueller Vergleich für die Live-Ausgangsszene:
`data/aisi/debug/discussion_relaxed_strength_2026-10-15/`. Bei sechs Personen
sinkt der gesamte Tischweg dort von rund 365 cm (100 %) auf 187 cm (25 %).
Bei zehn und fünfzehn bleiben wegen der vollständigen Sitz-/Bewegungsflächen
kleinere Änderungen; im Plot sind auch die relativen Tischposen verändert.
Messzeiten pro Fall einschließlich zusätzlicher Prüfungen und umgekehrter
Scene Order stehen in `checks.json`; die gesamte Live-Latenz ist noch zu prüfen.

Reproduktion ohne OSC-Netzwerkversand:

```sh
MPLCONFIGDIR=/tmp/aisi-mpl PYTHONPATH=src:. .venv/bin/python \
  scripts/validate_discussion_strength.py \
  --scene data/aisi/scenes/simulated/live_scene.json \
  --output data/aisi/debug/discussion_relaxed_strength_2026-10-15
```

Die folgenden Nachweise betreffen die unveränderte vollständige Zielform:

- 30 Fälle: Editor- und aktuelle Live-Ausgangsszene, jeweils fünf Rect-Tische
  und alle Teilnehmerzahlen 1–15. Quellen beim Lauf lokal eingefroren.
  Für 13–15 zusätzlich identischer Mittelpunktabstand aller Chair-Kreise zum
  Ringzentrum geprüft (Abweichung kleiner als 0,000001 cm).
- Gemeinsame ROI-/Kollisionsprüfung einschließlich Parktischen, 60-cm-Abstand,
  Übergänge 6→7 und 12→13, deterministische Wiederholung und umgekehrte Scene Order.
- 22 fokussierte Tests zu Eck-/Zwischenplätzen: Discussion-Chairs und unveränderte
  Rect-Templates. Auch fehlende Tische, Kapazität,
  Tangenz versus Durchdringung, Cache-Kopien, Stärke 0 und Teilstärken geprüft.
- OSC-Ausgabe lokal aufgezeichnet, ohne Netzwerkversand. Bestehende Adressen,
  Chair-Radius 25 als Float, Tischanzahl und Source-/Target-Reihenfolge beibehalten.
- Kontrollplots mit 4, 6, 12 und 15 Personen für beide Ausgangsszenen visuell geprüft;
  Eck-/Zwischenplätze violett hervorgehoben, gemeinsamer Pentagon-Chair-Kreis
  gelb gestrichelt eingezeichnet.
  Lokale Artefakte: `data/aisi/debug/discussion_pentagon_chair_circle_2026-10-15/`.

Reproduktion:

```sh
MPLCONFIGDIR=/tmp/aisi-mpl PYTHONPATH=src .venv/bin/python \
  scripts/validate_discussion_participants.py \
  --scene data/aisi/scenes/simulated/live_scene.json \
  --output data/aisi/debug/discussion_pentagon_chair_circle_2026-10-15
```

Der frühere 90-Fälle-Nachweis vom 2026-10-09 betraf den vorherigen festen Ring.
Der historische Größenvergleich bleibt über `scripts/plot_discussion_chair_fit.py`
reproduzierbar; er zeigt die inzwischen ersetzte Dreier-Längsseitenbelegung.
Der Chair-Durchmesser bleibt bei 50 cm.

## Floor-Naht der Zweiergruppe

31 fokussierte Tests und ein erneuter Offline-Lauf mit 30 Fällen bestanden.
Johannes ersetzt am 2026-10-15 die Konturbeschneidung durch einen physischen
Spalt von 10 cm. Die ursprünglichen 170 × 90 cm Floor-Konturen bleiben vollständig;
ihre Außenkanten treffen sich im Spalt. Die bereits angewandte Naht-Reparatur ist
manuell zurückzunehmen. Danach Sender neu starten und neu generieren.
[Textport-Anleitung](TOUCHDESIGNER_JOINED_FLOOR_CONTOURS.md).

## Offene Prüfung

Nach Sender-Neustart zusätzlich die Reglerwerte 0/25/50/75/100 % live prüfen.
Discussion-Chairs bei 100 % einzeln in Room Editor, Learning-Format-Interface
und TouchDesigner prüfen, besonders 4/5/6 Personen, Eckbelegung bei 9–12, Zwischenplätze bei 13–15 und beide Topologieübergänge
und die Parktische. Anschließend kurzer Formatwechsel-Check. Eigene
Tischkantentangenz und Rundungsüberstand physisch beurteilen.
Keine TD-Fernsteuerung, automatische Speicherung oder physische
Projektionsvalidierung erfolgt.
