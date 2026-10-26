"""Temporary simulation content + mask through the existing output chain.

No physical mask geometry/calibration changes. A single test gate switches
content and the input image of the original mask together, only in AISI.
"""
import copy

from td_builders import build_motion_output_routing as routing

SESSION='motion_output_simulation_test'
SIM='/project1/comp_aisi_motion_dynamic_mask_preview'
PAGE='Motion Simulation Test'
BRIDGE='select_aisi_motion_simulation_mask'
NAMES=('simulation_mask_legacy','simulation_mask_motion','simulation_mask_switch','out_simulation_mask')
CHAIR_BRIDGE='select_aisi_motion_simulation_chairs'


def simulation_gate():
    # Reuse the complete existing AISI/calibration condition. Real-source
    # approval remains OFF; only the separate simulation request replaces it.
    return routing.GATE.replace(
        'op(%r).par.Enablemotion.eval() and op(%r).par.Sourceapproved.eval()' % (routing.PATH,routing.PATH),
        'op(%r).par.Simulationtest.eval()' % routing.PATH,1)


def content_gate():
    return routing.GATE.replace(
        'op(%r).par.Enablemotion.eval() and op(%r).par.Sourceapproved.eval()' % (routing.PATH,routing.PATH),
        '(op(%r).par.Simulationtest.eval() or (op(%r).par.Enablemotion.eval() '
        'and op(%r).par.Sourceapproved.eval()))' % (routing.PATH,routing.PATH,routing.PATH),1)


def own_snapshot(resolve,comp):
    result=routing.owned_snapshot(comp,resolve(routing.LAYOUT+routing.BRIDGE))
    bridge=resolve(routing.LAYOUT+BRIDGE)
    routing.require(bridge is not None,'Lokale Simulationsmasken-Brücke fehlt.')
    result[bridge.path]=routing.signature(bridge)
    chairs=resolve(routing.LAYOUT+CHAIR_BRIDGE)
    if chairs is not None:
        result[chairs.path]=routing.signature(chairs)
    result[comp.path]['parameters']['Simulationtest'][1]=None
    return result


def validate(resolve,comp,info):
    routing.assert_snapshot(resolve,info['expected_protected'])
    routing.require(own_snapshot(resolve,comp)==info['expected_owned'],
                    'Test-Routing lokal verändert; nichts überschrieben.')
    routing.require(all(getattr(comp.par,p).eval()==value for p,value in info['flags'].items()),
                    'Produktive Freigaben während Test verändert; vor Rückbau ursprüngliche Werte herstellen.')


def restore(resolve,comp,info):
    if any(p.name=='Simulationtest' for p in comp.pars()):
        comp.par.Simulationtest=False
    for surface,expression in info['index_expressions'].items():
        comp.op(surface+'_switch').par.index.expr=expression
    mask=resolve(routing.LAYOUT+'null_table_mask')
    mask.inputConnectors[0].connect(resolve(info['original_mask_input']))
    if 'original_chair_input' in info:
        resolve(routing.LAYOUT+'composite_floor_with_synth_chairs').inputConnectors[1].connect(
            resolve(info['original_chair_input']))
    for path in reversed(info['created']):
        node=resolve(path)
        if node is not None:
            node.destroy()
    for page in comp.customPages:
        if page.name==PAGE:
            page.destroy()
            break
    routing.assert_snapshot(resolve,info['protected_before'])
    routing.assert_owned(resolve,comp)
    comp.unstore(SESSION)


