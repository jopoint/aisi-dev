# AISI TODO

Stand: 2026-10-19

Use this file to choose the next coherent task. Do not execute all items automatically. Completed implementation history belongs in Git and the handoff documents, not in this checklist.

## NOW — Participant-based Input / TouchDesigner integration

Inbetriebnahmeblock am 2026-10-19 abgeschlossen. Die folgenden Lab-Prüfblöcke
sind technisch und durch Johannes im Raum für die geprüften Stichproben bestanden:

1. Fünf-Tisch-Groupwork 5/5 → 15/5 → 15/2 → 4/1 → 10/5 technisch/live
   bestanden: Gruppen/Pairs, hohe Belegung, Park-Rückkehr und Sources ruhig.
2. Gemeinsamer Fünf-Tisch-Format-/Moduswechsel samt 15 Chairs Off/On live
   bestanden. Aktiver Tischabgang/-rückkehr bei Discussion 15 technisch
   bestanden (5/ready → 4/invalid → 5/ready). Auf Johannes' Präzisierung
   fehlende Source separat ausblenden: Sender aktualisiert Source-Verfügbarkeit
   bei veraltetem Zielvorschlag, 51 Tests bestanden, Sender/UI neu geladen.
   TD-Helfer ausgeführt und Abgang-/Rückkehrtest durch Johannes live bestätigt.
3. Gebündelte Tracking-Stichprobe bei Verdeckung, enger Begegnung und
   Abgang/Rückkehr durch Johannes live bestanden: Sources folgen wieder,
   keine vertauschten/eingefrorenen Konturen, ruhiges Bild. Keine Aussage
   über unveränderte Track-IDs nach längerer Abwesenheit.
4. Physische Projektions-/Maskenstichproben an ROI-Rändern und in der
   Projektorüberlappung durch Johannes bestanden: saubere Konturen/Helligkeit,
   keine Bodenpfeile auf Tischflächen, ruhiges Bild. Kalibrierung unverändert.
5. Neue manuelle TD-Sicherung inklusive jüngster Kontrollviewer-, Bodenpfeil-
   und Source-Verfügbarkeitskorrekturen sowie erneuter Öffnungscheck durch
   Johannes bestätigt; laufende Datei `AISI_v2.149_lab_layout_validated.toe`
   über Prozessargument nachgewiesen. Vollständiger Anwendungs-Wiederanlauf
   einschließlich TD und Bedienoberflächen technisch und live bestanden:
   Sources folgen, alle Formatwechsel und Tracking → AISI sauber, keine alten
   Elemente, ruhiges Bild. Kein Windows-Neustart geprüft.

Die separate Study-/Pilot-Validierung ist laut Johannes am 2026-10-19 nicht
mehr erforderlich und kein offener Folgeauftrag der Inbetriebnahme.
Neuer Auftrag: AISI-Bodenpfeil bis Target-Mittelpunkt. Nach Screenshots mit
fehlenden Pfeilen alte pauschale Overlap-Ausblendung offline reproduziert;
Helfer erweitert auf vorwärts gerichtete Source-Kante→Zielmitte-Strecke.
Elf Tests/96 reale Callback-Fälle bestanden; Johannes bestätigt Teil-Overlap
und Zielmitten-Ende live, ruhiges Bild. Neue TD-Sicherung und erneutes Öffnen
anschließend durch Johannes bestätigt.
Historische offene Einzelpunkte sind durch die aktuellen Live-Nachweise nur
für die tatsächlich geprüften Stichproben abgedeckt; keine Vollmatrix behaupten.

- [x] Lab-PC am 2026-10-19 inspiziert: bestehenden Tracking-only-Sender durch
  genau einen Layout-Sender ersetzt, Teilnehmer-Vorschau aktiviert. Laufendes
  Groupwork meldet zwei Ziele/vier Chairs; 46 fokussierte Tests und drei
  Offline-Format-/OSC-Stichproben bestanden. Kalibrierung unverändert.
  [Startpfad und Rückkehr](docs/LAB_INBETRIEBNAHME.md).
- [x] Reale Groupwork-Ausgabe und gebündelte Zwei-/Vier-Tisch-Formatwechsel
  nach Senderwechsel bestätigt; Fünf-Tisch-Groupwork bleibt eigener Block.
- [x] Erste Raumprüfung meldet Spiegelung auf beiden Achsen und fehlende
  Source-Konturen im Projektorausgang. Abweichende AISI-/Tracking-Positions-
  ausdrücke in gespeicherter TD-Version 144 nachgewiesen. Rücknehmbare
  Callback-Korrektur vorbereitet, 27 Tests bestanden; manuelle Live-Ausführung
  und aktuelle Zwei-Tisch-Raumprüfung durch Johannes bestätigt. Details im Lab-Handoff.
- [x] Johannes bestätigt nach manueller Achsenkorrektur: Source-Konturen auf
  realen Tischen, Ziele und Chairs richtig ausgerichtet (Zwei-Tisch-Groupwork).
  Speicherung/erneutes Öffnen und weitere Formate noch nicht bestätigt.
- [x] Anschließenden Anzeige-Stillstand eingegrenzt: Python-Pipeline lief
  weiter, TD-Timeline war pausiert. Johannes bestätigt Behebung durch Play;
  kein OSC-Neustart nötig. Physische Input-Einzelprüfung bleibt offen.
- [x] Johannes bestätigt danach Input, Discussion und Groupwork im Raum:
  Source-Konturen folgen Tischen, Ziele/Chairs plausibel, Bild ruhig.
  Qualitative erste Live-Stichprobe; keine vollständige Count-/Gruppenmatrix.
