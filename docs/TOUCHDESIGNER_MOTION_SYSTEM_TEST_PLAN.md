# Motion im aktuellen AISI-System — nächste Arbeitsblöcke

Stand: 2026-10-27. Reihenfolge ausdrücklich von Johannes vorgegeben:
**Systemtest → Motion als Standard → Learning-Format-UI modernisieren.**
Der separate Untertisch-Versuch bleibt pausiert und ist keine Voraussetzung.

## Abschlussmeldung — 2026-10-27

Johannes bestätigt sämtliche Systemtests abgeschlossen. Die folgenden Test-
und Zwischenstandsabschnitte sind die historische Planung, nicht erneut
auszuführen. Einzelbefunde und Grenzen der pauschalen Abschlussmeldung stehen
im [Systemtestprotokoll](MOTION_SYSTEMTEST_PROTOKOLL.md), konsolidierter Stand
im [Checkpoint](MOTION_CHECKPOINT_20261027.md). Aktueller Auftrag nur Sicherung;
die abschließende Konsolidierung zum regulären Standard bleibt nächster Block.

## Historischer Wiedereinstieg: reale Mehrtischprüfung — 2026-10-27

Auf ausdrückliche Folgeaufträge inzwischen umgesetzt: gemeinsamer Start,
Web-Aktivierung, automatische TD-Prüfung/Freigabe, kein Legacy-Fallback im
AISI-Modus, Reveal nach Prüfung und reduzierte UI. Diese Teile wurden einzeln
geprüft; vollständige reale Mehrtischabnahme ist damit nicht ersetzt. Die unten
beschriebene ursprüngliche Anschlusslücke und Reihenfolge sind historisch.

Jetzt je Lernformat einzeln vorgehen: **Input bis fünf Tische → Groupwork bis
fünf Tische → Discussion bis fünf Tische → gemeinsamer Formatwechsel**.
Nur fachlich zulässige Parameter als positive Fälle bewerten; ein Fehler wird
diagnostiziert und nicht durch geänderte Kalibrierung oder Generatorregeln verdeckt.

Arbeitsprotokoll mit tatsächlichen Raumfällen:
[Motion-Systemtestprotokoll](MOTION_SYSTEMTEST_PROTOKOLL.md).
Status des Web-/Motion-Endpunkts darf lesend abgefragt werden; keine weitere
Textport-Freigabe und keine zusätzliche Vollprüfung während der Reveal-Welle.
Sichtbefunde stammen von Johannes, keine Bildschirmzugriffe.

Pro gültigem Fall: Tischzahl/IDs frisch, explizite Aktivierung einmal, automatische
Freigabe, passende Ziel-/Chair-Menge, genau eine vollständige Welle. Jeden Tisch
einzeln verschieben/drehen: Source/Feedback folgen der richtigen ID, Ziele/Chairs
bleiben fest. Anschließend Parameter nur ändern und feste Ziele/Revision prüfen;
erst erfolgreiche erneute Aktivierung darf sie gemeinsam ersetzen.
Beim Hinzufügen/Entfernen eines Tisches darf die Ausgabe bis zur nächsten
gültigen Aktivierung ausgehen. Das ist die beschlossene Sperre bei abweichender
Quellen-/Masken-/Vorschlagsmenge, kein Anlass zum Neustart oder Neukalibrieren.

Aktueller technischer Ausgangspunkt: eine eigene Prozesskette je Kamera, Scene,
Study, Legacy-OSC und UI, kein alter Tk-Controller; frische `table_00`, Input,
drei Chairs, Sitzung 511129/Revision 2, TD automatisch freigegeben. Git-Basis
`a20a9ff`, aktuelle Integrations-/UI-Patches uncommitted im erhaltenen Worktree.
Physische Arbeitsdatei nach manueller Speicherung vorhanden; neuer Name noch
nicht erneut gemeldet. Aktueller Einstieg: zweiten Rect-Tisch hinzufügen,
Input mit sechs Teilnehmenden aktivieren und Bewegungs-/ID-Bindung prüfen.

