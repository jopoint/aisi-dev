"""Native-format isolated floor + tabletop output comparison, one projector at a time."""
import re

from td_builders import prepare_motion_under_table_probe as world
from td_builders import prepare_motion_under_table_projector_probe as geometry
from td_builders import update_motion_feedback_brightness as transaction
from td_builders import build_motion_output_routing as routing

PROBE='/project1/comp_aisi_motion_under_table_native_probe'
SESSION='motion_under_table_native_probe'
UNUSED_BACKUP='motion_under_table_native_no_install'
FORMATS={'rgba8fixed':1/255,'rgba16fixed':1/65535,'rgba16float':1/1024,'rgba32float':2**-23}


def format_parameter(node):
    par=getattr(node.par,'format',None)
    if par is None: par=getattr(node.par,'pixelformat',None)
    routing.require(par is not None,'Formatparameter fehlt: '+node.path)
    return par


def effective_format(node,_seen=frozenset()):
    """Resolve actual storage, including older TD builds without pixelFormatName."""
    name=getattr(node,'pixelFormatName',None)
    if name in FORMATS: return name
    display=str(getattr(node,'pixelFormat',''))
    if display in FORMATS: return display
    tokens=lambda value: sorted(re.findall(r'[a-z0-9]+',str(value).lower()))
    par=format_parameter(node)
    for name,label in zip(par.menuNames,par.menuLabels):
        if name in FORMATS and tokens(label)==tokens(display): return name
    value=par.eval()
    if value in FORMATS: return value
    # TD 2022 may expose neither format property. Trace only unambiguous inheritance.
    if value=='useinput':
        key=node.path
        routing.require(key not in _seen,'Zyklische Formatvererbung: '+key)
        sources=list(getattr(node,'inputs',()))
        if str(getattr(node,'type',''))=='select':
            ref=node.par.top.eval()
            ref=ref if hasattr(ref,'path') else node.op(str(ref))
            routing.require(ref is not None,'Select-Formatquelle fehlt: '+key)
            sources=[ref]
        if str(getattr(node,'type',''))=='switch':
            # A non-blending Switch passes one selected input, not all input formats.
            blend=getattr(node.par,'blend',None)
            routing.require(blend is not None and not bool(blend.eval()),
                            'Switch-Format bei aktiviertem Blending ohne Format-API nicht eindeutig: '+key)
            index=float(node.par.index.eval())
            routing.require(index.is_integer() and 0<=index<len(sources),
                            'Switch-Format verlangt ganzzahligen Index innerhalb der Eingänge: '+key)
            sources=[sources[int(index)]]
        if str(getattr(node,'type',''))=='in' and not sources:
            order=getattr(node.par,'connectorder',None)
            routing.require(order is not None,'In-TOP-Formatquelle nicht eindeutig auflösbar: '+key)
            index=int(order.eval())
            external=list(node.parent().inputs)
            ins=[n for n in node.parent().children if getattr(n,'isTOP',False) and str(n.type)=='in']
            orders=[getattr(n.par,'connectorder',None) for n in ins]
            routing.require(len(ins)==len(external) and all(p is not None for p in orders)
                            and {int(p.eval()) for p in orders}==set(range(len(external))),
                            'In-TOP-Reihenfolge nicht eindeutig: '+key)
            routing.require(0<=index<len(external),'In-TOP-Eingangsnummer ungültig: '+key)
            sources=[external[index]]
        routing.require(bool(sources),'Formatvererbung ohne bekannte Quelle: '+key)
        formats={effective_format(source,_seen|{key}) for source in sources}
        routing.require(len(formats)==1,'Gemischte Eingangsformate ohne effektive Format-API: '+key)
        return formats.pop()
    raise RuntimeError('Effektives natives Format nicht eindeutig unterstützt: '+node.path+' / '+display)


def spec(node):
    return dict(format=effective_format(node),size=[int(node.width),int(node.height)])


def remember(info,node):
    info['originals'][node.path]=world.signature(node)
    if getattr(node,'isTOP',False): info['specs'][node.path]=spec(node)


