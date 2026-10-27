# Motion: Start, Status und Wiederanlauf

Stand: 2026-10-27. Funktionaler Web-Anschluss installiert; Johannes meldet alle
Systemtests abgeschlossen. Abschließende Standard-Konsolidierung nächster Block.
Untertisch-Versuch bleibt pausiert.

Aktueller gesicherter Stand und Nachweisgrenzen:
[Motion-Checkpoint](MOTION_CHECKPOINT_20261027.md). Nachfolgende Trial-Anleitungen
sind historische/gezielte Installationshilfen, nicht blind erneut ausführen.

## Trial: Haken bis alle Tische fertig sind

`update_motion_group_success.py` ergänzt Runtime und Shader minimal: Haken
erscheinen nach vollständigem Reveal auch an anfangs richtig stehenden Tischen,
bleiben bis zur letzten Ankunft, anschließend gemeinsam 1 s sichtbar und
0,32 s Reverse-Pop. Bestehende Wiederaufnahme-Hysterese bleibt erhalten;
Tracking-/Freigabeausfälle pausieren den Anzeigezustand. Ziele/Chairs/Revision,
Kalibrierung und Masken unverändert. Native Installation bestanden, gemeinsamer
Zweitisch-Abschluss im Raum ausdrücklich bestätigt; Gesamtprüfung abgeschlossen
laut Johannes (siehe Checkpoint, keine fehlenden Einzelmessungen ergänzen).

Zwei getrennte Textport-Einträge:

```python
import json
from td_builders import update_motion_group_success as group_success
print(json.dumps(group_success.prepare(op), ensure_ascii=False, indent=2))
```

```python
print(json.dumps(group_success.install(op), ensure_ascii=False, indent=2))
```

Nach Wiederaufnahme von TD separat `live_output.verify(op)` ausführen. Dann
frühe und letzte Ankunft, anfangs korrekte Tische, kurze Verdeckung und erneute
Guidance testen. Aufploppen/Alpha/Grün bleiben wie abgenommen. Eigener Rückweg
`group_success.rollback(op)` stellt beide DATs nur bei unverändertem eigenem
Installationshash wieder her. Nichts automatisch speichern.

## Trial: gestrichelte weiße Zielkontur

Zwischenauftrag nach positiver schneller Groupwork-Wiederholung:
`update_motion_target_dashes.py` ersetzt nur die Zielzeichnung im tatsächlichen
Motion-Shader. Voreinstellung 5 cm breites Innenband, 14 gleichmäßige Striche
mit 74 % Strichanteil; gleiche zielgebundene Umfangsphase auf Boden/Tabletop,
abgerundeter ursprünglicher Außenumriss erhalten. Keine weiße Vollfüllung.
Feedback-Funktion und Clip auf den vollen Ziel-Footprint bleiben gleich;
Navigation, Zielhilfen, Erfolg und weiche Wiedereinblendung werden erhalten.
Die Zielhilfen werden im offenen Inneren weiß sichtbar. Layout-/Chair-Daten,
Revision, Masken und Kalibrierung werden nicht geändert.

Passiver Textport-Start:

```python
import json
from td_builders import update_motion_target_dashes as target_dashes
print(json.dumps(target_dashes.prepare(op), ensure_ascii=False, indent=2))
```

Bei `prepared: true` in separatem Eintrag:

```python
print(json.dumps(target_dashes.install(op), ensure_ascii=False, indent=2))
```

Vor Installation native GPU-Prüfung: 0/33/90 Grad, offene Innenfläche und
Strichlücken, kein Überschreiten des alten Footprints, passende sichtbare Kontur
auf beiden Oberflächen, erhaltener Feedback-Beitrag im offenen Zentrum und
weiterhin Begrenzung auf den vollen Ziel-Footprint. Erfolg und Redisplay prüfen.
Isolierte WebGL-Kompilierung und erzeugte Code-Vorschau vorher bestanden;
diese ersetzen den tatsächlichen TD-/Projektornachweis nicht.

Nach Installation ohne neue Layoutberechnung im Raum betrachten; bei Bedarf
einen Tisch aus seiner Zielposition bewegen. Keine neue Aktivierung erforderlich,
Installation startet keine neue Welle. Erst nach positiver Abnahme manuell in
TD speichern. Rücknahme: `target_dashes.rollback(op)`. Trial noch nicht als
gestalterischer Standard oder physisch bestanden verbucht.

## Groupwork-Berechnungsdauer

Unter Diagnose steht nach jeder Aktivierung die reine Generatorzeit in Sekunden
(auch nach einem Fehler). Sie ist von der anschließenden automatischen TD-
Freigabe und Reveal-Dauer getrennt; im Hauptbereich keine neue technische Zeile.

Gemeldeter Fall fünf Tische/15 Teilnehmende/drei Gruppen: Wartezeit um eine
Minute im Generator mit Aktivierungs-nahen Kameraposen reproduziert, 52,406 s.
Anfrageinternes Wiederverwenden identischer Optionen und kanonischer
Geometrieprüfungen reduziert denselben Offline-Fall auf 10,162 s, bei exakt
gleichen Zielen/Chairs und unveränderten Regeln. Kein fester Laufzeitwert für
andere Raumanordnungen. Controller aktualisiert; zum Live-Nachweis erneut
explizit aktivieren. Keine automatische Berechnung oder Änderung von Kalibrierung.

