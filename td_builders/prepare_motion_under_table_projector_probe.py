"""Disconnected calibrated floor comparison; copies TOPs, never projector COMPs."""
import hashlib
from td_builders import prepare_motion_under_table_probe as world
from td_builders import build_motion_output_routing as routing

PROBE='/project1/comp_aisi_motion_under_table_projector_probe'
SESSION='motion_under_table_projector_probe'


def set_float(node):
    par=getattr(node.par,'format',None)
    if par is None:
        par=getattr(node.par,'pixelformat',None)
    routing.require(par is not None,'Float-Ausgabeformat fehlt: '+node.path)
    par.val='rgba32float'


def local_source(parent,source):
    # TOP connectors cannot cross network boundaries; references use Select TOPs.
    if source.parent()==parent:
        return source
    name='ref_'+hashlib.sha256(source.path.encode('utf-8')).hexdigest()[:12]
    node=parent.op(name)
    if node is None:
        node=parent.create(routing.symbol('selectTOP'),name)
        node.par.top=source.path
    else:
        routing.require(str(node.type)=='select' and routing.ref(node.par.top)==source.path,
                        'Eigene TOP-Referenz kollidiert: '+name)
    return node


def copy_top(parent,original,name,inputs):
    """Copy only known static TOPs; retain source sampling/transform settings."""
    routing.require(getattr(original,'isTOP',False) and str(original.type) in ('glsl','transform','comp','level'),
                    'Unerwarteter Operatortyp: '+original.path)
    routing.require(all(str(p.mode)=='ParMode.CONSTANT' for p in original.pars()),
                    'TOP enthält dynamische Parameter; Kopie verlangt gezielte Prüfung: '+original.path)
    routing.require(len(original.inputs)==len(inputs),'Anzahl der Kopie-Eingänge weicht ab: '+original.path)
    node=parent.copy(original,name=name,includeDocked=False)
    for index,source in enumerate(inputs):
        node.inputConnectors[index].connect(local_source(parent,source))
    # Float precision only in this isolated experiment; native originals are untouched.
    set_float(node)
    return node


def copy_warp(parent,original,name,source):
    pixel=original.par.pixeldat.eval()
    if not hasattr(pixel,'text'):
        pixel=original.op(str(pixel))
    routing.require(pixel is not None and str(pixel.type)=='text','Warp-Pixel-DAT fehlt: '+original.path)
    shader=parent.create(routing.symbol('textDAT'),name+'_pixel')
    shader.text=pixel.text
    node=copy_top(parent,original,name,[source])
    node.par.pixeldat=shader.path
    # Resolve any other shader references in the original scope; do not run DAT modules.
    for key in ('vertexdat','computedat'):
        par=getattr(original.par,key,None)
        if par is not None:
            value=par.eval()
            if value:
                ref=value if hasattr(value,'path') else original.op(str(value))
                routing.require(ref is not None,'Shader-Referenz nicht auflösbar: '+str(value))
                getattr(node.par,key).val=ref.path
    size=(int(original.width),int(original.height))
    routing.require(size==(3840,2160),'Projektorraster weicht vom gelesenen Shader ab: '+str(size))
    node.par.outputresolution='custom'
    node.par.resolutionw,node.par.resolutionh=size
    return node


def replace_input_copy(parent,original,name,old_source,new_source):
    inputs=list(original.inputs)
    routing.require(sum(n.path==old_source.path for n in inputs)==1,
                    'Bestätigter Anschluss weicht ab: '+original.path)
    inputs=[new_source if n.path==old_source.path else n for n in inputs]
    return copy_top(parent,original,name,inputs)


def validate(resolve,probe,info):
    source=resolve(world.PROBE)
    routing.require(source is not None,'Weltbild-Prüfzweig fehlt.')
    world.assert_unchanged(resolve,source,source.fetch(world.SESSION))
    routing.require(world.own_snapshot(probe)==info['owned'],'Projektor-Prüfzweig lokal verändert.')
    return source


