# Floor-/Tabletop-Kontrollansicht

Auftrag von Johannes am 2026-10-08: ein COMP unter `comp_layout_proposal`,
der den bestehenden Floor inklusive optionaler synthetischer Chairs mit den
blauen Tabletop-Source-Rechtecken und Tabletop-Motion-Pfeilen überlagert.

## Manueller Aufbau

Im TouchDesigner-Textport ausführen:

```python
exec(open('/Users/Johannes/dev/Promotion_Prototypen/AISI/td_builders/create_floor_tabletop_control.py').read())
```

Der Helfer prüft zuerst die vorhandenen Operatoren und erzeugt ausschließlich
`/project1/comp_layout_proposal/floor_tabletop_control` (Container COMP).
Ein bereits vorhandener gleichnamiger COMP wird erhalten und ausdrücklich
abgelehnt. Bei Aufbaufehlern wird nur der neu angelegte COMP zurückgenommen.
Die Operatortypen werden auch aus TD-Builtins aufgelöst, damit der manuelle
`exec`-Aufruf nicht ohne Ausgabe übersprungen wird.

Interne Operatoren:

- `select_existing_floor` (Select TOP) liest den unveränderten
  `null_floor_with_optional_synth_chairs` (Null TOP).
- `render_source_and_tabletop_motion` (Render TOP) übernimmt die bestehenden
  Floor-Render-Einstellungen und dieselbe Kamera. Es rendert ausschließlich
  vorhandene `table_source_geo` und `table_motion_line_tabletop_geo`
  (Geometry COMPs) der aktiven Rect-Items. Die dynamische Auswahl folgt neuen
  Instanzen; Template, Chairs und Tabletop-Zielkonturen werden nicht zusätzlich
  gerendert. Die vorhandenen Materialien, Geometrien und Sichtbarkeiten bleiben
  unverändert. Kamera und Lichter werden als absolute Referenzen aufgelöst.
- `composite_control` (Composite TOP) addiert Floor und diesen Overlay-Render.
- `out_control` (Out TOP) stellt das kombinierte Bild bereit.

Der Container zeigt `out_control` in seinem Operator-Viewer. Er wird nicht in
die Panel-Komposition des übergeordneten COMPs eingeblendet. Keine neue Kamera,
keine Tischkopie, keine Änderung an Masken, Homographien, Kalibrierung,
Projektoren, Study oder `comp_output`. Optionaler Chair-Schalter und aktuelle
Geometriesichtbarkeit gelten weiterhin. Kein Force-Cook und kein Speichern.

Die Render-Geometrieauswahl und Hintergrundparameter entsprechen der
[Render-TOP-Dokumentation](https://docs.derivative.ca/Render_TOP); der Panel-
Hintergrund ist ein [Background TOP des Container COMPs](https://docs.derivative.ca/Container_COMP).

## Prüfung und Stand

Syntax und dynamische Auswahl offline geprüft: nur Rect-Source-/Motion-Geometrien,
keine Targets/Templates; neu hinzukommende Items werden berücksichtigt.
Ein lokaler strukturgetreuer Mock prüft die Floor-/Kamerareferenzen, unveränderte
Parameter des vorhandenen Renderers, leere Lichtauswahl und Ablehnung einer
zweiten Erstellung. Diese Checks ersetzen kein TD-Rendering.

Der Helfer wurde noch nicht im laufenden Projekt ausgeführt. Nach Ausführung
`floor_tabletop_control` (Container COMP) bzw. `out_control` (Out TOP) ansehen:
Floor-Ziele und Chairs, blaue Source-Rechtecke und Tabletop-Motion-Pfeile müssen
raumgleich erscheinen. Keine physische Projektionskorrektheit behauptet.
Rücknahme: ausschließlich den neuen `floor_tabletop_control`-COMP löschen.