## Vorbereitet: Chairs mit derselben Reveal-Welle

Nach bestandenem Input-Zweitischfall meldet Johannes vorzeitig sichtbare
Chair-Kreise. Der Motion-Shader verwendet bereits die zusätzliche visuelle
Uhr, der Chair-Shader bislang die alte globale Uhr. Gezielter Patch
`update_motion_chair_reveal.py`: vor visuell bestätigter Freigabe transparent,
danach gleiche drei Sekunden und radiale Einblendung wie die Motion-Welle.
Markerfreie Legacy-/Simulationsdaten behalten das bisherige Verhalten.
Positionen, Radien, CPU-State, Engine/Revision und Masken bleiben erhalten.

Vorbereitung verwendet die tatsächlich geöffneten Chair-/Motion-DATs und
verlangt bereits installierte visuelle Reveal-Uhr. Eigene Probe mit zwei
synthetischen State-Eingängen und sechs Chairs. GPU prüft fünf Zeiten:
vor Freigabe RGBA-null, gemeinsamer Reveal pixelgleich zur bisherigen Chair-
Darstellung bei entsprechendem Alter, Legacy-State unverändert. Erst danach
Chair-Shader austauschen und ausschließlich seinen `chair_owned`-Texthash
aktualisieren; Rücknahme erhält Originaltext/-Snapshot. Nichts speichern.

Textport:

```python
import json
from td_builders import update_motion_chair_reveal as chair_reveal
print(json.dumps(chair_reveal.prepare(op), ensure_ascii=False, indent=2))
```

Bei `prepared: true` in separatem Eintrag:

```python
print(json.dumps(chair_reveal.install(op), ensure_ascii=False, indent=2))
```

Danach nächste bewusste Vorschlagsaktivierung in der UI beobachten. Vor der
Welle dürfen keine Chairs sichtbar sein; sie erscheinen, wenn die gemeinsame
Welle ihre Position erreicht. Rücknahme: `chair_reveal.rollback(op)`.
Noch kein TD-/GPU-/Raumnachweis dieses Patches behauptet.

## Aktuelle Oberfläche: Format → Einstellungen → Aktivieren

Die grafisch überarbeitete Motion-Web-UI läuft weiterhin auf
<http://127.0.0.1:8080>. Drei Formatkarten zeigen die Auswahl. Darunter stehen
Teilnehmende und nur die zum Format passenden Felder: Gruppen bei Groupwork,
Präsentationsseite bei Input. Anzeige-Schalter für Stühle/Personen bleiben
erhalten. Es gibt einen primären Aktivierungsbutton und einen kompakten Status.
Anleitungen, IDs und technische Zustände stehen nicht mehr dauerhaft im
Hauptbereich; Details und Generatoroption sind unter Diagnose eingeklappt.

Änderungen werden ohne Seitenneuladen gespeichert, aber weiterhin erst durch
bewusste Vorschlagsaktivierung produktiv. UI-Anfragen laufen geordnet, damit
die Aktivierung die vorher gespeicherten Einstellungen verwendet. Fehler bei
Speicherung und fehlende Kameradaten bleiben sichtbar. Die bestehende
Server-/Motion-/TD-Sicherheitslogik ist unverändert.

UI ist als lokale HTML/CSS/JS-Dateien paketiert, ohne externe Ressourcen oder
neue Dienste. Künftige reine Asset-Änderungen benötigen nur Seitenneuladen;
die erstmalige Einbindung erforderte einen kontrollierten Webcontrollerwechsel.
Dieser wurde nach bestätigter automatischer TD-Sperre ausgeführt, Vision und
andere Dienste blieben laufen. Danach einmal Vorschlag aktivieren. Noch kein
Benutzer-Sichtbefund für das neue Design; Browserdarstellung bei Desktop und
390-px-Mobilbreite sowie Bediensemantik sind geprüft. Tests: 386 Motion-Fälle
bestanden, sieben optionale GPU-Fälle übersprungen; sechs UI-/Serverfälle und
isolierter Headless-Browsertest bestanden. Tatsächliche neue Seite danach
lesend über HTTP und Headless-Browser geprüft, keine JS-Fehler.

Reveal-Folgebefund: Johannes bestätigt den neuen Reveal-Patch inzwischen als
vollständig/flüssig nach Freigabe, mit festen Zielen/Chairs. Dessen manuelle
TD-Speicherung wurde nicht erneut bestätigt. UI-Aktualisierung speichert TD nicht.

## Vorbereitet: volle Reveal-Welle nach Prüfungen

`update_motion_visual_reveal.py` trennt den visuellen Start vom Empfang der
neuen Layoutrevision. Die bisherige Uhr und alle Tisch-State-Zeilen bleiben
unverändert. Ein zusätzlicher bisher unbenutzter Texel `[5,1]` übermittelt
visuelle Sekunden, Freigabe und Versionsmarker. Nur der Motion-Shader verwendet
ihn; Chair-Shader und Maskenzweige behalten ihre bisherigen Eingänge. Bis
`phase: active` und exakt passender Sitzung/Revision bleibt der Motion-Content
verborgen, danach läuft der bisherige Reveal über volle drei Sekunden.