def start(resolve,symbols):
    """Prepare and GPU-check the OFF branch. Activate in a later TD frame."""
    comp=resolve(routing.PATH)
    routing.require(comp is not None and not comp.fetch(SESSION,None),'Routing fehlt oder Simulationstest läuft bereits.')
    routing.check(resolve)  # Requires both productive flags OFF; does not enable anything.
    sim,motion=resolve(SIM),resolve(routing.MOTION[:-1])
    routing.require(sim is not None and sim.fetch('motion_dynamic_simulation_only',False)
                    and motion is not None,'Geprüfte dynamische Simulation fehlt.')
    routing.require(motion.par.Useosc.eval() and not motion.par.Demo.eval()
                    and not motion.par.Usedat.eval(),'Motion verwendet nicht die isolierte OSC-Simulation.')
    routing.require(routing.ref(sim.op('motion_state').par.top)==routing.MOTION+'state',
                    'Simulationsmaske und Content lesen nicht denselben State.')
    from td_builders.build_motion_dynamic_mask_preview import mask_expression
    for row in range(5):
        geo=sim.op('mask_item_%d' % row)
        routing.require(geo is not None,'Simulationsmaskengeometrie fehlt.')
        for name in ('tx','ty','rz','sx'):
            routing.require(getattr(geo.par,name).expr==mask_expression(sim.op('mask_adapter').path,row,name),
                            'Explizite Frame-Bindung der Simulationsmaske fehlt.')
    layout=resolve(routing.LAYOUT[:-1])
    routing.require(not any(p.name=='Simulationtest' for p in comp.pars())
                    and not any(p.name==PAGE for p in comp.customPages)
                    and all(comp.op(n) is None for n in NAMES) and layout.op(BRIDGE) is None,
                    'Lokale Testknoten/-parameter existieren bereits; nichts überschrieben.')
    mask=resolve(routing.LAYOUT+'null_table_mask')
    routing.require(len(mask.inputs)==1 and mask.inputs[0].path==routing.LAYOUT+'reorder_table_mask',
                    'Originale Maskenquelle weicht ab; nichts geändert.')
    original=mask.inputs[0]
    from td_builders.build_motion_layout_chairs import PATH as chair_path, MARK as chair_mark
    chair_source=resolve(chair_path)
    with_chairs=chair_source is not None and chair_source.fetch(chair_mark,False)
    chair_composite=resolve(routing.LAYOUT+'composite_floor_with_synth_chairs')
    if with_chairs:
        routing.require(len(chair_composite.inputs)==2
                        and chair_composite.inputs[1].path==routing.LAYOUT+'select_synth_chairs_regular'
                        and layout.op(CHAIR_BRIDGE) is None
                        and all(comp.op(n) is None for n in ('simulation_chairs_legacy',
                            'simulation_chairs_motion','simulation_chairs_switch','out_simulation_chairs')),
                        'Chair-Einfügepunkt weicht ab; nichts geändert.')
    info={'protected_before':routing.snapshot(resolve),'created':[],
          'original_mask_input':original.path,
          'index_expressions':{s:comp.op(s+'_switch').par.index.expr for s in ('floor','tabletop')},
          'flags':{p:bool(getattr(comp.par,p).eval()) for p in ('Enablemotion','Sourceapproved')}}
    images={p:routing.digest(resolve(p)) for p in routing.SURFACES}
    try:
        comp.appendCustomPage(PAGE).appendToggle('Simulationtest',label='Simulation in Ausgabekette testen')[0].val=False
        def create(kind,name,parent=comp):
            node=parent.create(kind,name)
            info['created'].append(node.path)
            return node
        legacy=create(symbols['selectTOP'],NAMES[0]); legacy.par.top=original.path
        simulated=create(symbols['selectTOP'],NAMES[1])
        simulated.par.top=SIM+'/reorder_simulation_mask'
        simulated.par.outputresolution='custom'
        simulated.par.resolutionw.expr='op(%r).width' % legacy.path
        simulated.par.resolutionh.expr='op(%r).height' % legacy.path
        routing.digest(simulated)
        switch=create(symbols['switchTOP'],NAMES[2])
        switch.inputConnectors[0].connect(legacy); switch.inputConnectors[1].connect(simulated)
        switch.par.index.expr=simulation_gate()
        out=create(symbols['outTOP'],NAMES[3]); out.inputConnectors[0].connect(switch)
        bridge=create(symbols['selectTOP'],BRIDGE,layout); bridge.par.top=out.path
        if with_chairs:
            old_chairs=chair_composite.inputs[1]
            info['original_chair_input']=old_chairs.path
            legacy_chairs=create(symbols['selectTOP'],'simulation_chairs_legacy')
            legacy_chairs.par.top=old_chairs.path
            motion_chairs=create(symbols['selectTOP'],'simulation_chairs_motion')
            motion_chairs.par.top=chair_path+'/out_chairs'
            motion_chairs.par.outputresolution='custom'
            motion_chairs.par.resolutionw.expr='op(%r).width' % legacy_chairs.path
            motion_chairs.par.resolutionh.expr='op(%r).height' % legacy_chairs.path
            routing.digest(motion_chairs)
            chair_switch=create(symbols['switchTOP'],'simulation_chairs_switch')
            chair_switch.inputConnectors[0].connect(legacy_chairs)
            chair_switch.inputConnectors[1].connect(motion_chairs)
            chair_switch.par.index.expr=simulation_gate()
            chair_out=create(symbols['outTOP'],'out_simulation_chairs')
            chair_out.inputConnectors[0].connect(chair_switch)
            chair_bridge=create(symbols['selectTOP'],CHAIR_BRIDGE,layout)
            chair_bridge.par.top=chair_out.path
            chair_composite.inputConnectors[1].connect(chair_bridge)
        for surface in ('floor','tabletop'):
            comp.op(surface+'_switch').par.index.expr=content_gate()
        mask.inputConnectors[0].connect(bridge)
        info['expected_protected']=copy.deepcopy(info['protected_before'])
        info['expected_protected'][mask.path]['inputs']=[bridge.path]
        if with_chairs:
            info['expected_protected'][chair_composite.path]['inputs'][1]=chair_bridge.path
        routing.assert_snapshot(resolve,info['expected_protected'])
        for path,pixels in images.items():
            routing.require(routing.digest(resolve(path))==pixels,'Test-Verdrahtung verändert den deaktivierten Bypass: '+path)
        info['expected_owned']=own_snapshot(resolve,comp)
        clock=routing.symbol('absTime')
        info['prepared_td_frame']=float(clock.frame) if clock is not None else None
        info['prepared_signature']=(motion.fetch('motion_live_status',{}) or {}).get('signature')
        info['phase']='prepared'
        info['bypass_pixel_checks']=len(images)
        comp.store(SESSION,info)
        return {'passed':True,'simulation_test_prepared':True,'simulation_test_started':False,
                'active_in_current_mode':False,'bypass_pixel_checks':len(images),
                'prepared_td_frame':info['prepared_td_frame'],'saved':False,
                'status':'GPU preparation complete; activate in a later TD frame'}
    except Exception as error:
        try:
            restore(resolve,comp,info)
        except Exception as rollback:
            raise RuntimeError(str(error)+'; Test-Rückbau unvollständig: '+str(rollback)) from error
        raise