- [x] Einzeltischbewegung im Input live bestätigt: Source-/Tischzuordnung
  stabil, ruhiges Bild. Kontinuierliche quelladaptive Zielneuberechnung
  beobachtet; keine Ziel-Fixierung ergänzt. Messstichprobe im Lab-Handoff.
- [x] Input 4 → 3 live bestätigt: drei Kreise, stabile Source-/Tischzuordnung.
  Auf Auftrag wieder vier aktiviert, Sender meldet vier Chairs.
- [x] Chair-Konturen weiß und 2,5 cm wie Ziel-Tischkonturen: Helfer
  `repair_chair_visual_style.py` vorbereitet, fünf Tests und 16 echte
  gespeicherte Ring-Callbacks geprüft. Johannes bestätigt vier weiße Kreise
  und gute Lesbarkeit im Raum; damit Rückkehr 3 → 4 ebenfalls bestätigt.
- [x] Groupwork 4/1 mit zwei Tischen live bestätigt: Pair, vier Chairs,
  Source-Konturen und ruhiges Bild. Vergleich 4/2 ebenfalls live bestätigt:
  zwei getrennte Gruppen mit je zwei Chairs, Source folgt, ruhiges Bild.
- [x] Discussion 6 mit zwei realen Tischen live bestätigt: Spalt, vier
  Längsseiten-/zwei Stirnplätze, Source-Konturen und ruhiges Bild passend.
  Rückwechsel 6 → 4 ebenfalls live bestätigt: nur Stirn-Chairs entfernt,
  Tischziele/Längsseitenplätze unverändert und Bild ruhig.
- [x] Chair-Sichtbarkeit Off über echte OSC-Nullradien live bestätigt: alle
  vier Kreise verschwinden, Source-/Zielkonturen und Pfeile bleiben aktiv.
  On ebenfalls bestätigt: alle vier Kreise an denselben Plätzen, ruhiges Bild.
- [x] Gemeinsamer Zwei-Tisch-Formatwechsel Input → Groupwork 4/2 →
  Discussion 4 live bestätigt: vier Chairs je Format, keine alten Ziele/Pfeile,
  Source folgt, ruhiges Bild. Endzustand Discussion. Höhere Tischzahlen offen.
- [x] Modustrennung AISI → Tracking → AISI live bestätigt: nur reale
  Konturen in Tracking, Discussion/Pfeile/vier Chairs in AISI; Source folgt.
- [x] Study-Control auf Auftrag vereinfacht: Study-Einstellungen nur in Study,
  manuelle Target-Eingabe entfernt. 30 Tests und Tkinter-Moduscheck bestanden.
- [x] Neue Study-Control nach manuellem Neustart live bestätigt:
  Study-Einstellungen nur in Study, Target-Eingabe entfernt,
  AISI → Study → Tracking → AISI funktioniert.
- [x] Korrigierten TD-Graphen manuell als neue Version sichern; tatsächlichen
  Pfad bestätigen, gespeicherte Korrekturen offline prüfen und erneut öffnen.
- [x] Johannes speichert `AISI_v2.146_lab_layout_validated.toe` manuell;
  Achsen, Pfeilkorrekturen in Template/zwei Instanzen, 16 Chair-Ringe mit
  Stärke/Radiusbindung und weißes Material offline nachgewiesen.
- [x] Version 146 erneut geöffnet und auf Play live bestätigt: Source folgt,
  vier weiße Chairs/Discussion-Ziele, Pfeil-Endpunkt/Toleranz korrekt,
  ohne Helfer-Wiederholung. Weitere Format-/Count-Stichprobe folgt separat.
- [x] Input 2 nach erneutem Öffnen live bestätigt: zwei Chairs am aktiven
  Ziel, zweites Ziel ohne Chairs am Rand geparkt, beide Sources folgen,
  keine alten Elemente und ruhiges Bild.
- [x] Input 2 → 4 live bestätigt: beide Tische aktiv, vier Chairs,
  Parkziel verschwunden, Sources folgen und ruhiges Bild.
- [x] Input 6 mit zwei Tischen live bestätigt: je drei Chairs, keine Parkpose,
  folgende Sources und ruhiges Bild.
- [x] Groupwork 6/2 live bestätigt: zwei getrennte Ziele/je drei Chairs,
  Source folgt, ruhiges Bild.
- [x] Groupwork 6/1 live bestätigt: gemeinsames Pair/sechs Chairs,
  keine alten Gruppen, Source folgt und Bild ruhig.
- [x] Gebündelter Format-/Count-/Parkdurchlauf live bestätigt: insgesamt
  ruhig, keine hängen gebliebenen Elemente; technische Prüfung fehlerfrei.
- [x] Layout-Sender-Wiederanlauf und Format-/Countwechsel technisch und
  visuell bestanden: selbstständige Erholung, ruhiger Durchlauf.
- [x] Adapter-Wiederanlauf samt gebündelten Wechseln technisch und visuell
  bestätigt: selbstständige Rückkehr von Tracking/Darstellung, ruhiges Bild.
- [x] Leere Vision-Live-Szene im Layout-Sender repariert: explizite
  Null-Counts statt Layout-Ablehnung mit alten TD-Daten; 37 Tests bestanden.
- [x] Vision-Wiederanlauf samt Formatwechseln technisch und visuell bestätigt:
  Ausgabe verschwindet bei Unterbrechung, kommt selbstständig korrekt zurück,
  Wechsel ruhig. Endzustand Discussion 4.
- [x] Gemeinsamen Wiederanlauf Vision/Adapter/Layout-Sender technisch und
  visuell bestätigt: selbstständige Rückkehr, ruhiger Formatdurchlauf.
  Regulärer Zwei-Tisch-Inbetriebnahmeblock damit abgeschlossen.