Die Prüfung nach dem Einschalten geschieht somit vor dem sichtbaren Reveal.
Im stabilen aktiven Zustand führt die Automatik keine weiteren vollständigen
GPU-Readbacks aus. Eine manuelle Vollprüfung während der sichtbaren Animation
kann weiterhin Frames blockieren; den Sichttest ohne parallele Textport-Prüfung
durchführen. Andere Ursachen niedriger Dauerframerate bleiben separat zu messen.

Keine erneute Welle nach kurzer Verdeckung/Study-Rückkehr derselben Revision.
Installation setzt weder Engine noch Revision zurück und spielt das bestehende
Layout nicht erneut ab. Rücknahme stellt beide tatsächlichen DAT-Texte wieder
her. Kalibrierung, Maskierung, Layout-/Chair-Daten und automatischer Freigabe-
Nachweis bleiben erhalten. Zehn fokussierte Offline-Tests bestanden;
GPU-/Raumprüfung dieser Variante noch nicht durchgeführt.

Textport, Vorbereitung:

```python
import json
from td_builders import update_motion_visual_reveal as visual_reveal
print(json.dumps(visual_reveal.prepare(op), ensure_ascii=False, indent=2))
```

Bei `prepared: true` in einem **separaten Eintrag** installieren:

```python
print(json.dumps(visual_reveal.install(op), ensure_ascii=False, indent=2))
```

GPU-Probe prüft fünf Animationszeiten und jeweils gesperrten, freigegebenen
und Legacy-State für Boden/Tabletop. Gesperrt muss exakt RGBA-null sein;
freigegeben/Legacy maximal ein Float32-Epsilon und RGBA8-pixelgleich zur
bisherigen Darstellung. Erst bei bestandenem Nachweis werden die beiden
produktiven DATs geändert, sonst bleiben sie erhalten.

Danach einen Vorschlag in der Web-UI explizit aktivieren und prüfen:
Freigabeprüfung, danach vollständige Drei-Sekunden-Welle ohne anfängliche
Sprünge. Nur diese gewünschte Aktivierung erzeugt eine neue Layoutrevision.
Ziele/Chairs bleiben anschließend wie gehabt fest. Erst nach Abnahme TD
manuell speichern. Rücknahme: `visual_reveal.rollback(op)`.

## Vorbereitet: kein alter Layout-Fallback im AISI-Modus

Raumabnahme inzwischen erfolgt: Johannes bestätigt bei Verdeckung leere
Layoutausgabe, automatische Motion-Rückkehr, unverändertes Study/Tracking-only
und manuelle Speicherung. Dateiname nicht erneut genannt. Technische
Installation und gewünschtes Ausfallverhalten damit im laufenden Raum bestätigt.

Offener Folgebefund: Reveal-Welle ruckelig/schlecht sichtbar. Repository-Code
startet die Drei-Sekunden-Reveal-Zeit mit der neuen Motion-Revision, bevor die
Freigabeprüfungen fertig sind. Voller Verify verwendet mehrfach synchrones
`numpyArray(delayed=False)` und läuft nochmals nach Einschalten der Ausgabe.
Das kann sichtbare Restdauer reduzieren und Frames blockieren. Diese Diagnose
ist aus dem Code abgeleitet; tatsächliche Dauer/Framerate und aktuelle TD-DATs
noch nicht gemessen. Korrekturziel: eigene visuelle Startzeit nach Prüfungen,
keine neue Layoutrevision oder zurückgesetzte Engine. Noch nichts geändert.

TD-Installation inzwischen von Johannes bestätigt: `passed: true`, drei
GPU-Prüfgruppen für Boden/Tabletop/Chairs, jeweils Originalzweig pixelgleich
und Leerzweig RGBA-null. Genau die drei eigenen Legacy-Select-Referenzen
geändert; Kalibrierung/Masken unverändert, Engine nicht zurückgesetzt,
nicht gespeichert. Physische Ausfall-/Modusprüfung folgt noch.

Erster TD-Import scheitert vor `prepare`, weil ein wiederverwendeter veralteter
Builder beim Import im TD-Kontext absichtlich abbricht. Korrigiert: keine
Abhängigkeit mehr auf `isolate_aisi_tabletop_targets`, transparente Constant-
TOP-Farbkanäle lokal auflösen. Neun fokussierte Tests bestanden, darunter
Subprozess-Import mit vorhandenem TD-`op` und verbotenem Graphzugriff.
Die im Fehler genannte alte Rückbauanweisung ist hier nicht auszuführen.
Kein neuer Baustein durch diesen fehlgeschlagenen Import erstellt; Vorbereitung
mit korrigiertem Modul erneut ausführen.

