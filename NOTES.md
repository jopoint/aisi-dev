# AISI — Terminal Notes

Repository:

```powershell
cd C:\dev\Promotion_Prototypen\AISI
```

## Complete simulation pipeline

Starts the Room Editor, Learning Format interface, and OSC sender together:

```powershell
.\scripts\run_sim_pipeline.ps1
```

## Room / Layout Editor only

```powershell
python -m aisi.app.sim_room_editor
```

## Learning Format interface only

Use this to switch between Input, Groupwork, and Discussion and to change `transformation_strength`:

```powershell
python -m aisi.app.learning_format_server
```

## OSC simulator / sender only

```powershell
python -m aisi.app.sim_scene_to_osc
```

## If `python` does not use the project environment

Activate the virtual environment first:

```powershell
.\.venv\Scripts\Activate.ps1
```

Then run the desired command above.
