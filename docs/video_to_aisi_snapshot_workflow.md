# Video to AISI Snapshot Workflow

## 1. Ziel

Aus bereits aufgenommenen Videos einen brauchbaren, einzelnen Snapshot für AISI ableiten. Der Fokus liegt auf einem kurzen, stabilen Abschnitt mit möglichst klaren Tisch-Detektionen.

## 2. Warum Videos besser sind als alte JSONL-Logs

- Videos zeigen die Rohsituation direkt und sind nicht von einem alten Log-Format oder früheren Exportannahmen abhängig.
- Ein kurzer Abschnitt aus einem Video liefert mehrere aufeinanderfolgende Frames, aus denen sich ein stabiler Snapshot auswählen lässt.
- Fehler im CV-Stack lassen sich damit besser eingrenzen: Aufnahmeproblem, Frame-Problem oder Exportproblem.
- JSONL-Logs sind oft bereits vorverarbeitet und können wichtige Bilddetails oder Zwischenzustände verlieren.

## 3. Empfohlener Minimal-Workflow

1. Video auswählen
   - Nur ein Video pro Testfall.
   - Möglichst gleiche Kameraposition und ähnliche Lichtverhältnisse wie im Zielbetrieb.

2. Kurzen Abschnitt wählen
   - Nur einen kleinen Zeitbereich um die relevante Szene.
   - Kein langes Full-Video verarbeiten, wenn ein 5 bis 20 Sekunden Abschnitt reicht.

3. Frames extrahieren
   - Den Abschnitt in Einzelbilder zerlegen.
   - Ein brauchbares Sampling wählen, zum Beispiel 2 bis 5 fps.

4. CV auf Frames laufen lassen
   - Die extrahierten Frames mit dem bestehenden Vision-Stack auswerten.
   - Pro Frame die Tabellen-Detektion prüfen, nicht nur den ersten Treffer nehmen.

5. Besten Snapshot auswählen
   - Den Frame mit den klarsten und vollständigsten Tischobjekten wählen.
   - Bevorzugt: wenige Fehl-Detektionen, stabile Tischpositionen, gute Rotation.

6. AISI-Export und Test
   - Den gewählten Snapshot in das AISI-Format exportieren.
   - Danach mit dem AISI-Layout testen, ob die Szene plausibel und stabil ist.

## 4. Empfohlene erste Testfälle

- clean
  - klare Sicht, wenige Störungen, gute Referenz für den Baseline-Flow.
- messy
  - mehr Hintergrund, aber noch nachvollziehbare Tischdetektionen.
- leichte Occlusion
  - ein Tisch teilweise verdeckt, aber noch als Tisch erkennbar.

## 5. Praktische Entscheidungsregeln

- Ein Abschnitt ist brauchbar, wenn über mehrere Frames dieselben Tische konsistent erkannt werden.
- Ein Abschnitt ist brauchbar, wenn die Detektionen nicht stark springen und die Szene optisch ruhig ist.
- Ein Snapshot ist ungeeignet, wenn die Tischanzahl stark variiert, die Rotationen unplausibel sind oder Objekte häufig verschwinden.
- Ein Snapshot ist ungeeignet, wenn der Frame nur einen Zwischenzustand zeigt, zum Beispiel Bewegungsunschärfe, starke Verdeckung oder Kameraausreißer.

## 6. Nächste konkrete Schritte

1. Drei bis fünf kurze Videosegmente für clean, messy und leichte Occlusion auswählen.
2. Für jedes Segment ein kleines Frame-Set extrahieren.
3. Den bestehenden CV-Stack auf diese Frames laufen lassen.
4. Pro Segment den besten Snapshot manuell markieren.
5. Die ausgewählten Snapshots in den AISI-Export und in den Layout-Test geben.