Johannes verlangt, im normalen AISI-Modus bis zur gültigen Motion-Freigabe
und bei Ausfällen keine Layoutgrafik anzuzeigen. Study und Tracking-only
bleiben unverändert. `motion_no_legacy_fallback.py` erstellt dafür ausschließlich
einen eigenen Container mit drei Original-/Transparent-Zweigen. Die tatsächlichen
Quellen werden aus den bereits registrierten konstanten Legacy-Selects gelesen;
lokale Abweichungen werden nicht überschrieben. GPU-Prüfung vor Installation:
Originalpfade pixelgleich, Leerpfade vollständig RGBA-null und gleiches Raster.

Installation verändert nur die `top`-Referenzen von `floor_legacy`,
`tabletop_legacy` und `simulation_chairs_legacy` im eigenen Motion-Routing.
Im normalen AISI-Modus sind diese Quellen transparent. Freigegebenes Motion
verwendet weiterhin seinen direkten Eingang; bei Modus 0/1 werden die alten
Quellen unverändert geliefert. Kalibrierungsansichten sind ausgenommen.
Maskeneingänge/-reihenfolge, äußere Schalter und Projektorkette bleiben identisch.
Die drei Änderungen werden exakt im eigenen Live-Schutzsnapshot registriert;
keine neue Baseline für andere lokale Änderungen oder Kalibrierung übernehmen.

Einmalige passive Vorbereitung im Textport:

```python
import json
from td_builders import motion_no_legacy_fallback as no_fallback
print(json.dumps(no_fallback.prepare(op, {
    'containerCOMP': containerCOMP, 'selectTOP': selectTOP,
    'constantTOP': constantTOP, 'switchTOP': switchTOP, 'outTOP': outTOP
}), ensure_ascii=False, indent=2))
```

Installation in einem separaten TD-Eintrag:

```python
print(json.dumps(no_fallback.install(op), ensure_ascii=False, indent=2))
```

Danach separat `no_fallback.status(op)` lesen. Bei normalem AISI sind die drei
inneren Leer-Bypass-Indizes 1; die bisherigen Motion-Indizes bleiben 0/1.
Ohne Freigabe sollen Boden, Tabletop und Chairs keine Layoutgrafik zeigen.
Mit Freigabe bleibt Motion sichtbar; Modi 0/1 und Kalibrierungsansichten
separat prüfen. Noch keine Live-/Raumabnahme behauptet, TD nicht gespeichert.
Acht gezielte Offline-Fälle bestanden.

Rücknahme: `no_fallback.rollback(op)` stellt die drei Originalreferenzen und
den vorherigen eigenen Live-Snapshot wieder her und entfernt nur den eigenen
Baustein. **Vor einem Rückbau der gesamten Live-/Simulationseinbindung zuerst
diesen Patch zurücknehmen.** Wie zuvor bedeutet die Rücknahme wieder Legacy-
Fallback; nichts automatisch speichern.

## Vereinfacht: Kamera starten → Vorschlag aktivieren

Johannes lehnt den mehrteiligen manuellen Wiederanlauf als zu kompliziert ab.
Der normale Web-Pfad enthält deshalb keine Neuverbinden-Checkbox und keinen
separaten Neuverbinden-Knopf mehr. Nach einem Kamera-Prozessneustart gilt:

1. Fehlende Kamera mit `scripts/run_aisi_motion.ps1 -Action Start` starten.
2. Frische Quelle in der UI abwarten und **Vorschlag aktivieren**.

Intern erkennt Motion den Frame-Rücksprung. Erst wenn der frische lokale
TD-Automatikstatus beide Gatter als ausgeschaltet bestätigt, setzt Motion
ausschließlich die Stream-Verbindung zurück. Zwei neue Frames bleiben nötig.
Kalibrierungsidentität muss gleich bleiben; ein Kalibrierungswechsel bleibt
gesperrt. Eine noch laufende Berechnung des alten Kameraprozesses wird verworfen.
Letzter gültiger Vorschlag und Revision bleiben intern erhalten, werden aber
nach Prozessneustart nicht gegen neu gestartete IDs ausgegeben. Erst erfolgreiche
explizite Aktivierung ersetzt Ziele/Chairs und erhöht die Revision einmal.
Keine automatische Planung oder ungeprüfte ID-Neuzuordnung.

Offline 374 Motion-Fälle: 367 bestanden, sieben optionale GPU-Fälle übersprungen.
Einspielen ohne Textport: eigenen Webcontroller gestoppt, automatische TD-Sperre
tatsächlich abgewartet, dann neuen Controller gestartet. Kamera und übrige
Dienste erhalten. Neue Web-Sitzung zunächst ohne Vorschlag; einmalige Aktivierung
nach diesem Update nötig. Physischer Kameraneustart mit dem vereinfachten
Weg noch nicht abgenommen. Ältere manuelle Wiederanlaufabschnitte unten
dokumentieren den vorherigen Stand bzw. technischen Fallback.

## Aktuell: automatische Erstfreigabe in TD bestanden