def inspect_stages(resolve):
    """Read all planned native copy stages at once, without creating/cooking nodes."""
    paths=[routing.MOTION+name for name in ('render_floor','render_tabletop')]
    paths += [routing.PATH+'/'+name for name in ('floor_motion','tabletop_motion')]
    paths += [routing.LAYOUT+name for name in (
        'reorder_table_mask','null_table_mask','select_floor_for_synth_chairs',
        'composite_floor_with_synth_chairs','switch_enable_synth_chairs_regular',
        'null_floor_with_optional_synth_chairs',routing.BRIDGE,'null_tabletop',
        'mask_tabletop','null_tabletop_masked')]
    paths += [routing.OUTPUT+name for name in (
        'select_table_mask','switch_table_mask','select_central_floor','switch_floor',
        'layer_floor_switch','select_tabletop','switch_tabletop','layer_tabletop_switch',
        'rotate_180_floor','rotate_180_tabletop','rotate_180_table_mask')]
    for index in (0,1):
        root=routing.OUTPUT+'comp_projector_'+str(index)+'/'
        paths += [root+name for name in (
            'floor_masked_warped1','composite_final',
            'comp_homography_table_mask1' if index==0 else 'invert_table_mask')]
        for branch in ('floor','table','table_mask'):
            paths += [root+'comp_homography_'+branch+'/'+name
                      for name in (('homography_warp',) if branch=='table_mask'
                                   else ('homography_warp','multiply_blend'))]
    dynamic=[]
    formats=[]
    missing=[]
    for path in paths:
        node=resolve(path)
        if node is None:
            missing.append(path)
            continue
        for p in node.pars():
            if str(p.mode)=='ParMode.CONSTANT': continue
            try: value=str(p.eval())
            except Exception as error: value='LESEFEHLER: '+str(error)
            dynamic.append(dict(path=path,type=str(node.type),parameter=p.name,mode=str(p.mode),
                                evaluated=value,expression=p.expr or '',binding=p.bindExpr or ''))
        try: effective=effective_format(node)
        except Exception as error: effective='NICHT AUFGELÖST: '+str(error)
        formats.append(dict(path=path,setting=str(format_parameter(node).eval()),effective=effective,
                            size=[int(node.width),int(node.height)],gpu_memory_bytes=getattr(node,'gpuMemory',None)))
    return dict(read_only=True,nodes_created=False,forced_cooks=False,saved=False,
                inspected_nodes=len(paths),dynamic_parameters=dynamic,
                format_issues=[row for row in formats if row['effective'].startswith('NICHT AUFGELÖST:')],
                missing=missing)


def native_copy(parent,original,name,inputs,info,freeze=()):
    routing.require(getattr(original,'isTOP',False) and str(original.type) in
                    ('glsl','transform','comp','level','select','null','switch','reorder'),
                    'Nicht bestätigter TOP-Typ: '+original.path)
    routing.require(len(original.inputs)==len(inputs),'Eingangsanzahl weicht ab: '+original.path)
    dynamic=[p for p in original.pars() if str(p.mode)!='ParMode.CONSTANT']
    routing.require(all(p.name in freeze and str(p.mode)=='ParMode.EXPRESSION' for p in dynamic),
                    'Nicht freigegebener dynamischer Parameter: '+original.path+' / '
                    +str([(p.name,str(p.mode),p.expr or '',p.bindExpr or '') for p in dynamic]))
    remember(info,original)
    node=parent.copy(original,name=name,includeDocked=False)
    constant_mode=format_parameter(original).mode
    routing.require(str(constant_mode)=='ParMode.CONSTANT','Formatparameter ist dynamisch: '+original.path)
    for p in dynamic:
        value=p.eval()
        own=getattr(node.par,p.name)
        own.expr=''
        own.mode=constant_mode
        own.val=value
        info['frozen'].append((original.path,p.name,str(value)))
    for index,source in enumerate(inputs):
        node.inputConnectors[index].connect(geometry.local_source(parent,source))
    # Freeze resolved storage, not "useinput", since test inputs can have another format.
    format_parameter(node).val=info['specs'][original.path]['format']
    info['copies'][node.path]=info['specs'][original.path]
    return node


