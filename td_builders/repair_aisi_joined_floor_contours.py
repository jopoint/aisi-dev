"""Textport: AISI-Floor-Konturen an einer gemeinsamen Rect-Längskante begrenzen.

Nur vorhandenen AISI-Style-DAT und einen neuen SOP-Parameter ändern.
Kein Force-Cook, keine Fernsteuerung, kein Speichern.
"""
import importlib
import json
import sys

ROOT = '/project1/comp_layout_proposal'
STYLE = ROOT + '/aisi_table_visual_style'
BACKUP_KEY = 'aisi_joined_floor_contours_before_repair'
PAGE = 'AISI Floor Join'
EXPRESSION = "op(%r).module.floor_join_side_for_geo(parent())" % STYLE


def _library():
    repo = '/Users/Johannes/dev/Promotion_Prototypen/AISI'
    if repo not in sys.path:
        sys.path.insert(0,repo)
    return importlib.reload(importlib.import_module('td_builders.aisi_study_visual_style'))


def _page(script):
    return next((p for p in script.customPages if p.name==PAGE),None)


def _targets(layout):
    template = layout.op('table_template')
    items = sorted((n for n in layout.children if n.name.startswith('item')
        and n.name[4:].isdigit() and 1<=int(n.name[4:])<=5),key=lambda n:n.name)
    if template is None or not items:
        raise ValueError('Bekanntes Tisch-Template oder Tischinstanzen fehlen.')
    result = []
    for item in [template,*items]:
        script = item.op('table_target_floor_geo/table_outline_outer')
        callback = item.op('table_target_floor_geo/table_outline_outer_callbacks')
        if script is None or callback is None or STYLE not in callback.text or 'target_floor' not in callback.text:
            raise ValueError('Unbekannte Floor-Kontur-Anbindung: '+item.path)
        binding = getattr(script.par,'Joiningside',None)
        page = _page(script)
        if binding is not None and (page is None or binding.expr!=EXPRESSION):
            raise ValueError('Joiningside ist bereits anders belegt: '+script.path)
        if page is not None and (binding is None or [p.name for p in page.pars]!=['Joiningside']):
            raise ValueError('Parameterseite ist bereits anders belegt: '+script.path)
        result.append(script)
    return result


def restore_joined_floor_contours(resolve):
    layout = resolve(ROOT); style = resolve(STYLE)
    backup = layout.fetch(BACKUP_KEY,None) if layout is not None else None
    if backup is None or style is None:
        raise ValueError('Keine Rückfallkopie vorhanden.')
    page_paths = []
    for path in backup['scripts']:
        script = resolve(path)
        if script is None:
            raise ValueError('Rückfallziel fehlt: '+path)
        page = _page(script)
        if page is not None:
            if any(p.name!='Joiningside' or p.expr!=EXPRESSION for p in page.pars):
                raise ValueError('Parameterseite wurde inzwischen verändert: '+path)
            page_paths.append(path)
    library = _library()
    if style.text.strip() not in (backup['text'].strip(),library.shared_callback_source().strip(),
                                 library.shared_callback_source(shared_seam=False).strip()):
        raise ValueError('Style-DAT wurde inzwischen verändert; keine Rücknahme überschreibt ihn.')
    style.text = backup['text']
    for path in page_paths:
        page = _page(resolve(path))
        if page is not None:
            page.destroy()
    layout.store(BACKUP_KEY,None)
    return {'restored':True,'saved':False}


def repair_joined_floor_contours(resolve,project_name):
    library = _library()
    layout = resolve(ROOT); style = resolve(STYLE)
    if layout is None or style is None:
        raise ValueError('Bekannter AISI-Style-DAT fehlt.')
    old = library.shared_callback_source(join_aware=False)
    new = library.shared_callback_source()
    clipped = library.shared_callback_source(shared_seam=False)
    if style.text.strip() not in (old.strip(),clipped.strip(),new.strip()):
        raise ValueError('Style-DAT weicht vom bekannten Stand ab; nichts verändert.')
    compile(new,STYLE,'exec')
    scripts = _targets(layout)  # Alle Ziele vor der ersten Änderung prüfen.
    raw = resolve('/project1/comp_io/null_osc_raw')
    if raw is None or raw['study/mode'] is None or raw['study/mode'].eval()!=2:
        raise ValueError('Bitte AISI-Modus wählen; nichts verändert.')
    joins = [{'item':s.parent().parent().name,
              'side':library.floor_join_side_for_geo(s.parent(),resolve)}
             for s in scripts if s.parent().parent().name!='table_template']
    if not any(row['side'] for row in joins):
        raise ValueError('Keine exakt anliegende Zweiergruppe erkannt. Bitte Discussion 1–6 bei 100 % prüfen; nichts verändert.')
    missing = [s for s in scripts if _page(s) is None]
    if missing:
        if layout.fetch(BACKUP_KEY,None) is not None:
            raise ValueError('Unvollständige frühere Reparatur; zuerst restore_joined_floor_contours(op).')
        layout.store(BACKUP_KEY,{'text':style.text,'scripts':[s.path for s in missing]})
    previous_text = style.text
    try:
        style.text = new
        for script in missing:
            # A template update may already have propagated this parameter.
            if getattr(script.par,'Joiningside',None) is None:
                page = script.appendCustomPage(PAGE)
                page.appendFloat('Joiningside',label='Shared long edge',replace=False)
            script.par.Joiningside.expr = EXPRESSION
        for script in scripts:
            if script.par.Joiningside.expr!=EXPRESSION:
                raise ValueError('Abhängigkeit nicht übernommen: '+script.path)
            expected = library.floor_join_side_for_geo(script.parent(),resolve)
            if abs(script.par.Joiningside.eval()-expected)>1e-9:
                raise ValueError('Abhängigkeit nicht ausgewertet: '+script.path)
    except Exception:
        if missing:
            # Reset partially configured expressions before the guarded rollback.
            for script in missing:
                binding = getattr(script.par,'Joiningside',None)
                if binding is not None:
                    binding.expr = EXPRESSION
            restore_joined_floor_contours(resolve)
        else:
            style.text = previous_text
        raise
    return {'project':project_name,'join_sides':joins,'bound_contours':len(scripts),
            'physical_rect_cm':[library.RECT_WIDTH_CM,library.RECT_DEPTH_CM],
            'floor_rect_cm':[library.FLOOR_TARGET_WIDTH_CM,library.FLOOR_TARGET_DEPTH_CM],
            'shared_separator':True,'forced_cook':False,'saved':False}


try:
    _td_resolve = op
    _td_project_name = project.name
except NameError:
    if __name__=='__main__':
        raise RuntimeError('Im TouchDesigner-Python-Textport ausführen.')
else:
    print(json.dumps(repair_joined_floor_contours(_td_resolve,_td_project_name),indent=2))
    print('AISI-Floor: gemeinsame gestrichelte Trennkante sichtbar. Kein Force-Cook, nichts gespeichert. '
          'Jetzt Zweiergruppe und Wechsel zum Viererring visuell prüfen.')
    print('Rücknahme: restore_joined_floor_contours(op)')