Kurze Occlusion inzwischen von Johannes abgenommen: Freigabe fällt ab und
kehrt automatisch zurück; ID und Revision, Ziele und Chairs erhalten, keine
neue Reveal-Welle. Dies prüft Erkennungsverlust bei fortlaufendem Kamerastream.
Ein kompletter Kameraprozess-Neustart startet dagegen Framezähler und ggf.
Tisch-IDs neu. Der aktuelle Adapter blockiert einen Frame-Rücksprung bewusst;
automatische Übernahme des alten Vorschlags ist dafür nicht implementiert.
Nach Kameraneustart im Web ausdrücklich neu verbinden und Vorschlag aktivieren;
die TD-Prüfung/Freigabe erfolgt anschließend automatisch. Keine stille
Neuzuordnung alter Ziele zu neu gestarteten Tisch-IDs.

Geplanter Prozessausfall-Test (noch nicht durchgeführt): in Kameravorschau `q`
drücken (im vorhandenen CV-Code belegter Beenden-Hotkey), Motion-Sperre in UI
abwarten. Dann PowerShell `scripts/run_aisi_motion.ps1 -Action Start`; bestehende
übrige Dienste werden übernommen. Im Web-Bereich Wiederanlauf erst bei
bestätigt aufgehobener Freigabe das Feld für ausgeschaltete Ausgänge bestätigen,
Tracking neu verbinden, frische IDs abwarten, Vorschlag aktivieren und automatische
Freigabe beobachten. Neue Sitzung/Revision nach diesem ausdrücklichen Neuverbinden
erwartet; Erhalt der alten IDs/Revision wird für Prozessneustart nicht behauptet.

Folgebestätigung: Johannes meldet passenden Sichtbefund und manuelle
TD-Speicherung. Der neue Arbeitsdateiname wurde nicht genannt. Nächste Prüfung
ist ein kurzer Erkennungsverlust bei weiterlaufender Kamera; automatische
Sperre/Wiederfreigabe und unveränderte ID/Revision müssen noch nachgewiesen
werden. Ein echter Prozess-/Frameausfall und Kaltstart bleiben separate Tests.

Johannes bestätigt nach Installation und Web-Aktivierung: Auto-Baustein und
Callback aktiv, `phase: active`, `approved: true`, beide Ausgangsflags an;
Sitzung 4012265, Revision 2, `table_01`, TD-Frame 620089. Dies ist der Status
nach automatischem Maskennachweis, späterer Frame-Bestätigung und separater
Ausgabekontrolle. HTTP-Gegencheck bestätigt `td_approved: true` für dieselbe
Sitzung/Revision, Input, drei Chairs und frische Quelle. Die Verbindung
Web-Aktivierung → TD-Prüfung → Freigabe → Web-Rückmeldung ist damit erstmals
im laufenden System technisch nachgewiesen. Keine manuelle Freigabe angefordert.

Noch offen: Sichtbefund für diesen Durchlauf, Quellenverlust-/Modus-/Neustart-
Prüfung, Rechner-Kaltstart und manuelle TD-Speicherung. `saved: false` bedeutet,
dass die Helfer nicht speichern. Der folgende Abschnitt dokumentiert die
Vorbereitung vor diesem Live-Nachweis; der manuelle Startablauf bleibt Fallback.

## Vorbereitet: automatische TD-Freigabe — 2026-10-27

Johannes bestätigt die passive TD-Vorbereitung: `prepared: true`, eigener
`comp_aisi_motion_auto_approval`, `armed: false`, keine produktive Ausgabe-
oder Kalibrierungsänderung, nicht gespeichert. Automatik weiterhin nicht
installiert; als Nächstes beide Motion-Gatter vor dem Webcontroller-Wechsel aus.

Folgeschritt erfolgt: Johannes bestätigt alle drei Gatter aus. Nur kombinierte
UI/Motion-Kette ersetzt; Kamera/Scene/Study/Legacy-OSC-PIDs erhalten. Neuer
Webstatus liefert frische `table_01`, Sitzung 4012265/Revision 1, noch keinen
Vorschlag, `td_approved: false`. Neue TD-Statusanzeige ist damit im Webprozess
geladen; einmalige TD-Installation und erneute Web-Aktivierung stehen aus.

Johannes beauftragt automatische Freigabe nach erfolgreichem Maskenabgleich,
damit nach dem Start nur noch die Web-Aktivierung nötig ist. Code und
Offline-Prüfungen sind vorbereitet; **noch nicht im laufenden TD installiert
oder physisch geprüft**. Der laufende Webprozess verwendet bis zu seinem
kontrollierten Neustart noch die vorherige Statusdarstellung.

`install_motion_auto_approval.py` erstellt ausschließlich den neuen eigenen
`comp_aisi_motion_auto_approval` (Container COMP) mit einem Execute DAT.
Vorhandene Komponenten/Leitungen, Kalibrierung, Masken und Motion-Engine werden
nicht ersetzt. Bestehende Live-Registrierung ist Voraussetzung. Vorhandener
gleichnamiger Baustein oder lokale Änderungen werden abgelehnt. Rücknahme
deaktiviert die Freigaben und entfernt ausschließlich den eigenen Baustein.

Ablauf nach späterer Installation und manueller TD-Speicherung:

1. TD-Start/erster Callback setzt beide Freigaben aus; gespeicherte Freigaben
   gelten niemals als neuer Nachweis.
