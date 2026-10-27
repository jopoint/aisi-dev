# AISI Motion Design — Integrationsstand

## Systemtests insgesamt abgeschlossen, Stand sichern — 2026-10-27

Johannes meldet alle Systemtests abgeschlossen. Einzelne nachfolgende offene
Trial-/Testangaben sind historische Zwischenstände; nicht ohne Anlass erneut
installieren. Aktueller Grafik-/Betriebsstand und Nachweisgrenzen gebündelt im
[Checkpoint](MOTION_CHECKPOINT_20261027.md). Durchgängige 5-cm-Zielkontur und
gleich starke Chairs ausdrücklich im Raum akzeptiert, persistenter gemeinsamer
Hakenabschluss ebenso. Keine neue genaue TD-Datei/Speicherung bestätigt;
Sicherung umfasst Repository-Code/Tests/Übergabe. Untertisch bleibt pausiert.

## Durchgängige Konturen im Raum akzeptiert — 2026-10-27

Johannes bestätigt `update_motion_continuous_contours.install`: `passed: true`,
durchgängige Zielkontur und gleiche Chair-Strichstärke passen. Native GPU-
Installation und Sichtbefund positiv; keine neue Speicherung gemeldet.
Fortsetzung der Systemprüfung mit Groupwork ein Tisch/drei Teilnehmende/eine
Gruppe, danach fehlende Counts und Discussion. Keine Gesamtfreigabe aus dieser
gestalterischen Abnahme ableiten; Untertisch bleibt pausiert.

## Durchgängige Zielkontur und 5-cm-Chair-Ringe — Trial 2026-10-27

`update_motion_continuous_contours.py` ersetzt den gestrichelten Zielhelfer durch
das durchgängige Band `coverage(d)-coverage(d+5 cm)` auf Boden/Tabletop. Außen-
Footprint unverändert, Innenkante entsprechend der bisherigen Bandgeometrie.
Chair-Strichbreite ebenfalls 5 cm: Ringmitte von Außenradius−1,25 cm auf
Außenradius−2,5 cm verlegen, Halbbreite 2,5 cm. Damit Außenradius und Position
erhalten; zusätzliche Breite liegt innen. Bestehende Source-/Zielhilfen,
Feedback-Clipping/-Wachstum, Hakenabschluss und gemeinsame Reveal-Uhr erhalten.
Beide tatsächlichen Shader werden im isolierten Prüfzweig getestet, zusammen
installiert/rückgenommen; nur eigener Chair-DAT-Hash im Schutzsnapshot geändert.
Sieben fokussierte Offline-Tests und isolierter Float32-WebGL-Nachweis bestanden;
native TD-GPU-/Raumabnahme und manuelle Speicherung noch ausstehend.

## Source-Striche weiß, Zielkreis/-striche im Alpha — Trial 2026-10-27

Gemeinsamer Hakenabschluss nativ installiert und von Johannes mit zwei Tischen
akzeptiert. Anschließende Präzisierung der Hilfen: bewegte Source-Striche weiß,
nur Zielring und Zielstriche als Alpha-Aussparungen. Shader-Trial
`update_motion_source_bars_white.py` setzt nur die Source-Strich-Komposition
auf weiße Überlagerung zurück. Bei Überdeckung hat der bewegte Source-Strich
wie die Navigation Vorrang vor Zielhilfen. Ziel-Aussparungen bleiben sonst
auch durch grünes Feedback erhalten. Feedbackradius, Fade-Distanzen, Haken,
Runtime und geschützte Geometrie unverändert. 20 fokussierte Tests und
isolierter Float32-WebGL-Vergleich bestanden; native TD-/Raumabnahme offen.

## Persistente Fertig-Haken und gemeinsamer Abschluss — Trial 2026-10-27

Johannes akzeptiert Feedbackgröße/Alpha-Aussparungen nach nativer Installation.
Neuer Trial `update_motion_group_success.py`: eigener Layout-/ID-gebundener
Anzeigestatus aus unveränderten Engine-Phasen, Haken auch für anfangs korrekt
stehende `active=False`-Tische. Eintritt startet erst nach vollständigem Reveal,
damit vorher abgelaufene Erfolgszeit die Anzeige nicht verbraucht. Frühe Haken
bleiben; letzte Ankunft startet gemeinsame Haltezeit 1 s und Reverse-Pop 0,32 s.
Tracking-/Freigabeausfälle pausieren Zeit, fehlende/geänderte IDs blockieren
Abschluss. Wiederaufnahme nach vorhandener Hysterese öffnet Abschluss erneut;
keine Änderung von Ankunftsschwellen, Ziel-/Chair-Pose, Revision oder Reveal.
State-Spalte 5 erhält Z=Hakenmaßstab, W=Versionsmarker 1; Redisplay-X/Y erhalten.
Ohne Marker bleibt alter Shaderpfad kompatibel. GPU-Nachweis vor Änderung beider
DATs, gemeinsamer Rollback bei Fehler. Zwölf Offline-Tests und isolierter
Float32-WebGL-Vergleich bestanden, native TD-/Raumabnahme noch ausstehend.

## Radius 80 % bei 20 cm, Hilfen im Alpha — Trial 2026-10-27

Präzisierung durch Johannes: `update_motion_feedback_size_cutouts.py` ersetzt
die vorherige Mindestkurve durch zwei glatt verbundene Distanzabschnitte:
80→20 cm Abstand: Radius 35→65,12 cm; 20→8 cm: 65,12→81,4 cm. Damit bei 20 cm
exakt 80 % des Maximalradius, unabhängig vom Orientierungs-/Kontaktfortschritt.
Kontaktblende bleibt erhalten. Source-Striche und Zielhilfen wieder transparent
durch weiße/gestrichelte Ziele und grünes Feedback, statt weißer Auflage.
Erfolg, Ziel-/Chair-Posen, Revision, Boden und Kalibrierung unverändert.
Elf fokussierte Tests sowie isolierter WebGL-Alpha-/Radiusnachweis bestanden;
eigene native TD-GPU-Transaktion und physische Abnahme ausstehend.

Erster nativer Installversuch stoppte vor Shaderwechsel an der Alpha-Prüfung:
teilgedeckte AA-Pixel (`coverage > .999`) wurden fälschlich als Null-Kern geprüft.
Float32-Reproduktion bestätigt Rest-RGBA 0,000032 an 33-Grad-Kante, Kern null.
Prüfung korrigiert auf exakten Kern und separate Komplementprüfung der Kante;
kein Grafikcode geändert, kein erneutes Prepare nötig. Fünf fokussierte Tests
inklusive Ablehnung sichtbarer Kern-/Kantenfehler bestanden. TD-Wiederholung offen.

## Größerer Feedback-Halo vor Erfolg — Trial 2026-10-27

`update_motion_feedback_proximity.py` ändert ausschließlich die Radiusformel:
Maximum aus bisheriger geglätteter 1,2-facher Progression und weicher Annäherung
von 80 bis 20 cm. Radius bleibt 35–81,4 cm; bei 20 cm bereits maximal, unabhängig
von noch ausstehender Winkelkorrektur. Kontaktblende, Richtung/Asymmetrie,
Farbe, vollständiges Ziel-Clipping und Erfolgsentscheidung unverändert.
Eigener Prüfzweig/Backup mit GPU-Nachweis vor Installation; kompatibel mit beiden
Zielstilen. Zwölf Offline-Tests und isolierter WebGL-Vergleich bestanden;
TD-Installation und physischer Befund noch ausstehend. Kein automatisches Speichern.

## Gestrichelte Zielkontur als rücknehmbarer Trial — 2026-10-27

Nach positivem Groupwork-Fünftischfall neuer gestalterischer Auftrag: solide
weiße Zielfläche durch dicke gestrichelte Kontur ersetzen, gleicher Umriss und
gleiches Muster auf Boden/Tabletop; grüner Feedback-Kreis bleibt erhalten.
`update_motion_target_dashes.py` vorbereitet mit 5 cm Innenband, 14 Strichen,
74 % Strichanteil und fortlaufender echter Umfangslänge über gerundete Ecken.
Voller semantischer Ziel-Footprint bleibt für Feedback/Geometrie/Ankunft erhalten.
Keine Außenvergrößerung oder Änderung von Masken/Projektoren/Engine/Revision.
Vier fokussierte Tests sowie isolierte Shader-Kompilierung/-Darstellung bestanden,
noch kein nativer TD-GPU-/Raumnachweis. [Textport-Trial](MOTION_BETRIEB.md).

## Reveal abgenommen, Web-UI überarbeitet — 2026-10-27

Johannes bestätigt nach Reveal-Installation vollständige flüssige Welle erst
nach Freigabe, feste Ziele und Chairs. Keine neue Speicherbestätigung für
diesen Patch. Auf Folgeauftrag neue reduzierte Learning-Format-UI bereitgestellt,
ohne TD-Graph-/Masken-/Kalibrierungsänderung: Formatkarten, passende Einstellungen,
ein Aktivierungsbereich, Technik unter Diagnose. HTTP-/Browserprüfungen bestanden;
nur gemeinsamer Web/Motion-Prozess kontrolliert aktualisiert, andere Dienste
erhalten. Nach Aktualisierung einmalige Vorschlagsaktivierung im Web nötig.

## Neue visuelle Reveal-Uhr nach Freigabe — vorbereitet 2026-10-27

Welle wird bis zum Abschluss beider automatischer Vollprüfungen verborgen.
Danach beginnt eine eigene Drei-Sekunden-Anzeigeuhr bei null; die bestehende
Engine-/Layoutzeit bleibt erhalten. Neuer State-Texel `[5,1]` nur für den
Motion-Shader, gemeinsame globale Uhr und Chair-/Masken-Verbraucher unverändert.
Kein neues Layout, keine Ziel-/Chair-Änderung, kein Engine-Reset. Dieselbe Revision
bekommt bei Wiederfreigabe keine zweite Welle. Patch der tatsächlichen DATs mit
isolierter GPU-Probe und eigener Sicherung. Zehn fokussierte Tests bestanden,
TD-/Raumprüfung noch offen. [Textport-Ablauf](MOTION_BETRIEB.md).

## Kein Legacy-Fallback im AISI-Modus — 2026-10-27

Ausdrücklicher Auftrag: bis zur Motion-Freigabe und bei Ausfällen keine
Layoutgrafik im AISI-Modus. Vorbereiteter Helfer
`motion_no_legacy_fallback.py` sperrt ausschließlich die bisherigen
Legacy-Grafikquellen für Boden/Tabletop/Chairs mittels eigener transparenter
Zweige. Vorhandene Motion-Gatter und Originalmaskierung bleiben unverändert;
Modi 0/1 und Kalibrierungsansichten behalten ihre Originalbilder.
Acht fokussierte Offline-Fälle bestanden, noch keine Installation/Abnahme in TD.
Installations-/Rücknahmefolge: [Betrieb](MOTION_BETRIEB.md).

## Automatische TD-Erstfreigabe live bestanden — 2026-10-27

Eigener Auto-Baustein installiert und nach Web-Aktivierung erstmals technisch
bestanden: `phase: active`, `approved: true`, beide Flags an; Sitzung 4012265,
Revision 2, `table_01`, TD-Frame 620089. Separater HTTP-Gegencheck bestätigt
passende Freigabe in Web-UI, Input/drei Chairs, Quelle frisch. Keine manuelle
Freigabe für diesen Durchlauf angefordert. Raum-Sichtbefund, Fehlerfälle,
Kaltstart und manuelle Speicherung noch offen; keine automatische Speicherung.

## Automatische Freigabe nach Maskennachweis vorbereitet — 2026-10-27

Neuer expliziter Auftrag: nach dem Start nur Web-Vorschlag aktivieren müssen.
Zusätzlicher eigener TD-Execute-Baustein vorbereitet: Start gesperrt, bestehende
volle Schutz-/Geometrie-/Pixel-/Chair-Prüfung, spätere fortschreitende
Frame-Bestätigung, Freigabe, separate Ausgabekontrolle. Keine neue Zielberechnung
oder Änderung an Kalibrierung, Masken, vorhandenem Routing oder Motion-Engine.
Heartbeat zur bestehenden Web-UI, ungültig bei falscher Sitzung/Revision/IDs oder
fehlender Aktualität. 364 Offline-Tests bestanden, sieben GPU-Fälle übersprungen;
TD-Installation/Live-/Raumprüfung noch offen. [Einmalige Einrichtung](MOTION_BETRIEB.md).
Untertisch bleibt pausiert.

## Funktionaler Web-Anschluss installiert — 2026-10-27

Auf Folgeauftrag Start/Status/Wiederanlauf vereinheitlicht und explizite
Motion-Aktivierung in bestehende Web-UI integriert. Getrenntes Tk-Fenster im
neuen Pfad ersetzt; D005a erhalten. Neue Sitzung nur bei bewusster
Neuinitialisierung, TD-Ausgänge vorher aus; keine automatische TD-Freigabe.
[Bedienung, Startbefehle und Nachweis](MOTION_BETRIEB.md).
352 Motion-Tests bestanden, sieben optionale GPU-Fälle übersprungen; echte
Kameraframes im neuen Webstatus frisch. UI→TD- und Raumprüfung noch offen,
kein allgemeiner Standardwechsel. Untertisch bleibt pausiert. Der folgende
Lückenabgleich beschreibt den vorherigen Stand.

## Nächster regulärer Block: Systemintegration vor Standard und UI — 2026-10-27

Auftrag von Johannes: vollständigen aktuellen AISI-Betrieb bis fünf Tische mit
Learning-Format-UI prüfen, danach Motion als Standard einrichten, danach UI
gestalterisch modernisieren. [Testplan und Reihenfolge](TOUCHDESIGNER_MOTION_SYSTEM_TEST_PLAN.md).
Untertisch-Experimente bleiben pausiert. Schutz der bestehenden Study-/Tracking-
Modi, Kalibrierung und Maskenreihenfolge unverändert.
Codeabgleich: Motion-Aktivierung liegt aktuell noch im separaten Kamera-Tk-
Controller; UI-Werte werden dort nur beim Aktivieren gelesen. Web-`regenerate`
ist nicht direkt mit Motion verbunden. Diese funktionale Anschlusslücke ist Teil
der ersten Abnahme, keine bereits geprüfte Integration. Noch keine neue reale
Mehrtischprüfung, Standardumschaltung oder UI-Gestaltungsänderung vorgenommen.

## Untertisch-Versuch pausiert — 2026-10-27

Johannes möchte den zeitaufwendigen Versuch vorerst zurückstellen. Aktueller
Arbeitsstand, geprüfte Modelle, tatsächliche TD-2022-Diagnose und konkreter
Wiedereinstieg sind in [der Untertisch-Übergabe](TOUCHDESIGNER_UNDER_TABLE_HANDOFF.md)
gesichert. Keine weitere Arbeit ohne neuen Auftrag. Bestehende Motion-Ausgabe
weiterhin unverändert, kein Untertisch-Produktivpatch oder Raumversuch, keine
Kalibrierungs-/Maskenänderung oder automatische Speicherung. Neuer Folgeauftrag
autorisiert ausschließlich Commit/Push: Grafikänderungen, Helfer, Tests und diese
Übergabe einschließlich der unvollständigen nativen Probe werden gemeinsam
gesichert. Untertisch-Versuch bleibt pausiert und nicht produktiv installiert.
Motion-Prüfung zur Sicherung erneut 345 bestanden, sieben optionale GPU-Fälle
übersprungen. Laufzeit-/Kalibrierungsdaten und lokale Simulationsszene ausgenommen. Wiederaufnahme
bei nativer Format-/Chair-Auflösungsvorbereitung, erfolgreiche Weltbild- und
Float32-Projektorprüfungen nicht unnötig wiederholen.

## Aktuell: native Ausgabe plus finale Tabletop-Komposition vorbereitet — 2026-10-27

Neuer ausdrücklich beauftragter isolierter Helfer
`prepare_motion_under_table_native_probe.py` mit `prepare(op,projector=0/1)`,
`check(op)`, `cleanup(op)`, ohne produktive Installationsfunktion. Eigener
Simulations-State und Kopien tatsächlicher Motion-Renderer, nativer Select-
Resampling-Stufen und Masken-/Floor-/Tabletop-Komposition. Chair-Quelle als
einmaliger Bildsnapshot, damit der Vorher-/Nachhervergleich keine Live-Animation
zwischen Messungen enthält; tatsächliche Ziele/Chairs werden nicht verändert.
Rohe Originalmasken-Alpha-Konvention wird lesend als konstant eins oder Coverage
erkannt und im synthetischen Maskenraster nachgebildet; sonst Abbruch. Reorder-
Einstellungen, Masken-Multiply und Null-/Select-Stufen kopiert. Content-/Layer-
Steuerung nur gelesen; Content mit beiden Ebenen erforderlich, keine automatische
Umschaltung. Eigene Konstanten für bestätigte Index-/Auflösungsausdrücke, sonst
unbekannte dynamische Parameter ablehnen.

Native effektive Formate/Raster aus aktuellen TOPs, keine Float32-Erzwingung.
RGBA8/16 fixed, RGBA16/32 float unterstützt, unbekannte Speicherung abgelehnt.
Eigene Kopien nach GPU-Kochen gegen Originalformat/Raster geprüft. Original-
Out/Output-Null müssen unveränderte Weitergabe des finalen Composite bestätigen.
Projektorabhängige Transformations-/Warp-/Blend-/Maskenoperationen und finale
Tabletop-Over-Komposition kopiert, Shader und aktive Uniformkonstanten direkt
vom laufenden Graph; keine Kalibrierung aus DATs neu anwenden.

Messung: sechs Posefälle je Projektor plus completed und Source ungültig.
Native Tabletop-Renderer-Vergleich, tatsächliche Front/Floor-Finalbilder und
premultiplizierte Over-Referenz mit ausgewiesener formatabhängiger Rundungsgrenze.
Gesperrte Maskenbereiche und opake Frontpixel erlauben höchstens 1e-06 RGB-
Zusatz/Änderung unabhängig von dieser Rundungsgrenze. Gemeinsame Original-
Signaturen inklusive Shader-/Kalibrierungs-DATs sowie native Spezifikationen,
Steuerwerte und Engine/Reader/Revision schützen die Produktion. Ein Projektor
pro Probe, keine Window-/Projektorverbindung, kein Speichern. Cleanup wiederholbar.
337 Offline-Tests bestanden, sieben optionale GPU-Fälle übersprungen.
TD-GPU- und physischer Nachweis dieser Folgestufe noch offen.

Erster nativer `prepare(op,projector=0)`-Aufruf scheitert vor Einbau an unbekannter
roher Masken-Alpha-Konvention (`raw_mask_alpha`). Eigener COMP im Fehlerpfad
entfernt. Beide bisher unterstützten Fälle (Alpha konstant 1 oder Alpha≈Rot)
reichen für den tatsächlich laufenden Raw-Render nicht aus. Rohe/reorderte
RGBA-Verteilung und tatsächliche Reorder-Kanalzuordnung zuerst lesend diagnostizieren;
keine Kalibrierungs-/Maskenänderung, keine ungeprüfte Alpha- oder Toleranzanpassung.

Nach tatsächlicher Diagnose korrigiert: Raw-RGB ist nur ca. 0,098–0,102 im
Tischinneren, während Alpha dort 1 und im Hintergrund 0 ist. Der aktive
Reorder kopiert Alpha auf alle drei RGB-Ausgänge und setzt A auf Eins
(`chanmask=15`, `format=useinput`). Raw-/Reorder-Pixel in gleicher Auflösung
und genaue Parameter werden vor Modellaufbau geprüft; kein Alpha=Rot mehr
vorausgesetzt. Im synthetischen Raw-TOP nur Coverage in A nachgebildet, RGB=0
weil diese Kanäle nach bestätigtem Reorder verworfen werden. Kein Eingriff in
Originalmaterial oder Renderlicht. Nachfolgende native Kopie des Reorders
übernimmt tatsächliche Einstellungen.
TD-2022-Fallback ergänzt: fehlende PixelFormat-Eigenschaften durch eindeutig
belegte `useinput`-Kette auflösen, mehrere Inputs nur bei identischem Format,
Select-Referenz folgen; unklare In-Reihenfolge/Zyklen/gemischte Formate ablehnen.
341 Offline-Tests bestanden, sieben optionale GPU-Fälle übersprungen. Eigener
Teilzweig des fehlgeschlagenen Versuchs war entfernt; Modul neu laden und native
Vorbereitung erneut ausführen, GPU-Nachweis noch offen.

Zweiter nativer `prepare`-Aufruf stoppt am Formatresolver des echten
`simulation_chairs_switch` (Switch TOP) vor Chair-Snapshot. Unterschiedliche
Formate an Switch-Eingängen sind bei eindeutiger Auswahl kein gleichzeitiger
Mischfall. Resolver folgt jetzt nur bei deaktiviertem Blending und gültigem
ganzzahligem Index dem gewählten Eingang, entsprechend Switch-Dokumentation.
Ungewählte Formate nicht gleichsetzen oder erzwingen; Blending/Bruchindizes/
ungültige Auswahl und unbekannte Composite-Mischfälle bleiben Sperrgründe.
Kein Schreiben an Original-Switch oder Ausgabe; eigener Teilzweig entfernt.
345 Offline-Tests bestanden, sieben optionale GPU-Fälle übersprungen.
Neue Vorbereitung und native GPU-Prüfung weiterhin offen.

Dritter nativer Versuch stoppt nach Chair-Snapshot an unbekannter Dynamik von
`composite_floor_with_synth_chairs` (Composite TOP), eigener Teilzweig entfernt.
Keine Originalparameter geändert. Neuer Sammelbericht `inspect_stages(op)`
liest sämtliche vorgesehenen Kopierstufen auf dynamische Parameter und ungelöste
Formate; liefert Namen/Modi/evaluierte Werte/Ausdrücke/Bindungen. Dadurch gezielt
nur bestätigte Abhängigkeiten in eigenen Kopien einfrieren; keine pauschale
Freigabe aller dynamischen Parameter. Kein Aufbau, kein explizites Kochen,
kein Speichern. 17 fokussierte native Offline-Tests bestanden, TD-Nachweis offen.

## Aktuell: Weltbildvergleich und beide kalibrierten Float32-Proben bestanden — 2026-10-27

Projektor 1 vollständig zurückgemeldet mit `passed: true`: sechs Fälle,
zusätzliche Pixel 103279–238112 (klar freier Maskenbereich 93838–230741),
RGB-Gleichungsfehler maximal 8,195639e-08. Gesperrte Pixel
670013/671904/671294/0/2346/37780, maximaler Zusatz 7,748604e-07 ≤ 1e-06.
Bei (320,350)/0 Grad keine vollständig gesperrten Pixel, dort kein Sperrnachweis.
Projektor-0-Probe laut `removed: true` zuvor entfernt; Originalkalibrierung,
Masken und Ausgabe unverändert. Beide Proben inzwischen abwesend: Weltbild-
Cleanup meldet `removed: true`, Ausgabe unverändert, nicht gespeichert;
erneute Cleanup-Aufrufe melden für beide Pfade fehlende Probe, keine weitere
Entfernung nötig. Beide Modelle zeigen zusätzliche projizierbare Zielanteile
innerhalb des vertikalen Footprints, bei erhaltener Projektormaskierung.
Nur Modellnachweis im isolierten Float32-Floor nach Maske, vor finalem Tabletop-
Composite; keine physische Freigabe. Nächster Block native Formate und finale
Komposition, erst anschließend möglicher Raumversuch. Keine Produktivinstallation.

Projektor-0-Folgenachweis im laufenden TD bestanden: sechs Float32-Fälle
(180,150)/(320,350), je 0/33/90 Grad; RGB-Gleichungsfehler maximal
6,705523e-08, zusätzliche Pixel 49109–192815, vollständig freier Maskenanteil
49109–183186. Bei (180,150) kein vollständig gesperrter Bildpixel erfasst;
kein dortiger Sperrnachweis. Bei (320,350) gesperrte Pixel
832113/835269/833759, Zusatz maximal 0/7,748604e-07/0 (Toleranz 1e-06).
Originalmasken/Kalibrierung unverändert, unverbundene Simulation, nichts
gespeichert. Projektor-0-Zweig entfernt und Projektor-1-Nachweis oben ergänzt.
Native Ausgabequantisierung, finale Tabletop-Komposition und Raumvalidierung offen.

Weltbild-Probe laut vollständiger TD-Ausgabe `passed: true`: zwölf GPU-Gruppen,
neun Überlappungsfälle (0/33/90 Grad, ein/fünf Tische, Reveal). Zusätzliche
Zielpixel 28946–164068, maximaler Muster-Floatfehler 5,9604645e-08,
RGBA8-Abweichung 0; Tabletop Floatfehler 0. Sonderfälle und Erfolg/Redisplay
bestanden. Unverbundene Simulation, keine produktive Shader-/Masken-/
Kalibrierungsänderung oder Speicherung, keine physische Validierung.

Nächste eigene Probe `prepare_motion_under_table_projector_probe.py` kopiert
nur statische relevante TOPs und Shader aus tatsächlichen Projektorzweigen:
Floor-/Masken-Homographie, aktive Uniformkonstanten, für Projektor 1 bestehende
Floor-/Masken-Transformationen, Invert-Level und Floor-Multiply. Vorhandene
Blend-Quellen nur lesend referenziert; keine COMPs/Callbacks kopiert und keine
Kalibrierungs-DATs ausgeführt oder neu angewendet. Unbekannte dynamische
Parameter/Raster/Verbindungen führen zum Abbruch. TOP-Netzwerkgrenzen mit eigenen
Select TOPs überbrückt. Eigene Float32-Kopien bei 3840×2160 zur Isolierung von
nativer Quantisierung; Originalformate bleiben unverändert. Ein Projektor pro
Vorbereitung, eigene Probe vor dem anderen entfernen.

Messstufe nach Floor-Maskierung und vor finalem Tabletop-Over: Differenz
Nachher−Vorher = transformierter, geblendeter, maskierter Zusatzanteil;
vollständig gesperrte Maskenpixel ohne Zusatzlicht. Zwei simulierte Positionen,
drei Drehungen je Projektor. Referenz sind aktive Parameter und tatsächliche
Shader/Korrekturen, keine idealisierten Homographien aus Buildern.
328 Offline-Tests bestanden, sieben optionale GPU-Fälle übersprungen.
TD-Vorbereitung/-Prüfung dieser Stufe offen. Native Ausgabequantisierung,
finale Komposition und tatsächliche Untertischprojektion noch nicht nachgewiesen.

## Aktuell: isolierter Untertisch-Contentvergleich vorbereitet — 2026-10-27

Autorisiert: isolierter Versuch nur Bodenzielgrafik vom frühen Footprint-Ausschluss
ausnehmen, bestehende Projektormaske/Kalibrierung erhalten. Neuer Helfer
`prepare_motion_under_table_probe.py`, eigener Container COMP
`/project1/comp_aisi_motion_under_table_probe`, Schnittstellen ausschließlich
`prepare(op)`, `check(op)`, `cleanup(op)`. Kein Installieren oder Aktivieren.
Vorher-/Nachher-Shader aus tatsächlichem produktivem Text, synthetischer State-TOP.
Neue Weltbild-Floor-Ausgabe: bisherige Ausgabe unverändert plus separat überlagerte
Ziel-Füllanteile × gemeinsame Source-Footprint-Belegung. Reveal-/Erfolgs- und
Wiedereinblendungsfaktoren pro Ziel erhalten. Pfeile/Reveal-Welle bleiben
ausgeschlossen, Tabletop-Code und produktiver Standardshader unberührt.

Diagnostik-TOP codiert Footprint-Belegung, akkumuliertes Zielalpha und deren
Produkt; GPU-Differenzprüfung gegen ausschließlich diesen Zusatzanteil.
Teilweise geglättete SDF-Kanten mit bestehender enger AA-Toleranz und maximal
einer RGBA8-Stufe, flache Regionen streng; Tabletop mit bestehendem Float32-
Epsilon-/exaktem RGBA8-Vergleich. Fälle: 0/33/90 Grad, ein/fünf Tische,
Reveal/Erfolg/Redisplay sowie ungültig/inaktiv/completed/ausgeblendet/ohne Überlappung.
Prüfung ausschließlich eigener TOPs. Projektorzweige inklusive Matrizen,
Korrektur- und Kalibrierungs-DATs/Shader/Transforms/Blending vor und nach Vergleich
signaturgeschützt. Keine produktive Verdrahtung, keine Speicherung.
319 Offline-Tests bestanden, sieben optionale GPU-Fälle übersprungen.
TD-GPU-Test noch offen; Weltbildvergleich beweist keine kalibrierte
Projektorbildraum-Erreichbarkeit oder tatsächliche Untertischprojektion.

## Boden unter Tisch: laufenden Projektorgraph lesend geprüft — 2026-10-27

Lesender Abschluss aus dritter Ausgabe: Tabletop und Tabletop-Maske je Projektor
verwenden dieselben neun evaluierten h0/h1/h2-Komponenten und identischen
Shader-Vorspann einschließlich hardcodierter lokaler Korrekturfunktion.
Vollständige `main`-Funktionen unterscheiden sich ausschließlich im Alpha bei
UV außerhalb ROI (Tabletop 0, Maske 1). Projektorpixel → inverse Homographie →
`physicalCorrection` → Input-UV identisch. Lokaler Vergleich der gelieferten
Texte bestätigt beide Projektoren; kein GPU- oder neuer physischer Test.
Aktive Uniform-Konstanten statt abweichend genauer Matrix-DATs als Referenz
verwenden, keine bestehende Kalibrierung neu anwenden.

Die getrennte Floor-/Tabletop-Abbildung und nachgeschaltete invertierte
Tabletop-Maske können bereits geometrisch erreichbare Bodenstrahlen unterscheiden.
Pauschaler Motion-Footprint-Ausschluss ist zusätzlicher, früherer Informationsverlust.
Ein künftiger Versuch sollte ausschließlich die Bodenzielgrafik davor bewahren,
die bestehende Projektormaske und sämtliche Kalibrierung unverändert erhalten.
Nicht die gesamte `occupied`-Verwendung entfernen (Reveal/Pfeile/Preview betroffen).
Kein Aufbau oder Produktivpatch im ausschließlich lesenden Auftrag; tatsächliche
Untertischfläche und Tischplattenfreiheit physisch noch nicht geprüft.

Zweite Ausgabe: Tabletop-/Masken-`homography_matrix`, `homography_matrix_inv`
und `correction_points` (Table DATs) je Projektor textgleich. Beide Masken-Outs
direkt am `homography_warp` (GLSL TOP), Floor-/Tabletop-Outs zusätzlich durch
Blend-Multiply; diese getrennte Behandlung erhalten. Eingebetteter Motion-
Shader bestätigt pauschale Footprint-Ausblendung `(1.0-occupied)` vor Warps.
Homographie-Shader besitzen zusätzlich hardcodierte `physicalCorrection`-
Raster, deren einzelne Werte von Korrektur-DATs abweichen; keine Änderung
daraus ableiten. Die auf 100 Zeilen begrenzte Ausgabe enthält die Shader-
Hauptfunktionen nicht vollständig. Effektive h0/h1/h2-Uniformwerte ebenfalls
noch nicht ausgegeben. Folgeschritt ausschließlich vollständige Main-Abschnitte,
Uniformbindungen und direkter Tabletop-/Masken-Korrekturfunktionsvergleich.

Arbeitsdatei laut Textport: `AISI_v3.2_motion_lab_checkpoint_20261026.12.toe`.
Beide tatsächlichen Projektorzweige verwenden getrennte Floor-/Tabletop-/
Tabletop-Masken-Homographie-COMPs. Masken-Out → Level TOP (Invert=1) →
`floor_masked_warped1` (Composite TOP, Multiply mit Floor-Homographie-Out).
Danach Tabletop-Homographie-Out über Boden in `composite_final` (Composite TOP,
Over) → `out1` (Out TOP). Projektor 1 erhält vorgeschaltete 180-Grad-Transform-TOPs;
sein `comp_homography_floor_alt` gehört nicht zum berichteten aktiven Ausgangspfad.
Die mit aufgelisteten `window_projector_0/1` sind Window COMPs.

Projektorabhängige Maskierung damit strukturell vorhanden; geometrische
Korrektheit und identische Tabletop-/Masken-Korrekturpfade noch nicht bewiesen.
Nächste lesende Untersuchung: sechs aktive Homographie-Teilgraphen samt
Shadern/Matrixreferenzen sowie tatsächlicher Motion-Footprint-Ausschluss.
Kein Aufbau/Bypass/Testlicht, keine erzwungenen Cooks und keine Änderungen oder
Speicherung. Untertisch-Erreichbarkeit nicht physisch geprüft.

## Aktuell: Haken-Pop-out statt Fade installiert und abgenommen — 2026-10-27

Folgewunsch: akzeptiertes Aufploppen erhalten, nach einer Sekunde ähnlich
verschwinden, ohne Fade. Neuer Helfer `update_motion_success_pop_out.py` ersetzt
nur das bestehende Haken-Overlay. Bis Sekunde eins unveränderte Eingangsskalierung,
danach zeitliche Umkehr über 0,32 s; Deckkraft vollständig weiß statt langsamem
Alpha-Abfall. Ab 1,32 s unsichtbar. Bestehende Ausrichtung und Mitte, Erfolgszeit,
Source-Maske, Führungsrückkehr, Boden und Kalibrierung bleiben erhalten.
Eigene Probe/Sitzung/Sicherung. GPU-Prüfplan: Eintrittsgeometrie gegen bisherige
Variante nach Entfernung nur des alten Alpha-Fades, zeitlich gespiegelte
Ein-/Ausgangsformen, Endzeit und volle Deckkraft bei drei Rotationen;
Guidance/Source-Ungültigkeit/Wiedereinblendung und Bodenausgabe erhalten.
312 Offline-Tests bestanden, sieben optionale GPU-Fälle übersprungen.
Johannes meldet Installation `passed: true` und bestätigt am realen Tisch
Aufploppen und Verschwinden nach einer Sekunde mit Pop-Bewegung; „Passt so“.
Pop-out ist damit gestalterischer Standard und löst den Drei-Sekunden-Fade ab.
Vollständiger GPU-Report nicht geliefert. Separate aktuelle Live-Prüfung nach
diesem Patch und Speicherung noch offen; keine umfassende Raumabnahme ableiten.

## Aktuell: Haken-Pop/Fade installiert und gestalterisch abgenommen — 2026-10-27

Dauer durch Johannes geklärt: drei Sekunden, nicht Minuten. Neuer eigenständiger
Helfer `update_motion_success_pop.py` patcht nur Haken-Overlay und ergänzt
`successPop(age)`: Ease-out-back über 0,32 s mit knapp 10 % Übergröße, anschließend
exakt ursprüngliche Endgröße. Alpha von Beginn an `clamp(1-age/3,0,1)`, kein
spätes Abblenden oder Halteintervall. Skalierung um Source-Navigationszentrum,
bisherige Leserichtung aus Zielpose unverändert. Vorhandene Erfolgsanimation,
Source-Ungültigkeit und weiche Führungsrückkehr bleiben erhalten.
Eigene GPU-Probe, Sitzung und hash-gesicherte Rücknahme; bestehende Haken-Sicherung
nicht umgeschrieben. GPU-Prüfplan: messbare Übergröße/Rückfederung, Alphaverlauf,
Weiß/Premultiplikation, Ausrichtung, Guidance/Source-Ungültigkeit/Wiedereinblendung
und unveränderte Bodenausgabe. 307 Offline-Tests bestanden, sieben optionale
GPU-Fälle übersprungen. Johannes meldet Installation `passed: true` und bestätigt
am realen Tisch Aufploppen und Fade innerhalb von drei Sekunden; „Passt so“.
Vollständige GPU-Ausgabe nicht geliefert. Separate aktuelle Live-Prüfung nach
diesem Patch und Speicherung noch offen; keine umfassende Raumabnahme ableiten.

## Aktuell: weißer Erfolgshaken vorbereitet — 2026-10-27

Nähe-Fade von Zielkreis und Strichen durch Johannes im Raum abgenommen und TD
manuell gespeichert. Neuer Versuch: weißer Haken an der Source-Navigationsmitte,
drei Sekunden ab bestehender Zielerreichung (einschließlich 0,18 s Ein- und
0,2 s Ausblendung). `update_motion_success_check.py` fügt nur eine Zeichenfunktion
und einen Tabletop-Overlay nach dem bisherigen Erfolgszweig ein, damit der Haken
auch in `completed` bis Sekunde drei sichtbar bleibt. Bestehende Erfolgsauflösung,
Bodenausgabe und weiche Rückkehr zur Führung bleiben erhalten. Keine neue
Runtime-Uhr, Engine-Instanz, Revision, Zielberechnung oder Maskenverdrahtung.

Leserichtung: von der zur ROI-Mitte gewandten Längsseite; die Hochachse des
Hakens steht senkrecht auf der Längsseite. Gewählt anhand der eingefrorenen
Zielpose, Position am bisherigen Source-Navigationszentrum. Bei Gleichstand
feste lokale +Y-Längsseite. Haken 3 cm Strichbreite mit runden Kappen,
etwa 23 × 18 cm Außenmaß, weiß und premultipliziert, an bestehende Source-Maske
und Wiedereinblendung gebunden. Ungültige Source oder neue Führungsphase zeigt
keinen Erfolgshaken. Eigene Probe/Sitzung/Sicherung und streng begrenzter Patch.
299 Offline-Tests bestanden, sieben optionale GPU-Fälle übersprungen.
GPU-Prüfplan: Dauer über beide Erfolgsphasen, reine Weißdarstellung,
Leserichtung bei 0/33/90/180/270 Grad und mehreren ROI-Positionen,
ungültige Source, Wiedereinblendung und unveränderte Bodenausgabe.
Noch nicht in TD installiert; GPU-/Live-/Raumabnahme und Speicherung offen.

Erster Installationsversuch stoppt vor produktiver Änderung mit
„Haken zur ROI-Längsseite falsch ausgerichtet“. Prüfcode leitete Array-Y direkt
aus Welt-Y ab. Korrektur ausschließlich am Prüfcode: unabhängige vorhandene
Masken-Renderausgabe bei (180,180) bestimmt X-/Y-Arrayrichtung eindeutig über
Flächenschwerpunkt. Anschließend unverändert strenge Prüfung der vier
Haken-Strichpunkte bei fünf Drehungen und fünf ROI-Positionen; Fehler nennt
jetzt Position/Drehung/Punkt/Alpha. Keine Toleranzlockerung oder Shaderänderung.
Vier Array-Achsenkombinationen sowie leere/mehrdeutige Prüfmasken offline geprüft;
Motion-Suite 308 Fälle, 301 bestanden, sieben optionale GPU-Fälle übersprungen.
Bestehende Probe bleibt nutzbar; erneuter GPU-Nachweis in TD noch offen.

Nachtrag: Johannes meldet danach Installation `passed: true`; vollständige
GPU-Ausgabe nicht übernommen. Erster physischer Eindruck „schon nicht schlecht“.
Folgewunsch: Haken stärker aufploppen lassen und sofort langsam ausfaden.
Zeitangabe drei Minuten widerspricht den vorherigen drei Sekunden; Klärung
angefragt. Dauerabhängiger Folgepatch noch nicht implementiert. Separate aktuelle
Live-Prüfung und manuelle Speicherung des Hakens nicht bestätigt.

