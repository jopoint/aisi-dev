"""Isolated synthetic floor-target experiment; never installs or routes output."""
import hashlib

from td_builders import update_motion_feedback_brightness as transaction
from td_builders import update_motion_redisplay as redisplay
from td_builders import update_motion_alignment_guides as alignment
from td_builders import build_motion_output_routing as routing
from td_builders.update_motion_target_divisions import check_pattern

PROBE='/project1/comp_aisi_motion_under_table_probe'
SESSION='motion_under_table_probe'
UNUSED_BACKUP='motion_under_table_probe_no_install'
DECLARATION='    vec4 floorColor=vec4(0), tableColor=vec4(0);'
TARGET='            floorColor=over(f*(released*pulse.w*redisplay),floorColor);'
FINAL='    floorColor=over(white(waveAlpha),floorColor)*(1.0-occupied);'
PAIRS=(
    (DECLARATION,DECLARATION+'\n    vec4 floorTargets=vec4(0);'),
    (TARGET,TARGET+'''\n            // Only target fill bypasses the early vertical footprint exclusion.
            floorTargets=over(white(targetFill)*(released*pulse.w*redisplay),floorTargets);'''),
    (FINAL,FINAL+'''\n    // Retain masked arrows/wave; restore only the target portion inside footprints.
    floorColor+=floorTargets*occupied;'''),
)
SURFACE='    else if(uSurface.x<1.5) fragColor=TDOutputSwizzle(tableColor);'
DIAGNOSTIC='    else if(uSurface.x<1.5) fragColor=TDOutputSwizzle(vec4(occupied,floorTargets.a,floorTargets.a*occupied,1));'


def patch_shader(text):
    routing.require(text.count('float targetLines=0.0; // Accepted default: solid target surface without divider.')==1,
                    'Zielfläche lokal abweichend; ausschließlich soliden Standard prüfen.')
    return redisplay._patch(text,PAIRS)


def signature(node):
    result=routing.signature(node)
    if getattr(node,'isDAT',False) and str(node.type) in ('text','table'):
        result['text_sha256']=hashlib.sha256(node.text.encode('utf-8')).hexdigest()
    return result


def projection_snapshot(resolve):
    paths=[routing.OUTPUT+'comp_projector_'+str(i) for i in (0,1)]
    paths += [routing.OUTPUT+name for name in (
        'switch_floor','switch_tabletop','switch_table_mask','layer_floor_switch',
        'layer_tabletop_switch','rotate_180_floor','rotate_180_tabletop','rotate_180_table_mask',
        'out_projector_0','out_projector_1')]
    result={}
    for path in paths:
        node=resolve(path)
        routing.require(node is not None,'Bestätigter Ausgabeknoten fehlt: '+path)
        for child in [node]+(list(node.findChildren()) if node.isCOMP else []):
            result[child.path]=signature(child)
    return result


def own_snapshot(probe):
    return {n.path:signature(n) for n in [probe]+list(probe.findChildren())}


def assert_unchanged(resolve,probe,info):
    routing.require(own_snapshot(probe)==info['owned'],'Prüfzweig lokal verändert; nichts überschrieben.')
    routing.require(projection_snapshot(resolve)==info['projection'],
                    'Projektor-/Masken-/Kalibrierungsgraph seit Vorbereitung verändert.')
    comp=resolve(routing.MOTION[:-1])
    routing.require(comp.op('motion_pixel').text==info['old'], 'Produktiver Shader seit Vorbereitung verändert.')
    routing.require(comp.fetch('motion_engine',None) is info['engine']
                    and comp.fetch('motion_osc_reader',None) is info['reader']
                    and getattr(info['engine'],'revision',None)==info['revision'],
                    'Engine/Reader/Revision seit Vorbereitung verändert.')


def prepare(resolve):
    comp=transaction.shadow._validate(resolve)
    projection=projection_snapshot(resolve)
    engine,reader=comp.fetch('motion_engine',None),comp.fetch('motion_osc_reader',None)
    revision=getattr(engine,'revision',None)
    result=transaction.prepare(resolve,probe_path=PROBE,session=SESSION,
                               backup=UNUSED_BACKUP,patcher=patch_shader)
    probe=resolve(PROBE)
    try:
        info=dict(probe.fetch(SESSION))
        routing.require(info['new'].count(SURFACE)==1,'Surface-Ausgabe lokal abweichend.')
        info['mask']=info['new'].replace(SURFACE,DIAGNOSTIC,1)
        probe.op('mask_pixel').text=info['mask']
        info.update(projection=projection,engine=engine,reader=reader,revision=revision)
        info['owned']=own_snapshot(probe)
        probe.store(SESSION,info)
        assert_unchanged(resolve,probe,info)
    except Exception:
        probe.destroy()
        raise
    result.update(simulation_only=True,projector_connected=False,production_shader_changed=False,
                  calibration_changed=False,masks_changed=False,
                  next='run check(op) in a separate Textport entry; no installation exists')
    return result


