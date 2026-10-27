# AISI Project Context

Stand: 2026-10-27

## Gesamtabschluss der Systemtests und Sicherung — 2026-10-27

Johannes meldet alle Systemtests abgeschlossen und beauftragt die Sicherung.
Dies als manuelle Gesamtbestätigung dokumentieren; für zuletzt nicht einzeln
zurückgemeldete Counts/Parameter/Fälle keine Messdaten oder technischen Beweise
erfinden. Maßgeblicher kompakter Übergabestand:
[Motion-Checkpoint](MOTION_CHECKPOINT_20261027.md). Frühere offene Testangaben
in nachfolgenden Zwischenständen sind durch den Gesamtabschluss überholt.
Letzter lesender Webstatus: Sitzung 2730811/Revision 27, Input/13 Chairs,
fünf frische IDs, TD automatisch freigegeben, kein Fehler. Kein neuer genauer
TD-Dateiname/Speichernachweis. Code sichern, physische `.toe` nur manuell;
Master und Kalibrierung geschützt. Untertisch pausiert. Nächster unabhängiger
Block bleibt abschließende Konsolidierung von Motion als AISI-Standard.

## Groupwork ein Tisch bestätigt; nächster Count zwei — 2026-10-27

Johannes bestätigt einen Tisch/drei Teilnehmende/eine Gruppe mit drei Chairs,
einer Welle und richtiger Source-/Feedback-Bindung. Änderung auf zwei ohne
Aktivierung erhält Ziele/drei Chairs. Raumfall akzeptiert; damalige Revision/
Dauer nicht gemeldet. Später lesender Webstatus zeigt anderen Zustand:
Sitzung 2730811/Revision 16, Input/13 Chairs, fünf frische IDs, TD freigegeben;
nicht als rückwirkenden technischen Eintischnachweis werten. Nächster Versuch
genau zwei erkannte Rect-Tische, Groupwork/sechs Teilnehmende/zwei Gruppen,
Einzel-/Simultanbewegung prüfen. Dann Gruppenzahl auf eins ohne Aktivierung:
Ziel-/Chair-Positionen und Revision bleiben. Pair-/Ein-Gruppen-Fall danach
gesondert; Groupwork 3–4, Discussion und Formatwechsel weiter offen.

## Konturen akzeptiert, Systemprüfung fortsetzen — 2026-10-27

Johannes bestätigt native Kontur-/Chair-Installation `passed: true` und positiven
Sichtbefund; akzeptiert. Neuester lesender Webstatus: Sitzung 2730811/Revision 5,
fünf frische IDs `table_00` bis `table_04`, Groupwork/15 Chairs, TD freigegeben.
Letzte Berechnung 14,503 s für diese Posen; ältere 2,028 s sind ein anderer Fall,
keine allgemeine Laufzeitobergrenze. Kein neuer Speicher-/Dateinachweis.
Systemprüfung jetzt fortsetzen: Input 1–5 und Groupwork 5/15/drei Gruppen positiv;
kleine Groupwork-Counts fehlen. Nächster Fall ein erkannter Rect-Tisch, drei
Teilnehmende/eine Gruppe, UI-Aktivierung; anschließend nur Einstellung auf zwei
ändern und feste Ziele/drei Chairs/Revision prüfen. Dann Groupwork 2–4,
Discussion und abschließender Formatwechsel. Untertisch bleibt pausiert.

## Kontur durchgängig, Chair-Striche ebenfalls 5 cm — Trial 2026-10-27

Johannes ersetzt die gestrichelte Zielkontur durch eine durchgängige Linie und
wünscht dieselbe Strichstärke für Chairs. Eigener Doppel-Shader-Trial
`update_motion_continuous_contours.py`: unverändertes gerundetes 5-cm-Innenband
auf Boden/Tabletop, nur Lücken entfernen; Chair-Kreise von 2,5 auf 5 cm nach
innen verbreitern, Außenradius unverändert. Keine Positions-/Ziel-/Revisions-,
Runtime-/Reveal- oder Maskenänderung. Source-/Zielhilfen bleiben im tatsächlichen
Ausgangsshader erhalten (voriger Weiß-Patch noch nicht explizit bestätigt).
Transaktion prüft beide Shader vor Änderung, aktualisiert ausschließlich den
eigenen Chair-DAT-Texthash im bestehenden `chair_owned`-Snapshot und sichert
beide alten Texte gemeinsam. Sieben fokussierte Tests und isolierter Float32-
WebGL-Vergleich bei drei Rotationen bestanden. Native TD-/Raumabnahme offen.

## Hakenabschluss akzeptiert, Source-/Zielhilfen getrennt — 2026-10-27

Johannes bestätigt native Gruppenhaken-Installation (`passed: true`) und
Zweitisch-Sichtbefund: erster Haken wartet auf zweiten, gemeinsames Verschwinden
passt. Anfangs korrekte Tische/Ausfälle noch kein eigener neuer Raumnachweis.
Neue präzise Farbregel: Source-Striche am bewegten Navigationskreis weiß;
Zielring und Zielstriche weiterhin ausgespart. Eigener Shader-Trial
`update_motion_source_bars_white.py` ändert nur Source-Composite-Zeile und
zugehörigen Kommentar im tatsächlichen DAT; Runtime, Feedback, Hakenabschluss,
Ziel-/Chair-Posen/Revision unverändert. 20 fokussierte Tests und isolierter
Float32-WebGL-Vergleich mit drei Rotationen bestanden. Native Installation
und physischer Sichtbefund dieses Farbpatches noch ausstehend.

## Persistente Haken bis zum gemeinsamen Abschluss — Trial 2026-10-27

Feedbackradius und Alpha-Hilfen sind nach korrigierter Kantenprüfung nativ
installiert und von Johannes im Raum akzeptiert. Folgeauftrag:
`update_motion_group_success.py` ergänzt ausschließlich eigenen Anzeigezustand
(`motion_group_success.py`) in den freien Z/W-Kanälen von State-Spalte 5;
vorhandene Redisplay-X/Y-Werte bleiben gleich. Nach vollständig sichtbarem
Reveal ploppt jeder bereits/fertig platzierte Tischhaken auf, auch bei
`active=False`. Frühe Haken bleiben bis alle IDs fertig sind. Nach letzter
Ankunft eine Sekunde gemeinsame Sichtbarkeit, dann synchron 0,32 s Reverse-Pop.
Bestehende Engine-Phasen und Hysterese entscheiden Ankunft/Wiederaufnahme;
keine neue Layoutberechnung, Ziele/Chairs/Revision und Reveal-Uhr unverändert.
Ungültige Quellen oder fehlende/geänderte IDs können keinen Abschluss auslösen;
Anzeigezeiten pausieren bei Tracking-/Freigabeausfall. Neues Layout leert nur
eigenen Anzeigenachweis; erneute Guidance öffnet die Abschlussgruppe wieder.
Zwölf fokussierte Tests sowie isolierter Float32-WebGL-Vergleich bestanden.
Native TD-GPU-Prüfung und Raumabnahme noch offen; transaktionaler eigener
Rollback, keine automatische Speicherung.

## Feedbackpräzisierung: 80 % bei 20 cm, Hilfen transparent — 2026-10-27

Neuer Benutzerwunsch ersetzt den nachfolgenden 100-%-bei-20-cm-Trial:
`update_motion_feedback_size_cutouts.py` setzt rein distanzabhängigen Radius,
35 cm ab 80 cm Abstand, 65,12 cm bei 20 cm (=80 % von maximal 81,4 cm), Maximum
bei 8 cm. Erfolgsschwellen selbst unverändert. Zielring/-striche und Source-
Striche als Alpha-Aussparungen; keine weißen Hilfen im offenen Zielinneren oder
auf grünem Feedback. Navigation bleibt über Zielhilfen geschichtet wie zuvor.
Transaktion unterstützt alte oder bereits angepasste Radiusversion sowie solide
und gestrichelte Ziele. Elf fokussierte Tests und isolierte WebGL-Prüfung
(drei Rotationen, transparente Hilfen, Boden pixelgleich) bestanden;
TD-/Raumabnahme offen, keine automatische Speicherung.

Erste native Installation durch GPU-Prüfung vor Mutation gestoppt: `.999`-Maske
schloss teilgedeckte Randpixel ein, obwohl vollständige Transparenz verlangt
wurde. Isoliert mit Float32 bei 33 Grad reproduziert (Rest-RGBA ca. 0,000032,
Kern null). Nur Prüflogik korrigiert: exakte Vollmaske für Null-RGBA-Kern;
Rand muss Komplement der Maskendeckung einhalten, Float32-SDF-Toleranz nur dort.
Fünf fokussierte Tests bestanden. Bestehender TD-Prüfzweig kann nach Modul-Reload
erneut installiert werden; Shadertext/Backup-Schlüssel unverändert.

## Feedback vor Zielerreichung größer — Trial 2026-10-27

Johannes meldet zu kleinen Halo kurz vor Ankunft und abrupten Größenwechsel bei
Erfolg. Bisherige Größe folgt kontaktrelativer Progression einschließlich Winkel;
Shader-Trial `update_motion_feedback_proximity.py` ergänzt deshalb distanzabhängige
Mindestgröße: weich ab 80 cm, voller bisheriger Radius 81,4 cm bei 20 cm. Bisheriges
Wachstum wird nie verkleinert. Keine Änderung an Kontaktblende, Erfolgsgrenzen,
Erfolgsanimation, Zielen, Chairs, Revision oder Masken. Patch unterstützt solide
und gestrichelte Ziele. Zwölf fokussierte Tests und isolierte WebGL-Kompilierung/
Darstellung mit pixelgleichem Boden bestanden. Native TD-GPU-/Raumabnahme offen;
vorbereitete andere Shader-Trials vor dieser Änderung abschließen.

## Groupwork-Wiederholung bestätigt, gestrichelte Ziele vorbereiten — 2026-10-27

Johannes bestätigt fünf Tische/15 Teilnehmende/drei Gruppen deutlich schneller,
mit passender Freigabe/Reveal/Darstellung und festen Zielen/Chairs. Aktueller
Webstatus: fünf IDs, 15 Chairs, Sitzung 2730811/Revision 3, freigegeben,
Generatorzeit 2,028 s für diese Posen. Restliche Systemtestfälle weiter offen.

Auf Zwischenauftrag gestrichelten Zielumriss wie in Screenshots vorbereitet:
eigener rücknehmbarer Shader-Trial, 5 cm Innenkontur am identischen gerundeten
Außen-Footprint, 14 Striche/74 % Anteil über echte Umfangslänge. Statisches
zielgebundenes Muster, gleich für Boden/Tabletop; offenes Inneres. Grüner
Feedback-Halo verwendet unverändert vollen Ziel-Footprint und bisherige Funktion,
Zielhilfen bleiben im offenen Inneren sichtbar. Engine/Revision/Ziele/Chairs,
Kalibrierung und Masken unangetastet. Vier Offline-Patchtests und isolierte
WebGL-Kompilierung/-Visualisierung bestanden; 396 Motion-Tests bestanden,
sieben optionale GPU-Fälle übersprungen. Tatsächliche TD-GPU-/Raumprüfung
steht aus, keine Installation oder automatische Speicherung vorgenommen.

## Groupwork-Performancefall — 2026-10-27

Johannes testet direkt fünf Tische/15 Teilnehmende/drei Gruppen, meldet mindestens
eine Minute und UI „Vorschlag wird berechnet“. Danach 15 Chairs und Freigabe
technisch vorhanden, vollständiger Raumfall noch nicht abgenommen. Offline-
Replay eines Kameraframes nahe Aktivierung (91650, ca. 76 ms zuvor) reproduziert
52,406 s Generatorzeit; aktuelle andere Posen benötigen 2,764 s. Ursache ist
geometrieabhängige Suche mit wiederholten Optionen/Kollisions-/Sitzraumprüfungen.

Gezielte Optimierung im Suchkern/Groupwork-Profile-Planner: anfrageinternes
Teilen identischer lokaler Optionssätze und kanonischer Geometrieurteile über
Profile hinweg, exakt nach Quellen/ROI/Form/Winkeln getrennt. Keine andere
Kandidatenmenge, Zielfunktion, Toleranz, Sitz-/Clearance- oder Gruppenregel.
Mutable TableTargets bleiben partitionseigen. Replay danach 10,162 s mit exakt
identischen Zielen/Chairs. 56 relevante Geometrie-/Groupwork-/Cachetests sowie
392 Motion-Tests bestanden, sieben optionale GPU-Fälle übersprungen.

Gemeinsamen Controller nach beobachteter automatischer TD-Sperre erneuert,
Kamera/übrige Dienste erhalten; neue Sitzung 2730811 ohne automatische Planung.
UI-Diagnose zeigt jetzt `planning_seconds`. Live-Wiederholung und kleinere
Groupwork-Counts noch offen. Andere Ausgangsposen können weiter abweichende
Laufzeiten haben. Mess-/Replayartefakte bleiben ungestagt unter debug.

## Input mit ein bis fünf realen Tischen abgenommen — 2026-10-27

Johannes bestätigt alle Input-Tischcounts; zuletzt fünf Tische/15 Chairs,
eine Welle, keine Vertauschung, kurze Verdeckung mit automatischer Rückkehr
ohne neue Welle und feste Ziele/Chairs. Vier-Tischfall auch mit zwei gleichzeitig
bewegten Tischen bestanden; Dreitischfall mit Änderung neun auf acht ohne
Aktivierung erhält neun Chairs/feste Ziele. Groupwork und Discussion sowie
formatübergreifende Wechsel bleiben offen. Groupwork-Einstieg ein realer
Rect-Tisch, drei Teilnehmende/eine Gruppe; bisherige Plannerregeln erhalten.

## Input-Zweitischfall bestätigt; Chair-Reveal angleichen — 2026-10-27

Folgeabnahme: Johannes bestätigt Chair-Reveal-Installation `passed: true` und
korrekte Einblendung erst mit der Welle. Webstatus frisch/freigegeben, dieselben
IDs und sechs Chairs, Sitzung 511129/Revision 5. Nächster Raumfall Input mit
drei Tischen/neun Teilnehmenden einschließlich Einstellungsänderung ohne
Aktivierung. Speicherung der Chair-Reveal-Reparatur noch nicht bestätigt.

Johannes bestätigt reale Input-Prüfung mit zwei Tischen/sechs Chairs:
eine Welle, richtige Source-/Feedback-ID-Bindung, feste Ziele/Chairs, keine
Vertauschung. Webstatus frisch, IDs `table_00`/`table_01`, Sitzung 511129,
Revision 4 und automatische Freigabe bestätigt. Raumprotokoll aktualisiert.
Nebenbefund: Chair-Kreise erscheinen vor der neuen Reveal-Welle, da der
Chair-Shader weiterhin die alte globale Uhr liest. Zielpatch vorbereitet:
derselbe zusätzliche visuelle Marker/Takt wie Motion, vor Freigabe RGBA-null,
danach gleiche radiale Freigabe. Keine Änderung an Chair-Positionen/-Radien,
Engine, Revision, Layoutdaten oder Masken. Nur eigener Shader und exakt dessen
registrierten Chair-Texthash ändern. Isolierter GPU-Nachweis/TD-Installation
und Raumabnahme noch offen, danach Input mit drei Tischen fortsetzen.

## Neue Learning-Format-Oberfläche bereitgestellt — 2026-10-27

Johannes bestätigt Reveal-Patch im Raum: Start nach Freigabe, vollständig und
flüssig, Ziele/Chairs fest. Danach ausdrücklich grafische UI-Überarbeitung mit
weniger technischen Informationen beauftragt. Neue Oberfläche im bestehenden
Motion-Webmodus: helle responsive Formatkarten, relevante Einstellungen,
Anzeige-Schalter, ein Aktivierungsbereich und kurze situationsbezogene Status.
Technik und Generatoroption unter eingeklappter Diagnose. Keine neuen Dienste,
Abhängigkeiten oder externen Fonts; HTML/CSS/JS als lokale Paketressourcen.

Bestehendes `/set` liefert auf Wunsch JSON für geordnete Änderungen ohne
Seitenneuladen; HTML-Kompatibilität bleibt. Einstellungen aktivieren nichts;
Aktivierung wartet in derselben Request-Reihenfolge hinter den Änderungen.
HTTP-/Headless-Browserprüfungen für Desktop/Mobil bestanden, inklusive einer
expliziten Aktivierung und deaktiviertem Button bei Trackingverlust. 386 Motion-
Tests bestanden, sieben GPU-Fälle übersprungen; sechs UI-/Serverfälle bestanden.

Bereitstellung: nur Web/Motion aktualisiert, automatische TD-Sperre vorher
tatsächlich beobachtet, andere Dienste erhalten. Neuer echter GET und JS-
Ausführung lesend geprüft; Sitzung 511129, Revision 1, frische `table_00`,
noch kein Vorschlag. Nach Update einmalige Benutzeraktivierung erforderlich.
Gestalterische Laborabnahme noch offen, keine neue Mehrtisch-/Raumabnahme
behauptet. Untertisch bleibt pausiert.

## Reveal nach vollständiger Freigabe vorbereiten — 2026-10-27

Johannes beauftragt vollständige flüssige Welle erst nach Prüfungen. Neuer
Helfer `update_motion_visual_reveal.py` liest/patcht ausschließlich tatsächliche
Runtime-/Shader-DATs und erstellt vorher einen isolierten GPU-Vergleich. Eigene
Anzeigeuhr `motion_visual_reveal.py` startet bei exakt passender aktiver
Auto-Freigabe, nach der separaten Ausgabekontrolle. Zusätzlicher State-Texel
`data[5,1]` statt Veränderung der gemeinsamen globalen Uhr: Chair-Shader und
Masken bleiben identisch versorgt. Engine/Reader, Zustände, Ziele, Chairs,
Layoutrevision und Engine-Start unverändert. Kurze Wiederfreigabe und Modus-
Rückkehr derselben Revision starten keine neue Welle; Installation selbst
markiert bestehendes Layout als bereits gezeigt. Zehn fokussierte Tests
bestanden. Tatsächliche TD-GPU-Installation und Raum-/Framerateprüfung noch
offen; keine automatische Speicherung, keine Kalibrierungsänderung.

## AISI ohne gültige Motion-Freigabe bleibt leer — vorbereitet 2026-10-27

Johannes bestätigt inzwischen Raumprüfung und manuelle TD-Speicherung:
bei Verdeckung keine alte Layoutgrafik, Motion kehrt automatisch zurück,
Study/Tracking-only unverändert. Neuer Arbeitsdateiname nicht genannt.
Folgebefund: globale Reveal-Welle nach Vorschlagsaktivierung ruckelig und
schlecht sichtbar. Codeanalyse: Reveal-Zeit beginnt beim State-Empfang der
Revision vor abgeschlossener Freigabe; Shader hat drei Sekunden Reveal.
Synchroner voller GPU-Verify vor und nach Einschalten kann Startzeit verbrauchen
und sichtbare Frames blockieren. Konkrete Laufzeiten noch nicht gemessen,
aktuelle eingebettete TD-DATs noch nicht für diesen Befund ausgelesen.
Keine Kalibrierungs-/Helligkeitskorrektur oder Reveal-Änderung vorgenommen.

TD-Folgeschritt bestätigt: Installation `passed: true`, GPU-Boden/Tabletop/
Chairs jeweils Originalzweig pixelgleich und Leerzweig RGBA-null. Drei eigene
Select-Referenzen umgestellt; Kalibrierung/Masken unverändert, Engine erhalten,
nicht gespeichert. Physischer Quellenverlust und Modi 0/1 noch zu prüfen.

Johannes verlangt ausdrücklich keinen Rückfall auf die alte Layoutgrafik.
Neuer rücknehmbarer Helfer `motion_no_legacy_fallback.py` vorbereitet:
liest die tatsächlich registrierten Legacy-Selects für Boden, Tabletop und
Chairs, erstellt eigene Original-/Transparent-Zweige und schaltet nur bei
Modus 2 mit normalen Kalibrierungspanels auf transparent. Installation leitet
die drei Legacy-Selects auf diese Zweige um. Freigegebener Motion-Zweig bleibt
direkt und unverändert, ursprüngliche Modi 0/1 bleiben pixelgleich. Masken,
Schalterreihenfolge, Projektor-/Kalibrierungsknoten und Engine unverändert.
Live-Schutzsnapshot wird ausschließlich um die drei bewusst geänderten
Select-Referenzen aktualisiert; Original-Testregistrierung bleibt erhalten.
Acht fokussierte Offline-Fälle bestanden. TD-Vorbereitung/GPU-Installation,
Raum-/Ausfall-/Modusprüfung und manuelle Speicherung noch offen.

## Vereinfachter Kamera-Wiederanlauf — 2026-10-27

Johannes findet Checkbox/Neuverbinden vor Aktivierung zu umständlich. Normaler
Pfad vereinfacht auf gemeinsamen Start und einen expliziten Aktivierungsknopf.
Motion verbindet nach Frame-Rücksprung automatisch neu, sobald frischer
TD-Automatikstatus beide Gatter aus bestätigt; gleiche Kalibrierung erforderlich,
danach zwei neue Frames. Alter Vorschlag/Revision intern erhalten, Ausgabe nach
Kameraneustart bis erfolgreicher neuer Aktivierung gesperrt. Keine automatische
Planung oder Übernahme neu gestarteter IDs. 367 Motion-Tests bestanden, sieben
optionale GPU-Fälle übersprungen. Webcontroller ohne Textport aktualisiert,
vor Neustart automatische TD-Sperre tatsächlich beobachtet, andere Dienste
erhalten. Neuer Vorschlag und physischer Neustarttest noch offen. Alte manuelle
Wiederanlaufbeschreibungen nachfolgend sind historisch/technischer Fallback.

## Automatische Erstfreigabe im laufenden TD bestanden — 2026-10-27

Nachfolgende Occlusion-Prüfung von Johannes bestanden: automatische Sperre und
Wiederfreigabe bei unveränderter ID/Revision, festen Zielen/Chairs und ohne
Reveal-Welle. Kompletter Kameraprozessausfall noch offen. Bestehender Adapter
verlangt nach Frame-Rücksprung explizites Neuverbinden und neue Web-Aktivierung;
kein ungeprüftes Wiederverwenden neu gestarteter Tisch-IDs. TD-Freigabe bleibt
nach dieser Aktivierung automatisch.

Johannes bestätigt inzwischen passenden Sichtbefund und manuelle Speicherung
des Auto-Bausteins; neuer Arbeitsdateiname noch nicht genannt. Fehlerfall- und
Kaltstartnachweis weiterhin offen, zunächst kurze Occlusion bei unverändertem
Tisch und Vorschlag geplant.

Johannes liefert nach einmaliger Installation und Web-Aktivierung den aktiven
Auto-Status: Sitzung 4012265/Revision 2/`table_01`, TD-Frame 620089, beide
Flags an, `approved: true`. Damit vollständiger Maskennachweis, spätere
Frame-Bestätigung und separate Ausgabekontrolle durchlaufen. Lesender
HTTP-Gegencheck bestätigt `td_approved: true` für dieselbe Sitzung/Revision,
Input/drei Chairs, Kamera frisch. Automatik erstmals technisch live bestätigt;
Sichtbefund, Fehlerfall-/Kaltstartprüfung und manuelle Speicherung noch offen.
Die nachfolgenden Vorbereitungsabschnitte beschreiben den vorherigen Stand.

## Automatische TD-Freigabe vorbereitet — 2026-10-27

Johannes autorisiert automatische Freigabe nach bestandenem Maskenabgleich.
Neuer eigener TD-Baustein mit Execute-DAT-Callback, ohne vorhandene Verdrahtung
oder Kalibrierung zu ersetzen: beim Start sperren, vollständigen bisherigen
Live-Nachweis ausführen, in späterem Frame Quelle bestätigen, freigeben und
separat nachprüfen. Verlust/Wechsel von Quelle/Sitzung/Revision und Study-/Tracking-
oder Kalibrierungsmodus sperren bzw. verlangen neue Prüfung. D005a bleibt erhalten.
Lokaler Status-Heartbeat wird nur passend zu Sitzung/Revision/IDs und mit TTL
akzeptiert. Launcher darf Start ohne manuelle Bestätigung erst bei frischem
Nachweis ausgeschalteter Auto-Gatter zulassen. 364 Offline-Motion-Tests bestanden,
sieben optionale GPU-Fälle übersprungen; TD-3.9-Syntax/PS-Parser geprüft.
Installation im tatsächlichen TD, Webprozess-Aktualisierung, Live-/Fehlerprüfung
und manuelle Speicherung noch offen. Kein physischer Nachweis behauptet.
Details und einmalige Textport-Vorbereitung in `MOTION_BETRIEB.md`.
Untertisch-Versuch bleibt pausiert.

## Aktueller Folgeauftrag: Start/Status/Web-Aktivierung — 2026-10-27

Folgediagnose: Johannes meldet Stillstand/fehlgeschlagenen TD-Maskenabgleich.
Alle Backend-Ketten laufen, Kamera und Scene schreiten beim lesenden Gegencheck
fort (234401 → 234500), Web-Motion Input/Revision 3/drei Chairs aktiv. Keine
Neustarts vorgenommen; TD-Detailreport offen. Vollständiger Rechnerneustart-
Ablauf einschließlich TD-Freigabe jetzt in `MOTION_BETRIEB.md` beschrieben;
Vision gehört zum gemeinsamen Start und muss nicht separat gestartet werden.
Inzwischen liefert Johannes beide TD-Nachweise: Maskencheck und separater
Live-Verify nach manueller Freigabe bestanden (Sitzung 6233135, Revision 4,
`table_01`, Frame 9248, drei Chairs, Indizes 1/1/0/1). Originalmaske erhalten;
keine abweichenden Pixel außerhalb der Ein-Pixel-Kante. Wiederaufnahme ohne
Vision-Neustart, frühere Fehlerursache offen. Physischer Sichtbefund für diesen
Web-Pfad und manuelle TD-Speicherung noch nicht bestätigt.

