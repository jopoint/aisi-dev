"""Transactional display-clock patch, based on the actual open runtime/shader DATs."""
import hashlib
import time

from td_builders import build_motion_output_routing as routing
from td_builders import update_motion_feedback_brightness as transaction
from td_builders import motion_visual_reveal as visual

PROBE = '/project1/comp_aisi_motion_visual_reveal_check'
SESSION = 'motion_visual_reveal_probe'
BACKUP = 'motion_visual_reveal_backup'
RUNTIME = '    data[5, 0] = (now - engine.started, age, int(enabled), len(rows))'
NEW_RUNTIME = '''    from td_builders.motion_visual_reveal import display_state
    visual_age, reveal_ready, reveal_managed = display_state(owner, engine, now, age, enabled)
    data[5, 0] = (now - engine.started, age, int(enabled), len(rows))
    data[5, 1] = (visual_age, int(reveal_ready), int(reveal_managed), 0)'''
SHADER = '    vec4 clock=datum(0,5);'
NEW_SHADER = SHADER + '''
    vec4 visualReveal=datum(1,5);
    if(visualReveal.z>.5) {
        if(visualReveal.y<.5) {
            fragColor=TDOutputSwizzle(uSurface.x>1.5?vec4(.188,.282,.247,1):vec4(0));
            return;
        }
        clock.y=visualReveal.x;
    }'''


def patch_runtime(text):
    routing.require(text.count(RUNTIME) == 1 and 'motion_visual_reveal' not in text,
                    'Runtime-Uhr lokal abweichend oder Patch bereits installiert.')
    result = text.replace(RUNTIME, NEW_RUNTIME, 1)
    compile(result, 'motion_runtime', 'exec')
    return result


def patch_shader(text):
    routing.require(text.count(SHADER) == 1 and 'visualReveal' not in text and
                    text.count('reveal=clamp(clock.y/3.0,0.0,1.0)') == 1,
                    'Reveal-Shader lokal abweichend oder bereits installiert.')
    return text.replace(SHADER, NEW_SHADER, 1)


def prepare(resolve):
    comp = transaction.shadow._validate(resolve)
    runtime = comp.op('motion_runtime')
    auto = resolve(visual.AUTO)
    routing.require(auto is not None and auto.par.Enabled.eval(), 'Installierte aktivierte TD-Automatik erforderlich.')
    routing.require(runtime is not None and comp.fetch(visual.KEY, None) is None, 'Runtime fehlt oder visuelle Uhr bereits vorhanden.')
    old, new = runtime.text, patch_runtime(runtime.text)
    result = transaction.prepare(resolve, probe_path=PROBE, session=SESSION, backup=BACKUP, patcher=patch_shader)
    probe = resolve(PROBE)
    info = dict(probe.fetch(SESSION))
    info.update(runtime_old=old, runtime_new=new)
    probe.store(SESSION, info)
    result.update(runtime_changed=False, reveal_duration_seconds=3,
                  reveal_start='after full automatic output proof', engine_reset=False)
    return result


def gpu_check(probe):
    import numpy as np
    from td_builders.motion_design import WIDTH, DEPTH, CORNER
    checks = []
    for age in (0, .5, 1.5, 2.9, 3.1):
        for ready, managed in ((False, True), (True, True), (False, False)):
            data = np.zeros((6,6,4), np.float32)
            data[0,0] = (180,180,0,1)
            data[0,1] = (320,320,33,1)
            data[0,2] = (1,1,.5,0)
            data[0,3] = (0,0,0,1)
            data[0,4] = (WIDTH,DEPTH,CORNER,0)
            data[0,5] = (1,1,0,0)
            data[5,0] = (10,age,1,1)
            data[5,1] = (age,int(ready),int(managed),0)
            probe.store('data', data)
            probe.op('state').cook(force=True)
            nonempty = False
            for surface in ('floor','tabletop'):
                images = []
                for version in ('old','new'):
                    node = probe.op(version+'_'+surface)
                    routing.digest(node)
                    images.append(node.numpyArray(delayed=False).copy())
                old, new = images
                routing.require(np.isfinite(new).all(), 'Reveal-Ausgabe nicht endlich.')
                if managed and not ready:
                    routing.require(np.count_nonzero(new) == 0, 'Reveal während Prüfung sichtbar: '+surface)
                else:
                    from td_builders.update_motion_alignment_guides import check_floor
                    check_floor(old,new)  # Established float32-epsilon + identical RGBA8 criterion.
                nonempty = nonempty or bool(np.max(old) > .1)
            routing.require(age == 0 or nonempty, 'Leerer Reveal-Referenzfall.')
            checks.append(dict(age_seconds=age, ready=ready, managed=managed,
                               hidden_until_approved=bool(managed and not ready),
                               approved_or_legacy_rgba8_equal=bool(ready or not managed)))
    return checks


