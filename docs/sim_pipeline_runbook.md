# AISI Sim-Pipeline Runbook

## Zweck
Die Sim-Pipeline erlaubt das Testen der AISI-Pipeline ohne echten Raum, ohne echte Kamera und ohne echte Projektion.

## Architektur

```text
Sim Room Editor
→ live_scene.json
→ sim_scene_to_osc.py
→ Source (Tables/Persons/Chairs) + Target OSC
→ TouchDesigner Layout Proposal
```

Parallel:

```text
Browser / Tablet
→ learning_format_server.py
→ learning_format.json
→ sim_scene_to_osc.py
→ Target Layout Selection
```

## Wichtige Dateien
- src/aisi/app/sim_room_editor.py
- src/aisi/app/sim_scene_to_osc.py
- src/aisi/app/learning_format_server.py
- scripts/run_sim_pipeline.ps1
- data/aisi/scenes/simulated/live_scene.json
- data/aisi/state/learning_format.json
- td_builders/build_aisi_td_step_26_sim_live_source_osc_ready.py

## Starten
Empfohlen:
```powershell
cd C:\dev\Promotion_Prototypen\AISI
.\scripts\run_sim_pipeline.ps1
```

Falls PowerShell blockiert:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\run_sim_pipeline.ps1
```

## TouchDesigner
- TouchDesigner öffnen
- TouchDesigner in Play-Modus setzen
- Outputmode 0 wählen
- OSC In Port: 9000
- /project1/comp_io/oscin1: Network Port 9000, Active On
- Source-Tische kommen aus dem Simulator
- Personen kommen aus dem Simulator (gelbe Outline-Kreise)
- Stühle kommen aus dem Simulator (grüne Outline-Kreise)
- Target-Tische kommen aus der Lernformat-Auswahl
- Motion-Pfeile werden aus Source- und Target-Geos abgeleitet
- render1 Geometry-Liste muss eine einzeilige Liste bleiben

## Bedienung
### Sim Room Editor
- Tische mit Maus verschieben
- Q/E dreht ausgewählten Tisch
- Personen sind Kreise mit radius_cm = 40
- Stühle sind Kreise mit radius_cm = 30
- J: Jitter für Personen/Stühle an/aus
- O: Occlusion/Dropout für Personen/Stühle an/aus
- S speichert
- R reset
- ESC schließt

### Learning Format UI
- Browser öffnen: http://127.0.0.1:8080
- Input / Groupwork / Discussion wählen

### sim_scene_to_osc.py
- 1=input
- 2=groupwork
- 3=discussion
- q=quit

## Testcheck
- Bewegen sich Source-Tische in TD, wenn ich sie im Simulator verschiebe?
- Bewegen sich Personen und Stühle in TD korrekt mit?
- Sind Personen gelb als Outline-Kreise sichtbar?
- Sind Stühle grün als Outline-Kreise sichtbar?
- Wechseln Target-Tische, wenn ich im Browser ein Lernformat wähle?
- Aktualisieren sich Motion-Pfeile?
- Stimmt die Rotation?
- Bleibt die Darstellung nur im TD-Play-Modus live?

## Bekannte Hinweise
- Koordinaten bleiben in cm.
- TD rechnet cm in TD-Koordinaten um.
- TD invertiert die Y-Achse.
- Deshalb wird Rotation beim OSC-Senden für TD invertiert.
- Jitter/Occlusion betreffen nur Personen und Stühle, nicht Tische.
- Sim Room Editor nur einmal starten; mehrere Instanzen schreiben parallel live_scene.json und verursachen springende Werte.
- /project1/comp_io/oscin1 muss auf Port 9000 laufen und aktiv sein.
- TouchDesigner muss im Play-Modus sein, sonst aktualisiert sich die Darstellung nicht.
- Das Tabletop Grid ist aktuell stabil und soll nicht weiter verändert werden.
- Echte Kamera und echte Projektion sind in dieser Sim-Pipeline noch nicht enthalten.

## Aktueller stabiler Stand
- Sim Room Editor funktioniert
- Live Source-OSC funktioniert
- Personen und Stühle werden per OSC gesendet
- Personen (radius_cm = 40) und Stühle (radius_cm = 30) sind im Simulator integriert
- Target-Layouts funktionieren
- Browser-/Tablet-Auswahl funktioniert
- Launcher-Skript funktioniert
- TD Outputmode 0 reagiert live
- Tische, Target-Tische und Motion-Pfeile funktionieren weiterhin
