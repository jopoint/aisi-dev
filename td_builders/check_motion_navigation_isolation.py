"""Controlled navigation probes through the copied simulation mask only.

Temporarily substitutes two local Select TOP sources, restores them in finally,
and never resets the advancing Motion engine or changes the Room Editor.
"""
import builtins
import json
import sys

REPO='C:/dev/Promotion_Prototypen/AISI'
MOTION='/project1/comp_aisi_motion_v1_5'
MASKED='/project1/comp_aisi_motion_dynamic_mask_preview'
NAMES=('navigation_probe_callbacks','navigation_probe_state','navigation_probe_render')


def fixture(contact):
    import numpy as np
    from td_builders.motion_design import WIDTH,DEPTH,CORNER
    data=np.zeros((6,6,4),dtype=np.float32)
    data[4,0]=(270,350,90,1) if contact else (400,400,90,1)
    data[4,1]=(250,350,90,1)
    data[4,2]=(.2,1,.8,0) if contact else (1,0,0,0)
    data[4,3]=(0,0,0,1)
    data[4,4]=(WIDTH,DEPTH,CORNER,0)
    data[5,0]=(4,4,1,1)  # Reveal finished; no pulse or dissolve.
    return data


def pixel_stats(array):
    import numpy as np
    if array.ndim != 3 or array.shape[2] != 4 or not np.isfinite(array).all():
        raise ValueError('Ungültiges RGBA-Proberaster.')
    lit=np.max(array[:,:,:3],axis=2)>.5
    return {'size':[int(array.shape[1]),int(array.shape[0])],
            'lit_pixels':int(lit.sum()),'lit_fraction':float(lit.mean())}


def check(resolve,symbols):
    motion,comp=resolve(MOTION),resolve(MASKED)
    if motion is None or comp is None or not comp.fetch('motion_dynamic_simulation_only',False):
        raise RuntimeError('Dynamischer Maskenprüfzweig fehlt; nichts geändert.')
    if any(comp.op(name) is not None for name in NAMES):
        raise RuntimeError('Probe-Knoten existieren bereits; nichts überschrieben.')
    selectors={name:comp.op(name) for name in ('motion_state','motion_tabletop')}
    if any(node is None for node in selectors.values()):
        raise RuntimeError('Lokaler Select TOP fehlt; nichts geändert.')
    expected={'motion_state':MOTION+'/state','motion_tabletop':MOTION+'/out_tabletop'}
    for name,node in selectors.items():
        if str(node.par.top.mode) != 'ParMode.CONSTANT' or node.par.top.val != expected[name]:
            raise RuntimeError('Lokale Quelle wurde anderweitig geändert; nichts überschrieben: '+name)
    original=motion.op('render_tabletop')
    if original is None:
        raise RuntimeError('Tabletop-Shader fehlt; nichts geändert.')
    report={'passed':False,'cases':[],'saved':False,'production_outputs_changed':False,
            'main_engine_reset':False,'physical_validation':'not performed'}
    created=[]

    def pixels(node):
        node.cook(force=True)
        if node.errors():
            raise RuntimeError(node.path+': '+str(node.errors()))
        return node.numpyArray(delayed=False).copy()

    try:
        callbacks=comp.create(symbols['textDAT'],NAMES[0]); created.append(callbacks)
        callbacks.text='''import numpy as np
def onCook(scriptOp):
    scriptOp.copyNumpyArray(np.asarray(scriptOp.fetch('probe_data'), dtype=np.float32))
'''
        state=comp.create(symbols['scriptTOP'],NAMES[1]); created.append(state)
        state.store('probe_data',fixture(False))
        state.par.callbacks=callbacks.path
        fmt=getattr(state.par,'format',None)
        if fmt is None:
            fmt=getattr(state.par,'pixelformat',None)
        if fmt is None:
            raise RuntimeError('Script TOP besitzt keinen Pixel-Format-Parameter.')
        fmt.val='rgba32float'
        render=comp.copy(original,name=NAMES[2],includeDocked=False); created.append(render)
        render.inputConnectors[0].connect(state)
        render.par.pixeldat=motion.op('motion_pixel').path
        render.par.outputresolution='custom'
        for name,size in (('resolutionw',1000),('resolutionh',1000)):
            parameter=getattr(render.par,name)
            parameter.expr=''
            parameter.val=size
        selectors['motion_state'].par.top=state.path
        selectors['motion_tabletop'].par.top=render.path
        for contact in (False,True):
            state.store('probe_data',fixture(contact))
            state.cook(force=True)
            selectors['motion_state'].cook(force=True)
            before=pixel_stats(pixels(render))
            selectors['motion_tabletop'].cook(force=True)
            mask=pixel_stats(pixels(comp.op('reorder_simulation_mask')))
            after=pixel_stats(pixels(comp.op('out_tabletop')))
            ratio=after['lit_fraction']/before['lit_fraction'] if before['lit_fraction'] else 0
            geo=comp.op('mask_item_4')
            case={'name':'contact' if contact else 'no_contact',
                  'source':fixture(contact)[4,0].tolist(),'target':fixture(contact)[4,1].tolist(),
                  'unmasked':before,'mask':mask,'masked':after,'retained_area_ratio':ratio,
                  'passed':before['lit_pixels']>0 and .95 <= ratio <= 1.05,
                  'mask_transform':{p:float(getattr(geo.par,p).eval()) for p in ('tx','ty','rz','sx')}}
            sop=geo.op('select_table_surface')
            points=[tuple(float(point.P[i]) for i in range(3)) for point in sop.points]
            case['mask_local_bounds']=[[min(p[i] for p in points),max(p[i] for p in points)]
                                       for i in range(3)] if points else None
            report['cases'].append(case)
        report['passed']=all(case['passed'] for case in report['cases'])
    except Exception as error:
        report['failure']=str(error)
    finally:
        # Restore sources before removing nodes, including on a failed probe.
        for name,node in selectors.items():
            node.par.top=expected[name]
        report['local_inputs_restored']=all(n.par.top.val == expected[k] for k,n in selectors.items())
        for node in reversed(created):
            node.destroy()
        report['temporary_probes_removed']=all(comp.op(name) is None for name in NAMES)
        try:
            pixels(comp.op('out_tabletop'))
        except Exception as error:
            report['restore_cook_error']=str(error)
            report['passed']=False
    return report


def symbol(name):
    return (globals().get(name) or getattr(builtins,name,None)
            or getattr(sys.modules.get('__main__'),name,None))


if globals().get('__spec__') is None and callable(symbol('op')):
    for path in (REPO,REPO+'/src'):
        if path not in sys.path:
            sys.path.insert(0,path)
    print(json.dumps(check(symbol('op'),{k:symbol(k) for k in ('textDAT','scriptTOP')}),
                     ensure_ascii=False,indent=2))