Johannes zieht die funktionale Vereinfachung ausdrücklich vor den Systemtest.
Learning-Format-Server läuft jetzt mit `--motion --send`: ein Web-/Motion-Prozess,
expliziter Aktivierungsknopf, vorgemerkte Einstellungen getrennt vom aktiven
Vorschlag, Kamerafrische/IDs und Fehlerstatus. Neue Planung nur beim Knopf;
Ziele und Chairs werden atomar eingefroren. Gemeinsamer PowerShell-Launcher
startet fehlende Dienste, übernimmt laufende und bietet Status. Bewusstes
Neuverbinden verlangt ausgeschaltete TD-Ausgänge, neue leere Sitzung und neue
explizite Aktivierung. TD-Freigabe bleibt manuell und wird im Web nicht behauptet.
Details: [Motion-Betrieb](MOTION_BETRIEB.md).

Offline 352 bestanden, sieben GPU-Fälle übersprungen. Nach bestätigtem
Ausgang-Aus alte UI/Tk-Ketten ersetzt; Kamera/Scene/Study/Legacy-OSC erhalten,
Webstatus frisch für `table_01`, noch ohne Vorschlag. Neuer UI→TD-Weg und
Mehrtisch-Raumabnahme offen. Untertisch bleibt pausiert. Folgender bisheriger
Prioritäten-/Lückenabgleich dokumentiert den Zustand vor diesem Anschluss.

## Neue Prioritäten: Systemtest, Standardbetrieb, UI — 2026-10-27

Johannes gibt die nächsten drei Blöcke ausdrücklich in dieser Reihenfolge vor:
Motion mit aktuellem AISI-System einschließlich bis zu fünf Tischen und Layout-
wechseln über Learning-Format-UI testen; danach als Standard einrichten;
anschließend UI grafisch modernisieren. [Konkreter Systemtestplan](TOUCHDESIGNER_MOTION_SYSTEM_TEST_PLAN.md).
Noch keine Standardumschaltung, Diensteänderung oder UI-Neugestaltung erfolgt.
Untertisch-Versuch bleibt pausiert, unabhängig von diesen Blöcken.

Anschlussabgleich zeigt wichtige Lücke: `motion_live_control.main.activate()`
liest Web-UI-State nur beim lokalen Tk-Knopf. Web-POST schreibt Einstellungen
und erhöht `layout_revision` ausschließlich bei `action=regenerate`; Motion
beobachtet diese Anforderungsrevision bisher nicht. Direkter UI→Motion-
Aktivierungspfad deshalb nicht als schon vorhanden abnehmen. Im ersten Block
gezielt prüfen/herstellen, D005a mit expliziter Aktivierung und gemeinsam
eingefrorenen Zielen/Chairs erhalten. Echte Mehrtisch-Raumprüfung getrennt von
bereits bestandener Fünftisch-Simulation protokollieren. Keine neue fachliche
Kapazitätsregel oder Kalibrierungsänderung als Nebeneffekt.

## Aktuell: Untertisch-Versuch ausdrücklich pausiert — 2026-10-27

Johannes stellt den Untertisch-Versuch wegen Zeitaufwand zurück. Keine weitere
Entwicklung, Hintergrundarbeit oder TD-Prüfung ohne neuen Auftrag. Vollständiger
kompakter Wiedereinstieg: [Untertisch-Übergabe](TOUCHDESIGNER_UNDER_TABLE_HANDOFF.md).
Weltbild und beide isolierten Float32-Projektormodelle bestanden; native
Vorbereitung/Komposition noch nicht bestanden, physischer Raumversuch nicht
durchgeführt. Letzte Sammeldiagnose: 41 Knoten vorhanden, Chair-Composite hat nur
zusätzliche Auflösungsausdrücke, Formatprobleme stammen wesentlich aus
Masken-Composite-Mischformaten und Blend-Rampen mit `useinput` ohne Kabelquelle.
Diese Befunde sind aufgezeichnet, noch nicht in weitere Korrekturen umgesetzt.
Kein Untertisch-Produktivpatch, keine Änderung von Kalibrierung/Maskierung/Diensten,
keine TD-Speicherung. Johannes beauftragt anschließend ausdrücklich Commit/Push:
Dieser Sicherungscommit enthält Grafikänderungen, Helfer/Tests und Dokumentation,
einschließlich des unvollständigen nativen Zwischenstands. Vollständige Motion-
Prüfung erneut 345 bestanden, sieben optionale GPU-Fälle übersprungen. Laufzeit-
und Kalibrierungsdaten sowie lokale Simulationsszene bleiben ungestagt erhalten.
Die Sicherung hebt die Pause nicht auf. Erster späterer Block nur native Vorbereitung anhand der Diagnose
fertigstellen; nicht erneut beim ursprünglichen Graph-Audit beginnen.

## Aktuell: native Untertisch-Komposition vorbereitet — 2026-10-27

Johannes autorisiert isolierten Vergleich in nativen Formaten einschließlich
finaler Tabletop-Komposition, keine produktive Ausgabe-/Kalibrierungsänderung.
`prepare_motion_under_table_native_probe.py` baut eigenen Container COMP
`/project1/comp_aisi_motion_under_table_native_probe`, unabhängig von entfernten
Vorgängerproben, mit eigenem synthetischem State. Native Kopien tatsächlicher
Motion-Renderer und Routing-Selects/Resampling, Floor-/Chair-Komposition,
roher Masken-Alpha-Konvention, Reorder/Tabletop-Maskierung, Content-/Layer-Switches,
180-Grad-Transforms, Warps/Uniforms, Blending, invertierter Maske und finalem Over.
Aktuelle Content-Steuerung und beide Ebenen werden nur gelesen und für eigene
Kopien eingefroren; unbekannte Dynamik führt zum Abbruch, keine Modi umgeschaltet.
Chair-Quelle einmal als Bild eingefroren, nicht als Layout neu berechnet.

Effektive native Formate statt `useinput` werden aus laufenden TOPs gelesen
(`pixelFormatName`, ältere Builds über Displayformat/Menü). Unterstützt RGBA8/
RGBA16 fixed und RGBA16/32 float, sonst Abbruch. Originalparameter/Formate bleiben
unverändert, aktive Uniforms werden nicht aus Matrix-DATs neu geladen. Eigene
Kopien mit tatsächlichen Rastern nach Kochen geprüft. Format/Größe von Out TOP
und abschließendem Output-Null müssen finalem Composite entsprechen, sonst
unerfasste Konvertierung und Abbruch. Referenz zur API:
https://docs.derivative.ca/TOP_Class

GPU-Prüfplan je Projektor: sechs Posefälle plus completed/ungültig; native
Tabletop-Vorher-/Nachher-Grafik erhalten, Over-RGBA gegen tatsächliche native
Floor-/Frontbilder mit formatabhängiger Rundungsgrenze, Zusatzkomposition,
vollständig gesperrte Maskenbereiche und opakes Tabletop mit strenger 1e-06-
Grenze. Ergebnis berichtet reale Fehler und Grenzen. Projektorgraph, weitere
benutzte Originalknoten, effektive Formate/Raster, eingefrorene Steuerung und
Engine/Reader/Revision signaturgeschützt. Nur eigene TOPs explizit gekocht;
vorhandene Masken-/Chair-Bilder einmal lesend übernommen. Keine produktive
Installationsfunktion, kein Speichern oder Window-Anschluss. Cleanup bei bereits
fehlender eigener Probe wiederholbar.
337 Offline-Tests bestanden, sieben optionale GPU-Fälle übersprungen.
Native TD-GPU-Prüfung und physischer Untertischnachweis weiterhin offen.

Erster manueller Vorbereitungsaufruf für Projektor 0 stoppt in `raw_mask_alpha`:
rohe Maske entspricht weder konstantem Alpha 1 noch Alpha=Rot innerhalb der
unterstützten Grenzen. Eigener Teilzweig durch Ausnahmebehandlung entfernt,
Produktion unverändert. Nächste lesende Diagnose: rohe und reorderte RGBA-Werte
nach Hintergrund/Innenfläche/Kante sowie tatsächliche Reorder-Kanalauswahl.
Keine neue Alpha-Konvention erfinden und keine Toleranz pauschal erhöhen.

Diagnose inzwischen vollständig durch Johannes geliefert: Raw-Render 2000²,
Hintergrund RGBA 0, Innen-RGB ca. 0,098–0,102 bei Alpha 1; Kanten-Alpha ca.
0,247/0,251/0,498/0,749/0,753. Reorder `outputred/green/blue=input1`, jeweils
Kanal `alpha`; `outputalpha=input1`, Kanal `one`, `chanmask=15`, Format `useinput`.
Reorder-Ausgabe Hintergrund (0,0,0,1), innen (1,1,1,1), Kanten RGB=Raw-Alpha.
341 Offline-Tests bestanden, sieben optionale GPU-Fälle übersprungen nach
gezielter Korrektur: `source_mask_convention` prüft genau diese Kanalzuordnung
und Pixelbeziehung mit 1e-06, keine Erhöhung der Toleranz. Synthetische Raw-Maske
liefert Coverage in A; RGB auf null gesetzt, weil die bestätigte Reorder-Stufe
diese Kanäle vollständig ignoriert. Tatsächlicher Reorder weiterhin unverändert
kopiert, Originalmaske/Material/Beleuchtung nicht korrigiert.

Die Diagnose meldet außerdem Format-Display-Eigenschaft als fehlend (`?`).
Formatauflösung unterstützt deshalb nun eindeutige Vererbung über reale TOP-
Eingänge und Select-Referenzen für TD 2022. Bei mehreren Inputs nur identische
aufgelöste Formate zulassen; Zyklen/unklare In-TOP-Reihenfolge ablehnen, keine
Bit-Tiefe raten. Erneute native Vorbereitung/GPU-Prüfung noch offen.

Zweiter tatsächlicher Aufruf erreicht Chair-Snapshot, stoppt jedoch beim
`simulation_chairs_switch` (Switch TOP) an unterschiedlichen Eingangsformaten;
eigener Teilzweig im Fehlerpfad entfernt. Resolver hatte alle Switch-Eingänge
wie gleichzeitig komponierte Inputs behandelt. Korrektur folgt dokumentierter
Auswahlsemantik: nur bei `blend=False` und ganzzahligem Index im gültigen Bereich
dem ausgewählten Eingang folgen; anderer Eingang muss kein gleiches Format haben.
Aktiviertes Blending, Bruch-/ungültige Indizes sowie unklare komponierende
Mischformate weiter ablehnen. Keine Originalauswahl geändert und keine
Toleranz gelockert. 345 Offline-Tests bestanden, sieben optionale GPU-Fälle
übersprungen; erneuter TD-Vorbereitungs-/GPU-Nachweis offen.
Referenz: https://docs.derivative.ca/Switch_TOP

Dritter nativer Vorbereitungsversuch passiert Formatauflösung und Chair-Snapshot,
stoppt jedoch an einem noch nicht freigegebenen dynamischen Parameter der
`composite_floor_with_synth_chairs` (Composite TOP). Name/Modus/Ausdruck wurden
im bisherigen Fehlertext nicht geliefert; keine Freigabe ohne lesende Erfassung.
Eigener Teilzweig entfernt, Originalgraph unverändert. `inspect_stages(op)` neu:
alle vorgesehenen Original-Kopierstufen gesammelt rein lesend erfassen,
dynamische Parameter mit evaluiertem Wert/Ausdruck/Bindung und verbleibende
Formatprobleme/Raster/GPU-Speicher melden. Keine Knoten erzeugen oder explizit
kochen, keine Flags schreiben. Fehlertext von `native_copy` nennt künftig auch
konkrete Parameterdaten. 17 fokussierte native Offline-Tests bestanden.
Native Vorbereitung/GPU-Prüfung weiterhin offen; erst tatsächliche Dynamik lesen.

## Aktuell: Untertisch-Weltbild und beide isolierten Projektormodelle bestanden — 2026-10-27

Projektor 1 inzwischen separat geprüft, `passed: true`; vorherige Projektor-0-
Probe laut Rückgabe entfernt. Sechs Fälle an (180,150)/(320,350), je 0/33/90 Grad.
Zusatzpixel 103279–238112, vollständig freier Maskenanteil 93838–230741;
maximaler RGB-Gleichungsfehler 8,195639e-08. Gesperrte Pixel je Fall
670013/671904/671294/0/2346/37780; maximaler Zusatz dort 7,748604e-07,
innerhalb Float-Toleranz 1e-06. Fall (320,350)/0 Grad hat keine vollständig
gesperrten Pixel und liefert dafür keinen Sperrnachweis. Originalmasken und
Kalibrierung unverändert, keine produktive Verbindung oder Speicherung.

Ergebnis beider Modelle: vorhandene projektorabhängige Maskierung lässt
zusätzliche Zielanteile unter dem vertikalen Footprint durch. Keine neue
Schattenmaskierung für die nächste Vergleichsstufe erforderlich. Getestet sind
isolierte Float32-Floorzweige vor Tabletop-Komposition, keine physische Projektion.
Beide temporären Proben inzwischen abwesend: Weltbild-Cleanup meldet
`removed: true`, produktive Ausgabe unverändert, nicht gespeichert; spätere
Cleanup-Aufrufe melden jeweils fehlende Probe. Keine erneute Entfernung nötig.
Nächster unabhängiger Block: native Ausgabeformate und
finale Tabletop-Komposition isoliert vergleichen, danach gegebenenfalls Raumversuch.

Nachtrag Projektor 0: tatsächlicher isolierter TD-Bericht `passed: true`, sechs
Fälle an (180,150)/(320,350) mit 0/33/90 Grad. Zusätzliche Floorpixel
49109–192815, davon vollständig freier Maskenbereich 49109–183186;
maximaler RGB-Gleichungsfehler 6,705523e-08. Erste Position hat in allen drei
Drehungen null vollständig gesperrte Bildpixel; dort keine Sperraussage ableiten.
Zweite Position hat 832113/835269/833759 vollständig gesperrte Pixel und maximalen
Zusatz 0/7,748604e-07/0, innerhalb der definierten Float-Toleranz 1e-06.
Kalibrierung/Masken/Produktion unverändert, keine physische Projektion oder
Speicherung. Projektor-1-Folgenachweis inzwischen oben ergänzt.

Johannes liefert Weltbild-Probe mit `passed: true`: zwölf GPU-Prüfgruppen,
neun Überlappungsfälle bei 0/33/90 Grad, ein/fünf Tischen und Reveal.
Zusätzliche Zielpixel je Fall 28946–164068; maximaler Muster-Floatfehler
5,9604645e-08, keine RGBA8-Abweichung. Tabletop exakt (Floatfehler 0), Sonderfälle
und Erfolg/Wiedereinblendung bestanden. Produktiver Shader, Projektorgraph,
Masken/Kalibrierung unverändert; keine Ausgabe angeschlossen oder gespeichert.

Folgehelfer `prepare_motion_under_table_projector_probe.py` erstellt eigene Probe
`/project1/comp_aisi_motion_under_table_projector_probe` (Container COMP).
Er kopiert ausschließlich bestätigte statische TOPs, niemals vollständige
Projektor-COMPs oder deren Callback-Logik. Tatsächliche Warp-Shader und konstante
Uniformwerte, bestehende Transformationen und Maskenoperationen werden kopiert;
Blend-Quellen nur lesend per Select TOP eingebunden. Keine Matrix-DATs neu laden.
Netzwerkgrenzen über eigene Select TOPs, kein externer TOP-Kabelanschluss.
Nur eigene Kopien in Float32 und bestätigtem 3840×2160-Raster, Originalformate
unverändert. Je ein Projektor zur Begrenzung des GPU-Speichers: vorbereiten,
separat prüfen, eigene Probe entfernen, dann anderen Projektor vorbereiten.

Vergleichsstufe: Floor nach bestehender äquivalenter Projektormaske, vor finalem
Tabletop-Composite. RGB-Differenz muss ausschließlich dem gleich transformierten/
geblendeten/maskierten Ziel-Zusatz entsprechen; vollständig gesperrte Maskenpixel
bekommen kein Zusatzlicht. Zwei simulierte ROI-Positionen, drei Drehungen;
berichtete zusätzliche Pixel sind modellierte Erreichbarkeit, keine Raumprüfung.
328 Offline-Tests bestanden, sieben optionale GPU-Fälle übersprungen.
TD-Projektorvergleich noch offen; native Ausgabequantisierung, finales Composite
und physischer Nachweis weiterhin getrennt erforderlich. Keine produktive
Installationsschnittstelle vorhanden.

## Aktuell: isolierter Untertisch-Zielversuch vorbereitet — 2026-10-27

Johannes beauftragt isolierte Vorbereitung, bestehende Projektormaskierung und
Kalibrierung unverändert. `prepare_motion_under_table_probe.py` liest aktuellen
Motion-Shader und baut ausschließlich eigene synthetische Vergleichs-TOPs unter
`/project1/comp_aisi_motion_under_table_probe` (Container COMP). Kein produktiver
Shaderpatch und kein Installations-/Freigabe-API. Der alternative Shader akkumuliert
Ziel-Füllanteile separat mit bestehenden Reveal-/Erfolgs-/Redisplay-Faktoren;
nach unverändertem frühem Floor-Ausschluss wird nur `floorTargets*occupied`
ergänzt. Pfeile/Welle bleiben früh maskiert, Tabletop unverändert. Alle physischen
Tische bilden gemeinsam `occupied`, nicht nur der dem Ziel zugeordnete Tisch.
Keine Veränderung des Repository-Standardshaders.

Vorbereitung/Prüfung schützt tatsächliche produktive Shadertexte, Engine/Reader/
Revision und Projektorzweige einschließlich Kalibrierungs-Table-DAT-Inhalten
durch Signaturen. Nur eigene Probe wird beschrieben/gekocht; kein Speichern,
kein Anschluss an Projektoren. Eigene Probe mit Signaturprüfung entfernbar.
GPU-Prüfplan: Differenz exakt nur zusätzlicher Zielanteil in Footprints,
übrige Pixel und Tabletop erhalten, drei Drehungen, ein/fünf Tische, Reveal,
Erfolg/Wiedereinblendung sowie ungültige/inaktive/abgeschlossene/ausgeblendete
und nicht überlappende Ziele. 319 Offline-Tests bestanden, sieben optionale
GPU-Fälle übersprungen. TD-Vorbereitung/GPU-Prüfung noch offen. Dies ist zunächst
ein Contentvergleich im Weltbild; kalibrierter Projektorbildraum- und physischer
Untertischnachweis stehen gesondert aus. Nicht als Raumfreigabe verwenden.

## Lesende Analyse: Bodenprojektion unter Tisch — 2026-10-27

Abschluss der lesenden Untersuchung: dritte TD-Ausgabe enthält vollständige
Shader-Hauptfunktionen und evaluierte Uniformwerte. Pro Projektor alle neun
aktiven h0/h1/h2-Werte zwischen Tabletop und Maske exakt gleich; gleicher
Shader-Vorspann inklusive `physicalCorrection` bestätigt. Hauptfunktionen sind
textgleich nach Normalisierung ausschließlich des Outside-ROI-Alphas
(Tabletop 0, Maske 1); gleiche Projektorpixel-/Welt-/UV-Berechnung.
Vergleich lokal aus gelieferten Texten nachgerechnet. Aktive Uniforms sind
konstant und teilweise gegenüber Matrix-DATs gerundet bzw. auf null gesetzt;
für Folgeprüfungen aktive Werte verwenden, nichts neu laden oder korrigieren.

Ergebnis: vorhandene projektorabhängige Maskierung ist eine geeignete Grundlage
für isolierten Versuch; eine neue Schattenmaske ist nach jetzigem strukturellem
Nachweis nicht zwingend nötig. Zusätzlicher früher Motion-Footprint-Ausschluss
entfernt Bildinformation auch dort, wo die spätere Projektormaske sie durchließe.
Nur Bodenzielgrafik müsste probeweise davon ausgenommen werden; nicht pauschal
`occupied` entfernen, da Reveal/Pfeile/Preview weitere Nutzer sind. Keine Änderung
implementiert oder freigegeben. Tatsächlich erreichbare Bodenfläche noch nicht
gemessen; Tischbeine/Untergestell und physische Randabweichungen nicht modelliert.
Nächster möglicher Block isolierter GPU-/Bildvergleich vor jedem produktiven
Eingriff; separate Raumprüfung erforderlich. Auftrag endet bei lesender Analyse.

Zweite tatsächliche TD-Ausgabe bestätigt Motion-Footprint-Ausschluss in
`motion_pixel` (Text DAT): `floorColor=...*(1.0-occupied)`.
Pro Projektor sind `homography_matrix`, `homography_matrix_inv` und
`correction_points` (Table DATs) zwischen Tabletop- und Masken-COMP textgleich.
Floor-/Tabletop-Outs besitzen Edge-Blending-Multiply, Masken-Out führt direkt
vom `homography_warp` (GLSL TOP) zum Out TOP. Shader enthalten zusätzliche
fest codierte `physicalCorrection`-Raster; Korrektur-DATs allein beweisen nicht
die tatsächlich verwendete Korrektur. Einige DAT-/Shaderwerte weichen ab;
keine Reparatur oder Synchronisierung autorisiert. Ausgabe begrenzt Shader
auf 100 Zeilen und schneidet entscheidende `main`-Abschnitte ab. Uniform-
`value*`-Parameter wurden bisher nicht erfasst. Diese zwei Punkte noch gezielt
lesend prüfen, bevor exakte geometrische Gleichheit/Erreichbarkeit behauptet wird.

Johannes autorisiert ausschließlich lesende Untersuchung des laufenden Graphen.
Textport bestätigt Arbeitsdatei `AISI_v3.2_motion_lab_checkpoint_20261026.12.toe`
im bekannten OneDrive-TouchDesigner-Ordner; daraus keine Speicherbestätigung
einzelner letzter Grafikpatches ableiten. Beide `comp_projector_0/1` (Base COMP)
besitzen getrennte `comp_homography_floor`, `comp_homography_table` und
`comp_homography_table_mask` (Base COMP). Masken-Out wird invertiert
(Level TOP: bei Projektor 0 `comp_homography_table_mask1`, bei 1
`invert_table_mask`) und mit Floor-Out in `floor_masked_warped1` (Composite TOP,
Multiply) multipliziert. `composite_final` (Composite TOP, Over) legt Tabletop
darüber. Projektor 1 bekommt vorgeschaltete `rotate_180_*` (Transform TOP).
Sein `comp_homography_floor_alt` ist in diesem berichteten Ausgangspfad nicht
angeschlossen. Window COMPs sind Ausgabefenster, keine weiteren Projektoren.

Damit projektorabhängige Bildraummaskierung strukturell bestätigt. Ob diese
korrekt den physischen Tischschatten abbildet, bleibt bis Einsicht in tatsächliche
Homographien/Shader/Korrekturen offen. Motion-Repository-Shader maskiert zuvor
zusätzlich pauschal den vertikalen Footprint via `(1.0-occupied)`; tatsächlichen
eingebetteten Shader ebenfalls noch lesend abgleichen. Keine Masken-/Kalibrierungs-
oder Routingänderung erfolgt. Parameter-`val` der ersten Ausgabe sind bei
Expressions/automatischer Auflösung kein Nachweis aktueller Auswahl/Bildgröße.

## Aktuell: Erfolgshaken nach einer Sekunde zusammenpoppen — abgenommen 2026-10-27

Johannes bestätigt Aufploppen, ersetzt aber den Drei-Sekunden-Fade durch
ähnliches Verschwinden nach einer Sekunde. Interpretation ausdrücklich mitgeteilt:
Ausgangsbewegung startet eine Sekunde nach Zielerreichung, dauert wie Eingang
0,32 s und ist somit bei 1,32 s beendet. `update_motion_success_pop_out.py`
ersetzt ausschließlich Haken-Overlay: Eintritt weiterhin bestehendes
`successPop(age)`, Austritt `successPop(1.32-age)`, volle Deckkraft statt Fade.
Kurze Übergröße vor Schrumpfen ist die zeitliche Umkehr des akzeptierten Eintritts.
Orientierung, Position, Runtime, Ziele/Chairs, Masken und Kalibrierung unverändert.
Eigene Probe und Rücknahme; ältere Rücknahmen erst nach diesem Folgepatch.
312 Offline-Tests bestanden, sieben optionale GPU-Fälle übersprungen.
Johannes meldet Installation `passed: true` und bestätigt am realen Tisch:
Haken ploppt auf und verschwindet nach einer Sekunde mit der Pop-Bewegung;
„Passt so“. Damit ersetzt diese Variante den Drei-Sekunden-Fade als Standard.
Vollständiger GPU-Report nicht geliefert. Separate aktuelle Live-Prüfung und
manuelle Speicherung noch offen; Sichtabnahme betrifft den Effekt, keine
umfassende Mehrtisch-/Projektorvalidierung.

## Aktuell: Haken-Aufploppen und unmittelbarer Fade abgenommen — 2026-10-27

