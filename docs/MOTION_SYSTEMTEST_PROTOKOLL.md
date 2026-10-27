# Motion: reale Systemabnahme

Stand: 2026-10-27. Untertisch-Versuch bleibt pausiert.
Vorhandene Fünftisch-Simulation zählt nicht als reale Fünftischprüfung.

## Gesamtabschluss durch Johannes — 2026-10-27

Johannes meldet ausdrücklich: „alle Systemtest abgeschlossen. Stand sichern“.
Die reale Systemtestphase wird auf Grundlage dieser manuellen Gesamtbestätigung
geschlossen. Die unten einzeln dokumentierten positiven Fälle bleiben als
konkrete Befunde erhalten; zuletzt nicht gesondert gemeldete Parameter, IDs,
Laufzeiten oder GPU-Berichte werden nicht nachträglich erfunden. Frühere offene
Testschritte sind historische Zwischenstände, keine neue Aufforderung zur
Wiederholung der bereits insgesamt abgeschlossenen Prüfung.

Offline-Codeprüfungen, tatsächliche native GPU-Installationsberichte und
Johannes' physische Sichtbefunde bleiben getrennte Nachweisarten. Gesamtabschluss
ist kein unabhängiger automatisierter Projektionsnachweis und kein Beleg für
eine neue Speicherung der TD-Datei. Kompakte Übergabe:
[Motion-Checkpoint](MOTION_CHECKPOINT_20261027.md). Untertisch bleibt pausiert.

## Groupwork ein Tisch bestanden, nächster Fall zwei Tische — 2026-10-27

Johannes bestätigt Groupwork mit einem realen Tisch/drei Teilnehmenden/einer
Gruppe: drei Chairs, eine Welle, Source und Feedback folgen. Änderung auf zwei
Teilnehmende ohne Aktivierung erhält Ziele/drei Chairs. Raumfall bestanden;
Berechnungsdauer und damalige ID/Revision nicht nachgereicht.

Lesender Gegencheck danach ist ein anderer aktueller Zustand: Sitzung 2730811/
Revision 16, Input/13 Chairs, fünf frische IDs `table_00`, `table_03`, `table_04`,
`table_05`, `table_06`, TD freigegeben, letzte Berechnung 0,009814 s. Dies nicht
als technischen Nachweis des zurückliegenden Eintisch-Groupwork-Falls ausgeben.

Nächster Raumfall: genau zwei erkannte Rect-Tische, Groupwork/sechs Teilnehmende/
zwei Gruppen. Beide IDs frisch abwarten, einmal aktivieren. Sechs Chairs, zwei
Gruppen, eine Welle, Einzel- und gleichzeitige Bewegung/Drehung beider Tische
ohne Vertauschung; Ziele/Chairs fest. Dann Gruppenzahl auf eins nur vormerken,
nicht aktivieren: Ziel-/Chair-Positionen und Revision unverändert. Erst nach
positivem Befund Ein-Gruppen-Fall gezielt aktivieren und gesondert prüfen.

## Aktueller Wiedereinstieg nach Konturabnahme — 2026-10-27

Johannes bestätigt native Kontur-/Chair-Installation `passed: true` und positiven
Sichtbefund. Lesender Webstatus: Sitzung 2730811/Revision 5, fünf frische IDs
`table_00`–`table_04`, Groupwork/15 Chairs, automatische TD-Freigabe aktiv.
Letzte Berechnung 14,503 s für diese Posen, anderer Fall als frühere 2,028 s.
Keine zusätzliche Vollprüfung während Reveal, keine Neustarts/Speicherung.

Input 1–5 und Groupwork fünf Tische/15 Teilnehmende/drei Gruppen positiv.
Jetzt Groupwork-Counts 1–4 nachholen, danach Discussion und gemeinsame Fälle.
Nächster Fall: genau einen Rect-Tisch im erkannten ROI belassen, frisch abwarten;
AISI darf bis zum neuen gültigen Vorschlag ausblenden. Groupwork/drei Teilnehmende/
eine Gruppe einmal aktivieren: drei Chairs, eine Welle, Freigabe, richtige
Source-/Feedback-Bindung und feste Ziele prüfen. Danach Teilnehmende auf zwei
stellen, nicht aktivieren: Ziele/drei Chairs/Revision bleiben. Berechnungsdauer
und Sichtbefund melden. Andere Parameter vor den jeweiligen Counts festlegen.

## Gestalterischer Zwischenstand: Feedback und Abschluss — 2026-10-27

