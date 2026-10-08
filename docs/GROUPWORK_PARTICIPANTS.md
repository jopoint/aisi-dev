# Teilnehmendenbasierter Rect Groupwork — Offline-Handoff

Stand: 2026-10-08. Teilnehmendenmodell mit Vorschau-Anbindung auf Branch `vision/wip-dark-proposals`;
OSC-Anbindung im Code; kein laufender Sender neu gestartet, keine TD-Fernsteuerung, kein Speichern einer `.toe`.

## Umgesetzt

`src/aisi/generation/groupwork_participants.py` bildet möglichst gleich große
Teilnehmergruppen aus `participants` und `number_of_groups`. Ein eigener
Clusterdatensatz hält Teilnehmergruppe, Tischidentitäten und Belegung getrennt.
Mehrere Singletons/Pairs dürfen einer Teilnehmergruppe angehören.
Tischziele kommen in Source Scene Order zurück; Cluster-/Chair-Zuordnung ist
deterministisch. Inaktive Tische bleiben sichtbar und werden mit dem vorhandenen
Parkverfahren platziert. Ein begrenzter Cache liefert Kopien statt veränderbarer
gemeinsamer Ergebnisse.

Der vorhandene Groupwork-Suchkern unterstützt optional vorgegebene Clustergrößen
und eine zusätzliche vollständige Kandidatenprüfung. Sein bisheriger Aufruf
behält die bestehenden Pair-/Singleton-Regeln. Bei vier/fünf Singletons werden
zusätzlich konservative Hüllrechtecke aus den kanonischen Sitzflächen mit der
vorhandenen kontinuierlichen Hard-Constraint-Reparatur verschoben. Zunächst
werden Source-Winkel erhalten, bei fehlender Lösung Raumachsen versucht.
Die Endprüfung verwendet ausschließlich tatsächliche kanonische Tisch- und
Sitzpolygone sowie vollständige Chair-Kreise. Dieser zusätzliche Reparaturpfad
gilt bisher nur für Singleton-Profile mit ausschließlich Längsseitenplätzen.

Singletons nutzen die bisherigen beidseitigen abgerundeten 60-cm-Längsstreifen,
bei belegten Stirnseiten zusätzlich geometrisch entsprechend abgerundete
60-cm-Stirnseitenstreifen. Pairs behalten ihre bestehende Ellipse und 8-cm-Seam;
die innere Seam erhält keine Sitzplätze. Chair-Radius bleibt 25 cm.
Reguläre Längsseiten werden vor regulären Stirnseiten und diese vor Verdichtung
belegt. Bei fünf Personen am Einzel-Rect ergibt sich `2 + 2 + 1`.
Profile enthalten theoretische Positionsobergrenzen; erst die Kreis-/Flächenprüfung
entscheidet, welche Belegung tatsächlich möglich ist. Insbesondere begrenzt
die Pair-Ellipse mögliche Randpositionen.

Geprüft werden Teilnehmer-/Chair-Counts, Gruppen-/Cluster-/Tischzuordnung,
ROI, Tisch-/Chair-Kollisionen, freie Sitz-/Bewegungsflächen, Pair-Geometrie
und Parktische. Ein vorläufiger relativer räumlicher Test fordert, dass die
Verbindungen innerhalb einer Teilnehmergruppe kürzer als alle Abstände
zwischen Clusterzentren verschiedener Gruppen sind. Vollständige Bewegungspfade,
Raumerschließung und physische Gruppenerkennbarkeit sind damit nicht belegt.

## Nachweise

65 fokussierte Tests bestanden: Groupwork-Teilnehmendenmodell (9), Rect-Templates
(11), synthetische Input-Geometrie (10), Tracking-/OSC-Isolation (24) und
kanonische Footprint-Reparatur (11). Das Sieben-Personen-Beispiel Pair mit vier
plus Singleton mit drei Plätzen sowie die Fünf-Personen-Sitzpriorität sind
direkte Regressionstests. Die gezielte Groupwork-Suite wurde nach der letzten
Reparaturanpassung erneut bestanden.

Zehn Offline-Integrationsfälle bestanden: Editor und eine beim Prüflauf
eingelesene Live-Quelle; `5/1` für beide Tischprioritäten, `7/2`, `10/2`, `15/5`
für die Priorität wenige Tische. Jeweils gleiche Wiederholung und umgekehrte
Scene Order geprüft. Die zunächst nicht gefundene `15/5`-Lösung der Live-Quelle
wurde durch den vollständigen Singleton-Reparaturpfad ermöglicht.
Es wird keine Vollständigkeit der begrenzten Suche behauptet; fehlende gültige
Kandidaten werden als `LayoutConstraintError` ausdrücklich abgelehnt.