def copy_shader(parent,original,name,source,info,text=None,freeze=()):
    pixel=original.par.pixeldat.eval()
    if not hasattr(pixel,'text'): pixel=original.op(str(pixel))
    routing.require(pixel is not None and str(pixel.type)=='text','Pixel-DAT fehlt: '+original.path)
    remember(info,pixel)
    shader=parent.create(routing.symbol('textDAT'),name+'_pixel')
    shader.text=pixel.text if text is None else text
    node=native_copy(parent,original,name,[source],info,freeze=freeze)
    node.par.pixeldat=shader.path
    for key in ('vertexdat','computedat'):
        par=getattr(original.par,key,None)
        if par is not None and par.eval():
            value=par.eval()
            ref=value if hasattr(value,'path') else original.op(str(value))
            routing.require(ref is not None,'Shader-Referenz fehlt: '+str(value))
            remember(info,ref)
            getattr(node.par,key).val=ref.path
    return node


def select_copy(parent,original,name,source,info):
    routing.require(str(original.type)=='select','Select TOP erwartet: '+original.path)
    node=native_copy(parent,original,name,[],info,freeze=('resolutionw','resolutionh'))
    node.par.top=source.path
    return node


def freeze_image(parent,original,name,info):
    remember(info,original)
    pixels=original.numpyArray(delayed=False)
    routing.require(pixels is not None,'Snapshot-Textur fehlt: '+original.path)
    parent.store(name+'_data',pixels.copy())
    callback=parent.create(routing.symbol('textDAT'),name+'_callbacks')
    callback.text="def onCook(scriptOp):\n    scriptOp.copyNumpyArray(scriptOp.parent().fetch(%r))\n" % (name+'_data')
    node=parent.create(routing.symbol('scriptTOP'),name)
    node.par.callbacks=callback.path
    format_parameter(node).val=info['specs'][original.path]['format']
    info['copies'][node.path]=info['specs'][original.path]
    return node


def source_mask_convention(pixels,reordered,channels):
    import numpy as np
    routing.require(pixels is not None and pixels.ndim==3 and pixels.shape[2]==4
                    and np.isfinite(pixels).all(),'Originale rohe Maskenpixel fehlen.')
    expected={'outputred':'input1','outputredchan':'alpha',
              'outputgreen':'input1','outputgreenchan':'alpha',
              'outputblue':'input1','outputbluechan':'alpha',
              'outputalpha':'input1','outputalphachan':'one','chanmask':'15'}
    routing.require(all(str(channels.get(k))==v for k,v in expected.items()),
                    'Nicht bestätigte Reorder-Kanalzuordnung; nichts produktiv verändert.')
    routing.require(reordered is not None and reordered.shape==pixels.shape
                    and np.isfinite(reordered).all(),'Reorder-Vergleichspixel fehlen.')
    alpha=pixels[:,:,3]
    routing.require(float(alpha.min())>=0 and float(alpha.max())<=1,'Maskenalpha außerhalb 0..1.')
    routing.require(float(np.max(np.abs(reordered[:,:,:3]-alpha[:,:,None])))<=1e-6
                    and float(np.max(np.abs(reordered[:,:,3]-1)))<=1e-6,
                    'Gemessene Maske folgt nicht bestätigter Alpha-zu-RGB-Zuordnung.')
    return 'alpha_coverage_to_rgb'


def validate(resolve,probe,info):
    routing.require(world.projection_snapshot(resolve)==info['projection'],
                    'Projektor/Kalibrierung/Maskierung seit Vorbereitung verändert.')
    for path,expected in info['originals'].items():
        node=resolve(path)
        routing.require(node is not None and world.signature(node)==expected,'Originalknoten verändert: '+path)
    for path,expected in info['specs'].items():
        routing.require(spec(resolve(path))==expected,'Natives Originalformat/Raster verändert: '+path)
    for path,name,value in info['frozen']:
        routing.require(str(getattr(resolve(path).par,name).eval())==value,
                        'Erfasste Steuerung/Auflösung verändert: '+path+'/'+name)
    motion=resolve(routing.MOTION[:-1])
    routing.require(motion.op('motion_pixel').text==info['old']
                    and motion.fetch('motion_engine',None) is info['engine']
                    and motion.fetch('motion_osc_reader',None) is info['reader']
                    and getattr(info['engine'],'revision',None)==info['revision'],
                    'Produktiver Motion-Zustand seit Vorbereitung verändert.')
    routing.require(world.own_snapshot(probe)==info['owned'],'Eigener nativer Prüfzweig lokal verändert.')


