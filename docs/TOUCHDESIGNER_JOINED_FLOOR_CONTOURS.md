# Discussion-Zweiergruppe: ursprüngliche Floor-Konturen und 10-cm-Spalt

Stand: 2026-10-15. Johannes ersetzt die Konturbeschneidung durch 10 cm
physischen Abstand zwischen den parallelen Tischlängskanten.

## Aktueller Stand

Bei 1–6 Personen stehen die beiden 160 × 80 cm Rect-Tische mit 90 cm
Mittelpunktabstand. Die ursprünglichen 170 × 90 cm Floor-Konturen bleiben
vollständig; ihre Außenkanten treffen sich im Spalt. Die 2,5 cm breiten Balken
liegen innerhalb ihrer Konturgrenzen, daher berühren sich zwei Balken und bilden
gemeinsam 5 cm Strichbreite. Sie werden nicht zu einem einzelnen Balken verschmolzen.
Die gemeinsamen Stirn-Sitzflächen überspannen beide Tischhälften samt Spalt,
also 170 cm. Außenplätze und Chair-Durchmesser bleiben unverändert.

Die frühere Reparatur beschnitt die gepaddeten Konturen bei exakt anliegenden
Tischen. Ihre erste Fassung entfernte die Innenkante; eine zweite ergänzte eine
geteilte Trennlinie. Beide Fassungen werden durch den Tischspalt abgelöst.
Der alte Reparaturhelfer bleibt ausschließlich für die rücknehmbare Migration
erhalten und soll für diese Discussion-Zweiergruppe nicht erneut angewandt werden.

## Manuelle Anwendung

Zuerst die bereits angewandte TD-Kontur-Reparatur aus ihrer im Graph gespeicherten
Rückfallkopie zurücknehmen. Dieser eigenständige Einstieg führt keine neue
Reparatur aus und benötigt keine Funktionen aus einer früheren Textport-Sitzung:

```python
exec(open('/Users/Johannes/dev/Promotion_Prototypen/AISI/td_builders/restore_aisi_joined_floor_contours.py').read())
```

Der Helfer prüft bekannte DAT-Fassungen und eigene Parameterseiten vor der
Rücknahme. Abweichende manuelle Änderungen werden nicht überschrieben.
Fehlt die Rückfallkopie, bricht er mit einer eindeutigen Meldung ab.
Er speichert keine `.toe` und erzwingt keinen Cook.

Anschließend den OSC-Sender mit dem aktualisierten Python-Code neu starten und
Discussion bei sechs Personen und 100 % neu generieren. Der neue Abstand kommt
aus dem Generator; die Rücknahme allein verschiebt keine Tische.

## Nachweis und offene Prüfung

31 fokussierte Tests bestanden (Discussion-Chairs, Rect-Templates und TD-Konturhelfer). Sie prüfen 10 cm Abstand der kanonischen physischen
Tischflächen, Kontakt der gepaddeten Konturgrenzen, Sitz-/Chair-Geometrie,
ROI, Parkabstände, Determinismus und Scene Order. Die Rücknahme ist sowohl
für die erste Reparatur als auch das Trennlinien-Update abgesichert.
Der erneute Offline-Lauf mit zwei Ausgangsszenen und Counts 1–15 bestand alle 30 Fälle.
Lokale Kontrollplots: `data/aisi/debug/discussion_pair_gap_2026-10-15/`.

Offen: manuelle Rücknahme im aktuellen TD-Graph und Live-Kontrolle bei 4/5/6
Personen sowie 6→7→6. Keine TD-Fernsteuerung, automatische Speicherung oder
physische Projektionsvalidierung. Study, Tracking, Tabletop, Masken und
Projektorkonfiguration bleiben unverändert.
