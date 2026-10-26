"""Read/cook existing content stages to locate missing physical table guidance.

No parameter/node writes, engine reset, flag changes, or project saves.
"""
import math


def inspect(resolve):
    import numpy as np
    from td_builders import build_motion_output_routing as routing
    motion=resolve(routing.MOTION[:-1])
    if motion is None:
        raise RuntimeError('Motion-Komponente fehlt.')
    report={'read_only':True,'parameters_changed':False,'saved':False,
            'tables':[],'stages':[],'flags':{}}
    comp=resolve(routing.PATH)
    if comp is not None:
        report['flags']={p:bool(getattr(comp.par,p).eval())
                         for p in ('Enablemotion','Sourceapproved','Simulationtest')}
    state=motion.op('state')
    state.cook(force=True)
    report['state_errors']=str(state.errors() or '')
    data=state.numpyArray(delayed=False)
    report['state_shape']=list(data.shape) if data is not None else None
    report['live']=motion.fetch('motion_live_status',{}) or {}
    reader=motion.fetch('motion_osc_reader',None)
    engine=motion.fetch('motion_engine',None)
    if data is not None and data.shape==(6,6,4):
        report['clock']=data[5,0].tolist()
        for index,row in enumerate(reader.rows if reader is not None else []):
            if index>=5: break
            identity,source,target,valid,active=row
            feedback=engine.tables.get(identity) if engine is not None else None
            report['tables'].append({'id':identity,'source':list(source),'target':list(target),
                'valid':valid,'active':active,'distance_cm':math.hypot(source.x-target.x,source.y-target.y),
                'state_source':data[index,0].tolist(),'state_target':data[index,1].tolist(),
                'navigation_contact_halo_phase':data[index,2].tolist(),
                'phase':getattr(feedback,'phase',None),'touching':getattr(feedback,'touching',None)})
    paths=[routing.MOTION+n for n in ('render_floor','render_tabletop','out_floor','out_tabletop')]
    paths += [routing.PATH+'/'+n for n in ('floor_motion','tabletop_motion','out_floor','out_tabletop')]
    paths += [routing.LAYOUT+n for n in ('null_tabletop','null_tabletop_masked')]
    paths += [routing.OUTPUT+n for n in ('switch_floor','switch_tabletop',
                                       'layer_floor_switch','layer_tabletop_switch')]
    for path in paths:
        node=resolve(path)
        if node is None:
            report['stages'].append({'path':path,'missing':True})
            continue
        entry={'path':path,'type':str(node.type),'inputs':[n.path for n in node.inputs],
               'parameters':{}}
        for p in node.pars():
            if p.name in ('top','index','pixeldat','vec0name','vec0valuex','uniname0','value0x'):
                entry['parameters'][p.name]={'value':str(p.eval()),'expression':p.expr}
        try:
            node.cook(force=True)
            entry['errors']=str(node.errors() or '')
            pixels=node.numpyArray(delayed=False)
            if pixels is not None and pixels.ndim==3 and pixels.shape[2]==4:
                entry['size']=[int(pixels.shape[1]),int(pixels.shape[0])]
                rgb=np.max(pixels[:,:,:3],axis=2)
                entry.update({'max_rgb':float(rgb.max()),'lit_rgb_pixels':int((rgb>.1).sum()),
                              'alpha_pixels':int((pixels[:,:,3]>.1).sum())})
        except Exception as error:
            entry['inspection_error']=str(error)
        report['stages'].append(entry)
    return report
