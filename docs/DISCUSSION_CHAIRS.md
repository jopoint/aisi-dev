# Discussion-Chairs

Stand: 2026-10-09. Die synthetische Opt-in-Vorschau ist implementiert und offline
geprüft. Johannes bestätigt nach dem Größenvergleich den bisherigen Durchmesser
von 50 cm. Drei Chairs pro Rect-Tisch sind zulässig, damit fünf Tische maximal
15 Personen aufnehmen. Alle Tische bleiben aktiv; Teilnehmer werden möglichst
gleichmäßig verteilt. Zusätzliche Präsentationsrollen sind nicht eingeführt.

Chairs liegen auf der äußeren Längsseite des nach innen gerichteten Tischrings.
Bei drei Chairs beträgt ihr Mittelpunktabstand 52 cm und der Abstand zwischen
Kreisen 2 cm. Die bestehende kanonische Sitzfläche ist 50 cm tief und an den
äußeren Ecken mit 30 cm gerundet. Johannes akzeptiert den geplotteten Überstand
von rund 0,51 cm an diesen Rundungen. Die Prüfung erlaubt maximal 0,51 cm,
ausschließlich dort: Die geraden Begrenzungen bleiben für den vollen Kreis
verbindlich. Reine Tangenz an der eigenen Tischkante ist vorläufig erlaubt;
Überlappung mit dem Tisch sowie fremde Tisch-/Chair-Berührungen bleiben verboten.

Die volle Tisch- und Chair-Geometrie muss innerhalb der ROI bleiben. Beide
bestehenden Sitz-/Bewegungsflächen dürfen keine fremden Tische blockieren.
Die gemeinsame Fünf-Tisch-Phasen-/Mittelpunktsuche berücksichtigt bei Bedarf
zusätzlich die vollen Chair-Außenkanten. Tischradius, Flächenform, Koordinaten
und Source-Winkelreihenfolge bleiben erhalten. Ausgabe erfolgt in Scene Order;
kein zweiter globaler Slottausch. Begrenzte Caches liefern unabhängige Kopien.

Aktivierung über `adaptive_layout_preview=True` und ganzzahlige positive
`participants`. Anfragen über `3 × Tischanzahl` beziehungsweise 15 werden
explizit abgelehnt, ohne Kürzung oder Rückfall auf ein anderes Layout.
Bei Stärke 0 bleiben Source-Posen exakt und Chairs ausgeblendet. Teilstärken
verwenden die bestehende Blend-/Repair-Tischsynthese; ungeeignete gemeinsame
Chair-Geometrie wird ausdrücklich abgelehnt. Für die virtuelle Prüfung 100 %
verwenden. Normaler Modus und isoliertes Tracking behalten ihre bisherigen Wege.

## Offline-Nachweis

- 90 gemeinsame Fälle: Editor- und aktuelle Live-Ausgangsszene, ein bis fünf
  Rect-Tische, jeweils alle Teilnehmerzahlen von 1 bis `3 × Tischanzahl`.
- 35 fokussierte Tests: Discussion-Chairs, bestehende Rect-Templates,
  Input-Geometrie und Groupwork-Vorschau. Counts, kapazitive Ablehnung,
  Identität/Scene Order, Determinismus, Cache-Isolation, Tangenz versus
  Durchdringung, Rundungsgrenzen und lokale OSC-Aufzeichnung eingeschlossen.
- Bestehende OSC-Chair-Adressen und Float-Radius 25 cm beibehalten;
  ausgeblendete Chairs mit Radius 0. Kein Netzwerkversand im Check.
- Lokale Plots und eingefrorene Prüfquellen:
  `data/aisi/debug/discussion_chairs_validation_2026-10-09/`.

Der Größenvergleich ist weiterhin reproduzierbar:

```sh
PYTHONPATH=src .venv/bin/python scripts/plot_discussion_chair_fit.py \
  --output data/aisi/debug/discussion_chair_fit_2026-10-09
```

Die 45-cm-Alternative ist verworfen; die bestehende Größe bleibt erhalten.
PNG/SVG/PDF und Prüfberichte bleiben lokale Debug-Artefakte.

## Offene Prüfung

Discussion-Chairs bei 100 % einzeln in Room Editor, Learning-Format-Interface
und TouchDesigner prüfen; anschließend kurzer Formatwechsel-Check.
Tischkantentangenz und Rundungsüberstand physisch beurteilen. Keine automatische
TD-Änderung oder Speicherung und keine physische Projektionsvalidierung erfolgt.