Gemeinsame Hakenanzeige danach nativ mit `passed: true` installiert. Johannes
bestätigt im Raum mit zwei Tischen: früher Haken bleibt bis zur zweiten Ankunft,
anschließend verschwinden beide gemeinsam. Akzeptiert. Anfangs korrekte Tische
und Ausfälle des neuen Hakenpfads weiter offen; keine Speicherung gemeldet.

Johannes bestätigt `update_motion_feedback_size_cutouts.install`: `passed: true`,
Feedbackgröße passend, Ausrichtungshilfen wieder transparent ausgespart.
Damit native GPU-Installation und Sichtbefund positiv; keine neue manuelle
Speicherbestätigung. Anschließender Gruppenhaken-Trial inzwischen nativ und
mit zwei Tischen im Raum bestätigt (siehe vorstehender Absatz).

## Ausgangspunkt

- Git: `vision/wip-dark-proposals`, Basis `a20a9ff`; aktuelle Änderungen noch
  uncommitted, lokale Laufzeit-/Simulationsdaten erhalten.
- Laufender Backend-Status: Kamera/Scene/Study/Legacy-OSC/UI je eine Prozesskette,
  alter Tk-Controller nicht vorhanden. Frische `table_00`, Sitzung 511129,
  Revision 2, Input/drei Chairs, `td_approved: true`.
- Einzelner realer Tisch bereits mit Bewegung, festen Zielen/Chairs, automatischer
  Freigabe und kurzer Occlusion geprüft. Neuer Reveal im Raum flüssig/vollständig
  bestätigt; reduzierte UI gestalterisch akzeptiert. Mehrtischfälle noch offen.
- TD wird ausschließlich manuell bedient/gespeichert. Neuester gespeicherter
  Dateiname nicht erneut gemeldet. Keine Kalibrierungsänderung oder Screensharing.

## Block A: Input

Prüfwerte bewusst innerhalb der bisherigen Kapazität wählen, nicht Generator-
Grenzen neu definieren. Bei unerwarteter Ablehnung konkreten Status erfassen.

| Reale Tische | Teilnehmende | Ergebnis | Bemerkung |
| --- | --- | --- | --- |
| 1 | 3 | Basis bereits bestätigt | Einzelbetrieb; keine neue Mehrtischabnahme |
| 2 | 6 | im Raum bestanden | Sechs Chairs, eine Welle, richtige Source-/Feedback-Bindung, Ziele/Chairs fest, keine Vertauschung |
| 3 | 9 | im Raum bestanden | Neun Chairs, eine Welle, keine Vertauschung; Änderung auf acht ohne Aktivierung erhält Ziele/neun Chairs |
| 4 | 12 | im Raum bestanden | Zwölf Chairs, eine Welle, keine Vertauschung auch bei zwei gleichzeitig bewegten Tischen; Ziele/Chairs fest |
| 5 | 15 | im Raum bestanden | 15 Chairs, eine Welle, keine Vertauschung; kurze Verdeckung mit Rückkehr ohne neue Welle, Ziele/Chairs fest |

Je Zeile erfassen: tatsächliche IDs/Revision, automatische Freigabe und einmalige
Reveal-Welle, Ziel-/Chair-Menge und sichtbare Zuordnung, jedes Source/Feedback
bei Bewegung/Drehung der richtigen ID zugeordnet, Ziele/Chairs fest. Bei zwei
Tischen zusätzlich Einstellungen ohne Aktivierung ändern, Unverändertheit
prüfen und erst danach bewusst neue Aktivierung mit einmaliger Revision/Welle.

Johannes bestätigt Input mit zwei Tischen. Lesender technischer Gegencheck:
Sitzung 511129, Revision 4, `table_00`/`table_01`, sechs Chairs, Quelle frisch,
`td_approved: true`. Offener Nebenbefund: Chairs erscheinen vor der Reveal-Welle.
Gezielter Chair-Shader-Patch danach installiert (`passed: true`) und von Johannes
im Raum abgenommen: Chairs erscheinen jetzt erst mit der Reveal-Welle.
Lesender Gegencheck: Sitzung 511129/Revision 5, dieselben zwei IDs, sechs Chairs,
Quelle frisch und TD freigegeben. Speicherung dieser Reparatur noch nicht
bestätigt. Nächster Fall: Input mit drei Tischen/neun Teilnehmenden; zusätzlich
neun auf acht Teilnehmende ohne Aktivierung ändern und feste neun Chairs prüfen.

## Block B: Groupwork

### Auffälliger Direktfall: fünf Tische / 15 Teilnehmende / drei Gruppen

