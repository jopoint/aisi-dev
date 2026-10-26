"""Measure the real mask and route the static snapshot in the isolated preview."""
import builtins
import json
import sys

SNAPSHOT = '/project1/comp_aisi_motion_aligned_snapshot'
ROUTE = '/project1/comp_aisi_motion_routing_preview'
PROBE_NAMES = ('alignment_probe_pixel','alignment_probe','alignment_probe_masked',
               'alignment_probe_mask_source')
REPO = 'C:/dev/Promotion_Prototypen/AISI'


def coverage_shader(source):
    if source.count('void main()') != 1:
        raise ValueError('Motion-Shader enthält keinen eindeutigen main-Einstieg.')
    return source.replace('void main()', 'void renderContent()', 1) + '''
void main() {
    if (uSurface.x < 2.5) { renderContent(); return; }
    vec2 p=vec2(vUV.x,1.0-vUV.y)*500.0;
    float occupied=0.0;
    for(int i=0;i<5;i++) {
        vec4 source=datum(0,i), shape=datum(4,i);
        if(source.w<.5) continue;
        occupied=max(occupied,coverage(roundedRect(
            rotate2(p-source.xy,-source.z),shape.xy*.5,shape.z)));
    }
    fragColor=TDOutputSwizzle(white(occupied));
}
'''


def measure(source, masked, mask):
    import numpy as np
    if (source.shape != masked.shape or source.shape != mask.shape
            or source.ndim != 3 or source.shape[2] != 4):
        raise ValueError('Probe und Maske haben unterschiedliche RGBA-Raster.')
    if not all(np.isfinite(a).all() for a in (source,masked,mask)):
        raise ValueError('Nicht endliche Pixelwerte.')
    interior=source[:,:,0]>.98
    inside_count=int(interior.sum())
    if not inside_count:
        raise ValueError('Weiße Probe enthält keine Tischfläche.')
    brightness=np.max(masked[:,:,:3],axis=2)
    mask_support=np.max(mask[:,:,:3],axis=2)>1/255
    return {
        'resolution':[int(source.shape[1]),int(source.shape[0])],
        'nominal_interior_pixels':inside_count,
        'interior_retained_fraction':float((interior & (brightness>.5)).sum()/inside_count),
        'mask_outside_nominal_pixels':int((mask_support & (source[:,:,0]<.01)).sum()),
        'lit_pixels_outside_mask':int(((~mask_support) & (brightness>2/255)).sum()),
        'masked_probe_lit_pixels':int((brightness>.5).sum()),
    }


def create_mask_probe(snapshot, route, probe, select_type, created):
    # TOP cables stay inside one network. A Select TOP bridges the external
    # mask by path, without reconnecting its original producer or consumers.
    local_mask=snapshot.create(select_type,PROBE_NAMES[3])
    created.append(local_mask)
    local_mask.par.top=route.op('mask_existing').path
    masked=snapshot.copy(route.op('tabletop_masked'),name=PROBE_NAMES[2],includeDocked=False)
    created.append(masked)
    masked.inputConnectors[0].connect(probe)
    masked.inputConnectors[1].connect(local_mask)
    if list(masked.inputs) != [probe,local_mask]:
        raise RuntimeError('Lokale Probe-Verbindungen konnten nicht hergestellt werden.')
    return masked,local_mask


