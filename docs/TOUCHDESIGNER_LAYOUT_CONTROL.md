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
Bei einem vorhandenen Kontroll-COMP aktualisiert derselbe Aufruf ausschließlich
die Render-Einstellungen und Geometrieauswahl seines `render_source_and_tabletop_motion` (Render TOP).
Alle Nodes bleiben erhalten; die Einstellungen werden aus `render_tabletop`
(Render TOP) übernommen. Bei Aufbaufehlern wird
nur der neu angelegte COMP zurückgenommen.
Die Operatortypen werden auch aus TD-Builtins aufgelöst, damit der manuelle
`exec`-Aufruf nicht ohne Ausgabe übersprungen wird.

Interne Operatoren:

- `select_existing_floor` (Select TOP) liest den unveränderten
  `null_floor_with_optional_synth_chairs` (Null TOP).
- `render_source_and_tabletop_motion` (Render TOP) übernimmt die bestehenden
  Tabletop-Render-Einstellungen und dessen Kamera. Es rendert ausschließlich
  vorhandene `table_source_geo` und `table_motion_line_tabletop_geo`
  (Geometry COMPs) der aktiven Rect-Items. Die Auswahl referenziert ausdrücklich
  die fünf unterstützten Slots `item1` bis `item5`; fehlende Slots werden
  übersprungen, später angelegte wieder berücksichtigt. Template, Chairs und Tabletop-Zielkonturen werden nicht zusätzlich
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
keine Targets/Templates; fehlende und später angelegte Slots werden berücksichtigt.
Die frühere Suche über alle direkten Kinder wurde durch die fünf konkreten
Item-Pfade ersetzt. Das vermeidet eine unnötig breite Referenz auf das gesamte
Layout-Netzwerk. Ob dadurch die vielen sichtbaren Referenzlinien verschwinden,
ist noch live zu prüfen; notwendige Referenzen bleiben bestehen.
Die Übernahme von `render_tabletop` am vorhandenen Kontroll-Renderer und ihr Rücknahmezustand wurden
ebenfalls offline geprüft.
Ein lokaler strukturgetreuer Mock prüft die Floor-/Kamerareferenzen, unveränderte
Parameter des vorhandenen Renderers, leere Lichtauswahl und Ablehnung einer
zweiten Erstellung. Diese Checks ersetzen kein TD-Rendering.

Der erste Live-Aufbau wurde bei `composite_control` abgebrochen: TOPs unterstützen
`setInput` hier nicht. Der Helfer ist auf das im Repository verwendete
`inputConnectors[index].connect(source)` korrigiert; der Fehlerpfad entfernt
ausschließlich den neu angelegten Kontroll-COMP. Der frühere Mock belegte nur
die Struktur und konnte die falsche API nicht erkennen. Johannes' Screenshot
zeigt inzwischen den angelegten Kontroll-COMP. Die kombinierte Bildausgabe und
die Reduktion der Referenzlinien sind noch nicht bestätigt. Nach Ausführung
`floor_tabletop_control` (Container COMP) bzw. `out_control` (Out TOP) ansehen:
Floor-Ziele und Chairs, blaue Source-Rechtecke und Tabletop-Motion-Pfeile müssen
raumgleich erscheinen. Keine physische Projektionskorrektheit behauptet.
Rücknahme: ausschließlich den neuen `floor_tabletop_control`-COMP löschen.
Die letzte Änderung des Kontroll-Renderers lässt sich im selben Textport
zurücknehmen:

```python
restore_control_renderer(_aisi_control_renderer_backup)
```

Am 2026-10-08 präzisiert: Der zusätzliche Render entspricht `render_tabletop`
(Render TOP) mit ausschließlich Source-Rechtecken und Tabletop-Motion-Pfeilen.
Zielrechtecke kommen nur aus dem bestehenden Floor-Bild. Der frühere Helfer
kopierte dafür fälschlich die Floor-Render-Einstellungen. Die Parameterübernahme
nutzt die dokumentierte [OP.copyParameters-Methode](https://docs.derivative.ca/OP_Class).
Syntax, Parameterübernahme, transparenter Hintergrund und Rücknahme sind offline
geprüft; Bildüberlagerung und Referenzlinien bleiben live zu bestätigen.

Johannes bestätigt am 2026-10-08 die kombinierte Kontrollansicht als passend.
Der Screenshot zeigt Floor-Ziele/Chairs mit blauen Source-Rechtecken und
Tabletop-Motion-Pfeilen. Eine Reduktion der Network-Referenzlinien und physische
Projektionskorrektheit sind damit nicht separat belegt.