def install(resolve):
    comp = transaction.shadow._validate(resolve)
    probe = resolve(PROBE)
    routing.require(probe is not None, 'Zuerst prepare aufrufen.')
    info = probe.fetch(SESSION, None)
    routing.require(isinstance(info, dict), 'Eigene Prüfregistrierung fehlt.')
    pixel, runtime = comp.op('motion_pixel'), comp.op('motion_runtime')
    routing.require(pixel.text == info['old'] and runtime.text == info['runtime_old']
                    and comp.fetch(BACKUP,None) is None and comp.fetch(visual.KEY,None) is None,
                    'Runtime/Shader seit Vorbereitung verändert.')
    for name in ('old','new','mask'):
        routing.require(probe.op(name+'_pixel').text == info[name], 'Prüfshader lokal verändert.')
    checks = gpu_check(probe)
    engine, reader = comp.fetch('motion_engine',None), comp.fetch('motion_osc_reader',None)
    routing.require(engine is not None, 'Aktive Motion-Engine fehlt.')
    revision, started = engine.revision, engine.started
    try:
        # Applying the patch is not a layout event: do not replay the current layout.
        comp.store(visual.KEY, dict(revision=revision, started=time.monotonic()-3.1))
        comp.storeStartupValue(visual.KEY, None)
        runtime.text = info['runtime_new']
        routing.require(callable(runtime.module.td_tick), 'Runtime kompiliert nicht.')
        pixel.text = info['new']
        comp.op('state').cook(force=True)
        routing.require(not comp.op('state').errors(), 'State meldet Fehler.')
        for name in ('render_floor','render_tabletop','render_preview'):
            routing.digest(comp.op(name))
        transaction.shadow._validate(resolve)
        routing.require(comp.fetch('motion_engine',None) is engine and
                        comp.fetch('motion_osc_reader',None) is reader and
                        engine.revision == revision and engine.started == started,
                        'Engine, Reader, Revision oder Zustandsstart verändert.')
    except Exception:
        runtime.text, pixel.text = info['runtime_old'], info['old']
        comp.unstore(visual.KEY)
        raise
    comp.store(BACKUP, dict(runtime_old=info['runtime_old'], shader_old=info['old'],
                           runtime_hash=hashlib.sha256(info['runtime_new'].encode()).hexdigest(),
                           shader_hash=hashlib.sha256(info['new'].encode()).hexdigest()))
    probe.destroy()
    return dict(passed=True, gpu_checks=checks, reveal_duration_seconds=3,
                reveal_after_approval=True, engine_reset=False, targets_changed=False,
                chairs_changed=False, revision_changed=False, masks_changed=False, saved=False,
                next='activate one proposal in UI; observe full reveal and automatic approval')


def rollback(resolve):
    comp = transaction.shadow._validate(resolve)
    info = comp.fetch(BACKUP,None)
    routing.require(isinstance(info,dict), 'Eigene Reveal-Sicherung fehlt.')
    runtime, pixel = comp.op('motion_runtime'), comp.op('motion_pixel')
    routing.require(hashlib.sha256(runtime.text.encode()).hexdigest() == info['runtime_hash'] and
                    hashlib.sha256(pixel.text.encode()).hexdigest() == info['shader_hash'],
                    'Runtime/Shader später verändert; nichts überschrieben.')
    runtime.text, pixel.text = info['runtime_old'], info['shader_old']
    comp.unstore(visual.KEY)
    comp.unstore(BACKUP)
    return dict(restored=True, engine_reset=False, revision_changed=False, saved=False)