Lokale Ergebnisse und Vergleichsplot:
`data/aisi/debug/groupwork_participant_preview_2026-10-08/review/`.

```sh
MPLBACKEND=Agg MPLCONFIGDIR=/private/tmp/aisi-mpl .venv/bin/python scripts/validate_groupwork_participants.py --output /private/tmp/aisi-groupwork-check
# Exakt gespeicherte Quellen erneut verwenden:
MPLBACKEND=Agg MPLCONFIGDIR=/private/tmp/aisi-mpl .venv/bin/python scripts/validate_groupwork_participants.py --fixtures data/aisi/debug/groupwork_participant_preview_2026-10-08/review/validation.json --output /private/tmp/aisi-groupwork-recheck
```

## Tischpriorität

Die Tischwahl ist in zwei überprüfbaren Varianten vorbereitet:

- `few_tables`: zuerst wenige aktive Tische, danach geringe Verdichtung und
  wenige Stirnseitenplätze. Fünf Personen können einen Einzel-Rect mit `2 + 2 + 1` nutzen.
- `regular_seats`: zuerst geringe Verdichtung und wenige Stirnseitenplätze,
  danach wenige Tische. Fünf Personen können zwei Singletons mit `3 + 2`
  regulären Längsseitenplätzen nutzen; die drei Personen eines Singletons sitzen
  dabei über beide Längsseiten verteilt, nicht verdichtet an einer Seite.

Johannes bestätigt `few_tables`: fünf Personen bevorzugt am Einzel-Rect mit
`2 + 2 + 1`. Diese Priorität ist der Standard des Modells und der opt-in Vorschau.
`regular_seats` bleibt als explizite Offline-Vergleichsoption verfügbar.

## Vorschau und OSC

`compute_synthetic_layout` erzeugt bei aktivierter Vorschau auch Groupwork-Chairs.
Der bestehende `prepare_scene_output` übergibt sie mit unveränderten Float-Adressen
`/chair/{index}/{x,y,radius}`; Tischziele bleiben in Source Scene Order.
Anfragen über 15 werden vor der Synthese aufgrund der technischen TD-Slots
abgelehnt, ohne Kürzung oder Ersatzlayout. Dies begrenzt nicht das Offline-Modell.
Bei Stärke 0 bleiben Source-Positionen und Winkel exakt, ohne Reparatur oder Chairs.
Bei positiver Teilstärke erfolgt zuerst das vorhandene Shortest-angle-Blending,
danach vollständige Cluster-Reparatur. Teilnehmergruppen, Cluster und Tischrollen
bleiben gebunden; wenn keine gültige Reparatur gelingt, folgt ausdrückliche Ablehnung.
Chairs werden aus den reparierten Sitzflächen neu abgeleitet.
Ein begrenzter Cache liefert unabhängige Kopien für wiederholte OSC-Ausgaben.

52 fokussierte Tests bestanden: neues Groupwork-Vorschau-Modul (6),
Groupwork-Teilnehmendenmodell (9), Tracking-/OSC-Isolation (24), synthetische
Input-Geometrie (10) und Lernformat-Interface (3). Nach Ergänzung des Teilstärken-
Caches wurden die sechs Vorschautests erneut bestanden; enthalten sind auch
unabhängige Cache-Kopien. OSC wurde ausschließlich mit einem lokalen Recorder
auf Float-Adressen, Source-/Target-Indexbindung und Radius-null-Ausblendung geprüft.
18/18 Offline-Adapterfälle aus den gespeicherten Editor-/Live-Quellen bestanden:
`5/1`, `7/2`, `15/5` jeweils bei 0 %, 50 % und 100 %, mit gleicher Wiederholung.
Bericht: `review/adapter_validation.json` neben dem bisherigen Offline-Bericht.
Keine neuen Netzwerkpakete, keine Aussage zur physischen Darstellung.

Die laufende Anwendung wurde nicht neu geladen und kein OSC-Paket ins laufende
TD-Projekt gesendet. Nächster Block: interaktive Groupwork-Einzelprüfung mit
bestehendem Sender nach manuellem Neuladen, insbesondere fünf Personen/eine Gruppe
bei 100 %, dann Count-/Gruppenwechsel und Teilstärken. Physische Gruppenerkennbarkeit
und Projektion bleiben separat offen. Input, Discussion, Study, Tracking,
Kalibrierung und Projektorkonfiguration bleiben unverändert.