## Aktuelle Ergänzung: Zielkreis wie Ausrichtungshilfen einblenden — 2026-10-27

Vorbereitet: mittige Zielringschablone mit bestehendem `guides`-Faktor über
45→15 cm einblenden. Source-Navigationskreis und akzeptierte solide Zielfläche
ohne Trennstrich unverändert. 293 Offline-Tests bestanden, sieben optionale
GPU-Fälle übersprungen. In TD installiert, sieben GPU-Prüfgruppen bestanden;
separate aktive Live-Prüfung bestanden (Revision 3, `table_01`, drei Chairs,
Indizes 1/1/0/1). Physische Abnahme des Nähe-Fades und Speicherung offen.

## Abgenommener Standard: solide Zielfläche ohne Trennstrich — 2026-10-27

Johannes bestätigt direkten Vergleich ohne Trennstrich als deutlich besser und
legt diese Darstellung wieder als Standard fest. Repository-Shader entsprechend
gesetzt: solide weiße Zielgrundfläche ohne zusätzliche Rahmen-/Trennlinien,
ursprünglicher Footprint und übrige Motion-Grafik erhalten. Sieben neue
Schutz-/Übernahmetests bestanden; Motion-Suite 294 Fälle, 287 bestanden und sieben
optionale GPU-Fälle übersprungen. Laufende Vergleichsansicht noch per
`divider_compare.adopt_as_default(op)` übernehmen; separate abschließende
Live-Prüfausgabe und manuelle TD-Speicherung noch offen. Keine neue Aktivierung.

## Temporärer Direktvergleich ohne Trennlinie — 2026-10-27

Auf Johannes’ Wunsch reversiblen Ein-Befehl-Vergleich vorbereitet:
`compare_motion_target_divider.hide(op)`/`show(op)`. Nur `targetLines` auf null
setzen beziehungsweise vollständigen tatsächlichen Originalshader hash-gesichert
wiederherstellen; Shader-Grunddarstellung ansonsten unverändert. Eigener
COMP-Speicher, keine Layout-/Runtime-/Maskenänderung oder automatische Speicherung.
Kompilierung aller drei eigenen Renderer mit Fehler-Rücknahme und unveränderter
Engine/Reader/Revision geprüft. Offline nur Syntax/Text-Roundtrip bestätigt;
manueller TD-Aufruf und Sichtvergleich noch offen. Vor weiteren Shaderpatches
Vergleich zurücksetzen oder bewusst finalisieren.

## Aktueller letzter Linienversuch — 2026-10-27

Vorbereitet: Trennlinie wieder dünn (0,4 cm), auf Boden und Tabletop innen;
weißer Randstreifen weiter 2,5 cm, weißer Kern erhalten. Boden-Außenrahmen entfällt,
kein zusätzlicher Rahmen über ursprünglichen Tisch-Footprint hinaus.
280 Offline-Tests bestanden, sieben optionale GPU-Fälle übersprungen. In TD
installiert, fünf GPU-Prüfgruppen bestanden; separate aktive Live-Prüfung und
physische Abnahme offen, nichts gespeichert.

## Aktuelle gleiche Streifenbreiten und Verdeckungsbefund — 2026-10-27

Neue Grafik inzwischen installiert: acht TD-GPU-Prüfungen bestanden, alle
Streifen je 2,5 cm, Außenrahmen bei deckungsgleicher Source-Maske sichtbar,
Erfolg/Fade erhalten. Maximaler Muster-Floatfehler 8,147955e-05 an geglätteten
Kanten, maximal eine RGBA8-Stufe. Engine/Ziele/Masken unverändert. Freigaben
weiter aus; frischen Maskenabgleich, kontrollierte Freigabe für Revision 3 und
separate aktive/physische Prüfung noch durchführen. Nichts gespeichert.

Wiederaufnahme inzwischen ausgeschaltet geprüft: bewusste neue Input-Aktivierung
durch Johannes, Controller zeigt `table_01`/Revision 3/drei Chairs. Separater
`live_output.verify(op)`-Check passed, Session 2610399/Revision 3, Main/Chairs
Frame 69385, Rasterframe 69371. Originalmaske `rect_setup_mask_geo_00`, Kantenfehler
maximal 0,063567 cm, keine Pixel außerhalb Ein-Pixel-Grenze, Indizes weiter 0.
Erste noch alte Statusausgabe vor diesem Check nicht als aktuellen Zustand
verwenden. Keine Prozessneustarts oder automatischen ID-/Zieländerungen.
Neue Grafik jetzt bei gesperrter Ausgabe vorbereiten; Freigabe danach offen.

Johannes bestätigt nach Deaktivierung: Indizes 0, Motion frisch, Session 2610399/
Revision 2/Frame 65770, ID `table_00` valid=False. Neue Kamera-ID `table_01`
noch nicht explizit aktiviert. Bestehende Ziele bleiben dadurch geschützt.
Kontrollierte Wiederaufnahme erfordert bewusste neue Aktivierung (einmalig neue
Ziele/Chairs/Revision), danach ausgeschalteten Originalmaskenabgleich; keine
automatische ID-Umhängung oder Neustarts.

Rahmenstreifen und transparente Trennung auf Johannes’ Wunsch gleich breit wie
bestehende Ausrichtungshilfen: 2,5 cm. Weißer Kern bleibt; Bodenrahmen außen,
Tabletop-Rahmen innen. Offline vorbereitet, 274 Motion-Tests bestanden, sieben
optionale GPU-Fälle übersprungen. Noch nicht in TD installiert.
Nach gemeldeter Verdeckung laufen alle Backend-Prozesse weiter; aktuelle Szene
Frame 58531 mit `table_01` statt bisherigem `table_00`. Keine automatische
Neuberechnung/ID-Umhängung oder Neustarts. Freigaben/Stream-/Maskenzuordnung vor
nächstem Live-Grafiktest per manuellem Textport prüfen, nichts speichern.

## Aktuelle Präzisierung: 4-cm-Rahmenstreifen — 2026-10-27

Der letzte 0,3-cm-Linienentwurf ist verworfen: Johannes meint den weißen
Rahmenstreifen, nun 4 cm, auf Boden außen und auf Tabletop innen. Repository-
Oberflächenpatch gezielt zurückgenommen, vorheriger Einzel-Linienzustand
hergestellt; sieben fokussierte Tests bestanden. Tatsächlicher TD-Rollback noch
nicht bestätigt. Johannes bestätigt anschließend weiße Innenfläche mit feiner
Trennlinie. Korrigierter 4-cm-Patch vorbereitet: Bodenrahmen außen (0–4 cm),
Tabletop-Rahmen innen (0–4 cm), feine Linie wieder 0,6 cm. 268 Offline-Tests
bestanden, sieben optionale GPU-Fälle übersprungen. Noch nicht in TD installiert,
GPU-/Live-/physische Abnahme offen; keine automatische Speicherung.

## Aktueller Oberflächen-Linienentwurf — 2026-10-27

Vorbereitet: Linienbreite 0,3 cm; Bodenlinie 1 cm außerhalb ursprünglicher
Zielfläche, Tabletop-Linie weiter 10 cm innerhalb. Bestehende Masken/Erfolgslogik
unverändert. 260 Offline-Tests bestanden, sieben optionale GPU-Fälle übersprungen.
GPU soll besonders hypothetisch deckungsgleiche Source-/Zielposen prüfen;
TD-Einbau, aktive Live-Prüfung und physische Abnahme noch offen.

## Aktueller Einzel-Linien-Entwurf — 2026-10-27

Johannes bestätigt Drei-Linien-Installation `passed: true` und sichtbares Muster;
gestalterisch nun nur äußerste Linie gewünscht. Vorbereitet: Linie bei 10 cm
Randabstand auf 0,6 cm verschmälert, innere Linien entfernt. Weiße Füllung und
Rundung bleiben. 253 Offline-Tests bestanden, sieben optionale GPU-Fälle
übersprungen. Neuer Folgepatch noch nicht in TD installiert, GPU-/Live-/physische
Abnahme offen; nichts gespeichert.

## Aktueller Linienversuch — 2026-10-27

Rahmen durch weiße Füllung mit drei gerundeten transparenten Rechtecklinien
ablösen, gemäß Johannes’ neuer Referenz. Erstentwurf 10/20/30 cm innenliegend,
1 cm Breite, Ecken aller Linien kanonisch gerundet. Auf Boden und Tabletop.
245 Offline-Tests bestanden, sieben optionale GPU-Fälle übersprungen; neuer
Linienversuch noch nicht in TD installiert. GPU-/Live-/physische Abnahme offen.
Vorherigen Rahmen hat Johannes als sichtbar bestätigt, detaillierter GPU-Bericht
wurde nicht geliefert. Keine Speicherung.

## Aktueller Konturversuch — 2026-10-27

Zielfüllung auf Boden und Tabletop auf Johannes’ Wunsch als dicke Kontur
vorbereitet: 8 cm nach innen, äußerer Umriss unverändert, Außen-/Innenecken
abgerundet. Feedback bleibt im ursprünglichen Zielumriss; Zielschablone/-striche
im offenen Inneren weiß. 239 Offline-Tests bestanden, sieben optionale GPU-Fälle
übersprungen. Noch nicht in TD installiert: GPU-/Live-Prüfung und physische
Abnahme offen, nichts gespeichert.

## Wiederaufnahme — 2026-10-27

Alle sechs Backend-Komponenten auf Wunsch gestartet, keine Doppelinstanz;
TD bereits mit Startargument `AISI_v3.2_motion_lab_checkpoint_20261026.8.toe`
aktiv. Kamera-/Szenenstream schreitet mit `table_00` fort, HTTP 8080=200,
UDP 9000 bei TD. Kalibrierungshash unverändert; alte Kamera-JSONL vor Writer-
Neustart gesichert, großes temporäres OBB-Debuglogging nicht aktiviert.
Protokolle/Startargumente unter `data/aisi/debug/startup_20261027_074804/`.
Johannes hat neuen Vorschlag inzwischen explizit aktiviert. Ausgeschalteter
`live_output.verify(op)`-Nachweis passed: Session 2610399/Revision 2,
Main/Chairs Frame 2768, Rasterframe 2755, `table_00`, drei Chairs,
Originalmaske aktiv, alle Indizes 0. Kein Pixel außerhalb Ein-Pixel-Grenze;
maximaler Konturkantenfehler 0,0000216 cm, sechs doppelte Referenzen erhalten.
Kontrollierte Freigabe und separate aktive Prüfung anschließend bestanden:
Session 2610399/Revision 2, Main/Chairs Frame 7132, Rasterframe 7118, drei Chairs,
Indizes 1/1/0/1, Originalmaske aktiv, Konturkantenfehler 0 cm und keine Pixel
außerhalb Ein-Pixel-Grenze. Johannes bestätigt Motion-Grafik/drei Chairs sichtbar,
Source/Feedback folgen, Ziele/Chairs fest. Wiederanlauf abgeschlossen; kein
vollständiger neuer Raum-/Projektornachweis.
Tatsächlicher Dateiname per Textport noch nicht geliefert, nur Startargument bekannt.
Keine automatische TD-Speicherung, kein Bildschirmzugriff, kein neuer
physischer Projektionsnachweis. Git-Quellenstand `a9cb57a` unverändert.

## Aktueller Windows-Stand — 2026-10-26

Tagesabschluss: Johannes bestätigt die weiche Wiedereinblendung mit „passt“ und
beauftragt Sicherung/Push auf dem aktiven Branch `vision/wip-dark-proposals`.
TD speichert er manuell; finale Speicherdatei/erneutes Öffnen noch nicht bestätigt.
Letzte bestätigte Arbeitsdatei `AISI_v3.2_motion_lab_checkpoint_20261026.6.toe`.
Abschlussprüfung: 319 Tests bestanden, sieben optionale GPU-Fälle übersprungen.
Separate abschließende aktive Prüfausgabe nach letzter Runtimeänderung fehlt;
beim nächsten Start mit tatsächlichem Dateinamen und `live_output.verify(op)` erfassen.

Aktuell in TD installiert: weiche Wiedereinblendung über 0,35 s nach erfolgreicher
Einpassung und anschließendem Herausbewegen. Vorhandener Reaktivierungsübergang
bleibt, rein visuelle Ergänzung an Uploader/Shader; keine neue Reveal-Welle.
233 Offline-Tests bestanden, sieben optionale GPU-Fälle übersprungen.
Sechs TD-GPU-Prüfungen bestanden; physische Abnahme durch Johannes bestätigt,
separate abschließende aktive Prüfausgabe nicht geliefert. Speicherung manuell.

Aktuell in TD installiert: Source-Ausrichtungsstriche immer weiß, Zielstriche weiter
ausgespart; Halo-Radiuswachstum bei gleicher Annäherung etwas früher, mit
20 Prozent stärkerem Fortschrittsargument bei gleichen Anfangs-/Endradien.
223 Offline-Tests bestanden, sieben optionale GPU-Fälle übersprungen.
Vier TD-GPU-Prüfgruppen bestanden; separate aktive Live-Prüfung und physische
Abnahme noch offen, nichts gespeichert.

Aktuelle Nachjustierung installiert bestätigt: Schablonengröße bei 20 statt 8 cm erreichen,
Source-/Zielstriche später über 45→15 statt 65→25 cm einblenden. Zielring,
Pfeil und Erfolg unverändert. 218 Offline-Tests bestanden, sieben optionale
GPU-Fälle übersprungen. Installation durch Shader-/Sicherungsabgleich bestätigt;
detaillierter TD-GPU-Bericht nicht zurückgemeldet. Separate aktive Live-Prüfung
bestanden, früherer Größenabgleich und spätere Striche durch Johannes physisch
abgenommen. Timinganpassung abgeschlossen; Speicherung dieses Stands offen.

Aktuelle Präzisierung vorbereitet: Kreisgröße nur aus Distanz (65 → 8 cm),
Pfeil bleibt zum Zielmittelpunkt gerichtet und schrumpft innerhalb 12 cm auf null.
Keine Änderung der Erfolgslogik. 213 Offline-Tests bestanden, sieben optionale
GPU-Fälle übersprungen. In TD installiert, fünf GPU-Prüfgruppen bestanden;
separate aktive Live-Prüfung und physische Abnahme offen. Nichts gespeichert.

Neuer Versuch in TD installiert: halber Navigations-Mindestradius, mittige transparente
Zielringschablone und längsachsige Ausrichtungsstriche nach Johannes’ drei
Referenzbildern. Erfolg zieht Kreis nach innen auf null, Hilfen verschwinden.
208 Offline-Tests und neun Prüfungen auf der laufenden TD-GPU bestanden,
sieben optionale native GPU-Fälle übersprungen. Separate aktive Live-Prüfung
und physische Abnahme offen, nichts gespeichert.

Aktueller Auftrag: Feedbackgrün leicht aufhellen. Halo-Farbe RGB 0/236/101 →
0/255/110, etwa acht Prozent heller; Deckkraft/Verlauf/Zielbegrenzung und
Erfolgsfarbe unverändert. In TD installiert, sechs GPU-Vergleiche bestanden.
200 Offline-Tests bestanden, sieben optionale GPU-Fälle übersprungen.
Separate aktive Live-Prüfung und physische Sichtabnahme offen; nichts gespeichert.

Aktueller Auftrag: grünes Tabletop-Feedback auf weiße Zielfläche begrenzen.
Gezielter Shader-Patch im laufenden TD installiert, sechs GPU-Vergleiche
bestanden. Offline 192 Motion-Tests bestanden, sieben optionale GPU-Fälle
übersprungen. Separate aktive Live-Prüfung und physische Sichtabnahme durch
Johannes ebenfalls bestanden: Grün bleibt bei Bewegung/Drehung in der weißen
Zielfläche, Navigationskreis und Schatten passen. Anpassung abgeschlossen;
Speicherung noch nicht bestätigt.

5-cm-Tabletop-Rand vollständig zurückgenommen: Johannes bestätigt TD-Rollback
und vorherige Darstellung; Repository-Shader zurückgesetzt, eigene Inset-Helfer/
Tests entfernt. Nichts gespeichert, CV-Größenfilter erhalten. Neuer Auftrag:
Schlagschatten unter Navigationskreis im laufenden TD installiert, vier GPU-
Vergleiche bestanden; Kreisinneres/Boden unverändert, ohne Navigation/bei Erfolg
kein Schatten. Präzisierung: Schatten statisch mittig/rundum homogen statt versetzt;
radiale Fassung inzwischen installiert, fünf GPU-Vergleiche einschließlich
Rundumsymmetrie und Feedback-Unabhängigkeit bestanden. Separate aktive
Live-Prüfung ebenfalls bestanden; Johannes hat die radiale Fassung am realen
Tabletop mit „ist gut so“ gestalterisch abgenommen. Schattenanpassung
abgeschlossen, manuelle Speicherung durch Johannes bestätigt. Neuer vollständiger
Dateiname und erneutes Öffnen noch nicht bestätigt.

Jüngster Folgeblock CV abgeschlossen: kalibrierte Mindestkanten 140/70 cm,
64 Tests/Originalbild-Replay bestanden; unter aktiver Motion-Projektion in
400 Live-Auditframes jeweils zwei rohe OBBs, genau die Bodenkontur verworfen,
nur realer `table_00` weitergeführt. Aktuelle Session 2207576/Revision 2,
drei Chairs, Indizes 1/1/0/1, Originalmaske erneut geprüft. Die folgenden
Session-4463454-Befunde betreffen den früheren Ein-Tisch-Wiederöffnungstest.