def prepare(resolve,projector=0):
    routing.require(projector in (0,1),'Projektor muss 0 oder 1 sein.')
    motion=transaction.shadow._validate(resolve)
    routing.require(resolve(PROBE) is None,'Eigener nativer Prüfzweig existiert bereits.')
    # Content mode and both layers are read, never switched by this helper.
    for name,wanted in (('switch_floor',0),('switch_tabletop',0),('switch_table_mask',0),
                        ('layer_floor_switch',1),('layer_tabletop_switch',1)):
        routing.require(resolve(routing.OUTPUT+name).par.index.eval()==wanted,
                        'Vergleich verlangt Content mit beiden Ebenen: '+name)
    projection=world.projection_snapshot(resolve)
    engine,reader=motion.fetch('motion_engine',None),motion.fetch('motion_osc_reader',None)
    revision=getattr(engine,'revision',None)
    transaction.prepare(resolve,probe_path=PROBE,session=SESSION,
                        backup=UNUSED_BACKUP,patcher=world.patch_shader)
    probe=resolve(PROBE)
    try:
        info=dict(probe.fetch(SESSION))
        info.update(projector=projector,projection=projection,engine=engine,reader=reader,
                    revision=revision,originals={},specs={},copies={},frozen=[])
        state=probe.op('state')
        layout=resolve(routing.LAYOUT[:-1])
        raw=layout.op('render_table_mask')
        remember(info,raw)
        real_reorder=layout.op('reorder_table_mask')
        routing.require(list(real_reorder.inputs)==[raw],'Roher Masken-/Reorder-Pfad weicht ab.')
        channels={p.name:str(p.eval()) for p in real_reorder.pars()}
        alpha_mode=source_mask_convention(raw.numpyArray(delayed=False),
                                         real_reorder.numpyArray(delayed=False),channels)
        # Same canonical synthetic occupancy as the previous model, now native mask raster/storage.
        # Raw RGB is lighting-dependent and ignored by the confirmed Reorder mapping.
        text=info['new'].replace(world.SURFACE,
            '    else if(uSurface.x<1.5) fragColor=TDOutputSwizzle(vec4(vec3(0),occupied));',1)
        shader=probe.create(routing.symbol('textDAT'),'native_mask_pixel')
        shader.text=text
        mask_source=probe.copy(probe.op('mask_tabletop'),name='native_mask_raw',includeDocked=False)
        mask_source.par.pixeldat=shader.path
        mask_source.par.resolutionw,mask_source.par.resolutionh=info['specs'][raw.path]['size']
        format_parameter(mask_source).val=info['specs'][raw.path]['format']
        info['copies'][mask_source.path]=info['specs'][raw.path]
        reorder=native_copy(probe,layout.op('reorder_table_mask'),'native_mask_reorder',[mask_source],info)
        mask_null=native_copy(probe,layout.op('null_table_mask'),'native_mask_null',[reorder],info)
        mask_select=select_copy(probe,resolve(routing.OUTPUT+'select_table_mask'),'native_mask_select',mask_null,info)
        mask_switch=resolve(routing.OUTPUT+'switch_table_mask')
        mask_input=native_copy(probe,mask_switch,'native_mask_switch',
                               [mask_select,mask_switch.inputs[1]],info,freeze=('index',))
        chairs=layout.op('composite_floor_with_synth_chairs')
        routing.require(chairs is not None and len(chairs.inputs)==2,'Bestätigte Chair-Komposition fehlt.')
        chair_snapshot=freeze_image(probe,chairs.inputs[1],'frozen_chairs',info)
        # Native Motion renderer and resampling stages are copied from the running graph.
        floor_inputs={}
        for role,key in (('before','old'),('after','new')):
            render=copy_shader(probe,motion.op('render_floor'),role+'_world_floor',state,info,
                               text=info[key],freeze=('resolutionw','resolutionh'))
            routed=select_copy(probe,resolve(routing.PATH+'/floor_motion'),role+'_motion_floor',render,info)
            base=select_copy(probe,layout.op('select_floor_for_synth_chairs'),role+'_base_floor',routed,info)
            composed=native_copy(probe,chairs,role+'_with_chairs',[base,chair_snapshot],info)
            optional=native_copy(probe,layout.op('switch_enable_synth_chairs_regular'),role+'_optional_chairs',
                                 [base,composed],info,freeze=('index',))
            original=layout.op('null_floor_with_optional_synth_chairs')
            common=native_copy(probe,original,role+'_floor_null',[optional],info)
            central=select_copy(probe,resolve(routing.OUTPUT+'select_central_floor'),role+'_floor_select',common,info)
            switch=resolve(routing.OUTPUT+'switch_floor')
            content=native_copy(probe,switch,role+'_floor_switch',[central,switch.inputs[1]],info,freeze=('index',))
            layer=resolve(routing.OUTPUT+'layer_floor_switch')
            floor_inputs[role]=native_copy(probe,layer,role+'_floor_layer',[layer.inputs[0],content],info,freeze=('index',))
        table_renders={}
        for role,key in (('before','old'),('after','new')):
            table_renders[role]=copy_shader(probe,motion.op('render_tabletop'),role+'_world_tabletop',state,info,
                                           text=info[key],freeze=('resolutionw','resolutionh'))
        tt=select_copy(probe,resolve(routing.PATH+'/tabletop_motion'),'native_motion_tabletop',table_renders['before'],info)
        tt=select_copy(probe,layout.op(routing.BRIDGE),'native_tabletop_bridge',tt,info)
        tt=native_copy(probe,layout.op('null_tabletop'),'native_tabletop_null',[tt],info)
        tt=native_copy(probe,layout.op('mask_tabletop'),'native_tabletop_masked',[tt,mask_null],info)
        tt=native_copy(probe,layout.op('null_tabletop_masked'),'native_tabletop_masked_null',[tt],info)
        tt=select_copy(probe,resolve(routing.OUTPUT+'select_tabletop'),'native_tabletop_select',tt,info)
        switch=resolve(routing.OUTPUT+'switch_tabletop')
        tt=native_copy(probe,switch,'native_tabletop_switch',[tt,switch.inputs[1]],info,freeze=('index',))
        layer=resolve(routing.OUTPUT+'layer_tabletop_switch')
        tt=native_copy(probe,layer,'native_tabletop_layer',[layer.inputs[0],tt],info,freeze=('index',))
        if projector==1:
            for role in floor_inputs:
                floor_inputs[role]=native_copy(probe,resolve(routing.OUTPUT+'rotate_180_floor'),
                                               role+'_rotation',[floor_inputs[role]],info)
            tt=native_copy(probe,resolve(routing.OUTPUT+'rotate_180_tabletop'),'tabletop_rotation',[tt],info)
            mask_input=native_copy(probe,resolve(routing.OUTPUT+'rotate_180_table_mask'),'mask_rotation',[mask_input],info)
        actual=resolve(routing.OUTPUT+'comp_projector_'+str(projector))
        mask=actual.op('comp_homography_table_mask')
        routing.require(list(mask.op('out1').inputs)==[mask.op('homography_warp')],'Maskenpfad weicht ab.')
        mask_warp=copy_shader(probe,mask.op('homography_warp'),'native_mask_warp',mask_input,info)
        inverse=actual.op('comp_homography_table_mask1' if projector==0 else 'invert_table_mask')
        routing.require(list(inverse.inputs)==[mask.op('out1')] and inverse.par.invert.eval()==1,'Invert-Pfad weicht ab.')
        transmission=native_copy(probe,inverse,'native_transmission',[mask_warp],info)
        def warped(branch,input_node,name):
            real=actual.op('comp_homography_'+branch)
            warp=real.op('homography_warp')
            blend=real.op('multiply_blend')
            routing.require(list(real.op('out1').inputs)==[blend],'Blend-Ausgang weicht ab: '+real.path)
            own=copy_shader(probe,warp,name+'_warp',input_node,info)
            inputs=[own if n.path==warp.path else n for n in blend.inputs]
            routing.require(sum(n.path==warp.path for n in blend.inputs)==1,'Blend-Verbindung weicht ab.')
            return native_copy(probe,blend,name+'_blend',inputs,info)
        front=warped('table',tt,'tabletop')
        outputs={}
        floor_outputs={}
        real_floor=actual.op('comp_homography_floor/out1')
        real_masked=actual.op('floor_masked_warped1')
        final=actual.op('composite_final')
        routing.require(real_masked.par.operand.eval()=='multiply' and final.par.operand.eval()=='over',
                        'Multiply-/Over-Reihenfolge weicht ab.')
        routing.require([n.path for n in final.inputs]==[actual.op('comp_homography_table/out1').path,real_masked.path]
                        and list(actual.op('out1').inputs)==[final],'Finale Anschlüsse weichen ab.')
        routing.require(spec(actual.op('out1'))==spec(final)
                        and spec(resolve(routing.OUTPUT+'out_projector_'+str(projector)))==spec(final),
                        'Zusätzliche Ausgabeformat-/Rasterkonvertierung entdeckt.')
        for role,input_node in floor_inputs.items():
            floor=warped('floor',input_node,role)
            mapping={real_floor.path:floor,inverse.path:transmission}
            routing.require(all(n.path in mapping for n in real_masked.inputs),'Floor-Maskenanschluss weicht ab.')
            floor=native_copy(probe,real_masked,role+'_floor_masked',[mapping[n.path] for n in real_masked.inputs],info)
            result=native_copy(probe,final,role+'_final',[front,floor],info)
            outputs[role]=result.path
            floor_outputs[role]=floor.path
        info.update(outputs=outputs,floor_outputs=floor_outputs,front=front.path,transmission=transmission.path,
                    table_renders={k:v.path for k,v in table_renders.items()},mask_alpha=alpha_mode)
        info['owned']=world.own_snapshot(probe)
        probe.store(SESSION,info)
        validate(resolve,probe,info)
    except Exception:
        probe.destroy()
        raise
    return dict(prepared=True,projector=projector,probe=PROBE,simulation_only=True,projector_connected=False,
                original_calibration_changed=False,original_masks_changed=False,production_outputs_changed=False,
                chair_snapshot=True,mask_alpha=alpha_mode,
                native_formats={role:spec(resolve(path)) for role,path in outputs.items()},saved=False,
                next='run check(op) in a separate Textport entry; native output remains disconnected')


