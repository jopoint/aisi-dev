# AISI Sim-Pipeline Runbook

## Zweck
Die Sim-Pipeline erlaubt das Testen der AISI-Pipeline ohne echten Raum, ohne echte Kamera und ohne echte Projektion.

## Architektur

```text
Sim Room Editor
→ live_scene.json
→ sim_scene_to_osc.py
→ Source + Target OSC
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
- Outputmode 0 wählen
- OSC In Port: 9000
- Source-Tische kommen aus dem Simulator
- Target-Tische kommen aus der Lernformat-Auswahl
- Motion-Pfeile werden aus Source- und Target-Geos abgeleitet

## Bedienung
### Sim Room Editor
- Tische mit Maus verschieben
- Q/E dreht ausgewählten Tisch
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
- Wechseln Target-Tische, wenn ich im Browser ein Lernformat wähle?
- Aktualisieren sich Motion-Pfeile?
- Stimmt die Rotation?

## Bekannte Hinweise
- Koordinaten bleiben in cm.
- TD rechnet cm in TD-Koordinaten um.
- TD invertiert die Y-Achse.
- Deshalb wird Rotation beim OSC-Senden für TD invertiert.
- Das Tabletop Grid ist aktuell stabil und soll nicht weiter verändert werden.
- Echte Kamera und echte Projektion sind in dieser Sim-Pipeline noch nicht enthalten.

## Aktueller stabiler Stand
- Sim Room Editor funktioniert
- Live Source-OSC funktioniert
- Target-Layouts funktionieren
- Browser-/Tablet-Auswahl funktioniert
- Launcher-Skript funktioniert
- TD Outputmode 0 reagiert live