Nach Optimierung von Johannes bestätigt: deutlich schneller, Freigabe/Reveal/
Darstellung passend, Ziele und Chairs fest. Lesender Gegencheck: Sitzung
2730811/Revision 3, fünf frische IDs, 15 Chairs, `td_approved: true`, reine
Berechnung 2,028 s für die dabei aktuellen Posen. Dieser positive Raumfall
ist dokumentiert; andere Counts/Gruppenverteilungen bleiben offen. Gestalterischer
Zwischenauftrag gestrichelte Zielkontur unterbricht die weitere Testfolge.

Johannes überspringt zunächst die kleinen Counts und meldet mindestens eine
Minute bis Layout/Reveal; UI zeigt währenddessen „Vorschlag wird berechnet“.
Technisch danach Sitzung 511129/Revision 10, alle fünf IDs, 15 Chairs und
automatische Freigabe. Noch kein vollständiger Bewegungs-/Stabilitätsnachweis
für diesen Groupwork-Fall; keine reguläre Performance-Abnahme.

Diagnose offline, ohne OSC/TD: aktuelle Posen zunächst 2,764 s, dagegen aus
vorhandenem Kamera-JSONL rekonstruierter Frame 91650 etwa 0,0764 s vor der
letzten Einstellungs-/Aktivierungsdatei 52,406 s. Damit Suchaufwand stark von
Ausgangsgeometrie abhängig, lange Wartezeit im Generator reproduziert.
Nach anfrageinternem Wiederverwenden identischer lokaler Optionen und
kanonischer Geometrie-/Kompatibilitätsurteile: 10,162 s auf demselben Replay,
Tischziele und sämtliche Chair-Daten exakt identisch zur Vorher-Ausgabe.
Keine Kandidaten oder Geometriebedingungen reduziert. Andere Posen müssen
weiter geprüft werden; keine allgemeine Laufzeitobergrenze daraus ableiten.

56 Groupwork-/Geometrie-/Cachefälle und 392 Motion-Fälle bestanden, sieben
optionale GPU-Fälle übersprungen. Optimierung im gemeinsamen Controller nach
bestätigter automatischer TD-Sperre bereitgestellt, Kamera/andere Dienste
erhalten. Neue Sitzung 2730811 zunächst ohne Vorschlag. Nun denselben UI-Fall
erneut aktivieren, Dauer unter Diagnose/Berechnung und Raumverhalten melden.
Runtime-Replays und Messdaten unter
`data/aisi/debug/groupwork_timing_20261027/`, nicht als Produktiv-/Studydaten stagen.

Input 1–5 damit im Raum abgenommen. Einstieg in Groupwork: ein realer
Rect-Tisch, drei Teilnehmende, eine Gruppe. Zulässig nach bestehendem Planner;
keine Änderung an Kapazitätsregeln. Erst nach erfolgreicher Aktivierung drei
Chairs und Bewegung/Rotation prüfen; Teilnehmerzahl danach auf zwei ändern,
ohne zu aktivieren: bisherige Ziele/drei Chairs und Revision müssen bleiben.
Dieser Groupwork-Fall inzwischen von Johannes im Raum bestätigt (siehe oben).

Counts 1–5 getrennt prüfen, jeweils zulässige Gruppen-/Teilnehmendenzahl
vor dem Fall festlegen und notieren. Unzulässige Konstellationen als saubere
Ablehnung prüfen, nicht als bestandene positive Raumdarstellung zählen.
Positiver Fünftischfall mit 15 Teilnehmenden/drei Gruppen inzwischen bestätigt;
Count 1 inzwischen bestätigt; Counts 2–4 und weitere Gruppenverteilungen offen.

## Block C: Discussion

Counts 1–5 mit zulässigen Parametern und höchstens 15 Chairs getrennt prüfen.
Noch keine realen Mehrtischfälle dieses Blocks bestätigt.

## Gemeinsamer Abschluss

Erst nach Einzelabnahme: Input → Groupwork → Discussion → Input über UI mit
gleicher Tischmenge. Auswahl allein ändert nichts; erfolgreiche Aktivierung
übernimmt vollständige Ziele/Chairs einmalig. Fehler erhalten letzten gültigen
Vorschlag/Revision. Kurze Occlusion und Tischzahländerung bei mehreren Tischen
sowie Modi 0/1/2 prüfen; Rechner-Kaltstart bleibt eigener Nachweis.

Alle Ergebnisse getrennt notieren: Offline-Codeprüfung, technische TD-/GPU-
Freigabe und physischer Sichtbefund. Automatische Freigabe ersetzt nicht den
Raumnachweis. Keine Gesamtfreigabe aus einem einzelnen Tischcount ableiten.
