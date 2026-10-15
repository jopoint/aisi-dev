# AISI-Floor-Konturen an der gemeinsamen Tischkante

Stand: 2026-10-15. Manuelle TD-Anwendung noch offen.

## Befund

Johannes meldet bei der Discussion-Zweiergruppe überkreuzte Konturen in
`null_floor_with_optional_synth_chairs` (Null TOP). Die kanonischen physischen
Rect-Tische sind 160 × 80 cm groß und liegen mit 80 cm Mittelpunktabstand exakt
an ihrer gemeinsamen Längskante. Offline besteht keine positive Tischüberlappung.
Die vorhandenen Study-artigen Floor-Konturen sind 170 × 90 cm groß. Ihre
jeweiligen 5 cm Zugabe reichen über die gemeinsame Kante hinaus und ergeben
einen 10 cm breiten Überlappungsbereich. Die bisherigen Geometrieplots zeigten
physische Tischflächen und haben diesen Darstellungsfehler nicht sichtbar gemacht.

## Lokale Korrektur

`td_builders/repair_aisi_joined_floor_contours.py` aktualisiert ausschließlich
`aisi_table_visual_style` (Text DAT) und bindet `Joiningside` als neuen Parameter
an den bestehenden Floor-Kontur-SOPs (Script SOPs), einschließlich Template.
Die Floor-Balken werden an der physischen gemeinsamen Kante abgeschnitten.
Die innenliegenden Querstriche entfallen; die äußeren kurzen Kanten enden dort.
Physische Tischposen, Chair-Posen, Maße und OSC-Vertrag bleiben erhalten.

Die Erkennung verwendet vorhandene `tx`, `ty`, `rz` der
`table_target_floor_geo` (Geometry COMPs) mit bestehender Skalierung und
aktuellem `table/count`. Sie gilt nur im AISI-Modus für eine eindeutig exakt
anliegende Rect-Längskante. Ein realer Überlapp, Abstand, Versatz, gedrehte
Nachbarn, uneindeutige Nachbarn oder unpassende Skalierung werden nicht als
Naht versteckt. Nicht anliegende Tische behalten die vollständigen Konturen.
Study, Tracking, Tabletop, Masken und Projektorkonfiguration werden nicht geändert.
Die Abhängigkeit liegt ausdrücklich in einem SOP-Parameter, damit Layout- und
Moduswechsel eine Neuberechnung auslösen können. Kein Force-Cook.

Im Textport bei AISI / Discussion mit 1–6 Personen und 100 % ausführen:

```python
exec(open('/Users/Johannes/dev/Promotion_Prototypen/AISI/td_builders/repair_aisi_joined_floor_contours.py').read())
```

Der Helfer prüft zuerst alle bekannten Callback-Anbindungen und den bisherigen
Style-DAT. Abweichende manuelle Fassungen werden vor Änderungen abgelehnt.
Er meldet den tatsächlichen Projektnamen und die erkannten Nahtseiten.
Wiederholte Ausführung ist idempotent; keine `.toe` wird gespeichert.
Eine Rückfallkopie bleibt nur im laufenden Graph vorhanden. Rücknahme:

```python
restore_joined_floor_contours(op)
```

Bei Fehlern während der Installation werden die eigenen Änderungen zurückgenommen.
Später veränderte eigene Parameterseiten oder Style-Texte werden bei Rücknahme
nicht überschrieben. Grundlage ist die dokumentierte
[Script-SOP-Parameter-API](https://docs.derivative.ca/ScriptSOP_Class).

## Nachweis und offene Prüfung

- Zehn fokussierte Tests für kanonische Konturen, Kontakt-Erkennung,
  Drehungen, vorhandene OSC-Achsen, Modussperren, Legacy-/Scout-Fallback,
  idempotente Installation und Rücknahme einschließlich Fehlerfall bestanden.
- Der serialisierte Legacy-DAT ist bytegleich zum bisherigen Stand.
- 30 Offline-Fälle aus zwei Ausgangsszenen, Counts 1–15: jeweils nur die
  beiden verbundenen aktiven Tische bei 1–6 als Naht erkannt. Vierer-/Fünferringe
  bleiben bei dieser lokalen Korrektur unverändert.
- Physische Naht ohne Flächenüberlappung, bisherige Floor-Balken mit
  Überschneidung, korrigierte Balken ohne Überschneidung bei 0°, 37° und 90° geprüft.
- Lokaler Vorher-/Nachher-Plot:
  `data/aisi/debug/discussion_joined_floor_2026-10-15/floor_naht_vorher_nachher.png`.

Noch offen: Helfer im aktuellen manuellen Graph ausführen und die Floor-Naht,
Count-Wechsel 6→7→6 sowie Study-/Tracking-/Tabletop-Ausgaben visuell prüfen.
Es erfolgten keine TD-Fernsteuerung, Live-Anwendung, Speicherung oder physische
Projektionsvalidierung. Die Aussage betrifft diese gemeinsame Zweiergruppennaht,
keine allgemeine Überlappungsfreiheit sämtlicher gepaddeter Floor-Konturen.