def compare_final(before,after,floor_before,floor_after,front,transmission,output_format,floor_format):
    import numpy as np
    images=(before,after,floor_before,floor_after,front,transmission)
    routing.require(all(a.shape==before.shape and a.ndim==3 and a.shape[2]==4
                        and np.isfinite(a).all() for a in images),'Ungültige native RGBA-Prüfbilder.')
    routing.require(output_format in FORMATS and floor_format in FORMATS,'Nicht unterstütztes natives Format.')
    q=FORMATS[output_format]
    tolerance=q+1e-6
    errors=[]
    for image,floor in ((before,floor_before),(after,floor_after)):
        expected=front+floor*(1-front[:,:,3:4])
        error=float(np.max(np.abs(image-expected)))
        routing.require(error<=tolerance,'Native Over-Komposition folgt nicht premultipliziertem RGBA: '+str(error))
        errors.append(error)
    difference=after[:,:,:3]-before[:,:,:3]
    expected=(floor_after[:,:,:3]-floor_before[:,:,:3])*(1-front[:,:,3:4])
    equation_error=float(np.max(np.abs(difference-expected)))
    routing.require(equation_error<=2*q+2e-6,'Native Zusatzkomposition unerwartet: '+str(equation_error))
    blocked=np.max(np.abs(transmission[:,:,:3]),axis=2)<=1e-6
    opaque=front[:,:,3]>=1-1e-7
    max_at=lambda mask:float(np.max(np.abs(difference[mask]))) if mask.any() else 0.0
    blocked_error,opaque_error=max_at(blocked),max_at(opaque)
    routing.require(blocked_error<=1e-6,'Zusatzlicht in vollständig gesperrtem nativen Maskenbereich.')
    routing.require(opaque_error<=1e-6,'Opakes Tabletop durch Bodenzusatz verändert.')
    routing.require(float(difference.min())>=-(FORMATS[floor_format]+2*q+2e-6),
                    'Unerwartete Abdunklung durch Bodenzusatz.')
    return dict(over_max_error=max(errors),over_quantization_bound=tolerance,
                added_composition_max_error=equation_error,
                blocked_pixels=int(blocked.sum()),max_added_rgb_in_blocked_area=blocked_error,
                opaque_tabletop_pixels=int(opaque.sum()),max_rgb_change_on_opaque_tabletop=opaque_error,
                additional_pixels=int((difference.max(axis=2)>max(.01,2*q)).sum()))