def activate(resolve):
    """Lightweight activation: no GPU digests before the freshness decision."""
    comp=resolve(routing.PATH)
    info=comp.fetch(SESSION,None) if comp is not None else None
    routing.require(info is not None and info.get('phase')=='prepared',
                    'Zuerst den deaktivierten Test vorbereiten.')
    clock=routing.symbol('absTime')
    frame=float(clock.frame) if clock is not None else None
    if frame is not None and frame==info['prepared_td_frame']:
        return {'passed':False,'simulation_test_started':False,'saved':False,
                'status':'waiting for a later TD frame; legacy content remains selected'}
    motion=resolve(routing.MOTION[:-1])
    # A blocking Textport cook can leave the same TD-frame CHOP cache in place.
    # Consume newly received OSC data before evaluating the source timeout.
    # This cooks existing input nodes only; no receiver setting is changed.
    raw=resolve(str(motion.par.Oscpath.eval()))
    if raw is not None:
        for source in raw.inputs:
            if str(source.type)=='oscin':
                source.cook(force=True)
        raw.cook(force=True)
    state=motion.op('state'); state.cook(force=True)
    routing.require(not state.errors(),'State-TOP fehlerhaft: '+str(state.errors()))
    live=motion.fetch('motion_live_status',{}) or {}
    if not live.get('fresh',False) or live.get('signature')==info['prepared_signature']:
        return {'passed':False,'simulation_test_started':False,'live_stream':live,'saved':False,
                'status':'waiting for fresh advancing frames after preparation; legacy remains selected'}
    validate(resolve,comp,info)  # Structural only; deliberately no GPU rendering.
    try:
        comp.par.Simulationtest=True
        indices={s:int(comp.op(s+'_switch').par.index.eval()) for s in ('floor','tabletop')}
        mask_index=int(comp.op(NAMES[2]).par.index.eval())
        routing.require(indices['floor']==indices['tabletop']==mask_index,
                        'Content und Maske nicht gemeinsam umgeschaltet.')
        chair_index=None
        if 'original_chair_input' in info:
            chair_index=int(comp.op('simulation_chairs_switch').par.index.eval())
            routing.require(chair_index==mask_index,'Content, Maske und Chairs nicht gemeinsam umgeschaltet.')
        info['phase']='active'
        comp.store(SESSION,info)
        return {'passed':True,'simulation_test_started':True,'active_in_current_mode':mask_index==1,
                'content_indices':indices,'mask_index':mask_index,'chair_index':chair_index,'live_stream':live,
                'activated_td_frame':frame,'real_source_approved':False,'saved':False,
                'active_output_pixels_verified':False,'physical_validation':'not performed',
                'status':'activated; run the separate output check after TD resumes'}
    except Exception:
        comp.par.Simulationtest=False
        raise