def gpu_check(probe):
    import numpy as np
    from td_builders.motion_design import WIDTH,DEPTH,CORNER
    checks=[]
    table_errors=[]
    def render(rotation=0,reveal=4,phase=0,age=0,valid=1,active=1,
               visibility=1,opacity=1,count=1,target_x=215):
        data=np.zeros((6,6,4),np.float32)
        for i in range(count):
            # Other physical tables may cover this table's target, too.
            sx,sy=(180,250) if i==0 else (100+i*65,210+(i%2)*70)
            data[i,0]=(sx,sy,rotation,valid)
            data[i,1]=(target_x if i==0 else sx+25,sy,rotation+10,active)
            data[i,2]=(.5,.5,.6,phase)
            data[i,3]=(0,0,age,opacity)
            data[i,4]=(WIDTH,DEPTH,CORNER,0)
            data[i,5]=(visibility,1,0,0)
        data[5,0]=(4,reveal,1,count)
        probe.store('data',data)
        probe.op('state').cook(force=True)
        images={}
        for name in ('old_floor','new_floor','old_tabletop','new_tabletop','mask_tabletop'):
            node=probe.op(name)
            routing.digest(node)
            images[name]=node.numpyArray(delayed=False).copy()
            routing.require(np.isfinite(images[name]).all(),'Nichtendliche GPU-Ausgabe.')
        table_errors.append(alignment.check_floor(images['old_tabletop'],images['new_tabletop'])['max_float_error'])
        old,new=images['old_floor'],images['new_floor']
        diagnostic=images['mask_tabletop']
        extra=diagnostic[:,:,2]
        expected=old+extra[:,:,None]
        proof=check_pattern(new,expected)
        outside=extra<=0
        routing.require(outside.any(),'Prüffläche außerhalb Zusatzanteil fehlt.')
        check_pattern(new[outside],old[outside])
        routing.require(float(new.min())>=-1e-6 and float(new.max())<=1.000001,
                        'Premultiplizierte Ausgabe außerhalb 0..1.')
        return images,dict(added_target_pixels=int((extra>.01).sum()),**proof)
    for rotation in (0,33,90):
        for count,reveal in ((1,4),(5,4),(1,1.5)):
            images,proof=render(rotation=rotation,count=count,reveal=reveal)
            routing.require(proof['added_target_pixels']>100,'Kein Zielanteil im Tisch-Footprint.')
            checks.append(dict(case='only_target_restored_inside_footprints',rotation_deg=rotation,
                               tables=count,reveal_wave=reveal<3,**proof))
    for options in (dict(valid=0),dict(active=0),dict(phase=2,age=1.5),dict(opacity=0),dict(target_x=400)):
        images,proof=render(**options)
        routing.require(proof['added_target_pixels']==0,'Unerwartete zusätzliche Bodengrafik.')
        check_pattern(images['new_floor'],images['old_floor'])
    checks.append(dict(case='invalid_inactive_completed_faded_and_nonoverlap_unchanged',passed=True))
    full,_=render()
    half,_=render(visibility=.5)
    check_pattern(half['new_floor'],full['new_floor']*.5)
    render(phase=1,age=.3,opacity=.7)
    checks.append(dict(case='success_and_redisplay_preserved',passed=True))
    checks.append(dict(case='tabletop_precision',rgba8_pixel_equal=True,max_float_error=max(table_errors)))
    # Leave a useful five-table synthetic example in the disconnected viewers.
    render(rotation=33,count=5)
    return checks


def check(resolve):
    probe=resolve(PROBE)
    routing.require(probe is not None,'Zuerst prepare(op) aufrufen.')
    info=probe.fetch(SESSION,None)
    routing.require(isinstance(info,dict),'Eigene Prüfregistrierung fehlt.')
    assert_unchanged(resolve,probe,info)
    checks=gpu_check(probe)
    assert_unchanged(resolve,probe,info)
    return dict(passed=True,gpu_checks=checks,simulation_only=True,projector_connected=False,
                production_shader_changed=False,calibration_changed=False,masks_changed=False,
                saved=False,physical_validation='not performed',
                viewers=dict(before=PROBE+'/old_floor',after=PROBE+'/new_floor'),
                next='inspect isolated comparison; calibrated projector-space proof still pending')


def cleanup(resolve):
    probe=resolve(PROBE)
    routing.require(probe is not None,'Eigener Prüfzweig fehlt.')
    info=probe.fetch(SESSION,None)
    routing.require(isinstance(info,dict),'Eigene Prüfregistrierung fehlt.')
    assert_unchanged(resolve,probe,info)
    routing.require(all(not n.outputs for n in probe.findChildren() if getattr(n,'isTOP',False)
                        and n.name in ('old_floor','new_floor','old_tabletop','new_tabletop','mask_tabletop')),
                    'Prüfausgabe extern verdrahtet; nicht entfernen.')
    probe.destroy()
    return dict(removed=True,production_outputs_changed=False,saved=False)
