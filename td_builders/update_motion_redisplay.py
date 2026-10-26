"""Transactional runtime/shader update for soft guidance reappearance."""
import hashlib

from td_builders import build_motion_output_routing as routing
from td_builders import update_motion_alignment_guides as alignment
from td_builders import update_motion_feedback_brightness as transaction
from td_builders import motion_redisplay

PROBE='/project1/comp_aisi_motion_redisplay_check'
SESSION='motion_redisplay_probe'
BACKUP='motion_redisplay_backup'
RUNTIME_LOOP='    for index, (identity, source, target, valid, active) in enumerate(rows):'
NEW_LOOP='''    from td_builders.motion_redisplay import begin_frame, visibility
    redisplay_events = begin_frame(owner, engine)
'''+RUNTIME_LOOP
RUNTIME_UPDATE='        state = engine.update(identity, source, target, now, valid)'
NEW_UPDATE='''        previous_phase = getattr(engine.tables.get(identity), 'phase', None)
'''+RUNTIME_UPDATE
RUNTIME_UPLOAD='        data[index, 4] = (WIDTH, DEPTH, CORNER, 0)'
NEW_UPLOAD=RUNTIME_UPLOAD+'''
        data[index, 5] = (visibility(redisplay_events, identity, previous_phase, state.phase, now, valid), 1, 0, 0)'''
SHADER_STATE='        vec4 pulse=datum(3,i), shape=datum(4,i);'
NEW_STATE=SHADER_STATE+'''
        vec4 redisplayState=datum(5,i);
        float redisplay=redisplayState.y>.5?redisplayState.x:1.0;'''
SHADER_FLOOR='            floorColor=over(f*(released*pulse.w),floorColor);'
NEW_FLOOR='            floorColor=over(f*(released*pulse.w*redisplay),floorColor);'
SHADER_TABLE='        tableColor=over(layer,tableColor);'
NEW_TABLE='''        layer*=redisplay;
'''+SHADER_TABLE


def _patch(text, pairs):
    if all(text.count(new)==1 and text.count(old)==new.count(old) for old,new in pairs):
        return text
    routing.require(all(text.count(old)==1 and new not in text for old,new in pairs),
                    'Wiedereinblend-Code lokal abweichend; nichts überschrieben.')
    for old,new in pairs: text=text.replace(old,new,1)
    return text


def patch_runtime(text):
    return _patch(text, ((RUNTIME_LOOP,NEW_LOOP),(RUNTIME_UPDATE,NEW_UPDATE),(RUNTIME_UPLOAD,NEW_UPLOAD)))


def patch_shader(text):
    return _patch(text, ((SHADER_STATE,NEW_STATE),(SHADER_FLOOR,NEW_FLOOR),(SHADER_TABLE,NEW_TABLE)))


def prepare(resolve):
    comp=transaction.shadow._validate(resolve)
    runtime=comp.op('motion_runtime')
    routing.require(runtime is not None,'Aktiver Runtime-DAT fehlt.')
    routing.require(comp.fetch(motion_redisplay.KEY,None) is None,'Lokaler Wiedereinblend-Speicher bereits vorhanden.')
    old=runtime.text
    new=patch_runtime(old)
    routing.require(old!=new,'Runtime-Wiedereinblendung bereits installiert.')
    compile(new,runtime.path,'exec')
    result=transaction.prepare(resolve,probe_path=PROBE,session=SESSION,backup=BACKUP,patcher=patch_shader)
    probe=resolve(PROBE)
    info=dict(probe.fetch(SESSION))
    info.update(runtime_old=old,runtime_new=new)
    probe.store(SESSION,info)
    result.update(duration_seconds=motion_redisplay.DURATION,runtime_changed=False,
                  transition='completed -> guidance',state_channel='column 5, version flag y=1')
    return result