## 1. Aktuellen AISI-Betrieb Ende zu Ende prüfen

Ziel: aktuellen Kamera-/Szenen-/Generator-/UI-/OSC-Pfad zusammen mit Motion
im tatsächlich geöffneten TD-Projekt prüfen, mit bis zu fünf realen Rect-Tischen.
Vorhandene Fünftisch-Simulation ist ein Vorabnachweis, kein Ersatz für reale
Mehrtischprüfung. Welche Tischanzahlen im Raum verfügbar und geprüft sind,
jeweils protokollieren. Nicht verfügbare Raumfälle als offen kennzeichnen.

Zuerst Arbeitsdatei, aktiven Git-/Dienstestand und tatsächliche TD-Routing-
Freigaben/Quelle lesend erfassen; keine Dienste blind doppelt starten. Frühere
Session-/Revision-/ID-Werte nicht als aktuelle Bedingungen hart codieren.
Letzte technisch bestätigte Basis: einzelner realer Tisch, stabile ID,
Originalmaskenabgleich und AISI-Indizes 1/1/0/1. Fünftisch-Nachweise bisher
vorwiegend Simulation; umfassende reale Mehrtisch-/UI-Abnahme fehlt.

### Historischer Anschlussabgleich — inzwischen behoben

Codeprüfung: `motion_live_control.py` liest `learning_format_server.read_state()`
nur bei seiner lokalen Tk-Aktion `activate()` / „Vorschlag aktivieren“.
Die Web-UI `/set` schreibt Format/Einstellungen; nur `action=regenerate`
erhöht deren `layout_revision`. Der Motion-Controller wertet diese Web-Revision
derzeit nicht als Aktivierungsauftrag aus. Eine vollständige direkte Web-UI-
Aktivierung darf daher noch nicht als vorhanden/getestet bezeichnet werden.

Diese funktionale Kopplung im ersten Block prüfen und gegebenenfalls gezielt
herstellen, bevor der vollständige Systemtest als bestanden gilt. Bis dahin
ist „UI einstellen → separaten Kamera-Controller aktivieren“ nur ein ausdrücklich
bezeichneter Zwischenpfad. Keine grafische UI-Neugestaltung vorziehen.

Verbindliche Semantik aus D005a: Nur bewusste erfolgreiche Vorschlagsaktivierung
berechnet aus aktuellen Istposen, übernimmt Tischziele und Chairs gemeinsam und
erhöht die Motion-Revision einmal. Änderungen von Teilnehmenden/Gruppen/
Präsentationsseite und Tischbewegung aktivieren nichts. UI-Auswahl und tatsächlich
aktives Layout unterscheidbar halten; Formatwechsel nur bei bewusster Aktivierung
übernehmen. Fehlgeschlagene Vorschläge erhalten vorheriges Layout und Revision.

### Prüfumfang in dieser Reihenfolge