- [x] Hinweis auf fehlende Tische implementiert: tatsächlicher Senderstatus
  in Learning Format UI, Tischanzahl/Planerfehler und veraltete letzte Anzeige.
  47 Tests und Live-HTTP-Fehler-/Recoveryprüfung bestanden.
- [x] Tischzugang/-abgang und UI-Hinweis im Raum bestätigt: dritter Tisch
  hinein/heraus korrekt berücksichtigt; Discussion-7-Warnung bei fehlenden
  Tischen, Recovery bei vier Personen oder Hinzufügen eines vierten Tisches.
  [Nachweise und aktueller Endzustand](docs/LAB_TISCHANZAHL.md).
- [x] Vier-Tisch-Discussion 6 → 7 → 6 technisch und live bestätigt:
  vier stabile IDs, ready in allen Stufen, 6/7/6 Chairs, Fehlerlog leer.
  Endzustand Discussion 6; Nachweise im Tischanzahl-Handoff.
- [x] Discussion 8 → 9 → 10 → 11 → 12 → 8 technisch und live bestätigt:
  technisch vier stabile IDs, korrekte Counts, alle Stufen ready, Fehlerlog
  leer; Tischziele offline innerhalb der Stufe exakt gleich. Endzustand 8.
- [x] Vier-Tisch-Groupwork 8/4 → 12/4 → 12/2 → 8/2 live bestätigt:
  vier Gruppen/zwei Pairs plausibel, Chair-Wechsel vollständig, Bild ruhig.
- [x] Kontrollviewer-Source-Auswahl repariert: native Pfade statt zu None
  aufgelöster Expression. Johannes bestätigt vier folgende blaue Konturen,
  Projektorausgabe unverändert. Manuelle Speicherung dieser Reparatur offen.
- [x] Discussion 12 → 13 → 14 → 15 → 12 technisch/live bestätigt:
  Pentagon/Plätze plausibel, Rückkehr/Parken sauber, fünf Sources folgen,
  ruhiges Bild. Kontrollviewer nach fünftem Tischzugang ebenfalls bestätigt.
- [x] Fünf-Tisch-Input 4 → 8 → 10 → 12 → 15 → 4 live bestätigt:
  Parken/Aktivieren und Verdichtung plausibel, alle 15 Chairs sichtbar,
  Rückwechsel ohne alte Kreise und ruhiges Bild.
- [x] AISI-Tabletop-Pfeile bei großem Overlap am Target-Mittelpunkt begrenzen:
  Helfer `repair_aisi_arrow_endpoint.py` vorbereitet, vier Tests und 1152
  Offline-Fälle auf gespeicherten TD-Callbacks bestanden. Manuelle Ausführung
  und Annäherung live bestätigt; Anleitung im Lab-Handoff.
- [x] Johannes bestätigt die AISI-Pfeil-Endpunktkorrektur als passend.
- [x] AISI-Pfeile bei ≤ 8 cm und ≤ 5° ausblenden, Spitzen mit Schaft verkleinern:
  `repair_aisi_arrow_arrival.py` vorbereitet, 23 Tests und 300 Fälle auf zwölf
  gespeicherten Callbacks bestanden. Johannes bestätigt kleiner werdende
  Pfeile, Ausblenden innerhalb der Toleranz und Wiedererscheinen beim Entfernen.
  Study unverändert, Endpunktkorrektur erhalten. Anleitung im Lab-Handoff.

Johannes bestätigt am 2026-10-15 Input für den Moment als in Ordnung. Dies ist
eine qualitative Freigabe der aktuellen Anzeige, kein zusätzlicher Nachweis
aller Counts/Seiten oder physischer Projektion. Der gemeinsame Formatwechsel-Check
ist der nächste zusammenhängende Prüfschritt; offene Einzel-/TD-Nachweise bleiben
separat erhalten. Die unmittelbar vorherige Codeänderung betraf Discussion;
daraus wird keine zusätzliche explizite Discussion-Live-Freigabe abgeleitet.

**Source-Rotation im Rect Input — Auftrag vom 2026-10-07, offline behoben am 2026-10-08:**
- [x] Beobachtung am 2026-10-08 offline reproduziert: Alle fünf Source-Tische stehen horizontal (0°/180°), die Automatik erzeugt vertikale Ziele (±90°). Ursache ist die positionsbasierte Präsentationsachse mit Ost-Ausweichlösung, kein zusätzlicher Darstellungsversatz. Nord und Süd erhalten die horizontale Orientierung und bestehen die gemeinsame Geometrieprüfung. Source-/Target-Winkel im lokalen OSC-Recorder und 18 gespeicherte Geo-Bindungen aus Version 141 geprüft; kein neuer Live-Nachweis.
- [x] Nach Johannes' Zustimmung bevorzugt die gemeinsame Rect-Input-Synthese die axiale Source-Orientierung; Positionen bestimmen Präsentationsende und Rollen, explizite Seiten bleiben verbindlich. Die konkrete Live-Quelle ergibt jetzt fünf horizontale Ziele, 0° statt 450° gesamter axialer Rotation. D007 aktualisiert.
- [x] ROI, Kapazität, Chairs und gerichtete Sitz-/Bewegungsflächen erneut abgesichert: 300/300 gespeicherte Geometriefälle, 300 deterministische Wiederholungen, 140 Scene-Order-Prüfungen, 60 Überkapazitätsablehnungen sowie 57 fokussierte Tests bestanden. [Prüfbericht](docs/INPUT_GEOMETRY_VALIDATION.md).
- [x] Johannes bestätigt am 2026-10-08 die neue Rotationswahl in der Live-Stichprobe als sinnvoll. Zuvor wurde der doppelte alte Sender beendet; Bild anschließend ruhig. Diese Bestätigung betrifft die virtuelle Anzeige, keine physische Raumprüfung; keine zusätzliche Behauptung zu vollständigen Count-/Seitenkombinationen.

