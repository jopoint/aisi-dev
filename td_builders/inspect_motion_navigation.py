"""Inspect a missing navigation circle before/after the simulation mask.

Only reads/cooks the owned Motion test nodes; no parameter or graph changes.
"""
import builtins
import json
import sys

MOTION='/project1/comp_aisi_motion_v1_5'
MASKED='/project1/comp_aisi_motion_dynamic_mask_preview'


def inspect(resolve):
    import numpy as np
    motion,masked=resolve(MOTION),resolve(MASKED)
    if motion is None or masked is None:
        raise RuntimeError('Motion-Komponente oder dynamischer Maskenprüfzweig fehlt.')
    report={'parameters_changed':False,'nodes_changed':False,'nodes':{},'tables':[]}
    state=motion.op('state')
    state.cook(force=True)
    if state.errors():
        raise RuntimeError('state: '+str(state.errors()))
    data=state.numpyArray(delayed=False).copy()
    if data.shape != (6,6,4):
        raise RuntimeError('Unerwartetes State-Raster: '+str(data.shape))
    pictures={}
    for name,node in (('unmasked',motion.op('out_tabletop')),
                      ('mask',masked.op('reorder_simulation_mask')),
                      ('masked',masked.op('out_tabletop'))):
        node.cook(force=True)
        errors=str(node.errors() or '')
        report['nodes'][name]={'path':node.path,'errors':errors,'size':[node.width,node.height]}
        if not errors:
            pictures[name]=node.numpyArray(delayed=False).copy()
    live=motion.fetch('motion_live_status',{})
    report['live']=live
    engine=motion.fetch('motion_engine',None)
    identities=live.get('ids',[])
    for row in range(min(5,len(identities))):
        identity=identities[row]
        source,target=data[row,0],data[row,1]
        status=engine.tables.get(identity) if engine else None
        entry={'id':identity,'source':source.tolist(),'target':target.tolist(),
               'navigation_contact_halo_phase':data[row,2].tolist(),
               'phase':getattr(status,'phase',None),'touching':getattr(status,'touching',None)}
        geo=masked.op('mask_item_%d' % row)
        if geo is not None:
            entry['mask_transform']={p:float(getattr(geo.par,p).eval()) for p in ('tx','ty','rz','sx')}
        # Probe both array-Y conventions explicitly; neither is assumed here.
        if source[3]>.5 and not getattr(status,'touching',False):
            entry['center_windows']={}
            for name,array in pictures.items():
                height,width=array.shape[:2]
                x=float(source[0])/500
                y=float(source[1])/500
                samples=[]
                for cy in (y,1-y):
                    x0=min(width,max(0,int((x-.05)*width)))
                    x1=max(0,min(width,int((x+.05)*width)+1))
                    y0=min(height,max(0,int((cy-.05)*height)))
                    y1=max(0,min(height,int((cy+.05)*height)+1))
                    window=array[y0:y1,x0:x1]
                    samples.append({'array_y_fraction':cy,
                        'max_rgb':float(np.max(window[:,:,:3])) if window.size else None,
                        'lit_rgb_fraction':float((np.max(window[:,:,:3],axis=2)>.1).mean())
                            if window.size else None})
                entry['center_windows'][name]=samples
            if geo is not None:
                sop=geo.op('select_table_surface')
                if sop is not None:
                    points=[tuple(float(point.P[i]) for i in range(3)) for point in sop.points]
                    entry['mask_local_bounds']=[[min(p[i] for p in points),max(p[i] for p in points)]
                                                for i in range(3)] if points else None
                    entry['mask_select_parameters']={p.name:{'value':str(p.eval()),'expression':p.expr}
                        for p in sop.pars() if p.name in ('sops','soppath','xform','transform','tx','ty','sx','sy')}
        report['tables'].append(entry)
    return report


def symbol(name):
    return (globals().get(name) or getattr(builtins,name,None)
            or getattr(sys.modules.get('__main__'),name,None))


if globals().get('__spec__') is None and callable(symbol('op')):
    print(json.dumps(inspect(symbol('op')),ensure_ascii=False,indent=2))
