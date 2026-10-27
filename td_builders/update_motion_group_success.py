"""Guarded runtime/shader trial for persistent checks and a common finish."""
import hashlib

from td_builders import build_motion_output_routing as routing
from td_builders import update_motion_feedback_brightness as transaction
from td_builders import update_motion_alignment_guides as alignment
from td_builders import update_motion_success_pop_out as previous
from td_builders import motion_group_success as group

PROBE = '/project1/comp_aisi_motion_group_success_check'
SESSION = 'motion_group_success_probe'
BACKUP = 'motion_group_success_backup'
RETURN = '    return data'
STATE = '        data[index, 5] = (visibility(redisplay_events, identity, previous_phase, state.phase, now, valid), 1, 0, 0)'
NEW_RETURN = '''    from td_builders.motion_group_success import apply as apply_group_success
    apply_group_success(owner, engine, rows, data, now)
    return data'''
OVERLAY = '''        // Per-layout completion checks include captured, initially stationary tables.
        if(redisplayState.w>.5 || (target.w>.5 && state.w>.5 && pulse.z<1.32)) {
            float checkScale=redisplayState.w>.5 ? redisplayState.z
                :(pulse.z<=1.0?successPop(pulse.z):successPop(max(0.0,1.32-pulse.z)));
            if(checkScale>.0001)
                layer=over(white(successCheck((p-source.xy)/checkScale,target.xyz)
                    *sourceMask*released),layer);
        }
'''


def patch_runtime(text):
    routing.require(text.count(RETURN) == 1 and 'motion_group_success' not in text
                    and 'motion_visual_reveal' in text and text.count(STATE) == 1,
                    'Runtime weicht vom geprüften Reveal-/Wiedereinblendstand ab.')
    result = text.replace(RETURN, NEW_RETURN, 1)
    compile(result, 'motion_runtime', 'exec')
    return result


def patch_shader(text):
    routing.require(text.count(previous.OVERLAY) == 1 and text.count('vec4 redisplayState=datum(5,i);') == 1,
                    'Haken-/State-Shader lokal abweichend; nichts überschrieben.')
    return text.replace(previous.OVERLAY, OVERLAY, 1)


def prepare(resolve):
    comp = transaction.shadow._validate(resolve)
    runtime = comp.op('motion_runtime')
    old = runtime.text
    new = patch_runtime(old)
    routing.require(comp.fetch(group.KEY, None) is None, 'Gemeinsamer Hakenstatus bereits vorhanden.')
    result = transaction.prepare(resolve, probe_path=PROBE, session=SESSION, backup=BACKUP, patcher=patch_shader)
    probe = resolve(PROBE)
    info = dict(probe.fetch(SESSION))
    info.update(runtime_old=old, runtime_new=new)
    probe.store(SESSION, info)
    result.update(runtime_changed=False, stationary_tables_included=True,
                  common_exit='1 second after last arrival, reverse pop over 0.32 seconds',
                  clocks_start='after complete approved reveal')
    return result


def gpu_check(probe):
    import numpy as np
    from td_builders.motion_design import WIDTH, DEPTH, CORNER
    checks = []
    floor_errors = []
    for scale, marker, active, valid in ((1,1,1,1), (1,1,0,1), (.7,1,0,1),
                                          (0,1,1,1), (1,1,1,0), (0,0,1,1)):
        data = np.zeros((6,6,4), np.float32)
        for i, center in enumerate(((150,180), (350,320))):
            data[i,0] = (*center, 33*i, valid)
            data[i,1] = (*center, 33*i, active)
            data[i,2] = (0,0,0,2)
            data[i,3] = (0,0,10,0)
            data[i,4] = (WIDTH,DEPTH,CORNER,0)
            data[i,5] = (1,1,scale,marker)
        data[5,0] = (20,10,1,2)
        data[5,1] = (10,1,1,0)
        probe.store('data', data)
        probe.op('state').cook(force=True)
        images = {}
        for name in ('old_floor','new_floor','old_tabletop','new_tabletop'):
            node = probe.op(name)
            routing.digest(node)
            images[name] = node.numpyArray(delayed=False).copy()
            routing.require(np.isfinite(images[name]).all(), 'Nichtendliche Haken-Ausgabe.')
        floor_errors.append(alignment.check_floor(images['old_floor'], images['new_floor'])['max_float_error'])
        image = images['new_tabletop']
        if scale > 0 and marker and valid:
            routing.require(float(image[:,:,3].sum()) > 100, 'Persistente/stationäre Haken fehlen.')
            routing.require(float(np.max(np.abs(image-image[:,:,3,None]))) < 1e-6,
                            'Haken nicht weiß/premultipliziert.')
        else:
            routing.require(not image.any(), 'Ausgeblendete/ungültige Haken sichtbar.')
        checks.append(dict(scale=scale, marker=marker, active=active, valid=valid, passed=True))
    checks.append(dict(case='floor_unchanged', rgba8_pixel_equal=True, max_float_error=max(floor_errors)))
    return checks