def check(resolve, symbols):
    snapshot, route = resolve(SNAPSHOT), resolve(ROUTE)
    if (snapshot is None or not snapshot.fetch('motion_static_snapshot',False)
            or route is None or not route.fetch('motion_routing_preview_only',False)):
        raise RuntimeError('Statischer Snapshot oder isolierter Routing-Prüfzweig fehlt.')
    if any(snapshot.op(name) is not None for name in PROBE_NAMES):
        raise RuntimeError('Probe-Knoten existieren bereits; nichts überschrieben.')
    selectors={s:route.op(s+'_motion') for s in ('floor','tabletop')}
    flag=route.par.Enablemotion
    if any(n is None for n in selectors.values()):
        raise RuntimeError('Routing-Select fehlt.')
    pars=[n.par.top for n in selectors.values()]+[flag]
    if any(str(p.mode) != 'ParMode.CONSTANT' for p in pars):
        raise RuntimeError('Lokale Routing-Parameter sind nicht konstant; nichts geändert.')
    old_paths={s:n.par.top.val for s,n in selectors.items()}
    for surface,path in old_paths.items():
        if path not in ('/project1/comp_aisi_motion_v1_5/out_'+surface,
                        SNAPSHOT+'/out_'+surface):
            raise RuntimeError('Lokale Routing-Quelle wurde anderweitig geändert; nichts überschrieben.')
    old_enabled=flag.val
    result={'passed':False,'checks':[],'saved':False,
            'production_outputs_changed':False,'physical_validation':'not performed'}
    created=[]

    def require(ok, text):
        if not ok:
            raise RuntimeError(text)
        result['checks'].append(text)

    def pixels(node):
        node.cook(force=True)
        if node.errors():
            raise RuntimeError(node.path+': '+str(node.errors()))
        return node.numpyArray(delayed=False).copy()

    try:
        # The helpers use stored table/geometry data, not a claim of fresh tracking.
        if REPO not in sys.path:
            sys.path.insert(0,REPO)
        from td_builders.build_motion_aligned_snapshot import preflight,screen_pose
        rows, alignment=preflight(resolve)
        require(alignment['pose_alignment_passed'],'Aktuelle Masken passen weiterhin zu den Legacy-Slots')
        dat=snapshot.op('poses')
        stored={dat[i,0].val:tuple(float(dat[i,j].val) for j in range(1,4))
                for i in range(1,dat.numRows)}
        require(len(stored)==len(rows) and all(
            'legacy_slot_%d' % slot in stored and all(abs(a-b)<1e-6
                for a,b in zip(stored['legacy_slot_%d' % slot],screen_pose(source)))
            for slot,source,target in rows),'Snapshot-Sources entsprechen weiterhin exakt den Maskenposen')
        pixel=snapshot.create(symbols['textDAT'],PROBE_NAMES[0])
        created.append(pixel)
        pixel.text=coverage_shader(snapshot.op('motion_pixel').text)
        probe=snapshot.copy(snapshot.op('render_tabletop'),name=PROBE_NAMES[1],includeDocked=False)
        created.append(probe)
        probe.par.pixeldat=pixel.path
        probe.inputConnectors[0].connect(snapshot.op('state'))
        uniform=getattr(probe.par,'vec0valuex',None)
        if uniform is None:
            uniform=getattr(probe.par,'value0x',None)
        if uniform is None:
            raise RuntimeError('Uniform-Schnittstelle fehlt.')
        uniform.val=3
        masked,local_mask=create_mask_probe(snapshot,route,probe,symbols['selectTOP'],created)
        result['checks'].append('Beide Masken-Probeeingänge liegen im Snapshot-Netzwerk')
        result['mask_measurement']=measure(pixels(probe),pixels(masked),pixels(local_mask))
        measurement=result['mask_measurement']
        require(measurement['masked_probe_lit_pixels']>0,'Bestehende Maske lässt Tisch-Content durch')
        require(measurement['lit_pixels_outside_mask']==0,'Kein helles RGB außerhalb der bestehenden Maske')
        flag.val=False
        for surface,node in selectors.items():
            node.par.top=snapshot.op('out_'+surface).path
        flag.val=True
        require(all(route.op(s+'_switch').par.index.eval()==1 for s in selectors),
                'Aktueller AISI-Modus wählt die Snapshot-Ausgänge im Prüfzweig')
        for surface in selectors:
            pixels(route.op('out_'+surface))
        result['checks'].append('Snapshot-Ausgänge im isolierten Routing-Prüfzweig fehlerfrei')
        route.store('motion_snapshot_routing_previous',{'sources':old_paths,'enabled':bool(old_enabled)})
        route.storeStartupValue('motion_snapshot_routing_previous',None)
        result.update({'passed':True,'local_preview_enabled':True,
            'tabletop_viewer':route.op('out_tabletop').path,'floor_viewer':route.op('out_floor').path,
            'mask_shape_acceptance':'measurement and manual review pending; no physical claim'})
    except Exception as error:
        flag.val=False
        for surface,node in selectors.items():
            node.par.top=old_paths[surface]
        flag.val=old_enabled
        result['failure']=str(error)
        result['local_routing_restored']=True
    finally:
        for node in reversed(created):
            node.destroy()
        result['temporary_probes_removed']=True
    return result


def symbol(name):
    return (globals().get(name) or getattr(builtins,name,None)
            or getattr(sys.modules.get('__main__'),name,None))


if globals().get('__spec__') is None and callable(symbol('op')):
    kinds=('textDAT','selectTOP')
    print(json.dumps(check(symbol('op'),{k:symbol(k) for k in kinds}),ensure_ascii=False,indent=2))
