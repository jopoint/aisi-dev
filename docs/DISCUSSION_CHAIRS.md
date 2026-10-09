# Discussion-Chairs: visuelle Entscheidungsgrundlage

Stand: 2026-10-09. Die Implementierung ist noch offen; keine Änderung am
laufenden TD-Projekt, am produktiven Tischring oder an Sitzflächen.

Johannes erlaubt vorläufig reine Berührung an der eigenen Tischkante und
möchte bis zu drei Chairs pro Tisch beziehungsweise 15 Personen an fünf Tischen.
Der bisherige Radius synthetischer Chairs beträgt 25 cm. Die bestätigte äußere
Discussion-Sitzfläche ist 50 cm tief, mit bestehenden 30-cm-Eckrundungen.

Der Vergleich zeigt einen kanonischen Rect-Tisch (160 × 80 cm), die äußere
Sitzfläche und drei Chair-Mittelpunkte mit 52 cm Abstand. Bei 50 cm Durchmesser
beträgt die Überschreitung der polygonalisierten Rundung rund 0,51 cm; zwischen
benachbarten Chair-Kreisen verbleiben 2 cm. Mit 45 cm Durchmesser liegen alle
Kreise vollständig in der Fläche, mit rund 1,99 cm Mindestreserve und 7 cm
Chair-Abstand. Der 45-cm-Fall ist ein Vorschlag, keine bestätigte neue Größe.

Eine reduzierte Eckrundung wurde versuchsweise geprüft, lässt den bisherigen
Fünf-Tisch-Ring mit vollständigen Sitzflächen jedoch nicht mehr in die ROI
passen; die versuchsweisen Codeänderungen wurden vollständig zurückgenommen.
Die Größenentscheidung bleibt offen. Eine nominale Probe mit 45-cm-Kreisen
auf dem bestehenden Fünf-Tisch-Ring zeigt 15 vollständig enthaltene Kreise ohne
Chair-Kollisionen; die vollständige Implementierung/Integration steht aus.

Reproduktion:

```sh
PYTHONPATH=src .venv/bin/python scripts/plot_discussion_chair_fit.py \
  --output data/aisi/debug/discussion_chair_fit_2026-10-09
```

PNG/SVG/PDF und geometrischer Prüfbericht `fit.json` bleiben lokale
Debug-Artefakte. Der Plot wurde visuell geprüft; die enthaltenen Prüfungen
bestätigen den Überstand bei 50 cm und vollständige Einhaltung bei 45 cm.
Keine physische Sitz-/Bewegungs- oder Projektionsvalidierung.