Johannes klärt die Dauer ausdrücklich auf drei Sekunden. Neuer reversibler
Shaderpatch `update_motion_success_pop.py`: Haken wächst von null mit
Ease-out-back über 0,32 s, knapp 10 % Übergröße und Rückkehr zur bisherigen
Endgröße; Alpha fällt von Beginn an linear bis Sekunde drei auf null.
Keine Haltephase. Bestehende Hakenposition, Leserichtung, Erfolgsauflösung,
Source-Maske und Wiedereinblendung erhalten. Runtime und Erfolgszeit unverändert.
Eigene Probe/Sicherung; ältere Haken-Rücknahme erst nach Rücknahme dieses Patches.
307 Offline-Tests bestanden, sieben optionale GPU-Fälle übersprungen.
Johannes meldet Installation mit `passed: true` und bestätigt am realen Tisch:
Haken ploppt auf und fadet innerhalb von drei Sekunden aus; Gestaltung abgenommen.
Vollständiger GPU-Report nicht geliefert. Separate aktuelle Live-Prüfung nach
diesem Patch und manuelle Speicherung noch offen. Sichtbefund betrifft diesen
Effekt, keine umfassende Mehrtisch-/Raum-/Projektorvalidierung.

## Aktuelle Ergänzung: Erfolgshaken vorbereitet — 2026-10-27

Johannes bestätigt Nähe-Fade am realen Tabletop und manuelle TD-Speicherung.
Neu beauftragt: weißer Haken mittig am bisherigen Navigationskreis nach
Zielerreichung, drei Sekunden sichtbar, alles andere verschwindet wie gehabt.
`update_motion_success_check.py` ergänzt ausschließlich den Shader: Haken an
Source-Mitte, Ausrichtung aus eingefrorener Zielrotation und der zur ROI-Mitte
gewandten Längsseite; von dieser Seite lesbar. Bei exakt mittiger Zielpose bzw.
Gleichstand feste lokale +Y-Seite. Vorhandene Erfolgszeit `pulse.z` wird auch in
Phase `completed` verwendet; insgesamt drei Sekunden mit 0,18 s Ein- und
0,2 s Ausblendung. Bei erneuter Führung verschwindet der Haken; vorhandene
Wiedereinblendung bleibt erhalten. Source-Ungültigkeit blendet ihn aus.
Engine, Ankunftsschwellen, Ziel-/Chair-Bindung, Masken und Kalibrierung unverändert.
Eigene isolierte Probe und hash-gesicherte Rücknahme, keine TD-Speicherung.
299 Offline-Tests bestanden, sieben optionale GPU-Fälle übersprungen.
Installation, GPU-Nachweis im laufenden TD und physische Abnahme noch offen.

Erster manueller Einbau am Orientierungstest gestoppt, vor produktivem Schreiben.
Die Prüfung hatte Arrayzeilenrichtung ungeprüft aus Welt-Y abgeleitet. Jetzt
werden beide Achsen unabhängig anhand der bestehenden isolierten Prüfmaske bei
asymmetrischer Zielposition (180,180) bestimmt; bei uneindeutiger Zuordnung Abbruch.
Geometrische Strichpunktprüfung bleibt streng, Shader unverändert. Bestehende Probe
nach Modul-Reload wiederverwendbar. 301 Offline-Tests bestanden, sieben optionale
GPU-Fälle übersprungen; erneute GPU-Prüfung und Ursachenbestätigung in TD offen.

Nachtrag: Johannes meldet erneute Installation mit `passed: true` und ersten
Sichtbefund „schon nicht schlecht“. Vollständige GPU-Ausgabe und separate
Live-Prüfung nach Hakeninstallation nicht geliefert; Speicherung nicht bestätigt.
Nun gewünscht: stärkeres Aufploppen und sofortiger langsamer Fade. Neue Nachricht
nennt drei Minuten, bisher drei Sekunden; explizite Dauerklärung angefragt und
noch offen. Bis zur Antwort keine dauerabhängige Folgeänderung.

## Aktuelle Ergänzung: Zielkreis mit Nähe-Fade — 2026-10-27

Johannes möchte die mittige Zielringschablone wie Ausrichtungshilfen erst in
Nähe sehen. Einziger Shader-Eingriff vorbereitet: `templateRing` mit bereits
vorhandenem `guides` multiplizieren, Einblendung über 45→15 cm und bestehende
Erfolgsabblendung gemeinsam. Keine zweite Distanz-/Zeitlogik. Source-Navigationskreis,
solide Zielfläche ohne Trennstrich, Zielpose/Chairs/Revision, Masken und Runtime
unverändert. `update_motion_target_template_fade.py` mit eigener Probe/Sicherung.
Temporärer Trennlinienvergleich muss vor Folgepatch als Standard abgeschlossen
sein, damit dessen alte Vergleichssicherung nicht unbemerkt ungültig wird.
293 Motion-Tests bestanden, sieben optionale GPU-Fälle übersprungen. Inzwischen
in TD installiert, sieben GPU-Prüfgruppen bestanden: Zielkreis folgt 45→15-cm-Fade,
bei 30 cm halb sichtbar, nahe Fassung bei drei Drehungen erhalten, Erfolg und
Wiedereinblendung erhalten. Boden RGBA8-pixelgleich, maximaler Floatfehler 0;
Engine/Ziele/Masken unverändert. Separate aktive Live-Prüfung bestanden:
Session 2610399/Revision 3, `table_01`, drei Chairs, Indizes 1/1/0/1;
Originalmaske aktiv, Kantenfehler 0,0000153 cm, Original-/Vergleichsmaske je
204490 beleuchtete Pixel, keine Pixel außerhalb der Ein-Pixel-Grenze.
Johannes bestätigt inzwischen den Nähe-Fade am realen Tabletop und manuelle
TD-Speicherung; neuer Dateiname nicht erneut gemeldet.

## Aktueller Standard: solide weiße Zielfläche — 2026-10-27

Johannes vergleicht die Darstellung ohne Trennstrich, nimmt sie als deutlich
besser ab und bestimmt sie ausdrücklich wieder als Standard. Repository-Shader
setzt Linienanteil dauerhaft auf null: solide weiße Zielgrundfläche auf Boden
und Tabletop, kein zusätzlich außenliegender Rahmen. Ursprünglicher Footprint,
Masken, Navigation/Feedback und Schatten, Source-Striche/Zielhilfen, Erfolg und
Wiedereinblendung bleiben erhalten. Kein neuer Layout-/ID-/Revisionswechsel.

`compare_motion_target_divider.adopt_as_default(op)` zur gezielten Übernahme der
laufenden Vergleichsansicht ergänzt: tatsächlichen versteckten Shader/Hashes
prüfen, nur temporären Marker durch Standardmarker ersetzen, eigene Sicherung
des vorherigen sichtbaren Linienstands behalten und temporäre Vergleichssitzung
schließen. Unterstützt auch bekannte sichtbare Fassung. Lokale Folgeänderungen
verhindern blindes Überschreiben. Explizite Rücknahme nur über eigene Sicherung;
historische Grafikversuche nicht erneut installieren. 287 Motion-Tests bestanden,
sieben optionale GPU-Fälle übersprungen. Physische Sichtabnahme ohne Trennstrich
vorhanden; tatsächliche Standardübernahme per TD-Aufruf, separate abschließende
Live-Prüfausgabe und manuelle TD-Speicherung noch offen. Kein automatischer
Save/Commit/Push.

## Aktueller letzter Versuch: dünne innere Trennlinie ohne Außenrahmen — 2026-10-27

Johannes ist mit den gleichen 2,5-cm-Bändern noch nicht überzeugt und wünscht
0,4-cm-Trennlinie sowie keinerlei zusätzlichen Bodenrahmen außerhalb ursprünglichen
Tisch-Footprints. Neuer Entwurf: auf beiden Oberflächen weißer Randstreifen
weiter nominal 2,5 cm, Trennlinie zwischen 2,5 und 2,9 cm innen (Mitte 2,7 cm),
weißer Kern erhalten. Boden verwendet wieder denselben Ziel-Füllmaskenwert wie
Tabletop; kein äußerer Streifen mehr. Bestehende Bodenpfeile, Masken, Erfolg,
Navigation und Wiedereinblendung unverändert. Keine Ziel-/ID-/Revisionsänderung.

`update_motion_target_inner_divider.py` liest bekannten tatsächlich installierten
2,5-cm-Bänder-Shader und ersetzt nur Linienfunktion/Boden-Grunddarstellung,
eigener GPU-Probe/Hash-Backup. GPU soll drei Drehungen, dünne innere Linie,
weiße Zwischenflächen und leeren früheren Außenrahmenbereich auch bei deckungs-
gleichen Posen prüfen. 280 Motion-Tests bestanden, sieben optionale GPU-Fälle
übersprungen. Inzwischen im laufenden TD installiert: fünf GPU-Prüfgruppen
bestanden, 0/33/90 Grad, Tabletop-Innenlinie/Weißfüllung und Erfolg/Fade erhalten.
Maximaler Muster-Floatfehler 7,510185e-05, höchstens eine RGBA8-Stufe an geglätteten
Kanten; keine exakte Diagnose-Rastergleichheit behauptet. Engine/Ziele/Masken
unverändert. Separate aktive Live-Prüfung und physische Abnahme offen, nichts
gespeichert und keine neue Layoutaktivierung.

## Aktueller Wunsch: gleiche Rahmen-/Trennbreite und Tracking-ID-Wechsel — 2026-10-27

Aktueller Grafiknachweis: `target_equal_bands.install(op)` passed, acht TD-GPU-
Prüfungen bestanden. Weiße und transparente Streifen je 2,5 cm, 0/33/90 Grad,
Außenrahmen trotz deckungsgleicher Source-Maske sichtbar, Erfolg/Fade erhalten.
Unabhängiger Mustervergleich an geglätteten Kanten maximal 8,147955e-05 und
eine RGBA8-Stufe; keine bitgleiche Diagnose behauptet. Engine/Ziele/Masken
unverändert, nichts gespeichert. Frühere Linien-/4-cm-Entwürfe abgelöst.
Freigaben bleiben aus; aktueller ausgeschalteter Maskenabgleich, kontrollierte
Freigabe für Session 2610399/Revision 3 und separate aktive/physische Prüfung
noch offen. Keine erneute Aktivierung erforderlich.

Aktueller Wiederaufnahmenachweis: Johannes hat bewusst neuen Input-Vorschlag
aktiviert; Controller zeigt `table_01`, Revision 3 und drei Chairs. Nach noch
älterer Statusausgabe (Frame 68432/Revision 2) aktualisiert der separate
`live_output.verify(op)`-Check erfolgreich auf Session 2610399/Revision 3,
Main/Chairs Frame 69385, Rasterframe 69371. `table_01` eindeutig an unveränderte
Originalmaske `rect_setup_mask_geo_00` zugeordnet, maximaler Kantenfehler
0,063567 cm, Original/Kopie je 204505 beleuchtete Pixel, keine Pixel außerhalb
Ein-Pixel-Grenze; maximale RGBA-Differenz 0,254902, keine exakte Rastergleichheit
behauptet. Sechs doppelte Maskenreferenzen erhalten. Freigaben aus, Indizes 0.
Keine Neustarts/automatische ID-Umhängung; neue Ziele/Chairs nur durch bewusste
Aktivierung. Grafik-GPU-Vorbereitung kann bei weiterhin ausgeschalteter Ausgabe
fortgesetzt werden, aktive Freigabe/Prüfung danach offen.

Aktueller TD-Nachweis nach Verdeckung: alle Ausgabefreigaben aus, Indizes 0;
Motion frisch, Session 2610399/Revision 2, Frame 65770, gebundene ID `table_00`
mit valid=False. Kein Streamstillstand: alte aktivierte Identität ist nicht
mehr beobachtet, neue Kamera-ID ist `table_01`. Ziele korrekt beibehalten.
Wiederaufnahme geplant durch bewusste explizite Aktivierung im Controller:
neue ID-Zuordnung, einmalig neue Ziele/Chairs/Revision, anschließend frischer
Originalmaskenabgleich bei ausgeschalteter Ausgabe. Kein stilles Umhängen,
keine automatischen Neustarts oder Vorschlagsänderungen.

Johannes wünscht transparente Trennung ebenso breit wie weißen Rahmenstreifen,
beides so breit wie Ausrichtungshilfen. Deren aktuelle Shaderbreite beträgt
2,5 cm (`coverage(d-1.25)`). Neue Grafik offline vorbereitet: Boden weißer
Streifen 0–2,5 cm außen, transparente Trennung 0–2,5 cm innen; Tabletop weißer
Streifen 0–2,5 cm innen, transparente Trennung 2,5–5 cm innen. Weißer Kern,
ursprüngliche Masken/Erfolg erhalten. `update_motion_target_equal_bands.py`
prüft tatsächliche Ausrichtungshilfenbreite, bekannte Vorgänger, eigene Probe/
Hash-Sicherung. 274 Motion-Tests bestanden, sieben optionale GPU-Fälle übersprungen.
Inzwischen gemäß aktuellem Grafiknachweis oben in TD installiert; noch keine Speicherung.

Gleichzeitig Verdeckungsproblem gemeldet. Lesender Befund: alle ursprünglichen
Prozessketten laufen, Kamera-/Controllerfehlerprotokolle ohne Traceback; Szene
Frame 58531 enthält `table_01` statt vorherigem `table_00`, kalibrierte Pose
vorhanden. Das ist ein ID-Wechsel, kein beobachteter Prozessabbruch. Bestehendes
Motion-Proposal ist noch nicht als auf neue ID gebunden bestätigt; keine stille
Umhängung/Neuberechnung und keine Neustarts. Vor weiterem Grafik-Livetest
Freigaben per manuellem Textport deaktivieren, tatsächliche Stream-/Zielbindung
und Maskenzuordnung prüfen. Neue explizite Aktivierung nur bewusst durch Johannes.

## Aktuelle Korrektur: 4-cm-Rahmenstreifen — 2026-10-27

Johannes korrigiert die Bedeutung: weißer Rahmenstreifen etwa halber bisheriger
Breite, ausdrücklich 4 cm; auf Boden außerhalb ursprünglicher Fläche, auf
Tabletop weiter innerhalb. Feine 0,3-cm-Linie war missverstanden. Auf ausdrücklichen
Rücknahmewunsch letzten Oberflächen-Linienpatch im Repository gezielt entfernt,
vorherigen Einzel-Linienzustand wiederhergestellt; sieben fokussierte Tests
bestanden. Kein TD-Rollback bestätigt, keine automatische TD-Änderung/Speicherung.
Johannes bestätigt anschließend weiße Innenfläche mit feiner Trennlinie.
Korrigierter Patch `update_motion_target_frame_strip.py` vorbereitet: Boden-
Rahmenstreifen 0–4 cm außerhalb ursprünglicher Kontur, feine Trennlinie am
ursprünglichen Rand; Tabletop-Trennlinie 4 cm innen. Weißer Kern beibehalten,
feine Linie wieder 0,6 cm. Rahmenbreite als SDF-Konstantabstand, dadurch saubere
gleichmäßige Rundungen; keine zusätzliche 1-cm-Versetzung aus Fehlentwurf.
Bekannte Rahmen-/Drei-Linien-/Einzellinien-/missverstandene Außenlinienvarianten
werden gezielt korrigiert, unbekannte lokale Änderungen verweigert. Eigene
Probe/Hash-Sicherung, physische Masken und Erfolgsablauf unverändert. GPU soll
4-cm-Lage, weiße Innenfläche, erhaltenen Bodenrahmen bei deckungsgleichen Posen,
Tabletop-Erfolg und Fade prüfen. 268 Motion-Tests bestanden, sieben optionale
GPU-Fälle übersprungen. Noch nicht in TD installiert; GPU-/Live-/physische Abnahme
offen. Keine automatische Speicherung oder neue Layoutaktivierung.

## Aktuelle Präzisierung: Bodenlinie außen, Tabletop-Linie innen — 2026-10-27

Johannes verlangt halbe bisherige Linienstärke, auf dem Boden außerhalb der
ursprünglichen Fläche, auf dem Tabletop weiter innen. Erstentwurf 0,3 cm Breite
(vorher 0,6), äußere Bodenlinie 1 cm außerhalb als positive Abstandslinie der
ursprünglichen kanonischen SDF; weiße Zielfüllung auf Boden ohne innere Linie.
Tabletop-Linie bei 10 cm Randabstand innen, ebenfalls 0,3 cm. Der 1-cm-Abstand
schafft auch Raum zur unveränderten Kanten-Antialiasmaske. Keine Änderung von
physischer Maske, Zielgeometrie, Erfolg oder Projektor-/Weltparametern. Nur die
gezeichnete Bodenlinie erweitert bewusst den grafischen Außenbereich.

`update_motion_target_surface_lines.py` mit eigenem Probe/Backup vorbereitet.
Bekannte Vorgänger (drei Linien oder einzelne 0,6-cm-Linie) werden gezielt
unterstützt, keine unbekannten lokalen Varianten überschrieben. GPU soll drei
Drehungen und hypothetisch deckungsgleichen Source/Ziel bei ausdrücklich noch
aktiver Führungsphase prüfen: Außenlinie bleibt trotz bestehender Source-Maske
erhalten. Tatsächlicher Erfolg blendet weiterhin gemäß bestehendem Ablauf aus;
keine dauerhafte Erfolgsmarkierung eingeführt. 260 Motion-Tests bestanden,
sieben optionale GPU-Fälle übersprungen. Noch nicht in TD installiert; GPU-/Live-
Prüfung und physischer Masken-/Projektionsnachweis offen, nichts gespeichert.

## Aktuelle Präzisierung: eine dünnere äußere Trennlinie — 2026-10-27

Johannes meldet Drei-Linien-Installation `passed: true` und bestätigt sichtbare
weiße Fläche mit drei gerundeten Linien, wünscht aber nur die äußerste Linie.
Folgeentwurf: geschlossene Linie bei 10 cm Abstand zum Außenrand beibehalten,
Breite von 1 auf 0,6 cm reduziert; innere Linien bei 20/30 cm entfernt.
Nur Muster-Hilfsfunktion geändert; weiße Füllung, äußerer Umriss, Rundung,
Navigation/Feedback/Einpasshilfen, Erfolg und Wiedereinblendung bleiben erhalten.

`update_motion_target_single_line.py` mit eigener Probe/Hash-Sicherung vorbereitet.
GPU soll drei Drehungen, unveränderten Außenbereich, beide entfernten Linien,
schmaler erhaltene äußere Linie und erhaltene Erfolgs-/Feedback-/Fade-Funktion
vor Einbau prüfen. Rücknahme stellt zunächst drei Linien wieder her; ältere
Sicherungen unverändert. 253 Motion-Tests bestanden, sieben optionale GPU-Fälle
übersprungen. Neuer Einzel-Linien-Patch noch nicht in TD installiert, GPU-/Live-
und physische Abnahme offen. Keine Speicherung/Commit/Push.

## Aktueller Gestaltungsversuch: weiße Füllung mit gerundeten Linien — 2026-10-27

Johannes bestätigt den Rahmen sichtbar, wünscht nun wieder weiße Füllung mit
ineinanderliegenden Rechtecklinien gemäß neuer Referenz. Alle Linienecken
sauber gerundet. Erstentwurf: drei geschlossene transparente Linien bei
10/20/30 cm Abstand vom ursprünglichen Außenrand, 1 cm Linienbreite, gleicher
kanonischer Rundungsradius an allen Rechtecken. Boden und Tabletop verwenden
dasselbe Muster. Ursprünglicher äußerer Umriss, physische Masken und Kalibrierung
bleiben erhalten. Linien nach Feedbackkomposition ausgespart, damit sie auch
im grünen Bereich sichtbar bleiben; Navigation und Einpasshilfen darüber.
Zielhilfen auf weißer Füllung wieder ausgespart, bei Linienüberquerung weiß;
Source-Striche weiter weiß. Erfolg und weiche Wiedereinblendung erhalten.

`update_motion_target_divisions.py` vorbereitet: nur bekannte Rahmenblöcke im
tatsächlichen lokalen Shader ersetzen, eigener Probe/Hash-Backup. Rücknahme
zunächst Linienversuch (stellt Rahmen wieder her), danach bei Bedarf früheren
Rahmenversuch (stellt frühere Füllung wieder her). 245 Offline-Tests bestanden,
sieben optionale GPU-Fälle übersprungen. Neuer Linienversuch noch nicht in TD
installiert; GPU-/Live-Prüfung und physische Abnahme offen, nichts gespeichert.
Für den vorherigen Rahmen wurde nur der Sichtbefund geliefert, kein detaillierter
GPU-/Installationsbericht; diesen Nachweis nicht ergänzend erfinden.

Erster Linien-Einbau vor produktiver Änderung gestoppt: unabhängiger GPU-
Diagnosezweig weicht an geglätteter Linie maximal 6,330013e-05 ab, Bodenwert
0,4793027 statt 0,4793660; kein Pixel über 1/255. Produktiver Shader unverändert
bestätigt. Vergleich präzisiert: Kanten-Zwischenwerte maximal 1e-4, flache
weiße/transparente Bereiche weiter 1e-6, quantisierte Differenz maximal eine
RGBA8-Stufe. Keine Änderung des Shaders oder Lockerung des Außenbereichschutzes.
Drei Regressionstests ergänzt; 248 Motion-Tests bestanden, sieben optionale
GPU-Fälle übersprungen. Wiederholung mit bestehendem Probe noch offen.

## Aktueller Gestaltungsversuch: Zielkontur statt Füllung — 2026-10-27

Johannes wünscht gemäß Referenzbild die gleiche dicke, abgerundete Zielkontur
auf Boden und Tabletop statt durchgehend weißer Füllung. Reversibler Erstentwurf:
8 cm breite Kontur nach innen, äußerer Zielumriss und Zielpose unverändert;
innere und äußere Kontur über bestehende `roundedRect`-Funktion mit abgerundeten
Ecken. Kein Eingriff in Tischmasken, Homographien, Weltmaßstab oder Projektoren.
Nur weiße Zielfüllung ersetzt; grünes Feedback bleibt am gesamten ursprünglichen
Zielumriss beschnitten, nicht nur am weißen Rand. Mittige Zielringschablone und
Zielstriche im jetzt offenen Inneren weiß, bei Überlagerung weißer Kontur weiter
als Aussparung. Source-Striche weiß, Navigationskreis, Erfolg und Wiedereinblendung
erhalten. Keine Runtime-/OSC-/Ziel-/Chair-/Revisionsänderung.

`update_motion_target_outline.py` vorbereitet: gezielter Patch des tatsächlichen
lokalen Shaders, eigener isolierter GPU-Vergleich vor Einbau und eigene
Hash-Rücknahmesicherung. Kein Überschreiben vorhandener Komponenten. Offline
239 Motion-Tests bestanden, sieben optionale GPU-Fälle übersprungen. Laufender
TD-Graph noch nicht geändert; TD-GPU-Prüfung/Einbau, separate aktive Live-Prüfung
und physische Gestaltungsabnahme offen. Keine automatische Speicherung oder
zusätzlicher Commit/Push beauftragt.

## Wiederaufnahme am Laborrechner — 2026-10-27

Backend auf Johannes’ Wunsch gestartet. Git weiterhin `vision/wip-dark-proposals`,
gesicherter Stand `a9cb57a`; lokale Laufzeitdaten erhalten. Vorher keine Python-
Dienste aktiv. TD PID 13188 bereits gestartet mit Argument
`AISI_v3.2_motion_lab_checkpoint_20261026.8.toe`; tatsächliche Projektdatei noch
per Textport bestätigen, kein Bildschirmzugriff und keine automatische TD-Speicherung.

Genau eine Prozesskette je Dienst: Kamera 4748→7164, Szenenadapter 4232→13376
(`--poll-seconds 0.01`), Lernformat-Server 8092→6380, Study-Control 21684→20912
(`--mode 2`), Legacy-OSC 18948→10888 (beide Study-Bindings, frische Live-Szene,
Intervall 0,05 s), Motion-Controller 22004→14244 (`--send`). PIDs sind Momentaufnahme.
Bestehende Kamera-/Kalibrierungsargumente erhalten, temporäres großes OBB-Debuglog
nicht erneut aktiviert. Alte Kamera-JSONL vor Writer-Neustart gesichert (69767610
Bytes); alte Szene ebenfalls gesichert. Kalibrierungshash weiter
`480026FBE25BFE6503ECDF103A0070E7F14B3E6A8830F48BA31B95CCE1018AE9`.

Backend-Nachweis: Szene Frame 407→994, stabile ID `table_00`, Lernformat-HTTP
`http://127.0.0.1:8080/` antwortet 200, UDP 9000 gehört TD PID 13188;
kein Traceback/Exception/Error in den Start-Fehlerprotokollen. Startargumente,
Backups und Nachweise unter `data/aisi/debug/startup_20261027_074804/`.
Johannes hat den neuen Motion-Vorschlag inzwischen explizit aktiviert und bei
deaktivierten Freigaben geprüft: `live_output.verify(op)` passed, Session
2610399/Revision 2, Main/Chairs Frame 2768, Rasterframe 2755, `table_00`, drei
Chairs, Originalmaske aktiv, alle vier Indizes 0. Original/Kopie je 204562
beleuchtete Pixel, kein Pixel außerhalb Ein-Pixel-Grenze, Konturkantenfehler
maximal 0,0000216 cm; RGBA-Maximaldifferenz 0,254902, keine exakte Rastergleichheit
behauptet. Sechs doppelte Maskenreferenzen erhalten. Anschließend kontrollierte
Freigabe und separate aktive Prüfung durch Johannes bestätigt: `verify` passed,
gleiche Session 2610399/Revision 2, Main/Chairs Frame 7132, Rasterframe 7118,
drei Chairs, Indizes 1/1/0/1, Originalmaske aktiv. Konturkantenfehler 0 cm,
Original/Kopie je 204571 beleuchtete Pixel, kein Pixel außerhalb Ein-Pixel-Grenze,
RGBA-Maximaldifferenz 0,254902. Johannes bestätigt physisch Motion-Grafik und drei
Chairs sichtbar, Source/Feedback folgen der Bewegung, Ziele/Chairs bleiben fest.
Wiederanlauf abgeschlossen; kein vollständiger neuer Raum-/Projektornachweis.
Tatsächliche Projektdatei per Textport noch offen, bisher nur Startargument
`.8.toe` bekannt. Keine automatische TD-Speicherung oder Git-Commit/Push heute.

