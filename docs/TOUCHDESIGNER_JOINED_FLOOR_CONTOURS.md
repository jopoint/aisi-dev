# AISI-Floor-Konturen an der gemeinsamen Tischkante

Stand: 2026-10-15. Erste Fassung von Johannes live ausgeführt; aktualisierte Trennlinie noch manuell anzuwenden.

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
Die überstehenden innenliegenden Querstriche entfallen; die äußeren kurzen Kanten enden dort.
Auf der physischen Naht bleibt eine gemeinsame gestrichelte Trennlinie sichtbar.
Jeder Tisch zeichnet die halbe Strichbreite auf seiner Seite, zusammen 2,5 cm
wie die vorhandenen Konturen. Die beiden Tischobjekte bleiben dadurch visuell
unterscheidbar. Die erste Fassung hatte diese Linie vollständig entfernt;
Johannes meldete daraufhin den Eindruck eines einzigen Tisches.
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
Die erste Fassung kann direkt durch erneute Ausführung desselben Befehls
aktualisiert werden; die ursprüngliche Rückfallkopie bleibt erhalten.
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

- Zwölf fokussierte Tests für kanonische Konturen, Kontakt-Erkennung,
  Drehungen, vorhandene OSC-Achsen, Modussperren, Legacy-/Scout-Fallback,
  idempotente Installation, Upgrade von der bereits angewendeten Fassung und
  Rücknahme einschließlich Fehlerfall bestanden. Eine gemeinsame gestrichelte
  Linie mit voller 2,5-cm-Strichbreite aus zwei überschneidungsfreien Hälften geprüft.
- Der ursprüngliche Legacy-DAT und die erste Naht-Fassung sind bytegleich
  rekonstruierbar und werden beim Upgrade erkannt.
- 30 Offline-Fälle aus zwei Ausgangsszenen, Counts 1–15: jeweils nur die
  beiden verbundenen aktiven Tische bei 1–6 als Naht erkannt. Vierer-/Fünferringe
  bleiben bei dieser lokalen Korrektur unverändert.
- Physische Naht ohne Flächenüberlappung, bisherige Floor-Balken mit
  Überschneidung, korrigierte Balken ohne Überschneidung bei 0°, 37° und 90° geprüft.
- Neuer lokaler Vergleich: ursprüngliche Überkreuzung, erste Fassung ohne
  Trennlinie und aktuelle gemeinsame Trennlinie. Physische Tischflächen werden
  im Plot ohne eigene Kontur gezeichnet, damit keine zusätzliche graue Linie
  eine fehlende Floor-Trennlinie verdeckt:
  `data/aisi/debug/discussion_joined_floor_separator_2026-10-15/gemeinsame_trennlinie.png`.

Noch offen: aktualisierten Helfer im aktuellen manuellen Graph erneut ausführen
und die Unterscheidbarkeit beider Tische an der Floor-Naht,
Count-Wechsel 6→7→6 sowie Study-/Tracking-/Tabletop-Ausgaben visuell prüfen.
Die erste Fassung ist laut Johannes live ausgeführt. Die ergänzte gemeinsame
Trennlinie ist offline geprüft, noch nicht live bestätigt. Es erfolgten keine
TD-Fernsteuerung, automatische Speicherung oder physische Projektionsvalidierung. Die Aussage betrifft diese gemeinsame Zweiergruppennaht,
keine allgemeine Überlappungsfreiheit sämtlicher gepaddeter Floor-Konturen.