Neuer expliziter Auftrag: AISI-Zieltischkonturen müssen auf dem Floor
erscheinen; AISI-Elemente sollen gestalterisch dem bestehenden Study-Modus
entsprechen. Vorhandene AISI-Geometrien erweitern, keine parallele
Tischpipeline. Chairs bleiben vorerst unverändert, da ihre Study-Gestaltung
noch nicht spezifiziert ist. Aktuellen Livegraph gezielt lesen, danach
AISI-Auswahl des Floor-Renderers und betroffene Darstellung anpassen;
Study/Tracking, Masken und physische Projektion bleiben geschützt.
Umgesetzt im laufenden Projekt auf Basis von Version 138:
`apply_aisi_study_visual_style.py` meldet `passed: true`; Johannes bestätigt
Floor-/Tabletop-Ansicht. Geschützte Einstellungen, Chair-Bild und Table-Mask
unverändert; fünf Rect-Instanzen haben korrekte Konturprimitive. Drei
fokussierte Tests und Erhalt der Tracking-/Study-Floor-Pfade offline geprüft.
Aktueller manuell gespeicherter und dateisystemseitig verifizierter Stand:
`AISI_v2.141_coherent_chairs_validated.toe`. Johannes bestätigt den
fehlenden-Chair-Fehler nach expliziter Ring-Radius-Bindung als behoben;
Template + 15 Instanzen enthalten die Reparatur nachweislich in der Datei.
Ein erneuter Öffnungscheck von Version 141 bleibt ein separater Nachweis.


Geprüfter TD-Zwischenstand: `AISI_v2.137_coherent_chairs.toe` ist manuell
gespeichert und erneut geöffnet; der Ausgabecheck besteht. Gemeinsame
Chair-Geometrie mit 15 Slots und Count 7 ist geprüft. Die zentralen Viewer
unter `comp_layout_proposal` bleiben erhalten; alte externe Komponenten,
doppelte Debug-Geometrien und der alte Chair-Zweig in `comp_output` sind
entfernt. Referenzprüfung ohne Treffer und zehn Bilder bitgleich bei der
Bereinigung. Nach erneutem Öffnen: Floor Off bitgleich, beide Projektorpfade
reagieren auf On, Tabletop/Table-Mask bitgleich, regulärer Zusatz unabhängig
von Debug/Preview. Speichern erfolgt künftig ausschließlich manuell durch
Johannes. Count 15 und danach reagierende Count-Wechsel sind durch Johannes
beobachtet; der direkte Wechsel 3 → 15 → 3 nach erneutem Öffnen ohne Force-Cook
ist ebenfalls durch Johannes bestätigt. Der isolierte TD-Radius-null-Test
besteht (15 → 14 gültige Chairs, nur Chair 0 ausgeblendet, danach restauriert);
der entsprechende echte OSC-Test bleibt offen. Der Moduscheck wurde mit nachweislich regulären Chairs On wiederholt:
Tracking/Study/Calibration liefern Index 0, AISI liefert 1. Vollständige
bildliche Modusvergleiche bleiben offen. Verbleibende Livetests und die
aufgeschobene Raumprüfung sind getrennt von der bestandenen Offline-Prüfung.

1. [x] Zentrale gemeinsame 15-Chair-Struktur laut aktuellem Handoff geprüft; die frühere Acht-Slot-Grenze ist aufgehoben. Source, Target, Parktische und Chairs werden gemeinsam offline geprüft; keine zusätzliche TD-Bearbeitung in diesem Block.
2. [x] Wiederkehrenden Chair-Aktualisierungsfehler behoben und von Johannes nach den angefragten Count-Wechseln bestätigt.
   - Veralteten Python-Sender neu gestartet; veraltete Nullradius-Geometrie an Index 9 durch explizite SOP-Radius-Bindung für Template + 15 Instanzen korrigiert. Count 10 zeigt zehn Kreise; Stand manuell als Version 141 gespeichert und offline auf gespeicherte Bindungen geprüft.
   - Bisherige Counts 6, 9, 10, 11, 15 und Room-Editor-/OSC-Live-Reaktion sind bestätigt. Diagnose und Reparatur im [Chair-Debug-Handoff](docs/TOUCHDESIGNER_SYNTH_CHAIR_DEBUG.md).
   - Count 0 ist ausgenommen. Echte OSC-Radius-null-Prüfung und erneutes Öffnen von Version 141 bleiben getrennte Live-Aufgaben.
3. [x] Input-Kapazitäts-/Fehlervertrag offline geprüft: über `15` explizite Ablehnung vor Ausgabe, kein Ersatzlayout; bestehende `/chair/0…14/{x,y,radius}`-Float-Nachrichten mit lokalem Recorder geprüft. Echte OSC-Radius-null-Prüfung bleibt offen.
4. [x] Gemeinsame Table–Chair–Park-Geometrie offline validiert.
   - 300/300 Fälle: fünf Rect-Tische, Counts 1–15, vier Quellen und automatische/vier vorgegebene Präsentationsseiten, 100 %.
   - ROI, Tisch-/Chair-Kollisionen, Chair-Abstände und freie gerichtete Sitz-/Bewegungsflächen bestanden.
   - 300 deterministische Wiederholungen, 140 Scene-Order-Prüfungen und 60 explizite Überkapazitätsablehnungen bestanden; 59 fokussierte Tests bestanden.
   - Drei Plotübersichten und reproduzierbare Quellen im [Prüfbericht](docs/INPUT_GEOMETRY_VALIDATION.md). Count 0 ausgenommen, physische Raumprüfung aufgeschoben.