2. Frische ID-gebundene Quelle, nichtleere aktivierte Tischmenge, AISI-Modus,
   ausgeschaltete Simulation und normale Kalibrierungspanels abwarten.
3. Vorhandenen vollständigen `live_output.verify` bei ausgeschalteter Ausgabe
   ausführen; Schutzsignaturen, Geometrie, Maskenpixel und Chairs bleiben streng.
4. In einem späteren TD-Frame dieselbe Sitzung/Revision/IDs mit fortschreitendem
   Frame und erneut passender Source-Geometrie bestätigen, dann freigeben.
5. In einem weiteren TD-Frame vollständige Ausgabekontrolle; erst danach Status
   „automatisch geprüft und freigegeben“. Bei Fehlern sperren und mit zwei
   Sekunden Abstand erneut prüfen. Keine wiederholten Tracebacks im Textport.
6. Im Betrieb Frische, Gatter und Tischmenge beobachten. Quellenverlust,
   Modus-/Sitzungs-/Revisionswechsel sperren bzw. verlangen neue Prüfung.
   Keine automatische Layoutberechnung, ID-Neuzuordnung oder Reveal-Aktivierung.

GPU-Prüfungen laufen nur beim Freigabeübergang, nicht in jedem Frame.
Ein lokaler atomarer Status-Heartbeat `data/aisi/state/motion_td_approval.json`
meldet Prüfung/Fehler an die bestehende Web-UI. Sie akzeptiert Freigabe nur für
passende Sitzung/Revision/IDs und höchstens drei Sekunden alte Meldungen.
Bei pausiertem/geschlossenem TD wird der Status damit ungültig. Kein zusätzlicher
Netzwerkdienst oder Teilnehmerdatenspeicher.

Der gemeinsame Launcher kann nach Installation ohne `-OutputsOff` starten,
wenn der frische TD-Heartbeat die aktivierte Automatik und beide ausgeschalteten
Gatter bestätigt. Andernfalls bleibt der bisherige manuelle Weg erforderlich.
Geplanter Kaltstart: gespeicherte Arbeitsdatei öffnen/Play → `Start` → Web-UI
„Vorschlag aktivieren“. TD muss weiterhin manuell geöffnet und gespeichert werden.

Einmalige passive Vorbereitung im Textport:

```python
import json
from td_builders import install_motion_auto_approval as auto_approval
print(json.dumps(auto_approval.prepare(op, {'containerCOMP': containerCOMP, 'executeDAT': executeDAT}), ensure_ascii=False, indent=2))
```

Anschließende Installation separat und mit dem Webprozess-Wechsel koordinieren:
erst TD-Ausgänge aus bestätigen, dann kombinierten Webcontroller aktualisieren,
dann `auto_approval.install(op)` und `auto_approval.status(op)` in getrennten
TD-Einträgen. Installation ist kein physischer Nachweis. Nach erfolgreicher
Live-/Fehlerfallprüfung TD manuell speichern; Master `AISI_v2.toe` unberührt.

Offline: 371 Motion-Fälle, 364 bestanden, sieben optionale GPU-Fälle übersprungen.
Zusätzlich Python-3.9-Syntax beider TD-Helfer und PowerShell-Parser geprüft.
Prüfungen umfassen Frame-Trennung, fehlgeschlagene Vor-/Nachprüfung, neue
Sitzung/Revision, Quellenverlust, Wiederholungsabstand, ungültigen UI-Heartbeat,
passive Vorbereitung und Rücknahme ohne Überschreiben lokaler Änderungen.

Aktueller TD-Nachweis von Johannes: Arbeitsdatei
`AISI_v3.2_motion_lab_checkpoint_20261026.12.toe`, Sitzung 6233135,
Revision 4, `table_01`. Separater `live_masks.check` bestanden; nach manueller
Freigabe auch `live_output.verify` bestanden, Frame 9248. Indizes 1/1/0/1,
Originalmaske ausgewählt, drei frische Chairs an derselben Revision/Frame.
Maximaler geometrischer Randfehler 0,0211 cm, keine abweichenden Maskenpixel
außerhalb der Ein-Pixel-Kante. Kein Vision-Neustart für diese Wiederaufnahme.
Frühere Fehlerursache nicht eindeutig belegt. Physischer Sichtbefund und
manuelle TD-Speicherung dieses Zustands noch nicht bestätigt.

## Vollständiger Start nach Rechnerneustart

Vision muss **nicht separat** gestartet werden. Der gemeinsame Launcher startet
Kamera, Scene-Adapter, Study-Control, bisherigen System-OSC-Sender und den
kombinierten Learning-Format-/Motion-Webserver. TouchDesigner bleibt manuell.

1. Kamera und Projektoren einschalten. In TD die zuletzt manuell gespeicherte
   und geprüfte Motion-Arbeitsdatei öffnen, **nicht `AISI_v2.toe`**. TD muss im
   Play-Modus laufen. Im Textport zuerst:

   ```python
   print('WORKFILE:', project.folder, project.name)
   r = op('/project1/comp_aisi_motion_output_routing')
   assert r is not None, 'Diese Datei enthält den integrierten Motion-Graph nicht.'
   r.par.Enablemotion = False
   r.par.Sourceapproved = False
   r.par.Simulationtest = False
   ```