Neue Arbeitsdatei `AISI_v3.2_motion_lab_checkpoint_20261026.toe` manuell
gespeichert; beide Live-Freigaben/Simulation aus und alle Indizes 0 geprüft.
Generator-/Chair-Simulation aller drei Formate bestanden; echte Ein-Tisch-
Input-Ausgabe mit zwei Chairs nach Runtime-Wiederherstellung und korrigierter
Reaktivierung durch Johannes bestätigt. Echte Quelle aktiv, Originalmaske
unverändert. Aktuelle Session 4463454, Revision 2, ID `table_00`.
UI-Freeze, Verdeckung/ID-Rückkehr und Live-Modusvergleich bestätigt.
Vier eingebettete Importzeilen auf Windows korrigiert; beide DATs kompilieren.
Jüngste Prüferfassung ausgeschaltet und aktiv in TD bestanden: Rasterframe
98951, Main/Chairs identisch frisch mit Frame 98966, Originalmaske erhalten.
Offline 175 Tests bestanden, sieben optionale GPU-Fälle übersprungen.
Jüngster Sichtbefund ebenfalls bestätigt: derselbe Vorschlag/zwei Chairs ohne
neue Welle, Source/Feedback folgen, Ziele/Chairs fest. Nächster Block:
Frischer TD-Start der gespeicherten Arbeitskopie mit ausgeschalteter Ausgabe
bestanden, anschließend denselben Vorschlag für die Sitzung freigegeben und
aktiv geprüft (Main/Chairs Frame 125442, Rasterframe 125426). Gespeicherter
Startzustand bleibt aus. Jüngster Sichtbefund nach Wiederöffnung bestätigt:
Motion-Grafik/zwei Chairs sichtbar, Source/Feedback folgen, Ziele/Chairs fest.
Ein-Tisch-Input-Inbetriebnahme abgeschlossen; nächster Block zwei reale Tische
bei zunächst ausgeschalteter Motion-Ausgabe. Gesamtruntime-Neustart und
Mehrtisch-Raumabnahme offen.
[Letzter Nachweis und Grenzen](#aktiver-nachweis-nach-pfad--und-prüferkorrektur--2026-10-26).
Die folgenden Abschnitte enthalten die historische Mac-Übergabe und die
chronologisch ergänzten Windows-Einzelbefunde; dieser Abschnitt ist die
aktuelle Kurzfassung.

Stand: 2026-10-26 (Git-Übergabe; letzte TD-Nachweise vom 2026-10-23). Auftrag: freigegebenes Remotion Motion Design v1.5 als eigene
Content-Komponente mit getrennten Floor-/Tabletop-Ausgängen umsetzen.
TouchDesigner läuft auf macOS. Johannes führt Textport-Befehle manuell aus;
kein Bildschirmzugriff. Keine automatische Projektspeicherung.

## Git-Übergabe an den Laborrechner — 2026-10-26

Übergabe-Branch: `codex/aisi-motion-td-handoff-20261026`, auf Basis von
`4d400b6` (`vision/wip-dark-proposals`). Enthalten sind ausschließlich
Motion-Implementierung, Prüfungen, die isolierte Autosave-Pfadoption des
Room Editors und zugehörige Dokumentation. Keine `.toe`-/`.tox`-Dateien,
Kalibrierungsdateien, lokalen Laufzeit-States, Vision-/Study-Daten oder
Debug-Artefakte. Andere lokale Arbeiten auf dem Mac bleiben uncommittet.

**Letzter nachgewiesener Stand:** Motion-Preview und Fünftisch-Simulation
visuell geprüft; 25 TD-Zustands-/Shaderkriterien bestanden. Reversibler Einbau
in die produktive Ausgabekette einschließlich Originalmaske installiert und
aktiv geprüft: sechs Kriterien bestanden, Tabletop maximaler Pixelfehler 0,0.
Johannes bestätigt die Tischdarstellung und vorhandene Bodenpfeile. Die
bisherige Chair-Quelle zeigte noch das alte Layout. Der neu implementierte
Generator-/Chair-Anschluss ist offline geprüft; seine anschließenden
Textport-Befehle wurden in diesem Chat noch nicht als ausgeführt bestätigt.
Kein Speicher-/Wiederöffnungsnachweis des Mac-TD-Projekts; der gebaute Graph
wird mit diesem Git-Push nicht übertragen. Der heutige Laufzustand von TD
wurde nicht untersucht.

**Fachlich fest:** Beim expliziten Aktivieren aus aktuellen Istposen berechnen,
anschließend Tischziele und Chairs gemeinsam festhalten. Bewegung und
UI-Einstellungsänderungen dürfen keine fortlaufende Neuberechnung auslösen.
Dies ist keine Abschaltung der quelladaptiven Berechnung beim Aktivieren.
Details unter D005a in `DECISIONS.md`.

**Vor Fortsetzung im Labor:**

1. `AGENTS.md`, aktuellen Git-/TD-Stand und diesen Abschnitt lesen. Den Motion-Branch gegen den tatsächlich aktiven Labor-Branch abgleichen; vorhandene lokale Laboränderungen erhalten. Der separat gepushte Labor-Branch `codex/lab-inbetriebnahme-20261021` (`cac6365`) ist hier nicht gemergt. Seine Änderungen an Laufzeitstatus, Source-Verfügbarkeit und Labor-Dokumentation dürfen beim Zusammenführen nicht verloren gehen.
2. Plattformpfade prüfen: TD-Helfer verwenden derzeit vielfach `/Users/Johannes/dev/Promotion_Prototypen/AISI`, der Simulator-Launcher `.venv/bin/python` und `/private/tmp`. Diese Mac-Befehle sind auf Windows noch nicht direkt ausführbar. Repository-/Python-/Temp-Pfade für den Laborrechner anpassen und die Syntax/gezielten Tests prüfen, bevor ein TD-Builder ausgeführt wird. Original-Master und Kalibrierung bleiben geschützt.
3. Tatsächlichen geöffneten TD-Graph lesend mit `inspect_motion_content.py`, `inspect_motion_live.py` und `inspect_motion_routing.py` prüfen. Komponenten werden nur bei passenden Voraussetzungen angelegt; vorhandene Namen oder abweichende Verdrahtung sind kein Auftrag zum Überschreiben. Die neue Chair-/Generator-Simulation setzt die zuvor aufgebauten eigenen Motion-/Masken-/Output-Komponenten voraus.
4. Danach den Generator-/Chair-Anschluss gemäß dem Abschnitt „Layout-Generierung einmal bei Aktivierung“ isoliert in TD prüfen. Echte Trackingdaten sind weiterhin nicht angeschlossen: `motion_live_adapter.py` ist ein geprüfter Zustandskern, kein aktiver Kamerasender. Stabile IDs, Paketaktualität, explizite Layoutaktivierung und Übereinstimmung mit den tatsächlichen Masken müssen vor produktiver Live-Freigabe zusammen geprüft werden.

Die `Sourceapproved`-Freigabe für echte Daten bleibt aus. Study-/Tracking-
Modusvergleiche und physische Projektor-/Raumabnahme bleiben gesondert offen.
Keine neue TD-Datei automatisch speichern. Der erste eigenständige
Labor-Schritt ist der Windows-Pfad-/Voraussetzungsabgleich der Motion-Helfer.

Erneute Git-Übergabeprüfung am 2026-10-26: Motion-Testauswahl mit 144 Fällen,
137 bestanden und sieben optionale native GPU-Fälle ohne konfigurierten
Runner übersprungen. Zusätzlich acht Room-Editor-Tests bestanden; Diff auf
Whitespacefehler geprüft. Die früheren nativen GPU-Nachweise sind oben bzw.
im jeweiligen Prüfblock getrennt dokumentiert; heute kein neuer TD-/Raumtest.

## Windows-Laborabgleich — 2026-10-26

Motion-Commit `0681604` wurde ohne Branchwechsel, Staging oder Commit per
konfliktgeprüftem Dreiwegeabgleich gegen Basis `4d400b6` in den aktiven
Labor-Worktree übernommen. Tatsächlicher Labor-HEAD: `0b08f4c` auf
`vision/wip-dark-proposals`; lokaler und Remote-Laborbranch zeigen auf
`9ae189f`, nicht mehr auf den historischen Übergabestand `cac6365`.
Laboränderungen an Source-Verfügbarkeit und Laufzeitstatus bleiben erhalten;
lokale Vision-Änderungen, Szenen, Kalibrierungs- und Debugdaten unberührt.
Git-Zugriff erfolgt außerhalb des Sandbox-Kontos ohne Änderung von
`safe.directory` oder Umgehung des Eigentümerschutzes.

Ausführbare Motion-Helfer verwenden jetzt den Windows-Repositorypfad.
Der Simulator startet mit `.venv/Scripts/python.exe` unter Windows und
verwendet das Betriebssystem-Tempverzeichnis statt `/private/tmp`.
Der Simulator bleibt separat und wird hierdurch noch nicht gestartet.
Historische Mac-Befehle unten dokumentieren frühere Prüfungen.

Offline auf Windows: 144 Motion-Fälle, davon 137 bestanden und sieben
optionale native GPU-Fälle ohne Runner übersprungen; sechs Laufzeitstatus-
und zwei Source-Verfügbarkeitstests bestanden. Das JSONL-Testfixture schreibt
explizite Bytes, damit sein Byteoffset unabhängig von Windows-Zeilenenden ist.
Kein neuer GPU-/TD-/Projektor-Nachweis. D005a bleibt verbindlich.

**Nächster erforderlicher Nachweis:** Johannes liest im TD-Textport die
geöffnete Datei und die vorhandenen Motion-/Routing-/Eingangskomponenten aus.
Vor diesem Abgleich keinen Builder oder Installer ausführen. Generator-/Chair-
Simulation zuerst; echte Quelle bleibt bis zu ID-/Aktualitäts-/Aktivierungs-
und Originalmaskenprüfung gesperrt. Keine TD-Datei verändert oder gespeichert.

### Erste Windows-TD-Inventur durch Johannes — 2026-10-26

Textport bestätigt die geöffnete Arbeitsdatei
`C:/Users/johan/OneDrive/Dokumente/AISI_DEV/touchdesigner/AISI_v3.1_preview_validated.toe`.
Ein wiederholter Importfehler in `motion_runtime` (Text DAT) meldete fehlendes
`td_builders`. Nach Ergänzung von Repository und `src` in `sys.path` bestätigt
Johannes den Import von `motion_geometry_compat.py` aus dem Windows-Repository.
Dies ist nur eine Sitzungskorrektur; Ende des Fehlerstroms und dauerhafte
Startfähigkeit sind noch nicht bestätigt. Keine Code-DATs überschrieben.

Die zurückgegebene lesende Routing-Inventur bestätigt bereits vorhandene
Motion-Einfügepunkte: Floor-Select referenziert den Motion-Ausgang;
Tabletop-Content geht über den Motion-Select vor `mask_tabletop` (Composite
TOP, Multiply). `null_table_mask` (Null TOP) erhält aktuell den Eingang vom
Simulationsmasken-Select. Die tatsächliche Wahl zwischen Original- und
Simulationsmaske innerhalb des Routing-COMPs ist noch auszulesen.
Die Chair-Komposition verwendet weiterhin `select_synth_chairs_regular`
(Select TOP), nicht den neuen Motion-Chair-Zweig. `study/mode = 2`;
die drei äußeren Kalibrierungs-Switches stehen auf Content (Index 0).
Dies belegt Struktur, keine fehlerfreie GPU-Ausgabe, Source-Freigabe oder
physische Maskenübereinstimmung. Nächster Schritt: vorhandene Motion-COMPs,
Freigabeparameter, interne Switches und gespeicherte Testregistrierung lesen;
keinen Builder erneut ausführen.

### Rückbauprüfung im Windows-Graph: Abweichungen offen

Johannes meldet bei `motion_output_simulation_test.validate` Abweichungen an
`item1` bis `item5` und deren Unterknoten. Die anschließend separat ausgegebene
Erfolgszeile ist kein Prüfnachweis. Kein Rückbau/Neuaufbau freigegeben; bestehende
Snapshots nicht neu setzen und Unterschiede nicht pauschal ausnehmen.
Gespeicherter `motion_sim_process` ist `None`. Motion-Content und Simulationsmaske
stehen auf Index 1, `Simulationtest=True`, `Enablemotion=False`,
`Sourceapproved=False`; Motion-Chair-COMP fehlt. Eingebetteter Runtime-Code
enthält weiterhin Mac-Pfade. `inspect_motion_registration.py` vergleicht
registrierte und aktuelle Signaturen rein lesend nach Feldern, um die Ursache
vor dem Generator-/Chair-Anschluss einzugrenzen. Kein TD-/Raum-Erfolgsnachweis.

### Leere Laufzeit-Replikation eingegrenzt — 2026-10-26

Johannes' Differenzbericht: 1290 registrierte geschützte Knoten, keine
Signaturänderung an vorhandenen Knoten; fehlend sind ausschließlich die
fünf `item1`–`item5`-Teilbäume. Alle 15 eigenen Routing-Signaturen stimmen.
Die folgende Textport-Inventur bestätigt `table/count=0` und
`replicate_tables` (Replicator COMP) mit `tables_active` (Script DAT),
`table_template` (Base COMP), `replicator_callbacks` (Text DAT),
Namensbildung `rowindex`. Das erklärt plausibel die entfernten Laufzeit-
instanzen; Tabelleninhalt und neue Validierung noch nicht live bestätigt.

Die Snapshot-Prüfung erlaubt nun ausschließlich diese fehlenden Instanzbäume,
wenn zusätzlich die aktuelle Tabelle nur den erwarteten Header enthält,
der Legacy-Count null ist, keine Tischinstanz existiert und alle registrierten
Rezept-/Template-/Callback-Signaturen unverändert sind. Vorhandene Knoten,
Masken und Instanzen werden weiterhin strikt geprüft; kein Rebaselining,
keine Erzeugung oder Änderung von Tischinstanzen. Sieben neue Regressionstests
prüfen Annahme und Ablehnung einschließlich Maskenänderung und fehlender
statischer Knoten. Gesamtauswahl: 151 Fälle, 144 bestanden, sieben optionale
GPU-Fälle übersprungen. Nächster Schritt: Module im TD neu laden und streng
validieren; nur bei Erfolg vorhandenen Vorbereitungshelfer verwenden.

### Generator-/Chair-Vorbereitung im Windows-TD bestanden — 2026-10-26

Johannes führt die nachgeladene Validierung und Vorbereitung erfolgreich aus:
Registrierung geprüft, alter Simulationstest kontrolliert beendet; drei
Pixel-Bypass-Prüfungen bestanden. `comp_aisi_motion_layout_chairs` (Container
COMP) neu isoliert angelegt, Shader im laufenden TD kompiliert. Fünftisch-
Simulator mit `generated_layouts=True` gestartet (PID zum Prüfzeitpunkt 35636),
Szene/Log unter `%TEMP%/aisi-motion-sim`. Empfang und sichtbares Fenster sind
durch diese Startmeldung noch nicht bestätigt.

Ausgabetest erfolgreich vorbereitet (`passed=True`,
`simulation_test_prepared=True`, `simulation_test_started=False`,
`active_in_current_mode=False`); nichts gespeichert. Damit ist die Installation
des Generator-/Chair-Anschlusses vorbereitet, noch keine aktive Abnahme.
Nächster Schritt: separate Aktivierung in einem späteren TD-Frame, anschließend
Input mit acht Teilnehmenden/100 Prozent/Chair-Opt-in explizit im Simulator
aktivieren, aktive Ausgabe prüfen und feste Ziele/Chairs bei Tischbewegung und
Einstellungsänderung bestätigen. Groupwork/Discussion danach einzeln prüfen.
Reale Quelle bleibt gesperrt; physische Validierung offen.

### Windows-Ausgabetest aktiviert, Vorschlagsabnahme noch offen

Johannes bestätigt nach separatem erneutem Aktivierungsaufruf:
`passed=True`, `simulation_test_started=True`, `active_in_current_mode=True`;
Floor, Tabletop, Simulationsmaske und Chairs jeweils Index 1. Stream frisch
(`receiving`, Session 1744786, Frame 3201, Layoutrevision 1). Die vorherige
Aktivierung blieb mangels bestätigtem Folgeframe korrekt deaktiviert; kein
Timeout verändert. IDs noch leer, da kein generierter Vorschlag aktiviert.
`real_source_approved=False`, nichts gespeichert, aktive Pixelprüfung und
physische Validierung noch nicht durchgeführt. Nächster Schritt: Input mit
acht Teilnehmenden/100 Prozent/Chair-Opt-in im Simulator explizit aktivieren,
danach `verify(op)` und feste Tischziele/Chairs bei Bewegung und geänderten
UI-Einstellungen prüfen. Dieser Befund bestätigt noch keine sichtbaren Chairs.

### Aktive Windows-Ausgabe mit acht Chairs technisch bestanden

Johannes liefert `verify(op)`: sieben Kriterien bestanden, Floor/Tabletop/
Simulationsmaske/Chairs jeweils Index 1. Chair-Stream frisch, acht sichtbare
Chairs, Layoutrevision 2; Tabletop-Maximalpixelfehler durch den bestehenden
Maskenoperator gegenüber dynamischem Simulationszweig 0,0. Echte Quelle nicht
freigegeben, nichts gespeichert; keine physische Validierung. Sichtbefunde
zu Bewegung, eingefrorenen Zielen/Chairs und Einstellungswechsel fehlen noch.

Der gleichzeitig gelieferte Screenshot der Learning-Format-Oberfläche meldet
einen Tisch und einen ungültigen Gruppenauftrag. Lesender Repositoryabgleich:
`learning_format_server` liest `layout_status.json` des bisherigen
`sim_scene_to_osc`-Senders; `motion_preview_sim` publiziert diesen Status nicht.
Die Statusdatei meldet tatsächlich einen verfügbaren Tisch und vier Gruppen.
Aktuelle Einstellungen beim lesenden Abgleich: Groupwork, acht Teilnehmende,
vier Gruppen, 100 Prozent, Chair-/Teilnehmenden-Opt-in an. Dies beweist nicht,
welche Einstellungen bei Revision 2 aktiviert wurden. Daher technische
Ausgabeprüfung verbuchen, aber noch keine Input-Einzelabnahme behaupten.
Für Motion gilt zunächst die Aktivierungsstatusmeldung im eigenen Room Editor.
Labor-Statusdatei und Oberfläche nicht verändert.

### Input-Einzelprüfung der Windows-Motion-Simulation bestanden

Johannes bestätigt Input explizit im laufenden Simulator: Source und Feedback
folgen Bewegung/Rotation; Tischziele und Chairs bleiben fest. Änderung der
Teilnehmerzahl von acht auf neun ohne erneute Aktivierung erhält denselben
Vorschlag. Anschließendes `verify(op)` besteht alle sieben Kriterien;
Floor/Tabletop/Maske/Chairs jeweils Index 1, frischer Chair-Stream mit acht
Chairs, Session 1744786, Layoutrevision 3, Frame 18784. Tabletop-Maximalpixelfehler
0,0. Dies bestätigt D005a für diese Input-Stichprobe einschließlich
Einstellungsänderung; keine vollständige Count-/Teilnehmendenmatrix.

Echte Quelle bleibt gesperrt, nichts gespeichert, keine physische Raum- oder
Projektorvalidierung. Nächste Einzelprüfung: Groupwork, acht Teilnehmende,
zwei Gruppen, 100 Prozent und Chairs an; explizit aktivieren, danach Bewegung
und Einstellungsänderung ohne Klick prüfen. Discussion, erneute erfolgreiche
Aktivierung, Fehlererhalt sowie Modus-/Trackinganschlussprüfungen bleiben offen.

### Groupwork-Einzelprüfung der Windows-Motion-Simulation bestanden

Johannes bestätigt Groupwork nach der vorgegebenen Einzelprüfung mit acht
Teilnehmenden/zwei Gruppen: Source und Feedback folgen, Tischziele und Chairs
bleiben bei Bewegung/Rotation fest. Änderung auf drei Gruppen ohne erneute
Aktivierung erhält den Vorschlag. `verify(op)` besteht alle sieben Kriterien;
Floor/Tabletop/Maske/Chairs jeweils Index 1, frischer Chair-Stream mit acht
Chairs, Session 1744786, Layoutrevision 4, Frame 22127. Tabletop-Pixelfehler
0,0. D005a damit für diese Groupwork-Stichprobe bestätigt. Nächste Einzelprüfung:
Discussion mit acht Teilnehmenden; UI-Änderung auf neun ohne Klick muss den
Vorschlag erhalten. Echte Quelle weiter gesperrt, nichts gespeichert, keine
physische Validierung. Keine vollständige Gruppen-/Countmatrix behaupten.

### Discussion-Einzelprüfung der Windows-Motion-Simulation bestanden

Johannes bestätigt auch Discussion nach dem vorgegebenen Test mit acht
Teilnehmenden: Source/Feedback folgen Bewegung, Ziele und Chairs bleiben
fest, einschließlich Einstellungsänderung ohne Aktivierung. Sieben aktive
TD-Ausgabeprüfungen bestanden; Floor/Tabletop/Maske/Chairs jeweils Index 1,
frischer Stream mit acht Chairs, Session 1744786, Revision 5, Frame 25339.
Tabletop-Pixelfehler 0,0, echte Quelle gesperrt, nichts gespeichert, keine
physische Validierung. Damit sind Input, Groupwork und Discussion jeweils
für diese Fünftisch-Stichproben auf D005a geprüft.

Offen vor Übergang zur echten Quelle: erneute erfolgreiche Aktivierung mit
vollständiger neuer Chair-/Zielmenge und genau einer Reveal-Welle, Fehlererhalt
bei ungültiger Anfrage, kurzer gemeinsamer Format-/Modusvergleich. Nächster
Test: Discussion neun Personen explizit aktivieren, danach 16 als ungültigen
Auftrag aktivieren und Erhalt von Revision, Zielen und neun Chairs prüfen.

### Neuaktivierung und Fehlererhalt durch Johannes bestätigt

Discussion neun Personen: neun Chairs, genau eine neue Reveal-Welle,
Layoutrevision 6. `verify(op)` besteht sieben Kriterien, alle vier Indizes 1,
Chair-Stream frisch (Session 1744786, Frame 28130), Pixelfehler 0,0.
Ungültiger Auftrag mit 16 Personen meldet einen Fehler und erhält laut Johannes
Ziele, neun Chairs und Revision 6. Screenshot zeigt den separaten Legacy-UI-
Status; Fehlererhalt im Motion-Simulator ist durch Johannes' Sichtbefund belegt.
Keine zweite vollständige Prüfausgabe für den Fehlerfall geliefert. Nichts
gespeichert, echte Quelle weiter gesperrt, keine physische Validierung.

Lesende Kamera-Vorprobe danach: 27 neue FrameEvents in zwei Sekunden,
`fresh=True`, `ready_for_mapping_check=True`, beobachtete ID `table_00`,
Kalibrierungskennung `calibration`, letzter Frame 29512. Kein Layout aktiviert,
keine Netzwerkpakete gesendet; weder stabile Wiedererkennung noch TD-
Maskenübereinstimmung dadurch nachgewiesen.

Lesende Windows-Prozessinventur identifiziert echte Doppelketten zusätzlich
zu normalen venv-Eltern-/Kindpaaren: Legacy-Sender 21596→7328 mit Freshness-
und Study-Bindings sowie 25856→9104 ohne diese Optionen; Scene-Adapter
2560→18036 (Poll 0,01 s) und 2292→19104 (Default), jeweils dieselbe
`vision_live_scene.json`. Kamera 33732→2688, Motion-Simulator 35636→35760,
Study-Control 1808→26448. PIDs sind nur Momentaufnahme, vor Eingriff neu prüfen.
Keine Prozesse beendet oder neu gestartet. Doppelbelegung vor echter
Motion-Freigabe konsolidieren; geschützte Source-/Laufzeitstatusfunktionen und
Study-/Tracking-Modi erhalten. Nächster manueller Test: kurze Modusfolge
AISI→Tracking→Study (ohne Sessionstart)→AISI; gemeinsame vier Zweige und
Rückkehr prüfen. Danach Doppelketten/echte ID- und Maskenzuordnung bearbeiten.

### Technischer Modusvergleich und Laufzeitkonsolidierung bestätigt

Johannes liefert drei erfolgreiche `verify(op)`-Ausgaben: Tracking (`mode=0`)
und Study (`mode=1`) wählen Floor/Tabletop/Maske/Chairs jeweils Index 0;
AISI (`mode=2`) jeweils Index 1. Echte Quelle bleibt in allen Fällen gesperrt.
Dies ist ein technischer Modusnachweis; ein zusätzlicher visueller Vergleich
der bisherigen Modi wurde mit diesen Ausgaben nicht ausdrücklich bestätigt.

Erneute Prozessinventur bestätigt die zusätzlichen, am 2026-10-26 gestarteten
Doppelketten. Nach Identitäts-/Parent-/Argumentprüfung und Sicherung ihrer
Startargumente unter `data/aisi/debug/motion_runtime_consolidation_20261026_100857/`
wurden ausschließlich 25856→9104 (zusätzlicher OSC-Sender ohne Schutzoptionen)
und 2292→19104 (zusätzlicher Scene-Adapter) beendet. Unmittelbare Nachprüfung:
genau eine jeweilige Labor-Prozesskette verbleibt, 21596→7328 mit Freshness-
und Study-Bindings sowie 2560→18036 mit Poll 0,01 s. Kamera, Study-Control,
Motion-Simulator und Benutzerdateien nicht geändert. Kein neuer Sender gestartet.

Für den tatsächlichen Maskenabgleich ist `inspect_motion_mask_alignment.py`
lesend ergänzt: ausgewertete Original-Maskengeometrien mit Transformationen,
Sichtbarkeit und Parenting sowie aktuelle `/vision/table/*`-Werte. Keine
Kalibrierungs- oder Maskenparameter schreiben. Syntax für TD-Python 3.9 geprüft.
Nächster Schritt: Johannes führt diese Abfrage im noch unveränderten Graph aus.
Simulation nicht zurückbauen, echte Quelle noch nicht anschließen/freigeben.

### Originalmasken ausgelesen; echter Live-Zustandskern offline ergänzt

Johannes' Textport-Bericht zeigt den tatsächlichen Original-Maskenrenderer:
`render_table_mask` (Render TOP), 2000², Kamera `cam1` (Camera COMP), ortho,
Breite 2,6, Position (0,0,5), keine Rotation. Geometrieliste enthält dieselben
sechs `rect_setup_mask_geo_00`–`05` (Geometry COMP) doppelt; unverändert lassen.
Aktiv ist ausschließlich Slot 0 (`sx=1`), Slots 1–5 haben `sx=0`.
`vision/table/count=1`, dagegen `table/count=2` mit zwei älteren Zielslots;
aufbewahrte höhere Vision-Kanäle/`available=1` sind keine aktuelle Belegung.
Tisch-/Source-Slots nicht löschen oder als aktuelle Kamera-ID-Liste verwenden.

Slot 0 bestätigt bei Weltpose (401,7687378;100,1079712;90,2619553°):
`tx=-0,7891974365`, `ty=-0,7794385498`, `rz=-90,2619553°`;
Ausdrücke `tx=(250-world_x)*0.0052`, `ty=(world_y-250)*0.0052`,
`rz=-world_r`. Die einzige neue Live-Content-Grenze komponiert diese tatsächlich
beobachtete Abbildung mit vorhandenem `motion_design.td_pose`: Content-Pose
(500-world_x;500-world_y;world_r). Rect-Ausrichtung ist axial. Chairs und Ziele
werden an derselben Grenze umgesetzt; Weltgenerator/-tracking bleibt unverändert.
Maskengeometrie, Kamera, Homographien und Projektorpfade werden nicht angepasst.

Implementierung `src/aisi/app/motion_live_control.py`: neuer expliziter
Live-Controller auf Basis von `MotionLiveAdapter`, keine Fixture-Ziele,
öffentliche frische Source-Kopie für Klickberechnung; Worker nur bei Klick,
vollständiger Ziel-/Chair-Commit nach Aktualitäts-/ID-Mengenprüfung. Bewegung
und UI-Änderungen erzeugen keine Aufträge. Fehler/Bestandswechsel erhalten
vorigen Vorschlag. Direkte Kameraframes statt 15-Frame-Retentionscache;
fehlende IDs bleiben ungültig unter ihrer ursprünglichen Ziel-ID, kein Ersatz.
Bei Kamera-Timeout werden Sources ungültig und Chairs unsichtbar, auch wenn
Transportframes weiterlaufen. `--send` ist explizites Opt-in; Standard startet
nur lokale Bedienung ohne OSC. Kein TD-Installer und keine Source-Freigabe.
Ein sendender Start verwendet denselben `/aisi_motion/`-Namensraum wie der
Simulator und darf erst nach dessen kontrolliertem Ende bei deaktiviertem
TD-Ausgabetest erfolgen. Echte Ausgabefreigabe weiterhin separat erforderlich.

Neun neue Tests bestanden: Content-/Maskenabbildung, frische Source-Kopien,
Start ohne Ziele, feste Ziele/Chairs, Timeout, ID-Verlust/-Wechsel, atomarer
Fehlererhalt, Reaktivierung/OSC-Chair-Zusammenhang und echter Input-Generator
mit einem Tisch/zwei Personen. Gesamtauswahl 160 Fälle: 153 bestanden,
sieben optionale GPU-Fälle übersprungen. Zusätzliche netzwerkfreie Kameraprobe:
28 neue Frames, ID `table_00`, Input mit zwei Personen ergibt einen Tisch
und zwei Chairs, lokale Revision 2; kein Paket gesendet, kein TD-Anschluss.
Diese lokale Revision ist nicht die aktuelle TD-Simulationsrevision 6.

Nächster manueller Schritt: registrierten Test validieren, ausschließlich
`Simulationtest=False` setzen und Rückfall auf vier Legacy-Zweige prüfen.
Testregistrierung vorerst behalten; nicht aufbauen/stoppen/neu baselinen.
Erst nach Bestätigung Simulator-Prozess kontrolliert beenden und echten
Sender ohne produktive Freigabe starten; danach aktuelle Source-ID-/Pose-
und Pixelübereinstimmung mit Originalmaske prüfen. Dieser aktive Echtquellen-
vergleich sowie die eigentliche Live-Umschaltung sind noch nicht erfolgt.
Nichts gespeichert, keine physische Validierung.

### Geschützter Wechsel vom Simulator zum echten Kamera-Controller

Johannes bestätigt nach `Simulationtest=False` den erfolgreichen Rückfall:
Floor/Tabletop/Maske/Chairs jeweils Index 0, echte Quelle nicht freigegeben.
Die vorhandene Testregistrierung wurde erhalten. Nach erneuter Prozess-
Identitätsprüfung wurden nur Simulator 35636→35760 beendet und dessen
Startargumente unter `data/aisi/debug/motion_live_control_20261026_102349/`
gesichert. Kamera-/Scene-/Legacy-Sender-/Study-Control-Ketten bleiben erhalten.
Neuer Controller `.venv/Scripts/python.exe -u -m aisi.app.motion_live_control
--send`, PID zum Start 31400, gestartet. Prozess läuft, Fehlerlog leer; sichtbares
Fenster und erfolgreiche Live-Aktivierung müssen noch von Johannes bestätigt
werden. Der Controller sendet ausschließlich `/aisi_motion/*`; kein eigener
Empfänger und keine Freigabe-/Graphänderung. Framegebundene Kamera-Metadaten
`camera/fresh`, `camera/session`, `camera/frame` ergänzt.

`check_motion_live_masks.py` ist ein gesperrter Vergleich: verlangt alle drei
Freigaben aus, unveränderte Testregistrierung, frischen fortschreitenden
Motion-Stream und zum Paket passende frische Kamerametadaten. Vergleicht
aktuelle gültige Sources unter ihren Kamera-IDs mit eindeutigen aktiven
Originalmasken innerhalb der bisherigen Ein-Pixel-Kantenabweichung. Alte
Masken-Slots mit `sx=0` werden nicht als aktuelle Belegung gezählt. Zusätzlich
Originalmaskenbild gegen kopierten Source-Maskenprüfzweig: keine hellen Flächen
außerhalb des gegenseitigen Ein-Pixel-Rands; nichtleere, endliche, gleichgroße
RGBA-Bilder erforderlich. Rohe maximale Pixelabweichung separat ausgeben;
keine Pixelgleichheit oder physische Abnahme allein aus Rasterassoziation.
Doppelte Original-Geometriereferenzen bleiben erhalten. Der Legacy-Masken-
OSC enthält selbst keine stabilen IDs; der Nachweis ist eindeutige aktuelle
Posekorrespondenz mit dem direkten Kamera-ID-Stream. Keine automatische
`Sourceapproved`-Freigabe und keine Knoten-/Parameteränderung durch den Prüfer.

Vier neue Maskentests sowie 25 bestehende Live-Adapter-/Controller-Tests
bestanden (29 insgesamt). TD-Python-3.9-Syntax des Prüfers geprüft. Nächster
manueller Schritt: Input mit zwei Teilnehmenden, 100 Prozent, Opt-in und Chairs
an wählen; im neuen Kamera-Controller explizit aktivieren. Dann bei ruhigem
realem Tisch den geschützten Maskenprüfer im TD-Textport ausführen; bei
unbestätigtem ersten Frame später erneut lesen. Bis zur erfolgreichen
aktuellen Prüfung bleibt die Ausgabe aus. Keine TD-Speicherung oder
physische Validierung erfolgt.

### Aktueller Echtquellen-Maskenabgleich in Windows-TD bestanden

Johannes bestätigt Kamera-Controller: `receiving`, Frame 52100, ID `table_00`,
Input, Revision 2, zwei Chairs. Erster TD-Aufruf wartete erwartungsgemäß auf
einen Folgeframe. Zweiter Aufruf besteht: frischer Motion-Stream Session
4715980/Frame 4827/Revision 2, eindeutige Zuordnung zu
`rect_setup_mask_geo_00` (Geometry COMP), maximale Kantenabweichung
0,0131607105 cm. Original-/Kopiermasken haben 204586/204591 helle Pixel;
keine Abweichung außerhalb des Ein-Pixel-Rands, rohe maximale RGBA-Abweichung
0,2549019754. Somit Rasterassoziation bestanden, ausdrücklich keine
Pixelgleichheit. Sechs doppelte Geometriereferenzen erhalten. Keine Ausgabe
verändert/freigegeben, nichts gespeichert; keine physische Validierung.

Reversible Live-Umschaltung `td_builders/motion_live_output.py` offline ergänzt:
Vorbereitung verlangt alle drei Freigaben aus und erfolgreichen aktuellen
Maskenvergleich, wärmt den isolierten Chair-Reader und prüft drei Bypassbilder.
Ändert ausschließlich den bekannten eigenen `simulation_chairs_switch`
(Switch TOP) von Simulations- auf gemeinsames Content-Gatter. Vorhandene
Floor-/Tabletop-Gatter bleiben erhalten, Simulationsmasken-Gatter bleibt aus;
Originalmaskenbild bleibt produktiv. Ursprüngliche Testregistrierung unverändert
als Rückfall behalten, eigene Live-Registrierung separat speichern. Keine
Code-DATs/Masken/Projektorparameter ersetzen; kein Engine-Reset/keine Speicherung.

Separate Aktivierung in späterem TD-Frame verlangt weiterlaufende Kamera-
Frames derselben Session, unveränderte Vorschlagsrevision/ID-Menge und neue
numerische Maskenkorrespondenz. Erst dann Sourceapproved/Enablemotion setzen.
Erwartet in AISI: Floor/Tabletop/Chairs 1, Simulationsmaske 0. Study/Tracking/
Kalibrierung behalten alte Quellen. Separate `live_output.verify(op)` prüft
aktuelle Rasterassoziation, unverändertes Routing, tatsächlichen produktiven
Originalmaskeneingang und frischen Chair-Stream derselben Revision/Signatur
samt vollständiger sichtbarer Chair-Menge. Bei Prüffehler beide Live-Flags aus;
keine fremde Verdrahtung zurückschreiben. `live_output.rollback(op)` nimmt nur
die eigene Chair-Ausdrucksänderung zurück, Flags aus, ursprüngliche
Testregistrierung bleibt erhalten. Nach Vorbereitung nicht mehr den alten
`motion_test.verify` verwenden, sondern den Live-Prüfer.

Zwölf neue Live-Ausgabetests bestanden; gesamte Motion-Auswahl 176 Fälle,
169 bestanden und sieben optionale GPU-Fälle übersprungen. Noch keine
Installation/Aktivierung der Live-Erweiterung in TD bestätigt. Nächster
manueller Schritt: Maskenprüfmodul nachladen, `motion_live_output.prepare(op)`
ausführen und Ergebnis liefern; weiterhin keine Ausgabe freigeben/speichern.

### Live-Vorbereitung im laufenden Windows-TD bestanden

Johannes liefert `live_output.prepare(op)`: `passed=True`,
`live_prepared=True`, drei Bypass-Pixelprüfungen bestanden,
`original_mask_selected=True`, `source_approved=False`, `enabled=False`,
Vorbereitungsframe 316658. Nichts gespeichert. Damit ist die gezielte eigene
Chair-Gatteränderung in TD installiert; beide produktiven Freigaben bleiben aus.
Nächster Schritt: `live_output.activate(op)` als neue Textport-Eingabe bei
ruhigem Tisch; danach in separater Eingabe `live_output.verify(op)`. Aktivierung,
aktive Ausgabe und physische Raumprüfung noch nicht bestätigt. Ursprüngliche
Testregistrierung erhalten; ab jetzt Live-Prüfer statt `motion_test.verify`.

### Echte Motion-Quelle aktiv und technisch in TD verifiziert

Johannes liefert `live_output.activate(op)` und anschließendes
`live_output.verify(op)` mit `passed=True`. Sourceapproved an; Floor/Tabletop/
Chairs jeweils Index 1, Simulationsmaske Index 0, Originalmaske ausgewählt.
Frischer direkter Kamera-Stream mit `table_00`, Session 4715980, Revision 2;
Aktivierungsframe des Streams 21459, anschließende Prüfung Frame 22052.
Chair-Stream frisch, identische Session/Frame/Revision, zwei sichtbare Chairs.
Originalmasken-Zuordnung weiterhin eindeutig, Kantenfehler 0,0388204606 cm;
Rasterassoziation innerhalb eines Pixels bestanden, kein Pixel außerhalb
des gegenseitigen Ein-Pixel-Rands. Original-/Kopiermaske 204572/204574 helle
Pixel, rohe RGBA-Maximalabweichung 0,2549019754. Sechs doppelte Original-
Geometriereferenzen erhalten. Keine Pixelgleichheit behaupten.

Die Prüfung hat keine Ausgänge umverdrahtet; eigene Live-Erweiterung aktiv,
Original-Testregistrierung für Rücknahme erhalten. Kein automatisches Speichern,
keine physische Raum-/Projektorvalidierung aus diesem technischen Bericht.
Nächster manueller Schritt: realen Tisch kurz verschieben/drehen, Source- und
Feedbacknachführung sowie feste Ziele/Chairs prüfen, anschließend UI-Zahl
2→3 ohne Aktivierung und kurze Verdeckung/Rückkehr samt Kamera-ID beobachten.
Den strengen Rasterprüfer erst wieder bei ruhigem, erneut erkanntem Tisch
aufrufen. Bei neuer statt alter ID keine automatische Neuzuordnung erwarten.
Live-Mehr-/Fünftischprüfung, Jitter-/Leistungsabnahme und erneuter Modusvergleich
mit echter Quelle bleiben offen. Eingebettete Mac-Importpfade sind bisher nur
in dieser TD-Sitzung über `sys.path` kompensiert; dauerhafter Startpfad ist vor
einer späteren manuellen Sicherung noch gezielt zu korrigieren. Masterdatei
unberührt.

### Physischer Befund: nur Chairs, Tisch-Content fehlt

Johannes meldet nach technischer Live-Freigabe: Auf dem realen Tisch keine
Einblendung, insgesamt nur zwei Chair-Kreise sichtbar. Damit ist die physische
Live-Ausgabe nicht bestanden; die vorherigen technischen Masken-/Routing-
Prüfungen belegen noch keinen sichtbaren Tisch-Content. Kein Bewegungs-/Freeze-
oder Verdeckungsnachweis am realen Tisch aus diesem Befund ableiten.

Nächster Schritt ist `inspect_motion_live_content.inspect(op)`: liest aktuellen
Source-/Target-/Aktiv-/Phasenstatus und RGB-Belegung entlang Motion-Renderer,
produktiver Select-Quellen, Originalmaskierung und äußerer Layer-Schalter.
Kocht vorhandene Operatoren für den Befund, verändert keine Parameter/Knoten,
setzt keine Engine zurück und speichert nichts. Prüft insbesondere tatsächliche
Select-Referenzen statt sie aus Buildern anzunehmen. Ursache noch offen;
keine Korrektur an Kalibrierung/Masken oder Generierungsregeln auf Verdacht.
TD-Python-3.9-Syntax des neuen lesenden Helfers geprüft.

### Fehlender Tisch-Content auf bereits erreichtem Ziel eingegrenzt

Johannes' lesender Content-Bericht zeigt die korrekten tatsächlichen Select-
Quellen auf die Haupt-Motion-Ausgänge; sämtliche Floor-/Tabletop-Stufen schon
vor der Maske transparent, keine Shaderfehler, äußere Layer eingeschaltet.
Direkte Kameraquelle frisch. Source und eingefrorenes Ziel unterscheiden sich
nur um 0,01047 cm, Winkeldifferenz rund 0,089°; Phase `completed`, Kontakt wahr.
Das quelladaptive Ein-Tisch-Input hat die vorhandene Pose als gültiges Ziel
beibehalten. Am erreichten Ziel ist die ausgeblendete Tischführung nach
Dissolve erwartetes Design; die beiden Chairs bleiben sichtbar.

Zusätzlicher Anschlussfehler erkannt: Live-Controller leitete `active=False`
aus bereits erfüllter Ankunftstoleranz beim Klick ab. Dadurch blieb selbst
nach späterem Verlassen der unveränderten Zielpose die Shader-Führung gesperrt,
obwohl die Motion-Zustandsmaschine reaktivieren kann. Korrigiert ausschließlich
im neuen `MotionLiveSession.commit`: Alle explizit generierten Tischziele
bleiben führungsberechtigt; Ankunft ist eine reversible Phase, kein inaktiver
Layout-Rollenstatus. Keine Veränderung an Generatorzielen, Chairs, Masken,
Shadern, Koordinaten oder Study-/Tracking-Baseline. Bestehende Schwellen
unverändert: Reaktivierung bei mehr als 18 cm oder mehr als 12° Abweichung von
der gespeicherten Erfolgspose, keine neue Layoutrevision/Reveal-Welle.

Neue Regression durchläuft Ankunft→Dissolve→Completed→25-cm-Abgang und prüft
Rückkehr zu Guidance bei unveränderten Zielen, Chairs, Revision und Reveal-
Startzeit. Gesamte Motion-Auswahl 177 Fälle: 170 bestanden, sieben optionale
GPU-Fälle übersprungen. Korrektur noch nicht im laufenden Controller geladen.
Identifizierte zugehörige Prozesskette zum Nachladen: 31400→33060, beide exakt
`-u -m aisi.app.motion_live_control --send`; vor Eingriff erneut prüfen.
Nächster manueller Schritt: `live_output.rollback(op)` (Flags aus, nur eigene
Chair-Gatteränderung zurück); danach ausschließlich Kamera-Controller neu
starten und Vorschlag aus aktueller Pose einmal explizit aktivieren. Danach
Masken-/Live-Vorbereitung und separate Aktivierung erneut prüfen. Physischer
Test anschließend mindestens 25 cm Bewegung ohne erneuten Klick; am Ziel im
Stillstand weiterhin keine dauerhafte Tischführung erwarten. Nichts gespeichert.

### Rückbau und Controller-Neustart für Reaktivierungskorrektur bestätigt

Johannes bestätigt `live_output.rollback(op)`: erfolgreich, beide Live-Flags
aus, Floor/Tabletop/Simulationsmaske/Chairs jeweils 0; ursprüngliche
Testregistrierung erhalten, nichts gespeichert. Nach erneuter Identitätsprüfung
nur Kamera-Controller 31400→33060 beendet und mit korrigiertem Live-Commit
neu gestartet. Neuer Start-PID 23452, Protokolle/gesicherte vorherige Argumente
unter `data/aisi/debug/motion_live_reactivation_20261026_110241/`. Prozess läuft,
Fehlerlog leer. Kamera, Scene-Adapter, Legacy-Sender, Study-Control und TD-
Graph nicht neu gestartet. Korrektur nun im neuen Controllerprozess geladen;
noch keine neue explizite Aktivierung oder Ausgabeprüfung durch Johannes.
Nächster Schritt: Input 2 bei ruhigem Tisch explizit im neuen Controller
aktivieren; Live-Vorbereitung, separate Aktivierung und Verifikation wiederholen.
Erst danach Tisch 25–30 cm bewegen, ohne erneuten Aktivierungsklick; Guidance
muss nach Completed zurückkehren und Ziel-/Chairpositionen fest bleiben.
Im Stillstand auf dem bereits erreichten Ziel bleibt ausgeblendete Führung
weiterhin erwartetes Verhalten. Keine physische Bestätigung der Korrektur bisher.

### Korrigierter Controller technisch aktiv; anschließender Prozessverlust

Johannes bestätigt nach Neustart erneut Vorbereitung (drei Bypass-Prüfungen,
TD-Frame 405079), Aktivierung und Verifikation erfolgreich. Neue Motion-Session
2778202, Revision 2, ID `table_00`, zwei frische Chairs. Aktivierungsframe 4172,
Verifikationsframe 4245; Floor/Tabletop/Chairs 1, Simulationsmaske 0,
Originalmaske aktiv. Kantenfehler rund 0,0000108 cm, jeweils 204596 helle Masken-
Pixel, kein Pixel außerhalb des Ein-Pixel-Rands; rohe RGBA-Abweichung weiter
0,2549019754, keine Pixelgleichheit. Sichtbare Reaktivierung nach Bewegung
wurde in dieser Ausgabe noch nicht bestätigt.

Anschließend meldet Johannes vollständig leere physische Ausgabe. Lesende
Prozessinventur bestätigt: Motion-Controller, Scene-Adapter und Legacy-OSC-
Sender laufen nicht mehr. Kamera 33732→2688, TD 30044 mit unveränderter
`AISI_v3.1_preview_validated.toe`, Study-Control 1808→26448 und Lernformat-
Server 30420→24492 laufen weiter. Kamera-Datei zuletzt 11:16:57 aktualisiert,
Live-Szene zuletzt 11:14:07, Legacy-Status 11:14:06. Neues Controller-Fehlerlog
leer. Prozessende nicht erklärt; keine Kalibrierungsursache daraus ableiten.
Ohne neuen Motion-Sender läuft der bestehende Aktualitäts-Timeout ab und
Content wird transparent. Nichts automatisch neu gestartet oder freigegeben.

Nächster manueller Schritt: ausschließlich Enablemotion und Sourceapproved
auf False setzen, vier Zweige auslesen; vorhandene Live-/Testregistrierung
behalten. Danach fehlenden Scene-Adapter und Legacy-Sender mit den zuvor
gesicherten Schutzoptionen sowie Kamera-Controller gezielt wiederherstellen,
keinen zweiten Kameraprozess/Study-Control/Lernformat-Server starten. Echte
Ausgabe erst nach erneuter aktuellen Prüfung aktivieren. Physischer Befund
weiter offen, nichts gespeichert.

### Fehlende Laufzeitketten nach bestätigtem Bypass wiederhergestellt

Johannes bestätigt nach Enablemotion/Sourceapproved=False alle vier Indizes 0;
bestehende Live-/Testregistrierungen bleiben erhalten. Erneute Prozessinventur
vor Wiederherstellung: keine Motion-/Scene-/Legacy-Kette vorhanden, kein
Doppelstart. Nur fehlenden Scene-Adapter mit `--poll-seconds 0.01` gestartet
(1280→26468), neue aktuelle Scene-Datei nachgewiesen. Anschließend Legacy-Sender
mit bisherigen `--require-fresh-live-scene` und beiden Study-Bindings gestartet
(36888→16552) sowie korrigierten Kamera-Controller (27172→37920). Kamera,
TD, Study-Control und Lernformat-Server unverändert weiterverwendet.

Protokolle unter `data/aisi/debug/motion_recovery_20261026_112559/`;
alle drei Fehlerlogs leer. Legacy meldet Input, einen Tisch, zwei Chairs,
fortschreitende Source-Posen. Lesende Kameraprobe: 28 neue Frames in zwei
Sekunden, frisch, `table_00`, zuletzt Frame 104655. Kein Motion-Vorschlag
automatisch aktiviert; Ausgabe weiterhin per manuell bestätigtem Bypass aus.
Die Ursache des vorherigen Prozessendes ist nicht geklärt.

Nächster manueller Schritt: neuer Kamera-Controller einmal Input 2 aktivieren.
Vorherige eigene Live-Erweiterung mit `live_output.rollback(op)` sauber
zurücknehmen, dann `live_output.prepare(op)` neu ausführen; ursprüngliche
Testregistrierung erhalten. Bei Wartebefund nur prepare später wiederholen.
Erst nach bestandenem neuen Maskenvergleich separat aktivieren und reale
25–30-cm-Bewegung ohne neuen Klick prüfen. Alte Sourceapproved-Freigabe nicht
blind übernehmen. Keine physische Abnahme und keine TD-Speicherung erfolgt.

## Reale Reaktivierung nach Runtime-Wiederherstellung bestätigt

Johannes meldet nach erfolgreicher erneuter Aktivierung und Verifikation
„jetzt funktioniert es“ im Kontext des angefragten realen 25–30-cm-
Bewegungstests ohne erneuten Aktivierungsklick. Damit ist die korrigierte
Guidance-Reaktivierung für diese Ein-Tisch-Input-Stichprobe bestätigt.
Keinen zusätzlichen Verdeckungs-/UI-/Mehrtisch-Nachweis daraus ableiten.

Letzte Ausgaben: `activate` und `verify` passed, Session 4463454, Revision 2,
ID `table_00`. Aktivierungsframe 18541, Verifikationsframe 21075; zwei Chairs
mit identischer frischer Session/Frame/Revision. Floor/Tabletop/Chairs 1,
Simulationsmaske 0, Originalmaske aktiv. Kantenabweichung 0,0000152588 cm,
beide Masken 204570 helle Pixel, kein Pixel außerhalb des Ein-Pixel-Rands.
Rohe RGBA-Abweichung 0,2549019754; keine Pixelgleichheit. Sechs doppelte
Geometriereferenzen unverändert. Keine automatische Speicherung/kein Commit.

Die vorherige Mengenabweichung war ein noch nicht aktivierter Motion-Vorschlag:
frischer Stream mit Count 0/Revision 1 gegenüber einem aktiven Originalmasken-
Slot. Erst expliziter Klick im eigenen Kamera-Controller, nicht „Neu generieren“
im Format-Browser, lieferte Revision 2 und zwei Chairs. Keine Maskenänderung
als Korrektur erforderlich; Schutz hat Freigabe leerer Vorschläge verhindert.

Nächster Block am realen Tisch: Teilnehmerzahl 2→3 ohne Aktivierung, feste
Ziel-/Chairmenge beobachten; dann kurze Verdeckung/Rückkehr, vor/nachher
Kamera-ID `table_00` beobachten und veraltete Source-/Feedbackanzeige prüfen.
Strengen Rasterprüfer erst nach Rückkehr bei ruhigem erkanntem Tisch ausführen.
Bei neuer ID keine automatische Ziel-Neuzuordnung oder Neuberechnung
behaupten, noch nicht neu aktivieren. Danach kurzer Tracking/Study/AISI-
Modusvergleich mit echter Quelle. Startup-Importpfade vor späterer manueller
Sicherung korrigieren; weiter kein Wiederöffnungs-/Windows-Neustartnachweis.

## Reale UI-Fixierung und ID-Rückkehr bestätigt — 2026-10-26

Johannes bestätigt am realen Input-Tisch: Änderung von zwei auf drei
Teilnehmende ohne erneute Aktivierung erhält Ziel und zwei Chairs. Nach kurzer
Verdeckung kehrt `table_00` zurück. Die Anzeige während der Verdeckung wurde
nicht separat beschrieben; daraus keinen vollständigen Timeout-Nachweis ableiten.

Anschließend `live_output.verify(op)` bestanden: Session 4463454, Revision 2,
Frame 28623; Source und zwei Chairs identisch frisch gebunden. Floor/Tabletop/
Chairs bleiben 1, Simulationsmaske 0, Originalmaske aktiv. Kantenabweichung
0,0090214424 cm, keine Pixel außerhalb des Ein-Pixel-Rands; Original/Kopie
204350/204355 helle Pixel, rohe RGBA-Abweichung 0,2549019754. Sechs doppelte
Maskenreferenzen erhalten. Kein Speichern oder Commit.

Nächster Schritt ist der Tracking-/Study-/AISI-Modusvergleich mit echter Quelle,
ohne Study-Trialstart und ohne neue Layoutaktivierung. Mehrtischprüfung,
Wiederanlauf und umfassende physische Projektionsabnahme bleiben offen.

## Modusvergleich mit echter Kameraquelle bestätigt — 2026-10-26

Johannes bestätigt Tracking/Study mit allen vier Ausgabeschaltern auf 0 und
AISI mit Floor/Tabletop/Simulationsmaske/Chairs auf 1/1/0/1. Nach Rückkehr
bleiben dieselben Ziele und zwei Chairs erhalten, ohne neue Reveal-Welle.
Damit ist der gemeinsame Modusschalter auch für die echte Ein-Tisch-Quelle
im laufenden TD geprüft. Daraus folgt keine vollständige Study-Trialabnahme.

Als Nächstes die eingebetteten Mac-Importpfade im tatsächlichen Graph lesend
erfassen und nur die nachgewiesenen Pfadzeilen reversibel korrigieren. Keine
Builder-Neuinstallation, keine neue Layoutaktivierung und keine automatische
Speicherung. Wiederöffnungs-/Neustartnachweis und Mehrtisch-Raumprüfung offen.

## Eingebettete Windows-Importpfade: Lesebefund — 2026-10-26

Textport-Inventur durch Johannes: Nur `motion_runtime` in
`comp_aisi_motion_v1_5` und `comp_aisi_motion_aligned_snapshot` enthält noch
die Mac-Importpfade, jeweils Zeilen 2 und 3. Keine weiteren Treffer für
`/Users/`, `/private/tmp`, `.venv/bin` oder `sys.path` in den untersuchten
Motion-DATs. Die Reihenfolge von Repo und src ist zwischen beiden DATs
unterschiedlich und bleibt erhalten.

Vorbereitete Korrektur ersetzt ausschließlich den alten Repo-Präfix in diesen
vier Zeilen, mit vollständiger Sicherung der bisherigen DAT-Texte im Textport
und Syntaxprüfung vor dem Schreiben. Keine Implementierung aus dem Repository
neu einbetten, keine Engine-/Reader-Storagewerte löschen und keine Registrierungen
neu erfassen. Die Schutz-Snapshots des Ausgaberoutings umfassen die beiden
Motion-Runtime-DATs nicht; sie bleiben unverändert. Ausführung, Kompilierung,
nachgelagerte Live-Prüfung und Wiederöffnungsnachweis noch offen.

## Windows-Pfadkorrektur kompiliert, Chair-Verifikation offen — 2026-10-26

Johannes hat die vier Importzeilen geändert; beide `motion_runtime`-DATs
kompilieren und exportieren `td_tick`. Bisherige Texte sind in der Textport-
Variable `motion_import_backup` gesichert. Keine automatische Speicherung.

Die separate Prüfung scheitert in `live_output.verify` am Vergleich des
Chair-Status mit dem Main-Stream: frisch sowie identische Layout-/Framebindung
nicht gemeinsam erfüllt. Welcher Teil abweicht, ist aus der Fehlermeldung
nicht bestimmbar. Der Fehlerpfad schaltet `Enablemotion` und `Sourceapproved`
aus; kein automatisches Wiederfreigeben. Als Nächstes beide gespeicherten
Statuswerte sowie Fehler und gezieltes Cook-Verhalten erfassen. Keine
Ursachenbehauptung oder Änderung an Timeout, Registrierung oder Verdrahtung.

## Cook-Reihenfolge der Live-Prüfung korrigiert — 2026-10-26

Textport-Diagnose: beide Freigaben aus; Main frisch, Chairs veraltet mit
derselben Session 4463454, Revision 2 und Frame 44789. Explizites Cooken von
Main-State und Chair-State liefert beide frisch mit Frame 46280 und zwei
Chairs, ohne Knotenfehler. Kein Hinweis auf eine geänderte Layoutrevision.

`motion_live_output.verify` führte GPU-Rücklesen vor dem Statusvergleich aus;
Cooken des Chair-Out-TOP erzwingt keinen frischen Cook des gecachten Script TOP.
Der Prüfer erfasst daher nach allen GPU-Prüfungen erneut die frische Kamera
und cookt Chair-State ausdrücklich. Layout und IDs müssen zum vorigen
Rastervergleich passen, Main und Chairs weiterhin exakt dieselbe aktuelle
Framebindung besitzen. Pixelvergleichsframe wird separat als
`mask_pixel_signature` ausgegeben. Keine Timeoutverlängerung, Änderung der
DAT-Texte, Registrierung, Verdrahtung oder automatische Wiederfreigabe.

14 fokussierte Offline-Tests bestanden, darunter simuliertes Altern des
Chair-Status während GPU-Arbeit, Neu-Cook danach sowie Ablehnung geänderter/
veralteter Quellen und abweichender Chair-Frames. Neue Prüferfassung muss
im Textport geladen und zuerst bei ausgeschalteten Freigaben geprüft werden.
Keine TD-Speicherung, kein Wiederöffnungsnachweis.

## Korrigierter Live-Prüfer im ausgeschalteten Zustand bestätigt — 2026-10-26

Nach `importlib.reload(live_output)` bestätigt Johannes `verify` passed:
Sourceapproved false, alle vier Indizes 0; Originalmaske aktiv. Main und
zwei Chairs frisch mit Session 4463454, Revision 2 und Frame 48966.
Die separat ausgewiesene Rasterprobe stammt aus Frame 48950: Original/Kopie
je 204285 helle Pixel, keine Pixel außerhalb des Ein-Pixel-Rands, rohe
RGBA-Abweichung 0,2549019754. Aktueller Posevergleich: 0,0000215792 cm.
Sechs doppelte Maskenreferenzen erhalten. 18 fokussierte Offline-Tests bestehen.

Nächster Schritt: erneute Prüfung bei ausgeschalteten Freigaben, anschließend
ausschließlich beide bestehenden Freigabeschalter setzen. Keine neue
Vorschlagsaktivierung, keine Änderung von Engine, Revision oder Verdrahtung.
Danach separater aktiver Prüflauf und Sichtbefund. Kein Speichern oder Commit;
Wiederöffnungsnachweis bleibt offen.

## Aktive Nachprüfung: Pose-/Originalmaskenzuordnung erneut gesperrt — 2026-10-26

Nach erfolgreicher ausgeschalteter Prüfung wurden nur beide Live-Freigaben
gesetzt; Indizes 1/1/0/1 bestätigt. Die separate aktive Prüfung scheitert
jedoch im zweiten `current_sources` nach GPU-Rücklesen mit
„Keine eindeutige rastergenaue Originalmaske für table_00“. Der Fehlerpfad
setzt beide Freigaben wieder auf false. Keine erfolgreiche aktive Abnahme
der jüngsten Prüferfassung behaupten.

Ob eine zeitliche Abweichung zwischen den zwei unabhängigen Senderpfaden,
ein innerhalb desselben TD-Frames gecachter Transform oder eine reale
Poseabweichung vorliegt, ist noch offen. Als Nächstes aktuelle Reader-Posen,
Originalmaskentransforms und deren tatsächliche Parameterbindungen gemeinsam
erfassen. Keine Toleranzvergrößerung, Transformkorrektur oder automatische
Wiederfreigabe. Windows-Pfadkorrekturen bleiben erhalten; nichts gespeichert.

## Poseabweichung konkret erfasst — 2026-10-26

Johannes liefert gespeicherten Main-Status Session 4463454/Revision 2,
Frame 55823 mit Source `(122.2117462, 337.4647522, -118.0601959)`.
Aktive Originalmaske: `(122.8179932, 337.1897736, -117.7530212)`;
deren Parameter entsprechen exakt den beobachteten `vision/table/0/*`-
Kanälen und den bestehenden Transformationen. Etwa 0,67 cm Translation und
0,31 Grad axiale Winkeldifferenz überschreiten die Ein-Pixel-Assoziation.

Lesende Repository-/Prozessprüfung: genau eine Adapter-, Legacy-Sender- und
Motion-Controller-Kette; beide Quellen verwenden dieselbe `_tables_from_frame`-
Konvertierung, aber unabhängige Poll-/Senderpfade. Szenendatei und Kamera-JSONL
schreiben weiter, Adapter-/Legacy-Stderr leer. Der gespeicherte Main-Status
ist ohne Cook keine aktuelle Erfassungsprobe; daraus keine dauerhafte
Senderabweichung oder Kalibrierungsursache ableiten. Nächster Befund: explizite
gemeinsame Aktualisierung ohne GPU-Rücklesen und Maskenpose vor/nach Geo-Cook
vergleichen. Freigaben bleiben aus, Originalmasken unverändert.

## Gemeinsame Poseprobe und getrennte Prüferfassungen — 2026-10-26

Explizite Aktualisierung ohne GPU-Rücklesen liefert Main frisch mit Session
4463454/Revision 2, Frame 76073 und Source
`(122.8179779, 337.1897583, -117.7297134)`. Originalmaske vor und nach Geo-Cook
identisch `(122.8179932, 337.1897736, -117.7299805)`, keine Knotenfehler.
Winkeldifferenz etwa 0,000267 Grad, keine dauerhafte Transformabweichung in
dieser Probe. Unterschiedliche Erfassungszeitpunkte bleiben die Arbeitshypothese
für den früheren Befund; ein Geo-Cachefehler allein ist damit nicht bewiesen.

Neueste Korrektur: `current_sources` behält den strengen Pose-/Originalmasken-
Vergleich vor GPU-Arbeit; `current_stream` erfasst danach nur die aktuelle
Kameraquelle. Kein zweiter Vergleich neuer Posen mit Maskengeometrie aus einem
früheren Prüfstand. Ergebnis behält `source_mask_matches` und Rasterbeleg mit
`mask_pixel_signature`; Main-/Chair-Framebindung wird danach separat exakt
geprüft. Layout und IDs müssen zum ursprünglichen Maskenbeleg passen; fehlende
oder ungültige Sources, veraltete/ungebundene Kameradaten und abweichende Chairs
bleiben Sperrgründe. Die Quelle muss beim manuellen Rastertest stillstehen;
dies ist weiterhin keine Garantie kontinuierlicher Synchronität beider Sender.

Offline: 182 Motion-Fälle, 175 bestanden und sieben optionale GPU-Fälle
übersprungen; 21 fokussierte Prüfertests bestehen. Neue Tests prüfen, dass
die Nach-GPU-Erfassung keine Maskengeometrie liest, Kamerabindung und Source-
Validität strikt bleiben und der ursprüngliche Posebeleg erhalten wird.
Beide Helfer in TD neu laden; aktive Abnahme noch offen. Keine Verdrahtungs-,
Kalibrierungs- oder Timeoutänderung, kein Speichern/Commit.

## Getrennte Prüferfassungen ausgeschaltet in TD bestanden — 2026-10-26

Johannes hat `check_motion_live_masks` und `motion_live_output` neu geladen.
Anschließendes `verify` bestanden: Session 4463454/Revision 2, ID `table_00`,
Main und zwei Chairs identisch frisch mit Frame 96715; Maskenbeleg Frame
96699, Kantenfehler 0,0000215792 cm. Original/Kopie je 204286 helle Pixel,
keine Pixel außerhalb des Ein-Pixel-Rands, rohe RGBA-Abweichung 0,2549019754.
Sechs doppelte Referenzen erhalten. Beide Freigaben aus, alle vier Indizes 0.

Als Nächstes nach erneuter erfolgreicher ausgeschalteter Prüfung ausschließlich
die bestehenden Freigaben setzen, dieselbe Session/Revision erhalten und
separat aktiv verifizieren. Aktive Prüfung dieser neuesten Fassung, Sichtbefund
und Wiederöffnungsnachweis noch offen. Kein Speichern oder Commit.

## Aktiver Nachweis nach Pfad- und Prüferkorrektur — 2026-10-26

Johannes bestätigt erneute Freigabe mit Indizes 1/1/0/1 und separate aktive
`verify`-Prüfung passed: Session 4463454/Revision 2, ID `table_00`, Main und
zwei Chairs identisch frisch mit Frame 98966. Originalmaske aktiv. Pose- und
Rasterbeleg Frame 98951: Kantenfehler 0,0000076294 cm, Original/Kopie je
204291 helle Pixel, keine Pixel außerhalb des Ein-Pixel-Rands; rohe RGBA-
Abweichung 0,2549019754. Sechs doppelte Maskenreferenzen erhalten.

Keine neue Layoutaktivierung und keine Speicherung. Jüngster Sichtbefund
zu festen Zielen/zwei Chairs und ausbleibender Reveal-Welle noch nicht
mitgeliefert; frühere physische Ein-Tisch-Prüfung separat bestätigt. Nach
Sichtbestätigung Startfähigkeit und manuelle Sicherung vorbereiten;
Wiederöffnungs-, Windows-Neustart- und Mehrtisch-Raumnachweis offen.

## Sichtabnahme nach Pfad-/Prüferkorrektur bestätigt — 2026-10-26

Johannes bestätigt denselben sichtbaren Vorschlag und zwei Chairs, keine neue
Reveal-Welle. Source und Feedback folgen der Tischbewegung, Ziele und Chairs
bleiben fest. Damit sind jüngste technische aktive Prüfung und physische
Ein-Tisch-Input-Sichtprobe getrennt belegt. Keine allgemeine Mehrtisch- oder
Projektorabnahme daraus ableiten.

Vor manueller Sicherung bleibt zu prüfen, ob weitere eingebettete Module
Repository-Imports ohne eigenen Pfad-Bootstrap enthalten. Insbesondere der
Repository-Chair-Runtimecode importiert `td_builders` direkt; aus dem Builder
allein folgt kein Nachweis der Startreihenfolge im tatsächlichen Graph.
Eine neue Sitzung besitzt den manuell ergänzten globalen `sys.path` nicht.
Daher tatsächliche DAT-Importheader lesend erfassen, anschließend gezielt
Startfähigkeit absichern. Keine automatische Speicherung oder Änderung der
physischen Masterdatei, kein Commit.

## Eigenständiger Chair-Import vorbereitet — 2026-10-26

Tatsächliche DAT-Inventur durch Johannes: ausschließlich
`comp_aisi_motion_layout_chairs/chair_runtime` importiert `td_builders` ohne
eigenen `sys.path`-Bootstrap. Repository-Builder ergänzt diesen nun für neue
Chair-Komponenten; bestehende Komponenten werden nicht neu gebaut.

Für den bestehenden DAT nur drei Bootstrap-Zeilen voranstellen, bisherigen
Text unverändert erhalten. Zuvor vollständige `chair_owned`-Registrierung
streng prüfen und Text/Registrierung sichern; danach ausschließlich den
Hash dieses einen DAT-Texts im eigenen Chair-Nachweis fortschreiben.
Keine neue Erfassung anderer Parameter oder Verbindungen, keine Änderung
der Ausgaberouting-Registrierungen. Bei Abweichung keine Änderung durchführen.

Offline: sechs Chair-Testfälle, drei bestanden und drei optionale GPU-Fälle
übersprungen. Generierter Runtime-Text zusätzlich mit Windows-Venv-Python
unter `-I -S` ohne vorgegebenen Repo-Importpfad ausgeführt: `td_tick` ladbar.
TD-Installation und Prüfung stehen noch aus; dies ist kein vollständiger
TD-Wiederöffnungsnachweis. Kein Speichern oder Commit.

## Chair-Bootstrap installiert, manuelle Sicherung vorbereitet — 2026-10-26

Johannes bestätigt Installation: bisherige `chair_owned`-Registrierung streng
geprüft, drei Bootstrapzeilen vorangestellt, Modul kompiliert und ausschließlich
Hash dieses DAT-Texts fortgeschrieben. Text und alte Registrierung im Textport
als `chair_import_backup` gesichert. Aktive Live-Prüfung danach bestanden:
Session 4463454/Revision 2, Main und zwei Chairs identisch frisch mit Frame
108829; Pose-/Rasterbeleg Frame 108813, Kantenfehler 0,0094368052 cm,
Original/Kopie 204295/204298 helle Pixel, kein Pixel außerhalb des Ein-Pixel-
Rands, rohe RGBA-Abweichung 0,4980392158. Indizes 1/1/0/1, Originalmaske aktiv,
sechs doppelte Referenzen erhalten. Kein neuer Vorschlag aktiviert.

Als Nächstes beide Live-Freigaben und Simulation ausschalten und ausgeschaltete
Ausgabe verifizieren. Danach ausschließlich manuelles Save As einer neuen
Arbeitskopie `AISI_v3.2_motion_lab_checkpoint_20261026.toe` im bisherigen
TouchDesigner-Ordner; Datei war bei Vorbereitung nicht vorhanden. Bei
Überschreibungsdialog abbrechen. Weder Masterdatei noch bisherige Arbeitsdatei
überschreiben. Speicherung und frischer TD-Start noch nicht nachgewiesen;
Kamera und Sender während des späteren TD-Neustarts weiterlaufen lassen,
keine zweite Controller-/Senderinstanz starten. Kein automatisches Speichern.

## Neue Arbeitskopie manuell gespeichert — 2026-10-26

Johannes bestätigt ausgeschalteten Sicherungszustand: `verify` passed,
Enablemotion/Sourceapproved/Simulationtest false, alle vier Indizes 0.
Nach manuellem Save As meldet WORKFILE
`C:/Users/johan/OneDrive/Dokumente/AISI_DEV/touchdesigner/AISI_v3.2_motion_lab_checkpoint_20261026.toe`.
Datei lesend auf Datenträger bestätigt: 2187326 Bytes, 2026-10-26 13:23:03
lokal. Dies bestätigt die Sicherung, noch keinen Wiederöffnungs-/Neustarttest.

Als Nächstes ausschließlich TD vollständig beenden und diese neue Datei in
einem frischen TD-Prozess öffnen. Kamera, Adapter und beide bestehenden
Sender/Controller weiterlaufen lassen; keine zusätzlichen Instanzen starten.
Zunächst Module/State-Cooks ohne manuelle sys.path-Ergänzung prüfen, Flags und
Indizes müssen aus bleiben. In späterem TD-Frame Quelle/Originalmaske erneut
mit `live_output.verify` prüfen. Keine automatische Freigabe oder neue
Layoutaktivierung. Masterdatei bleibt geschützt, kein Commit.

## Frischer TD-Start der neuen Arbeitskopie bestanden — 2026-10-26

Johannes bestätigt WORKFILE der neuen Arbeitskopie, beide State-Cooks ohne
Fehler, Repository-Import ohne manuelle sys.path-Ergänzung und alle drei
Freigaben false sowie alle vier Indizes 0. Prozessinventur bestätigt einen
frischen TD-Prozess: PID 2352, Start 13:27:44 lokal, neue Datei als Argument.

Separate ausgeschaltete Live-Prüfung bestanden: Session 4463454/Revision 2,
ID `table_00`, Main und zwei Chairs identisch frisch mit Frame 123453.
Maskenbeleg Frame 123438, Kantenfehler 0,0000076294 cm; Original/Kopie je
204284 helle Pixel, keine Pixel außerhalb des Ein-Pixel-Rands, rohe RGBA-
Abweichung 0,2549019754. Originalmaske und sechs doppelte Referenzen erhalten.
Kamera, Adapter und Sender liefen während des TD-Neustarts weiter. Damit
kein Windows-/Gesamtruntime-Neustartnachweis.

Alte grafische Inhalte bei Indizes 0 sind der vorhandene Legacy-/Study-Pfad;
dieser Zustand ist beabsichtigt und wurde so gespeichert. Als Nächstes nach
erneuter Prüfung den vorhandenen Vorschlag für diese Sitzung wieder freigeben,
separat aktiv prüfen und Sichtbefund bestätigen. Keine neue Layoutaktivierung
und keine erneute Speicherung. Mehrtisch-Raumabnahme bleibt offen.

## Aktive technische Prüfung nach frischem TD-Start bestanden — 2026-10-26

Nach erneuter ausgeschalteter Prüfung hat Johannes nur die bestehenden
Live-Freigaben gesetzt. Indizes 1/1/0/1, separate aktive `verify`-Prüfung
passed: Session 4463454/Revision 2, ID `table_00`, Main und zwei Chairs
identisch frisch mit Frame 125442. Originalmaske aktiv, sechs doppelte
Referenzen erhalten. Pose-/Rasterbeleg Frame 125426: Kantenfehler 0 cm,
Original/Kopie je 204275 helle Pixel, kein Pixel außerhalb des Ein-Pixel-
Rands. Rohe RGBA-Abweichung 0,2549019754, daher keine Pixelgleichheit.

Technischer Wiederöffnungstest mit weiterlaufender Kamera-/Sender-Runtime
damit ausgeschaltet und aktiv bestanden. Kein neuer Vorschlag aktiviert und
nicht erneut gespeichert; die Arbeitskopie behält den ausgeschalteten
Startzustand. Sichtbefund nach diesem frischen TD-Start wurde mit den
letzten Ausgaben noch nicht mitgeliefert und bleibt separat zu bestätigen.
Frühere physische Ein-Tisch-Input-Sichtprobe bleibt dokumentiert; keine
allgemeine Mehrtisch-/Projektorabnahme oder Windows-Neustartprüfung.

## Ein-Tisch-Input-Inbetriebnahme einschließlich Wiederöffnung abgeschlossen — 2026-10-26

Johannes bestätigt nach dem frischen TD-Start auch den Sichtbefund: Motion-
Grafik und zwei Chairs sichtbar; Source und Feedback folgen der Bewegung,
Ziele und Chairs bleiben fest. Zusammen mit aktiver technischer Prüfung,
manueller neuer Arbeitskopie und ausgeschaltetem Startzustand ist dieser
Ein-Tisch-Input-Block abgeschlossen. Keine erneute Speicherung und kein Commit.

Nachweise getrennt: offline 175 Motion-Tests bestanden, sieben optionale
GPU-Fälle übersprungen; laufendes TD vor/nach frischem Start mit Originalmaske
geprüft; physisch eine reale Ein-Tisch-Input-Stichprobe. Mehrtisch-Raumprüfung,
vollständiger Windows-/Runtime-Neustart und umfassende Projektorabnahme offen.

Nächster unabhängiger Block: Motion zuerst deaktivieren, dann zweiten realen
Tisch erfassen. Beobachtete getrennte stabile IDs und zwei Originalmasken
nachweisen, bevor ein neuer Vorschlag explizit aktiviert und die erweiterte
Quelle erneut freigegeben wird. Alte Ein-Tisch-Freigabe nicht fortschreiben.
Bei zwei Masken und noch altem Ein-Tisch-Vorschlag ist eine Mengenabweichung
zu erwarten; nicht durch Maskenänderung oder Toleranzanpassung umgehen.

## CV-Folgeauftrag: projizierte Bodenziele durch Größenprüfung ausschließen — 2026-10-26

Johannes priorisiert CV-Ausschluss der kleineren Bodenziele vor grafischen
Änderungen und Zweitischprüfung. Lokaler Originalframe 260943 per bestehendem
c-Hotkey erfasst, ohne Bildschirmzugriff. Offline-Inferenz mit produktivem
Rect-OBB-Modell, Levels 200 und unveränderter Kalibrierung: realer Tisch
164,684×82,959 cm, projizierter Zielumriss 128,392×66,061 cm. Konfidenzen
0,956/0,929; ein Konfidenzfilter allein wäre ungeeignet. Vorhandene Minima
125/55 cm ließen die Projektion durch.

Nur Mindestkanten des bestehenden kalibrierten Rect-Größenfilters auf
140/70 cm gesetzt (87,5 Prozent der nominalen 160/80 cm); Maxima 200/110 cm
unverändert. Filter liegt vor Assoziation und Track-Erzeugung. Vorhandene
lokale Vision-/Tracking-Änderungen erhalten; kein zusätzlicher Pixel-/Ortfilter,
keine Änderung an Homographien oder TD-Ausgabe. Regressionsfälle für gemessene
Boden-/Tischmaße und unabhängige inklusive Mindestkanten ergänzt.

Offline: 64 Tests zu Zuordnung, OBB-Rotation, Kalibrierung und Preprocessing
bestanden. Vollständiger CPU-Replay des Originalbilds über drei Frames erzeugt
nach Bestätigung nur realen `table_00` und führt ihn regulär weiter; genau
eine Größenablehnung bei zwei rohen OBBs pro Frame. Artefakte unversioniert
unter `data/vision/debug/motion_floor_size_filter_20261026/`.

Deployment noch offen: laufende Kamera lädt Konstanten erst nach Neustart.
Zuvor TD-Motion deaktivieren, aktive Prozessargumente sichern und aktuelle
Kamera-JSONL vor Writer-Trunkierung kopieren. Kamera-Framezähler/Trackzustand
beginnen neu; Motion-Adapter darf Rollbackschutz nicht umgehen. Controller
anschließend bewusst neu initialisieren, neue Vorschlagsaktivierung nur
explizit, Quelle/Originalmasken neu prüfen. Keine alte Freigabe übernehmen.
Live-Nachweis und Prüfung echter Tische bei Rotation/kurzer Verdeckung stehen
aus; Offline-Erfolg gilt für diese Aufnahme. Kein Commit und keine TD-Speicherung.

## CV-Größenfilter kontrolliert in laufende Runtime übernommen — 2026-10-26

Johannes bestätigt TD-Bypass 0/0/0/0. Unmittelbar vor Prozesswechsel exakte
Argumente, Startzeiten und Parent/Child-Zuordnung geprüft und gesichert;
nur alte CV-Kette 33732→2688 und Motion-Controller 27172→37920 gestoppt.
Kamera-JSONL anschließend vor neuem Writer unverändert kopiert (127230619
Bytes). Sicherung/Protokolle:
`data/aisi/debug/cv_floor_filter_restart_20261026_142506/`.

Neue Kamera-Kette 16524→5348 mit ursprünglichen Argumenten und zusätzlichem
lokalem OBB-Audit-JSONL gestartet, neuer Controller 39368→25636 mit originalen
Argumenten. Stderr beider Ketten leer. Scene-Adapter 1280→26468 und Legacy-
Sender 36888→16552 weitergeführt; deren vorhandene Truncate-Behandlung liest
neue Frames. Kamera-/Szenenframe 314→329 innerhalb einer Sekunde, nur realer
`table_00`. TD, Kalibrierung und Study-/Formatsteuerung unverändert.

Controller bewusst noch ohne Vorschlag, TD-Ausgabe weiterhin aus. Aktuelle
UI-Einstellungen Input/drei Teilnehmende; neue explizite Aktivierung darf drei
Chairs liefern. Nach Benutzerklick erst Quelle/Originalmaske ausgeschaltet neu
prüfen, danach aktuelle Session freigeben. Prüfung bei bewegtem realem Tisch
mit sichtbarem Bodenziel steht aus: Während des Bypass ist die bisherige
Motion-Bodenkontur nicht aktiv, daher aktueller Ein-Tisch-Output allein noch
kein Live-Nachweis der Unterdrückung unter Motion-Projektion. Kein Speichern/Commit.

## Neue CV-Session: Vorschlag aktiviert und Originalmaske erneut geprüft — 2026-10-26

Nach zunächst nicht aktiviertem Controller (Revision 1, Count 0 gegenüber einer
Originalmaske) bestätigt Johannes jetzt Input/Revision 2/drei Chairs. Neue
Session 2207576; separate ausgeschaltete Live-Prüfung passed: ID `table_00`,
Main und drei Chairs identisch frisch mit Frame 9891, Maskenbeleg Frame 9875.
Kantenfehler 0,0593052 cm, Original/Kopie 204300/204295 helle Pixel, keine Pixel
außerhalb des Ein-Pixel-Rands; rohe RGBA-Abweichung 0,5019608140. Originalmaske
und sechs doppelte Referenzen erhalten; alle Indizes 0, Quelle nicht freigegeben.

Nächster Schritt: nach frischer Prüfung ausschließlich neue Session freigeben,
Tisch 25–30 cm ohne neue Aktivierung bewegen und wieder stillstellen. Sichtbares
Bodenziel im CV muss ausgeschlossen bleiben, während realer `table_00` weiter
erkannt wird. Danach aktive Maskenprüfung und lokales OBB-Filteraudit auswerten.
Nicht auf alte Session 4463454 prüfen, keine automatische TD-Speicherung.

## Bodenkonturfilter unter aktiver Motion-Projektion live bestätigt — 2026-10-26

Nach neuer Freigabe bestätigt Johannes Indizes 1/1/0/1 und Vision-Count 1.
Separate aktive Live-Prüfung passed: Session 2207576/Revision 2, ID `table_00`,
Main und drei Chairs identisch frisch mit Frame 11388. Originalmaske aktiv,
sechs doppelte Referenzen erhalten. Pose-/Rasterbeleg Frame 11373: Kantenfehler
0,0000152588 cm, Original/Kopie je 204794 helle Pixel, kein Pixel außerhalb des
Ein-Pixel-Rands. Rohe RGBA-Abweichung 0,2549019754; keine Pixelgleichheit.

Unabhängig davon CV-Audit nach aktiver Projektion ausgewertet: Frames
11960–12359, alle 400 Frames mit zwei rohen OBBs und genau einer Größenablehnung.
Finale Trackmenge ausschließlich `table_00`, keine neuen Track-IDs in der
Stichprobe. Letzte reale OBB 160,881×82,055 cm akzeptiert; Bodenkandidat
137,648×64,872 cm trotz 0,912 Konfidenz wegen beider Mindestkanten verworfen.
Maschinenlesbarer Nachweis unter
`data/aisi/debug/cv_floor_filter_restart_20261026_142506/live_filter_verified_summary.json`.

CV-Fix damit offline (64 Tests und vollständiger Originalbild-Replay), in
laufendem TD (Originalmasken-/Streamprüfung) und anhand realer Kameraframes
unter Motion-Projektion getrennt bestätigt. Weitere Tischpositionen, Rotation/
Verdeckung und Mehrtisch-Raummatrix nicht vollständig geprüft. Kalibrierung,
Masken und gespeicherte TD-Datei unverändert; kein Commit. Temporäres OBB-
Audit ist im laufenden CV-Prozess aktiv, beim nächsten regulären Start ohne
Auditargument starten; kein zweiter Kamera-Neustart nur hierfür.

Nächster Block nach Johannes' Wunsch: konkrete grafische Motion-Anpassungen
abstimmen und gegen den gesicherten Ein-Tisch-Stand simulieren; Zweitisch-
Raumprüfung separat nach erneuter Quellfreigabe. Keine neue Vorschlagsaktivierung
oder Speicherung als Teil dieses abgeschlossenen Filter-Nachweises.

## 5-cm-Tabletop-Rand vorbereitet, noch nicht in TD installiert — 2026-10-26

Johannes wünscht 5 cm umlaufend unbeleuchteten Rand am realen Tabletop;
Anpassung der Tabletop-Zielfläche soll später betrachtet werden, zunächst nur
Rand. Interpretation: Abstand nach innen von der realen Tischkante, maximale
Innenfläche bei Rect 160×80 cm somit 150×70 cm. Keine Änderung von Tischzielen,
Chairs, Ankunftstoleranzen, Weltmaßstab, Originalmasken oder Kalibrierung.

Shader verwendet bestehenden Source-Rounded-Rect-Abstand im Weltmaß in cm.
Tabletop-Content inklusive Feedback und globaler Reveal-Welle wird 5 cm nach
innen beschnitten; bestehende 0,7-cm-Kantenglättung vollständig weiter innen,
damit der ganze äußere 5-cm-Streifen dunkel bleibt. Floor und dessen Ausschluss
der vollen physischen Tischfläche bleiben unverändert. Keine neue Geometrie-
oder Maskenquelle. Der Rand folgt aktuellen Source-Posen.

Helfer `td_builders/update_motion_tabletop_inset.py`: `prepare(op)` liest den
tatsächlich eingebetteten Shader und erzeugt nur einen separaten Vergleichs-
COMP. Keine bestehenden Komponenten oder abweichenden Patchstellen ersetzen.
`install(op)` muss zuerst echte GPU-Bilder alter/neuer Fassung für 0/33/90 Grad
und Reveal vergleichen: Floor pixelgleich, äußerer 5-cm-Streifen transparent,
Innenfläche pixelgleich und nicht leer. Pixelzeilenorientierung aus altem
Alpha-Bild gegen kanonische Source-Geometrie bestimmen. Erst bei Erfolg den
lokalen produktiven Shader gezielt patchen, bisherige Fassung im COMP sichern;
bei Compile-/Schutzfehler zurücknehmen. Probe nach erfolgreichem Einbau entfernen.
`rollback(op)` verweigert Überschreiben späterer lokaler Shaderänderungen.

Offline: sechs neue fokussierte Tests zu Patchgrenzen, Erhalt lokaler Änderungen,
physischem 5-cm-Abstand, Rücknahmeschutz, GPU-Fehler vor Installation und
TD-Python-3.9-Syntax bestanden. Motion gesamt 188 Fälle, 181 bestanden und sieben
optionale native GPU-Fälle übersprungen. Diese Tests ersetzen die vorbereitete
GPU-Prüfung im tatsächlichen TD nicht. TD-Ausführung/Installation und physischer
Randnachweis noch offen; aktuelle Live-Ausgabe und gespeicherte Arbeitskopie
bisher unverändert. Kein neuer Vorschlag, kein Speichern oder Commit.

## Inset-Prüfsicherung: bestätigte laufende Istposen berücksichtigt — 2026-10-26

`prepare(op)` im tatsächlichen TD bestanden, separater Prüfzweig vorhanden;
produktiver Shader unverändert. Erster `install`-Aufruf stoppt noch vor GPU-
Arbeit am Zusatzsnapshot von `comp_layout_proposal/item1`. Lesender Befund
durch Johannes zeigt ausschließlich die konstant gesetzten Livewerte X/Y/Rot:
X 0,8839355316→0,8839132355, Y -0,4794794189→-0,4799470032,
Rot -107,9238205→-107,8826675. Keine Mode-/Binding-/Verdrahtungsabweichung.

Zusatzsicherung im Inset-Helfer eng korrigiert: Nur X/Y/Rot an bestehenden
item1…item5 direkt unter Layout werden als Livewerte behandelt, und nur wenn
sie endlich und zur jeweiligen aktuellen `tables_active`-Zeile passend sind.
Vollständiges Datenrezept/Callbacks/Template/Replikator und genaue Header-
Zuordnung bleiben streng; alle anderen Parameter, Modi, Bindungen, Geometrien
und Verbindungen ebenfalls. Ursprünglichen Snapshot nicht neu erfassen oder
fortschreiben. Bestehende produktive Live-Routing-Prüfung unverändert.

Acht fokussierte Tests bestanden, einschließlich Akzeptanz belegter Pose-
Fortschreibung ohne Snapshotänderung und Ablehnung manueller Pose-, Mode-,
Ziel-, Geometrie-, Callback- und Rezeptänderungen. Vorhandenen Prüfzweig nach
Reload des Helfers weiterverwenden; erneute Vorbereitung würde keine Ursache
beheben. GPU-Prüfung, produktiver Einbau und Raumrandmessung noch offen.

## 5-cm-Tabletop-Innenrand installiert, GPU-Abnahme bestanden — 2026-10-26

Johannes bestätigt `tabletop_inset.install(op)` passed. Vier echte TD-GPU-
Vergleiche bestanden: Rotationen 0/33/90 Grad ohne Welle sowie 33 Grad mit
Reveal. Jeweils äußerer 5-cm-Streifen vollständig dunkel, Innenfläche und
Bodenausgabe pixelgleich zur bisherigen Fassung. Strenge Schutzprüfung nach
Einbau bestanden, keine Änderung an Engine/Reader/Revision, Zielen oder Masken.
Der eigene Vergleichszweig wurde nach Erfolg entfernt; vorheriger Shader unter
`motion_tabletop_inset_backup` im Motion-COMP gesichert. Kein Speichern.

Offline gesamt: 190 Motion-Fälle, 183 bestanden und sieben optionale native
GPU-Fälle übersprungen. Die tatsächlich im TD ausgeführten vier GPU-Vergleiche
sind ein separater positiver Nachweis. Nächster Schritt: bei ruhigem Tisch
`live_output.verify(op)`, danach äußeren dunklen Rand am realen Tabletop
beobachten/messen und bei Verschieben/Drehen prüfen. Physischer 5-cm-Nachweis
noch offen; kein flächiger Projektionsnachweis aus synthetischer GPU-Prüfung
ableiten. Zielgeometrie bleibt bis zum gesonderten Folgeauftrag unverändert.

## 5-cm-Rand verworfen, Rücknahme angefordert — 2026-10-26

Johannes bestätigt, dass der Rand sichtbar ist, findet die Gestaltung jedoch
nicht gut und verlangt Rücknahme. Keine weitere Randprüfung oder Zielgrößen-
anpassung ausführen. Nur diesen Versuch zurücknehmen: Repository-Shader auf
vorherigen Content-Clip zurückgesetzt; bestehende Halo-Anpassung erhalten.
Im laufenden TD gesicherten alten Shader via `tabletop_inset.rollback(op)`
wiederherstellen. Der Helfer verweigert Überschreiben späterer lokaler Änderungen.
Nach bestätigter TD-Rücknahme eigene temporäre Inset-Helfer/Tests entfernen.
Keine gespeicherte TD-Datei wurde geändert, kein Commit. CV-Filter 140/70 cm,
Kalibrierung, Masken, Ziele/Chairs und übrige Motion-Integration bleiben erhalten.
TD-Rücknahme noch durch manuelle Ausführung zu bestätigen.

## Rücknahme des 5-cm-Rands abgeschlossen — 2026-10-26

Johannes bestätigt `restored: true`, Rand verschwunden und vorherige Darstellung
im realen TD wieder sichtbar. Repository-Shader auf vorherige drei Source-
Clipstellen zurückgesetzt, Inset-Konstante entfernt. Ausschließlich die eigenen
Dateien `update_motion_tabletop_inset.py` und `test_motion_tabletop_inset.py`
entfernt; keine fremden lokalen Änderungen verworfen. Die oben stehenden
Inset-Installationsbefehle sind historisch und nicht mehr anzuwenden.

Keine Zielverkleinerung vorgenommen; Kalibrierung, Masken und gespeicherte
Arbeitskopie unverändert. CV-Größenfilter 140/70 cm bleibt erhalten. Keine
erneute Live-Maskenprüfung nach Rollback behaupten; positiver Rücknahme- und
Sichtnachweis stammt von Johannes. Kein Speichern oder Commit.

Neuer Auftrag: Schlagschatten des Navigationskreises, damit er auf umgebender
weißer Tabletop-Zielfläche erkennbar bleibt. Getrennter neuer Gestaltungsversuch;
kein Wiedereinführen des verworfenen Außenrands.

## Navigationskreis-Schlagschatten vorbereitet — 2026-10-26

Nach abgeschlossener Randrücknahme wünscht Johannes einen Schlagschatten,
damit der Navigationskreis auf umgebender weißer Tabletop-Zielfläche sichtbar
bleibt. Separater lokaler Shaderpatch vorbereitet: projizierten Hintergrund
vor Puls-/Kreis-Komposition abdunkeln, danach unveränderten Kreis darüber
zeichnen. Kreisinneres und Richtungsausschnitt erhalten; keine neue Kontur an
Tischkanten, keine Ziel-/Maskenänderung. Ein Projektor kann kein dunkles Licht
erzeugen, daher reduziert der Shader ausschließlich vorhandenes Hintergrundlicht.

Erster überprüfbarer Entwurf: Schattenversatz 2,5 cm auf beiden Contentachsen,
weicher Übergang ±2 cm, maximale Abdunkelung 65 Prozent. Alle Werte skalieren
mit Kreisgröße, Stärke fadet zusätzlich mit Navigation. Ohne Kreis und bei
Erfolg kein Schatten; Puls wird anschließend unverändert komponiert. Vorhandene
Source-Maske begrenzt die gesamte Tabletop-Ausgabe weiterhin wie zuvor.

`td_builders/update_motion_navigation_shadow.py`: tatsächlichen lokalen Shader
lesen und nur einen eigenen isolierten Vergleichszweig aufbauen. Vor Installation
GPU-Vergleich voller/kleiner/fehlender Kreis und Erfolg: Kontrast auf weißer
Zielfläche sichtbar, Kreisinneres und entfernter Inhalt unverändert, Boden
pixelgleich, ohne Navigation/bei Erfolg gesamte Tabletop-Ausgabe pixelgleich.
Lokale Codeabweichungen verweigern; keine neuen Snapshots laufender Istposen.
Bestehende Live-Schutzregistrierung vor/nach Einbau strikt prüfen. Vorherigen
Shader sichern, bei Fehler zurücknehmen, bei späterer lokaler Änderung nicht
überschreiben. Keine automatische Speicherung.

Rücknahme separat geprüft vor neuem Schattenpatch: 175 Motion-Tests bestanden,
sieben optionale GPU-Fälle übersprungen. Mit sechs neuen Tests für Patchgrenzen,
Erhalt lokaler Änderungen, GPU-/Compilefehler ohne dauerhaften Shaderwechsel,
Rücknahmeschutz und TD-Python-3.9-Syntax jetzt 181 bestanden, sieben übersprungen.
TD-GPU-Prüfung, Einbau und physischer Schatten-Sichtbefund stehen noch aus.
CV-Größenfilter und gespeicherte Arbeitskopie bleiben erhalten, kein Commit.

## Navigationskreis-Schlagschatten installiert, GPU-Prüfung bestanden — 2026-10-26

Johannes bestätigt `navigation_shadow.install(op)` passed. Vier tatsächliche
TD-GPU-Vergleiche bestanden: voller Kreis 1511 Schattenpixel, kleiner Kreis
(Navigation 0,35) 165 Schattenpixel, ohne Kreis und bei Erfolg jeweils 0.
Kreisinneres und Boden pixelgleich zur vorherigen Shaderfassung. Engine/
Reader/Revision, Ziele und Masken erhalten; vorheriger Shader unter
`motion_navigation_shadow_backup` im eigenen Motion-COMP gesichert, isolierten
Prüfzweig nach erfolgreichem Einbau entfernt. Kein Speichern/Commit.

Nächster Schritt: bei stillstehendem Tisch separate `live_output.verify(op)`-
Prüfung, danach Sichtbefund des Schattenkontrasts am realen Tabletop bei
umgebender weißer Zielfläche. GPU-Nachweis ersetzt keine gestalterische
Sichtabnahme im Raum. Der verworfene 5-cm-Rand bleibt vollständig entfernt;
keine neue Vorschlagsaktivierung oder Zielverkleinerung.

## Schattengestaltung präzisiert: mittig und radial — 2026-10-26

Johannes erkennt vermutlich einen Schatten, verlangt aber eine statische,
immer mittige und auf allen Seiten homogene Anordnung um den Navigationskreis;
keine Richtungsbewegung wie beim grünen Feedback. Erste versetzte Fassung
deshalb noch nicht gestalterisch abgenommen. Repository-Shader auf reinen
Radiusabstand zum Kreiszentrum umgestellt, Offset 0/0. Radius, Einblendung und
Weichheit bleiben an Navigationskreis gebunden, keine Abhängigkeit von
Feedbackrichtung, -phase oder -zeit. Kreisinneres/Richtungsausschnitt erhalten.

Patcher akzeptiert zusätzlich ausschließlich die exakt bekannte versetzte
Vorgängerfunktion. GPU-Referenz ist die Fassung ohne Schatten, damit Aufhellung
auf der früheren Schattenseite beim Zentrieren nicht als Fehler missverstanden
wird. Neue Prüfungen: Schattenalpha spiegel-/transpositionssymmetrisch sowie
identisch mit und ohne aktives grünes Feedback. Bestehende Boden-/Innenflächen-
und Null-Navigation-/Erfolgskriterien bleiben erhalten.

Bei Upgrade vorherige Schattensicherung anhand aktuellen Shaderhashes prüfen,
zwischen prepare/install unverändert verlangen und ursprünglichen Shader ohne
Schatten für vollständigen Rollback erhalten. Keine pauschale neue Baseline.
Neun fokussierte Tests bestanden, einschließlich Upgrade/Patcherhalt und Schutz
der ursprünglichen Sicherung. TD-Prüfung/Installation der radialen Fassung und
physischer Sichtbefund noch offen; aktuelle TD-Sitzung zeigt bislang die erste
versetzte Version. Nichts speichern oder neu aktivieren.

## Radialer Navigationsschatten installiert und GPU-geprüft — 2026-10-26

Johannes liefert `navigation_shadow.install(op)` mit `passed: true` zurück.
Fünf Vergleiche im laufenden TD bestanden: Navigation 1/0,35 ergibt 1184/108
Schattenpixel, ohne Navigation und bei Erfolg jeweils 0. Mit aktivem grünem
Feedback weiterhin 1184 Schattenpixel; Rundumsymmetrie und unveränderte
Schattenform gegenüber dem Fall ohne Feedback geprüft. Boden und Kreisinneres
pixelgleich zur Referenz ohne Schatten. Keine Engine-Rücksetzung, Ziel- oder
Maskenänderung; nichts gespeichert. Ursprüngliche Rücknahmesicherung bleibt
für vollständigen Rollback erhalten. Offline zuletzt 184 Motion-Tests bestanden,
sieben optionale native GPU-Fälle übersprungen.

Johannes bestätigt anschließend „ist gut so“: radiale Fassung gestalterisch am
realen Tabletop abgenommen und beibehalten. Anschließend separate aktive
`live_output.verify(op)`-Prüfung bestanden: Session 2207576/Revision 2,
`table_00`, Main/Chairs Frame 57607, drei sichtbare Chairs, Indizes 1/1/0/1,
Originalmaske aktiv, sechs doppelte Maskenreferenzen erhalten. Rasterframe
57591: Original/Kopie jeweils 204328 beleuchtete Pixel, keine Pixel außerhalb
der Ein-Pixel-Grenze, maximaler RGBA-Unterschied 0,254902; keine Behauptung
exakter Pixelgleichheit. Maximaler Konturkantenfehler 0,0000216 cm.
Schattenanpassung damit abgeschlossen. Johannes bestätigt anschließend die
manuelle Speicherung; neuer vollständiger Dateiname und erneutes Öffnen noch
nicht bestätigt. Die Sichtabnahme betrifft den Schattenkontrast, keine neue
vollständige Raum-/Projektorvalidierung; der Prüfhelfer meldet weiterhin
`physical_validation: not performed`.

## Tabletop-Feedback an Zielkontur begrenzen — vorbereitet 2026-10-26

Johannes zeigt überstehendes grünes Feedback auf dem Tabletop und verlangt
Begrenzung auf die weiße Zielfläche. Tatsächlicher Contentpfad:
`feedbackHalo` wird über `targetMask` komponiert, am Ende aber bisher nur
durch `sourceMask` beschnitten. Einziger produktiver Shader-Eingriff ist der
zusätzliche Faktor `targetMask` am Feedbackalpha. Zielkontur und physische
Tischmaske bleiben geometrisch unverändert; Navigationskreis, radialer Schatten,
Puls und Erfolgsdarstellung bleiben erhalten.

`td_builders/update_motion_feedback_clip.py` liest den tatsächlichen lokalen
Text von `motion_pixel` (Text DAT), verweigert unbekannten Feedback-Code und
lokale Änderungen zwischen Vorbereitung und Einbau. Eigener isolierter Prüfzweig,
kein Überschreiben vorhandener Komponenten. GPU-Vergleich vor Einbau: Boden
pixelgleich und Zielinneres unverändert, grünes Feedback außerhalb der
Zielkontur entfernt; Drehungen 0/33/90 Grad sowie Reveal, Erfolg und Feedback
aus. Prüfmaske verwendet die Funktionen des lokalen Shaders und kanonische
State-Geometrie. Shaderkompilierfehler stellen den vorherigen Text wieder her;
Engine/Reader/Revision bleiben erhalten. Eigene Hash-gesicherte Rücknahme
bewahrt den radialen Schatten; bestehende Schattensicherung unverändert.
Rücknahme bei Bedarf in umgekehrter Reihenfolge: Feedback, dann Schatten.

Acht fokussierte Tests bestanden; gesamte Motion-Suite 199 Fälle, davon 192
bestanden und sieben optionale native GPU-Fälle übersprungen. Historische
Halo-Testfixture um spätere Feedback-Begrenzung bereinigt, damit weiterhin der
ursprüngliche Halo-Upgradepfad geprüft wird. TD-GPU-Nachweis, Installation,
aktive `live_output.verify(op)`-Prüfung und physischer Sichtbefund noch offen.
Keine automatische Speicherung oder Layoutaktivierung.

## Feedback-Begrenzung installiert und GPU-geprüft — 2026-10-26

Johannes liefert `feedback_clip.install(op)` mit `passed: true` zurück.
Sechs Vergleiche auf der laufenden TD-GPU bestanden. Entfernte überstehende
grüne Pixel bei 0/33/90 Grad: 4859/10229/13781; bei 33 Grad mit Reveal ebenfalls
10229. Zielinneres und Bodenausgabe in allen Fällen pixelgleich, Erfolg und
deaktiviertes Feedback vollständig unverändert. Keine Engine-Rücksetzung,
Ziel- oder Maskenänderung. Eigene Rücknahmesicherung vorhanden, nichts
gespeichert. Anschließend separate aktive `live_output.verify(op)`-Prüfung
bestanden: Session 2207576/Revision 2, `table_00`, Main/Chairs Frame 69531,
drei Chairs, Indizes 1/1/0/1, Originalmaske aktiv, sechs doppelte Maskenreferenzen
erhalten. Rasterframe 69516: Original/Kopie 204764/204770 beleuchtete Pixel,
keine Pixel außerhalb der Ein-Pixel-Grenze, maximaler RGBA-Unterschied 0,498039;
keine exakte Pixelgleichheit behauptet. Maximaler Konturkantenfehler 0,035473 cm.

Johannes bestätigt physisch: Grün bleibt beim Bewegen und Drehen innerhalb der
weißen Zielfläche, Navigationskreis und Schatten passen weiterhin; „Ist gut so“.
Feedback-Begrenzung abgeschlossen. Speicherung dieser Änderung noch nicht
bestätigt. Sichtabnahme betrifft diese Gestaltung; keine vollständige neue
Raum-/Projektorvalidierung. Der technische Helfer meldet weiterhin
`physical_validation: not performed`.

## Feedbackgrün leicht aufgehellt — vorbereitet 2026-10-26

Johannes wünscht etwas grelleres/helleres Feedbackgrün. Nur die RGB-Konstante
des grünen Halos angehoben: 0/236/101 auf 0/255/110. Annähernd gleicher Farbton,
etwa acht Prozent höhere Kanalwerte. Alpha/Verlauf, bestehender Zielkonturclip,
Navigationskreis/radialer Schatten und separate Erfolgsfarbe unverändert.

`update_motion_feedback_brightness.py` patcht ausschließlich die bekannte lokale
Kompositionszeile. Isolierter GPU-Vergleich vor Installation bei drei Drehungen,
Reveal, Erfolg und deaktiviertem Feedback: Boden, Alpha und Ausgabe außerhalb
der Zielfläche pixelgleich; Feedback muss messbar heller werden und darf keine
Kanäle abdunkeln. Erfolg/Feedback aus vollständig unverändert. Transaktionale
Installation mit eigener Hash-Sicherung und Rücknahme; ältere Sicherungen
unverändert, Rücknahme bei Bedarf von neu nach alt (Aufhellung, Begrenzung,
Schatten). Keine automatische Speicherung, Layoutaktivierung oder Änderung
von Kalibrierung, Masken, Zielen und Chairs.

Acht fokussierte Schutz-/Rollbacktests bestanden; gesamte Motion-Suite 207
Fälle, davon 200 bestanden und sieben optionale native GPU-Fälle übersprungen.
TD-GPU-Prüfung/Einbau, separate aktive Live-Prüfung und physische Sichtabnahme
noch offen. Helligkeit im Raum wird erst nach Sichtbefund als bestätigt erfasst.

## Helleres Feedback installiert und GPU-geprüft — 2026-10-26

Johannes bestätigt `feedback_brightness.install(op)` mit `passed: true`.
Sechs Vergleiche auf der laufenden TD-GPU bestanden: bei 0/33/90 Grad
25828/20627/17027 aufgehellte Pixel, bei 33 Grad mit Reveal ebenfalls 20627.
Erfolg und deaktiviertes Feedback unverändert. Bodenausgabe, Alpha und Ausgabe
außerhalb der Zielfläche pixelgleich. Keine Engine-Rücksetzung, Ziel- oder
Maskenänderung; nichts gespeichert. Separate aktive `live_output.verify(op)`-
Prüfung und physische Helligkeits-/Gestaltungsabnahme am Tabletop noch offen.

## Tabletop-Einpasshilfen — vorbereitet 2026-10-26

Johannes verlangt nach drei Referenzbildern: Navigationskreis beim Annähern
nicht vollständig verkleinern, sondern bei 50 Prozent halten; mittiger Zielring
gleicher Endgröße als Schablone; Source-/Zielstriche entlang der jeweiligen
Tischlängsachse in Zielnähe. Auf weißer Zielfläche Hilfen schwarz/Alpha, im
Projektionspfad als transparente Aussparung umgesetzt. Source-Striche außerhalb
der Zielfläche weiß. Nach erfolgreicher Einpassung zieht sich der Navigationskreis
nach innen zusammen und verschwindet, ebenso die Hilfen.

Reversibler Erstentwurf: voller Radius 29 cm, minimal 14,5 cm; Zielring mittig
am Ziel, Außenradius 14,5 cm und Strichstärke 3 cm. Zwei runde Striche je Tisch,
10 cm Mittellinienlänge und 2,5 cm Breite, Mittelpunkte bei ±(Kreisradius+10 cm)
auf lokaler X-Längsachse. Zielstriche fest an Zielpose, Source-Striche an Istpose;
Distanzfade 65 → 25 cm. Nach Erfolg Kreisradius 14,5 → 0 cm über 0,18 s,
Hilfen ebenfalls ausgeblendet. Bestehende grüne Erfolgsauflösung bleibt, der
weiße Erfolgskreis wird separat darüber als schrumpfende Scheibe komponiert.
Keine Änderung von Erfolgsschwellen, Motion-State-Engine, Revision, Zielen,
Chairs, Kalibrierung, Masken oder Bodenkomposition. Anzeigegröße ausschließlich
lokal im Shader angepasst; der übertragene State bleibt unverändert.

`update_motion_alignment_guides.py` liest tatsächlichen lokalen Shader und
patcht nur bekannte Blöcke; unbekannte Abweichungen werden nicht überschrieben.
Wiederverwendung des Helligkeits-Transaktionshelfers mit optionalen Argumenten
für eigenen Probe-/Session-/Backupnamen, Patcher und GPU-Prüfung; bestehende
Aufrufe unverändert. Isolierte GPU-Fälle vor Installation: ferner/halber Radius,
mittiger transparenter Zielring, distanzabhängige Striche weiß/transparent,
0/33/90-Grad-Zieldrehung, unveränderte Bodenausgabe sowie Einwärtskontraktion
und vollständiges Verschwinden nach Erfolg. Eigene Rücknahme vor älteren
Shader-Rücknahmen ausführen. Keine automatische Aktivierung oder Speicherung.

Sechs fokussierte neue Schutz-/Dispatchtests und gesamte Motion-Suite bestanden:
213 Fälle, davon 206 bestanden und sieben optionale native GPU-Fälle übersprungen.
TD-GPU-Prüfung/Installation, aktive Live-Prüfung und physische Gestaltungsabnahme
noch offen. Bisherige Helligkeitsanpassung ist GPU-geprüft installiert; deren
separate aktive/physische Abnahme wurde noch nicht geliefert.

## Einpasshilfen: Float-Rundung im Bodenvergleich — 2026-10-26

Erster TD-Einbau vor produktiver Änderung abgebrochen: strikter Floatvergleich
des unveränderten Bodenpfads ungleich. Johannes’ isolierte Diagnose bestätigt
produktiven Shader unverändert, beide Bilder endlich/fehlerfrei, 759 abweichende
Pixel, maximale Floatabweichung 5,960464477539063e-08; kein Pixel über 1/255.
Dies entspricht der Größenordnung einer Float32-Rundung.

Prüfung präzisiert: maximal eine Float32-Maschinengenauigkeit absolut und
zusätzlich exakt gleiche auf RGBA8 gerundete Pixel. Größere Abweichungen,
Quantisierungsgrenzübertritte und NaN werden weiterhin abgewiesen. Bericht
unterscheidet RGBA8-Gleichheit und maximalen Floatfehler; keine Behauptung
bitgleicher Floatbilder. Zwei Regressionstests dafür bestanden; gesamte
Motion-Suite 215 Fälle, 208 bestanden und sieben optionale GPU-Fälle übersprungen.
Bestehender Prüfzweig bleibt erhalten; nur Python-Prüflogik neu laden und
Installation erneut prüfen. Produktiver Shader bisher unverändert, keine Speicherung.

## Einpasshilfen: Weiß-Prüffall vom Distanzfade getrennt — 2026-10-26

Erneuter Einbau nach bestandenem Bodenvergleich vor produktiver Änderung
gestoppt: Weiß-Prüfung eines Source-Strichs bei 60 cm Distanz verlangte volle
Deckkraft, obwohl dort der beabsichtigte 65→25-cm-Fade erst schwach eingeblendet
ist. Prüffall korrigiert auf 20 cm Distanz mit 90 Grad gedrehtem Ziel: Source-Strich
liegt außerhalb der weißen Zielfläche und ist vollständig eingeblendet. Separater
Fall bei fernem Ziel prüft weiterhin unsichtbare Striche. Kein Shader-/Fade-Wert
verändert, nur isolierte Prüflogik. Acht fokussierte Tests bestanden; erneute
TD-GPU-Prüfung noch offen, nichts gespeichert.

## Einpasshilfen installiert und GPU-geprüft — 2026-10-26

Johannes bestätigt `alignment_guides.install(op)` mit `passed: true`.
Neun GPU-Prüfungen bestanden: Navigationsradius 14,5/29 cm, mittige transparente
Zielringschablone, nahe Striche weiß/transparent, Zieldrehungen 0/33/90 Grad,
Einwärtskontraktion und vollständiges Verschwinden nach Erfolg. Bodenbilder
exakt gleich nach RGBA8-Quantisierung, maximale Floatabweichung
5,960464477539063e-08; keine bitgleiche Float-Ausgabe behauptet. Engine nicht
zurückgesetzt, Ziele und Masken unverändert. Eigene Rücknahmesicherung vorhanden,
nichts gespeichert. Separate aktive `live_output.verify(op)`-Prüfung und
physische Sichtabnahme der Annäherung/Ausrichtung/Erfolgsanimation noch offen.

## Distanzbasierte Navigation und schrumpfender Zielpfeil — vorbereitet 2026-10-26

Johannes präzisiert: Navigationskreis nur distanzabhängig verkleinern, unabhängig
von Orientierung. Pfeilspitze weiter zum Mittelpunkt der Zielkontur richten,
bei sehr kleiner Distanz in sich zusammenziehen statt sichtbarem Richtungswechsel.
Ursache im bisherigen Shader: Kreisgröße aus kombiniertem Runtime-Fortschritt;
Pfeil über gemeinsamen Winkel, der unter 3 cm auf null springt, danach abrupte
Ausblendung. Runtime-Fortschritt und Erfolgsschwellen bleiben unberührt.

Shaderdarstellung jetzt vorbereitet mit Radiusfaktor
`0.5 + 0.5 * smoothstep(8,65,distance)`: bei mindestens 65 cm voller Radius
29 cm, bei höchstens 8 cm halber Radius 14,5 cm. Nach Erfolg bestehende
0,18-s-Kontraktion unverändert. Pfeil separat über `atan(delta.y,delta.x)`
auf Zielmittelpunkt gerichtet; Größenfaktor zusätzlich `smoothstep(0,12,distance)`.
Bei exakt null Distanz unsichtbar, keine Division durch null. Die mathematische
Richtung kehrt sich beim Überqueren des Zielmittelpunkts weiterhin um; die
Darstellung schrumpft dort vorher auf null. Halo-Winkel und Bodenpfeile nicht
verändert. Zielschablone und Ausrichtungsstriche bleiben erhalten.

Reversibler Helfer `update_motion_distance_navigation.py`: nur bekannte lokale
Größen-/Pfeilblöcke ersetzen, eigener Probe und eigene Hash-Sicherung. GPU-Vergleich
vor Installation: identische neue Darstellung bei variierendem altem Fortschritt
über sieben Distanzen, voller Radius, Pfeilflächenabnahme und null bei Zielmitte,
Richtung auf beiden Seiten, unveränderte Erfolgsanimation und Boden nach bestehendem
Float32-/RGBA8-Kriterium. Isolierte Pfeildiagnose verwendet exakt den produktiven
Pfeilausdruck; nur eigener Prüf-DAT angepasst und mitregistriert. Keine bestehenden
Komponenten überschreiben. Rücknahme gegebenenfalls zuerst diese Distanzänderung,
danach Einpasshilfen und ältere Shaderänderungen.

Fünf fokussierte neue Tests bestanden; historische Einpasshilfen-Testfixture
um spätere Distanzänderung bereinigt. Motion-Suite 220 Fälle: 213 bestanden,
sieben optionale native GPU-Fälle übersprungen. TD-GPU-/Live-Prüfung und physische
Sichtabnahme dieser Präzisierung noch offen, keine automatische Speicherung.

## Distanznavigation installiert und GPU-geprüft — 2026-10-26

Johannes bestätigt `distance_navigation.install(op)` mit `passed: true`.
Fünf GPU-Prüfgruppen bestanden: neue Darstellung bei gleichem Abstand unabhängig
vom bisherigen Fortschrittswert (0/6/8/25/40/65/120 cm), schrumpfender Pfeil
bei 12/6/2/0 cm (Alphasummen 322,1474609375/75,70828247070312/2/0),
Zielrichtung auf beiden Seiten, unveränderte Erfolgsanimation und Boden.
Boden exakt RGBA8-pixelgleich, maximaler Floatfehler 0. Keine Engine-Rücksetzung,
Ziel- oder Maskenänderung. Eigene Rücknahmesicherung vorhanden; nichts gespeichert.
Separate aktive `live_output.verify(op)`-Prüfung und physischer Sichtbefund für
reines Drehen bei gleicher Distanz, Annäherung und Zielüberquerung noch offen.

## Früherer Größenabgleich, spätere Striche — vorbereitet 2026-10-26

Johannes wünscht früher abgeschlossene Kreisverkleinerung und etwas später
erscheinende Ausrichtungshilfen beider Kreise. Nur zwei Darstellungsparameter
angepasst: Navigationsradius nun über Distanz 65→20 cm von 29 auf 14,5 cm;
Source-/Zielstriche über 45→15 cm von unsichtbar auf vollständig eingeblendet.
Bei 30 cm Strichdeckkraft 50 Prozent. Zielring weiter unverändert sichtbar,
Pfeilverhalten und Erfolgskontraktion erhalten. Keine Änderung der Runtime,
Erfolgsschwellen, Revision, Ziele, Chairs, Masken oder Kalibrierung.

`update_motion_alignment_timing.py` liest bekannten lokalen Shader, ersetzt nur
diese beiden Ausdrücke und sichert separat. Isolierter GPU-Diagnosezweig verwendet
exakt den produktiven Größen-/Strichcode; prüft acht Distanzen 0/8/15/20/30/45/65/120
cm sowie Boden nach Float32-/RGBA8-Kriterium. Installation nur nach positivem
GPU-Nachweis, keine automatische Aktivierung/Speicherung. Rücknahme bei Bedarf
zuerst Timing, dann Distanznavigation und ältere Shaderänderungen.

Fünf fokussierte neue Tests und gesamte Motion-Suite bestanden: 225 Fälle,
218 bestanden und sieben optionale native GPU-Fälle übersprungen. Historische
Einpasshilfen-/Distanz-Testfixtures normalisieren die spätere Timingänderung.
TD-GPU-Prüfung, Einbau, aktive Live-Prüfung und physische Sichtabnahme noch offen.

## Timing bereits installiert: Sicherungsabgleich bestätigt — 2026-10-26

Erneuter Installationsaufruf meldet fehlenden Prüfzweig. Lesende Diagnose:
kein Timing-/Alignment-Prüfzweig mehr vorhanden, eigene Timing-Sicherung existiert.
Johannes bestätigt anschließend beide Prüfungen mit True: SHA-256 des tatsächlichen
produktiven Shaders entspricht `new_sha256` der Sicherung und aktueller Shader
entspricht exakt `alignment_timing.patch_shader(backup['old'])`. Damit ist die
Timinginstallation bestätigt, ein erneuter Einbau unnötig. Der Helfer erzeugt die
Sicherung und entfernt den Prüfzweig nach erfolgreichem GPU-geprüftem Einbau;
der detaillierte GPU-Ergebnisbericht wurde hier nicht zurückgemeldet.

Textport bestätigt aktuelle Arbeitsdatei
`C:/Users/johan/OneDrive/Dokumente/AISI_DEV/touchdesigner/AISI_v3.2_motion_lab_checkpoint_20261026.6.toe`.
Aus dem Dateinamen allein wird keine Speicherung der aktuellen Timingänderung
abgeleitet. Separate aktive `live_output.verify(op)`-Prüfung und physischer
Sichtbefund für früheren Größenabgleich/spätere Striche noch offen.

## Timing aktiv und am Tabletop abgenommen — 2026-10-26

Johannes bestätigt: Kreis passt früh genug in die Schablone, Striche erscheinen
angenehm spät; „Ist gut so“. Separate aktive `live_output.verify(op)`-Prüfung
bestanden: Session 2207576/Revision 2, `table_00`, Main/Chairs Frame 136446,
drei Chairs, Indizes 1/1/0/1, Originalmaske aktiv und sechs doppelte Referenzen
erhalten. Rasterframe 136430: je 204417 beleuchtete Pixel in Original/Kopie,
keine Pixel außerhalb der Ein-Pixel-Grenze, maximaler RGBA-Unterschied 0,254902;
keine exakte Pixelgleichheit behauptet. Konturkantenfehler maximal 0,0000153 cm.

Timinganpassung abgeschlossen. Speicherung dieses Stands noch nicht bestätigt.
Sichtabnahme bezieht sich auf Größenabgleich und Strich-Timing; kein neuer
vollständiger Raum-/Projektornachweis. Der technische Helfer meldet weiterhin
`physical_validation: not performed`. Separate frühere Abnahmepunkte zu
Helligkeit, Orientierungseinfluss und Zielüberquerung werden dadurch nicht
pauschal als physisch bestätigt markiert.

## Weiße Source-Striche und früheres Feedbackwachstum — vorbereitet 2026-10-26

Johannes verlangt weiße Ausrichtungshilfen des Navigationskreises und etwas
schnellere Vergrößerung des grünen Feedbackkreises. Source-Striche nun weiß
über den darunterliegenden Content komponiert, auch auf weißer Zielfläche;
ihre bisherige Aussparung entfällt. Zielstriche bleiben als transparente
Aussparungen erhalten. Einblendabstände 45→15 cm unverändert.

Nur Halo-Radiuskurve beschleunigt: `smoothstep(0,1,clamp(h*1.2,0,1))` statt
`smoothstep(0,1,h)`. Bei gleichem Fortschritt früher größer, Endgröße schon
bei h≈0,833 statt 1. Anfangs-/Endradius weiter 35/81,4 cm. Keine Änderung von
Richtungsasymmetrie, Kontakt-/Runtime-Zeitkonstanten, Erfolgsschwellen, Zielclip,
Farbe, Navigation, Schatten, Zielen, Chairs, Masken oder Kalibrierung. Dies ist
eine geänderte Wachstumskurve, keine um 20 Prozent verkürzte Zeitkonstante.

`update_motion_feedback_response.py` patcht nur bekannte Radius-/Source-Strich-
Ausdrücke; eigener Probe/Hash-Backup. GPU-Vergleich vor Einbau: Source-Striche
weiß auf Ziel, Zielstriche weiter ausgespart; beide Halo-Funktionen aus
tatsächlichen alten/neuen Shadern isoliert verglichen (h 0/0,25/0,5/0,75/1),
früheres Wachstum mit gleichen Endpunkten; Erfolgsauflösung nach Hilfen-Ausblendung
und Boden erhalten. Naher Strich-Prüffall bei 15 cm für volle Deckkraft des
beabsichtigten Distanzfades. Rücknahme bei Bedarf zuerst diese Änderung.

Fünf neue Schutz-/Dispatchtests und gesamte Motion-Suite bestanden: 230 Fälle,
223 bestanden und sieben optionale native GPU-Fälle übersprungen. Historische
Einpasshilfen-Testfixture normalisiert spätere Source-Strich-/Radiusänderung.
TD-GPU-Prüfung/Einbau, aktive Live-Prüfung und physische Sichtabnahme noch offen.
Keine automatische Speicherung.

## Weiße Source-Striche und Feedbackwachstum installiert — 2026-10-26

Johannes bestätigt `feedback_response.install(op)` mit `passed: true`.
Vier GPU-Prüfgruppen bestanden: Source-Striche weiß und Zielstriche weiter
transparent; früheres Halo-Wachstum mit gleichen Anfangs-/Endpunkten;
Erfolgsauflösung nach Hilfen-Ausblendung erhalten; Boden RGBA8-pixelgleich
bei maximalem Floatfehler 5,960464477539063e-08.

Halo-Alphasummen neu/alt für h=0/0,25/0,5/0,75/1:
11141,144/11141,144; 18927,850/16699,541; 40152,184/32174,084;
61572,559/52799,621; 63885,688/63885,688. Dies ist ein isolierter GPU-
Darstellungsnachweis, keine physische Raum-/Helligkeitsmessung. Keine
Engine-Rücksetzung, Ziel- oder Maskenänderung. Eigene Rücknahmesicherung vorhanden,
nichts gespeichert. Separate aktive `live_output.verify(op)`-Prüfung und
Johannes’ Sichtabnahme der Strichfarbe/Wachstumswirkung am Tabletop noch offen.

## Weiche Wiederaufnahme der Führung — vorbereitet 2026-10-26

Johannes wünscht weiches Wiedererscheinen der grafischen Information, wenn ein
Tisch nach Erfolg wieder herausbewegt wird. Dafür erstmals in diesem Grafikblock
eine kleine Uploader-Ergänzung erforderlich: der Shader allein kennt keinen
Zeitpunkt des Reaktivierungsereignisses. Aktiven `motion_runtime`-DAT zuvor per
Textport lesend geprüft; `td_tick` und tatsächlicher Uploadblock entsprechen
den erwarteten Anschlussstellen. Keine Ableitung allein aus Buildern.

`motion_redisplay.py` verwaltet pro stabiler ID rein visuelle Ereignisse. Nur
der bereits vorhandene Übergang `completed → guidance` startet einen 0,35-s-
Smoothstep von null auf volle Deckkraft. Keine Veränderung von TableMotion-
Klassen oder vorhandenen Instanzen; der Uploader erfasst die vorherige Phase
und nutzt dieselbe Engine. Kleine Bewegungen unter bestehender Reaktivierungsschwelle
und ungültiges Tracking starten keinen neuen Fade. Neue Layoutrevision setzt
die Fade-Ereignisse zurück; ursprüngliche explizite Aktivierung/Reveal bleibt.
Eigener COMP-Speicher `motion_redisplay_events`, Startup-Wert None.

Interne bisher freie State-Spalte 5 je Tisch: X=Sichtbarkeit, Y=Versionsmarker 1.
Shader ohne Marker weiter voll sichtbar. Floor- und Tabletop-Content pro Tisch
werden gemeinsam premultipliziert eingeblendet; bestehende Masken, Belegungs-
ausblendung, Weltgeometrie und Projektorpfad unverändert. Chairs/Ziele bleiben
eingefroren; kein zusätzlicher Layout-/OSC-/Reveal-Trigger. Ältere Zustandsbilder
und isolierte Shaderprüfungen ohne Marker bleiben kompatibel.

`update_motion_redisplay.py` liest tatsächliche Runtime und Shader, patcht nur
bekannte Blöcke. Isolierter GPU-Nachweis vor produktiver Änderung: volle Ausgabe
entspricht Vorgänger, Sichtbarkeiten 0/0,15625/0,5/0,84375/1 für beide Oberflächen,
Legacy-State ohne Marker identisch. Zwei-DAT-Installation kompiliert Runtime,
State und Renderer, prüft identische Engine/Reader/Revision; Fehler stellt beide
alten Texte wieder her und entfernt nur eigenen neuen Fade-Speicher. Eigene
Hash-Sicherung beider DATs für spätere Rücknahme, vor älteren Shaderänderungen
zurücknehmen. Keine automatische Speicherung.

Zehn fokussierte Tests bestanden, darunter tatsächlicher `td_tick`-Durchlauf
Erfolg → completed → guidance mit Werten 0/0,5/1 und unveränderter Engine,
Tabelleninstanz, Revision und Zielpose; ungültiges Tracking, unabhängige IDs,
neue Revision, lokale Patcherhaltung, GPU-/Kompilierfehler und Zwei-DAT-Rollback.
Motion-Suite 240 Fälle: 233 bestanden und sieben optionale native GPU-Fälle
übersprungen. TD-GPU-/Live-Prüfung und physische Sichtabnahme noch offen;
produktiver TD-Graph bislang nicht geändert.

## Weiche Wiedereinblendung installiert und GPU-geprüft — 2026-10-26

Johannes bestätigt `motion_redisplay_update.install(op)` mit `passed: true`.
Runtime und Shader gezielt aktualisiert. Sechs GPU-Prüfungen bestanden:
Floor-/Tabletop-Content gemeinsam premultipliziert mit Sichtbarkeiten
0/0,15625/0,5/0,84375/1; Legacy-State ohne Marker unverändert. Dauer 0,35 s,
Engine nicht zurückgesetzt, Ziele/Masken unverändert. Zwei-DAT-Rücknahmesicherung
vorhanden, nichts gespeichert. Separate aktive `live_output.verify(op)`-Prüfung
und physischer Ablauf Erfolg → Herausbewegen noch offen: weiches Wiedererscheinen,
gleiche Ziele/Chairs/Revision und keine neue Reveal-Welle prüfen.

## Tagesabschluss und Sicherungsauftrag — 2026-10-26

Johannes bestätigt nach dem Wiedereinblendungstest „passt“ und beendet die
heutige Arbeit mit ausdrücklichem Commit-/Pushauftrag. Keine weiteren Live-
Experimente. TD-Datei speichert er selbst; keine automatische Speicherung,
Masterdatei bleibt unverändert. Letzte per Textport bestätigte Arbeitsdatei:
`AISI_v3.2_motion_lab_checkpoint_20261026.6.toe`; neuer finaler Dateiname und
Neustartnachweis noch nicht geliefert. Git enthält Quellen/Tests/Dokumentation,
keinen Ersatz für die manuell gespeicherte physische TD-Arbeitsdatei.

Abschlussprüfung erneut durchgeführt: 257 Motion-/Labor-/Room-Editor-Fälle,
250 bestanden und sieben optionale native GPU-Fälle übersprungen; 69 CV-Fälle
bestanden. Insgesamt 319 bestandene Tests. Physische Sichtabnahme der letzten
weichen Wiederaufnahme ist durch Johannes bestätigt. Letzte separate aktive
Masken-/Streamprüfung bleibt Frame 136446/Session 2207576/Revision 2, vor den
letzten Source-Strich-/Wachstums-/Runtimeänderungen; keine abschließende technische
Prüfausgabe danach erfinden. Kein vollständiger neuer Raum-/Projektornachweis.

Produktive Motion-/CV-Änderungen, relevante lokale Laborhelfer und ihre Tests
sowie Übergabedokumentation werden auf `vision/wip-dark-proposals` gesichert.
Lokale Runtime-/Debug-/Kalibrierungs-/Trainingsdaten einschließlich simulierter
`live_scene.json` bleiben erhalten und ungestagt. Vorhandene Labor-Source-
Verfügbarkeits-/Laufzeitstatusimplementierung bleibt erhalten. Nächster Start:
manuell gespeicherten TD-Checkpoint öffnen, tatsächlichen Dateinamen und
`live_output.verify(op)` erfassen.

## Abgerundete Zielkontur statt weißer Füllung — vorbereitet 2026-10-27

Nach erfolgreich bestätigtem Wiederanlauf wünscht Johannes anhand eines
Referenzbilds eine dicke weiße Kontur mit gleichem Umriss und abgerundeten Ecken
anstelle der gefüllten Zielfläche, ausdrücklich auch auf dem Tabletop.
Erstentwurf 8 cm innenliegend. `targetOutline` verwendet dieselbe lokale
Zielkoordinate, kanonische Shape-Daten und bestehende `roundedRect`-/Coverage-
Funktionen: Originalkontur minus innenliegendes abgerundetes Rechteck. Äußerer
Umriss einschließlich Ecken unverändert; innere Ecken behalten den bestehenden
Rundungsradius, begrenzt auf innere Halbabmessungen. Keine neue physische Maske
oder parallele Footprint-Definition. Bodenpfeile verwenden weiter ursprünglichen
äußeren Zielrand, keine Änderung der Zielgeometrie oder Kalibrierung.

Weiße Grunddarstellung auf beiden Oberflächen verwendet die Kontur. Die
semantische Zielmaske bleibt für Feedbackclip, Zielringschablone und Zielstriche
erhalten. Grünes Feedback darf weiter innerhalb der ganzen ursprünglichen
Zielfläche wachsen. Damit die Einpasshilfen im nun transparenten Inneren nicht
verschwinden, dort weiß komponieren; auf dem weißen Rand weiter ausgespart.
Source-Striche bleiben weiß. Navigationskreis, Pfeil, Schatten, Erfolgsauflösung
und akzeptierte 0,35-s-Wiedereinblendung bleiben erhalten. Keine Layoutaktivierung,
Runtime-/OSC-/Revisions-/Chair-Änderung.

`update_motion_target_outline.py`: tatsächlichen lokalen Shader lesen, nur
bekannte Blöcke patchen; eigener Prüfzweig und eigene Hash-Sicherung. GPU-Prüfung
vor Installation: 0/33/90 Grad, Außenumriss und weiße Randpixel erhalten,
Bodeninneres offen, Tabletop-Füllung entfernt, sichtbare Einpasshilfen,
Feedback weiter vorhanden/begrenzt, Tabletop-Erfolg erhalten, Reveal endlich
und Wiedereinblendung proportional. Frühere Boden-Pixelgleichheit insgesamt
ist hier kein Kriterium: die Bodendarstellung wird ausdrücklich geändert;
Pixel außerhalb des ursprünglichen Zielumrisses bleiben geschützt.
Rücknahme bei Bedarf zuerst Konturversuch, danach ältere Shaderänderungen.

Sechs neue fokussierte Tests bestanden; gesamte Motion-Suite 246 Fälle,
239 bestanden und sieben optionale native GPU-Fälle übersprungen. Historische
Einpasshilfen-Testfixture normalisiert die spätere Konturänderung, um weiterhin
den ursprünglichen Upgradepfad zu prüfen. Keine TD-Installation oder Speicherung
bisher; tatsächlicher GPU-Nachweis, aktive Live-Prüfung und physischer Sichtbefund
stehen noch aus.

## Weiße Zielfüllung mit gerundeten Trennlinien — vorbereitet 2026-10-27

Johannes bestätigt den dicken Rahmen sichtbar und ersetzt den Gestaltungsauftrag:
wieder weiße Fläche, aufgeteilt durch ineinanderliegende Linien gemäß neuer
Referenz. Alle Ecken dieser Rechtecke sauber abgerundet. Für den Rahmenversuch
liegt kein detaillierter Installations-/GPU-Bericht vor; nur Sichtbarkeit belegt.

Erstentwurf drei geschlossene transparente Linien mit 10/20/30 cm Abstand vom
ursprünglichen Außenrand und 1 cm Breite. `targetDividers` nutzt bestehendes
`roundedRect`/Coverage und denselben kanonischen Shape-Rundungsradius für jedes
Rechteck, auf die jeweilige Halbabmessung begrenzt. Keine unterschiedlich frei
gezeichneten Ecken. Weiße Zwischenflächen wieder gefüllt; äußerer Zielumriss und
alle Masken/Projektor-/Weltparameter unverändert. Gleiches Muster für Boden und
Tabletop. Trennlinien auf dem Tabletop nach dem grünen Feedback ausgespart;
Navigation, Schatten, Source-Striche und Zielhilfen anschließend darüber.
Zielhilfen auf Weiß dunkel/transparent, an einer Trennlinie weiß für Kontrast.
Erfolgsdarstellung und 0,35-s-Wiedereinblendung bleiben erhalten.

`update_motion_target_divisions.py`: gezielter Folgepatch vom tatsächlichen
Rahmen-Shader, eigene Probe und eigene Hash-Sicherung. GPU-Prüfung vor Einbau:
0/33/90 Grad, mehrheitlich weiße Fläche und sichtbare Trennlinien, Außenbereich
unverändert, Tabletop-Füllung wiederhergestellt, alle drei Linien und weißen
Zwischenflächen vorhanden, Zielhilfen kontrastreich, Feedback/Erfolg/Reveal/
Wiedereinblendung erhalten. Eigene Rücknahme stellt zunächst Rahmen wieder her;
für ursprüngliche Füllung danach Rahmen-Rollback ausführen. Keine automatische
Layoutaktivierung oder Speicherung.

Sechs neue fokussierte Tests bestanden; gesamte Motion-Suite 252 Fälle,
245 bestanden und sieben optionale native GPU-Fälle übersprungen. Historische
Rahmen-/Einpasshilfen-Testfixtures normalisieren späteren Linienpatch. Neuer
Linienversuch noch nicht in TD installiert, tatsächlicher GPU-/Live-Nachweis und
physischer Sichtbefund offen.

## Linienversuch: geglättete GPU-Kante im Vergleich — 2026-10-27

Einbau vor produktiver Änderung gestoppt: Boden-/Diagnosemuster zunächst mit
1e-6 verglichen. Johannes bestätigt produktiven Shader unverändert; Diagnose
bei Ziel (300,300,0): maximale Abweichung 6,330013275146484e-05 bei Pixel (711,440),
Boden 0,47930270433425903 gegenüber Diagnose 0,4793660044670105, kein Pixel
über 1/255. Das Maximum liegt im Antialias-Zwischenbereich und entspricht der
Größenordnung unabhängiger GLSL-SDF-Auswertung an einer geglätteten Kante.

Prüfung nur dort präzisiert: maximal 1e-4 absolut bei Zwischenwerten, weiße oder
transparente Bereiche unverändert streng mit 1e-6; quantisierter Unterschied
höchstens eine RGBA8-Stufe. Keine Behauptung bitgleicher Bilder zwischen
unabhängigen Diagnose-/Produktionsshadern. Geometrieverschiebungen, Änderungen
flacher Bereiche, NaN und Kantenfehler über 1e-4 werden abgewiesen. Schutz des
Außenbereichs bleibt unverändert. Shader selbst nicht geändert, bestehender
Probe bleibt. Drei gezielte Regressionstests und gesamte Motion-Suite bestanden:
255 Fälle, 248 bestanden, sieben optionale native GPU-Fälle übersprungen.
Erneuter TD-Einbau noch offen, nichts gespeichert.

## Einzelne dünnere äußere Trennlinie — vorbereitet 2026-10-27

Johannes berichtet erfolgreiche Drei-Linien-Installation (`passed: true`) und
bestätigt weiße Fläche mit drei gerundeten Linien sichtbar. Vollständige
GPU-Ausgabe nicht geliefert. Neuer Gestaltungswunsch: nur die äußerste Linie
behalten und etwas dünner machen. Folgeentwurf bei 10 cm Randabstand, von
1 auf 0,6 cm Breite; Linien bei 20/30 cm entfernen. Ausschließlich bekannte
`targetDividers`-Hilfsfunktion ersetzt, gleicher kanonischer Rundungsradius und
äußerer Zielumriss. Weiße Füllung, Zielhilfe-Kontrast, Source-Grafik, Feedback,
Erfolg und Wiedereinblendung unverändert. Kein Runtime-/OSC-/Layout-Eingriff.

`update_motion_target_single_line.py` mit eigenem GPU-Prüfzweig und eigener
Hash-Sicherung. Prüfung vor Einbau: 0/33/90 Grad, einzelne dünne gerundete Linie,
weiße Füllung und unveränderter Außenbereich, an beiden früheren inneren
Linienpositionen wieder Weiß, äußerste Linie schmaler noch sichtbar; Feedback,
Erfolg und proportionaler Fade erhalten. Frühere Kanten-Diagnosetoleranz bleibt
unverändert. Rücknahme stellt zunächst drei Linien wieder her, ältere
Rücknahmen nur anschließend ausführen. Keine automatische Speicherung.

Fünf neue fokussierte Tests und gesamte Motion-Suite bestanden: 260 Fälle,
253 bestanden und sieben optionale native GPU-Fälle übersprungen. Historische
Linien-/Rahmen-/Einpasshilfen-Fixtures normalisieren den späteren Einzel-Linien-
Patch. GPU-/Live-Nachweis und physische Sichtabnahme des neuen Patches noch offen.

## Dünnere Linie außen auf Boden und innen auf Tabletop — vorbereitet 2026-10-27

Johannes verlangt halbe bisherige Stärke und getrennte Lage: Boden außerhalb
ursprünglicher Zielfläche, damit die Linie bei hypothetisch deckungsgleichem Tisch
nicht mitmaskiert wird; Tabletop weiter innen. Erstentwurf 0,3 cm (vorher 0,6),
Bodenlinie als SDF-Abstandslinie 1 cm außerhalb der ursprünglichen Rundkontur.
Dadurch liegt auch die geglättete Linie außerhalb der unveränderten Source-
Kantenmaske. Äußere Rundungen ergeben sich aus derselben kanonischen SDF.
Weiße Bodenfüllung wieder vollständig, keine innere Bodenlinie. Tabletop-Linie
10 cm innen, gleicher kanonischer Rundungsradius, ebenfalls 0,3 cm breit.

Keine Änderung an physischen Masken, deren Reihenfolge, Homographien, Weltmaßstab,
Footprints, Zielposen, Runtime, Chairs oder Revision. Nur grafische Bodenlinie
erweitert den dargestellten Außenbereich. Erfolg und Ausblendung bleiben wie
vorher; der geometrische GPU-Prüffall erzwingt weiterhin Führungsphase, damit
Maskierung und Erfolgsausblendung unabhängig geprüft werden. Keine permanente
Markierung nach Erfolg hinzugefügt.

`update_motion_target_surface_lines.py`: bekannter Drei-Linien- oder einzelner
0,6-cm-Vorgänger als Einstieg, eigener Probe und eigene Hash-Sicherung. Letzter
Einzellinien-Installationsbericht wurde nicht geliefert; beide bekannten Pfade
werden ohne Überschreiben unbekannter lokaler Varianten unterstützt. GPU vor
Einbau: 0/33/90 Grad, Bodenlinie vollständig außerhalb, Tabletop-Linie vollständig
innerhalb, keine innere Bodenlinie mehr, Außenlinie bei deckungsgleichem Source/
Ziel von Source-Maske unbeschnitten, dünnere Tabletop-Linie, Erfolg/Fade erhalten.
Außenbereichschutz schließt ausschließlich die nun ausdrücklich gewünschte neue
Bodenlinie aus; Maskenschutz bleibt unverändert. Eigene Rücknahme zuerst ausführen.

Sieben neue Schutz-/Dispatchtests und gesamte Motion-Suite bestanden: 267 Fälle,
260 bestanden und sieben optionale native GPU-Fälle übersprungen. Historische
Linien-/Rahmen-/Einpasshilfen-Fixtures normalisieren späteren Oberflächenpatch.
TD-GPU-Nachweis, Installation, aktive Live-Prüfung und physische Sichtabnahme
noch offen; keine automatische Speicherung.

## 4-cm-Rahmenstreifen mit weißer Innenfläche — vorbereitet 2026-10-27

Johannes klärt die Rückfrage: Innenfläche bleibt weiß mit feiner Trennlinie.
Es geht um 4 cm weißen Rahmenstreifen, nicht um eine 0,3-cm-Strichstärke.
Missverstandenen Oberflächen-Linienentwurf im Repository zurückgenommen und
gezielten Folgepatch vorbereitet. Tatsächlicher TD-Vorgänger wird beim Vorbereiten
gelesen und nur bei bekannter Struktur ersetzt; kein pauschaler Reset.

Boden: weiße Fläche bis 4 cm außerhalb der ursprünglichen Rundkontur erweitert,
feine transparente Trennlinie bei ursprünglichem Außenrand. Der weiße Streifen
liegt somit außen und bleibt bei deckungsgleicher Source-Maske sichtbar.
Tabletop: ursprünglicher Außenumriss bleibt, Trennlinie bei 4 cm nach innen;
weiße Innenfläche beibehalten. Feine Trennlinienbreite wieder 0,6 cm. SDF-
Konstantabstände gewährleisten gleichmäßige 4-cm-Streifen und saubere Rundungen
(außen Radius um 4 cm größer, innen entsprechend kleiner), dieselbe kanonische
Geometriefunktion. Keine zusätzliche 1-cm-Versetzung aus dem Fehlentwurf.

`update_motion_target_frame_strip.py` korrigiert bekannten 8-cm-Rahmen,
Drei-Linien-/Einzellinienzustand oder missverstandenen 0,3-cm-Außenlinienzustand.
Unbekannte lokale Varianten und Teiländerungen werden verweigert. Eigene Probe
und Hash-Sicherung; Rücknahme stellt tatsächlich vorgefundenen Zustand wieder her.
Physische Masken, Kalibrierung, Zielpose/Chairs/Revision, Runtime und Erfolg
unverändert. GPU-Nachweis vor Einbau: 0/33/90 Grad, 4-cm-Außenrahmen bleibt bei
deckungsgleichen Posen im hypothetischen Führungszustand unmaskiert, Weißfüllung/
Trennlinie an richtigen Grenzen, Tabletop-Erfolg und Wiedereinblendung erhalten.
Bestehende Erfolgsausblendung bleibt; keine permanente Erfolgsmarkierung eingeführt.

Acht neue Schutz-/Dispatchtests bestanden; gesamte Motion-Suite 275 Fälle,
268 bestanden und sieben optionale native GPU-Fälle übersprungen. Historische
Fixturen normalisieren die neueste Korrektur. Noch keine TD-Installation oder
Speicherung; GPU-/Live-Nachweis und physische Sichtabnahme offen.

## Gleiche weiße/transparenten Streifen — vorbereitet 2026-10-27

Johannes ersetzt die vorherigen Maße: transparente Trennung und weißer Streifen
gleich breit, beide wie Ausrichtungshilfen. Ausrichtungshilfen in bekanntem
Shader haben 2,5 cm Stärke; neuer Helfer verweigert lokal abweichende Breite.
Boden: weißer Streifen außerhalb ursprünglicher Kontur von Abstand 0 bis +2,5 cm,
transparente Trennung innen zwischen 0 und −2,5 cm, danach weißer Kern.
Tabletop: weißer Streifen zwischen 0 und −2,5 cm, transparente Trennung zwischen
−2,5 und −5 cm, danach weißer Kern. So verbraucht eine zentrierte Trennlinie
nicht die Hälfte des weißen Streifens. Alle Grenzen als Konstantabstände der
kanonischen Rundkontur; klare Nominalbreiten mit geglätteten Kanten.

`update_motion_target_equal_bands.py` normalisiert bekannte Vorgänger und patcht
gezielt neue Bänder, eigene Probe/Hash-Sicherung. Keine Änderung von physischen
Masken, Runtime, OSC, Zielen/Chairs/Revision oder Erfolgsablauf. GPU soll drei
Drehungen, gleiche Breiten, weißen Kern, unmaskierten Außenstreifen bei
hypothetisch deckungsgleichen Posen sowie Erfolg/Fade prüfen. Sechs neue
Schutz-/Dispatchtests bestanden, gesamte Motion-Suite 281 Fälle: 274 bestanden,
sieben optionale native GPU-Fälle übersprungen. TD-GPU-/Live-Prüfung und physische
Abnahme offen. Kein separater Installationsbericht für vorherigen 4-cm-Entwurf
geliefert; keine entsprechende Installation behauptet.

Vor Live-Einbau ist außerdem der gemeldete Verdeckungsfall zu prüfen: Kamera
4748→7164, Adapter 4232→13376, Controller 22004→14244 und übrige Dienste laufen
unverändert weiter. Szene Frame 58531 enthält `table_01`, frühere aktive
Layoutbindung war `table_00`, Session 2610399/Revision 2. Nicht als Prozesscrash
bezeichnen und IDs nicht still umhängen. Ausgabefreigaben manuell ausschalten,
aktuellen TD-Stream lesen und neue Bindung erst nach bewusster Aktivierung und
Maskenabgleich freigeben. Keine automatische Prozess-/Layoutänderung ausgeführt.

## Gleiche 2,5-cm-Streifen installiert und GPU-geprüft — 2026-10-27

Johannes liefert `target_equal_bands.install(op)` mit `passed: true` zurück.
Acht GPU-Prüfungen bestanden: gleiche weiße/transparente Streifen bei 0/33/90
Grad, Außenrahmen überlebt hypothetisch deckungsgleiche Source-Maske bei allen
drei Drehungen, Nominalbreite entspricht Ausrichtungshilfen, Tabletop-Erfolg
und Wiedereinblendung erhalten. Muster-Floatfehler bei 0/33/90 Grad:
6,306171417236328e-05 / 8,147954940795898e-05 / 6,127357482910156e-05;
maximale RGBA8-Stufendifferenzen 1/1/0. Dies betrifft unabhängigen geglätteten
Diagnose-/Produktionsvergleich; keine exakte Rastergleichheit behauptet.

Engine nicht zurückgesetzt, Ziele und Masken unverändert. Eigene Rücknahmesicherung
vorhanden; frühere Grafikentwürfe durch diesen Stand abgelöst, nicht erneut
installieren. Freigaben weiter aus; vor Live-Ausgabe frischen Originalmasken-
abgleich für Session 2610399/Revision 3/`table_01` prüfen, danach kontrolliert
freigeben und separat aktiv verifizieren. Physische Sichtabnahme dieses Grafik-
stands noch offen. Keine neue Layoutaktivierung oder automatische Speicherung.

## Dünne innere Trennlinie ohne zusätzlichen Bodenrahmen — vorbereitet 2026-10-27

Johannes verlangt einen letzten Gestaltungsversuch: Trennlinie 0,4 cm und auf
dem Boden kein zusätzlicher Außenrahmen; Linie wie auf dem Tabletop nach innen.
Weißer Randstreifen bleibt nominal 2,5 cm breit; transparente Trennlinie beginnt
bei 2,5 cm und endet bei 2,9 cm innen, Mittellinie bei 2,7 cm. Formel über
ursprüngliche kanonische Rundkontur, saubere Rundungen. Weiße Innenfläche bleibt.
Boden-Grunddarstellung verwendet wieder `targetFill` wie Tabletop; zusätzliche
äußere SDF-Fläche/-Streifen entfallen vollständig. Bestehende Bodenpfeile sind
unverändert; Aussage „kein Außenrahmen“ bezieht sich auf die Zielgrunddarstellung.

`update_motion_target_inner_divider.py` patcht nur bekannte 2,5-cm-Bänderfunktion
und Floor-Grunddarstellung. Eigene Probe/Hash-Sicherung; Rücknahme stellt letzte
breite Bänder wieder her. Keine Runtime-/Masken-/Kalibrierungs-/OSC-/Layoutänderung.
GPU-Prüfung vor Einbau: 0/33/90 Grad, Füllmuster mit dünner innerer Linie,
ursprünglicher Footprint erhalten und alter Außenrahmenbereich leer, auch bei
hypothetisch deckungsgleichen Source-/Zielposen; weiße Rand-/Innenbereiche,
Tabletop-Erfolg und Wiedereinblendung erhalten. Frühere Kantenvergleichsregel
unverändert, sechs neue Schutz-/Dispatchtests bestanden.

Gesamte Motion-Suite 287 Fälle: 280 bestanden, sieben optionale native GPU-Fälle
übersprungen. Historische Shader-Fixtures normalisieren neueste Präzisierung.
Noch keine TD-Installation oder Speicherung; tatsächlicher GPU-/Live-Nachweis
und physische Sichtabnahme offen. Keine erneute Vorschlagsaktivierung nötig.

## Innere 0,4-cm-Trennlinie installiert, Außenrahmen entfernt — 2026-10-27

Johannes liefert `target_inner_divider.install(op)` mit `passed: true` zurück.
Fünf GPU-Prüfgruppen bestanden: Innenlinie ohne zusätzlichen Außenrahmen bei
0/33/90 Grad, Tabletop-Innenlinie und weißer Kern, Tabletop-Erfolg und
Wiedereinblendung erhalten. Muster-Floatfehler bei 0/33/90 Grad:
6,127357482910156e-05 / 7,510185241699219e-05 / 6,109476089477539e-05;
maximale RGBA8-Stufendifferenzen 0/1/0. Vergleich betrifft unabhängige geglättete
GPU-Auswertungen; keine bitgleichen Diagnosebilder behauptet.

Engine nicht zurückgesetzt, Ziele/Masken unverändert, eigene Rücknahmesicherung
vorhanden. Keine neue Vorschlagsaktivierung, nichts gespeichert. Separate aktive
`live_output.verify(op)`-Prüfung und Johannes’ physischer Sichtbefund der dünnen
Innenlinie auf beiden Oberflächen ohne zusätzlichen Boden-Außenrahmen noch offen.

## Vergleich ohne Trennstrich als Standard abgenommen — 2026-10-27

Johannes bestätigt: „ohne Trennstrich ist es viel besser“ und beauftragt,
diesen Stand wieder zum Standard zu machen. Alle heutigen Rahmen-/Trennlinien-
Varianten sind damit gestalterisch abgelöst, nicht erneut installieren.
Repository-Shader setzt `targetLines` auf null mit explizitem Standardmarker.
Dies entspricht in der Darstellung der zuvor temporär ausgeblendeten Fassung;
keine zusätzliche Geometrie-/Maskenänderung. Navigation, Feedback, Schatten,
Source-Striche und mittige Zielschablone/-striche bleiben eigenständig erhalten.

Vergleichshelfer um `adopt_as_default(op)` ergänzt: bekannte sichtbare Fassung
oder hash-gesicherte Vergleichsansicht akzeptieren, tatsächliche lokale Texte
bewahren, temporäre Sitzung schließen und eigene Standard-Rücknahmesicherung
mit vorherigem sichtbaren Linienstand/Hashes speichern. Kompilierfehler stellen
vorherige Ansicht wieder her. Renderer und Engine/Reader/Revision geprüft,
keine automatische Speicherung. Explizite spätere Rücknahme über
`restore_previous_divider(op)`; normale `show(op)`-Vergleichssitzung ist nach
Standardübernahme geschlossen, damit Linien nicht versehentlich wiederkehren.

Sieben neue Tests für Übernahme aus Vergleich/normaler Fassung, lokale Folge-
änderungen, Kompilierfehler, Idempotenz und gesicherte Rücknahme bestanden.
Motion-Suite 294 Fälle: 287 bestanden, sieben optionale native GPU-Fälle
übersprungen. Historische Testfixtures normalisieren Standardmarker vor ihren
Upgradepfadtests. Physische Gestaltungsabnahme ohne Trennstrich durch Johannes
vorhanden; tatsächlicher Standardübernahme-Aufruf im laufenden TD, separate
abschließende `live_output.verify(op)`-Ausgabe und manuelle Speicherung noch offen.

## Zielringschablone mit gemeinsamem Nähe-Fade — vorbereitet 2026-10-27

Johannes wünscht den Kreis im Mittelpunkt der Zielkontur wie die Ausrichtungshilfen
erst bei Nähe eingeblendet. Einziger Eingriff: `templateRing *= guides`, bestehende
Distanzkurve 45→15 cm und Erfolgsfade dadurch gemeinsam. Keine neue Kurve,
keine andere Kreisgröße oder Position. Source-Navigationskreis bleibt unverändert;
solide Zielfläche ohne Trennstrich bleibt Standard. Keine Runtime-/OSC-/Masken-/
Layoutaktivierung oder Revision-/Chairänderung.

`update_motion_target_template_fade.py`: gezielter Patch der bekannten lokalen
Kreiszeile, eigener Probe/Hash-Backup. Noch offener temporärer Trennlinienvergleich
wird erkannt und vor Folgepatch zur Standardübernahme aufgefordert; keine
stille Invalidierung seiner Rücknahmesicherung. GPU-Prüfung vor Einbau:
Kreis bei 15 cm vollständig, bei 30 cm halb, ab 45 cm unsichtbar; nahe Fassung
bei 0/33/90 Grad unverändert, Erfolg/Wiedereinblendung und Bodenausgabe erhalten.
Sechs neue Schutz-/Dispatchtests bestanden; Motion-Suite 300 Fälle, 293 bestanden,
sieben optionale native GPU-Fälle übersprungen. Historische Einpasshilfen-Fixture
normalisiert spätere Fade-Ergänzung. TD-GPU-Nachweis, Installation und aktive/
physische Abnahme noch offen. Keine automatische Speicherung.

## Zielkreis-Nähe-Fade installiert und GPU-geprüft — 2026-10-27

Johannes liefert `target_template_fade.install(op)` mit `passed: true` zurück.
Sieben GPU-Prüfgruppen bestanden: Zielkreis bei 15 cm vollständig sichtbar,
bei 30 cm halb und ab 45 cm ausgeblendet; erwartete Hintergrundalphas
0/0,5/1/1 bei 15/30/45/60 cm exakt erreicht. Nahe Darstellung bei 0/33/90 Grad,
Erfolg und Wiedereinblendung erhalten. Boden RGBA8-pixelgleich, Floatfehler 0.
Engine nicht zurückgesetzt, Ziele und Masken unverändert. Eigene Rücknahmesicherung
vorhanden, nichts gespeichert. Separate aktive `live_output.verify(op)`-Ausgabe
inzwischen bestanden: Session 2610399/Revision 3, `table_01`, drei Chairs,
Main-/Chair-Frame 114756, Maskenprüf-Frame 114742, Indizes 1/1/0/1.
Originalmaske aktiv, sechs doppelte Maskenreferenzen erhalten, Kantenfehler
0,0000153 cm; beide Masken je 204490 beleuchtete Pixel und keine Pixel außerhalb
der Ein-Pixel-Grenze. Physischer Sichtbefund des gemeinsamen Nähe-Fades noch offen.

## Referenzen und Bearbeitungsstand

- Gelesen: `AGENTS.md`, relevante Abschnitte aus `TODO.md`,
  `PROJECT_CONTEXT.md`, `DECISIONS.md` und
  `/Users/Johannes/Downloads/AISI_TD_Implementation_Handoff.md`.
- Referenzpaket erhalten und entpackt: `/Users/Johannes/Downloads/AISI_Remotion_v1_5.zip`.
  SHA-256: `35a36c7232ba8a4976ecc5470907efc80ee57d0b52437265a9b9832d35cb7b11`.
  `src/model.ts`, `src/visual.ts`, `src/Scene.tsx`, Demo-/Interaktionsanbindung
  und Referenztests gelesen; MP4-Frames zum Vergleich extrahiert.
- Isolierter Builder, Zustandslogik, gemeinsamer Shader und Diagnose sind im
  Repository vorbereitet. Johannes hat die Motion-Komponente in TD erzeugt
  und die technische Diagnose erfolgreich ausgeführt. Keine bestehenden
  Render-/Projektorverbindungen verändert; nichts gespeichert.
- `td_builders/inspect_motion_content.py` liest die laufende Struktur aus.
  Syntax, Offline-Bericht und Verhalten bei fehlenden Knoten sind geprüft;
  Johannes hat die kompakte Abfrage erfolgreich in TD ausgeführt.

## Implementierte Preview-Fassung

- `td_builders/build_motion_preview.py` erzeugt ausschließlich
  `/project1/comp_aisi_motion_v1_5` (Container COMP). Existiert der Name bereits,
  wird abgebrochen; bei einem Aufbaufehler wird nur der neue COMP entfernt.
- `motion_runtime` (Text DAT) enthält den eingebetteten Code aus
  `td_builders/motion_design.py`; die Geometrie verwendet das kanonische Rect
  und die bestehenden Polygon-/Kreisprüfungen aus `aisi.core.table_geometry`.
- Erster manueller Builder-Aufruf in TD scheiterte noch vor der COMP-Erzeugung
  an `dataclass(slots=True)`. `motion_geometry_compat.py` lädt für Python 3.9
  denselben kanonischen Geometriequelltext in einen eigenen Namensraum ohne
  die Speicheroptimierung `slots` und ohne den nur für Annotationen benötigten
  Import der Anwendungsmodelle. `frozen` und alle Geometriefunktionen bleiben
  erhalten. Keine gemeinsamen Dateien oder globalen Dataclass-Funktionen
  werden im TD-Prozess verändert. Der erneute Aufbau ist inzwischen bestanden.
- Zweiter TD-Aufruf erreichte die Ausgangserzeugung; der fälschlich verwendete
  Parameter `index` am Out TOP verursachte einen Abbruch. Der neue COMP wurde
  durch den Builder zurückgenommen. Korrigiert: `connectorder` nur verwenden,
  falls vorhanden; andernfalls bestimmen die alphabetischen Namen
  `out_floor`, `out_tabletop` die Reihenfolge. Erneuter Aufbau bestanden.
- `state` (Script TOP) transportiert eine 6 × 6 RGBA-Float32-Matrix;
  `render_floor`, `render_tabletop`, `render_preview` (jeweils GLSL TOP)
  verwenden denselben Shader aus `td_builders/motion_design.frag`.
- Zwei Oberflächenausgänge: `out_floor`, `out_tabletop` (jeweils Out TOP).
  `render_preview` (GLSL TOP) kombiniert beide mit einer grauen Tischfläche;
  diese Hilfsfläche und der grüne Raumhintergrund gehören nur zur Vorschau.
- Reale monotone Sekunden; ein eigener Layout-Zähler startet die globale
  3-s-Welle einmal. Poseänderungen lösen keinen Reveal aus. Die Zustandsmaschine
  verwaltet Guidance, Dissolve, Completed und zeitliche Kontakt-/Pulszustände
  unabhängig je `table_id`; der Shader unterstützt bis zu fünf Rect-Tische.
- Der Pfeil entspricht den drei abgerundeten Segmenten aus `Scene.tsx`.
  Kontakt wird über die abgerundeten Kerne berechnet. Ziel-/Source-Schnitt,
  Verdeckung und Clipping verwenden dieselbe Kontur. Der erste Bodenpfeil
  verankert sich an der abgerundeten Zielkante; die Referenz benutzt hier
  noch die eckige Randdistanz. Diese Präzisierung folgt dem Handoff.
- Grüne Unschärfe, Puls-/Dissolve-Kanten und Reveal-Saum sind analytische
  GPU-Näherungen der SVG-Filter; keine Pixelgleichheit behaupten. Farb- und
  Kantenvergleich in TD ist noch erforderlich.

### Manuelle Verwendung

Im TD-Textport auf dem Mac:

```python
p = '/Users/Johannes/dev/Promotion_Prototypen/AISI/td_builders/build_motion_preview.py'; exec(compile(open(p, encoding='utf-8').read(), p, 'exec'))
p = '/Users/Johannes/dev/Promotion_Prototypen/AISI/td_builders/check_motion_preview.py'; exec(compile(open(p, encoding='utf-8').read(), p, 'exec'))
```

Die Diagnose kocht ausschließlich neue Motion-Operatoren und meldet Fehler,
Auflösung und Zustandsmatrix. `passed` betrifft diese technische Diagnose,
keine visuelle Freigabe. Im Operator-Viewer `render_preview` (GLSL TOP) öffnen.
Keine Projektorfenster öffnen und nicht automatisch speichern.

```python
c = op('/project1/comp_aisi_motion_v1_5')
c.par.Demo = True
c.par.Layoutrevision = int(c.par.Layoutrevision.eval()) + 1
```

Damit startet die einmalige 22-s-Referenzbewegung. `Demo = False` erlaubt
manuelle Source-/Target-Parameter in cm und Grad. Die Referenzrotation wird
einmal um +90° in die kanonische Längsachsenkonvention umgerechnet:
Source `(110, 180, 84°)`, Target `(320, 330, 122°)`.

Für einen frischen Kontaktversuch zuerst neue Source/Target setzen und danach
`Layoutrevision` erhöhen. Nach abgeschlossenem Dissolve sind größere Bewegungen
gegenüber der gespeicherten Erfolgspose zur Reaktivierung erforderlich.

`Usedat = True` schaltet auf `poses` (Table DAT) im neuen COMP um.
Spalten: `table_id, source_x, source_y, source_r, target_x, target_y, target_r,
valid, active`. IDs müssen eindeutig und nicht leer sein; maximal fünf Zeilen.
`active = 0` erhält die Tischbelegung für Verdeckung und globale Welle, ohne
individuelle Navigation. Ungültige/Nicht-Endliche Posen werden ausgeblendet
und können keinen Erfolg auslösen. Ein gestarteter Dissolve läuft zeitlich
weiter. Dieses konservative Verhalten ist eine technische Vorschauannahme,
keine gestalterische Freigabe für längeren Trackingverlust.

Stillstandserkennung für die Vorschau: Bewegung gegenüber dem letzten
Bewegungsanker über 0,3 cm oder 0,2° setzt die Idle-Zeit zurück. Diese
reversiblen Filterwerte sind noch unter realem Tracking-Jitter zu prüfen.

### Lokal ausgeführte Nachweise

- In der laufenden TD-Instanz durch Johannes geprüft: Python 3.9.5,
  `state` (Script TOP) 6 × 6 und Zustandsmatrix `[6, 6, 4]`; beide
  Oberflächenrenderer, beide Ausgänge und `render_preview` (GLSL TOP)
  fehlerfrei bei 1000 × 1000 Pixeln. Diagnose meldet `passed: true`.
  Source `(110,180,84°)`, Target `(320,330,122°)`, Navigationsskala 1,
  Kontakt/Grün/Phase jeweils 0. Das bestätigt Aufbau und Shaderausführung,
  noch keine sichtbare Bewegungssequenz oder kontinuierliche Aktualisierung.
- Anschließend Demo im Operator-Viewer gestartet; Johannes bestätigt
  „ja sieht richtig aus“. Damit ist die sichtbare Demo qualitativ bestätigt.
  Keine zusätzliche Behauptung zu einzelnen Grenzfällen, Trackingverlust,
  unabhängigen Mehrtisch-Abschlüssen oder realer Projektion.
- 14 fokussierte Tests in `tests/test_motion_design.py`: Python-3.9-kompatibler
  Geometrieimport mit weiterhin unveränderlichen Datenklassen, Kontakt einschließlich
  gedrehter Ecken, keine Freigabe vor Kontakt, erneuter Kontakt, Ausblendung,
  Verschlechterung, positiver Navigationsradius außerhalb der Toleranz,
  direkter/verriegelter Dissolve, Reaktivierung, ungültige Posen,
  Puls-Abbruch, globale Aktivierung und unabhängige IDs.
- Die 22-s-Demo läuft im Zustandsmodell bei 24, 60 und 97 Hz bis Completed.
- Alle 12 unveränderten Tests des gelieferten Remotion-Pakets bestehen.
- 1200 deterministische zufällige Posepaare: Kontaktentscheidung stimmt mit
  dem originalen `model.ts` aus v1.5 überein.
- Shader offline in einem macOS-CGL-Kontext kompiliert und gelinkt (Apple
  Software Renderer, GLSL 4.10); acht Zeitpunkte als Bilder gerendert.
  Beim Vergleich mit der gelieferten MP4 wurde ein undefinierter Richtungswinkel
  bei Distanz null erkannt und entsprechend der Referenz auf null gesetzt.
  Das ist kein Nachweis der Kompilierung in der laufenden TD-Version.

Reproduzierbare fokussierte Repository-Prüfung:

```bash
PYTHONPATH=src:. .venv/bin/python -m unittest discover -s tests -p test_motion_design.py -v
```

## Im laufenden Projekt durch Textport-Ausgabe nachgewiesen

Die von Johannes übermittelten Ausgaben stammen aus der laufenden Instanz;
sie belegen Anschlüsse und Parameter, keine korrekte physische Projektion.
Der Anfang des ersten langen Berichts fehlt. Die kompakte zweite Ausgabe
enthält Renderauswahl, Kamera und ausgewählte OSC-Werte vollständig.

Alle folgenden Pfade liegen unter `/project1/`:

| Funktion | Tatsächlicher Anschluss |
| --- | --- |
| Floor-Quelle | `comp_layout_proposal/null_floor_with_optional_synth_chairs` (Null TOP), gespeist von `switch_enable_synth_chairs_regular` (Switch TOP) |
| Floor-Auswahl | `comp_output/select_central_floor` (Select TOP) referenziert diese Floor-Quelle; Eingang 0 von `switch_floor` (Switch TOP) |
| Tabletop-Quelle | `comp_layout_proposal/null_tabletop_masked` (Null TOP), gespeist von `mask_tabletop` (Composite TOP, Multiply) |
| Tabletop-Auswahl | `comp_output/select_tabletop` (Select TOP) referenziert diese Tabletop-Quelle; Eingang 0 von `switch_tabletop` (Switch TOP) |
| Maskenquelle | `comp_layout_proposal/null_table_mask` (Null TOP), gespeist von `reorder_table_mask` (Reorder TOP) |
| Maskenauswahl | `comp_output/select_table_mask` (Select TOP) → Eingang 0 von `switch_table_mask` (Switch TOP) |
| Projektor 0 | `comp_output/comp_projector_0` (Base COMP), Eingänge: `layer_floor_switch`, `layer_tabletop_switch`, `switch_table_mask` (jeweils Switch TOP) |
| Projektor 1 | `comp_output/comp_projector_1` (Base COMP), Eingänge: `rotate_180_floor`, `rotate_180_tabletop`, `rotate_180_table_mask` (jeweils Transform TOP) |

`switch_floor`, `switch_tabletop` und `switch_table_mask` (jeweils Switch TOP)
wählen über `int(op('panel_mode')['state'][0])` zwischen Content und
Kalibrierungsquelle. Diese Umschaltung bleibt erhalten. Homographien,
Projektortransformationen und Maskenreihenfolge bleiben geschützt.

`render_floor` und `render_tabletop` (jeweils Render TOP) unter
`comp_layout_proposal` verwenden `cam1` (Camera COMP), orthografisch,
Breite 2,6 TD-Einheiten, Z = 5, keine Kamerarotation, 2000 × 2000 Pixel.
Ihre Geometry-Expressions enthalten getrennte Tracking-/Study-/AISI-Zweige.
Im gemeldeten AISI-Modus enthalten die aufgelösten Listen Tischgeometrien
doppelt; Ursache und Wirkung sind noch nicht untersucht. Keine Bereinigung
als Nebenänderung vornehmen.

## Pose-Schnittstelle und offene Umrechnung

Die Meldung enthält `study/mode = 2`, `table/count = 5`,
`table/0/source_available = 1`, Rect-Typ-ID 2 und Maße 160 × 80 cm.
`comp_io/null_osc_raw` (Null CHOP) enthält Source-/Target-Pose je Index.
Das Repository sendet Winkel über diesen allgemeinen Tischpfad negiert;
der separate Vision-Pfad verwendet Weltwinkel. Die Pfade nicht vermischen.

Gleichzeitig gemeldete Werte für Slot 0 und `item1` (Base COMP):

| Größe | OSC | Item-Parameter |
| --- | --- | --- |
| Source X | 162,442993 cm | +0,455296 TD |
| Source Y | 229,960999 cm | −0,104203 TD |
| Source Rotation | 178,576004° | 178,576004° |
| Target X | 152,662994 cm | +0,506152 TD |
| Target Y | 198,401993 cm | −0,268310 TD |
| Target Rotation | 178,638000° | 178,638000° |

Die Positionswerte entsprechen in dieser Stichprobe
`X = (250 − world_x) * 0.0052`, `Y = (world_y − 250) * 0.0052`.
Das ist gegenüber der dokumentierten Standardumrechnung auf beiden Achsen
umgekehrt. Die zuständige Aktualisierungslogik ist noch nicht ausgelesen;
eine allgemeine Transformationsregel oder Fehlerursache ist damit nicht
nachgewiesen. Vor dem Live-Anschluss an bekannten Posen prüfen und an einer
einzigen Content-Schnittstelle abbilden. Keine Kalibrierung kompensierend ändern.

`source_available` allein belegt keine Aktualität: Empfangszeit, stabile
`table_id`-/Slot-Bindung und Layout-Aktivierungsereignis sind vor Livebetrieb
noch zu prüfen. Eine Pose-Aktualisierung darf keinen Reveal auslösen.

## Room-Editor-/OSC-Simulation — Einzel-Tisch-Abnahme bestätigt

Johannes wählt ausdrücklich zuerst die Room-Editor-/OSC-Simulation. Bei der
Prüfung lief auf dem Mac kein Python-Sender. Der bestehende Empfänger ist
`comp_io/oscin1` (OSC In CHOP), Port 9000, `protocol = msging`,
`netaddress = localhost`, `timeslice = True`; diese Einstellungen bleiben
unverändert. Der Raw-CHOP enthält aufbewahrte Werte: Bei Vision-Count 5 sind
auch Slots 5/6 noch als verfügbar markiert. Keine Aktualität daraus ableiten.

`aisi.app.motion_preview_sim` verwendet den bestehenden Room Editor mit einem
optionalen separaten Szenenpfad. Standard-Editor und seine bisherige Szene
bleiben erhalten. Für die Motion-Simulation werden ein einzelner Rect-Tisch,
die Referenzzielpose und eigene Bedienelemente für Aktivierung, Zielpose und
Übertragungspause eingerichtet. Wahlweise sind jetzt 1, 3 oder 5 Tische
über `--tables` möglich; ohne CLI-Option bleibt es beim Einzel-Tisch-Fall.
Szene und Prozesslog liegen ausschließlich
unter `/private/tmp/aisi-motion-sim/`.

Der Simulator sendet alle 50 ms ein OSC-Bundle an den bestehenden Empfänger,
ausschließlich unter dem neuen Präfix `/aisi_motion/`. Keine bisherigen
`/table/...`, `/vision/...` oder `/study/...`-Adressen werden gesendet oder
geändert. Kein weiterer Netzwerkempfänger wird angelegt. Die neue Vorschau
liest Tischdaten anhand URL-kodierter `table_id` im Kanalpfad; Source und
Target bleiben unter derselben ID. Globale Session-, Frame-, Layoutzähler
und Count begrenzen die aktuellen Daten. Diese Zähler bleiben Float32-exakt.

`td_builders/motion_osc.py` prüft vollständige Frames und zählt alte
Tischkanäle nicht als aktuelle Belegung. Gespeicherte Startwerte werden erst
nach einem weiteren Frame derselben Session gültig. Ohne neuen Frame für
0,5 s wird die gesamte neue Content-Ausgabe transparent. Ungültige Daten,
zurücklaufende Frames und Zieländerungen ohne Layoutaktivierung werden
abgelehnt. Neue Posen starten keinen Reveal. Die Zielpose wird im Simulator
getrennt von den beweglichen Source-Posen gehalten; „Vorschlag aktivieren“
erhöht den Layoutzähler. Laufzeitobjekte erhalten leere TD-Startup-Werte,
damit monotone Zeiten oder alte Streamzustände nicht aus einer .toe fortleben.

Manuell nacheinander im TD-Textport ausführen. Der Launcher startet nach dem
Mehrtisch-Auftrag standardmäßig drei Tische. Bei einem Count-Wechsel startet
er den eindeutig zugeordneten Motion-Simulator neu; das TD-Preview bleibt offen:

```python
p = '/Users/Johannes/dev/Promotion_Prototypen/AISI/td_builders/connect_motion_sim_preview.py'; exec(compile(open(p, encoding='utf-8').read(), p, 'exec'))
p = '/Users/Johannes/dev/Promotion_Prototypen/AISI/td_builders/start_motion_simulation.py'; exec(compile(open(p, encoding='utf-8').read(), p, 'exec'))
```

Der erste Befehl aktualisiert ausschließlich die neue Motion-Komponente.
Der zweite startet den Room Editor mit dem vorhandenen Repository-Python
statt TD-Python 3.9; doppelte Starts desselben gestarteten Prozesses werden
vermieden. Das bestehende Motion-Preview-Fenster weiterverwenden.
Tisch ziehen, mit Q/E drehen; Zielkontur ist im Room Editor grün gestrichelt.
Bei Übertragungspause muss das TD-Preview nach 0,5 s nur den Raumhintergrund
zeigen. Nach Fortsetzen darf keine neue Welle starten. Mit „Auf Zielpose“
direkten Dissolve prüfen; mit „Vorschlag aktivieren“ eine neue Welle.
Beenden über ESC oder das Schließen des Room-Editor-Fensters.

Technische Diagnose danach erneut mit `check_motion_preview.py` ausführen;
`live_stream` meldet Aktualität, Grund, Session/Frame, IDs und Layoutkennung.
Zurück zur vorherigen Demo: `Useosc = False`, `Demo = True`, anschließend
`Layoutrevision` erhöhen.

Nachweise: 26 Motion-/Transporttests und acht bestehende Room-Editor-Tests
bestanden. Dazu gehören OSC-Bundle-Kodierung/-Dekodierung, Tischidentität,
alte Kanäle bei sinkendem Count, Senderneustart, Timeout, explizite
Layoutaktivierung, tatsächliche TD-Matrixausgabe mit simuliertem Raw-CHOP
und ein separater Szenenspeicherpfad. Keine echten Netzwerkpakete oder
GUI-Bedienung sind durch diese Offline-Tests nachgewiesen. Der aktualisierte
Shader kompiliert offline auf macOS. Der manuelle Anschluss in TD und das
Room-Editor-Fenster waren zunächst offen. Johannes hat danach den Anschluss
und Start ausgeführt (Simulator-PID 82544) und bestätigt: „das preview reagiert
korrekt“. Damit ist die Reaktion auf die Room-Editor-/OSC-Simulation
qualitativ bestätigt. Der Bericht des Anschlussskripts bestätigt unveränderte
Empfängereinstellungen und keine neuen Projektorverbindungen. Eine explizite
Einzelbestätigung von Pause/Fortsetzung oder sämtlichen Grenzfällen wird
daraus nicht abgeleitet. Kamera-/Live-Tracking und die produktive
Content-Umschaltung bleiben eigene folgende Schritte.

### Deterministische TD-Grenzfall-Abnahme

`td_builders/check_motion_acceptance.py` erstellt einen eigenen temporären
`comp_aisi_motion_acceptance` (Container COMP) mit kontrollierter Testzeit,
gleichem Zustandsmodell und gleichem Shader. Der bestehende Motion-COMP,
OSC-Empfänger, Kalibrierung und Ausgabe werden nicht verändert. Nach dem
Test wird ausschließlich der temporäre COMP entfernt; bei einem bereits
vorhandenen gleichnamigen COMP wird vorab abgebrochen.

Die Prüfung misst Kontakt-/Navigationszustände und echte TOP-Pixel: kein
Grün vor Kontakt trotz verbessertem Winkel; Kontaktbeginn und weitere
Annäherung; gehaltene Formgröße und sichtbares Ausfaden nach Kontaktverlust;
neuer Kontakt ohne alten Fortschritt; positiver Radius bei 6° Winkelfehler;
sofort grüne Platte, Kreis null und direkter Dissolve; Verriegelung bei
Poseänderung; beide Ausgänge nach 1 s transparent; unabhängiger zweiter Tisch;
Reaktivierung; Pulsstart und 180-ms-Abbruch; globale Welle auf inaktivem Tisch;
kein Erfolg bei ungültiger Pose. Physische Projektion und tatsächliche
Netzwerkausfälle sind damit nicht geprüft.

```python
p = '/Users/Johannes/dev/Promotion_Prototypen/AISI/td_builders/check_motion_acceptance.py'; exec(compile(open(p, encoding='utf-8').read(), p, 'exec'))
```

Johannes hat die Prüfung in der laufenden TD-Instanz ausgeführt:
`passed: true`, `check_count: 19`, `temporary_component_removed: true`,
`saved: false`. Alle 19 aufgeführten Zustands-/Pixelprüfungen bestehen.
Das umfasst insbesondere den positiven Navigationsradius bei 6° Winkelfehler,
den nicht abgeschnittenen grünen Kontaktverlust-Fade, die direkte grüne
Erfolgsfläche, beide vollständig transparenten Ausgänge nach dem Dissolve
und die unabhängige Navigation eines zweiten Tisches.

Diese synthetische TD-Abnahme ergänzt die qualitative Demo- und
Room-Editor-Bestätigung. Sie ersetzt weder den sichtbaren Netzwerk-Test
über „Übertragung pausieren“/„Übertragung fortsetzen“ noch eine physische
Prüfung. Johannes hat danach alle drei sichtbaren Punkte ausdrücklich bestätigt:
Timeout nach 0,5 s, Fortsetzung ohne neue Welle und genau eine neue Welle nur
bei „Vorschlag aktivieren“.

### Mehrtisch-Simulation — Drei- und Fünftisch-Prüfung bestätigt

`make_scenario()` im bestehenden Simulationsmodul enthält deterministische
Testposen. Studien-Trials und Lernformatvorlagen werden nicht geändert.

- Drei Tische: `table_0` von `(100,110,90°)` nach `(100,370,90°)`;
  `table_1` von `(250,110,70°)` nach `(250,370,90°)`;
  `table_2` bleibt bei `(400,250,90°)`. Die ersten beiden sind aktiv,
  der dritte erhält ausschließlich die gemeinsame Reveal-Welle.
- Fünf Tische: vier aktive Tische und ein unveränderter Tisch. Diese
  Kapazitätsstichprobe hat bereits überlappende eigene Source-/Target-Flächen.
  Source-/Ziel-Endzustände verschiedener Tische und sämtliche Mischungen
  abgeschlossener/unabgeschlossener Tische sind mit kanonischen Polygonen
  offline auf ROI und Kollisionsfreiheit geprüft. Freies Ziehen beliebiger
  Zwischenposen ist damit nicht als kollisionsfreie Bewegung geplant.
- OSC-IDs und zugehörige Targets bleiben bei umgekehrter Scene Order erhalten.
  Ein einzelner Abschluss verändert den zweiten aktiven Tisch nicht.
  Entfernte Tische bleiben trotz alter Empfangskanäle keine aktuelle Belegung.

Der TD-Launcher nutzt für drei Tische
`/private/tmp/aisi-motion-sim/multitable_3.json`; die alte Einzel-Tisch-Datei
bleibt erhalten. Beim ersten Wechsel blieb der alte Einzel-Tisch-Prozess
sichtbar. Der Launcher startet jetzt bei anderem Count ausschließlich den
im Motion-COMP gespeicherten Prozess neu, sofern dessen Programm und
Modul eindeutig dem Motion-Simulator entsprechen. Bei gleichem Count wird
die Instanz weiterverwendet; unbekannte Prozesse werden nicht beendet.
Drei fokussierte Launcher-Tests bestehen. Für eine spätere Fünftisch-Prüfung
kann direkt nach dem Laden des Launchers
`print(start(op, table_count=5))` im Textport ausgeführt werden.

Sichtbare Prüffolge: Reveal auf allen drei Tischen beobachten; `table_0`
auswählen und „Auf Zielpose“ betätigen. Danach muss dessen Content verschwinden,
während `table_1` weiter navigiert. Anschließend `table_1` auswählen und
abschließen; `table_2` bleibt ohne Navigationsgrafik. Kein Abschluss darf
eine neue Welle auslösen.

## Nächster Arbeitsschritt und Abnahme

Johannes meldet in der Dreitisch-Ansicht zwei grüne Feedbackformen, die trotz
Annäherung im Anfangszustand bleiben. Offline ist eine Referenzabweichung
reproduziert und im Quelltext korrigiert: Reaktivierung nach Abschluss darf
die separate Kontakt-Historie nicht zurücksetzen; sie läuft auch während
Dissolve/Completed weiter. Zwei neue Regressionstests sichern fortbestehenden
Kontakt und Kontaktverlust während des Dissolves ab. Die Navigationswerte
nach Reaktivierung stimmen im nachgespielten Fall mit `model.ts` und
`visual.ts` der Referenz überein. Alle 31 Motion-Tests bestehen.

Vor dem Laden der Korrektur las `inspect_motion_feedback.py` ohne Cook oder Schreibzugriff die aktuellen
Posen, Tisch-IDs, Kontakt-Baselines, Phasen und Fortschrittswerte aus. Die
Abfrage von Johannes bestätigt frische Daten für alle drei IDs:
`table_0` hat Baseline 0,6200 und Fortschritt 0,8333, also Navigation 0,5614;
`table_1` hat Baseline 0,9725 über Fortschritt 0,9167 und `table_2` Baseline
0,8854 über Fortschritt 0,7492. Die beiden letzteren bleiben deshalb bei
Navigation/Halo 0. Alle befinden sich in Guidance mit Kontakt; Erfolg-Anker
sind bereits gelöscht. Die Abfrage belegt die unmittelbare Ursache, kann
aber die vorherige Folge aus Kontakt, Aktivierung und Abschluss nicht
rekonstruieren. Insbesondere beginnt der unveränderte dritte Tisch bereits auf
seinem Ziel: Kontakt-Baseline 1 ist auch in der Referenz möglich und muss von
einem irrtümlichen Reset nach einem zuvor durchgeführten Anlauf unterschieden
werden. Dafür keine neue Fortschrittsformel einführen.

Zum Laden dient der bestehende `connect_motion_sim_preview.py`; dieser setzt
ausschließlich die eigene Motion-/Empfangshistorie zurück. Danach betroffene
Tische vollständig von ihrer Zielkontur wegziehen und wieder annähern, ohne
zwischendurch einen neuen Vorschlag zu aktivieren. Das erzeugt einen neuen
geometrischen Erstkontakt statt einer erfundenen rückwirkenden Baseline.
`check_motion_acceptance.py` enthält jetzt 22 statt 19 Prüfungen; die drei
zusätzlichen TD-Prüfungen betreffen fortbestehenden Kontakt bei Reaktivierung
und Kontaktverlust/-wiedereintritt während/nach Dissolve. Diese aktualisierte
TD-Abnahme ist inzwischen durch Johannes ausgeführt: alle 22 Prüfungen
bestanden, temporärer COMP entfernt und nichts gespeichert. Johannes
bestätigt korrekt wachsendes Grün bei allen drei Tischen sowie erhaltenen
Fortschritt nach Abschluss und erneutem Verdrehen. Damit ist die Korrektur
im laufenden Preview nachgewiesen, keine physische Raumprüfung.

Aufbau, Diagnose, sichtbare Demo, Simulationsreaktion, die 22 synthetischen
TD-Grenzfallprüfungen sowie Pause/Fortsetzung/Neuaktivierung sind bestätigt.
Das Dreitisch-Feedback samt Reaktivierung ist sichtbar bestätigt.
Die anschließende Fünftisch-Kapazitätsprüfung mit vier unabhängigen
Abschlüssen und einem unveränderten Tisch wurde durch Johannes ausgeführt.
Dazu den bestehenden Launcher
laden und `print(start(op, table_count=5))` ausführen. Dieser ersetzt
ausschließlich den zugeordneten Dreitisch-Simulator; der neue Session-Zähler
startet eine eigene Vorschau-Historie. Beim unveränderten Tisch
`table_2` muss die gemeinsame Reveal-Welle erscheinen, anschließend kein
Navigationscontent. Die vier aktiven Tische nacheinander über „Auf Zielpose“
abschließen; jeder Abschluss darf nur den eigenen Content entfernen und
keine neue Welle starten. Johannes bestätigt alle fünf sichtbaren Tische,
Reveal und unabhängige Abschlüsse wie beschrieben. Die Startausgabe bestätigt
den Wechsel von PID 89229 (drei Tische) auf PID 91706 (fünf Tische), eigene
Szenendatei `multitable_5.json`, keine TD-Projektspeicherung.

Johannes stellt klar: Auf diesem Mac gibt es keine echten Trackingdaten.
Kamera-/Live-Abnahme wird deshalb nicht aus Simulation abgeleitet. Als
nächster lokaler Schritt wird der Anschluss an die bestehende
Content-Umschaltung mit Simulationsdaten vorbereitet. Der neue Helfer
`inspect_motion_routing.py` liest dafür aktuelle Inputs/Outputs,
Select-/Switch-Parameter, Masken und einen vorgelagerten Verbindungsschritt.
Er erzwingt keine Cooks und ändert keine Operatoren. Johannes hat die Abfrage
ausgeführt: `mask_tabletop` ist ein Composite TOP mit Multiply, Eingang 0
`null_tabletop`, Eingang 1 `null_table_mask`. Floor läuft durch den vorhandenen
optionalen Chair-Zweig, die drei Ausgabe-Switches schalten unverändert über
`panel_mode` auf Kalibrierung. Aktueller `study/mode` ist 2 (AISI).

### Isolierte Routing-Vorprüfung — in TD bestanden

Die Motion-Simulation verwendet eigene Source-Posen. Die bestehende
Tabletop-Maske folgt weiterhin dem alten Tischdatenpfad. Deshalb darf deren
räumliche Deckung mit der neuen Simulation nicht vorausgesetzt werden.
Die bestehende Maskierung wird weder umgestellt noch durch eine neue
Produktionsmaske ersetzt.

`build_motion_routing_preview.py` erzeugt ausschließlich
`/project1/comp_aisi_motion_routing_preview` (Container COMP), anfänglich
deaktiviert. Zwei Select TOPs lesen die bisherigen endgültigen Floor-/Tabletop-
Quellen, zwei weitere die neuen Motion-Ausgänge. Der Motion-Tabletop-Zweig
verwendet eine Kopie des vorhandenen Multiply-Operators mit unveränderter
Input-Reihenfolge und einem Select auf die bestehende Maske. Der Floor-Zweig
kopiert die vorhandene Chair-Komposition und folgt deren bestehendem
Enable-Schalter. Originalknoten und deren Verbindungen bleiben unverändert;
der neue COMP wird nicht mit Projektoren oder Ausgabe-Selects verbunden.

Der lokale Schalter `Enablemotion` wird nur bei `study/mode == 2` wirksam;
fehlender Modus, Tracking und Study wählen den bisherigen Content. Vor dem
Kopieren werden aktuelle Masken-/Chair-Verbindungen geprüft. Dynamische
Composite-Parameter führen grundsätzlich zum Abbruch, damit relative Ausdrücke
oder Exports nicht versehentlich anders ausgewertet werden. Einzige Ausnahme:
Expressions für `resolutionw`/`resolutionh` werden in der Kopie durch absolute
Referenzen auf die ausgewerteten Originalparameter ersetzt. Originalausdrücke
bleiben unverändert; Auflösungsänderungen werden weiterhin übernommen.
Exports und Bindings bleiben auch für diese Parameter gesperrt. Bei Aufbaufehlern
wird nur der neue COMP entfernt. Sieben fokussierte Offline-Tests prüfen
Modusfälle, Preflight, getrennte Verbindungen und Rollback; Python-3.9-Syntax
der neuen TD-Helfer ist geprüft.

Johannes' erster Aufbauversuch brach in der Vorprüfung wegen der dynamischen
Chair-Parameter `resolutionw` und `resolutionh` ab, noch vor Erzeugung des
Prüfzweigs. Der anschließende Checker meldete deshalb erwartungsgemäß einen
fehlenden COMP. Die oben beschriebene explizite Auflösungsreferenz korrigiert
diese zu strenge Vorprüfung; die erneute Ausführung in TD ist bestanden. Tests
prüfen auch weitergereichte Auflösungsänderungen und unveränderte
Originalausdrücke. Die TD-Prüfung vergleicht zusätzlich beide
Auflösungsparameter der Kopien mit den Originalen.

```python
p = '/Users/Johannes/dev/Promotion_Prototypen/AISI/td_builders/build_motion_routing_preview.py'; exec(compile(open(p, encoding='utf-8').read(), p, 'exec'))
p = '/Users/Johannes/dev/Promotion_Prototypen/AISI/td_builders/check_motion_routing_preview.py'; exec(compile(open(p, encoding='utf-8').read(), p, 'exec'))
```

Die TD-Prüfung vergleicht im deaktivierten Prüfzweig Bildgröße und Pixelhash
mit den bisherigen Quellen, prüft Maskenreihenfolge, aktuelle Moduswahl,
fehlerfreies Kochen und Chair-Auswahl. Sie stellt den lokalen Enable-Wert
wieder her. Änderungen am globalen Modus oder an bestehenden Ausgabewegen
nimmt sie nicht vor. Johannes hat Aufbau und Prüfung erfolgreich ausgeführt:
alle sieben TD-Prüfungen bestehen, deaktiviert sind beide Ausgänge pixelgleich,
die Kopien übernehmen korrekte Auflösungswerte und die Chair-Auswahl folgt
dem Original. `production_outputs_changed: false`, `saved: false`,
`local_enable_restored: true`. Globale Study-/Tracking-Bildvergleiche sind
damit nicht ersetzt. Wegen unterschiedlicher Posen kann
das Motion-Bild im Prüfzweig an der alten Maske abgeschnitten erscheinen;
das ist noch kein Nachweis einer fehlerhaften Maske. Nächster Schritt nach
der technischen TD-Prüfung ist die gemeinsame Posequelle für Content und
bestehende Maske, bevor ein produktiver Anschluss aktiviert wird.

Der neue reine Lesehelfer `inspect_motion_mask_alignment.py` erfasst dazu
die vorhandene aktive Tischliste, Source-/Target-Parameter der bis zu fünf
Instanzen, Maskenrenderer und Kamera. Für die erste Instanz werden außerdem
Source-/Target-/Maskentransformationen und Grenzen der gerenderten SOP-Punkte
ausgelesen. So lassen sich Achsen und Maße anhand der tatsächlichen Geometrie
zuordnen. Es gibt keinen erzwungenen Cook und keine Änderungen. Johannes hat
die Ausgabe übermittelt. Sie bestätigt fünf Rect-Zeilen mit Legacy-Slots 0–4,
Source-/Target-Paaren und unveränderter orthografischer Kamera (Breite 2,6).
Die Source-Kontur hat lokale Maße 150 × 70 cm, die Zielkontur 170 × 90 cm;
das sind Gestaltungskonturen, keine neuen Maße für das kanonische Rect.
Die untersuchte Instanzmaske hat lokale Grenzen ±1 TD-Einheit, ist aber
überhaupt nicht in der aktiven Masken-Geometrieliste enthalten.

Der Maskenrenderer referenziert tatsächlich die sechs
`comp_study_visualization/rect_setup_mask_geo_00` bis `05`, jeweils doppelt.
Im Repository erzeugt `study_setup_masks.py` diese als Vision-Occupancy-
Masken; ihre tatsächlichen Transformationen im laufenden Graph waren im
Bericht noch nicht enthalten. Aus Namen allein wird keine Fehlfunktion
abgeleitet. Weder Liste noch geschützte Geometrien werden bereinigt.

### Statischer Poseabgleich mit der aktiven Maske — in TD bestanden

`build_motion_aligned_snapshot.py` liest unmittelbar die tatsächlich vom
Maskenrenderer referenzierten Geometrien. Er prüft deren sichtbare Slotmenge,
Translation, axiale Rotation, Skalierung und Neigung gegen `tables_active`.
Bestehende Source-/Target-Posen werden nicht geändert. Doppelte Maskenreferenzen
werden nur für die Prüfung zusammengefasst und im Bericht gezählt; die
Originalauswahl bleibt unverändert. Bei abweichenden Posen meldet der Helfer
die tatsächlichen Werte und legt nichts an.

Johannes' erster Versuch meldete Abweichungen für alle fünf Slots und legte
korrekt nichts an. Die tatsächlichen Differenzen sind jedoch sehr klein:
maximal 0,046001 cm Translation und 0,017014° axiale Rotation. Die bisherige
Gleichheitsprüfung war für die getrennten gespeicherten Werte zu streng.
Ihre zeitliche Entstehung ist nicht nachgewiesen; daraus keine Live-Aktualität
ableiten.

Die Slot-Zuordnung wird jetzt mit dem Rastermaß geprüft: ein Pixel über dem
500-cm-ROI, also 0,25 cm bei 2000 Pixeln. Die konservative obere Schranke
`Translation + 2 × halbe Tischdiagonale × sin(Winkelfehler / 2)` muss innerhalb
dieses Pixels liegen. Tischmaße kommen aus der gemeinsamen Motion-/Geometrie-
Implementierung. Das ist ausschließlich ein Zuordnungskriterium für die
statische Probe, keine Änderung der Erfolgs- oder Trackingtoleranzen.
Skalierung, Neigung, Slotmenge und Sichtbarkeit werden weiterhin geprüft.

Nur bei erfolgreichem rasterbezogenem Abgleich erzeugt der vorhandene Motion-Builder
einen separaten `comp_aisi_motion_aligned_snapshot` (Container COMP), gespeist
aus den **exakten eingefrorenen Maskenposen** als Sources und den unveränderten
Legacy-Targets desselben Slots. So bleibt zwischen Masken- und Content-Source
keine tolerierte Restabweichung innerhalb der Probe. Die bestehende Umrechnung
`td_pose` wird wiederverwendet. Kameraabbildung und quadratisches Raster
werden vorher geprüft. Die Original-Simulation, Routing-Selects und
Produktionsausgaben bleiben unverändert; nichts wird gespeichert.

Die Schlüssel `legacy_slot_0` usw. bezeichnen ausschließlich diesen Snapshot.
Sie ersetzen keine echten Tracking-IDs. Aktualität, kontinuierliches Tracking
und geometrische Maskenform sind durch den Posevergleich nicht nachgewiesen.
Zehn fokussierte Offline-Tests bestehen: bekannte Koordinaten, Paarung bei
anderer Reihenfolge, ungültige Zeilen, Sichtbarkeit, Pose-/Skalenabweichungen,
axiale Symmetrie und Abbruch ohne Erzeugung bei Fehlzuordnung. Hinzu kommen
die fünf tatsächlich gemeldeten Posen, exakte Übernahme der Masken-Sources
bei unveränderten Targets, kombinierter Rotations-/Translationsversatz,
ungültige Pixelbudgets und Preflight mit tatsächlichem Renderer-Raster.
Python-3.9-Syntax ist geprüft. Johannes hat den erneuten Aufbau erfolgreich
ausgeführt: `pose_alignment_passed: true`, keine Probleme, Snapshot bei
2000 × 2000, exakt übernommene Masken-Sources und unveränderte Legacy-Targets.
Maximaler konservativer Randversatz zur alten Source-Liste: 0,049122 cm,
Zuordnungsbudget 0,25 cm. Keine alten Knoten oder Routing geändert, nichts
gespeichert. Die Maskenform bleibt separat zu prüfen.

```python
p = '/Users/Johannes/dev/Promotion_Prototypen/AISI/td_builders/build_motion_aligned_snapshot.py'; exec(compile(open(p, encoding='utf-8').read(), p, 'exec'))
```

### Pixelprobe und statischer Routing-Anschluss — in TD bestanden

`check_motion_aligned_routing.py` prüft zuerst, ob der Snapshot noch zu den
aktuellen Maskenposen gehört. Eine temporäre GLSL-Probe verwendet die Kontur-
und Koordinatenfunktionen aus dem eingebetteten Motion-Shader, rendert aber
alle gültigen Source-Flächen weiß, unabhängig von Reveal, Navigation und
Abschluss. Eine temporäre Kopie der bestehenden Masken-Komposition
multipliziert diese Fläche mit der unveränderten Maske. Ein temporärer Select
TOP im Snapshot-Netzwerk liest die externe Maskenquelle per absolutem Pfad;
beide Composite-Eingänge bleiben dadurch im selben Netzwerk. Alle Probe-Knoten
liegen unter dem neuen Snapshot-COMP und werden anschließend entfernt.

Der Bericht misst den erhaltenen Anteil der nominalen Tisch-Innenfläche,
Maskenfläche außerhalb der nominalen Kontur und helles RGB außerhalb der
bestehenden Maske. Der erhaltene Anteil wird ausdrücklich berichtet, nicht
als geometrische oder physische Freigabe interpretiert. Ein absichtlicher
Masken-Inset kann Beschneidung ergeben. Leere oder unterschiedliche Raster,
fehlender Durchlass und RGB-Leckage führen zum Abbruch.

Bei bestandener technischer Prüfung werden nur `floor_motion` und
`tabletop_motion` (Select TOP) im isolierten Routing-COMP auf die Snapshot-
Ausgänge gestellt und dessen lokaler Schalter aktiviert. Andere lokale
Quelländerungen werden nicht überschrieben. Vorherige Werte werden im eigenen
COMP hinterlegt und bei Fehlern sofort wiederhergestellt. Produktions-
Selects, Projektoren, Masken und Simulation werden nicht verändert, nichts
gespeichert. Die Modussperre gilt weiter; AISI muss bereits aktiv sein.

Elf fokussierte Offline-Tests bestehen: Durchlass, Formbeschnitt, RGB-
Leckage, ungültige Raster, Shader-Ableitung und lokaler Rollback sowie
nebenwirkungsfreier Import beider Helfer bei vorhandenem TD-`op` und
weiterhin funktionierender Textport-Start, lokaler Select statt
netzwerkübergreifendem TOP-Kabel sowie Verbindungsprüfung vor dem Cook. Der
abgeleitete Shader kompiliert und linkt auf dem macOS Apple Software Renderer.
Die Offline-Kompilation ersetzt keine TD- oder Raumabnahme; der folgende
Absatz dokumentiert den späteren TD-Nachweis. Die visuelle Prüfung steht aus.

Der erste TD-Aufruf scheiterte noch vor der Pixelprobe mit „project1 fehlt
oder Snapshot existiert“. Ursache war ein versehentlicher zweiter Builder-
Aufruf beim Import von `build_motion_aligned_snapshot`: Der ursprüngliche
Einstieg prüfte lediglich, ob TD-`op` verfügbar war. Die Einstiegspunkte
beider Helfer prüfen nun zusätzlich, dass kein regulärer Python-Importspec
vorliegt. Ein Import definiert damit ausschließlich Funktionen, während
der manuelle Textport-`exec` den jeweiligen Einstieg weiter ausführt.
Keine Prüfung wurde ausgeführt, kein vorhandener Snapshot geändert;
lokales Routing wurde wiederhergestellt, keine Probe blieb zurück.
Wiederholung nur des Checkers mit dem vorhandenen Snapshot steht aus.

Johannes' folgende Nachricht enthält zunächst nochmals den Importfehler und
danach einen weiterlaufenden Versuch: Beide Poseprüfungen sind bestanden,
doch `alignment_probe_masked` meldet „Not enough sources specified“.
Ursache im Checker war der direkte Anschluss von `mask_existing` aus dem
Routing-COMP an die Probe im Snapshot-COMP. Dieser Anschluss ist jetzt durch
den oben beschriebenen lokalen Select TOP ersetzt; vor dem Cook wird die
vollständige Input-Liste geprüft. Zwei neue Regressionstests bilden die
Netzwerkgrenze und einen fehlgeschlagenen Anschluss ab. Die Probe-Knoten
wurden nach dem Fehler entfernt und das lokale Routing wiederhergestellt;
keine produktiven Ausgaben geändert. Die anschließende Wiederholung ist
inzwischen bestanden:

- `passed: true`, alle sieben aufgeführten Prüfungen bestanden;
- Raster 2000 × 2000, 1.010.626 nominale Innenpixel geprüft;
- `interior_retained_fraction: 1.0`: alle geprüften Innenpixel bleiben über
  der Helligkeitsschwelle, keine Aussage über identische Kanten-Antialiasingwerte;
- `lit_pixels_outside_mask: 0`;
- 2024 Maskenpixel außerhalb der nominalen Kontur und 1.018.806 helle Pixel
  in der maskierten Probe; Rand-/Formursachen nicht separat aufgelöst;
- lokale Snapshot-Vorschau aktiviert, temporäre Proben entfernt;
- keine produktiven Ausgaben geändert, nichts gespeichert, keine Raumprüfung.

Nur im isolierten Routing-COMP verweisen `floor_motion` und `tabletop_motion`
jetzt auf den statischen Snapshot. Johannes hat beide Ausgänge
`out_floor` und `out_tabletop` (jeweils Out TOP) im Operator-Viewer gezeigt.
Die Screenshot-Prüfung ergibt eine plausible statische Darstellung: Floor-
Zielreste außerhalb der Source-Flächen, am Tabletop vier grüne Kontaktanzeigen
und unten ein Navigationskreis ohne Grün. Die geraden weißen Schnittkanten
entsprechen der geometrischen Source-/Target-Überlappung. Der Pfeil ist eine
Aussparung im weißen Kreis und erscheint daher auf grünem Untergrund grün,
auf unbeleuchtetem Untergrund schwarz. Keine neue technische Abweichung ist
anhand dieser Bilder erkennbar; daraus keine Labor-/Projektionsfreigabe
oder Freigabe aller Bewegungsfälle ableiten. Die Probe enthält eingefrorene Posen;
Änderungen im separaten Room Editor bewegen diesen Snapshot nicht.
Zum Zurückschalten des lokalen Prüfzweigs genügt
`op('/project1/comp_aisi_motion_routing_preview').par.Enablemotion = False`.
Die bestehenden Produktionsausgaben wurden auch beim Aktivieren nicht umgestellt.

Der lokale statische Maskendurchlass ist damit technisch und anhand der beiden
Screenshots geprüft. Die spätere Beanstandung von Johannes begrenzt diese
Aussage ausdrücklich: Grünes Wachstum und Zentrierung sind durch diese
statischen Bilder nicht nachgewiesen. Es wurde weiterhin keine `.toe` gespeichert. Den
aktuellen Stand manuell über „Save As“ als neue benannte Arbeitskopie sichern,
beispielsweise `AISI_motion_v1_5_preview_validated.toe`; keine vorhandene
Datei überschreiben. Dieser Hinweis ist keine Behauptung einer erfolgten
Speicherung. Die unten beschriebene dynamische maskierte Prüfung wurde
anschließend bestätigt. Als Nächstes echte Trackingdaten, explizite
Layoutaktivierung und stabile Source-/Target-Identität anbinden; produktiven
Anschluss, Moduserhalt und Raumabnahme separat prüfen.

### Korrektur der statischen Sichtbewertung und dynamischer Maskentest

Johannes beanstandet vier identische grüne Anfangsformen und fehlende
Zentrierung beim nahen Tisch. Ursache des Prüfaufbaus: Der eingefrorene
Snapshot initialisiert jede Kontakt-Baseline mit dem bereits aktuellen
Fortschritt. Damit ist `A = (P − P0)/(1 − P0) = 0` für alle erstmals
eingelesenen Kontaktposen. Die identischen Formen sind kein Beleg einer
korrekten Fortschrittsanzeige. Die vorige optische Plausibilitätsbewertung
war insoweit zu weitgehend; ihre Masken-/Pixelnachweise bleiben gültig.
Keine Annäherungsgeschichte erfinden und keine Baseline aus der bloßen
aktuellen Zieldistanz rückrechnen.

`build_motion_dynamic_mask_preview.py` erzeugt deshalb ausschließlich einen
neuen `comp_aisi_motion_dynamic_mask_preview` (Container COMP). Content
und Maskenkopien lesen denselben fortlaufenden Float-State der ursprünglichen
Room-Editor-Komponente `comp_aisi_motion_v1_5`. Fünf Kopien der vorhandenen
Maskengeometrie behalten ihre Select-SOP-Fläche; relative Quellen werden vor
dem Kopieren absolut aufgelöst. Nur die Transformationen der Kopien folgen
dem State. `motion_sim_mask.py` bildet die inverse bestehende `td_pose`-
Schnittstelle ab; ungültige, entfernte oder veraltete Source-Zeilen blenden
die Maskenkopie aus. Auch abgeschlossene/inaktive gültige Tische behalten
ihre räumliche Maske für die globale Welle.

Maskenrenderer, Reorder und Multiply werden in denselben neuen COMP kopiert.
Kamera/Lichter/Materialien werden auf die Originalreferenzen aufgelöst;
alle Kabel bleiben lokal. Der Floor-Ausgang zeigt ausschließlich den
Motion-Simulationscontent, ohne die alten, anders positionierten Chairs.
Der alte Chair-Zweig bleibt erhalten. Die vorhandene statische Probe und
das alte Routing werden nicht umgestellt. Originalmasken, Kalibrierung,
Study-/Tracking-Pfade und Produktionsoutputs werden nicht verändert.

Sechs fokussierte Offline-Tests bestehen: inverse Poseabbildung, fortlaufende
Transformation auch nach Abschluss, Ausblenden bei ungültigen/stalen Daten,
absolut aufgelöste OP-Referenzen, unabhängige Tischfortschritte und der
reproduzierte Unterschied zwischen statischer Endpose (`A = 0`) und echter
Annäherung zur selben Pose (`A > 0,9`). Die Motion-Zustandsformel und der
Shader wurden nicht geändert. Python-3.9-Syntax ist geprüft. Johannes hat
Aufbau und sichtbaren Bewegungsablauf anschließend erfolgreich ausgeführt
und bestätigt ausdrücklich „jetzt ist es richtig“. Der Screenshot zeigt
unabhängigen Fortschritt: Rechts unten hat sich das Grün groß und annähernd
zentriert ausgedehnt, der Navigationskreis ist klein; die anderen aktiven
Tische behalten ihre eigene Anfangsform.

Die TD-Ausgabe bestätigt fünf frische Tisch-IDs `table_0` bis `table_4`,
keine Änderungen an Originalknoten/Produktionsoutputs und keine Speicherung.
Maskenrenderer, Reorder, Multiply und Tabletop-Out kochen fehlerfrei bei
2000 × 2000, Floor-Out bei 1000 × 1000. Aufgelöste gemeinsame Maskenfläche:
`/project1/comp_study_visualization/rect_tabletop_inner_geo/table_surface`.
Damit ist das dynamische maskierte Feedback in Simulation sichtbar bestätigt.
Reale Tracking-Aktualität, Projektionsleistung und Raumkorrektheit sind nicht
nachgewiesen. Die frühere statische Pixelprüfung und diese dynamische
Bestätigung bleiben getrennte Nachweise.

```python
p = '/Users/Johannes/dev/Promotion_Prototypen/AISI/td_builders/build_motion_dynamic_mask_preview.py'; exec(compile(open(p, encoding='utf-8').read(), p, 'exec'))
op('/project1/comp_aisi_motion_dynamic_mask_preview/out_tabletop').openViewer(unique=True)
```

Prüffolge im bestehenden Fünftisch-Room-Editor: mit `R` auf Ausgangsposen
zurücksetzen und einmal „Vorschlag aktivieren“. `table_4` unten rechts von
seinem Ziel nach rechts wegziehen, bis kein Kontakt mehr besteht. Danach
langsam zum Ziel zurückführen: ab Kontakt zunächst Anfangsform, bei weiterer
Annäherung größer und zunehmend um den Navigationskreis zentriert; dieser
wird kleiner. Ein anderer Tisch muss seinen eigenen Fortschritt behalten.
Während der Annäherung nicht erneut den Vorschlag aktivieren.

### Neuer Auftrag: produktive Umschaltung vor dem Laboranschluss

Johannes beauftragt ausdrücklich die Einbindung in die produktive
Ausgabekette bereits jetzt, bei Erhalt der bestehenden Maskierung und
Kalibrierung. Dies zieht die technische Umschaltung vor den noch offenen
echten Trackinganschluss; eine aktive reale Projektion wird damit nicht
als geprüft freigegeben. Die neue Umschaltung soll zunächst deaktiviert
bleiben und den bisherigen Content durchlassen.

Bevor produktive Verbindungen geändert werden, liest der erweiterte
`inspect_motion_routing.py` zusätzlich die Floor-Chair-Auswahl,
deren Basis-Select und das unmaskierte Tabletop aus. Die angestrebten
Einfügepunkte liegen vor der unveränderten Tabletop-Multiply-Maske und
vor der bestehenden Chair-Komposition. Die konkrete Verdrahtung wird
am aktuellen laufenden Graph geprüft, nicht aus älteren Buildern abgeleitet.
Die anschließende Installation und ihr Prüfer sind unten dokumentiert;
die aktive neue Quelle ist dabei weiterhin ausgeschaltet.

```python
p = '/Users/Johannes/dev/Promotion_Prototypen/AISI/td_builders/inspect_motion_routing.py'; exec(compile(open(p, encoding='utf-8').read(), p, 'exec'))
```

#### Produktive Einbindung installiert und Bypass geprüft

Johannes' aktueller Graph bestätigt:

- `select_floor_for_synth_chairs` (Select TOP) liest bislang
  `/project1/comp_output/select_floor`; sein Bild geht sowohl direkt in die
  Chair-Umschaltung als auch in die additive Chair-Komposition.
- `null_tabletop` (Null TOP) liest `render_tabletop` (Render TOP). Erst danach
  multipliziert `mask_tabletop` (Composite TOP) mit `null_table_mask` (Null TOP).
- Die Floor-/Tabletop-/Masken-Ausgabeschalter und ihre Kalibrierungszweige
  folgen unverändert hinter diesen Pfaden.

`build_motion_output_routing.py` erstellt
`/project1/comp_aisi_motion_output_routing` mit zwei lokalen Content-Schaltern
und einer neuen Select-TOP-Brücke im Layout. Genau zwei bestehende Stellen
werden geändert: Der Floor-Basis-Select liest den neuen Floor-Ausgang, und
`null_tabletop` liest über die lokale Brücke den neuen Tabletop-Ausgang.
Die Legacy-Eingänge des neuen Routers lesen die zuvor verwendeten Produzenten,
nicht ihre neu angeschlossenen Verbraucher; dadurch entsteht kein Rückkopplungspfad.
Die ursprüngliche Tabletop-Maske mit beiden Eingängen/Reihenfolge bleibt
vollständig erhalten. Es wird keine Ersatzmaske/-Chair-Komposition eingeführt.

`Enablemotion` und `Sourceapproved` starten beide ausgeschaltet. Motion wird
nur bei beiden Schaltern an, AISI-Modus (`study/mode == 2`) und beiden
Kalibrierungspanels aus ausgewählt. Ein unbekannter/fehlender Modus bleibt
auf Legacy. `Sourceapproved` ist eine manuelle Konfiguration für den späteren
nachgewiesenen Quellen-/Maskenabgleich, kein automatischer Trackingnachweis.
Die Simulationsquelle ist durch die Installation ausdrücklich nicht freigegeben.
Beide neuen Motion-Eingänge werden vor dem vorhandenen Masken-/Projektorpfad
auf die jeweilige Legacy-Auflösung gebracht. Die Ausdrücke der Umschaltung
haben eine explizite Frame-Abhängigkeit.

Der Builder prüft den vorgefundenen Graph, erstellt einen Snapshot aller
vorhandenen Parameter-/Eingangsverbindungen unter Layout, Output und Study-
Visualisierung und erlaubt danach ausschließlich die beiden genannten
Content-Änderungen. Text-DAT-Code wird zusätzlich per Hash verglichen.
Bei ausgeschaltetem Motion müssen Floor-, Tabletop- und Masken-Ausgabebild
vor/nach Einbau pixelgleich sein. Fehler führen zum Rückbau; bei Fehlern
während des Rückbaus werden die neuen Knoten zur Wiederherstellung erhalten
und der unvollständige Rückbau ausdrücklich gemeldet. Nichts wird gespeichert.

Zehn Offline-Tests bestehen: Einbau mit Bypass/Maskenerhalt, alle relevanten
Flag-/Modus-/Kalibrierungskombinationen, Rückbau, Fehler nach Neuverdrahtung,
abweichende Ausgangsgraphen, wiederholter Einbau, Erhalt späterer lokaler
Änderungen und Python-3.9-Syntax. Modelltests ersetzen keine TD-Pixelprüfung.
Johannes hat Installation und Prüfer im laufenden TD anschließend bestanden:
`installed: true`, drei pixelgleiche Ausgabebilder beim Einbau, geschützter
Graph verifiziert. Nur `select_floor_for_synth_chairs` und `null_tabletop`
wurden an den vorgesehenen Content-Stellen umverbunden. Originalmaske,
Chair-Komposition, Kalibrierung und Projektortransforms bleiben erhalten.
Der separate Prüfer besteht mit allen sieben Kriterien: zwei strukturelle
Nachweise, je Oberfläche Pixelgleichheit und Originalauflösung sowie
fehlerfreie zentrale Ausgabeschalter. Motion und Quellenfreigabe bleiben
aus, `active_motion_output_tested: false`, nichts gespeichert und keine
physische Validierung. Die technische Einbindung ist damit installiert;
ein aktiver neuer Projektionsinhalt ist daraus nicht als geprüft abzuleiten.

```python
p = '/Users/Johannes/dev/Promotion_Prototypen/AISI/td_builders/build_motion_output_routing.py'; exec(compile(open(p, encoding='utf-8').read(), p, 'exec'))
p = '/Users/Johannes/dev/Promotion_Prototypen/AISI/td_builders/check_motion_output_routing.py'; exec(compile(open(p, encoding='utf-8').read(), p, 'exec'))
```

Nur für einen ausdrücklich gewünschten Rückbau der neuen Einbindung:

```python
p = '/Users/Johannes/dev/Promotion_Prototypen/AISI/td_builders/remove_motion_output_routing.py'; exec(compile(open(p, encoding='utf-8').read(), p, 'exec'))
```

Der Prüfer aktiviert den neuen Content nicht. Er prüft den installierten
Bypass, unveränderte Originalknoten, Auflösungen und fehlerfreie zentrale
Ausgabeschalter. Spätere lokale Änderungen an neuen Routing-Knoten werden
vor Prüfung/Rückbau erkannt und nicht überschrieben. Eine aktive Ausgabe
der neuen Quelle, tatsächliche Modus-Bildvergleiche und Raumabnahme bleiben
separate Nachweise. Die `.toe`-Speicherung bleibt manuell.

#### Simulationstest durch die produktive Kette vorbereitet

Johannes möchte den neuen Content mit der Room-Editor-Simulation in der
produktiven Kette aktiv testen. Dafür müssen Tisch-Content und Maskenbild
dieselben simulierten Posen verwenden; die bisherigen gecachten Vision-Posen
sind hierfür ungeeignet. `motion_output_simulation_test.py` implementiert
einen temporären, getrennten `Simulationtest`-Schalter im installierten Router.
Die vorhandenen `Enablemotion`-/`Sourceapproved`-Freigaben bleiben aus.

Der Testschalter aktiviert gleichzeitig beide Motion-Content-Zweige und
eine neue Auswahl vor `null_table_mask` (Null TOP). Deren Legacy-Eingang
bleibt der bisherige `reorder_table_mask` (Reorder TOP); der Testeingang liest
`comp_aisi_motion_dynamic_mask_preview/reorder_simulation_mask` (Reorder TOP)
mit den bereits geprüften expliziten Frame-Bindungen an denselben Motion-State.
Es ändert sich vorübergehend nur der Bild-Eingang von `null_table_mask`.
Der originale Multiply-Maskenoperator, die Maskengeometrie/-parameter,
Floor-/Tabletop-Maskenreihenfolge und alle Kalibrierungs-/Projektorparameter
bleiben erhalten. Auch `select_table_mask` (Select TOP) erhält so das passende
Simulationsmaskenbild über seinen unveränderten bisherigen Quellpfad.
Die Chair-Komposition verwendet weiterhin ihre bisherige Datenquelle;
deren Zuordnung zu simulierten Tischen ist kein Nachweis dieses Tests.

Nur AISI und beide Kalibrierungspanels aus erlauben den Simulationstest.
Tracking, Study, Kalibrierung und unbekannte Modi bleiben auf Legacy-Content
und ursprünglichem Maskenbild. Die separate Quellenfreigabe für echtes
Tracking wird nicht gesetzt. Die Vorbereitung bleibt ausgeschaltet und
verlangt unverändertes Routing und korrekte Simulationsmasken-Bindungen.
Aktivierung folgt separat bei frischen, seit der Vorbereitung fortgeschrittenen
OSC-Frames; die blockierenden GPU-Abfragen gehören nicht in diesen Schritt.

Vor Aktivierung müssen die drei zentralen Ausgabebilder beim vorbereiteten,
noch ausgeschalteten Test pixelgleich bleiben. Danach werden unveränderte
Originalparameter/-verbindungen außerhalb der einen erlaubten zusätzlichen
Maskenbild-Verbindung, gemeinsame Content-/Maskenauswahl, fehlerfreie zentrale
Ausgaben sowie die aktive Maske geprüft. Das Tabletop-Bild durch die echte
Originalmaske wird gegen den geprüften dynamischen isolierten Prüfzweig
verglichen (maximal zwei RGBA8-Rundungsstufen Differenz). Beim Startfehler
wird der Test zurückgebaut; ein unvollständiger Rückbau wird ausdrücklich
gemeldet. Keine automatische Speicherung.

25 fokussierte Tests bestanden: zehn bestehende Produktionsrouting-Tests
und 15 Simulationstests einschließlich aktiver Pixelpfade, Schutz der
anderen Modi, veralteter Quelle, unveränderter Frame-Bindung, Rückbau nach
Pixelabweichung, vollständiger Wiederherstellung und Erhalt lokaler Änderungen.
Python-3.9-Syntax aller Testskripte geprüft. Aktivierung, Vergleich und
sichtbare Bewegung im laufenden TD sind noch auszuführen; kein Raumtest.

Vorbereitung, danach Aktivierung als neue Textport-Eingabe, separate
Pixelprüfung und Beenden:

```python
p = '/Users/Johannes/dev/Promotion_Prototypen/AISI/td_builders/start_motion_output_simulation_test.py'; exec(compile(open(p, encoding='utf-8').read(), p, 'exec'))
```

```python
p = '/Users/Johannes/dev/Promotion_Prototypen/AISI/td_builders/activate_motion_output_simulation_test.py'; exec(compile(open(p, encoding='utf-8').read(), p, 'exec'))
```

```python
p = '/Users/Johannes/dev/Promotion_Prototypen/AISI/td_builders/check_motion_output_simulation_test.py'; exec(compile(open(p, encoding='utf-8').read(), p, 'exec'))
```

```python
p = '/Users/Johannes/dev/Promotion_Prototypen/AISI/td_builders/stop_motion_output_simulation_test.py'; exec(compile(open(p, encoding='utf-8').read(), p, 'exec'))
```

Viewer sind jetzt `comp_output/switch_floor` und `comp_output/switch_tabletop`
(jeweils Switch TOP), also die vorhandenen produktiven zentralen Ausgaben.
Im Room Editor einmal Vorschlag aktivieren und danach Bewegung, Kontakt,
Mittelpunktdurchgang und unabhängigen Abschluss prüfen. Der Stop entfernt
nur die temporären Testknoten/-parameter, stellt den ursprünglichen
Maskenbild-Eingang und die zwei ursprünglichen Router-Ausdrücke wieder her
und führt den bisherigen deaktivierten Routing-Prüfer erneut aus. Der Test
ist vor Sicherung einer normalen Arbeitskopie zu beenden. Während des Tests
den eigenen Simulationsprüfer verwenden; der normale Router-Prüfer erkennt
die temporäre Erweiterung absichtlich als abweichenden lokalen Graph.

##### Erster Aktivierungsversuch ohne frische Simulationsframes

Johannes' erster Start bricht vor dem Erstellen/Umschalten der Testknoten
an `fresh == false` ab. Die anschließende Stop-Meldung „Kein registrierter
Simulationstest“ bestätigt, dass keine Testsitzung vorlag. Der Screenshot
von `comp_output/switch_floor` (Switch TOP) zeigt weiterhin die bisherige
Darstellung. Die zuvor bestandene produktive Installation/Bypass-Prüfung
bleibt erhalten; keine neue Aktivierungs- oder Raumabnahme ableiten.

Die Ursache ist damit noch nicht auf gestoppten/pausierten Sender oder
ausstehende Bestätigung fortschreitender Frames eingegrenzt.
`check_motion_simulation_source.py` liest den Zustand vor/nach einem Cook
des eigenen State-TOP, OSC-Empfängerparameter, rohe Session-/Frame-Metadaten
und den gespeicherten eigenen Sender-Prozesshandle aus. Er verändert keine
Produktionsverbindung oder Parameter und startet keinen Sender.

```python
op('/project1/comp_aisi_motion_v1_5/render_preview').openViewer(unique=True)
p = '/Users/Johannes/dev/Promotion_Prototypen/AISI/td_builders/check_motion_simulation_source.py'; exec(compile(open(p, encoding='utf-8').read(), p, 'exec'))
```

Der offene isolierte Viewer hält die zeitabhängige Quelle auch bei noch
deaktiviertem produktivem Routing im regulären Cook-Pfad. Erst die folgenden
Live-Metadaten belegen, ob tatsächlich neue Frames ankommen. Der Start gibt
bei fehlender Frische jetzt einen klaren Status inklusive Stream-Diagnose aus;
Stop ohne Sitzung prüft den unveränderten deaktivierten Router und meldet
„nichts geändert“. Die Textport-Wrapper laden das eigene Testmodul erneut,
damit Korrekturen im bereits laufenden TD wirksam werden. Der Launcher ist
beim normalen Modulimport nun ohne Start-Nebeneffekt, damit explizite
Fünftisch-Aufrufe nicht vorher versehentlich drei Tische starten.
21 fokussierte Routing-/Simulationstests und vier Launcher-Tests bestanden.
Die nach Öffnen des isolierten Previews direkt aufgerufene Diagnose
bestätigt anschließend frische Daten bereits vor und nach ihrem Cook:
Session 2548711, Frame 259368 → 259485, Revision 7, fünf IDs. Der Empfänger
ist aktiv auf Port 9000, eigener Sender PID 91706 läuft mit fünf Tischen.
Damit ist aktuell kein Senderneustart nötig. Die Ursache der anfänglichen
fehlenden Frische ist nicht abschließend isoliert. Aktive Umschaltung und
Bewegung durch die produktive Kette stehen noch aus; der direkte Modulaufruf
mit Reload umgeht die zuvor ohne Ausgabe gebliebene Textport-Startbedingung.

##### Korrektur des Startablaufs nach erneutem Timeout

Der nächste direkte Start meldet trotz zuvor nachgewiesen frischer Quelle
erneut `waiting for advancing frame / timeout` bei Frame 262645. Die
kombinierte Funktion führte umfangreiche GPU-Readbacks aus und kochte danach
den State im selben blockierten TD-Frame erneut. Ein gecachter OSC-CHOP-Wert
kann dadurch das 0,5-s-Zeitlimit überschreiten, obwohl der Sender läuft.
Diese Ursache folgt aus Ablauf und Symptomen; ein natives TD-Profilergebnis
liegt nicht vor.

`start` bereitet nun ausschließlich den deaktivierten Zweig samt drei
Bypass-Pixelprüfungen vor. Die registrierte Sitzung erhält Phase `prepared`,
TD-Framenummer und letzte Quellsignatur. `activate` muss in einem späteren
TD-Frame aufgerufen werden; es kocht zuerst den bestehenden OSC-In und Raw-
CHOP, dann den eigenen State. Es verlangt unverändert den 0,5-s-Frischetest
und eine neue Signatur. Nur dann werden Content und Simulationsmaske gemeinsam
aktiviert. Dieser leichte Schritt führt keine GPU-Digests/-Readbacks aus.
Die schwere aktive Pixelprüfung erfolgt separat über den Prüfer; bei einer
Pixelabweichung wird die unverändert registrierte Testsitzung zurückgebaut.
Zwischenzeitliche lokale Änderungen werden dabei weiter geschützt.

25 Routing-/Simulationstests bestanden, darunter neue Fälle für
Vorbereitung/Aktivierung in unterschiedlichen Frames, unveränderte
Quellsignatur trotz TD-Framefortschritt, keine GPU-Abfrage während Aktivierung
und Reihenfolge OSC-In → Raw-CHOP → State. Python-3.9-Syntax geprüft.
Die Textport-Wrapper erlauben den expliziten `p`-/`exec`-Aufruf auch bei
geerbtem `__spec__`, ohne beim normalen Modulimport automatisch zu laufen.
Die zweiphasige Aktivierung ist im laufenden TD erfolgreich ausgeführt:
Vorbereitung in Frame 1378043 mit drei Bypass-Pixelprüfungen, Aktivierung in
Frame 1379345 mit frischer Signatur (2548711, 279512), Revision 7 und fünf
Tisch-IDs. Floor-/Tabletop-Content und Simulationsmaske stehen jeweils auf
Index 1. Johannes bestätigt sichtbaren neuen Content. Die temporäre
Testsitzung ist derzeit aktiv; die reale Quelle ist weiterhin nicht
freigegeben. Die separate Prüfung über `output_test.verify(op)` hat alle
sechs Kriterien bestanden: Originalmaskenoperator erhalten, Kalibrierung,
Chair-Komposition und Projektorparameter unverändert, gemeinsame Modussteuerung,
drei zentrale Ausgabeschalter fehlerfrei, aktiver Maskeneingang pixelgleich
zur dynamischen Simulationsmaske sowie Tabletop durch die Originalmaske
pixelgleich zum dynamischen Prüfzweig (maximaler Pixelfehler 0,0).
Kontinuierliche Bewegung, Feedback und unabhängige Abschlüsse durch die
produktiven Ausgänge bleiben manuell zu bestätigen. Nichts gespeichert,
keine physische Validierung.

### Abschlussprüfung nach den visuellen Korrekturen

Nach Johannes' Freigabe des runden Grüns wird die deterministische
TD-Abnahme erweitert: Die bisherigen 22 Kriterien bleiben erhalten,
drei neue Formprüfungen bringen die Gesamtzahl auf 25. Am Ende der
Zustandsprüfungen verwendet ausschließlich die temporäre Prüfkomponente
einen Probe-Einstieg zur tatsächlichen GLSL-Funktion `feedbackHalo`, ohne
Tischbeschnitt. Geprüft werden Symmetrie/Zentrierung, Richtungsunabhängigkeit
beim Mittelpunktdurchgang und Stetigkeit am 8-cm-Übergang. Das ersetzt weder
die bestätigte dynamische Masken-Bewegungsprobe noch eine Raumabnahme.
Die Hauptkomponente und ihre Kontakthistorie werden nicht verändert.

77 fokussierte Offline-Tests bestanden; vier optionale native GPU-Tests
werden ohne konfigurierten Runner übersprungen und sind für die neue
Kreisform bereits separat bestanden. Syntax der erweiterten TD-Abnahme
auf Python 3.9 geprüft. Johannes hat die erweiterte Abnahme anschließend
im laufenden TD ausgeführt: `passed: true`, alle 25 Kriterien bestanden,
temporäre Prüfkomponente entfernt, nichts gespeichert. `physical_validation`
bleibt ausdrücklich `not performed`. Damit ist der Simulationsstand nach
beiden visuellen Korrekturen technisch und durch die zuvor bestätigten
Bewegungsproben geprüft. Echter Trackinganschluss, produktive Integration,
Study-/Tracking-Bildvergleiche und physische Raumabnahme stehen weiter aus.

```python
p = '/Users/Johannes/dev/Promotion_Prototypen/AISI/td_builders/check_motion_acceptance.py'; exec(compile(open(p, encoding='utf-8').read(), p, 'exec'))
```

### Vorbereitung des echten Trackinganschlusses

Die aktuelle Repository-Kette ist
`vision_live_to_aisi_scene.py` → eigene `vision_live_scene.json` →
`sim_scene_to_osc.py` → vorhandener TD-Empfänger. Der Vision-Adapter führt
stabile Track-IDs sowie `vision_live.frame_id` und `timestamp_iso` in der
Szenendatei. `send_tables` sendet hingegen Source-/Target-Daten nach Index;
die Track-ID wird dort nur für Debugtexte verwendet. `send_live_rect_tables`
liefert die separate indexbasierte Vision-Maskenquelle. Die bisher in TD
ausgelesenen Werte enthalten keine hinreichenden Frame-/Identitätsnachweise
für den Motion-Anschluss. Außerdem werden Targets im bestehenden Sender
wiederholt aus der aktuellen Szene berechnet; dies ersetzt keine explizite
Layoutaktivierung mit eingefrorenen Zielen.

Der spätere Live-Adapter muss deshalb die echte Track-ID-/Index-Zuordnung,
aktuelle Kamera-Frames und explizite Layoutaktivierung gemeinsam erhalten.
Ein laufender OSC-Sendetakt allein darf keine eingefrorene Kameraquelle
als frisch bestätigen. Die tatsächlichen gerenderten Maskenposen bleiben
die Grenze für den TD-Koordinatenabgleich. Kein Umbau der bestehenden
OSC-/Study-Kanäle, keine produktive Umschaltung und kein echter Live-Test
aus dieser Codeinspektion ableiten. Auf diesem Mac fehlt die echte Quelle.

### Live-Zustandskern und rein lesende Kameraprobe

`src/aisi/app/motion_live_adapter.py` implementiert den noch nicht
angeschlossenen `MotionLiveAdapter`. Er liest direkt kalibrierte FrameEvents
über dieselbe kanonische Posekonvertierung wie die bestehende Vision-Brücke.
Die Brücke hält fehlende Tische bis zu 15 Frames vor; dieser Cache wird für
Motion ausdrücklich nicht als Nachweis aktueller Tischsichtbarkeit verwendet.

Der Zustandskern verlangt zwei fortschreitende Frames. Wiederholtes Lesen
derselben Frame-ID verlängert das 0,5-s-Zeitlimit nicht. Zeitstempel benötigen
eine Zeitzone; alte/future Capture-Zeitstempel werden verworfen. Die bestehende
Vision-Uhr schreibt volle UTC-Sekunden: Die Capture-Altersprüfung berücksichtigt
eine zusätzliche Sekunde Quantisierung, während der monotone Empfangs-Timeout
weiter 0,5 s beträgt. Es handelt sich um eine Prüfung auf demselben Host;
abweichende Rechneruhren sind damit nicht automatisch synchronisiert.

Stabile Track-IDs halten Source und Target bei geänderter Reihenfolge
zusammen. Fehlende Tische werden sofort ungültig; neue IDs erben keine alten
Ziele. Nur `activate(revision, targets, active_ids, now)` übernimmt eine
vollständig geprüfte Zielmenge mit expliziten Aktivflags. Poseänderungen
erzeugen weder Ziele noch Layoutrevisionen. Neustart/Rücksprung der Kamera
oder Kalibrierungswechsel verlangen expliziten Stream-Reset und danach eine
neue Aktivierung. Reset setzt die bisherige Revision nicht zurück.

Die Ausgabe bleibt in AISI-Weltzentimetern/Grad, ohne zusätzliche Achsen- oder
Vorzeichenannahmen. Es gibt noch keine Verbindung zum laufenden TD, keinen
neuen Netzwerksender und keine produktive Umschaltung. Ein späterer Sender
muss das Frischeflag des Kameraadapters erhalten; ein eigener Sendetakt darf
keine eingefrorene Kamera als frisch ausgeben. Die tatsächliche TD-Masken-
und Slotzuordnung ist vor einer Verbindung im Labor abzugleichen.

16 neue Tests bestanden: wiederholte/alte Frames, UTC-Sekundenauflösung,
fehlende Kalibrierung, ID-Reihenfolge, fehlende/neue Tische, eingefrorene
Ziele, ungültige Aktivierungen, Kamera-/Kalibrierungswechsel, fehlerhafte
Posen/Counts sowie ein synthetischer Durchlauf über `frame_values` und
`MotionOSCReader` im bestehenden neuen Präfix. Außerdem bestanden zehn
bestehende Vision-Brückentests. Kein echter Kamera- oder Raumtest.

Die Modul-CLI überspringt vorhandene JSONL-Historie und beobachtet nur neu
angehängte Frames. Sie liest ausschließlich, sendet nichts und aktiviert
kein Layout. Im Repository-Terminal mit dem vorhandenen Python-Environment:

```sh
python -m aisi.app.motion_live_adapter --input data/vision/live/current_room_rect.jsonl --duration 2
```

`ready_for_mapping_check: true` besagt ausschließlich, dass am Ende aktuelle,
gültige, fortschreitende Frames vorliegen; `td_alignment_verified` bleibt
`false`. Die lokale Mac-Probe liefert erwartungsgemäß keine Quelle und keine
Freigabe. Der tatsächliche Labor-Startbefehl für Kamera/AISI/OSC ist noch zu
benennen, bevor dieser Zustandskern in die dort aktive Kette integriert wird.

### Neue visuelle Korrektur: rundes Grün nahe der Zielmitte

Johannes meldet nach der Bewegungsprüfung einen sichtbaren Umschlag der
grünen Form beim Überfahren der Zielmitte. Die ursprüngliche v1.5-Form in
`Scene.tsx` enthält auch bei hohem Fortschritt zeitabhängige Ellipsenachsen
und einen seitlichen Mittelpunktversatz. Außerdem hängt die Asymmetrie am
gemeinsamen Translations-/Rotationsfortschritt; nahe der Positionsmitte kann
bei verbleibendem Winkelfehler somit noch deutliche Richtungsform bestehen.
Dieser Abschnitt dokumentiert eine ausdrücklich von Johannes gewünschte
visuelle Weiterentwicklung der Referenz, keine Änderung der Erfolgskriterien.

`motion_design.frag` berechnet die Halodeckung nun in `feedbackHalo`.
Ein zusätzlicher Distanzfaktor `smoothstep(8,29,distance)` schwächt sämtliche
gerichteten Formanteile ab: Mittelpunktversatz, Ellipsenstreckung und
zeitabhängige Achsen-/Mittelpunktvariation. Innerhalb der bestehenden
8-cm-Positionstoleranz bleibt eine zentrierte Kreisform, auch wenn die
Rotation noch keinen Abschluss erlaubt. Ab 29 cm bleibt die bisherige
v1.5-Form unverändert; 29 cm entsprechen dem bestehenden vollen
Navigationsradius. Größe, Kontakt-/Fortschrittsgeschichte und Erfolgsschwellen
bleiben unverändert. Die Kreisform gilt vor dem Beschnitt durch die Maske;
die reale Tischfläche kann weiterhin Teile des Kreises abschneiden.

`update_motion_halo_shape.py` ersetzt im laufenden eigenen Shader nur den
bekannten Haloblock und ergänzt die neue Hilfsfunktion. Andere lokale
Shaderänderungen bleiben erhalten, abweichender Halocode führt zum Abbruch.
Bei Compile-Fehler wird der vorige Shader wiederhergestellt. Kein
Engine-/Kontakt-Reset, keine Änderung an Masken oder produktiven Ausgaben,
keine Speicherung. Johannes hat den Installer im laufenden TD ausgeführt:
Shader aktualisiert und kompiliert, kein Engine-Reset, keine Masken- oder
Produktionsänderung, nichts gespeichert. Den angefragten Mittelpunktdurchgang
bestätigt er anschließend mit „ja jetzt stimmt es“. Die visuelle Korrektur
im dynamischen Simulationsviewer ist damit abgenommen.

Verifikation: Acht fokussierte Tests in `test_motion_halo_shape.py` bestanden.
Vier native GPU-Prüfungen führen die tatsächliche GLSL-Halofunktion ohne
Tischbeschnitt aus: zentrierte Symmetrie und Richtungsunabhängigkeit bei
unterschiedlichem Fortschritt/Zeitpunkt, identische Form vor/nach dem
Mittelpunkt, stetiger Übergang an der Positionstoleranz und pixelgleiche
bisherige Form ab 29 cm. Symmetrie erlaubt eine RGBA8-Rundungsstufe.
Vier Installer-Prüfungen sichern Python-3.9-Syntax, Rollback bei
Compile-Fehler, Erhalt anderer lokaler Shaderänderungen und Abbruch bei
abweichendem Halocode. Der vollständige Content-Shader kompiliert/linkt
zusätzlich auf dem Apple Software Renderer. Keine TD- oder Laborabnahme
aus diesen Offline-Nachweisen ableiten.

```python
p = '/Users/Johannes/dev/Promotion_Prototypen/AISI/td_builders/update_motion_halo_shape.py'; exec(compile(open(p, encoding='utf-8').read(), p, 'exec'))
```

Sichtprüfung: Einen noch aktiven Tisch ausreichend verdreht lassen, damit
er nicht bereits beim Zentrieren abschließt. Langsam mehrfach durch die
Zielmitte schieben. Das Grün soll nahe der Mitte rund bleiben und beim
Überfahren nicht umschlagen; weiter außen soll die bisherige Richtungsform
zurückkehren. Johannes bestätigt diese Sichtprüfung; sie ist keine physische
Raumabnahme.

### Behobener Grenzfall: Navigation ohne Kontakt im dynamischen Maskenprüfzweig

Nach der Wachstumsbestätigung meldet Johannes: Beim Wegziehen eines Tisches
ohne Zielüberlappung verschwindet auch der Navigationskreis. Dieser muss bei
gültiger aktiver Guidance sichtbar bleiben. Die vorherige positive Abnahme
ist auf Wachstum/Zentrierung begrenzt, nicht auf alle Zustände des kopierten
Maskenpfads.

Ein gezielter Offline-GPU-Test des unveränderten Shaders mit Source
`(400,400,90°)`, Target `(250,350,90°)`, aktivem gültigem Tisch und beendetem
Reveal rendert den weißen Navigationskreis korrekt: 2336 Alpha-Pixel über
0,5 im 500 × 500 Testbild, GLSL kompiliert/linkt und GL-Status 0. Das grenzt
die Laufzeitursache noch nicht auf Aktivierungs-/Phasenstatus oder Maskierung
ein. Keine Formel oder geschützte Geometrie auf Verdacht ändern.

`inspect_motion_navigation.py` liest/kocht nur die eigenen Prüfoperatoren und
vergleicht Source-/Target-State, Aktivierungsflag, Navigation, Kontakt und
Phase sowie Pixelregionen um nicht überlappende Sources vor/nach der Maske.
Beide möglichen Array-Y-Konventionen werden separat berichtet. Die kopierten
Maskentransformationen und lokalen Select-SOP-Grenzen werden mit ausgegeben.
Keine Parameter-/Knotenänderungen, keine Speicherung. Python-3.9-Syntax ist
geprüft. Johannes' Abfrage erfasste bei allen Tischen noch Kontakt; bei
`table_4` Source `(297,857;371,429;90°)` zu Target `(250;350;90°)`,
Navigationsradiusfaktor 0,609 und Halo 0,391. Das ist noch kein Nachweis des
gemeldeten Zustands ohne Überlappung.

```python
p = '/Users/Johannes/dev/Promotion_Prototypen/AISI/td_builders/inspect_motion_navigation.py'; exec(compile(open(p, encoding='utf-8').read(), p, 'exec'))
```

`check_motion_navigation_isolation.py` prüft deshalb zwei deterministische
GPU-Zustände durch den vorhandenen kopierten Maskenpfad: nur Tisch-Slot 4
sichtbar, ohne Kontakt Source `(400,400,90°)` zu Target `(250,350,90°)` mit
vollem Navigationskreis; danach Kontakt Source `(270,350,90°)` mit kleinem
Kreis und fortgeschrittenem Grün. Diese expliziten Shader-Zustände sind
keine simulierte Bewegungshistorie. Der Test misst helle RGB-Flächen vor
und nach der Maske, auf die jeweilige Auflösung normiert. Er ersetzt kurz
ausschließlich die zwei lokalen Select-TOP-Quellen `motion_state` und
`motion_tabletop`, stellt sie im `finally` wieder her und entfernt seine
drei temporären Operatoren. Haupt-Engine, OSC-Sender, bestehende Geometrien
und produktive Ausgaben bleiben unverändert; keine Speicherung.
Fünf Offline-Tests bestanden: geometrisch eindeutige Kontaktzustände,
Auflösungsnormalisierung, ungültige Pixel, Wiederherstellung bei Fehler und
Python-3.9-Syntax. Johannes hat den Test anschließend im laufenden TD
bestanden: Ohne Kontakt 9327 helle Pixel bei 1000² vor der Maske und 37291
bei 2000² danach (normierter Flächenerhalt 99,954 %); mit Kontakt 47456
bzw. 189841 (100,009 %). Beide Proben bestanden. Lokale Eingänge
wiederhergestellt, temporäre Operatoren entfernt, Haupt-Engine nicht
zurückgesetzt, nichts gespeichert. Damit ist der Kreis im kontrollierten
Zustand auch durch den kopierten Maskenpfad nachgewiesen. Die konkrete
gemeldete Fehlerstellung im laufenden OSC-Betrieb bleibt noch offen;
aus diesem Test folgt keine Fehlerbehebung oder physische Raumabnahme.

Die folgende Live-Abfrage erfasste `table_4` tatsächlich ohne Kontakt:
Source `(423,571;365;90°)`, Target `(250;350;90°)`, gültig und aktiv,
Guidance, Navigationsradiusfaktor 1, Kontakt-Alpha 0. Der gespeicherte
Halo-Radius 0,630 ist bei Kontakt-Alpha 0 unsichtbar und kein Restkontakt.
Die Source-Maske folgt korrekt mit `tx=0,90257`, `ty=-0,598`, `rz=-90°`.
Am Source-Zentrum (NumPy-Y 0,27) liegen vor und nach der Maske helle Pixel:
Maximalwert jeweils 1, helle Fensterfläche 81,37 % bzw. 82,48 % bei
unterschiedlicher Auflösung. Stream frisch, alle drei TOPs fehlerfrei.
Damit wird der Navigationskreis zum Diagnosezeitpunkt auch im echten
OSC-Zustand ohne Kontakt gerendert. Die Abfrage erzwingt allerdings Cooks;
Johannes bestätigt anschließend, dass der Kreis erst durch diesen Befehl
sichtbar wurde. Damit ist ein Aktualisierungsproblem belegt; die genaue
Abhängigkeitsstelle lässt sich aus den erzwungenen Cooks allein nicht
isolieren.

Die kopierten Geo-Pose-Ausdrücke rufen bislang ein DAT-Modul auf, das den
State per `numpyArray()` liest. Diese indirekte GPU-Abfrage stellt keine
zuverlässige explizite Frame-Abhängigkeit der Geo-Parameter her. Der Builder
ergänzt deshalb `absTime.frame` als ausgewertete Abhängigkeit, ohne den
berechneten Transformationswert zu verändern. Keine Änderung an Footprint,
Koordinaten, Shader oder bestehender physischer Maske.

`update_motion_mask_dependencies.py` überträgt diese Korrektur auf den
bereits vorhandenen eigenen Prüfzweig: Vorabprüfung aller 20 Ausdrücke,
Abbruch bei abweichenden lokalen Bindungen, Rücksetzen bei Fehler,
wiederholbar ohne zusätzliche Änderungen. Kein Engine-Reset, keine neuen
Knoten, kein erzwungener Cook und keine Speicherung. Neun fokussierte
Offline-Tests bestehen, darunter Wertgleichheit mit explizitem Uhrzugriff,
Installation/Wiederholung und Erhalt abweichender lokaler Änderungen.
Python-3.9-Syntax separat geprüft. Johannes hat den Installer ausgeführt:
20 Ausdrücke aktualisiert, keine Original-/Produktionsänderung, kein
Engine-Reset, kein erzwungener Cook, nichts gespeichert. Anschließend
bestätigt er den angefragten Bewegungstest ohne Diagnosebefehl mit
„ja funktioniert“. Die Laufzeitkorrektur im dynamischen Simulationsviewer
ist damit bestätigt; keine Raumabnahme.

```python
p = '/Users/Johannes/dev/Promotion_Prototypen/AISI/td_builders/update_motion_mask_dependencies.py'; exec(compile(open(p, encoding='utf-8').read(), p, 'exec'))
```

Danach ausschließlich im offenen dynamischen Tabletop-Viewer prüfen:
`table_4` wiederholt aus dem Zielkontakt herausziehen und zurückführen,
ohne Diagnosebefehl oder Force-Cook. Der volle Kreis muss ohne Überlappung
mitwandern; bei erneuter Annäherung muss das grüne Feedback weiter korrekt
wachsen. Diese Prüffolge ist durch Johannes bestätigt.

```python
p = '/Users/Johannes/dev/Promotion_Prototypen/AISI/td_builders/check_motion_navigation_isolation.py'; exec(compile(open(p, encoding='utf-8').read(), p, 'exec'))
```

```python
p = '/Users/Johannes/dev/Promotion_Prototypen/AISI/td_builders/check_motion_aligned_routing.py'; exec(compile(open(p, encoding='utf-8').read(), p, 'exec'))
```

Kalibrierung, Maskenreihenfolge, Edge Blending und Study-/Tracking-Modi
bleiben geschützt.
Stabile ID-Zuordnung, Paketaktualität und Layoutaktivierung müssen für den
späteren Kameradatenpfad separat nachgewiesen werden.
Die vorhandene Maskierung muss beim späteren Anschluss
weiterverwendet werden; `select_tabletop` (Select TOP) liegt bereits hinter
der bestehenden Tabletop-Maskierung und ist deshalb kein ungeprüfter
Anschlusspunkt für unmaskierten neuen Content.

Offline-Tests und die 22 synthetischen TD-Zustands-/Pixelprüfungen bestehen.
Der sichtbare Pause-/Fortsetzungs-/Aktivierungstest im OSC-Simulator ist
bestätigt. Unabhängige Tischzustände sind in TD synthetisch geprüft;
Dreitisch-Feedback und Kontaktfortschritt nach Reaktivierung sind sichtbar
bestätigt; außerdem ist die sichtbare Fünftisch-Kapazitätsprüfung bestanden.
Der Kamera-/Live-Adapter ist
noch nicht angeschlossen: stabile ID-/Slot-Zuordnung, Aktivierungsereignis
und Aktualität sind für dessen tatsächlichen Datenpfad separat zu prüfen.
Tracking-/Study-Erhalt ist bisher nur strukturell vorbereitet; Bildvergleiche
der bestehenden Modi und Labortests sind nicht ausgeführt. Reale Projektion,
Jitter, Kontaktzeitpunkt, Wahrnehmung und Leistung benötigen eigene Labortests.


### Abgleich vor dem Anschluss der Layout-Generierung — 2026-10-23

Johannes bestätigt die sichtbaren Tischdarstellungen und Boden-Bewegungspfeile
in der produktiven Simulationsausgabe. Die Stühle stehen noch am alten Layout;
Tischziele und Chairs sollen künftig aus demselben explizit aktivierten
Vorschlag übernommen werden. Die bisherige Motion-Simulation verwendet
weiterhin Testziele und ist nicht mit der Layout-Generierung verbunden.

Johannes berichtet, die quelladaptive Generierung auf dem Laborrechner
deaktiviert zu haben. Diese Einstellung ist vor dem Generatoranschluss zu
klären: Gemeint sein kann das fortlaufende Nachberechnen während Bewegung
oder bereits die Berechnung eines Vorschlags aus den Istposen. Keine der
beiden Bedeutungen wird stillschweigend angenommen oder wieder aktiviert.

GitHub wurde lesend abgefragt und der Branch
`origin/codex/lab-inbetriebnahme-20261021` zum Vergleich abgerufen; kein Merge,
Checkout-Wechsel oder Überschreiben lokaler Änderungen. Sein Stand `cac6365`
enthält die Laborintegration. Die Generator-Dateien `sim_layout_rules.py` und
`layout_synthesizer.py` unterscheiden sich dort nicht vom lokalen HEAD
`4d400b6`; quelladaptive Synthese ist weiterhin enthalten. Der Labor-Handoff
`docs/LAB_INBETRIEBNAHME.md` dokumentiert weiterhin kontinuierliche Anpassung
und keine ergänzte Latch-/Freeze-Funktion. Eine spätere lokale Abschaltung im
Labor ist damit weder widerlegt noch auf diesem Branch nachgewiesen.
Laufzeit-State und die Labor-TOE wurden laut Handoff nicht über Git übertragen.
Bis zur Klärung wird keine Generatorvariante neu angeschlossen; die aktive
TD-Simulation und alle bestehenden Layout-/Study-/Kalibrierungspfade bleiben
unverändert.


### Layout-Generierung einmal bei Aktivierung — 2026-10-23

Johannes klärt den obigen Labor-Abgleich: Deaktiviert ist das fortlaufende
Nachberechnen während Tischbewegung. Beim Aktivieren darf aus den aktuellen
Istposen berechnet werden. Diese Präzisierung ist als D005a festgehalten.

Implementiert, noch nicht im laufenden TD installiert:

- `src/aisi/app/motion_layout_proposal.py`: bestehende Generatoren, maximal fünf Rect-Tische, stabile IDs/Scene Order, gemeinsame unveränderliche Ziel-/Chair-Menge. Keine Übernahme unvollständiger, nicht endlicher oder kollidierender Tischziele. Sitz-/Kontaktregeln bleiben in den bestehenden Formatplanern; Discussion-Chairs dürfen deren vorgesehene Tischkante berühren. Ohne Teilnehmenden-Opt-in nur Tischziele; kein stiller Fallback bei Planerfehlern.
- `motion_preview_sim.py --generated-layouts`: beim Klick aktuelles `learning_format.json` und Istposen erfassen, einmal im Worker berechnen. Währenddessen sendet der bisherige Vorschlag weiter. Nur erfolgreicher Commit im Editor-Thread erhöht die Revision. Geänderte Tischmenge während Berechnung oder Planerfehler erhalten den bisherigen Vorschlag. Verschieben und UI-Einstellungsänderungen lösen keine Aktivierung aus. Start ist bis zum ersten erfolgreichen Klick leer.
- `motion_chairs.py` und `.frag`: additive `/aisi_motion/chairs/...`-Nachrichten im selben Bundle wie die Tischposen. Session/Frame/Revision binden Stühle an den Vorschlag; Count-Schrumpfung, fehlende/alte/unvollständige Pakete und Timeout erzeugen keine alten Stuhlmarker. Weiße Ringe, 2,5 cm Stärke nach innen bei erhaltenem Außenradius; Reveal und aktuelle Tisch-Footprints werden berücksichtigt. Die beiden Texturen werden gemäß [GLSL-TOP-Dokumentation](https://docs.derivative.ca/Write_a_GLSL_TOP) über `sTD2DInputs[0]`/`[1]` gelesen.
- `build_motion_layout_chairs.py`: isolierte eigene Chair-Komponente. Der erweiterte registrierte Ausgabetest schaltet den zweiten Bild-Eingang der vorhandenen `composite_floor_with_synth_chairs` (Composite TOP) reversibel auf diese Quelle. Composite-Operation und bestehender Chair-Schalter bleiben erhalten. Gleiches Simulation-/AISI-/Kalibrierungsgatter wie für Content und Maske; Study, Tracking und Kalibrierung verwenden die alte Quelle. Stop stellt den Originaleingang wieder her; lokale Fremdänderungen werden geschützt.
- `prepare_motion_layout_simulation.py`: bisherigen registrierten Test zurückbauen, isolierte Chairs bauen oder unverändert wiederverwenden, nur den eigenen Fixture-Sender durch die Fünf-Tisch-Simulation mit Generator ersetzen, anschließend deaktivierte GPU-/Bypass-Vorbereitung. Keine automatische TD-Speicherung und kein Merge des Labor-Branches.

**Ausgeführt:** 62 fokussierte Prüfungen bestanden: zehn Vorschlags-/OSC-
Integrationstests mit echten Generatoren aller drei Lernformate, sechs
Chair-Tests (einschließlich drei nativer Zwei-Textur-GPU-Prüfungen),
29 Routing-/Simulationstests, fünf Launcher-Tests und zwölf bestehende
Motion-Transporttests. Getestet: eingefrorene Ziele/Chairs trotz Source-Bewegung
und Reihenfolgeänderung, genau einmaliger Commit, Fehlererhalt, explizites
Opt-in, alte Chair-Pakete, gemeinsamer Modusschalter, Rückbau und Schutz
lokaler Änderungen. Python-3.9-Syntax der TD-Skripte geprüft.

Echte Generatorprobe offline: Input, Groupwork, Discussion jeweils fünf Tische,
acht Teilnehmende, 100 %, bei Groupwork zwei Gruppen. Zusätzlich aktueller
lokaler State erfolgreich berechnet: Discussion, 13 Teilnehmende, 88 %, fünf
Tischziele/13 Chairs. Laufzeit-State nicht verändert. Native GPU-Prüfung
verwendet den echten Chair-Shader mit zwei Texturen; sie ersetzt keine
Kompilierung im laufenden TD und keine Projektor-/Raumabnahme.

**Manuell in TD ausführen:**

1. Den bisherigen Test und eigenen Simulator kontrolliert ersetzen sowie den neuen Ausgabetest vorbereiten:

```python
p = '/Users/Johannes/dev/Promotion_Prototypen/AISI/td_builders/prepare_motion_layout_simulation.py'
exec(compile(open(p, encoding='utf-8').read(), p, 'exec'))
```

2. Nach Rückkehr zum Textport als neue Eingabe aktivieren:

```python
import importlib, json
from td_builders import motion_output_simulation_test as output_test
output_test = importlib.reload(output_test)
print(json.dumps(output_test.activate(op), ensure_ascii=False, indent=2))
```

3. In der vorhandenen Learning-Format-Oberfläche gewünschte Einstellungen wählen. Für vergleichbare Abnahme: „Synthetische Tischplanung testen“ an, acht Teilnehmende, 100 %, bei Groupwork zwei Gruppen; Chairs an. Diese Einstellung aktiviert noch keinen Vorschlag. Im neuen Room Editor „Vorschlag aktivieren“ klicken und die erfolgreiche Statusmeldung abwarten. Dann erscheinen generierte Tischziele und Stühle.
4. Anschließend den aktiven Ausgabepfad prüfen:

```python
print(json.dumps(output_test.verify(op), ensure_ascii=False, indent=2))
```

Erwartet: `chair_index = 1`, gemeinsam mit beiden Content-Indizes und
`mask_index = 1`; Chair-Quelle im selben Gatter und fehlerfreie zentrale
Ausgänge. `chair_stream` zeigt die unabhängige Empfangsdiagnose und sichtbare
Chair-Anzahl. Bei Pixelabweichung baut der Prüfer eine unverändert registrierte
Sitzung zurück. Das bestehende Stop bleibt gültig:

```python
print(json.dumps(output_test.stop(op), ensure_ascii=False, indent=2))
```

**Noch in TD abzunehmen:** Für jedes Format einzeln einmal aktivieren,
Tisch bewegen/verdrehen und Ziel-/Stuhlpositionen unverändert beobachten;
Feedback und unabhängige Abschlüsse prüfen. Lernformat-Einstellungen ändern:
Bis zum nächsten Klick bleibt der Vorschlag stehen. Nach erneutem Klick
entsteht genau eine Reveal-Welle und die vollständige neue Ziel-/Chair-Menge.
Ungültige Anfrage muss Fehler anzeigen und bisherigen Vorschlag erhalten.
Danach kurzer formatübergreifender Durchlauf und tatsächlicher
Study-/Tracking-/Kalibrierungsmodusvergleich mit Rückkehr zu den alten Quellen.
Installation und aktive Pixelprüfung dieses erweiterten Anschlusses stehen
noch aus. Physische Raumvalidierung sowie Anschluss echter Trackingframes
bleiben Labortests; kein entsprechender Nachweis auf diesem Mac.
