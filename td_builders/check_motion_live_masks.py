"""Read/cook existing comparison operators; never approves or rewires output."""
import math


def match_sources(rows,masks,pixel_cm):
    """Require unique pose correspondence within the existing one-pixel bound."""
    from td_builders.motion_design import WIDTH,DEPTH
    if not math.isfinite(pixel_cm) or pixel_cm<=0:
        raise ValueError('Ungültiges Pixelmaß.')
    if not rows or len(rows)!=len(masks) or len({r[0] for r in rows})!=len(rows):
        raise ValueError('Aktuelle Source- und Originalmaskenmenge weichen ab.')
    radius=math.hypot(WIDTH,DEPTH)/2
    matched=[]
    used=set()
    for identity,source,target,valid,active in rows:
        if not valid:
            raise ValueError('Source fehlt oder ist veraltet: '+identity)
        candidates=[]
        for mask in masks:
            pose=mask['pose']
            if not all(math.isfinite(v) for v in (*source,*pose)):
                raise ValueError('Nicht endliche Source-/Maskenpose.')
            distance=math.hypot(source[0]-pose[0],source[1]-pose[1])
            angle=abs((source[2]-pose[2]+90)%180-90)
            error=distance+2*radius*math.sin(math.radians(angle)/2)
            if error<=pixel_cm:
                candidates.append((mask['path'],error))
        if len(candidates)!=1 or candidates[0][0] in used:
            raise ValueError('Keine eindeutige rastergenaue Originalmaske für '+identity)
        path,error=candidates[0]
        used.add(path)
        matched.append({'table_id':identity,'original_mask':path,'max_edge_error_cm':error})
    return matched


def compare_pixels(original,copied):
    """One-pixel association tolerance, not a change to the physical mask."""
    import numpy as np
    if (original.shape!=copied.shape or original.ndim!=3 or original.shape[2]!=4
            or not np.isfinite(original).all() or not np.isfinite(copied).all()):
        raise ValueError('Ungültige oder unterschiedlich große Maskenbilder.')
    a=np.max(original[:,:,:3],axis=2)>.5
    b=np.max(copied[:,:,:3],axis=2)>.5
    if not a.any() or not b.any():
        raise ValueError('Leere Maske ist kein Übereinstimmungsnachweis.')
    def dilate(image):
        padded=np.pad(image,1)
        return np.logical_or.reduce([padded[y:y+image.shape[0],x:x+image.shape[1]]
                                     for y in range(3) for x in range(3)])
    outside=int((a & ~dilate(b)).sum()+(b & ~dilate(a)).sum())
    return {'passed':outside==0,'pixels_outside_one_pixel_boundary':outside,
            'original_lit_pixels':int(a.sum()),'copied_lit_pixels':int(b.sum()),
            'max_rgba_difference':float(np.max(np.abs(original-copied))),
            'association_tolerance_pixels':1}


def _read_stream(resolve):
    """Fresh camera-bound rows without reading mask geometry or GPU pixels."""
    import time
    from td_builders import motion_output_simulation_test as test
    routing=test.routing
    comp=resolve(routing.PATH)
    routing.require(comp is not None,'Motion-Routing fehlt.')
    motion=resolve(routing.MOTION[:-1])
    raw=resolve(str(motion.par.Oscpath.eval()))
    routing.require(raw is not None,'OSC-Eingang fehlt.')
    for node in raw.inputs:
        if str(node.type)=='oscin': node.cook(force=True)
    raw.cook(force=True)
    state=motion.op('state')
    state.cook(force=True)
    routing.require(not state.errors(),'Motion-State fehlerhaft: '+str(state.errors()))
    status=motion.fetch('motion_live_status',{}) or {}
    report={'passed':False,'outputs_changed':False,'source_approved':bool(comp.par.Sourceapproved.eval()),'saved':False,
            'physical_validation':'not performed','live_stream':status}
    if not status.get('fresh'):
        report['status']='Warte auf zwei fortschreitende Frames; später erneut prüfen.'
        return report,None
    channels={c.name:c.eval() for c in raw.chans() if c.name.startswith('aisi_motion/')}
    signature=status['signature']
    routing.require(all(channels.get('aisi_motion/camera/'+key)==value for key,value in
        (('fresh',1),('session',signature[0]),('frame',signature[1]))),
        'Keine zum Motion-Frame gehörende frische Kameraquelle.')
    reader=motion.fetch('motion_osc_reader',None)
    snapshot=reader.read(channels,time.monotonic())
    routing.require(snapshot['fresh'],'Kamera-Motion-Stream inzwischen veraltet.')
    routing.require(snapshot['signature']==signature,'Motion-Frame während Erfassung verändert.')
    routing.require(all(row[3] for row in snapshot['rows']),'Source fehlt oder ist veraltet.')
    report['passed']=True
    return report,snapshot


