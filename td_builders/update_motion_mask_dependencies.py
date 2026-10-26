"""Add explicit time dependencies only to the owned simulation mask poses."""
import builtins
import json
import sys

REPO='/Users/Johannes/dev/Promotion_Prototypen/AISI'
PATH='/project1/comp_aisi_motion_dynamic_mask_preview'


def update(resolve):
    from td_builders.build_motion_dynamic_mask_preview import mask_expression
    comp=resolve(PATH)
    if comp is None or not comp.fetch('motion_dynamic_simulation_only',False):
        raise RuntimeError('Eigener dynamischer Maskenprüfzweig fehlt; nichts geändert.')
    adapter=comp.op('mask_adapter')
    if adapter is None:
        raise RuntimeError('Maskenadapter fehlt; nichts geändert.')
    changes=[]
    for row in range(5):
        geo=comp.op('mask_item_%d' % row)
        if geo is None:
            raise RuntimeError('Kopierte Maskengeometrie fehlt; nichts geändert.')
        for name in ('tx','ty','rz','sx'):
            par=getattr(geo.par,name)
            old=mask_expression(adapter.path,row,name,timed=False)
            new=mask_expression(adapter.path,row,name)
            if str(par.mode) != 'ParMode.EXPRESSION' or par.expr not in (old,new):
                raise RuntimeError('Abweichende lokale Pose-Bindung; nichts geändert: '+geo.path+'/'+name)
            changes.append((par,par.expr,new))
    changed=[]
    try:
        for par,old,new in changes:
            if old != new:
                changed.append((par,old))
                par.expr=new
        return {'component':comp.path,'pose_expressions_updated':len(changed),
                'time_dependency':'absTime.frame', 'original_nodes_changed':False,
                'production_outputs_changed':False,'main_engine_reset':False,
                'saved':False,'forced_cook_performed':False,
                'status':'installed; continuous movement without diagnostic cook still to verify'}
    except Exception:
        for par,old in reversed(changed):
            par.expr=old
        raise


def symbol(name):
    return (globals().get(name) or getattr(builtins,name,None)
            or getattr(sys.modules.get('__main__'),name,None))


if globals().get('__spec__') is None and callable(symbol('op')):
    if REPO not in sys.path:
        sys.path.insert(0,REPO)
    print(json.dumps(update(symbol('op')),ensure_ascii=False,indent=2))