2. In PowerShell, ohne notwendige manuelle venv-Aktivierung:

   ```powershell
   Set-Location C:\dev\Promotion_Prototypen\AISI
   .\scripts\run_aisi_motion.ps1 -Action Start -OutputsOff
   ```

   `-OutputsOff` bestätigt die tatsächlich ausgeschalteten TD-Schalter; es
   schaltet sie nicht selbst aus. Kamera mit laufender Vorschau nicht doppelt
   starten. Die Prozesse dürfen beim ersten Start einige Zeit zum Laden brauchen.

3. Status prüfen:

   ```powershell
   .\scripts\run_aisi_motion.ps1 -Action Status
   ```

   Erwartet: je eine Prozesskette für Kamera, Scene, Study, LegacyOSC, UI;
   null alter Motion-Controller. Im Motion-Status `camera_fresh: true`, die
   aktuellen Tisch-IDs und `error: null`. Ein frischer Backend-Status beweist
   noch keinen funktionierenden TD-Empfang oder Maskenabgleich.

4. <http://127.0.0.1:8080> öffnen oder neu laden. Lernformat und Parameter wählen,
   dann **Vorschlag aktivieren**. Erst fortfahren, wenn aktives Format, neue
   Revision und passende Chair-Anzahl angezeigt werden. Bei ungültigem Vorschlag
   dessen Fehlermeldung beheben; nicht durch wiederholten Dienstneustart umgehen.

5. Den Tisch für den Maskenabgleich stillhalten. Im TD-Textport:

   ```python
   import json
   from td_builders import motion_live_output as live_output
   proof = live_output.verify(op)
   print(json.dumps(proof, ensure_ascii=False, indent=2))
   ```

   Erwartet: `passed: true`, frische Quelle, passende IDs/Revision und
   `original_mask_selected: true`. Indizes dürfen hier noch alle null sein.
   Erst danach im **nächsten Textport-Eintrag**:

   ```python
   r = op('/project1/comp_aisi_motion_output_routing')
   assert not r.par.Simulationtest.eval()
   assert op('/project1/comp_io/null_osc_raw')['study/mode'].eval() == 2
   try:
       proof = live_output.verify(op)
       assert proof['passed']
       r.par.Sourceapproved = True
       r.par.Enablemotion = True
       assert live_output.indices(r) == dict(floor=1, tabletop=1, simulation_mask=0, simulation_chairs=1)
       print('Motion-Ausgabe eingeschaltet.')
   except Exception:
       r.par.Enablemotion = False
       r.par.Sourceapproved = False
       raise
   ```

   Dann separat nach fortgesetztem TD-Cook:

   ```python
   print(json.dumps(live_output.verify(op), ensure_ascii=False, indent=2))
   ```

   Bei Fehler keine Freigabe erzwingen. Dieser Ablauf setzt die bereits
   eingerichtete Live-Registrierung der gespeicherten Arbeitsdatei voraus.
   Fehlt sie, Diagnose zurückgeben; keine Builder oder `prepare` blind ausführen.

6. Im Raum prüfen: Motion sichtbar, Source/Feedback folgen, Ziele und Chairs
   bleiben fest. Erst das ist die physische Prüfung. TD nur manuell speichern.

## Diagnose statt pauschalem Neustart

Am 2026-10-27 meldet Johannes Stillstand und einen fehlgeschlagenen
`live_output.verify`. Lesende Gegenprüfung: alle fünf Prozessketten laufen;
Kameraframe 234401 → 234500, Scene-Adapter ebenfalls Frame 234500, Motion
aktuell für `table_01`, Sitzung 6233135, Revision 3, Input/drei Chairs. Ein
Vision-Stillstand ist damit zum Prüfzeitpunkt nicht nachgewiesen. Die Ursache
des TD-Prüffehlers ist noch offen; keine Dienste dafür neu gestartet.

Die generische `verify`-Exception verdeckt den detaillierten Rückgabestatus.
Bei ausgeschalteter Ausgabe separat lesen:

```python
import json
from td_builders import motion_live_output as live_output
from td_builders import check_motion_live_masks as live_masks
print('TD-FRAME:', absTime.frame, 'WORKFILE:', project.name)
print(json.dumps(live_masks.check(op, validator=live_output.validate, allow_live=True), ensure_ascii=False, indent=2))
```

`waiting for advancing frame` verlangt einen zweiten Aufruf nach laufenden
TD-Frames; ein Pixel-/Posefehler verlangt dessen konkrete Diagnose. Ein
fehlgeschlagener `verify` schaltet die beiden Motion-Freigaben ausdrücklich aus.
Kein neues Aktivieren oder Neukalibrieren allein wegen dieser Sammelmeldung.

## Bedienung

Learning-Format-UI: <http://127.0.0.1:8080>. Derselbe vorhandene Webserver führt
mit `--motion --send` jetzt den Kamera-Motion-Controller im Hintergrund aus.
Das zusätzliche Tk-Fenster wird in diesem Startpfad nicht benötigt.