def current_stream(resolve):
    """Freshness only; keep an earlier mask proof tied to its sampled frame."""
    return _read_stream(resolve)[0]


def current_sources(resolve):
    """Fresh camera-bound rows matched to original geometry before GPU work."""
    from td_builders import motion_output_simulation_test as test
    from td_builders.motion_design import td_pose
    routing=test.routing
    report,snapshot=_read_stream(resolve)
    if not report['passed']:
        return report
    renderer=resolve(routing.LAYOUT+'render_table_mask')
    geos=renderer.par.geometry.eval()
    routing.require(isinstance(geos,(list,tuple)),'Originalgeometrie nicht als Liste auflösbar.')
    masks=[]
    seen=set()
    for geo in geos:
        if geo.path in seen: continue
        seen.add(geo.path)
        scale=[float(getattr(geo.par,p).eval()) for p in ('sx','sy','sz')]
        if not geo.render or abs(scale[0])<1e-8: continue
        routing.require(not geo.inputs and all(abs(v-1)<1e-6 for v in scale)
                        and all(abs(getattr(geo.par,p).eval())<1e-6 for p in ('rx','ry','tz')),
                        'Originalmaske hat unerwartetes Parenting/Skalierung/Neigung.')
        pose=td_pose(*(float(getattr(geo.par,p).eval()) for p in ('tx','ty','rz')))
        masks.append({'path':geo.path,'pose':pose})
    routing.require(renderer.width==renderer.height and renderer.width>0,'Originalraster nicht quadratisch.')
    matched=match_sources(snapshot['rows'],masks,500./renderer.width)
    report.update({'passed':True,'source_mask_matches':matched,
        'duplicate_mask_references_preserved':len(geos)-len(seen)})
    return report


def check(resolve,validator=None,allow_live=False):
    from td_builders import motion_output_simulation_test as test
    routing=test.routing
    comp=resolve(routing.PATH)
    routing.require(comp is not None,'Motion-Routing fehlt.')
    flags=(bool(comp.par.Enablemotion.eval()),bool(comp.par.Sourceapproved.eval()))
    routing.require(not comp.par.Simulationtest.eval() and
                    (flags==(False,False) or (allow_live and flags==(True,True))),
                    'Vergleich verlangt deaktivierte Simulation und kontrollierte Live-Freigaben.')
    info=comp.fetch(test.SESSION,None)
    routing.require(isinstance(info,dict),'Registrierter Vergleichszweig fehlt.')
    (validator or test.validate)(resolve,comp,info)
    report=current_sources(resolve)
    if not report['passed']:
        return report
    original=resolve(routing.LAYOUT+'reorder_table_mask')
    copied=resolve(test.SIM+'/reorder_simulation_mask')
    routing.digest(original)
    a=original.numpyArray(delayed=False).copy()
    routing.digest(copied)
    pixels=compare_pixels(a,copied.numpyArray(delayed=False).copy())
    report.update({'passed':pixels['passed'],'mask_pixels':pixels,
        'legacy_mask_has_stable_id_channels':False,
        'mapping_evidence':'unique pose correspondence; stable IDs from direct camera stream',
        'status':'Maskenabgleich bestanden; keine automatische Freigabe.' if pixels['passed'] else
                 'Maskenraster weicht ab; Quelle bleibt gesperrt.'})
    return report