def install(resolve):
    comp = transaction.shadow._validate(resolve)
    probe = resolve(PROBE)
    routing.require(probe is not None, 'Zuerst prepare aufrufen.')
    info = probe.fetch(SESSION, None)
    routing.require(isinstance(info, dict), 'Eigene Prüfregistrierung fehlt.')
    pixel, runtime = comp.op('motion_pixel'), comp.op('motion_runtime')
    routing.require(pixel.text == info['old'] and runtime.text == info['runtime_old']
                    and comp.fetch(BACKUP, None) is None and comp.fetch(group.KEY, None) is None,
                    'Shader/Runtime seit Vorbereitung verändert oder bereits installiert.')
    for name in ('old','new','mask'):
        routing.require(probe.op(name+'_pixel').text == info[name], 'Prüfshader lokal verändert.')
    checks = gpu_check(probe)
    engine, reader = comp.fetch('motion_engine', None), comp.fetch('motion_osc_reader', None)
    routing.require(engine is not None, 'Aktive Engine fehlt.')
    revision, started = engine.revision, engine.started
    try:
        runtime.text = info['runtime_new']
        routing.require(callable(runtime.module.td_tick), 'Runtime kompiliert nicht.')
        pixel.text = info['new']
        comp.op('state').cook(force=True)
        routing.require(not comp.op('state').errors(), 'State meldet Fehler.')
        for name in ('render_floor','render_tabletop','render_preview'):
            routing.digest(comp.op(name))
        transaction.shadow._validate(resolve)
        routing.require(comp.fetch('motion_engine', None) is engine and comp.fetch('motion_osc_reader', None) is reader
                        and engine.revision == revision and engine.started == started,
                        'Engine/Reader/Revision/Zustandsstart verändert.')
    except Exception:
        runtime.text, pixel.text = info['runtime_old'], info['old']
        comp.unstore(group.KEY)
        raise
    comp.store(BACKUP, dict(runtime_old=info['runtime_old'], shader_old=info['old'],
                           runtime_hash=hashlib.sha256(info['runtime_new'].encode()).hexdigest(),
                           shader_hash=hashlib.sha256(info['new'].encode()).hexdigest()))
    probe.destroy()
    return dict(passed=True, gpu_checks=checks, engine_reset=False, targets_changed=False,
                chairs_changed=False, revision_changed=False, masks_changed=False, saved=False,
                next='separate live_output.verify; test stationary and sequential arrivals')


def rollback(resolve):
    comp = transaction.shadow._validate(resolve)
    info = comp.fetch(BACKUP, None)
    routing.require(isinstance(info, dict), 'Eigene Sicherung fehlt.')
    runtime, pixel = comp.op('motion_runtime'), comp.op('motion_pixel')
    routing.require(hashlib.sha256(runtime.text.encode()).hexdigest() == info['runtime_hash']
                    and hashlib.sha256(pixel.text.encode()).hexdigest() == info['shader_hash'],
                    'Runtime/Shader später verändert; nichts überschrieben.')
    runtime.text, pixel.text = info['runtime_old'], info['shader_old']
    comp.unstore(group.KEY)
    comp.unstore(BACKUP)
    return dict(restored=True, engine_reset=False, saved=False)