## Tagesabschluss Motion-Labor — 2026-10-26

Johannes nimmt die weiche Wiedereinblendung mit „passt“ ab und beauftragt
Sicherung/Push des aktuellen Stands. Arbeitsbranch und Pushziel:
`vision/wip-dark-proposals` / `origin/vision/wip-dark-proposals`; vorhandene sechs
lokale Commits werden mitübertragen. Motion-Übergabe `0681604` ist mit aktivem
Laborstand und dessen Source-Verfügbarkeit/Laufzeitstatus im Worktree integriert.
Aktuelle produktive Motion-/CV-Quellen einschließlich vorhandenem kalibrierten
Vorassoziationsfilter, relevante lokale Laborhelfer, Tests und Übergabedokumente
gehören zum Sicherungsstand. Laufzeit-/Debugdaten, Kamerabilder, Training und
Kalibrierungsdateien bleiben lokal ungestagt; simulierte `live_scene.json` bleibt
als lokale Laufzeitänderung erhalten. Kein Reset oder Branchwechsel.

Aktueller Grafikstand: Feedback auf Zielkontur begrenzt, helleres Grün und
früheres Halo-Wachstum; radialer Navigationsschatten; rein distanzbasierter Kreis
mit halbem Radius bereits bei 20 cm, zielgerichtet auf null schrumpfender Pfeil;
Zielringschablone und spätere Striche (45→15 cm), Source-Striche weiß und Zielstriche
ausgespart; weiche Wiederaufnahme nach Erfolg über 0,35 s. Tischziele und Chairs
bleiben bis zur nächsten erfolgreichen expliziten Aktivierung gemeinsam fest.

Nachweise getrennt: Abschluss offline 257 Motion-/Labor-/Editor-Fälle (250
bestanden, sieben optionale GPU-Fälle übersprungen) plus 69 CV-Fälle bestanden;
gesamt 319 bestanden. Zahlreiche isolierte GPU-Prüfungen im laufenden TD, zuletzt
sechs Wiedereinblendungsfälle bestanden. Letzte zurückgemeldete aktive
`live_output.verify(op)`-Prüfung vor den letzten Source-Strich-/Wachstums-/Runtime-
Änderungen: Session 2207576/Revision 2, Main/Chairs Frame 136446, drei Chairs,
Indizes 1/1/0/1, Originalmaske aktiv. Johannes’ physische Sichtabnahme bestätigt
das letzte Wiedereinblenden; keine separate abschließende technische Prüfausgabe
danach geliefert und keine vollständige neue Raum-/Projektorvalidierung behauptet.

TD speichert Johannes manuell. Letzte bestätigte Arbeitsdatei:
`C:/Users/johan/OneDrive/Dokumente/AISI_DEV/touchdesigner/AISI_v3.2_motion_lab_checkpoint_20261026.6.toe`.
Finaler Speichername und erneutes Öffnen noch nicht bestätigt. Master `AISI_v2.toe`
unverändert und nicht im Commit. Nächster Start: manuell gespeicherten Checkpoint
erneut öffnen, tatsächlichen Dateinamen und `live_output.verify(op)` erfassen.

Historischer abgeschlossener Lab-Prüfstand vor Motion:
`C:\Users\johan\OneDrive\Dokumente\AISI_DEV\touchdesigner\AISI_v2.151_tabletop_targets_validated.toe`.
Johannes bestätigt Speicherung und erneutes Öffnen: Sources folgen flüssig,
nur eigene Zielkonturen auf Tabletops, alles korrekt. Stabile Vorschläge,
Format-/Count-/Moduswechsel und unveränderte Bodenausgabe zuvor gebündelt
live bestätigt; 125 fokussierte Tests bestanden. Kalibrierung/Homographien/
Edge-Blend unverändert. Folgeblock abgeschlossen, keine weiteren Live-Schritte
daraus offen. Die folgenden Zwischenberichte sind historischer Verlauf.
Git-Übergabe des Folgeblocks am 2026-10-26 auf
`codex/lab-inbetriebnahme-20261021`, anschließend an `cac6365`.
Nur produktive Quellen, Tests und Projektdokumentation; Laufzeitdaten,
Debug-Ausgaben, Kalibrierung und fremde Vision-Änderungen ausgeschlossen.
Die physische TD-Datei 151 ist nicht Bestandteil der Git-Übergabe.

## Aktuelle Motion-Integration am Windows-Laborrechner — 2026-10-26

Aktueller Auftrag: Nach erfolgreicher Einpassung und anschließendem Herausbewegen
Führung weich wieder einblenden. Aktiven `motion_runtime`-Uploader per Textport
gelesen; minimale Ergänzung am bestehenden Übergang `completed → guidance`
vorbereitet. Neue rein visuelle Sichtbarkeit steigt über 0,35 s mit Smoothstep
von 0 auf 1, Floor-/Tabletop-Content pro Tisch gemeinsam. Keine Engine-Ersetzung,
Klassenänderung, Ziel-/Chair-/Revisionsänderung oder neue Reveal-Welle;
Reaktivierungsschwellen unverändert. Pro-ID-Ereignisse im eigenen flüchtigen
COMP-Speicher, bei neuer Layoutrevision verworfen. Interne freie State-Spalte 5
liefert Sichtbarkeit und Versionsmarker; alte State-TOPs ohne Marker bleiben
voll sichtbar, OSC-Vertrag unverändert.
`update_motion_redisplay.py` vorbereitet: gezielter Runtime-/Shaderpatch mit
Zwei-DAT-Sicherung und Wiederherstellung bei Kompilierfehler; GPU-Prüfung vor
Installation. `motion_redisplay.py` als kleiner Darstellungshelfer. Offline
233 Motion-Tests bestanden, sieben optionale GPU-Fälle übersprungen; tatsächlicher
`td_tick`-Pfad einschließlich Reaktivierung, ungültigem Tracking und gleicher
Engine/Revision geprüft. Inzwischen in TD installiert, sechs GPU-Prüfungen
bestanden: gemeinsame premultiplizierte Floor-/Tabletop-Sichtbarkeiten
0/0,15625/0,5/0,84375/1 sowie unveränderter Legacy-State ohne Marker.
Engine nicht zurückgesetzt, Ziele/Masken unverändert. Johannes bestätigt den
Erfolgs-/Reaktivierungsablauf anschließend mit „passt“. Separate abschließende
aktive Live-Prüfausgabe noch nicht geliefert; TD-Speicherung erfolgt manuell durch Johannes.

Aktueller Auftrag vorbereitet: Source-Ausrichtungsstriche durchgehend weiß,
auch über weißer Zielfläche; Zielstriche weiterhin als Aussparungen. Grüner
Feedbackkreis erreicht bei gleichem Annäherungsfortschritt früher größere
Radien: nur Radiuskurve mit `clamp(h*1.2,0,1)` beschleunigt, 35/81,4-cm-Endpunkte
erhalten. Halo-Richtung, Kontakt-/Runtime-Zeitkonstanten, Erfolgslogik, Zielclip,
Navigationskreis und bisheriges Timing unverändert. Eigener reversibler Helfer
`update_motion_feedback_response.py` mit isoliertem GPU-Vergleich vorbereitet.
223 Offline-Tests bestanden, sieben optionale GPU-Fälle übersprungen. In TD
installiert, vier GPU-Prüfgruppen bestanden: Source-Striche weiß/Zielstriche
ausgespart, früheres Halo-Wachstum bei gleichen Endpunkten, Erfolgsauflösung
nach Hilfen-Ausblendung erhalten und Boden RGBA8-pixelgleich (Floatfehler maximal
5,96e-08). Engine/Ziele/Masken unverändert. Separate aktive Live-Prüfung und
physische Abnahme offen, nichts gespeichert.

Aktuelle Nachjustierung installiert bestätigt: Kreis erreicht halben Radius/Schablonengröße
bereits bei 20 statt 8 cm Abstand (ferner Endpunkt weiter 65 cm). Source-/Zielstriche
blenden später über 45→15 statt 65→25 cm ein. Zielringschablone unverändert;
Pfeilschrumpfung und Erfolgsanimation unverändert. Nur zwei bekannte Shaderausdrücke
gezielt ersetzt, keine Runtime-/Schwellen-/Geometrieänderung.
`update_motion_alignment_timing.py` mit eigenem Probe/Backup vorbereitet; tatsächliche
Ausdrücke im isolierten GPU-Diagnosezweig geprüft, keine zweite Kurvenimplementierung.
218 Offline-Tests bestanden, sieben optionale GPU-Fälle übersprungen. Tatsächlicher
Shader-SHA stimmt mit Timing-Sicherung überein; Shader entspricht exakt dem Patch
auf deren vorherigen Text. Prüfzweig bereits entfernt, kein erneuter Einbau nötig.
Detaillierter TD-GPU-Bericht nicht zurückgemeldet; separate aktive Live-Prüfung
inzwischen bestanden: Session 2207576/Revision 2, Main/Chairs Frame 136446,
drei Chairs, Indizes 1/1/0/1, Originalmaske aktiv. Rasterframe 136430 ohne Pixel
außerhalb der Ein-Pixel-Grenze, Konturkantenfehler maximal 0,0000153 cm.
Johannes nimmt früheren Größenabgleich und spätere Striche am realen Tabletop
mit „Ist gut so“ ab. Timinganpassung abgeschlossen. Arbeitsdatei durch Textport bestätigt:
`C:/Users/johan/OneDrive/Dokumente/AISI_DEV/touchdesigner/AISI_v3.2_motion_lab_checkpoint_20261026.6.toe`.
Speicherung der aktuellen Timingänderung dadurch allein nicht bestätigt.

Aktuelle Präzisierung: Kreisgröße nur aus Distanz, nicht aus bisher kombiniertem
Positions-/Orientierungsfortschritt. Shader-Patch vorbereitet: Radius 29 →
14,5 cm über Distanz 65 → 8 cm. Pfeilrichtung separat aus tatsächlichem Vektor
zum Zielmittelpunkt, ohne bisherige Winkelumschaltung bei 3 cm; Pfeil innerhalb
12 cm nach innen auf null skaliert. Bei Zielüberquerung ist der Pfeil daher
bereits sehr klein. Erfolgskontraktion, Zielring, Striche und Runtime-Schwellen
unverändert. `update_motion_distance_navigation.py` mit eigenem Probe/Backup
vorbereitet. GPU prüft Unabhängigkeit vom Fortschrittswert, Pfeilschrumpfung,
Richtung, Erfolgserhalt und Boden; separate Pfeildiagnose verwendet exakt die
Produktionsformel, auch wenn transparente Pfeilform auf Weiß sonst verdeckt wäre.
213 Offline-Tests bestanden, sieben optionale GPU-Fälle übersprungen. Inzwischen
im laufenden TD installiert, fünf GPU-Prüfgruppen bestanden: sieben Distanzen
unabhängig vom bisherigen Fortschrittswert, schrumpfender Pfeil mit Alphasummen
322,147/75,708/2/0 bei 12/6/2/0 cm, Zielrichtung und Erfolgsanimation erhalten.
Boden RGBA8-pixelgleich und maximaler Floatfehler 0, Engine/Ziele/Masken unverändert.
Separate aktive Live-Prüfung und physische Abnahme offen, nichts gespeichert.

Aktueller Versuch nach drei Referenzbildern von Johannes: Navigationskreis auf
Tabletop schrumpft vor Erfolg höchstens auf halben Radius (29 → 14,5 cm).
Mittige transparente Zielringschablone, Außenradius 14,5 cm; Source-/Zielstriche
entlang der jeweils eigenen Tischlängsachse. Striche blenden zwischen 65 und
25 cm Distanz ein. Auf Zielfläche transparente Aussparungen, Source-Striche
außerhalb weiß. Bei Erfolg zieht der weiße Kreis innerhalb 0,18 s nach innen
auf null; Hilfen verschwinden, bestehende grüne Erfolgsauflösung bleibt.
Alle Werte sind reversible Gestaltungsparameter; keine Änderung von
Erfolgsschwellen, Runtime, Tischgeometrie oder Ziel-/Chair-Aktivierung.
`update_motion_alignment_guides.py` inzwischen erfolgreich in TD installiert;
eigener GPU-Prüfzweig und Hash-Sicherung. Bestehender Transaktionshelfer für
Helligkeitsänderung über optionale Argumente wiederverwendet; alte Aufrufe
unverändert. Offline 206 Motion-Tests bestanden, sieben optionale GPU-Fälle
übersprungen. TD-GPU-/Live-Prüfung und physische Abnahme offen. Erster Einbau
vor Änderung gestoppt: Boden-Floatbilder weichen maximal 5,96e-08 ab (759 Pixel),
produktiver Shader nachweislich unverändert. Vergleich nun auf Float32-Rundung
begrenzt und zusätzlich exakte RGBA8-Gleichheit verlangt.
Nach zwei zusätzlichen Regressionstests 208 Motion-Tests bestanden, sieben
optionale GPU-Fälle übersprungen. Weiterer Prüfstopp: Weiß-Prüffall bei 60 cm
verlangte fälschlich volle Deckkraft trotz beabsichtigtem Distanzfade. Prüffall
auf 20 cm/90-Grad-Ziel korrigiert, ohne Shaderänderung; acht fokussierte Tests
bestanden. Anschließend neun tatsächliche TD-GPU-Prüfungen bestanden: beide
Kreisgrößen, mittige Ringschablone, weiße/transparente nahe Striche, drei
Zieldrehungen, Erfolgskontraktion und Verschwinden. Boden RGBA8-pixelgleich,
maximaler Floatfehler 5,96e-08; Engine/Ziele/Masken unverändert. Separate aktive
Live-Prüfung und physische Sichtabnahme noch offen. Keine Speicherung.

Aktueller Gestaltungsauftrag: Feedbackgrün etwas heller/greller. Nur Halo-RGB
von 0/236/101 auf 0/255/110 angehoben, etwa acht Prozent; Alpha, Verlauf,
Zielbegrenzung, Navigation/Schatten und Erfolgsfarbe unverändert. Reversibler
Helfer `update_motion_feedback_brightness.py` vorbereitet: tatsächlichen lokalen
Shader lesen, isolierte GPU-Prüfung vor Einbau, keine automatische Speicherung.
Eigene Rücknahmesicherung; ältere Sicherungen unverändert. Rücknahmen bei
Bedarf in umgekehrter Reihenfolge: Aufhellung, Begrenzung, Schatten.
Offline 200 Motion-Tests bestanden, sieben optionale GPU-Fälle übersprungen.
TD-Einbau und sechs GPU-Vergleiche inzwischen durch Johannes bestätigt:
bei 0/33/90 Grad 25828/20627/17027 hellere Pixel, bei 33 Grad mit Reveal
ebenfalls 20627. Boden, Alpha und Ausgabe außerhalb der Zielfläche pixelgleich;
Erfolg und Feedback aus unverändert, keine Engine-/Ziel-/Maskenänderung.
Separate aktive Live-Prüfung und physische Sichtabnahme offen; nichts gespeichert.

Neuer Gestaltungsauftrag: grünes Feedback auf dem Tabletop an der weißen
Zielfläche abschneiden. Bisher nur durch Ist-Tischmaske begrenzt; im Shader
nun Feedbackalpha zusätzlich mit bestehendem `targetMask` multipliziert.
Keine Zielverkleinerung und keine Änderung von Navigationskreis, radialem
Schatten oder vollflächigem Erfolg. Reversibler Helfer
`update_motion_feedback_clip.py` liest den tatsächlichen lokalen Shader und
installiert erst nach isoliertem GPU-Vergleich (Drehungen 0/33/90 Grad,
Reveal, Erfolg, Feedback aus). Eigene Rücknahmesicherung; bestehende
Schattensicherung unverändert. Bei Rücknahme mehrerer Änderungen zuerst
Feedback-Begrenzung zurücknehmen, danach gegebenenfalls Schatten.
Offline 192 Motion-Tests bestanden, sieben optionale GPU-Fälle übersprungen.
TD-GPU-Prüfung und Einbau inzwischen durch Johannes bestätigt: sechs Vergleiche
bestanden, bei 0/33/90 Grad 4859/10229/13781 überstehende grüne Pixel entfernt,
mit Reveal bei 33 Grad ebenfalls 10229. Zielinneres/Boden unverändert, Erfolg
und deaktiviertes Feedback pixelgleich. Keine Engine-/Ziel-/Maskenänderung.
Separate aktive Live-Prüfung ebenfalls bestanden: Session 2207576/Revision 2,
Main/Chairs Frame 69531, drei Chairs, Indizes 1/1/0/1, Originalmaske aktiv.
Rasterframe 69516 ohne Pixel außerhalb der Ein-Pixel-Grenze, maximaler
Konturkantenfehler 0,035473 cm. Johannes bestätigt am realen Tabletop Grün
innerhalb der Zielfläche bei Bewegung/Drehung; Navigationskreis und Schatten
passen weiterhin. Anpassung abgeschlossen, Speicherung noch nicht bestätigt.

Der gestalterisch verworfene 5-cm-Tabletop-Rand ist vollständig zurückgenommen.
Johannes bestätigt TD-Rollback `restored: true`, Rand verschwunden und vorherige
Darstellung wiederhergestellt. Repository-Shader ebenfalls zurückgesetzt;
eigene Inset-Helfer und Tests entfernt. Zielgeometrie wurde nie verkleinert,
Masken/Kalibrierung nicht verändert, nichts gespeichert oder committet.
CV-Größenfilter 140/70 cm und übrige Motion-Integration bleiben erhalten.
Historische Inset-Befunde stehen ausschließlich im Motion-Design-Verlauf.

Neuer Gestaltungsauftrag: Navigationskreis mit Schlagschatten von umgebender
weißer Tabletop-Zielfläche abheben. Erste Fassung mit 2,5/2,5-cm-Versatz im TD
installiert und GPU-geprüft, gestalterisch durch Johannes präzisiert: Schatten
soll statisch mittig und auf allen Seiten homogen um den Navigationskreis
liegen, unabhängig vom grünen Feedback. Radiale Fassung ohne Versatz vorbereitet;
Kreisinneres und Richtungsausschnitt erhalten. Weicher Übergang 2 cm,
maximale Stärke 65 Prozent; Weichheit/Stärke skalieren mit Navigation.
Kein Schatten bei Kreisgröße 0 oder Erfolg, Puls darüber unverändert.
Helfer `update_motion_navigation_shadow.py` liest tatsächlichen lokalen Shader,
bereitet separaten GPU-Vergleich vor und installiert erst nach positivem
Kontrast-/Innenflächen-/Bodenvergleich. Lokale Änderungen erhalten, Rücknahme
gesichert, keine Engine-/Masken-/Zieländerung. 188 Motion-Fälle, 181 bestanden
und sieben optionale native GPU-Fälle übersprungen. TD-GPU-Prüfung und Einbau
inzwischen bestanden: Navigation 1/0,35 mit 1511/165 Schattenpixeln, ohne Kreis
und bei Erfolg jeweils 0. Kreisinneres und Boden pixelgleich, Engine/Ziele/
Masken erhalten. Vorheriger Shader im Motion-COMP gesichert, Vergleichszweig
entfernt. Diese Nachweise betreffen die erste versetzte Fassung. Neue GPU-
Prüfung verlangt zusätzlich Rundumsymmetrie und gleiche Schattenform mit/ohne
grünes Feedback; Upgrade schützt bestehende Rücknahmesicherung auf die ursprüngliche
Fassung ohne Schatten. Radiale Fassung inzwischen im laufenden TD installiert:
fünf GPU-Vergleiche bestanden, 1184/108 Schattenpixel bei Navigation 1/0,35,
mit grünem Feedback ebenfalls 1184, ohne Kreis/bei Erfolg jeweils 0.
Rundumsymmetrie und Feedback-Unabhängigkeit geprüft; Kreisinneres/Boden sowie
Engine/Ziele/Masken unverändert. Offline: 184 Motion-Tests bestanden, sieben
optionale native GPU-Fälle übersprungen. Johannes nimmt die radiale Fassung
gestalterisch am realen Tabletop mit „ist gut so“ ab. Separate aktive
Live-Prüfung ebenfalls bestanden: Session 2207576/Revision 2, Main/Chairs Frame
57607, drei Chairs, Indizes 1/1/0/1, Originalmaske aktiv. Rasterframe 57591:
je 204328 beleuchtete Pixel, keine Pixel außerhalb der Ein-Pixel-Grenze;
maximaler Geometriefehler 0,0000216 cm. Schattenanpassung abgeschlossen.
Johannes bestätigt anschließende manuelle Speicherung. Neuer vollständiger
Dateiname und erneutes Öffnen noch nicht bestätigt; keine vollständige neue
Raum-/Projektorvalidierung durchgeführt.

Aktueller Folgeauftrag: projizierte Bodenziele aus CV ausschließen. Original-
Kamerabild per vorhandenem c-Hotkey lokal erfasst, ohne Bildschirmzugriff:
`data/vision/debug/hard_examples/hard_example_20261026_141545_094_f260943_000.png`.
Mit unverändertem Rect-OBB-Modell, Levels 200 und Tabletop-Kalibrierung erkennt
YOLO real 164,684×82,959 cm (Konfidenz 0,956) und Projektion 128,392×66,061 cm
(0,929). Vorhandene Minima 125/55 cm lassen beide durch. Nur untere Kanten-
grenzen im bestehenden Vor-Assoziationsfilter auf 140/70 cm angehoben,
Maxima 200/110 cm und übrige Gates unverändert. Das ist ein Rect-Laborfilter,
kein genereller Scout- oder Verdeckungsnachweis. Kalibrierung unangetastet.

64 fokussierte Tests bestanden. Vollständiger CPU-Replay desselben Bilds über
drei Pipeline-Frames: zwei rohe OBBs, genau eine Größenablehnung pro Frame,
nur `table_00` ab zweitem Frame, im dritten regulär zugeordnet. Nachweis unter
`data/vision/debug/motion_floor_size_filter_20261026/summary.json`; nicht mit
Live-Abnahme verwechseln. Nach bestätigtem TD-Bypass CV/Controller gezielt neu
gestartet, weil die Konstanten beim Prozessstart geladen werden. Vor neuem
Writer alte Kamera-JSONL gesichert; Kamera-Framezähler/Trackzustand beginnen
neu, deshalb Controller bewusst neu initialisiert und Vorschlag erst explizit
aktiviert. Keine alte Maskenfreigabe übernommen.
Sicherung alter Kamera-JSONL (127230619 Bytes) und exakter Argumente unter
`data/aisi/debug/cv_floor_filter_restart_20261026_142506/`. Neue Kamera-
Prozesskette 16524→5348, Controller 39368→25636; Stderr leer. Adapter
1280→26468 und Legacy-Sender 36888→16552 weitergeführt, Kamera/Szene
frisch mit `table_00`. Aktuelle UI: Input/drei Teilnehmende. Neuer Vorschlag
explizit aktiviert, neue Session 2207576/Revision 2 zunächst ausgeschaltet
gegen Originalmaske geprüft und anschließend freigegeben. Separate aktive
Prüfung passed: Vision-Count 1, Main und drei Chairs Frame 11388, Rasterbeleg
Frame 11373, Indizes 1/1/0/1, Originalmaske aktiv. Kantenfehler 0,0000152588 cm,
Original/Kopie je 204794 helle Pixel, kein Pixel außerhalb des Ein-Pixel-Rands.
Rohe RGBA-Abweichung 0,2549019754, keine Pixelgleichheit behaupten.

Live-Filteraudit Frames 11960–12359: in allen 400 Frames zwei rohe OBBs,
genau eine Größenablehnung, ausschließlich `table_00` und keine neuen IDs.
Letzte Kandidaten: real 160,881×82,055 cm akzeptiert; Projektion
137,648×64,872 cm trotz Konfidenz 0,912 wegen beider Mindestkanten verworfen.
Nachweis `data/aisi/debug/cv_floor_filter_restart_20261026_142506/live_filter_verified_summary.json`.
Damit Filter live für diese Raumstichprobe bestätigt; kein allgemeiner
Mehrtisch-/Verdeckungs-/Positionsmatrix-Nachweis. Diagnose-JSONL bleibt beim
aktuellen CV-Start aktiv; beim nächsten regulären Start ursprüngliche Argumente
ohne temporäres Audit verwenden. Kein weiterer Neustart nur zum Abschalten
dieser Diagnose. Gespeicherte TD-Datei bleibt ausgeschaltet/unverändert.

Motion-Commit `0681604` ist mit aktuellem Labor-HEAD `0b08f4c` im Worktree
integriert; Branch/Index/Commits unverändert, lokale Vision-Änderungen und
Source-Verfügbarkeits-/Laufzeitstatuskorrekturen erhalten. Git wird unter dem
Eigentümerkonto ohne safe.directory-Änderung gelesen.

Ursprünglich geöffnete Arbeitsdatei:
`C:/Users/johan/OneDrive/Dokumente/AISI_DEV/touchdesigner/AISI_v3.1_preview_validated.toe`.
Inzwischen manuell als neue Arbeitsdatei gespeichert und per WORKFILE bestätigt:
`C:/Users/johan/OneDrive/Dokumente/AISI_DEV/touchdesigner/AISI_v3.2_motion_lab_checkpoint_20261026.toe`.
Datenträgerprüfung: 2187326 Bytes, Änderungszeit 2026-10-26 13:23:03 lokal.
Graph nur über manuelle Textport-Ausgaben untersucht/verändert, kein
Bildschirmzugriff, keine automatische Speicherung. Die physische Masterdatei,
Kalibrierung, Maskenreihenfolge, Projektortransforms und Edge Blend unverändert.