| Schritt | Prüfung | Erwarteter Nachweis |
| --- | --- | --- |
| Input | 1–5 Tische mit fachlich gültigen Parametern | UI-Aktivierung, gleiche IDs für Source/Ziel, richtige Ziel-/Chair-Menge, Maskenabgleich und Sichtbefund |
| Groupwork | 1–5 Tische soweit Gruppenzahl/Kapazität zulässig | Gruppenplanung und gemeinsame Ziel-/Chair-Aktivierung; unzulässige Kombinationen sauber ablehnen |
| Discussion | 1–5 Tische soweit zulässig | Formatsemantik, Stuhlzuordnung, Kapazität und bestehende Grenze von 15 Chair-Slots beachten |
| Gemeinsam | Formatfolge Input → Groupwork → Discussion → Input | Genau eine Aktivierung/Reveal pro erfolgreichem Vorschlag; keine zusätzliche Neuberechnung |
| Bewegung | Einzelne und mehrere Tische bewegen/drehen | Source/Feedback folgen; Ziele/Chairs bleiben fest; Navigation, Ausrichtung, Erfolgshaken und Wiedereinblendung korrekt |
| Einstellungen | Werte ändern, zunächst nicht aktivieren | Ziel-/Chair-Positionen und Revision bleiben unverändert; neue Werte erst bei erfolgreicher Aktivierung |
| Tracking | Kurze Verdeckung, Reakquisition, fehlende/alte Daten, Tischzahländerung | Keine Ghosts oder stille ID-Umhängung; nötige neue Zuordnung ausschließlich explizit aktivieren |
| Fehler | Unzulässige Kapazität, ROI-/Kollisionsfehler, Rechenfehler | Fehlermeldung statt stillem Fallback; bisheriger gültiger Vorschlag bleibt erhalten |
| Modi | Tracking-only / Study / AISI sowie Kalibrierungsansicht | Bisherige Modi und Masken-/Projektorkette erhalten, Motion ausschließlich im vorgesehenen AISI-Pfad |
| Neustart | Backend und manuell gespeicherte Arbeitsdatei | Eindeutige Quelle, keine doppelten Sender, frische Daten und passende Masken vor Ausgabe |

Jedes Format einzeln vom Generator bis zur Raumdarstellung abnehmen, erst dann
kurzen formatübergreifenden Durchlauf. Ungültige Fälle nicht durch Änderungen
an Generatorregeln oder Kalibrierung künstlich passend machen. Source-/Runtime-
Verfügbarkeit bewahren. Resultate getrennt als Offline-, TD-/GPU- und Raumprüfung
mit tatsächlicher Tischzahl festhalten.

## 2. Motion als Standard im AISI-Modus einrichten

Erst nach erfolgreicher Systemabnahme. Motion in den regulären Start-/Betriebspfad
übernehmen, sodass kein paralleler experimenteller Bedienweg erforderlich bleibt.
Startverhalten, Quelle/Aktualität, ID-Bindung, Layoutaktivierung und Abschaltung
bei fehlender gültiger Grundlage eindeutig gestalten. „Standard“ ersetzt keine
Prüfung der Quelle oder Masken. Tracking-only und Study bleiben erhalten.
Ein vorhandener reversibler Rückweg bleibt verfügbar; keine Umstellung der
Kalibrierung oder physischen Masterdatei. Neustart und regulären UI-Betrieb
anschließend erneut prüfen, Übergabedokumente aktualisieren. TD weiterhin nur
manuell durch Johannes speichern.

## 3. Learning-Format-UI grafisch und in der Bedienung modernisieren

Nach stabiler Standardintegration, auf der geprüften Aktivierungssemantik.
Klare visuelle Hierarchie, zeitgemäße Typografie/Abstände/Farben, große
Bedienelemente für Tablet/Telefon und erkennbare Auswahl. Aktives Format,
vorgemerkte Einstellungen, verfügbare Tische sowie Bereit-/Fehlerstatus verständlich
unterscheiden. Formatabhängige Einstellungen übersichtlich zeigen; Aktivieren
als eindeutige bewusste Aktion gestalten. Keine internen Session-/OSC-Details als
normale Bedienanforderung. Vorhandene Fachsemantik und vollständiger Vorschlag
bei 100 % bewahren; keine neue veränderliche Umbauintensität einführen.
Endgültige Gestaltung erst in diesem dritten Block konkretisieren und abnehmen.

## Unverändert geschützt

Homographien, Kalibrierungspunkte, Projektortransforms, lokale Korrekturen,
Edge Blending, Weltmaßstab, Projektor-Footprints und Maskenreihenfolge.
Die Masterdatei `AISI_v2.toe` weder überschreiben noch automatisch speichern.
Kein Bildschirmzugriff; TD-Befunde über manuelle Textport-Ausgaben und
Sichtbefunde von Johannes. Der Untertischversuch wird in keinem dieser Blöcke
automatisch fortgesetzt.