5. [x] Johannes bestätigt am 2026-10-08 die Chair-Umverteilung im Input bei Count-Wechseln als sinnvoll; qualitative Live-Stichprobe, keine Garantie minimaler Umverteilung für alle Quellen.
6. [ ] Physically validate the optional regular Floor-Chair output for visibility, position, size, masking, and projection behavior.
7. [x] Senderprüfung am 2026-10-08 nach gemeldetem Flackern: alter Sender PID 40517 und heutiger Sender PID 94900 liefen gleichzeitig auf Zielport 9000. Alten Sender beendet; danach genau eine Layout-Senderinstanz (PID 94900) verifiziert. Johannes bestätigt anschließend das ruhige Bild. Befunde im [Chair-Debug-Handoff](docs/TOUCHDESIGNER_SYNTH_CHAIR_DEBUG.md); beim Neuladen bestehenden Sender beenden statt eine zweite Instanz daneben starten.

## NEXT — Extend participant-based planning to other formats

Synthetische Chairs sind für Input und Groupwork umgesetzt. Die aktuelle Groupwork-Stichprobe `10/4` ist laut Johannes visuell passend. Der gemeinsame Groupwork-Offline-Abschlusscheck ist bestanden (130/130 Fälle). Johannes bestätigt am 2026-10-09 einen guten Gesamteindruck von Groupwork. Die Rückmeldung ist qualitativ; konkrete Counts und eine vollständige interaktive Einzelvalidierung sind damit nicht zusätzlich nachgewiesen. Discussion-Chairs sind inzwischen offline implementiert und geprüft; die interaktive Einzelvalidierung ist als Nächstes offen. Der gemeinsame Formatwechsel-Check folgt nach den Einzelvalidierungen. Physische Raumprüfungen bleiben separat offen.

### Groupwork