Fünftisch-Generator-/Chair-Simulation für Input/Groupwork/Discussion einzeln
live bestätigt: Source/Feedback folgen, Ziele/Chairs bleiben bei Bewegung und
UI-Änderung fest. Erfolgreiche Neuaktivierung erzeugt genau eine Welle und
vollständige neue Chair-Menge; ungültige 16 Personen erhalten den Vorschlag.
Technischer Modusvergleich in dieser Simulation: Tracking/Study vier Zweige 0,
AISI vier Zweige 1. Keine vollständige Count-/Teilnehmendenmatrix.

Echte Quelle: `MotionLiveAdapter` liest neue kalibrierte Kamera-Frames mit
stabilen IDs; `motion_live_control` berechnet nur beim expliziten Klick aus
frischen Istposen, friert Ziele/Chairs gemeinsam ein und setzt beim Timeout
Source-Validität/Chair-Sichtbarkeit aus. Ein anfänglich erfülltes Ziel bleibt
für spätere Guidance-Reaktivierung berechtigt; der fehlerhafte active=False-
Anschluss wurde korrigiert. Bestehende 18-cm-/12°-Reaktivierungsschwellen,
Generatorziele und Motion-Shader unverändert.

Nach Doppelketten-Konsolidierung und späterem ungeklärtem Prozessende wurden
nur fehlende Runtime-Ketten gezielt wiederhergestellt; je ein Scene-Adapter,
Legacy-Sender mit Freshness/Study-Bindings und korrigierter Motion-Controller
nachgewiesen. Kamera, TD, Study-Control und Formatserver weiterverwendet.
Protokolle/gesicherte Startargumente liegen unversioniert unter
`data/aisi/debug/motion_recovery_20261026_112559/` und den dokumentierten
Vorgängerordnern. Neustartzuverlässigkeit ist nicht nachgewiesen.

Letzter aktiver Nachweis vor manueller Sicherung: Floor/Tabletop/Chairs Index 1,
Simulationsmaske 0, vorhandene Originalmaske aktiv. Kamera-ID `table_00`,
Session 4463454, Layoutrevision 2, zwei Chairs mit identischer frischer
Framebindung. Eindeutiger Pose-/Rasterabgleich bestanden; letzter Kantenfehler
0,0094368052 cm (Rasterframe 108813, Main/Chairs Frame 108829), keine Pixel außerhalb des Ein-Pixel-Rands. Rohe RGBA-Abweichung
0,4980392158, daher keine Pixelgleichheit behaupten. Die sechs doppelten
Geometriereferenzen bleiben erhalten. `live_output` erhält die ursprüngliche
Testregistrierung und kann ausschließlich die eigene Chair-Gatteränderung
reversibel zurücknehmen; nach Live-Vorbereitung diesen Prüfer statt des alten
`motion_test.verify` verwenden.

Johannes bestätigt nun die Funktion am realen Tisch im Kontext des
angefragten 25–30-cm-Bewegungstests. Das ist eine erste Ein-Tisch-Input-
Raumstichprobe mit zwei Chairs, keine allgemeine Projektionsabnahme.
Offline: 175 Motion-Tests bestanden, sieben optionale GPU-Fälle übersprungen;
TD- und physische Nachweise werden davon getrennt geführt.

Johannes bestätigt zusätzlich: UI-Änderung 2→3 ohne Klick erhält Ziel und zwei
Chairs; nach kurzer Verdeckung kehrt `table_00` zurück. Live-Verifikation danach
bestanden: Session 4463454/Revision 2, Frame 28623, zwei Chairs, Kantenfehler
0,0090214 cm und keine Pixel außerhalb des Ein-Pixel-Rands. Die Anzeige während
der Verdeckung ist damit noch nicht separat bestätigt.

Auch der Modusvergleich mit echter Quelle ist durch Johannes bestätigt:
Tracking und Study vier Indizes 0, AISI 1/1/0/1; nach Rückkehr dieselben Ziele
und zwei Chairs ohne neue Reveal-Welle.

Die vier nachgewiesenen eingebetteten Mac-Importzeilen sind auf Windows
umgestellt; beide Runtime-DATs kompilieren. Während der Nachprüfung erfasste
der Prüfer veralteten Chair-State und verglich später neue Quellen mit einem
älteren Maskenprüfstand. Die Fehler schalteten die Freigaben jeweils aus.
Gemeinsame Poseprobe ohne GPU-Arbeit zeigte übereinstimmende Quellen/Masken;
ein zusätzlicher Geo-Cook änderte nichts.

Die korrigierte Prüferfassung erhält den strengen Pose-/Rasterbeleg vor
GPU-Arbeit und erfasst danach nur die aktuelle Kamera-/Chair-Bindung mit
explizitem Chair-State-Cook. Beide Prüfstände müssen dieselben IDs und dasselbe
Layout haben; Rasterframe wird separat ausgegeben. Kein Timeout oder
Maskentoleranzwert geändert. 21 fokussierte Prüfertests bestehen. Nach Reload
beider Helfer sind ausgeschaltete und aktive TD-Prüfung bestanden; aktueller
Nachweis siehe oben. Die getrennten Senderpfade bleiben unabhängig; dies ist
keine Garantie kontinuierlicher Pose-/Maskensynchronität bei Bewegung.

Johannes bestätigt auch nach den jüngsten Änderungen denselben sichtbaren
Vorschlag mit zwei Chairs ohne neue Reveal-Welle; Source und Feedback folgen
der Bewegung, Ziele und Chairs bleiben fest. Dies ergänzt den technischen
Nachweis um die aktuelle Ein-Tisch-Input-Sichtprobe.

Die zusätzliche DAT-Inventur fand nur Chair-Runtime ohne Import-Bootstrap.
Dort sind jetzt drei Windows-Bootstrapzeilen vorangestellt, Originaltext erhalten;
strenge `chair_owned`-Prüfung davor und danach, ausschließlich eigener Texthash
fortgeschrieben. Kompilierung und aktive Live-Verifikation bestanden. Cold-Import
des generierten Texts offline unter `-I -S` bestanden; frischer TD-Start
inzwischen ebenfalls bestätigt, siehe unten.

