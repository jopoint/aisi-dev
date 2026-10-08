# Groupwork-Laufzeit — Offline-Prüfung

Stand: 2026-10-08. Auftrag: die seit der Chair-Integration stark gestiegene
Generierungszeit reduzieren, ohne Geometrie oder Auswahlprioritäten zu lockern.

## Befund

Die konkrete `14/4`-Quelle aus dem vorherigen Bewegungs-Handoff benötigt vor
Optimierung ungefähr eine Minute. Das Profil des Standes `3a3f2ed` zeigt
84.480 vollständige Kandidatenaufbauten, rund 601.000 Polygon-Überlappungsprüfungen
und 21.307 Aufrufe der Cluster-Sitzprüfung. Dieselben lokalen Tisch-/Sitzflächen
werden in vielen Kombinationen erneut berechnet. Zusätzlich werden geometrisch
gleiche Sitzbelegungen für unterschiedliche Beschriftungen gleich großer Gruppen
wiederholt geprüft. Die Chair-Kosten entstehen damit in der Kandidatensuche.
Die Profiler-Laufzeit selbst ist wegen Instrumentierung deutlich höher und
wird nicht als normale Generierungszeit verwendet.

## Umgesetzt

- Geometrie jedes lokalen Clusterkandidaten einmal mit den vorhandenen
  kanonischen Funktionen vorbereiten. Paarweise Kompatibilität zwischen Optionen
  innerhalb eines Suchaufrufs wiederverwenden; unmögliche Kombinationen vor dem
  vollständigen Aufbau aussortieren. Ursprüngliche Produkt-/Tie-Reihenfolge erhalten.
- Bei `source_movement` nach einer vollständig akzeptierten Lösung nur noch
  Kandidaten mit konkurrenzfähiger maximaler/gesamter Verschiebung aufbauen und
  sitzseitig prüfen. Keine neue Heuristikschwelle und keine Begrenzung der Suche;
  der bisherige Gewinner bleibt erreichbar.
- Bei genau einem Cluster je Teilnehmergruppe gleiche physische Belegung für
  lediglich vertauschte Gruppenbeschriftungen einmal prüfen. Mehrere Cluster
  derselben Gruppe werden weiterhin getrennt geprüft.
- Identische Chair-Prüfungen innerhalb einer Generierung wiederverwenden:
  höchstens 4.096 Einträge, einschließlich negativer Ergebnisse. Schlüssel enthält
  ROI, Tischformen, sämtliche Zielposes, Clusterbelegung und bereits belegte
  Sitzflächen. Gruppennamen werden frisch zugeordnet, Chair-Dictionaries kopiert.
  Diese zusätzlichen Caches überleben den Generierungsaufruf nicht.

Die bestehenden gesamten Plan-/Teilstärken-Caches bleiben erhalten. Sie reagieren
weiterhin auf exakte Quellen; keine Rundung oder Quantisierung von Trackingdaten.
Materialisierte Kandidaten und der finale Plan durchlaufen weiterhin die
vollständigen Geometrieprüfungen. Keine Änderung an Counts, Sitzprioritäten,
Pair-Seam, Parken, Rollen-/Scene-Order-Regeln, OSC oder TD.

## Messung

Separater frischer Prozess je Stand, dieselbe gespeicherte `14/4`-Quelle,
100 % Zielzustand, kein Profiler und kein OSC-Versand:

| Messgröße | Vorher (`3a3f2ed`) | Nachher |
| --- | ---: | ---: |
| Cold-Generierung | 70,7 s | 10,4 s |
| Identische Wiederholung | 1,06 ms | 0,85 ms |
| Vollständige Kandidatenaufbauten | 84.480 | 742 |
| Cluster-Sitzprüfungen | 21.307 | 3.041 |

Rund **6,8-fache Beschleunigung** im direkten Vergleich. Andere neue Cold-Läufe
lagen bei 8,6 Sekunden; Werte hängen von Systemlast und Szene ab. Die bestehende
Wiederholungs-Cachezeit war schon vorher klein. Der Gewinn betrifft die erste
Generierung einer neuen Szene, nicht nur erneutes Anzeigen desselben Ergebnisses.
Die Aufrufzahlen vorher stammen aus dem Profil, nachher aus einfachen Zählern.

Lokale Quelle, exakter Ergebnisvergleich, Messwerte und Integrationsbericht:
`data/aisi/debug/groupwork_participant_preview_2026-10-08/performance/`.
Der Vergleichsstand wurde ausschließlich aus Git gelesen und offline geladen;
keine Änderung des Worktrees oder der laufenden Anwendung.

## Nachweise

35 fokussierte Tests bestanden: Teilnehmermodell, Vorschau/OSC, Teilstärken und
bisheriger table-only Suchkern. Neue Regressionen vergleichen frühe Kompatibilität
mit vollständiger kanonischer Aufzählung inklusive Reihenfolge, gefilterte Suche
mit vollständiger Bestenauswahl nach Ablehnung des ungefilterten Optimums und
Chair-Cacheverhalten bei neuen Gruppenlabels, mutierten Rückgaben, blockierenden
Tischen/Sitzflächen sowie veränderter ROI.