def gpu_check(probe):
    import numpy as np
    from td_builders.motion_design import WIDTH,DEPTH,CORNER
    checks=[]
    def render(alpha,version=1):
        data=np.zeros((6,6,4),np.float32)
        data[0,0]=(250,250,0,1)
        data[0,1]=(370,250,33,1)
        data[0,2]=(0,1,.5,0)
        data[0,3]=(0,0,0,1)
        data[0,4]=(WIDTH,DEPTH,CORNER,0)
        data[0,5]=(alpha,version,0,0)
        data[5,0]=(4,4,1,1)
        probe.store('data',data)
        probe.op('state').cook(force=True)
        images={}
        for name in ('old_floor','new_floor','old_tabletop','new_tabletop'):
            node=probe.op(name)
            routing.digest(node)
            images[name]=node.numpyArray(delayed=False).copy()
            routing.require(np.isfinite(images[name]).all(),'Nichtendliche GPU-Ausgabe.')
        return images
    baseline=render(1)
    for surface in ('floor','tabletop'):
        alignment.check_floor(baseline['old_'+surface],baseline['new_'+surface])
    for alpha in (0,.15625,.5,.84375,1):
        images=render(alpha)
        for surface in ('floor','tabletop'):
            expected=baseline['new_'+surface]*alpha
            error=float(np.max(np.abs(images['new_'+surface]-expected)))
            routing.require(error<=1e-6,'Wiedereinblendung nicht proportional: '+surface)
            routing.require(float(np.max(np.abs(baseline['new_'+surface])))>.1,'Leeres GPU-Prüfbild.')
        checks.append(dict(visibility=alpha,floor_and_tabletop_premultiplied_fade=True))
    legacy=render(0,version=0)
    for surface in ('floor','tabletop'):
        routing.require(np.array_equal(legacy['new_'+surface],baseline['new_'+surface]),
                        'Legacy-State ohne Fade-Marker verändert.')
    checks.append(dict(case='legacy_state_without_marker_unchanged',passed=True))
    return checks


def install(resolve):
    comp=transaction.shadow._validate(resolve)
    probe=resolve(PROBE)
    routing.require(probe is not None,'Zuerst prepare aufrufen.')
    info=probe.fetch(SESSION,None)
    routing.require(isinstance(info,dict),'Eigene Prüfregistrierung fehlt.')
    pixel,runtime=comp.op('motion_pixel'),comp.op('motion_runtime')
    routing.require(pixel.text==info['old'] and runtime.text==info['runtime_old']
                    and comp.fetch(BACKUP,None) is None,'Shader/Runtime seit Vorbereitung verändert.')
    for version in ('old','new','mask'):
        routing.require(probe.op(version+'_pixel').text==info[version],'Prüfshader lokal verändert.')
    checks=gpu_check(probe)
    engine,reader=comp.fetch('motion_engine',None),comp.fetch('motion_osc_reader',None)
    revision=getattr(engine,'revision',None)
    try:
        runtime.text=info['runtime_new']
        routing.require(callable(runtime.module.td_tick),'Aktualisierte Runtime kompiliert nicht.')
        pixel.text=info['new']
        comp.op('state').cook(force=True)
        routing.require(not comp.op('state').errors(),'Aktualisierter State meldet Fehler.')
        for name in ('render_floor','render_tabletop','render_preview'): routing.digest(comp.op(name))
        transaction.shadow._validate(resolve)
        routing.require(comp.fetch('motion_engine',None) is engine and comp.fetch('motion_osc_reader',None) is reader
                        and getattr(engine,'revision',None)==revision,'Engine/Reader/Revision verändert.')
    except Exception:
        runtime.text=info['runtime_old']
        pixel.text=info['old']
        comp.unstore(motion_redisplay.KEY)
        raise
    comp.store(BACKUP,dict(old=info['old'],runtime_old=info['runtime_old'],
                          new_sha256=hashlib.sha256(info['new'].encode()).hexdigest(),
                          runtime_new_sha256=hashlib.sha256(info['runtime_new'].encode()).hexdigest()))
    probe.destroy()
    return dict(passed=True,gpu_checks=checks,duration_seconds=motion_redisplay.DURATION,
                engine_reset=False,targets_changed=False,masks_changed=False,saved=False,
                next='separate live_output.verify and physical completed-to-guidance test')


def rollback(resolve):
    comp=transaction.shadow._validate(resolve)
    info=comp.fetch(BACKUP,None)
    routing.require(isinstance(info,dict),'Eigene Wiedereinblend-Sicherung fehlt.')
    pixel,runtime=comp.op('motion_pixel'),comp.op('motion_runtime')
    routing.require(hashlib.sha256(pixel.text.encode()).hexdigest()==info['new_sha256']
                    and hashlib.sha256(runtime.text.encode()).hexdigest()==info['runtime_new_sha256'],
                    'Shader/Runtime nach Installation verändert; nichts überschrieben.')
    pixel.text=info['old']
    runtime.text=info['runtime_old']
    comp.unstore(BACKUP)
    comp.unstore(motion_redisplay.KEY)
    return dict(restored=True,saved=False)