Aktuell beide Live-Freigaben und Simulation aus; ausgeschaltete Prüfung
bestanden, alle Indizes 0. Neue Arbeitskopie anschließend manuell gespeichert,
siehe oben. Vorheriger Dateiname war frei; keine automatische Speicherung.
Frischer TD-Prozess bestätigt: PID 2352, Start 13:27:44 lokal, neue Arbeitsdatei
im Prozessargument und WORKFILE. Beide State-Cooks fehlerfrei, Repository-
Importe ohne manuelle sys.path-Ergänzung, alle Freigaben/Indizes 0.
`verify` passed: Session 4463454/Revision 2, Main und zwei Chairs Frame 123453,
Maskenbeleg Frame 123438, Kantenfehler 0,0000076294 cm; beide Masken 204284
helle Pixel, keine Pixel außerhalb des Ein-Pixel-Rands. Kamera/Sender liefen
weiter; dies ist kein Windows-/Gesamtruntime-Neustartnachweis.
Anschließend vorhandenen Vorschlag für diese Sitzung wieder eingeschaltet und
separat aktiv geprüft: passed, Indizes 1/1/0/1, Originalmaske aktiv; Session
4463454/Revision 2, Main und zwei Chairs Frame 125442. Rasterbeleg Frame
125426, Kantenfehler 0 cm, beide Masken 204275 helle Pixel, keine Pixel
außerhalb des Ein-Pixel-Rands. Keine Pixelgleichheit: rohe RGBA-Abweichung
0,2549019754. Keine neue Layoutaktivierung oder erneute Speicherung.
Gespeicherter Startzustand bleibt aus, aktuelle Sitzung aktiv. Nächster
Schritt der Sichtbestätigung ebenfalls abgeschlossen: Johannes sieht Motion-
Grafik und zwei Chairs, Source/Feedback folgen der Bewegung, Ziele/Chairs
bleiben fest. Ein-Tisch-Input-Inbetriebnahme mit manueller Sicherung und
frischem TD-Start damit technisch und als physische Stichprobe bestätigt.
Nächster unabhängiger Block: zunächst Motion-Freigaben ausschalten, zweiten
realen Tisch erfassen und getrennte stabile IDs/Originalmasken nachweisen;
erst danach explizite neue Vorschlagsaktivierung und erneute Quellfreigabe.
Mehrtisch-/Fünftisch-Raumabnahme, Jitter/Leistung und vollständiger Wiederanlauf
offen. Kein Commit.
[Einzelbefunde](TOUCHDESIGNER_MOTION_DESIGN.md#aktiver-nachweis-nach-pfad--und-prüferkorrektur--2026-10-26).

## 1. Purpose and workstreams

AISI is a research prototype for adaptive, spatially augmented learning environments. It senses and tracks room objects, represents the room in a shared metric coordinate system, generates or loads target configurations, and communicates spatial transformations through projections on the floor and on tabletops.

The repository contains three related but distinct workstreams:

1. general AISI layout generation (`input`, `groupwork`, `discussion`);
2. the controlled dual-surface Study pipeline;
3. live computer vision/tracking and TouchDesigner integration.

Do not assume that a change in one workstream should alter the others.

## 2. Evidence levels

Use these labels when reporting status:

- **Repository-confirmed:** inspected or tested in the local checkout.
- **History-reported:** reported in prior project work but not re-run in the current task.
- **Physical-room-reported:** tested in the physical setup; cannot be established from repository checks alone.

The current worktree is the source of truth for code state. Branch, HEAD, and dirty-file status must be checked live with Git rather than stored here.

## 3. Coordinate system and physical setup

Repository-confirmed:

- world/ROI: `500 × 500 cm`, X and Y each spanning `0–500`;
- world center: `(250, 250) cm`;
- TouchDesigner scale: `1 cm = 0.0052 TD units`;
- TD mapping: `tx = (x_cm - 250) * 0.0052`, `ty = -(y_cm - 250) * 0.0052`;
- the simulation-to-OSC path negates source and target rotations before transmission.

Physical-room-reported:

- two Optoma UHZ36STe ceiling projectors;
- overlapping projection footprints with edge blending;
- separate floor and tabletop homographies per projector;
- tabletop plane at `z = 74 cm`;
- floor and tabletop calibration considered complete and protected;
- a nominal projected `50 × 50 cm` square measured approximately `50 × 49 cm` after calibration.

The calibration pipeline must not be changed as collateral work.

## 4. Main runtime paths

Lab-Inbetriebnahme am 2026-10-19: bestehende Kamera-/Adapter-Pipeline geprüft,
Tracking-only-Sender gezielt durch Layout-Sender ersetzt und Teilnehmer-Vorschau
aktiviert. Live-Protokoll meldet zwei Tische und vier Chairs im Groupwork;
physische Sichtprüfung noch offen. Startbefehl, Rückkehr zum Tracking-Betrieb
und Git-Ausführungskontext: [Lab-Inbetriebnahme](LAB_INBETRIEBNAHME.md).
Erste Raumprüfung meldet auf beiden Achsen gespiegelte AISI-Ausgabe. Die
gespeicherte TD-Version 144 bestätigt entgegengesetzte Positionsvorzeichen
zwischen AISI-Callbacks und Tracking-/Tischmasken. Rücknehmbare Korrektur
vorbereitet und offline geprüft.
Johannes bestätigt anschließend die manuelle Ausführung und reale Prüfung:
Source-Konturen auf den Tischen, Ziele und Chairs korrekt ausgerichtet.
Dieser Nachweis gilt für die aktuelle Zwei-Tisch-Groupwork-Stichprobe;
Speichern/erneutes Öffnen und weitere Formatprüfungen bleiben offen.
Johannes bestätigt anschließend auch Input, Discussion und Groupwork im Raum:
Source-Konturen folgen den Tischen, Ziele/Chairs plausibel, ruhiges Bild.
Qualitative erste Live-Stichprobe, keine vollständige Count-Matrix.
AISI-Tabletop-Pfeile laufen bei großem Overlap über den Target-Mittelpunkt;
rücknehmbare Begrenzung am Zielmittelpunkt offline geprüft und zur manuellen
Live-Ausführung vorbereitet. Details im Lab-Handoff.
Weitere Lab-Bestätigung am 2026-10-19: Pfeil-Endpunkt/Toleranz und weiße
2,5-cm-Chair-Konturen manuell angewandt und im Raum bestätigt. Gemeinsamer
Formatwechsel Input → Groupwork 4/2 → Discussion 4 mit zwei realen Tischen
bestanden: vier Chairs, keine alten Elemente, folgende Source und ruhiges
Bild. Count-/Gruppen- und Off/On-Stichproben im Lab-Handoff. Speicherung und
erneuter Öffnungscheck der manuellen TD-Korrekturen weiterhin unbestätigt.
Moduswechsel AISI → Tracking → AISI anschließend ebenfalls live bestätigt.
Study-Control blendet auf neuen Auftrag alle Study-Bedienelemente außerhalb
von Study aus und enthält keine manuelle Target-Eingabe mehr. Controller,
Trial-Ziele und OSC unverändert; 30 Tests und Tkinter-Moduscheck bestanden.
Johannes bestätigt anschließend Neustart und manuelle Sichtprüfung:
Study-Einstellungen nur in Study, Target-Eingabe entfernt, Wechsel AISI →
Study → Tracking → AISI funktioniert. Speicherung/erneutes Öffnen der
manuellen TD-Korrekturen bleibt der nächste Prüfblock.
Johannes hat anschließend `AISI_v2.146_lab_layout_validated.toe` manuell
gespeichert. Die Korrekturen sind in einer temporär expandierten Kopie
nachgewiesen (einschließlich Template und 16 Chair-Ringen). Dieser Stand
ist der neue gespeicherte Lab-Prüfstand; erneutes Öffnen noch offen.
Erneutes Öffnen von Version 146 anschließend durch Johannes bestätigt:
Source-Folge, vier weiße Chairs, Discussion-Ziele und Pfeil-Endpunkt/Toleranz
funktionieren ohne erneute Helferausführung. Weitere Count-/Parkprüfung folgt.
Weitere Zwei-Tisch-Stichproben (Input bis sechs Personen, Groupwork 6/1 und
6/2, Park-/Aktivwechsel, gebündelte Formatwechsel) sowie Sender-/Adapter-
Wiederanlauf im Raum bestätigt; Einzelbelege im Lab-Handoff. Vor Vision-
Neustart Runtime-Leerszenenfehler behoben: explizit geleerte Live-Szenen
liefern Null-Counts statt Layout-Ablehnung. 37 OSC-/Adapter-Tests bestanden;
neuer Sender aktiv. Vision-Neustart und anschließende Formatwechsel technisch
bestanden, visuelle Gesamtbestätigung noch offen.
Johannes bestätigt anschließend Vision- und gemeinsamen Python-Wiederanlauf
visuell; regulärer Zwei-Tisch-Inbetriebnahmeblock abgeschlossen.
Neuer Block: spontane Tischzugänge/-abgänge und fehlende Tische für neue
Anfragen. Learning Format UI zeigt jetzt tatsächlichen Senderstatus und
Planerfehler, ohne eigene Layoutberechnung. Auf Johannes' Entscheidung
bleibt die letzte gültige Anzeige bei Ablehnung stehen und wird in der UI
als veraltet gekennzeichnet. 47 Tests und Live-HTTP-Fehler/Recovery bestanden;
physische Tischzahlwechsel noch offen. [Handoff](LAB_TISCHANZAHL.md).
Johannes bestätigt anschließend den physischen Tischzahlwechsel: dritter
Tisch hinein/heraus korrekt berücksichtigt, UI-Warnung bei Discussion 7
und fehlenden Tischen; Warnung verschwindet bei geringerem Count oder
Hinzufügen eines vierten Tisches. Prüfblock abgeschlossen. Lesender
Endzustand: Discussion 6, drei reale Tische, sechs Chairs, Status ready.
Anschließend vier reale Tische erkannt und Discussion 6 → 7 → 6 gebündelt
technisch/live bestätigt: stabile Scene Order, Zweiergruppe/Parken ↔
Vier-Tisch-Rechteck, keine beanstandeten Altlasten/Unruhe. Endzustand
Discussion 6 mit vier realen Tischen; höhere Discussion-Counts noch offen.
Discussion 8–12 einschließlich Eckplätzen und Rückkehr zu acht anschließend
technisch/live bestätigt: plausible Ergänzung, vollständiges Entfernen,
ruhiges Bild und keine alten Elemente. Groupwork mit vier Tischen folgt.
Vier-Tisch-Groupwork (vier Gruppen/zwei Pairs, acht/zwölf Personen) sowie
Fünf-Tisch-Discussion 12 → 13 → 14 → 15 → 12 danach live bestätigt.
Kontrollviewer-Source-Auswahl war zwischenzeitlich leer; native Pfadauswahl
repariert sie. Johannes bestätigt fünf folgende Source-Konturen nach fünftem
Tischzugang, unveränderte Projektion und ruhige Topologie-/Chair-Wechsel.
Aktuell gespeicherte TD-Version bleibt 146; neue Viewer-Korrektur noch nicht
als gespeichert bestätigt. Fünf-Tisch-Input ist der nächste Prüfblock.
Fünf-Tisch-Input 4 → 8 → 10 → 12 → 15 → 4 anschließend live bestätigt:
plausibles Parken/Verdichten, alle 15 Chairs sichtbar, Rückkehr ohne alte
Kreise und ruhiges Bild. Endzustand Input 4. Offene gebündelte Prüfblöcke
stehen in TODO und im Tischanzahl-Handoff; als Nächstes Fünf-Tisch-Groupwork.
Fünf-Tisch-Groupwork und gemeinsamer Fünf-Tisch-Format-/Modus-/15-Chair-Off/
On-Test danach live bestätigt. Aktiver Tischabgang/-rückkehr technisch
erfolgreich; Johannes präzisiert, dass nur Ziele veraltet stehen bleiben
dürfen, während fehlende Sources verschwinden müssen. Sender/UI dafür
erweitert (additive Source-Verfügbarkeit, ID-gebundene Slots, 51 Tests),
neu geladen. Manueller AISI-Sichtbarkeitshelfer und Nachprüfung noch offen.
Johannes bestätigt anschließend Helferausführung und Abgang-/Rückkehrtest
als funktionierend. Fehlende Sources/Pfeile verschwinden, Live-Sources und
veralteter Zielvorschlag sind getrennt. Neue manuelle TD-Sicherung der seit
Version 146 angewandten Viewer-/Floor-Pfeil-/Source-Sichtbarkeitskorrekturen
bleibt offen. Weitere Robustheits-/Projektionsprüfungen siehe TODO.

### General simulation/layout path

```text
Room Editor
→ data/aisi/scenes/simulated/live_scene.json
→ scene interpretation
→ target structure/layout synthesis
→ constraint repair
→ OSC
→ TouchDesigner
```

Main entry points:

- `aisi.app.sim_room_editor`
- `aisi.app.learning_format_server`
- `aisi.app.sim_scene_to_osc`

State files:

- `data/aisi/scenes/simulated/live_scene.json`
- `data/aisi/state/learning_format.json`

Validate each format individually through Room Editor, Learning-Format-Interface, and OSC before a short cross-format pass.

### Study path

```text
Study trial definition
→ Study controller/state machine
→ tracking binding and live source pose
→ OSC /study channels
→ TouchDesigner Study visuals
→ append-only JSONL logging
→ study_metrics analysis
```

Key files:

- `data/aisi/study/trials.json`
- `src/aisi/app/study_trials.py`
- `src/aisi/app/study_control.py`
- `src/aisi/app/study_tracking.py`
- `src/aisi/app/study_logging.py`
- `src/aisi/analysis/study_metrics.py`

Die aktive Study-Definition ist `pilot_v8`. T1–T3, Familiarization und sämtliche Teilnehmerstartpositionen bleiben unverändert aus `pilot_v7`. Nur alle T4-Tischposen werden gemeinsam um `+11 cm` in Welt-Y verschoben; X, Rotation und A/B-Transformation bleiben erhalten. Practice bleibt aus Trial-Zählern und `study_metrics` ausgeschlossen.

### Vision/tracking path

Current code is primarily under `src/vision/`; earlier sensing/replay infrastructure remains under `src/aisi_sensing/`.

Current baseline:

- Rect tables use OBB geometry transformed to world coordinates;
- multi-table association, occlusion handling, and reacquisition were stabilized;
- tracking-only projection renders an inner tabletop contour and outer floor contour;
- adaptive smoothing is lighter during motion and stronger at rest.

Treat tracking as frozen unless a task explicitly concerns tracking.

## 5. TouchDesigner architecture

The authoritative manually maintained project is external to the repository:

`C:\Users\johan\OneDrive\Dokumente\AISI_DEV\touchdesigner\AISI_v2.toe`

Repository builders and `.toe` snapshots are references, not guaranteed representations of the active physical graph.

Aktueller Chair-Stand am 2026-10-07:

- Aktueller manuell gespeicherter Stand am 2026-10-07: `AISI_v2.141_coherent_chairs_validated.toe`, von Johannes nach erfolgreicher Radius-Reparatur bestätigt und dateisystemseitig verifiziert. In einer temporär expandierten Kopie sind Radius-Bindung und Callback für Template + 15 Instanzen nachgewiesen. Der frühere bereinigte Stand 137 wurde erneut geöffnet und geprüft; ein erneuter Öffnungscheck von 141 wird nicht behauptet. Speichern bleibt ausschließlich manuell durch Johannes.
- Der optionale Floor-Zweig unter `comp_layout_proposal` erreicht beide bestehenden Projektorpfade.
- Der bestehende `chairs`-Zweig ist auf 15 Slots erweitert. Bei Count 7 sind sieben Radien positiv und acht Null; die Positionen werden laufend gebunden.
- Debug und regulärer Floor verwenden dieselbe zentrale Chair-Geometrie. Der Floor verwendet `cam1`, 2000×2000 und addiert Chairs über den zentralen Composite.
- Der manuell ausgeführte Bildvergleich besteht: optionaler Floor Off bitgleich, beide Projektorausgänge reagieren auf On, Tabletop/Table-Mask bitgleich und Debug-/Preview-Schalter unabhängig vom regulären Zusatz.
- Die Viewer sind im laufenden Projekt nach `comp_layout_proposal/chair_debug` und `comp_layout_proposal/tables_chairs_virtual_preview` (jeweils Container COMP) kopiert. Johannes bestätigt den Migrationscheck: alle vier Viewerbilder und die sechs geprüften Floor-/Tabletop-/Masken-/Projektorbilder bitgleich. Die anschließende Bereinigung ist ebenfalls bestätigt: keine externen Referenzen, alte Top-Level-Komponenten, doppelte Debug-Geometrien und alter Chair-Zweig in `comp_output` entfernt; alle zehn geprüften Bilder bitgleich. Der bereinigte Stand ist in Version 137 gespeichert und nach erneutem Öffnen geprüft.
- Count 15 liefert vollständige OSC-Daten und 15 gültige Instanzen; Johannes bestätigt nach dem Diagnosecheck 15 sichtbare Kreise und danach reagierende Count-Wechsel. Der zunächst beobachtete Stillstand bei sieben Kreisen ist noch nicht abschließend erklärt. Johannes bestätigt auch den direkten Wechsel 3 → 15 → 3 nach erneutem Öffnen ohne Diagnose-/Force-Cook.
- Der isolierte TD-Radius-null-Test besteht: bei 15 gültigen Chairs verschwindet nur Chair 0, die anderen 14 Radien bleiben unverändert und beide Chair-Render reagieren. Callback und Chair 0 sind wiederhergestellt; keine neue Datei gespeichert. Ein Radius-null-Test über echte OSC-Nachrichten ist damit noch nicht bestätigt.
- Modussperren nach Wiederholung mit nachweislich regulären Chairs On durch Johannes bestätigt: Tracking, Study und Calibration liefern jeweils Switch-Index 0, AISI liefert 1. Der erste Durchlauf war wegen Chairs Off nicht aussagekräftig. Vollständige bildliche Modusvergleiche stehen noch aus.
- Johannes bestätigt 8 → 3 sowie die Counts 6, 9, 10, 11 und 15. Count 0 lässt sich in der bestehenden UI nicht eingeben; der vorher pauschal bestätigte Wechsel 1 → 0 wird deshalb nicht als gesicherter Count-null-Nachweis gewertet. Der Übergang 15 → 0 bleibt ungeprüft; die UI wird dafür nicht erweitert.
- Änderungen im Room Editor werden laut Johannes live in TD übernommen. Damit ist die Reaktion über die OSC-Brücke beobachtet; ein einzelner ungültiger Chair über echte OSC-Nachrichten und physische Projektionskorrektheit sind damit nicht bestätigt.
- Neue Stichprobe am 2026-10-07: neun sichtbare Kreise bei Count 9 und ebenfalls neun bei Count 10, zusätzlich auffällige Platzverteilung und links angeschnittene Kreise. Die Python-Ausgabe für dieselbe aktuelle Source enthält korrekt 9/10 Chairs; Version 140 enthält offline 15 korrekt zeilengebundene Chair-Instanzen. Der Livefehler ist damit erneut offen, ohne die bestandene Offline-Geometrieprüfung zu widerlegen. Ein manueller lesender Check ohne Force-Cook liegt in `td_builders/inspect_shared_chair_live_state.py`; Live-Ausgabe steht aus. Geschützte Kamera-/Projektionsparameter wurden nicht angepasst.
- Die anschließende manuelle Live-Ausgabe bestätigt Count 10, zehn positive DAT-Radien und vollständige Übereinstimmung OSC → DAT → Instanzparameter. Die empfangenen Positionen reproduzieren jedoch exakt den alten Python-Code (bis Float32-Rundung); der Sender lief seit 15:53 vor den Korrekturen. Gezielter Neustart um 17:48 mit aktuellem Code, genau ein Sender nachgewiesen, laufend zehn Chairs gemeldet; Study-Control unverändert. Die angeschnittenen Kreise sind durch die alten ROI-verletzenden Positionen erklärbar. Sichtbare Vollständigkeit nach Neustart ist noch von Johannes zu bestätigen; gegebenenfalls tatsächliche Ring-SOP-Geometrie prüfen.
- Nach Neustart bestätigt Johannes weiterhin neun sichtbare Kreise bei Count 10; die linken Kreise liegen jetzt vollständig innerhalb der Ansicht. Der verbleibende Fehler betrifft vermutlich die tatsächliche Ring-Geometrie, noch nicht bewiesen. Gezielter manueller Punkte-/Radius-Abgleich in `td_builders/inspect_shared_chair_ring_geometry.py` vorbereitet; keine Cook- oder Parameterreparatur vorgenommen, Live-Ausgabe offen.
- Ringpunkte-Bericht bestätigt die Ursache: nur Index 9 besitzt trotz Instanzradius 0,13 TD noch Nullradius-Geometrie mit Außenradius 0,001 TD. Manuelle Reparatur `td_builders/repair_shared_chair_radius_dependency.py` vorbereitet: explizite SOP-Radius-Bindung über den vorhandenen Custom-Parameter Valuea, gleicher Ring-Callback mit geänderter Radius-Lesezeile, Template + 15 Instanzen, rücknehmbar. Offline geprüft; Live-Ausführung, wiederholte Count-Wechsel und anschließendes manuelles Speichern noch offen. Kein Force-Cook und keine geschützten Änderungen vorgesehen.
- Johannes hat die Radius-Reparatur in Version 140 manuell ausgeführt: 16 Ringe einschließlich Template gebunden, kein Force-Cook und keine Speicherung. Danach sind bei Count 10 zehn Kreise sichtbar. Wiederholte Übergänge 9 → 10 → 9 → 10 und 3 → 15 → 3 sowie ein neuer manuell gespeicherter Stand bleiben noch zu bestätigen.
- Johannes bestätigt anschließend den Fehler als behoben und zeigt die manuell gespeicherte Version 141. Die Datei enthält nach Offline-Expansion tatsächlich die explizite Radius-Bindung und aktualisierte Callback-Lesezeile für Template + 15 Instanzen. Fehlender-Chair-Fehler abgeschlossen; erneutes Öffnen, echte OSC-Radius-null-Prüfung und aufgeschobene physische Raumprüfung bleiben getrennte Nachweise.

Detailed TD debug-node history belongs in `docs/TOUCHDESIGNER_SYNTH_CHAIR_DEBUG.md`, not here.

Physical-room-reported structure:

- modes include Calibration and Content;
- Content can switch between Tracking and AISI/Study paths;
- floor content, tabletop content, and table masks share downstream calibration/projector stages;
- floor/tabletop/mask ordering is physically consequential;
- Calibration + Floor requires a black table-mask input so the inverted mask becomes white and leaves the floor image unchanged.

Rendering/backend rules:

- the interactive Room Editor uses `tkinter` directly and avoids forcing a Matplotlib backend at import time;
- headless PNG/debug generation selects `Agg` before importing `pyplot`;
- shared plotting modules remain backend-neutral.

### Motion Design v1.5 — isolierte Vorschau technisch geprüft (2026-10-23)

Die neue Motion-Content-Komponente liegt als separater Builder mit eigenen
Floor-/Tabletop-Ausgängen vor, noch ohne Anschluss an bestehende Ausgaben.
Referenz ist das von Johannes gelieferte Remotion-Paket v1.5. Zustandslogik
und Kontaktgeometrie sind offline geprüft. Johannes hat den Aufbau und die
technische Diagnose in TouchDesigner mit Python 3.9.5 bestanden: Zustands-TOP
6 × 6, beide Oberflächenausgänge und Preview 1000 × 1000, alle fehlerfrei.
Johannes bestätigt anschließend die sichtbare Demo im Operator-Viewer als
passend. Kamera-/Live-Anschluss und Laborprüfung stehen noch aus; die
anschließenden Simulations- und Grenzfallnachweise folgen unten. Johannes
vermittelt ausschließlich Textport-Befehle, kein Bildschirmzugriff.
Anschlüsse, abweichende OSC-/Item-Positionsvorzeichen, Nachweise und die
noch offenen Preview-/Live-/Laborprüfungen stehen im
[Motion-Integrationsstand](TOUCHDESIGNER_MOTION_DESIGN.md).

Johannes wählt als nächsten Schritt die Room-Editor-/OSC-Simulation.
Der separate Simulator und ein Anschluss ausschließlich an das neue
Motion-Preview sind vorbereitet, mit stabilen Tisch-IDs, expliziter
Layoutaktivierung und Timeout. Nur das neue OSC-Präfix `/aisi_motion/`
wird an den vorhandenen Empfänger gesendet. 26 Motion-/Transporttests und
acht bestehende Room-Editor-Tests bestehen; Johannes hat den manuellen
Simulationsanschluss ausgeführt und die korrekte Preview-Reaktion bestätigt.
Anschließend hat Johannes alle 19 deterministischen Grenzfall-Prüfungen
im temporären TD-Prüfzweig bestanden, einschließlich echter TOP-Pixel und
unabhängigem zweitem Tischzustand; der Prüfzweig wurde entfernt und nichts
gespeichert. Johannes bestätigt außerdem Übertragungspause/-fortsetzung und
erneute Aktivierung genau wie beschrieben. Drei- und Fünftisch-Szenarien
sind vorbereitet und offline auf Identität, unabhängigen Abschluss sowie
kollisionsfreie Source-/Ziel-Endzustände und deren Mischungen geprüft.
Die anschließende Dreitisch-Simulation zeigte einen Resetfehler der
Kontakt-Historie bei Reaktivierung. Korrigiert entsprechend der separaten
Visual-Historie in Remotion v1.5; 31 fokussierte Offline-Tests bestehen.
Johannes bestätigt alle 22 erweiterten TD-Zustands-/Pixelprüfungen und
korrekt wachsendes Grün bei allen drei Tischen. Auch nach Abschluss und
erneutem Verdrehen bleibt der Kontaktfortschritt erhalten. Temporärer
Prüfzweig entfernt, nichts gespeichert. Anschließend bestätigt Johannes auch
fünf sichtbare Tische, globale Reveal-Welle und unabhängige Abschlüsse im
Fünftisch-Simulator. Der Launcher ersetzt nur den zugeordneten Dreitisch-Sender;
das TD-Projekt wurde nicht gespeichert. Auf diesem Mac stehen laut Johannes
keine echten Trackingdaten zur Verfügung. Als nächster Schritt wird die
bestehende Content-Umschaltung mit Simulation vorbereitet; Kameraanschluss
und physische Raumvalidierung bleiben separate Laborschritte.
Die aktuelle Routing-Abfrage bestätigt `mask_tabletop` als Composite TOP
mit Multiply: Content an Eingang 0, bestehende Maske an Eingang 1. Die
Ausgabe-/Kalibrierungsschalter bleiben dahinter. Ein isolierter
`comp_aisi_motion_routing_preview` ist inzwischen in TD aufgebaut und
geprüft; sieben Offline-Routing-Tests bestehen. Der erste Aufbauversuch
brach vor Änderungen wegen dynamischer `resolutionw`/`resolutionh` der
Chair-Komposition ab. Die Kopie referenziert diese nun ausdrücklich über
absolute Pfade auf die ausgewerteten Originalparameter; andere dynamische
Parameter bleiben gesperrt. Die TD-Wiederholung hat alle sieben Prüfungen
bestanden: deaktiviert pixelgleich zu bisherigen Floor-/Tabletop-Bildern,
Maskenreihenfolge und Auflösungsreferenzen korrekt, aktuelle Moduswahl und
Chair-Auswahl korrekt; lokaler Enable-Wert wiederhergestellt. Er kopiert ausschließlich
Masken-/Chair-Kompositionen in einen neuen Prüfzweig und verändert keine
bestehenden Ausgaben. Die separate Motion-Simulation und die bestehende
Tischmaske beziehen ihre Posen bisher aus unterschiedlichen Datenpfaden;
daraus darf noch kein produktiver oder physisch korrekter Anschluss abgeleitet
werden. Die folgenden statischen Pose-/Pixelnachweise ersetzen keine
tatsächlichen Study-/Tracking-Bildvergleiche oder Raumprüfung.
Der anschließende Geometriebericht bestätigt fünf Rect-Zeilen in
`tables_active` mit numerischen Legacy-Slots und die bekannte orthografische
Kamera (2,6 TD-Einheiten). Entscheidend: Der aktive Maskenrenderer referenziert
`rect_setup_mask_geo_00` bis `05` unter `comp_study_visualization`, jeweils
doppelt; die untersuchte `item1/table_mask_geo` ist keine aktive Quelle dieses
Renderers. Die doppelte Auswahl wird nicht geändert. Ein weiterer Helfer
`build_motion_aligned_snapshot.py` prüft die tatsächlichen Maskentransformationen
gegen die aktive Tischliste und erstellt nur bei übereinstimmenden Posen eine
separate statische Motion-Probe. Er verwendet die vorhandene Umrechnung
`td_pose`, verändert keine alten Knoten und schaltet kein Routing um.
Der erste TD-Versuch brach bei fünf geringfügig abweichenden gespeicherten
Source-Posen ab (maximal 0,046 cm / 0,0171°). Die statische Probe nutzt nun
direkt die exakten Maskenposen; zuvor wird die Slot-Zuordnung rasterbezogen
innerhalb eines Pixels geprüft (0,25 cm bei 2000 Pixeln über 500 cm).
Translation und rotationsbedingter Randversatz werden gemeinsam begrenzt.
Bestehende Posen, Masken und Erfolgstoleranzen werden nicht verändert.
Zehn Offline-Tests bestehen, einschließlich der fünf gemeldeten Posen und
des vollständigen Preflights; die TD-Wiederholung ist bestanden. Der neue
`comp_aisi_motion_aligned_snapshot` wurde mit fünf exakt übernommenen Masken-
Sources, unveränderten Legacy-Targets und 2000 × 2000 Pixeln erstellt.
Keine Probleme gemeldet, bestehende Knoten und Routing unverändert, nichts
gespeichert. Numerische
Slots belegen weder dauerhafte Tracking-IDs noch Aktualität.
Der nächste Helfer `check_motion_aligned_routing.py` prüft eine temporäre
weiße Tischflächenprobe durch die vorhandene Masken-Komposition und misst
Formbeschnitt sowie helles RGB außerhalb der Maske. Nur bei technischer
Erfüllung schaltet er die beiden Select TOPs des isolierten Routing-COMPs
auf den statischen Snapshot und aktiviert dessen lokale Motion-Vorschau.
Produktive Outputs bleiben unverändert; bei Fehlern wird der lokale Zustand
wiederhergestellt. Der erste TD-Versuch brach vor den Prüfungen ab: Beim
Python-Import des Snapshot-Helfers löste dessen bisheriger Textport-Einstieg
erneut den Builder aus; der vorhandene Snapshot verhinderte die Erzeugung.
Import und Textport-Start sind nun über den Python-Importspec getrennt,
auch wenn TD `op` in Builtins bereitstellt. Die nächste übermittelte TD-
Ausgabe bestätigt beide Poseprüfungen; die Pixelprobe scheiterte anschließend
an einem direkten TOP-Kabel vom Routing-COMP in den Snapshot-COMP.
Korrigiert über einen temporären lokalen Select TOP, der die bestehende Maske
per Pfad liest; beide Composite-Eingänge liegen damit im Snapshot-Netzwerk
und werden vor dem Kochen geprüft. Elf fokussierte Offline-Tests und die
abgeleitete GLSL-Kompilation bestehen. Die anschließende TD-Wiederholung
hat alle sieben Prüfungen bestanden: 2000 × 2000 Pixel, 1.010.626 geprüfte
Tisch-Innenpixel vollständig erhalten (`interior_retained_fraction: 1.0`),
kein helles RGB außerhalb der Maske. 2024 Maskenpixel liegen außerhalb der
nominalen Source-Kontur; daraus wird keine Änderung abgeleitet. Die beiden
Snapshot-Ausgänge sind nun ausschließlich im isolierten Routing-COMP aktiv.
Temporäre Proben entfernt, nichts gespeichert und keine produktiven Outputs
geändert. Johannes hat anschließend Screenshots beider Ausgänge übermittelt.
Die optische Prüfung ist für diesen statischen Snapshot plausibel: Floor-
Targets werden von Source-Flächen ausgespart, am Tabletop sind vier grüne
Kontaktanzeigen und ein Navigationskreis ohne Grün sichtbar. Die weißen
Teilflächen entsprechen der Source-/Target-Überlappung; der ausgesparte
Pfeil zeigt den darunterliegenden grünen bzw. schwarzen Untergrund.
Johannes bemängelt anschließend zu Recht die identischen grünen Anfangsformen:
Der statische Snapshot startet bei bereits bestehendem Kontakt, setzt jeweils
`P0 = P` und zeigt damit `A = 0`. Seine fehlende Annäherungsgeschichte kann
Wachstum oder Zentrierung nicht nachweisen. Die vorherige positive Bewertung
gilt nur für statischen Maskendurchlass und Schnittflächen, nicht für grünes
Fortschrittsfeedback. Die Motion-Formel wird deshalb nicht verändert.
Ein dynamischer maskierter Simulationsprüfzweig ist vorbereitet:
`build_motion_dynamic_mask_preview.py` erzeugt einen neuen COMP, liest den
fortlaufenden State-TOP der bereits geprüften Room-Editor-Motion-Komponente
und steuert damit ausschließlich kopierte Maskengeometrien. Die lokale
Kopie des Maskenrenderers verwendet die ursprüngliche Kamera, aufgelöste
Licht-/Materialreferenzen und dieselbe aufgelöste Select-SOP-Fläche. Reorder
und Multiply werden ebenfalls nur kopiert. Originale und produktive
Ausgaben bleiben unverändert. Sechs neue Offline-Tests bestätigen unter
anderem den Unterschied zwischen Snapshot und Annäherungsgeschichte,
unabhängigen Fortschritt und die inverse Poseabbildung. Johannes hat den
TD-Aufbau anschließend ausgeführt und bestätigt ausdrücklich „jetzt ist es
richtig“. Der Screenshot zeigt rechts unten großflächiges, zentriertes Grün
und einen kleinen Navigationskreis, während andere Tische ihren Anfangszustand
behalten. Die Ausgabe bestätigt fünf frische Tisch-IDs, Maskenrenderer,
Reorder, maskiertes Tabletop und Out TOP jeweils 2000 × 2000 sowie Floor
1000 × 1000, alle im Builder fehlerfrei gekocht. Die Maskenfläche ist
`comp_study_visualization/rect_tabletop_inner_geo/table_surface`.
Originalknoten und Produktionsoutputs wurden nicht verändert, nichts durch
das Skript gespeichert. Diese Bestätigung betrifft dynamische maskierte
Simulation; statische Snapshot-Bilder bleiben kein Wachstumsnachweis.
Johannes meldet anschließend einen weiteren Grenzfall: Ohne Überschneidung
mit dem Target verschwindet im dynamisch maskierten Prüfzweig auch der
Navigationskreis. Die frühere Bestätigung betrifft somit Wachstum/Zentrierung,
keine vollständige Freigabe des maskierten Vor-Kontakt-Zustands. Ein gezielter
Offline-GPU-Render mit gültiger aktiver Source ohne Kontakt zeigt den Kreis
im unmaskierten Shader korrekt (2336 Alpha-Pixel über 0,5 im 500²-Testbild).
Der Helfer `inspect_motion_navigation.py` vergleicht für die tatsächliche
Fehlerstellung State/Phase/Aktivierung, unmaskiertes Bild, Maskenbild und
maskiertes Bild sowie kopierte SOP-Grenzen. Er verändert keine Knoten oder
Parameter. Kontrollierte TD-Proben mit/ohne Kontakt bestehen mit praktisch
vollständigem Flächenerhalt durch die Maske. Die folgende Live-Abfrage
zeigt den Kreis auch ohne Kontakt; Johannes bestätigt jedoch, dass er erst
nach dem erzwungenen Diagnose-Cook sichtbar wurde. Die indirekten
Pose-Abfragen per DAT-Modul/`numpyArray()` erhalten deshalb eine explizite
`absTime.frame`-Abhängigkeit. `update_motion_mask_dependencies.py` hat alle
20 Pose-Ausdrücke ausschließlich der kopierten Simulationsmasken aktualisiert,
ohne Engine-Reset, Force-Cook, Original-/Produktionsänderung oder Speicherung.
Johannes bestätigt danach die angefragte Bewegung ohne Diagnosebefehl als
funktionierend. Neun fokussierte Offline-Tests und Python-3.9-Syntaxprüfung
bestanden; dieser virtuelle Grenzfall ist damit abgeschlossen.
Johannes fordert danach eine rundere grüne Form nahe der Zielmitte, damit
beim Überfahren kein Richtungsumschlag sichtbar wird. Der Shader blendet
alle gerichteten Verformungen zwischen 29 und 8 cm weich aus; innerhalb
der bestehenden 8-cm-Positionstoleranz ist die Form zentriert/rund, auch
bei verbleibendem Winkelfehler. Diese gewünschte visuelle Weiterentwicklung
von v1.5 verändert keine Kontakt-/Erfolgsschwelle oder Fortschrittsgeschichte.
Acht GPU-/Installer-Tests bestehen; `update_motion_halo_shape.py` erhält
den laufenden Zustand und andere lokale Shaderänderungen. Johannes hat den
Shader im laufenden TD erfolgreich installiert/kompiliert und bestätigt den
angefragten Mittelpunktdurchgang anschließend mit „ja jetzt stimmt es“.
Kein Engine-Reset, keine Masken-/Produktionsänderung, nichts gespeichert.
Diese visuelle Simulationsabnahme ersetzt keine physische Raumprüfung.
Die abschließende erweiterte TD-Regressionsabnahme besteht anschließend bei
Johannes mit allen 25 Kriterien, einschließlich Halosymmetrie,
Richtungsunabhängigkeit beim Mittelpunktdurchgang und stetigem Formübergang.
Temporäre Prüfkomponente entfernt, nichts gespeichert, physische Validierung
nicht ausgeführt. 77 fokussierte Offline-Tests und vier separat ausgeführte
native GPU-Tests bestanden. Der bestätigte Simulationsstand bleibt vom noch
ausstehenden echten Trackinganschluss getrennt.
Der neue, noch nicht angeschlossene Zustandskern
`aisi.app.motion_live_adapter.MotionLiveAdapter` konsumiert kalibrierte
FrameEvents direkt. Dadurch werden fehlende IDs nicht aus dem 15-Frame-Cache
der bestehenden Szenenbrücke übernommen. Zwei fortschreitende Kamera-Frames,
Zeitstempel und Kalibrierungsidentität sichern den Eingang; gleiche Frames
verlängern das 0,5-s-Zeitlimit nicht. Ziele und Aktivflags werden nur durch
explizite Aktivierung mit neuer Revision eingefroren. Kamera-Neustart oder
Kalibrierungswechsel verlangen Reset und erneute Aktivierung. AISI-Weltachsen
bleiben unverändert; der Abgleich zur tatsächlich gerenderten TD-Maske und
der produktive Anschluss sind ausdrücklich noch nicht durchgeführt.
16 neue Offline-Tests einschließlich synthetischem OSC-Durchlauf sowie zehn
bestehende Vision-Brückentests bestanden. Die rein lesende Modul-CLI prüft
nur neu angehängte Kamera-Frames, sendet nichts und aktiviert kein Layout.
Johannes beauftragt danach die technische produktive Umschaltung bereits
vor dem Laboranschluss. Der aktuelle Graph ist erneut ausgelesen.
`build_motion_output_routing.py` bereitet zwei reversible Content-Einfügepunkte
vor: Floor-Basis-Select vor der vorhandenen Chair-Komposition und Tabletop-
Null vor der unveränderten Originalmaske. Zehn Offline-Modelltests bestehen;
separater Prüfer und Rückbau verfügbar. Beide Freigabeschalter starten aus,
der Builder verlangt drei pixelgleiche Legacy-Ausgabebilder sowie unveränderte
Originalparameter/-verbindungen außerhalb der zwei erlaubten Stellen.
Johannes hat die Einbindung anschließend im laufenden TD installiert:
`installed: true`, drei Pixel-Bypass-Prüfungen und Vergleich des geschützten
Graphen bestanden. Der separate Prüfer besteht mit allen sieben Kriterien,
einschließlich pixelgleichem Floor-/Tabletop-Bypass, Originalauflösungen
und fehlerfreien Floor-/Tabletop-/Masken-Ausgabeschaltern. `Enablemotion`
und `Sourceapproved` bleiben aus. Die produktive Verdrahtung ist damit
vorhanden, weiterhin mit Legacy-Bild. Originalmaske, Chair-Komposition,
Kalibrierung und Projektortransforms unverändert, nichts gespeichert.
Johannes beauftragt anschließend einen Simulationstest durch diese produktive
Kette. Start-/Prüf-/Stop-Skripte ergänzen einen temporären gemeinsamen Schalter
für Content und das passende dynamische Simulationsmaskenbild vor dem
unveränderten Originalmaskenoperator. Ein zusätzlicher Maskenbild-Eingang
wird zeitweilig umgeschaltet; Originalgeometrien, Kalibrierung, Reihenfolge
und Projektorparameter bleiben erhalten. Echte Quellenfreigabe bleibt aus,
Tracking/Study/Kalibrierung wählen Legacy und Originalmaske. Der Stop stellt
den zuvor geprüften deaktivierten Router wieder her. 20 fokussierte
Routing-/Simulationstests zunächst bestanden. Der erste TD-Start meldet
danach fehlende frische Simulationsframes und bricht vor jeder Umschaltung
ab; keine Testsitzung registriert, Legacy-Bild bleibt erhalten. Die reine
Quellen-Diagnose `check_motion_simulation_source.py` grenzt Sender-/Frische-
zustand ein. Start/Stop behandeln diesen Zustand jetzt ohne Traceback;
21 Routing-/Simulationstests und vier Launcher-Tests bestanden. Die direkte
Quellendiagnose bestätigt nach Öffnen des isolierten Previews frische Frames
aller fünf Tisch-IDs, aktive OSC-Eingabe und laufenden eigenen Sender;
kein Neustart erforderlich. Ein erneuter kombinierter Start läuft dennoch
in den Timeout. Die umfangreichen synchronen GPU-Prüfungen vor dem erneuten
State-Cook sind die plausible Ursache einer im selben TD-Frame gecachten
OSC-Quelle. Vorbereitung und Aktivierung sind daher getrennt: erst
deaktivierter GPU-/Bypass-Aufbau, dann in späterem TD-Frame gezielt OSC-In,
Raw-CHOP und State aktualisieren. Aktivierung verlangt eine neue frische
Signatur gegenüber der Vorbereitung und enthält keine GPU-Pixelabfragen.
Timeout bleibt 0,5 s; Pixelprüfung folgt separat und setzt bei Abweichung
den geprüften Test zurück. 25 Routing-/Simulationstests bestanden.
Die zweiphasige Aktivierung ist im laufenden TD bestanden: Vorbereitung mit
drei Bypass-Pixelprüfungen in Frame 1378043, Aktivierung in Frame 1379345
mit frischer Signatur (2548711, 279512) und fünf Tisch-IDs. Floor, Tabletop
und Simulationsmaske stehen gemeinsam auf Index 1; Johannes bestätigt
sichtbaren neuen Content. Die temporäre Testsitzung ist aktiv. Die separate
aktive Ausgabeprüfung hat alle sechs Kriterien bestanden: aktiver Maskeneingang
pixelgleich zur dynamischen Simulationsmaske und Tabletop durch die Originalmaske
pixelgleich zum dynamischen Prüfzweig (maximaler Pixelfehler 0,0). Kalibrierung,
Chair-Komposition und Projektorparameter laut Strukturprüfung unverändert.
Bewegung durch die produktive Kette ist noch manuell zu bestätigen.
Die reale Quelle bleibt nicht freigegeben. Keine automatische Speicherung und
keine physische Validierung.
Aktive reale Quelle, tatsächliche Modus-Bildvergleiche
und Raumabnahme bleiben offen. Der lokale
TD-Stand ist weiterhin ungespeichert; eine neue benannte Arbeitskopie manuell
sichern. Nächster unabhängiger Block ist die Anbindung echter Trackingdaten
im Labor, mit stabilen IDs,
Paketaktualität und explizitem Layout-Ereignis.
Die normale Szene wird nicht überschrieben.

### Layout-Anschluss der Motion-Simulation — 2026-10-23

Johannes präzisiert die Labor-Abschaltung: Ziele sollen während Bewegung
nicht nachberechnet werden; beim Aktivieren ist quelladaptive Berechnung aus
den Istposen erlaubt (D005a). `motion_layout_proposal.py` verwendet die
bestehenden Generatoren in Scene Order und übernimmt Tischziele und Chairs
zusammen. Berechnung läuft im Worker; OSC sendet währenddessen weiter den
bisherigen Vorschlag. Commit erfolgt im Editor-Thread, nur bei unveränderter
Tischmenge. Keine automatische Neuberechnung durch Bewegung oder UI-Änderung.

`motion_preview_sim --generated-layouts` liest beim Klick die vorhandene
Learning-Format-State-Datei; Opt-in, Format, Teilnehmende, Gruppen,
Präsentationsseite, Chairs und Umbauintensität werden erhalten. Ohne
Teilnehmenden-Opt-in bleibt die Ausgabe ohne synthetische Chairs. Start ohne
aktivierten Vorschlag ist leer. Fehler ändern weder Ziele noch Revision.
Alle neuen Nachrichten bleiben unter `/aisi_motion/`; alte `/table`, `/chair`
und `/study` werden nicht beschrieben. Chair-Daten gehören zu derselben
Session, Frame und Revision wie die Tische; veraltete/unvollständige Pakete
werden ausgeblendet.

Eine eigene Chair-Komponente zeichnet die weißen Marker mit 2,5 cm Stärke
und erhält ihre Außenradien. Sie wird im registrierten Simulationstest über
einen zusätzlichen reversiblen Eingang vor die bestehende Chair-Komposition
geschaltet. Umschaltung folgt demselben AISI-/Kalibrierungsgatter wie Content
und Simulationsmaske. Study-/Tracking-/Kalibrierungsmodus verwendet die alte
Chair-Quelle; Rückbau stellt den ursprünglichen Composite-Eingang wieder her.
Kalibrierung, Originalmasken, Projektoren und die bestehenden Generatorregeln
werden nicht geändert. Der bestehende Chair-Ein-/Ausschalter bleibt erhalten.

Vorbereitung: `td_builders/prepare_motion_layout_simulation.py` beendet den
registrierten Ausgabetest, baut/reverwendet die geprüfte eigene Chair-Komponente,
ersetzt ausschließlich den eindeutig zugeordneten Simulator durch den
Fünf-Tisch-Modus mit generierten Layouts und bereitet den deaktivierten
Ausgabetest vor. Aktivierung in späterem TD-Frame, anschließend Vorschlag im
Room Editor aktivieren und separat `output_test.verify(op)` ausführen.
Offline mit echten Generatoren alle drei Formate bei fünf Tischen/acht
Teilnehmenden/100 % und die aktuellen lokalen Discussion-Einstellungen
(13 Teilnehmende/88 %) berechnet. Insgesamt 62 fokussierte Prüfungen bestanden,
einschließlich drei nativer Zwei-Textur-GPU-Prüfungen.
Installation/Pixelprüfung und Format-/Bewegungsabnahme dieses neuen
Anschlusses im laufenden TD sowie physische Raumvalidierung stehen noch aus.

## 6. Canonical geometry

Repository-confirmed table types:

| Type | Physical reference | Shape |
| --- | --- | --- |
| `summit` | approximately `157 × 70 × 74 cm` | trapezoidal |
| `sprint` | approximately `82 × 60 × 74 cm` | trapezoidal |
| `rect` | `160 × 80 × 74 cm` | rectangular |

The polygon-aware geometry migration is complete. Canonical footprints/supports are used for collision, ROI, clearance, repair, and debug rendering.

Important implementation invariants:

- format roles remain bound to `table_id`;
- target output returns to original scene order;
- `strength = 0` yields exact source poses without repair;
- `strength > 0` blends before one final hard-constraint repair;
- overall layout-generation capacity is five tables.

For binding design rules, seating/clearance semantics, and format-specific constraints, see the relevant entries in `docs/DECISIONS.md`.

## 7. Current Rect layout-generation state

### Input

The fixed Rect Input slots have been replaced by a source-adaptive presentation-plus-audience formation.

Current state:

- Automatische Präsentationsachse seit 2026-10-08: gemeinsame axiale Source-Orientierung bevorzugt, Positionen bestimmen Präsentationsende und Rollen. Ohne eindeutige Orientierungsresultierende gilt die räumliche Hauptausdehnung; eine explizite Präsentationsseite bleibt verbindlich (D007).
- presentation role is inferred spatially rather than from `table_id`;
- active Rect tables use one semantic long-side seating/movement surface;
- Die gemeinsame Rect-Input-Synthese berücksichtigt diese Orientierungspräferenz im normalen und im Vorschaupfad; teilnehmendenbasierte Teilmenge, Parken und Chairs bleiben opt-in.
- virtual Room Editor / Learning-Format / OSC / TouchDesigner checks have been accepted;
- physical room validation remains open.

### Participant-based Input preview

Johannes bestätigt am 2026-10-15 Input für den Moment als passend. Qualitative
Rückmeldung zur aktuellen Anzeige; keine zusätzliche vollständige Count-/Seiten-
oder physische Raumprüfung. Gemeinsamer Formatwechsel-Check bleibt offen.

Der explizit aktivierte Simulationspfad plant aktive und geparkte Rect-Tische
nach Teilnehmendenzahl und leitet Chair-Marker aus ihren gerichteten Sitzflächen ab.

- Zielverhältnis: zwei Teilnehmende pro aktivem Tisch; erst mit allen verfügbaren Tischen bis zu drei pro Tisch, damit `1–15` bei fünf Rect-Tischen.
- Überkapazität scheitert ausdrücklich mit `LayoutConstraintError` vor Ausgabe; kein stilles Ersatzlayout.
- Parktische bleiben sichtbar, Ziele folgen der Source Scene Order; interne Auswahl und Chair-Reihenfolge sind ID-stabil.
- Chair-Kreise haben `25 cm` Radius und liegen vollständig in den kanonischen gerichteten `70 cm` Sitzflächen. Ihre Richtung folgt der Zielnormalen auch nach Raumachsen-Ausweichlösung.
- Die optionale Präsentationsseite wird in der bestehenden Rect-Synthese berücksichtigt; ohne Vorgabe bleibt die Source maßgeblich.
- Transformationsstärke 0 erhält auch geparkte Tischposen exakt, ohne Reparatur. Die vollständige gemeinsame Sitzflächenprüfung gilt für 100 %.
- Offline am 2026-10-07: 300/300 Fälle bestanden (vier Quellen × fünf Ausrichtungen × Counts 1–15), 300 deterministische Wiederholungen, 140 Scene-Order-Prüfungen, 60 Überkapazitätsablehnungen und 59 fokussierte Tests. Nachweise und Grenzen: [Prüfbericht](INPUT_GEOMETRY_VALIDATION.md).
- Zentrale TD-Struktur mit 15 Slots, OSC-Live-Reaktion und Modussperren sind laut Handoff geprüft. Count 0 ist ausgenommen; echte OSC-Radius-null-Prüfung und physische Raumvalidierung bleiben offen.
- Ohne Vorschau bleiben normale Chair-Daten und andere Formate unverändert.

Bei späteren Live-Prüfungen darf genau eine `sim_scene_to_osc`-Instanz auf
Port `9000` senden. Diese Validierung hat keinen Sender gestartet.

### Groupwork

Neue Spezifikation vom 2026-10-08, als Offline-Prototyp umgesetzt: `participants`
und `number_of_groups` bestimmen möglichst gleich große Teilnehmergruppen.
Eine Teilnehmergruppe darf mehrere räumlich zugehörige Tischcluster nutzen.
Die bisherigen Insel-`groups` des Geometriegenerators sind keine vollständige
Teilnehmergruppenzuordnung. Reguläre Stirnseitenplätze erhalten Vorrang vor
verdichteten Längsseitenplätzen; zusätzliche kanonische Stirnseitenstreifen
werden im neuen Offline-Modell bei Belegung geprüft. 65 fokussierte Tests und
zehn Integrationsfälle bestanden. Johannes aktualisiert die Tischwahl nach
der Live-Stichprobe: drei Personen optimal am Einzel-Tisch, darüber bevorzugt
ein Pair, sofern passend. Standard `group_capacity` ersetzt `few_tables`;
nutzbare Stirnseiten bleiben vor verdichteten Längsseiten bevorzugt. Die opt-in
Vorschau/OSC-Anbindung ist im Code ergänzt; Stärke 0 ohne Chairs/Reparatur,
positive Teilstärken mit Blend-before-repair und gebundenen Rollen. Über 15
Chairs werden im Adapter als technische Ausgabegrenze abgelehnt.
Getrennte Cluster werden zusätzlich auf überlappende 170 × 90 cm
Bodenkonturen geprüft und anschließend ohne Rollenwechsel räumlich entzerrt.
Die physische Geometrie und Pair-Seam bleiben unverändert.
Die Clusterwahl minimiert weiterhin den Gesamtweg. Die abschließende starre
Entzerrung nutzt freie Fläche für ein weiches 60-cm-Ziel zwischen Bodenkonturen
verschiedener Teilnehmergruppen (bestehende Sitzflächentiefe); zusätzliche Wege
sind bis dahin zulässig, danach wieder nachrangig. Das Ziel ist keine harte
Ablehnungsbedingung. In der aktuellen `15/4`-Quelle steigt der kleinste
Gruppenabstand von 0,5 auf 60,4 cm bei rund 2,4 s Offline-Laufzeit.
Pair-Seam, Sitzflächen, ROI und Parkregeln bleiben erhalten;
Singletons erhalten zusätzliche Source-abgeleitete Winkelkandidaten.
Der Vier-/Fünf-Singleton-Reparaturpfad nutzt inzwischen begrenzte Winkelannäherung
statt eines direkten gemeinsamen orthogonalen Fallbacks und prüft abgerundete
kanonische Flächen. Geparkte Groupwork-Tische stehen bei 100 % mit ihrer physischen
Längsseite am ROI-Rand und bleiben von der anschließenden Entzerrung ausgenommen.
Zusätzlich halten Parktische mindestens 60 cm physischen Kantenabstand zu aktiven
Tischen. Bei gleicher fachlicher Topologie-/Belegungspriorität minimiert die Zielauswahl
den Gesamtweg aller Tische; aktive Wege dienen danach als Gleichstandsentscheidung.
Groupwork-Parken darf mehrere ROI-Ränder nutzen, wenn dies den Parkweg verkürzt.
Bei fehlendem Parkplatz erhält ein zusammenhängendes Pair mit drei Singletons
Vorrang vor fünf getrennten aktiven Tischclustern für nur vier Gruppen.
Die Topologie `2 + 1 + 1 + 1` erhält dafür eine begrenzte Winkelannäherung als
Fallback; Rollen, ursprüngliche Source-Winkel und Scene Order bleiben erhalten.
Eine neue lokal festgefahrene `15/5`-Source wird nach erfolgloser normaler Suche
mit zusätzlichen Source-abgeleiteten Mittelpunkt-/radialen Startpositionen repariert.
Alle kanonischen Geometriebedingungen bleiben unverändert; kein Parkabstandsproblem.
Bei gleicher Tischzahl/Topologie wird das Pair bevorzugt stärker belegt;
`10/4` soll eine Dreiergruppe am Pair und `3 + 2 + 2` an Singletons erhalten,
sofern die vollständige Geometrie passt.
Rollen bleiben nach der Clusterbildung gebunden; keine globale Zielpermutation.
Johannes bestätigt die aktuelle `10/4`-Vorschau visuell als passend.
Der gemeinsame Offline-Abschlusscheck besteht 130/130 Anfragen (Counts 1–15,
zulässige Gruppen 1–5, Editor-/Live-Quelle), einschließlich gemeinsamer Geometrie,
Identität, Scene Order und Determinismus. Kapazitätsbeispiele und technische
15-Slotgrenze sind separat geprüft. Eine Editor-Sackgasse bei `13/4`–`15/4` wird
nach Reparaturfehlschlag durch erneute Kandidatensuche mit voller Konturprüfung
gelöst; zuvor gültige Pfade bleiben unverändert. 52 fokussierte Tests bestanden.
[Abschlussbericht](GROUPWORK_ABSCHLUSSCHECK.md); Live-Stichprobe der neuen
Konturreparatur, vollständige interaktive Einzelvalidierung und gemessene
Live-Laufzeit bleiben offen. Die Offline-Suche ist inzwischen durch frühe
kanonische Konfliktprüfung, unveränderte Bestwert-Auswahl und auf einen Aufruf
begrenzte Chair-Prüfcaches beschleunigt; Vergleichspläne bleiben exakt gleich.
Die zweite Stufe ergänzt sichere Weggrenzen in der Entzerrung sowie kanonische
Hüllrechteck-Vorprüfung und begrenzte, vollständig koordinatenabhängige
Geometriecaches.
Die dritte Stufe zieht im Teilnehmerpfad Sitzflächenkonflikte vor und bricht
unmögliche Teilkombinationen vor weiteren Anhängen ab. Konkreter `10/4`-Fallback
31,9 → 5,9 s offline, vollständiger Plan unverändert; 46 Tests bestanden.
Siehe [Laufzeit-Handoff](GROUPWORK_PERFORMANCE.md). Details: D008b und
[Groupwork-Handoff](GROUPWORK_PARTICIPANTS.md).

Source-adaptive Rect Groupwork for counts `2–5` is productively implemented.

Current state:

- all Pair/Singleton partitions are derived from source geometry;
- fixed slots, ID-based pairing, and orthogonal target-angle grids are obsolete;
- Pair seam is `8 cm`;
- Singleton and Pair clearance geometry follows the accepted rules in `D008`;
- source orientation strongly influences Pair target orientation;
- focused repository and OSC/simulation checks have passed;
- interactive Room Editor, TouchDesigner, and physical room validation remain open.

### Discussion

Stand der teilnehmerabhängigen Opt-in-Chair-Vorschau: 2026-10-15.

- 1–4 Personen: zwei parallele Rect-Tische mit 10 cm Spalt zwischen den Längskanten, bis zu zwei gegenüberliegende Plätze je äußerer Längsseite. 5–6: zusätzliche gemeinsame Stirnplätze, bei fünf nur ein Ende.
- 7–12: nach innen gerichtetes Vier-Tisch-Rechteck, maximal zwei Chairs je äußerer Längsseite. Für 9–12 zusätzliche äußere Eckplätze zwischen Nachbartischen, bei zwölf acht Längs- plus vier Eckplätze. 13–15: Fünf-Tisch-Pentagon mit zehn Längsplätzen und drei bis fünf Zwischenplätzen; höchstens zwei direkt je Längsseite.
- Zweiergruppe am 2026-10-15 auf Johannes’ Wunsch auf 10 cm physischen Spalt umgestellt (90 cm Mittelpunktabstand). Ursprüngliche 170 × 90 cm Floor-Konturen sollen vollständig bleiben; ihre Außenkanten treffen sich im Spalt. Gemeinsame Stirnflächen überspannen nun 170 cm statt 160 cm. 31 fokussierte Tests und 30 Offline-Fälle bestanden. Rücknahme der angewandten Kontur-Reparatur und erneute Generierung mit aktualisiertem Sender manuell erforderlich. [Anleitung](TOUCHDESIGNER_JOINED_FLOOR_CONTOURS.md).
- Eckflächen aus kanonischen Kontur-Stützpunkten und bestehenden 50-cm-Streifen abgeleitet, vollständig für ROI und Parkplanung reserviert. Maximal ein Chair je Ecke/Zwischenraum, bei zehn zunächst gegenüberliegende Eckplätze. Im Pentagon entstehen die Zwischenflächen an den Mittelpunkten der einander zugewandten kanonischen Stirnkanten. Zwischen-Chairs und ihre vollständigen Sitzflächen werden nach außen auf den Kreis der zehn Längsseiten-Chairs verschoben (nominal rund 26,5 cm; gemeinsamer Mittelpunktabstand rund 225,5 cm). Die bestehende Phasen-/Mittelpunktsuche wahrt die ROI; in der aktuellen Live-Ausgangsszene maximal 3,2 cm Tischverschiebung und 1° gemeinsame Drehung gegenüber dem vorherigen Ziel.
- Tischidentitäten und Posen bleiben innerhalb jeder Teilnehmerstufe stabil; nur die Chair-Belegung ändert sich. Die jeweilige Maximalbelegung 6/12/15 wird vorgeplant und begrenzt zwischengespeichert.
- Überzählige Tische werden mit einer Längsseite am ROI-Rand geparkt, mindestens 60 cm von aktiven Tischen entfernt; alle Tischidentitäten und die ursprüngliche Scene Order bleiben erhalten. Die Auswahl berücksichtigt den Gesamtbewegungsweg.
- Chair-Radius 25 cm; kanonische Sitzflächen 50 cm tief. Eigene Kantentangenz und höchstens 0,51 cm Rundungsüberstand sind zugelassen. Vollständige ROI- und Fremdkollisionsprüfung einschließlich Parktischen.
- Ohne expliziten Count bleibt `2 × verfügbare Tischanzahl` der Standardwert; die aktive Topologie folgt anschließend der Teilnehmerstufe. Bei zu wenigen Tischen oder mehr als 15 Personen klare Ablehnung.
- Bisherige Ring-/Geometriefunktionen und kompakte Parkplanung werden wiederverwendet. Begrenzte Ergebnis-Caches und Wiederverwendung identischer Parkgeometrie innerhalb einer Suche; kein Netzwerkversand in Offline-Checks.
- Umbauintensität am 2026-10-15 nach Johannes’ Freigabe: Stärke 0 erhält exakte Source ohne Chairs; positive Teilstärken dürfen von der festen Discussion-Zielform abweichen. Einzelne Tische folgen der Interpolation; kanonische Chair-/Sitzgeometrie wird pro gebundenem Tisch transportiert. Begrenzte Reparatur einzelner Posen statt starrer Gesamtform. Maximale Stufenbelegung, beide Ring-Bewegungsstreifen, volle ROI, Tisch-/Chair-Kollisionsfreiheit, freie Sitzflächen und Randparken mit 60 cm bleiben geprüft. 100 % unverändert, Rollen/Scene Order erhalten. Cache weiterhin 32 unabhängige Ergebniskopien. 26 fokussierte Tests und 210 Offline-Fälle aus zwei Szenen, Counts 1–15 bei 0/1/25/50/75/99/100 % bestanden; zusätzlich relative Tischabstände statt bloßer gemeinsamer Drehung geprüft. Quellen, Checks und Vergleich lokal unter `data/aisi/debug/discussion_relaxed_strength_2026-10-15/`; reproduzierbar mit `scripts/validate_discussion_strength.py`. Live-Reglerprüfung nach Sender-Neustart offen.
- Offline: 30 Fälle aus zwei Ausgangsszenen, alle Counts 1–15; Übergänge, Parkabstände, Identität/Scene Order, Determinismus und lokale OSC-Ausgabe geprüft. Kontrollplots und eingefrorene Quellen lokal unter `data/aisi/debug/discussion_pentagon_chair_circle_2026-10-15/`.
- Aktualisierung des gemeinsamen Pentagon-Chair-Kreises: 22 fokussierte Discussion-/Rect-Template-Tests bestanden; Input und Groupwork unverändert. Interaktive Chair-Einzelvalidierung und physische Prüfung bleiben offen.
- Der bisherige Tischring ohne Opt-in-Vorschau bleibt unverändert; seine frühere virtuelle Bestätigung gilt nicht automatisch für die neuen Chair-Stufen.

## 8. Study state

### Active trials

Repository-confirmed:

- `trials.json`: `pilot_v8`, `frozen_for_study`;
- zugehöriger eingefrorener Snapshot: `trials_pilot_v8.json`; `pilot_v7` bleibt erhalten;
- T1–T3 und Familiarization einschließlich Teilnehmerstarts unverändert aus `pilot_v7`;
- T4A/T4B: Source, Target und beide Statiktische um exakt `+11 cm` in Welt-Y verschoben, bei unverändertem X und unveränderter Rotation;
- Anlass: natürlicherer Referenzweg mit vorangehendem kurzen Tischende ohne künstliches anfängliches Zurücksetzen; physische Raumvalidierung bleibt offen;
- eight experimental trials: T1–T4 × A/B;
- T1/T2 use one active table and no distractors;
- T3/T4 use one active table and two static distractors;
- exact coordinates, A/B transforms, participant positions, ROI safety, and snapshot metadata are covered by tests.

Task logic:

| | low/limited occlusion | increased occlusion |
| --- | --- | --- |
| simpler layout | T1 | T2 |
| denser layout | T3 | T4 |

This is a deliberate 2×2 task-creation logic; physical factors may not be perfectly orthogonal, so factorial claims require methodological justification.

### Conditions and mappings

- modes: Tracking `0`, Study `1`, AISI `2`;
- conditions: Floor-only `0`, Dual-surface `1`;
- phases: Home `0`, Ready `1`, Active `2`, Complete `3`.

Dual-surface may spatially redistribute guidance rather than merely add tabletop graphics to otherwise identical floor guidance.

### Arrival and logging

- translation tolerance: `8 cm`;
- rotation tolerance: `5°`;
- confirmation duration: `0.5 s` continuously inside tolerance;
- objective arrival and participant-declared completion are distinct;
- arrival entered/confirmed/exited events are logged;
- tracking loss and post-arrival behavior are represented in analysis metrics;
- session metadata includes the active trial-definition SHA-256;
- logs are append-only and participant/session/attempt aware.

## 9. Documentation risks

Known drift outside these handoff files:

- the root `README.md` still describes older prototype status and layout/vision assumptions;
- `docs/PROJECT_STATE_2026-05.md` is historical;
- some human-readable notes in `trials.json` may not literally match the numeric poses and should be reviewed before the next pilot.

Do not change frozen trial geometry merely to resolve prose drift; determine first whether only the notes are wrong.

## 10. Validation principle

Keep repository-confirmed, history-reported, and physical-room-reported claims separate. A local test or virtual TouchDesigner check does not establish physical projection correctness.

### Floor-Renderer in Chair-Arbeitsdatei 137

Die gespeicherte Version 137 wurde am 2026-10-07 in einer temporären Kopie
mit `toeexpand` untersucht. `comp_layout_proposal/render_floor` (Render TOP)
hat eine aktive Geometry-Expression: Im Tracking-Modus werden Tracking-
Floor-Geometrien gewählt, ansonsten phasenabhängige Study-Geometrien.
Der als konstanter Parameterwert gespeicherte ältere Pfad zu
`item*/table_target_floor_geo` ist bei dieser Expression nicht maßgeblich.
Study-Geometrien sind zusätzlich nach Modus/Phase auf Sichtbarkeit begrenzt.
Ein leerer ursprünglicher Floor im AISI-Modus ist deshalb erklärbar und
belegt keinen Fehler der Chair-Integration: Chairs werden erst im zentralen
Composite hinzugefügt. Eine dauerhaft leere Darstellung auch im passenden
Tracking-/Study-Zustand wäre separat im laufenden Projekt zu untersuchen.
Johannes nimmt Count 0 aus dem aktuellen Prüfumfang; die physische
Raumprüfung ist derzeit nicht möglich und bleibt aufgeschoben.

### AISI-Floor und Study-Gestaltung — Live-Zwischenstand

Auf Basis von `AISI_v2.138_coherent_chairs_validated.toe` hat Johannes
`apply_aisi_study_visual_style.py` ausgeführt und die Darstellung bestätigt.
AISI rendert nun vorhandene Zieltischkonturen und Bodenpfeile in
`render_floor` (Render TOP); Tracking/Study behalten ihre bisherigen Zweige.
Rect-Ziele verwenden die weißen gestrichelten Study-Konturen (Floor
170 × 90 cm, Tabletop 150 × 70 cm, Strichstärke 2,5 cm), Rect-Source
die blaue durchgehende Tabletop-Kontur. Zentraler gemeinsamer Style-Code
liegt in `comp_layout_proposal/aisi_table_visual_style` (Text DAT);
vorhandene Item-Geometrien und Template werden weiterverwendet.
Chairs und Scout-Fallback bleiben unverändert.

Der Livebericht meldet `passed: true`: geschützte Einstellungen unverändert,
Chair- und Table-Mask-Bilder bitgleich, sichtbare Floor-Pixel, fünf Rect-Items
mit je vier Source- und zwölf Zielprimitiven je Oberfläche. Der Stand
ist laut Johannes manuell gespeichert. Die Dateien
`AISI_v2.139_aisi_floor_study_style.toe` und
`AISI_v2.140_coherent_chairs_validated.toe` sind am 2026-10-07 im
Projektordner verifiziert; Version 140 stimmt per SHA-256 mit der
unnumerierten Datei `AISI_v2_coherent_chairs_validated.toe` überein.
Kein TD-Zugriff, automatisches Speichern oder erneutes Öffnen während der
Offline-Validierung. Die physische Raumprüfung bleibt aufgeschoben.

Johannes bestätigt am 2026-10-19 eine neue manuell gespeicherte TD-Version
mit anschließendem erneutem Öffnen: alle jüngsten Live-Korrekturen funktionieren
weiterhin. Versionsnummer/Dateipfad noch nicht erfasst; Version 146 ist deshalb
nicht als diese neue Sicherung auszugeben. Nächster gebündelter Prüfblock:
Verdeckung, Wiedererkennung und enge Tischbegegnung. Vor Beginn Discussion 8,
vier erkannte Tische, Status ready, Sender-Fehlerlog leer. Raumprüfung dieses
Robustheitsblocks noch offen; keine Trackingparameter geändert.

Gebündelte Tracking-Robustheitsprüfung am 2026-10-19 durch Johannes im Raum
bestanden: Nach Verdeckung, enger Begegnung und Abgang/Rückkehr folgen alle
Source-Konturen wieder korrekt. Keine vertauschten oder eingefrorenen Konturen,
ruhiges Bild. Qualitative Stichprobe; Erhalt derselben Track-ID über längere
Abwesenheit nicht nachgewiesen. Anschließender Laufzeitcheck: Discussion 8,
vier Tische, ready, Sender-Fehlerlog leer. Trackingparameter unverändert.
Nächster offener Block: physische Projektion/Masken an ROI-Rändern und in
der Projektorüberlappung; Kalibrierung bleibt geschützt.

Projektions-/Maskenblock am 2026-10-19 durch Johannes im Raum bestanden:
Auch in der Projektorüberlappung und an ROI-Rändern saubere Konturen und
Helligkeit, keine Bodenpfeile auf Tischflächen, ruhiges Bild. Qualitative
Stichprobe; Kalibrierung, Homographien und Edge-Blend nicht verändert.
Laufender TD-Prozess öffnet laut CommandLine die manuell gesicherte Datei
`C:\Users\johan\OneDrive\Dokumente\AISI_DEV\touchdesigner\AISI_v2.149_lab_layout_validated.toe`.
Damit ist der zuvor unbekannte Versionspfad erfasst. Nächster Block:
vollständiger Anwendungs-Wiederanlauf einschließlich TD und Bedienoberflächen,
kein Windows-Neustart. Vorhandene Startargumente bleiben maßgeblich.

Vollständiger Anwendungs-Wiederanlauf am 2026-10-19 technisch durchgeführt:
TD und Study-Control durch Johannes geschlossen. Vision-Fenster-Schließen
beendet die cv2.imshow-Schleife nicht; Q/Esc beendet regulär. Kein nachgewiesener
Supervisor-Neustart. Verbliebene fünf AISI-Prozessketten gezielt beendet,
Nullbestand einschließlich TD geprüft, danach alle fünf mit gesicherten
Argumenten neu gestartet. Startbefehle: full_restart.before.json; neue Logs:
full.<Modul>.stdout/stderr.log im bestehenden Lab-Debugordner.
Discussion 8 automatisch wieder ready mit vier Tischen/acht Chairs, alle fünf
Fehlerlogs leer. TD-Version 149 interaktiv geöffnet und Learning-Format-Seite
im Codex-Browser angefordert. Play, sichtbare Study-Control und physischer
Wiederanlauf-/Format-/Modustest noch durch Johannes zu bestätigen.

## Abschluss der Lab-Inbetriebnahme — 2026-10-19

Johannes bestätigt den vollständigen Anwendungs-Wiederanlauf einschließlich
TouchDesigner und Bedienoberflächen im Raum: Sources folgen, alle Formatwechsel
und Tracking → AISI funktionieren sauber, keine alten Elemente, ruhiges Bild.
Der Inbetriebnahmeblock ist damit auf ausdrücklichen Auftrag abgeschlossen.
Gesicherter TD-Prüfstand: `AISI_v2.149_lab_layout_validated.toe` im bekannten
physischen TouchDesigner-Verzeichnis. Kein erneuter Helferaufruf erforderlich.
Abschlusscheck: Discussion 8, vier erkannte Tische, Status ready; alle fünf
`full.*.stderr.log` leer. Dokumentationsdiff geprüft; keine neue Codeänderung.

Abgedeckt sind die dokumentierten Rect-Stichproben mit zwei bis fünf Tischen,
Input/Discussion/Groupwork, Chairs/Moduswechsel, dynamischer Tischanzahl,
veraltetem Zielvorschlag mit aktuellen Sources, Verdeckung/enger Begegnung,
ROI-Rändern/Projektorüberlappung und Wiederanlauf. Keine Vollmatrix oder
Identitätserhaltung über beliebig lange Abwesenheit behauptet. Kalibrierung,
Homographien, Edge-Blend und Layout-Regeln im Inbetriebnahmeblock unverändert.
Separat offen bleibt die vollständige Study-/Pilot-Validierung; ein Windows-
Neustart ist nicht Bestandteil des bestätigten Anwendungs-Wiederanlaufs.

Johannes erklärt am 2026-10-19 die separate Study-/Pilot-Validierung für
nicht mehr erforderlich. Sie ist damit kein offener Folgeauftrag der
abgeschlossenen Inbetriebnahme; daraus wird keine zusätzliche physische
Study-Testbestätigung abgeleitet. Study-Code und Trialdefinitionen unverändert.

## Git-Übergabe — 2026-10-21

Die abgeschlossene Lab-Inbetriebnahme wird mit Integrationscode, TD-Helfern,
106 erneut bestandenen fokussierten Tests und Projektdokumentation gesichert.
Laufzeitdaten, Debug-Ausgaben und Kalibrierungsdateien bleiben ausgeschlossen;
auch die lokale TD-Datei Version 149 wird nicht über Git übertragen.
Die zuvor vorhandenen Vision-Änderungen und die simulierte Live-Szene bleiben
unverändert außerhalb dieses Commits.

Der lokale Branch enthält vier ältere, noch nicht gepushte Commits, darunter
Study-Auswertungen und Debug-Plots. Deshalb erfolgt die datenfreie Übergabe
auf `codex/lab-inbetriebnahme-20261021`, direkt auf Basis von
`origin/vision/wip-dark-proposals`, ohne diese älteren Daten-Commits.
Der ursprüngliche lokale Branch und seine Historie bleiben erhalten.

## Neustartbefund am 2026-10-21: falscher Sender-Startpfad

Nach manuellem Pipeline-Neustart meldet Johannes nur einen Tisch und fehlenden
Layoutstatus. Prozessargumente belegen den Start über
`scripts/run_current_room_tracking_only.ps1`: `--tracking-only` und
`--tracking-table-id table_00`. Vision und Adapter liefern gleichzeitig fünf
aktuelle Tische. Der Tracking-only-Sender veröffentlicht absichtlich keinen
Layoutstatus; MODE AISI in Study-Control ändert diese Prozessoptionen nicht.

Nur die Senderkette wurde durch den oben dokumentierten Layout-Sender ersetzt,
mit beiden Study-Bindings, `--require-fresh-live-scene` und `--interval 0.05`.
Vision/Adapter/TD und fachliche UI-Eingaben unverändert. Anschließend HTTP-Status
`ready`, Input 8, fünf Tische und acht gesendete Chairs; Senderfehlerlog leer.
Sicherung/Protokolle lokal unter `data/aisi/debug/restart_sender_20261021/`.
Physische Sichtbestätigung nach diesem Austausch noch offen.

Für künftigen AISI-Layoutbetrieb den Vision→Scene→OSC-Layoutpfad verwenden,
nicht `run_current_room_tracking_only.ps1`. Der vorhandene
`scripts/run_current_room_vision_to_osc.ps1` ist der Layout-Launcher; er startet
weder Study-Control noch Learning-Format-Server. Vollständige validierte
Senderargumente stehen im Abschnitt „Geprüfter Startpfad“. Bestehende Pipeline
vor erneutem Launcheraufruf beenden, damit kein zweiter Sender entsteht.

## Tischbezogene Tabletop-Zielkonturen — Umsetzung vorbereitet, 2026-10-21

Auf Johannes' Auftrag neuer rücknehmbarer Textport-Helfer:
`td_builders/isolate_aisi_tabletop_targets.py`. Untersuchung einer temporären
Expansion der unveränderten TD-Version 149 bestätigt gemeinsame Tabletop-
Zielausgabe, gemeinsame physische Maske und passende lokale Tischflächen in
Template/vier gespeicherten Instanzen. Der laufende Count kann davon abweichen;
der Helfer adressiert fünf native Item-Pfade und funktioniert ohne Neubau bei
Count-Wechseln. Fehlende Instanzen/Source-Verfügbarkeit sperren ihren Zielanteil.

Neuer isolierter COMP `aisi_own_tabletop_targets`: fünf Target-Render TOPs,
jeweils bestehende Tabletop-Kamera, Source-Flächengeometrie desselben Items,
Masken-Render TOP und kopierte bisherige Reorder-/Maskenoperation. Erst nach
Einzelbeschneidung addieren. Sources/Tabletop-Pfeile bleiben im separaten
bisherigen gemeinsamen Maskenzweig erhalten. Nur Eingang von
`null_tabletop_masked` (Null TOP) auf neuen Modus-Switch umstecken; bei
Tracking/Study unverändert den ursprünglichen `mask_tabletop` (Composite TOP)
verwenden. Originalrenderer und physische Maskenkette bleiben unangetastet.

Vorbedingungen prüfen Verschaltung/Kamera/Geometrien. Vor Anschluss fertig
aufbauen; bei Fehlern ursprünglichen Eingang wieder verbinden und nur eigenen
neuen COMP entfernen. Parameter-/Verbindungsfingerprint für Kalibrierung,
Projektorausgabe, originale Floor-/Tabletop-Renderer und Masken vor/nachher.
Kein Force-Cook, keine Speicherung. Rücknahme:
`restore_aisi_tabletop_targets(op)`; Sicherung enthält dauerhafte Operatorpfade.

59 fokussierte Tests bestanden, darunter synthetischer Bildfluss mit zwei
Zielen, die beide Tischflächen schneiden: pro Fläche nur eigenes Ziel statt
Summe beider Ziele; auch Source-Abgang/Count-Reduktion. Weitere Tests prüfen
Originalpfad in Tracking/Study, wiederholten Aufruf, Rücknahme und Rollback
bei Erstellfehler. Gespeicherte Template-/Instanzgeometrien separat gelesen.
Diese Checks belegen noch keine reale Projektion oder GPU-Performance.
Manuelle Anwendung, gebündelte Raumprüfung und neue TD-Sicherung offen.

Manuell im TD-Python-Textport:

```python
exec(compile(open(r'C:\dev\Promotion_Prototypen\AISI\td_builders\isolate_aisi_tabletop_targets.py', encoding='utf-8').read(), 'isolate_aisi_tabletop_targets.py', 'exec'))
```

Gebündelt prüfen: eigene/fremde Zielkontur bei Teilüberlappung, mehrere Tische
bewegen/drehen, Tischabgang/Rückkehr und Count-Wechsel, Formatwechsel sowie
Tracking → AISI. Source-/Pfeildarstellung und Floor unverändert, keine fremden
Zielkonturen auf Tabletop, keine neuen Aussetzer/Flackern; GPU-Belastung live
beobachten. Kalibrierung, Homographien und Edge-Blend unverändert.

Erster manueller Aufruf des Tabletop-Isolationshelfers bricht beim Transparent-
TOP ab: `par[name] = 0` wird von TD nicht als Wertzuweisung akzeptiert.
Korrigiert auf `par[name].val = 0`; Testdouble lehnt die falsche API nun ebenfalls
ab. 59 fokussierte Tests erneut bestanden. Fehler liegt vor Anschluss des neuen
Zweigs und im abgesicherten Rücknahmeblock; tatsächlicher TD-Rückfallzustand
nicht automatisch gelesen. Erneute Helferausführung/Liveprüfung noch offen.

Zweiter Live-Aufruf zeigt zusätzlich fehlenden Constant-TOP-Parameter bei
der angenommenen RGBA-Namensfolge. Helfer löst RGB und Alpha nun vollständig
vor Wertzuweisung auf (insbesondere alpha statt colora). Fehlende Parameter
liefern verfügbare Namen statt None-Zugriff. Testdouble erfindet keine Parameter
mehr; beide Alpha-Varianten und fehlender Kanal geprüft. 60 Tests bestanden,
erneute manuelle Anwendung offen. Keine reale Erfolgsbestätigung behauptet.

Live-Anwendung meldet erfolgreichen Aufbau, Johannes sieht danach jedoch keine
Tabletop-Informationen. Rücknahme sofort angeleitet; deren Ausführung noch nicht
bestätigt. Konkreter Kontextfehler gefunden: die kopierte Source-/Pfeil-Geometrie-
Expression verwendet parent().findChildren und sucht im neuen Unter-COMP statt
im Layout-COMP. Korrigiert auf native absolute Pfade für alle fünf Source-/
Pfeilpaare, vor Anschluss echte OP-Auswahl prüfen, ebenso aktive Ziele/Masken.
62 Tests bestanden. Dies erklärt die fehlenden Sources/Pfeile; vollständige
Bildkorrektheit ist noch nicht physisch nachgewiesen.

Der manuelle Helfer bereitet ab jetzt standardmäßig nur eine getrennte Vorschau
vor und lässt den ursprünglichen Ausgang aktiv. Eigene ältere aktive Version
wird zunächst zurückgenommen. Vorschau-TOP:
`comp_layout_proposal/aisi_own_tabletop_targets/slot4_add`.
Erst nach Sichtprüfung `activate_aisi_tabletop_targets(op)` verwenden; bekannte
Operatorfehler verhindern die Aktivierung. Keine neue Live-Erfolgsbehauptung.

## Renderzweig verworfen; Polygon-Clipping vorbereitet — 2026-10-21

Johannes meldet starke Verzögerung bereits bei vorbereiteter Vorschau. Weiterhin
sichtbare fremde Ziele sind im nicht aktivierten Vorschauzustand erwartbar, da
der ursprüngliche Ausgang aktiv bleibt. Sofortige vollständige Rücknahme des
Vorschauzweigs angeleitet. Zusätzliche Render-/Maskenpässe sind verworfen.

Neuer Helfer `td_builders/clip_aisi_tabletop_targets.py`: ausschließlich
Tabletop-Target-SOP-Callbacks in Template/Instanzen ergänzen. Ursprüngliche
Kontur erzeugen, ihre Polygone geometrisch an der vorhandenen kanonischen
Source-Fläche desselben Items beschneiden. Source-Fläche mit bestehenden
Source-/Target-Geo-Posen ins Target-Lokalsystem transformieren; kein neuer
Footprint, keine neuen Koordinatenkonventionen. Fehlende Source sperrt Target.
Tracking/Study umgehen die Beschneidung. Keine zusätzlichen Renderer, keine
Änderung an bestehenden Render-, Masken- oder Projektorparametern. Alter eigener
Vorschauzweig wird vor Anwendung entfernt und ursprünglicher Ausgang verbunden.
Kein Force-Cook/Speichern; Callback-Rücknahme mit
`restore_clipped_aisi_tabletop_targets(op)`, auch für inzwischen neue Replikate.

49 fokussierte Tests bestanden; zusätzlich 240 Fälle mit echten gespeicherten
TD-149-Target-Callbacks und Style-DAT geprüft. Live-Anwendung/Performance und
physische Zielisolation noch offen. Der alte Renderzweig-Helfer lässt sich nicht
mehr versehentlich direkt aktivieren. Keine Erfolgsbehauptung für neue Variante.

```python
exec(compile(open(r'C:\dev\Promotion_Prototypen\AISI\td_builders\clip_aisi_tabletop_targets.py', encoding='utf-8').read(), 'clip_aisi_tabletop_targets.py', 'exec'))
```

Lag-Eingrenzung am 2026-10-21: Johannes bestätigt Rücknahme des Renderzweigs,
Lag bleibt. GPU-Stichprobe 45 %, ca. 4.5/10 GiB belegt, keine belegte GPU-Sättigung.
Konkrete Offline-Messung derselben aktuellen Fünf-Tisch-Discussion-8-Szene:
prepare_scene_output bei Stärke 0.95 ca. 2287.9 ms, bei 1.0 ca. 0.3 ms.
Die laufende UI hatte 0.95 gespeichert; auf vorgesehenen 100-%-Betrieb über
bestehenden /set-Endpunkt zurückgestellt. Dies ist eine belegte Senderbremse,
kein vollständiger Ende-zu-Ende-Latenznachweis.
Währenddessen öffnet Johannes TD-Version 149 neu und startet Layout-Launcher;
zuvor laufende Adapter/Sender blieben offen, daher zwei Ketten je Modul.
Alle Adapter-/Senderprozesse gezielt bereinigt und genau eine validierte Kette
mit beiden Bindings/frischer Szene/0.05-s-Intervall gestartet; neue Vision/TD
beibehalten. Protokolle lokal `data/aisi/debug/lag_diagnosis_20261021/`.
Danach Discussion 8/100 %, fünf Tische, ready. Clipping-Helfer noch nicht live
angewendet, physische Lag-Bestätigung nach Bereinigung noch offen.

## Discussion-Lag: Live-Versand von Planung entkoppelt — 2026-10-21

Johannes grenzt den weiterhin sichtbaren Lag ein: Vision direkt, TD/Projektion
verzögert; Input flüssig, Discussion langsam. Die frühere Einordnung allein
über 95 % war unvollständig: neue Fünf-Tisch-Discussion-8-Szene braucht auch bei
100 % ca. 2068 ms ohne Profiler. cProfile weist den Hauptanteil _solve_topology,
_attach_parking und _compact_park_targets zu. Posegenaue Cache-Schlüssel werden
bei Trackingrauschen neu; keine Cache-Quantisierung/Layout-Regeländerung.

`aisi.app.live_layout_worker`: genau ein Hintergrundauftrag, keine anwachsende
Queue. Der Discussion-Vorschaupfad im Sender wartet nicht mehr synchron auf
Layoutberechnung. Währenddessen aktuelle Sources auf letzten gültigen Slots,
Live-Occupancy und bestehende Study-Track-Kanäle weiter senden; letzte Ziele/
Chairs erhalten. Ergebnisse bei veränderter Anfrage, IDs/Reihenfolge, ROI,
Geometrie oder aktiver Bindung verwerfen. Source-Posen eines abgeschlossenen
Vorschlags vor Versand auf aktuellen Stand bringen, ohne Slotpermutation.
Leere Szenen/Tracking-only/Input/Groupwork bleiben auf bisherigen direkten
Pfaden. Bei Formatwechsel Ergebnis invalidieren. Ziele können weiterhin langsamer
neu berechnet werden; keine Echtzeitgarantie für Discussion-Planung behauptet.

68 fokussierte Tests bestanden, darunter blockierter Planner bei fortlaufenden
Source-Nachrichten, keine Warteschlange, veraltete Anfrage, Invalidierung,
Fehler/Recovery und Erhalt der ID-Bindung. Offline-Integration mit realer Szene:
92 Source-Updates in fünf Sekunden, Median 51.0 ms, maximal 65.7 ms Abstand.
Nur Sender mit unveränderten Argumenten neu geladen; Input 8, fünf Tische, ready,
Fehlerlog leer. Logs lokal `data/aisi/debug/discussion_async_20261021/`.
Physische Discussion-Prüfung noch offen; neuer Polygon-Clipping-Helfer bleibt
bis dahin unangewendet. Kalibrierung/Geometrie/Layout-Regeln unverändert.

## Neuer Auftrag: Vorschläge nach Generierung stabil halten — 2026-10-21

Johannes erklärt die fortlaufende quelladaptive Neuberechnung ausdrücklich für
nicht notwendig: nur Sources sollen nach der Generierung weiterlaufen; der
Vorschlag bleibt stabil. Umsetzung für Input, Groupwork und Discussion im
Layout-Vorschaupfad: einmal gültigen vollständigen Vorschlag pro Anfrage und
Inventar speichern, aktuelle Source-Posen per ID bei jedem Versand auffrischen.
Target-/Chairdaten bleiben bei Bewegung/Rotation/Jitter unverändert. Bei
geänderter Anfrage, ROI, Tischinventar/-reihenfolge/-geometrie oder manueller
Generierungsrevision neue Planung. Count/Abgang und veraltete Ziele weiterhin
explizit behandeln. Tracking-only und Legacy-Passthrough unverändert.

Format-UI bietet „Neu generieren“. Additiver lokaler State layout_revision wird
UI/Sender/Status konsistent mitgeführt; keine OSC-Vertragsänderung. Sichtbarkeits-
toggles lösen keine Neuplanung aus. Nebenfehler korrigiert: POST ohne
presentation_side darf bestehende Vortragsseite nicht leeren, sonst würde etwa
Chairs Off/On unabsichtlich Layout-Eingaben ändern.

73 Tests bestanden; synthetische Source-Bewegung/-Rotation hält Ziele und
Chairs unverändert, Revision/Inventar invalidieren, UI-Button/Persistenz geprüft.
Offline-Integration reale Discussion-Szene: initial 1945.1 ms, anschließend 100
bewegte Source-Updates bei identischen Zielen/Chairs, im Mittel 0.144 ms je Update.
Sender und UI mit bisherigen Argumenten neu geladen; aktueller Zustand Input 8,
100 %, fünf Tische, ready, neuer Knopf im HTTP-HTML, Senderfehlerlog leer.
Logs lokal `data/aisi/debug/stable_proposal_20261021/`.
Gebündelte physische Prüfung und Rückkehr zum noch unangewendeten Polygon-
Clipping stehen aus. Frühere Beobachtung kontinuierlich quelladaptiver Ziele
ist damit bewusst abgelöst, nicht rückwirkend als Implementierungsfehler gewertet.

Johannes bestätigt am 2026-10-21 die neue Vorschlagsbindung im Raum:
Vorschläge bleiben stabil, Sources folgen flüssig. Rückkehr zum Tabletop-Fix
explizit beauftragt. Aktueller HTTP-Zustand Groupwork 15/4, fünf Tische, 100 %,
Revision 1, ready; diesen Zustand nicht ungefragt ändern. Polygon-Clipping-
Helfer erneut fokussiert geprüft; vor Callback-Mutation jetzt vorhandene Source-
Punkte und tatsächliche TD-Primitive-vertices-API prüfen. Keine zusätzlichen
Renderer. Manuelle Anwendung und physische Prüfung weiterhin ausstehend.

Erster manueller Polygon-Clipping-Aufruf bricht vor Mutation in der neuen
Vorprüfung ab: echte TD-Poly besitzt keine .vertices-Eigenschaft. Umgestellt
auf direkte Vertex-Iteration (for vertex in primitive); Testdouble enthält
keine erfundene vertices-Eigenschaft mehr. 16 fokussierte Checks bestanden.
Vorheriger Graph durch diesen Aufruf unverändert; erneute Anwendung offen.

Polygon-Clipping manuell angewendet: sechs Callbacks, keine zusätzlichen
Renderer. Johannes meldet anschließend keine Zielrechtecke mehr auf Tabletop,
Sources/Pfeile aber weiterhin sichtbar. Ursache noch offen: keine eigene
geometrische Überlappung, falsche Beschneidung oder TD-Callbackfehler unterscheiden.
Lesender Helfer inspect_tabletop_target_clip.py vorbereitet: aktuelle Source-/
Target-Posen, SOP-Fehler und tatsächliche Primitive; ungeclippte Kontur in reinem
Python-Recorder mit Originalfunktion nachbilden, erwarteten eigenen Schnitt
ermitteln. Keine TD-SOP-/Operator-Mutation, kein Force-Cook. Bericht nach
manueller Ausführung lokal data/aisi/debug/tabletop_target_clip.json auswerten.

Lesender Livebericht tabletop_target_clip.json beweist Ursache für leere Ziele:
Source-SOP enthält acht Punkte, aber die kanonische Fläche referenziert nur vier.
Vier zusätzliche unreferenzierte appendPoly-Defaultpunkte wurden fälschlich als
zusätzliche Randvertices verwendet. Alle fünf erwarteten Schnitte deshalb leer,
obwohl Source-/Target-Posen nahezu deckungsgleich; keine Callbackfehler.
Korrektur v2 verwendet ausschließlich Vertices des einen Source-Flächenpolygons,
keine Änderung am vorhandenen Surface-SOP oder physischer Maskenkette. Regressions-
fixture bildet zusätzliche unbenutzte Punkte ab. 18 fokussierte Tests bestanden;
Replay aller fünf berichteten Posen liefert wieder sichtbare Zielsegmente.
Helfer aktualisiert bestehende v1-Callbacks ohne doppelten Wrapper und behält die
ursprüngliche Rückfallkopie. Erneute manuelle Ausführung/Liveprüfung noch offen.

Johannes bestätigt Polygon-Clipping v2 live am 2026-10-21: eigene Zielkonturen
wieder sichtbar, fremde erscheinen nicht mehr auf Tischplatten. Sources und
Pfeile bleiben flüssig. Erste physische Zielisolation damit bestanden; noch
keine neue TD-Sicherung. Laufzeitabgleich Groupwork 15/4, fünf Tische, 100 %,
Revision 1, ready; Senderfehlerlog leer. Nächster gebündelter Liveblock:
Formate bei gleichbleibend 15 Personen wechseln, Sources über eigene/fremde
Ziele bewegen/drehen, Tischabgang/Rückkehr, Chairs Off/On und Tracking → AISI.
Erwartung: Vorschlag bei reiner Bewegung stabil, eigene Tabletop-Ziele korrekt
beschnitten, keine fremden Ziele/alten Elemente, nach Wechsel/Rückkehr ruhiges
Bild. Testresultat dieses Folgeblocks noch offen; Kalibrierung unverändert.

## Gebündelte Tabletop-Abnahme bestanden — 2026-10-21

Johannes bestätigt Formatwechsel, Tischabgang/-rückkehr, Chairs Off/On und
Tracking → AISI: nur eigene Zielkonturen auf den Tabletops, Bodenausgabe
unverändert, Sources/Pfeile und gesamte Darstellung flüssig. Polygon-Clipping
v2 und stabile Vorschläge damit für diesen gebündelten Lab-Durchlauf bestanden.
Aktueller Laufzeitstatus Input 15, fünf Tische, 100 %, Revision 1, ready;
Senderfehlerlog leer. Kalibrierung/Homographien/Edge-Blend unverändert.

Johannes möchte den Stand sichern. Neue manuelle TD-Sicherung und anschließender
Öffnungscheck noch ausstehend. Im TD-Ordner existiert bereits
`AISI_v2.150_Grafik_überarbeitet.toe`; diese Datei nicht überschreiben.
Vorschlag für neue Sicherung: `AISI_v2.151_tabletop_targets_validated.toe`.
Prozessargument nennt weiterhin die beim Prozessstart geladene Version 149;
dies beweist nicht den aktuellen Save-As-Pfad. Keine automatische TD-Speicherung.
