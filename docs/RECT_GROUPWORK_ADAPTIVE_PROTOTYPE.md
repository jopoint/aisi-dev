# Rect Groupwork — quelladaptiver Suchkern

Status: virtuell geprüft, fachlich bestätigt und produktiv umgesetzt
Geltungsbereich: Entscheidungsgrundlage und gemeinsame Geometrie für die
produktive Rect-Groupwork-Synthese

## Verworfenes Modell

Starre absolute Zielpositionen, orthogonale Zielwinkel und die Bindung von
Pair-/Singleton-Rollen an die sortierte `table_id` sind verworfen. Die frühere
Auswertung bleibt ausschließlich als negativer Regression-Case erhalten.

## Suchmodell

Für Rect-Counts 2–5 enumeriert der Prototyp jede Partition in Paare und bei
ungerader Anzahl einen Singleton. Paare entstehen lokal um ihre Ausgangstische;
Gruppenmittelpunkt und Winkel werden aus der Quellgeometrie abgeleitet und mit
nicht gerasterten, reellwertigen lokalen Winkel-/Positionsschritten verfeinert.
Beide Mitgliederzuordnungen pro Pair werden geprüft.

Die bestätigte Clearance-Semantik ist asymmetrisch nach Inseltyp: Ein Singleton
erhält zwei vollständige Sitz-/Bewegungsstreifen mit exakt `60 cm` Tiefe über
die komplette Breite seiner Längsseiten; an den Stirnseiten liegen keine
Sitzflächen. Die beiden dem Tisch abgewandten Ecken jedes Streifens sind mit
`30 cm` Radius abgerundet. Ein Pair erhält eine um seine gemeinsame Geometrie gelegte,
elliptische `60 cm`-Clearance. Damit werden Pair-Ecken weniger stark als bei
einer quadratischen Hülle gewichtet und freie Drehwinkel bleiben möglich. Alle
Flächen liegen vollständig innerhalb der ROI.

Die Zielrotation eines Pairs erhält die axiale mittlere Orientierung seiner
beiden Source-Tische als starke Präferenz. Die räumliche Verbindungsachse der
Source-Zentren bestimmt die Zielrotation nicht allein. Die lokale Vorauswahl
erhält orientierungstreue Außenvarianten, damit sie eine valide globale
Pair-/Singleton-Partition nicht vorzeitig verwirft.

Das bewegungsminimale Profil wählt lexikographisch:

1. keine Overlap-, ROI-, Clearance- oder gerichtete-Zonen-außerhalb-ROI-Verletzung;
2. minimale maximale Verschiebung eines Tisches;
3. minimale Gesamtverschiebung;
4. minimale gesamte Rotationsänderung;
5. keine gekreuzten Zuordnungsvektoren, wenn gleichwertig oder besser.

Für die fachliche Bewertung erzeugt der Prototyp zusätzlich ein **aggressives
Clearance-Profil**: Es minimiert ohne Bewegungsbudget zuerst die gesamte
Überlappungsfläche von Sitz-/Bewegungszonen. Bei gleicher Überlappung minimiert
es maximale und gesamte Verschiebung, dann Rotation und Kreuzungen, und
maximiert erst danach den kleinsten Inselabstand. Das frühere Profil mit
`+50 cm`-Bewegungsbudget bleibt als technische Vergleichsoption verfügbar, ist
aber nicht die dargestellte Empfehlung.

Ein Singleton behält zunächst exakt seine Ausgangspose und wird nur für harte
Geometriebedingungen verschoben. `table_id` bleibt Identität; die Ausgabe kehrt
in die ursprüngliche Scene Order zurück.

## Regression-Ergebnis

Die Count-2–5-Szenen bleiben Regression-Cases. Die aktuellen, nicht
versionierten Plots und die zugehörige `decision_summary.json` dokumentieren
Pairings, Source-to-Target-Vektoren, Einzelverschiebungen, Winkel,
Gesamtmetriken und den minimalen Inselabstand. Für die aggressive
Clearance-Auswahl ist eine Zonenüberlappung von `0 cm²` für Count 3 und Count 5
automatisch getestet.

## Reproduktion

```bash
.venv/bin/python scripts/analyze_rect_groupwork_adaptive_prototype.py
```

Erzeugt werden ausschließlich diese unversionierten Prüfartefakte:

- `data/aisi/debug/rect_groupwork_adaptive_prototype/rect_groupwork_adaptive_count3.png`
- `data/aisi/debug/rect_groupwork_adaptive_prototype/rect_groupwork_adaptive_count5.png`
- `data/aisi/debug/rect_groupwork_adaptive_prototype/decision_summary.json`

## Verifiziert

- alle Partitionen für Counts 2–5 werden enumeriert;
- Rotations- und Translationsäquivarianz gilt außerhalb aktiver ROI-Grenzen;
- geometrische Ergebnisse hängen nicht von der `table_id`-Sortierung ab;
- identische Eingabe liefert identisches Ergebnis;
- die kanonischen Overlap- und ROI-Prüfungen sowie alle Singleton-Streifen und
  Pair-Ellipsen innerhalb der ROI bestehen;
- keine andere Arbeitsinsel diese Sitz-/Bewegungsflächen mit positiver Fläche
  schneidet; genau `60 cm` Abstand bleibt zulässig.

## Bestätigter und produktiver Stand

Die lokalen frei gedrehten Pairings, die Singleton-Streifen, die Pair-Ellipsen
und die aggressive überlappungsfreie Count-5-Auswahl sind fachlich bestätigt.
Die Clearance-Semantik und der Pair-Seam sind damit produktiv festgelegt. Die
Learning-Format-Steuerung, der Simulationsadapter und der lokale OSC-Ausgang
sind gegen die Count-5-Regression geprüft. Offen bleiben die interaktive
Room-Editor-/TouchDesigner-Prüfung und die physische Raumvalidierung.