1. Lernformat und Parameter wählen. Das sind **vorgemerkte Einstellungen**.
2. **Vorschlag aktivieren** berechnet einmalig aus frischen Istposen bei 100 %.
3. Der aktive Status zeigt Format, Revision und Chairs. Erst erfolgreiche
   Aktivierung ersetzt Ziele und Chairs gemeinsam; Fehler behalten den letzten
   gültigen Vorschlag. Bewegung und Einstellungsänderungen aktivieren nichts.

Kamerafrische, beobachtete IDs, fehlende aktive IDs, Berechnung und Fehler werden
im Motion-Status angezeigt. Eine frische Kamera ist keine TD-Ausgabefreigabe.
Der Webserver kann die tatsächlichen TD-Schalter nicht lesen oder freigeben.

## Ein Startbefehl und ein Statusbefehl

PowerShell im Repository:

```powershell
.\scripts\run_aisi_motion.ps1 -Action Status
.\scripts\run_aisi_motion.ps1 -Action Start
```

Start übernimmt vorhandene eigene Prozessketten und startet nur fehlende
Kamera-, Scene-, Study-, Legacy-OSC- und UI/Motion-Dienste. Der Kamera-Launcher
und seine bestehende Kalibrierung bleiben maßgeblich. Laufender Study-Modus
wird nicht verändert; ein neu gestarteter Study-Control beginnt wie bisher mit
Modus 2. Neue eigene Hilfsprozesse laufen ohne zusätzliche Konsolenfenster;
die Kameravorschau bleibt verfügbar. Logs: `data/aisi/debug/motion_runtime/`.
Prozessanwesenheit beweist keine gültige Quelle; `/motion-status` prüft neue
Kameraframes. Ein `Start -DryRun` verändert keine Dienste.

Fehlt der kombinierte Controller, verlangt Start zuvor ausgeschaltete
TD-Motion-Ausgänge und zusätzlich `-OutputsOff`. Für den bewussten Ersatz eines
laufenden Controllers: `-Action ReplaceController -OutputsOff`. Nur eindeutig
zugeordnete Repository-venv-Ketten werden ersetzt. Fremde/mehrfache Ketten
führen zum Abbruch. Live-Sender haben zusätzlich eine Prozesssperre; keinen
Motion-Simulator parallel starten.

## Wiederanlauf

- Kurzer Frame-Ausfall: neue fortschreitende Frames erholen die Frische
  automatisch. Kein neuer Vorschlag, keine neue Revision.
- Neue Tisch-ID: keine automatische Zuordnung zum alten Ziel. Fehlerstatus
  lesen und bewusst erneut aktivieren; neue erfolgreiche Aktivierung berechnet
  aus den dann aktuellen Istposen.
- Kamera-Prozess fehlt: `Start` startet nur fehlende Dienste. Frame-Rücksprung
  oder Kalibrierungswechsel blockiert den bisherigen Adapter ausdrücklich.
- Bewusstes Neuverbinden oder Controller-Neustart: zuerst in TD
  `Enablemotion`, `Sourceapproved`, `Simulationtest` ausschalten. Im Web-Bereich
  **Wiederanlauf** bestätigen und **Tracking neu verbinden** wählen. Dies
  beginnt eine neue leere Motion-Sitzung; zwei neue Frames abwarten und explizit
  aktivieren. Vor erneuter Projektion Maskenabgleich/Freigabe manuell prüfen.
  Es erfolgt keine automatische Übernahme geänderter Kalibrierung als geprüft.

TD bleibt manuell bedient und gespeichert. Der Launcher öffnet, verändert oder
speichert keine `.toe`-Datei. Study-/Tracking-Modi, Masken und Kalibrierung
werden durch diese Integration nicht geändert.

## Nachweis vom 2026-10-27

- Offline: 359 Motion-Fälle, davon 352 bestanden und sieben optionale GPU-Fälle
  übersprungen; zusätzliche bestehende Web-/Status-/Launcher-Prüfungen bestanden.
  Neue Tests prüfen HTTP-Einstellungsänderung ohne Aktivierung, expliziten
  Snapshot, Doppelaktivierung, fehlgeschlagene Planung, ID-Wechsel während
  Berechnung, Neustart ohne Vorschlag und exklusiven Live-Sender.
- Laufende Dienste: nach bestätigtem TD-Ausgang-Aus nur alte UI und Tk-Motion
  ersetzt; Kamera/Scene/Study/Legacy-OSC-PIDs erhalten. Neuer Webstatus liefert
  frische `table_01`, Sitzung 432798, Revision 1, kein Vorschlag, kein Fehler.
  Wiederholter Start-Dry-run erzeugt keine weiteren Dienste. Kalibrierungsdatei
  SHA256 unverändert `480026FBE25BFE6503ECDF103A0070E7F14B3E6A8830F48BA31B95CCE1018AE9`.
- Laufendes TD/physischer Raum: neuer Web-Aktivierungsweg noch nicht abgenommen;
  keine automatische Freigabe oder Speicherung. Nächster Schritt: vorhandenes
  Input mit drei Teilnehmenden im Web aktivieren, dann separat
  `motion_live_output.verify(op)` und Sichtprüfung durchführen.