def prepare(resolve,projector=0):
    routing.require(projector in (0,1),'Projektor muss 0 oder 1 sein.')
    source=resolve(world.PROBE)
    routing.require(source is not None,'Zuerst Weltbildvergleich vorbereiten und prüfen.')
    source_info=source.fetch(world.SESSION,None)
    routing.require(isinstance(source_info,dict),'Registrierung des Weltbildvergleichs fehlt.')
    world.assert_unchanged(resolve,source,source_info)
    routing.require(resolve(PROBE) is None,'Eigener Projektor-Prüfzweig existiert bereits.')
    probe=resolve('/project1').create(routing.symbol('containerCOMP'),PROBE.rsplit('/',1)[1])
    try:
        # Extract occupancy and the exact extra target component from the proven shader.
        for name,output in (('source_mask','vec4(occupied)'),
                            ('extra_target','white(floorTargets.a*occupied)')):
            text=source_info['new'].replace(world.SURFACE,
                '    else if(uSurface.x<1.5) fragColor=TDOutputSwizzle('+output+');',1)
            shader=probe.create(routing.symbol('textDAT'),name+'_pixel')
            shader.text=text
            node=probe.copy(source.op('mask_tabletop'),name=name,includeDocked=False)
            node.par.pixeldat=shader.path
            # Make the dependency explicit; never change the source State TOP.
            node.inputConnectors[0].connect(local_source(probe,source.op('state')))
            set_float(node)
        branches={}
        # One native-resolution projector at a time limits isolated Float32 GPU memory.
        for index in (projector,):
            prefix='p'+str(index)+'_'
            actual=resolve(routing.OUTPUT+'comp_projector_'+str(index))
            floor=actual.op('comp_homography_floor')
            mask=actual.op('comp_homography_table_mask')
            routing.require(floor is not None and mask is not None,'Homographie-Zweig fehlt.')
            floor_warp=floor.op('homography_warp')
            floor_blend=floor.op('multiply_blend')
            routing.require(floor_warp is not None and floor_blend is not None
                            and list(floor.op('out1').inputs)==[floor_blend],
                            'Floor-Ausgangspfad lokal abweichend.')
            routing.require(list(mask.op('out1').inputs)==[mask.op('homography_warp')],
                            'Masken-Ausgangspfad lokal abweichend.')
            real_masked=actual.op('floor_masked_warped1')
            routing.require(real_masked is not None and len(real_masked.inputs)==2
                            and real_masked.par.operand.eval()=='multiply','Boden-Maskierung weicht ab.')
            real_inverse=actual.op('comp_homography_table_mask1' if index==0 else 'invert_table_mask')
            routing.require(real_inverse is not None and list(real_inverse.inputs)==[mask.op('out1')]
                            and real_inverse.par.invert.eval()==1,'Invertierte Tischmaske weicht ab.')
            mask_source=probe.op('source_mask')
            if index==1:
                mask_source=copy_top(probe,resolve(routing.OUTPUT+'rotate_180_table_mask'),
                                     prefix+'mask_rotation',[mask_source])
            mask_warp=copy_warp(probe,mask.op('homography_warp'),prefix+'mask_warp',mask_source)
            inverse=copy_top(probe,real_inverse,prefix+'transmission',[mask_warp])
            outputs={}
            for role,input_node in (('before',source.op('old_floor')),
                                    ('after',source.op('new_floor')),
                                    ('extra',probe.op('extra_target'))):
                if index==1:
                    input_node=copy_top(probe,resolve(routing.OUTPUT+'rotate_180_floor'),
                                        prefix+role+'_rotation',[input_node])
                warp=copy_warp(probe,floor_warp,prefix+role+'_warp',input_node)
                blend=replace_input_copy(probe,floor_blend,prefix+role+'_blend',floor_warp,warp)
                mapping={floor.op('out1').path:blend,real_inverse.path:inverse}
                routing.require(all(n.path in mapping for n in real_masked.inputs),'Zusätzliche Maskeneingänge entdeckt.')
                masked=copy_top(probe,real_masked,prefix+role,[mapping[n.path] for n in real_masked.inputs])
                outputs[role]=masked.path
            branches[index]=dict(outputs=outputs,transmission=inverse.path,
                                 raster=[3840,2160],precision='isolated float32')
        info=dict(branches=branches)
        info['owned']=world.own_snapshot(probe)
        probe.store(SESSION,info)
        validate(resolve,probe,info)
    except Exception:
        probe.destroy()
        raise
    return dict(prepared=True,probe=PROBE,projector=projector,simulation_only=True,projector_connected=False,
                original_calibration_changed=False,original_masks_changed=False,
                precision='float32 copies; native originals unchanged',saved=False,
                next='check this projector separately; remove own probe before preparing the other projector')