def check(resolve):
    import numpy as np
    from td_builders.motion_design import WIDTH,DEPTH,CORNER
    probe=resolve(PROBE)
    routing.require(probe is not None,'Zuerst prepare(op) ausführen.')
    info=probe.fetch(SESSION,None)
    routing.require(isinstance(info,dict),'Eigene native Prüfregistrierung fehlt.')
    validate(resolve,probe,info)
    def read(path):
        node=resolve(path)
        routing.digest(node)
        return node.numpyArray(delayed=False).copy()
    def upload(center,rotation,phase=0,valid=1):
        data=np.zeros((6,6,4),np.float32)
        data[0,0]=(*center,rotation,valid)
        data[0,1]=(center[0]+25,center[1],rotation+10,1)
        data[0,2]=(.5,.5,.6,phase)
        data[0,3]=(0,0,1.5 if phase else 0,1)
        data[0,4]=(WIDTH,DEPTH,CORNER,0)
        data[0,5]=(1,1,0,0)
        data[5,0]=(4,4,1,1)
        probe.store('data',data)
        probe.op('state').cook(force=True)
    checks=[]
    cases=[(center,rotation,0,1) for center in ((180,150),(320,350)) for rotation in (0,33,90)]
    cases += [((180,150),0,2,1),((180,150),0,0,0)]
    for center,rotation,phase,valid in cases:
        upload(center,rotation,phase,valid)
        old=read(info['outputs']['before'])
        new=read(info['outputs']['after'])
        old_floor=read(info['floor_outputs']['before'])
        new_floor=read(info['floor_outputs']['after'])
        front=read(info['front'])
        transmission=read(info['transmission'])
        output_fmt=spec(resolve(info['outputs']['before']))['format']
        floor_fmt=spec(resolve(info['floor_outputs']['before']))['format']
        result=compare_final(old,new,old_floor,new_floor,front,transmission,output_fmt,floor_fmt)
        if phase==2 or not valid:
            routing.require(np.array_equal(old,new),'Completed/ungültiger Zustand verändert native Ausgabe.')
        old_tt=read(info['table_renders']['before'])
        new_tt=read(info['table_renders']['after'])
        tt_error=float(np.max(np.abs(old_tt-new_tt)))
        routing.require(tt_error<=1e-6,'Native Tabletop-Grafik verändert.')
        result['tabletop_max_error']=tt_error
        checks.append(dict(source_center_cm=list(center),rotation_deg=rotation,phase=phase,valid=bool(valid),**result))
    for path,expected in info['copies'].items():
        routing.require(spec(resolve(path))==expected,'Kopie entspricht nicht nativem Format/Raster: '+path)
    validate(resolve,probe,info)
    upload((180,150),33)
    return dict(passed=True,projector=info['projector'],gpu_checks=checks,
                simulation_only=True,projector_connected=False,production_outputs_changed=False,
                original_calibration_changed=False,original_masks_changed=False,saved=False,
                native_formats={role:spec(resolve(path)) for role,path in info['outputs'].items()},
                compared_stage='native calibrated floor plus final tabletop Over composition',
                chair_snapshot=True,physical_validation='not performed',viewers=info['outputs'],
                next='evaluate report; remove own probe before preparing the other projector')


def cleanup(resolve):
    probe=resolve(PROBE)
    if probe is None: return dict(removed=False,already_absent=True,production_outputs_changed=False,saved=False)
    info=probe.fetch(SESSION,None)
    routing.require(isinstance(info,dict),'Eigene native Prüfregistrierung fehlt.')
    validate(resolve,probe,info)
    probe.destroy()
    return dict(removed=True,production_outputs_changed=False,saved=False)