12/12 Integrationsfälle bestanden: gespeicherte Editor-/Live-Quellen mit
`3/1`, `5/1`, `7/2`, `10/2`, `15/2`, `15/5`. Wiederholung und umgekehrte Scene Order
geprüft. Alle zwölf vollständigen Pläne sind exakt gleich zu den gespeicherten
Plänen vor der Optimierung. Auch die konkrete `14/4`-Quelle liefert exakt gleiche
Ziele, Cluster, Gruppen, Chairs und Sitz-/Bewegungsflächen.

Die interaktive Laufzeit im laufenden Sender ist noch nach manuellem Neuladen
zu prüfen. Bestehende Senderinstanz ersetzen, keine zweite daneben starten.
Kein OSC-Liveversand, keine TD-Fernsteuerung, keine `.toe`-Speicherung und kein
physischer Raum-Nachweis. Eine allgemeine obere Laufzeitgrenze wird nicht behauptet.

Gezielte Reproduktion der konkreten Szene mit frischem Prozess:

```sh
PYTHONPATH=src:tests .venv/bin/python -m unittest test_groupwork_participants.GroupworkPlanningTests.test_live_four_groups_do_not_send_upper_left_source_into_distant_pair
```

Der Regressionstest enthält die unveränderliche Source-Fixture und prüft
Geometrie, Bewegungswege, Wiederholung und Scene Order. Für Zeitvergleiche
frische Prozesse und gleiche Quellen verwenden; instrumentierte Profilzeiten
nicht mit normalen Laufzeiten mischen.

## Zweite Optimierungsstufe

Am 2026-10-08 den verbleibenden Aufwand des Standes `8a0856b` gemessen.
Im instrumentierten `14/4`-Lauf: 80.769 Polygonprüfungen und 448 vollständige
Entzerrungs-Kandidaten. Die nachträgliche Entzerrung macht etwa ein Viertel der
Profilzeit aus; Polygon-SAT bleibt der größte geometrische Einzelposten.

Zusätzlich umgesetzt:

- Solange Konturkonflikte bestehen, bleibt die Entzerrung vollständig. Nach ihrer
  Lösung werden Kandidaten mit strikt schlechterem gerundetem Source-Weg vor
  der Chair-/Flächenrekonstruktion verworfen. Gleiche Wege bleiben für den
  bestehenden Abstand-Tie-Break erhalten; Score und Rundung sind unverändert.
- `footprint_bounds` aus der kanonischen Geometrie schließt eindeutig getrennte
  Hüllrechtecke vor SAT aus. Der Abstand muss mehr als `1e-7` betragen; Kontakte
  und mögliche Überschneidungen behalten die vollständige bisherige Prüfung.
- Bis zu 4.096 Ergebnisse des reinen Polygonprädikats wiederverwenden. Schlüssel
  sind beide vollständigen unveränderlichen Polygone, einschließlich aller
  Koordinaten. Veränderte Formen/Posen erhalten keine alten Ergebnisse.
- Bis zu 64 lokale abgerundete Streifen wiederverwenden. Breite, Tiefe,
  Richtung und effektiver Radius sind Bestandteil des Schlüssels. Die gleiche
  kanonische Streifengenerierung liefert unveränderte Tupel.

Die beiden neuen reinen Geometriecaches sind prozessweit und begrenzt;
Scene-/Chair-Caches der ersten Stufe bleiben auf einen Generierungsaufruf
begrenzt. Keine Tracking-Quantisierung und keine Änderung fachlicher Regeln.

37 fokussierte Tests bestanden (36 im gemeinsamen Lauf, zusätzlicher
Radius-/Formcachetest separat). Direkter Vergleich mit erzwungenem vollständigem
SAT umfasst Rotationen, Berührung, minimale Überschneidung/Trennung und eine
gekrümmte Pair-Ellipse. Änderungen an Polygonen, Streifenmaßen, Richtung und
Radius werden separat geprüft. Der Source-Singleton-Test bestätigt außerdem,
dass sicher schlechtere Wege keine Chair-Rekonstruktion auslösen.
12/12 Vergleichspläne einschließlich aller Chairs/Flächen exakt erhalten;
Wiederholung und umgekehrte Scene Order erneut geprüft. Keine Live-Ausgabe.

Direkter Cold-Vergleich mit separaten frischen Prozessen und identischer `14/4`-
Quelle: **9,6 s (`8a0856b`) → 5,6 s**, rund **42 % weniger Zeit** bzw. **1,7×**
schneller als die erste Optimierungsstufe. Identische Wiederholung rund 0,75 ms.
Der neue Polygoncache liefert im konkreten Lauf 43.350 Treffer bei 16.109
Misses; maximal 4.096 Einträge. Ergebnis einschließlich sämtlicher Chairs und
Sitzflächen exakt gleich. Keine allgemeine obere Laufzeitgrenze daraus ableiten.
Quelle und Messbericht: `performance_next/benchmark.json` unter dem bisherigen
lokalen Debug-Verzeichnis; Integrationsbericht daneben.
Live-Laufzeit nach manuellem Sender-Neuladen weiterhin separat prüfen.