def compare_rgb(before,after,extra,transmission):
    import numpy as np
    routing.require(before.shape==after.shape==extra.shape==transmission.shape
                    and before.ndim==3 and before.shape[2]==3,'Ungültige RGB-Prüfbilder.')
    routing.require(all(np.isfinite(a).all() for a in (before,after,extra,transmission)),
                    'Nichtendliche Projektor-Prüfbilder.')
    difference=after-before
    routing.require(float(extra.min())>=-1e-6 and float(difference.min())>=-1e-5,
                    'Unerwartete Abdunklung statt zusätzlicher Zielgrafik.')
    error=float(np.max(np.abs(difference-extra)))
    routing.require(error<=1e-5,'Zusatzlicht folgt nicht unveränderter Projektormaske: '+str(error))
    blocked=np.max(np.abs(transmission),axis=2)<=1e-6
    blocked_error=float(np.max(np.abs(difference[blocked]))) if blocked.any() else 0
    routing.require(blocked_error<=1e-6,'Zusatzlicht in vollständig gesperrtem Maskenbereich.')
    lit=np.max(extra,axis=2)>.01
    clear=np.min(transmission,axis=2)>=.999
    return dict(max_rgb_equation_error=error,blocked_pixels=int(blocked.sum()),
                max_added_rgb_in_blocked_area=blocked_error,additional_pixels=int(lit.sum()),
                additional_pixels_in_clear_area=int((lit&clear).sum()))


def check(resolve,projector):
    import numpy as np
    from td_builders.motion_design import WIDTH,DEPTH,CORNER
    routing.require(projector in (0,1),'Projektor muss 0 oder 1 sein.')
    probe=resolve(PROBE)
    routing.require(probe is not None,'Zuerst prepare(op) ausführen.')
    info=probe.fetch(SESSION,None)
    routing.require(isinstance(info,dict),'Eigene Registrierung fehlt.')
    routing.require(projector in info['branches'],'Dieser Projektor ist nicht vorbereitet.')
    source=validate(resolve,probe,info)
    branch=info['branches'][projector]
    def read_rgb(path):
        node=resolve(path)
        routing.digest(node)
        return node.numpyArray(delayed=False)[:,:,:3].copy()
    checks=[]
    for center in ((180,150),(320,350)):
        for rotation in (0,33,90):
            data=np.zeros((6,6,4),np.float32)
            data[0,0]=(*center,rotation,1)
            data[0,1]=(center[0]+25,center[1],rotation+10,1)
            data[0,2]=(.5,.5,.6,0)
            data[0,3]=(0,0,0,1)
            data[0,4]=(WIDTH,DEPTH,CORNER,0)
            data[0,5]=(1,1,0,0)
            data[5,0]=(4,4,1,1)
            source.store('data',data)
            source.op('state').cook(force=True)
            images={role:read_rgb(path) for role,path in branch['outputs'].items()}
            transmission=read_rgb(branch['transmission'])
            result=compare_rgb(images['before'],images['after'],images['extra'],transmission)
            checks.append(dict(source_center_cm=list(center),rotation_deg=rotation,**result))
    validate(resolve,probe,info)
    return dict(passed=True,projector=projector,gpu_checks=checks,simulation_only=True,
                additional_pixels_found=any(c['additional_pixels']>0 for c in checks),
                projector_connected=False,original_calibration_changed=False,original_masks_changed=False,
                saved=False,physical_validation='not performed',
                compared_stage='calibrated floor after original-equivalent mask; before tabletop composite',
                precision='float32 copies; native-output quantization not verified',
                viewers=branch['outputs'],next='evaluate both projector reports before any live/physical trial')


def cleanup(resolve):
    probe=resolve(PROBE)
    routing.require(probe is not None,'Eigener Projektor-Prüfzweig fehlt.')
    info=probe.fetch(SESSION,None)
    routing.require(isinstance(info,dict),'Eigene Registrierung fehlt.')
    validate(resolve,probe,info)
    probe.destroy()
    return dict(removed=True,production_outputs_changed=False,saved=False)