- [x] Spezifikation vom 2026-10-08 aufgenommen: Teilnehmergruppe von Tischclustern trennen; mehrere räumlich eindeutig zusammengehörige Cluster pro Gruppe zulässig. Sitzpriorität: zwei Personen je nutzbarer Längsseite optimal → geometrisch nutzbare Stirnseiten → drei Plätze an einer Längsseite; fünf Personen am Einzel-Rect bevorzugt `2 + 2 + 1`. [D008b](docs/DECISIONS.md#d008b--teilnehmendenbasierte-groupwork-gruppen-und-sitzprioritäten).
- [x] Offline-Prototyp ergänzt: gleichmäßige Teilnehmergruppen, separate Cluster-/Chair-Zuordnung, kanonische Stirnseitenflächen, vollständige Table-/Chair-/Sitzflächen-/Parkprüfung. 65 fokussierte Tests und zehn Integrationsfälle bestanden; [Handoff](docs/GROUPWORK_PARTICIPANTS.md).
- [x] Tischwahl nach Live-Stichprobe aktualisiert: optimal drei Personen am Einzel-Tisch; größere Gruppen erhalten bevorzugt ein Pair aus zwei Tischen, sofern vollständig geometrisch gültig. Neuer Standard `group_capacity` ersetzt `few_tables`; Stirnseiten vor Verdichtung bleiben erhalten.
- [x] `participants` und `number_of_groups` möglichst gleichmäßig auf Teilnehmergruppen verteilen; benötigte Tischzahl und Cluster je Gruppe geometrisch bestimmen statt Teilnehmergruppe mit Insel gleichzusetzen.
- [x] Chairs mit getrennten Teilnehmergruppen-/Clusterzuordnungen aus freien Sitzflächen ableiten. Bestehende Singleton-Geometrie um die nun erlaubten Stirnseitenplätze ergänzen; Sitzprioritäten prüfen.
- [x] Offline-Modell an die opt-in Vorschau und den bestehenden OSC-Adapter angebunden; über 15 technische TD-Slots ausdrücklich ablehnen. Stärke 0 erhält exakte Source ohne Chairs/Reparatur; positive Teilstärken blenden vor vollständiger Reparatur bei gebundenen Gruppen-/Cluster-/Tischrollen.
- [x] Vorschau-/Adapter-Meilenstein offline geprüft: 52 fokussierte Tests, sechs Vorschautests nach Cache-Ergänzung erneut, 18/18 Adapterfälle (0/50/100 %, Editor-/Live-Quelle), lokale OSC-Aufzeichnung ohne echte Netzwerkpakete.
- [x] Aktualisierte Pair-Priorität offline geprüft: 16 Groupwork-Tests und zwölf Integrationsfälle, einschließlich 15 Personen/zwei Gruppen mit zwei Pairs; aktuelle Live-Quelle zusätzlich offline geprüft.
- [x] Bodenkontur-Überlappung der `14/4`-Live-Stichprobe offline behoben: bestehende 170 × 90 cm Darstellungsränder prüfen, getrennte Cluster ohne Rollenwechsel räumlich verbessern; 17 Tests und zwölf Integrationsfälle bestanden. Live-Bestätigung nach Neuladen noch offen.
- [x] Unnötigen Source-Positionswechsel der `14/4`-Stichprobe offline behoben: Source-Wege bei Clusterbildung/Entzerrung priorisieren, zusätzliche Source-abgeleitete Singleton-Winkel. Oben links bleibt am Ort; Gesamtweg rund 567 → 142 cm; 32 fokussierte Tests und zwölf Integrationsfälle bestanden. Live-Nachweis nach Neuladen offen.
- [x] Groupwork-Laufzeit offline optimiert: konkrete `14/4`-Quelle 70,7 → 10,4 s (6,8×), exakter Plan erhalten. Frühe kanonische Konfliktprüfung, sichere Bestwert-Grenzen, Wiederverwendung identischer Sitzprüfungen. 35 fokussierte Tests und zwölf Integrationsfälle bestanden; alle Vergleichspläne exakt erhalten. [Messung und Handoff](docs/GROUPWORK_PERFORMANCE.md).
- [x] Weitere Groupwork-Beschleunigung geprüft: konkrete `14/4`-Quelle 9,6 → 5,6 s (42 % weniger Zeit), exakter Plan erhalten. Weggrenze in der Entzerrung, kanonische Hüllrechteck-Vorprüfung, begrenzte reine Geometriecaches. 37 Tests bestanden; zwölf vollständige Vergleichspläne exakt erhalten.
- [x] Fünf-Gruppen-Fallback nach Live-Stichprobe korrigiert: Source-abgeleitete Winkel schrittweise annähern statt sofort alle Tische orthogonal auszurichten; kanonische abgerundete Flächen und Bodenkonturen gemeinsam reparieren. Geparkte Tische bei 100 % mit physischer Längsseite am ROI-Rand halten, von der Entzerrung ausnehmen. Einzelne Count-Änderungen müssen bei gleicher Tisch-/Sitzflächenzahl keine neuen Tischposen erzeugen. 34 fokussierte Tests und zwölf Integrationsfälle bestanden; zwei Vergleichsplots im Handoff vermerkt. Live-Nachweis nach manuellem Neuladen offen.
- [x] Nach verbesserter Live-Stichprobe 60-cm-Mindestabstand zwischen Park-/Aktiv-Footprints ergänzt; Parkplatzsuche und Endprüfung erzwingen dieselbe Regel. Aktive Source-Wege haben Vorrang vor Parkwegen. 36 fokussierte Tests und 14 Offline-Integrationsfälle bestanden; Live-Nachweis der neuen Regel und physische Prüfung offen.
- [x] `10/4`-Fallback nach Live-Stichprobe angepasst: Bei fehlendem gültigem Parken ein Pair plus drei Singletons vor fünf getrennten Clustern bevorzugen. Begrenzte Winkelannäherung für `2 + 1 + 1 + 1`; tatsächliche Source-Winkel und vier Gruppen erhalten. 28 Tests und 14 Offline-Fälle bestanden, `10/5` weiterhin fünf Einzel-Tische. Live-/Raumnachweis offen.
- [x] Pair-Fallback erneut beschleunigt: `10/4` 31,9 → 5,9 s offline (81 % weniger Zeit), vollständiger Plan exakt erhalten. Frühe kanonische Sitzflächen-Kompatibilität und Abbruch unmöglicher Teilkombinationen; Produkt-/Tie-Reihenfolge erhalten. 46 Tests bestanden, zwölf Integrationspläne sowie `10/4`/`10/5` exakt erhalten. Live-Zeitmessung nach manuellem Neuladen offen.
- [x] Pair-Belegung nach visueller Bestätigung priorisiert: Bei gleicher Tischzahl/Topologie bevorzugt die größere Gruppe am Pair, `10/4` jetzt drei Personen am Pair und `3 + 2 + 2` an Singletons. 28 Tests und 14 Offline-Fälle bestanden; frische `10/4`-Läufe 3,1/2,3 s. Johannes bestätigt die aktuelle Belegung visuell als passend; vollständige Einzelvalidierung bleibt offen.
- [x] Aktuelle `15/5`-Sackgasse offline behoben: Source-abgeleitete Mittelpunkt-/radiale Reparaturstartpunkte vor dem Legacy-Fallback; volle kanonische Geometrie einschließlich Bodenkonturen erhalten. Kein Parkabstandsproblem, da alle fünf Tische aktiv sind. Johannes bestätigt die aktuelle Live-Stichprobe als passend; physische Prüfung offen.
- [x] Nach Johannes’ Bestätigung Gesamtweg vor strikter Aktiv-Wegpriorität bewerten; Groupwork-Parken darf mehrere ROI-Ränder nutzen. Aktuelle `5/1`-Quelle: Gesamtweg 608 → 315 cm, längster Weg 371 → 85 cm. Input-Standard unverändert; harte Geometriebedingungen bleiben erhalten. Beide aktuellen Korrekturen mit 42 fokussierten Tests und zwölf Offline-Fällen geprüft. Johannes bestätigt die aktuelle Live-Stichprobe als passend; vollständige Einzelvalidierung und physische Prüfung offen.
- [x] Freie Fläche nach erneuter `15/4`-Live-Stichprobe für Abstand getrennter Gruppen nutzen: bestehende Entzerrung mit weichem 60-cm-Ziel (Sitzflächentiefe), danach wieder Gesamtweg priorisieren; keine harte Ablehnungsgrenze. Aktuelle Quelle 0,5 → 60,4 cm Gruppen-Konturabstand bei rund 2,4 s; 35 Tests und zwölf gespeicherte Offline-Fälle geprüft. Live-Nachweis offen.
- [ ] Neue Groupwork-Laufzeit im laufenden Sender nach manuellem Neuladen prüfen; allgemeine Laufzeitgrenze und weitere Optimierung getrennt behandeln.
- [ ] Neue Groupwork-Vorschau einzeln im Room Editor, Lernformat-Interface und laufenden TD-Projekt prüfen; danach physische Prüfung. Bestehenden Sender beim manuellen Neuladen ersetzen, keine zweite Instanz starten.
- [x] Gemeinsamer Groupwork-Offline-Abschlusscheck: 130/130 Fälle (Counts 1–15, zulässige Gruppen 1–5, Editor-/Live-Quelle), kanonische gemeinsame Geometrie, relative Gruppenzuordnung, Identität/Scene Order und Determinismus. Beispiele sieben Personen auf Pair 4 + Singleton 3 sowie Einzel-Tisch `2 + 2 + 1`, geometrische Kapazität und technische 15-Slotgrenze getrennt geprüft. 52 Tests bestanden; Editor-Sackgasse `13/4`–`15/4` durch erneute Suche mit Konturfilter behoben. Live-Stichprobe der neuen Reparatur offen. [Prüfbericht](docs/GROUPWORK_ABSCHLUSSCHECK.md).

### Discussion

- [x] Umbauintensität mit Chairs repariert: Zwischenwerte wurden bisher abgelehnt, wodurch der Sender das alte Bild stehen ließ. Nach Interpolation jetzt gebundene Zweier-/Ringform samt Sitzflächen reparieren, ROI und Randparken erhalten; begrenzter Cache für Wiederholungen. 27 fokussierte Tests und 210 Offline-Fälle über zwei Szenen, Counts 1–15 und sieben Stärken bestanden.
- [x] Nach Johannes’ Rückmeldung war die starre Reparatur noch zu restriktiv. Lockerere Zwischenformen ausdrücklich freigegeben und umgesetzt: einzelne Tischposen samt gebundener Chair-/Sitzgeometrie; feste Zielform erst bei 100 %. 26 Tests und 210 Offline-Fälle bestanden, relative Abstände ändern sich in allen drei Stufen.
- [ ] Sender neu starten und lockere Discussion-Zwischenformen bei 0/25/50/75/100 % live prüfen; vollständige Sitz-/Bewegungsflächen und hohe Belegung können die Wirkung weiterhin begrenzen.

- [x] Pentagon-Zwischenplätze auf Johannes’ Wunsch radial nach außen verschoben: alle Chair-Mittelpunkte liegen auf dem Kreis der regulären Längsplätze, nominal rund 26,5 cm zusätzliche Verschiebung. Vollständige Sitzflächen werden mitverschoben und erneut auf ROI/Kollisionen geprüft; 22 Tests und 30 Offline-Fälle bestanden.

- [x] Pentagon-Belegung am 2026-10-15 angepasst: 13–15 Personen mit zehn Längsseitenplätzen und drei bis fünf Zwischenplätzen; höchstens zwei direkt je Längsseite. Kanonische Stirnkanten, volle Zwischenflächen und ROI-/Kollisionsprüfung wiederverwendet.

- [x] Überkreuzte Floor-Naht der Zweiergruppe offline auf die 5-cm-Konturzugabe je Tisch zurückgeführt. Rücknehmbarer Textport-Helfer vorbereitet und mit zehn Tests / 30 Fällen geprüft; keine Tischposen geändert. [Anleitung](docs/TOUCHDESIGNER_JOINED_FLOOR_CONTOURS.md).
- [x] Erste Floor-Naht-Korrektur von Johannes live ausgeführt: blendete die Innenkante aus, wodurch die Zweiergruppe wie ein Tisch wirkte. Update mit einer gemeinsamen gestrichelten Trennlinie vorbereitet; zwölf Tests einschließlich direktem Upgrade und Rücknahme bestanden.
- [x] Auf Johannes’ Wunsch stattdessen 10 cm Spalt zwischen den Längskanten der Zweiergruppe umgesetzt; vollständige ursprüngliche Floor-Konturen, gemeinsame Stirnflächen auf 170 cm erweitert. Vorbereitete Trennlinien-Korrektur damit abgelöst. 31 fokussierte Tests und 30 Offline-Fälle bestanden.
- [ ] TD-Kontur-Reparatur manuell zurücknehmen, Sender neu starten und Discussion neu generieren; 10-cm-Spalt, ursprüngliche Konturen und 6→7→6 visuell bestätigen. Keine automatische Speicherung.

- [x] Eckplätze am 2026-10-15 ergänzt: 9–12 Personen mit acht Längsseitenplätzen und ein bis vier zusätzlichen Eckplätzen; höchstens zwei direkt je Längsseite, bei zehn gegenüberliegende Ecken zuerst.
- [x] Teilnehmerstaffelung nach Johannes am 2026-10-15 umgesetzt: 1–4 Zweier-Tischgruppe mit gegenüberliegenden Längsplätzen; 5–6 zusätzliche Stirnplätze; 7–12 Vier-Tisch-Rechteck; 13–15 Pentagon. [Details](docs/DISCUSSION_CHAIRS.md).
- [x] Überzählige Tische am ROI-Rand parken, mindestens 60 cm von aktiven Tischen und außerhalb der Sitz-/Bewegungsflächen. Aktive/geparkte Auswahl gemeinsam nach Gesamtweg bewerten; alle IDs und Scene Order erhalten.
- [x] Standard-Count ohne explizite Teilnehmerzahl bleibt zwei Personen je verfügbarem Tisch; aktive Topologie folgt dem Count. Fehlende Tische für die Stufe und Counts über 15 klar ablehnen.
- [x] 50-cm-Chairs beibehalten; eigene Kantentangenz und 0,51 cm Rundungsüberstand vorläufig akzeptiert. Die beiden Tische der Zweiergruppe halten jetzt 10 cm Spalt; gemeinsame Stirnplätze bleiben mittig vor beiden Tischhälften.
- [x] Offline-Abschluss der neuen Staffelung: 30 Fälle aus zwei Ausgangsszenen für Counts 1–15, aktuell 22 fokussierte Discussion-/Rect-Template-Tests einschließlich Pentagon-Zwischenplätzen; Kontrollplots erstellt. Der frühere 90-Fälle-Nachweis vom 2026-10-09 betraf den vorherigen festen Ring.
- [ ] Discussion mit Chairs interaktiv bei 100 % im Room Editor, Learning-Format-Interface und TouchDesigner prüfen, insbesondere 4/5/6, Eckplätze bei 9–12, Zwischenplätze bei 13–15, 6→7, 12→13 und geparkte Tische; Berührungen und Rundungsüberstand dabei beurteilen.
- [ ] Präsentations-/Publikumsrollen nur definieren, falls das Format sie benötigt.

## Kontrollansicht für Layout-Stichproben

- [x] Manueller Helfer für `comp_layout_proposal/floor_tabletop_control` vorbereitet: Floor inkl. optionaler Chairs + bestehende blaue Tabletop-Source-Konturen + Tabletop-Motion-Pfeile. Syntax/Struktur offline geprüft, keine bestehenden Ausgaben geändert. [Anleitung](docs/TOUCHDESIGNER_LAYOUT_CONTROL.md).
- [x] Kontroll-COMP laut Johannes' Screenshot angelegt. Geometrieauswahl auf konkrete Slots `item1` bis `item5` begrenzt; Aktualisierung bestehender Kontrollansicht offline geprüft. Overlay übernimmt nun `render_tabletop`-Einstellungen mit ausschließlich Source-/Motion-Geometrien.
- [x] Johannes bestätigt die kombinierte Floor-/Tabletop-Kontrollansicht am 2026-10-08 als passend; kein physischer Projektionsnachweis.
- [ ] Reduktion der Referenzlinien im Network Editor separat bestätigen. Keine automatische Speicherung.

## NEXT — Manual layout validation

- [ ] Rect Groupwork: complete interactive Room Editor and TouchDesigner validation.
- [ ] Run one short cross-format pass for Input / Groupwork / Discussion covering format changes, Scene Order, full `100 %` targets, and OSC coupling.
- [ ] Perform remaining physical room validation for Input, Groupwork, and Discussion after virtual checks are stable.

## NEXT — Pilot / Study readiness

Status 2026-10-19: Die separate Study-/Pilot-Validierung ist auf Johannes'
Anweisung nicht mehr erforderlich. Die nachfolgenden historischen Prüfpunkte
werden nicht als aktueller Auftrag verfolgt; dies ist keine Testbestätigung.

- [ ] Validate Familiarization in the authoritative TouchDesigner project and physical room, including live switching between Floor-only and Dual-surface.
- [ ] Alle acht experimentellen `pilot_v8`-Trials in beiden Bedingungen im Raum prüfen; insbesondere T4 nach der Verschiebung um `+11 cm` in Welt-Y.
- [ ] Verify HOME, READY, ACTIVE, and COMPLETE transitions in the authoritative TouchDesigner project.
- [ ] Verify Floor-only and Dual-surface visuals match the written method description.
- [ ] Verify active-table and distractor binding for T3/T4 under real tracking.
- [ ] Verify objective arrival (`8 cm`, `5°`, `0.5 s`) under real tracking jitter.
- [ ] Verify participant-declared completion remains independent from objective arrival.
- [ ] Verify logs, session manifest, attempt/run indices, tracking-loss intervals, and trial-definition hash.
- [ ] Review human-readable `trials.json` notes against numeric poses without changing frozen geometry casually.

Done when a participant-like session runs without manual data repair and visuals, tracking, controller state, and logs stay synchronized.

## NEXT — Freeze analysis plan before data collection

- [ ] State one primary research question comparing Floor-only and Dual-surface.
- [ ] State a secondary/exploratory question about task-specific differences.
- [ ] Describe T1–T4 as a 2×2 design structure without claiming unverified orthogonality.
- [ ] Define exactly what information appears on each surface in each condition.
- [ ] Choose primary, secondary, and exploratory outcomes.
- [ ] Decide whether the sample is framed as pilot/exploratory.
- [ ] Predefine treatment of aborted trials, tracking loss, missing objective arrival, and repeated attempts.
- [ ] Document apparatus accuracy, tracking frequency/latency, projection, and calibration sufficiently for the paper.

## OPEN DECISIONS — Johannes

- [ ] Ist `pilot_v8` bereit für die Datenerhebung oder weiterhin eine Vorpilot-Konfiguration?
- [ ] Which Study measures are formally primary versus secondary/exploratory?

## DEFERRED — Documentation

- [ ] Update the root `README.md`; current prototype-status, vision, geometry, and priority sections are outdated.
- [ ] Mark `docs/PROJECT_STATE_2026-05.md` clearly as historical or replace it with a dated current state.
- [ ] Link `docs/PROJECT_CONTEXT.md`, `docs/DECISIONS.md`, and `TODO.md` from the README.
- [ ] Ensure macOS and Windows launch instructions reflect actual supported workflows.
- [ ] Document current Study controller, active trial version, logging, and metrics commands.
- [ ] Keep physically confirmed facts separate from repository-only verification.

## DEFERRED — Focused regression commands

There is no canonical repository-wide command. Confirm and document the narrowest working commands for:

- Rect layout/geometry;
- Study trial definitions;
- Study control/state transitions;
- Study tracking/binding;
- Study logging/metrics;
- TouchDesigner builder structure tests;
- vision table association and tracking-only OSC.

Do not install optional dependencies merely to expand test scope.

## DEFERRED — General layout follow-up

- [ ] Verify mixed Summit/Sprint/Rect layouts after current Rect-specific work is stable.
- [ ] Design Scout-specific seating and Groupwork semantics as a dedicated task.
- [ ] Decide which Summit/Sprint sides may pair and how seating zones are derived.
- [ ] Preserve generic polygon support so the decision does not require a geometry rewrite.

## DEFERRED — Tracking

- [ ] Keep the current tracking baseline frozen until a reproducible failure is recorded.
- [ ] If tuning resumes, capture the failing scene/log first and compare against the successful reacquisition baseline.
- [ ] Separate detection, association, smoothing, projection alignment, and Study binding when diagnosing failures.

## DEFERRED — Repository hygiene

- [ ] Decide whether `.gitignore` should cover recurring debug/runtime folders.
- [ ] Never blanket-ignore intentionally versioned data such as frozen trial definitions.
- [ ] Keep model files, calibration captures, run logs, and generated plots under explicit policy rather than ad hoc staging.