def check(resolve):
    import numpy as np
    comp=resolve(routing.PATH)
    info=comp.fetch(SESSION,None) if comp is not None else None
    routing.require(info is not None,'Kein registrierter Simulationstest.')
    validate(resolve,comp,info)
    indices={s:int(comp.op(s+'_switch').par.index.eval()) for s in ('floor','tabletop')}
    mask_index=int(comp.op(NAMES[2]).par.index.eval())
    routing.require(indices['floor']==indices['tabletop']==mask_index,
                    'Content und Simulationsmaske sind nicht gemeinsam umgeschaltet.')
    chair_index=None
    if 'original_chair_input' in info:
        chair_index=int(comp.op('simulation_chairs_switch').par.index.eval())
        routing.require(chair_index==mask_index,'Tischziele, Maske und Chairs nicht gemeinsam umgeschaltet.')
    for path in routing.SURFACES:
        routing.digest(resolve(path))
    checks=['Nur Maskenbild-Eingang zusätzlich umgeschaltet; Originalmaskenoperator erhalten',
            'Kalibrierung, Chair-Komposition und Projektorparameter unverändert',
            'Content und Maskenquelle verwenden denselben AISI-/Kalibrierungsschalter',
            'Drei zentrale Ausgabeschalter fehlerfrei']
    if chair_index is not None:
        checks[0]='Nur die vorgesehenen Masken-/Chair-Bildeingänge zusätzlich umgeschaltet; Originalmaske erhalten'
        checks[1]='Kalibrierung, Chair-Composite-Operation und Projektorparameter unverändert'
    pixel_error=None
    if chair_index is not None:
        routing.require(routing.digest(resolve(routing.LAYOUT+CHAIR_BRIDGE))==routing.digest(
            comp.op('simulation_chairs_motion' if chair_index==1 else 'simulation_chairs_legacy')),
            'Chair-Einfügepunkt entspricht nicht dem gewählten Zweig.')
        checks.append('Chair-Quelle folgt derselben Simulation-/AISI-/Kalibrierungsumschaltung')
    if mask_index==1:
        routing.require(routing.digest(resolve(routing.LAYOUT+'null_table_mask'))
                        ==routing.digest(comp.op(NAMES[1])),'Aktive Maske entspricht nicht der Simulationsmaske.')
        a_node=resolve(routing.LAYOUT+'null_tabletop_masked')
        b_node=resolve(SIM+'/out_tabletop')
        routing.digest(a_node); routing.digest(b_node)
        a=a_node.numpyArray(delayed=False).copy(); b=b_node.numpyArray(delayed=False).copy()
        routing.require(a.shape==b.shape,'Auflösungen des maskierten Tabletop-Vergleichs weichen ab.')
        pixel_error=float(np.max(np.abs(a-b)))
        routing.require(pixel_error<=2/255+1e-5,'Maskiertes Tabletop weicht vom geprüften Simulationsbild ab: '+str(pixel_error))
        checks.extend(['Aktiver Maskeneingang pixelgleich zur dynamischen Simulationsmaske',
                       'Tabletop durch Originalmaske entspricht dynamischem Prüfzweig'])
    return {'passed':True,'checks':checks,'simulation_requested':bool(comp.par.Simulationtest.eval()),
            'active_in_current_mode':mask_index==1,'content_indices':indices,'mask_index':mask_index,'chair_index':chair_index,
            'chair_stream':(resolve('/project1/comp_aisi_motion_layout_chairs').fetch('chair_live_status',None)
                            if chair_index is not None else None),
            'tabletop_max_pixel_error':pixel_error,'real_source_approved':False,
            'viewers':{'floor':routing.OUTPUT+'switch_floor','tabletop':routing.OUTPUT+'switch_tabletop'},
            'saved':False,'physical_validation':'not performed'}


def verify(resolve):
    """Heavy verification is separate from activation; revert a valid test on failure."""
    try:
        return check(resolve)
    except Exception as error:
        comp=resolve(routing.PATH)
        info=comp.fetch(SESSION,None) if comp is not None else None
        if info is None:
            raise
        validate(resolve,comp,info)  # Never overwrite intervening local edits.
        restore(resolve,comp,info)
        return {'passed':False,'failure':str(error),'simulation_test_stopped':True,
                'disabled_production_routing_restored':routing.check(resolve)['passed'],'saved':False}


def stop(resolve):
    comp=resolve(routing.PATH)
    info=comp.fetch(SESSION,None) if comp is not None else None
    if info is None:
        report=routing.check(resolve)
        return {'simulation_test_stopped':False,'status':'no registered simulation test; nothing changed',
                'disabled_production_routing_verified':report['passed'],'saved':False}
    validate(resolve,comp,info)
    restore(resolve,comp,info)
    report=routing.check(resolve)
    return {'simulation_test_stopped':True,'original_mask_source_restored':True,
            'disabled_production_routing_restored':report['passed'],
            'temporary_test_nodes_removed':True,'saved':False}
