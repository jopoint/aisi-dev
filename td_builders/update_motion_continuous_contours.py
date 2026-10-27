"""Continuous 5 cm target contour and equally thick, inward chair rings."""
import copy
import hashlib

from td_builders import build_motion_output_routing as routing
from td_builders import update_motion_feedback_brightness as transaction
from td_builders import update_motion_target_dashes as dashes
from td_builders import update_motion_chair_reveal as chairs
from td_builders.update_motion_target_divisions import check_pattern

PROBE = '/project1/comp_aisi_motion_continuous_contours_check'
SESSION = 'motion_continuous_contours_probe'
BACKUP = 'motion_continuous_contours_backup'
HELPER = '''float targetContour(vec2 local, vec2 halfSize, float corner) {
    float d=roundedRect(local,halfSize,corner);
    return max(0.0,coverage(d)-coverage(d+5.0));
}
'''
FILL = dashes.NEW_FILL.replace('targetDashes(', 'targetContour(')
OLD_CHAIR = 'coverage(abs(length(p-c.xy)-(c.z-1.25))-1.25)'
NEW_CHAIR = 'coverage(abs(length(p-c.xy)-(c.z-2.5))-2.5)'


def patch_shader(text):
    routing.require(text.count(dashes.HELPER) == 1 and text.count(dashes.NEW_FILL) == 1
                    and 'float targetContour(' not in text,
                    'Gestrichelter Zielshader lokal abweichend; nichts überschrieben.')
    return text.replace(dashes.HELPER, HELPER, 1).replace(dashes.NEW_FILL, FILL, 1)


def patch_chairs(text):
    routing.require(text.count(OLD_CHAIR) == 1 and NEW_CHAIR not in text
                    and 'clock.y=visualReveal.x;' in text,
                    'Chair-Strich-/Revealcode lokal abweichend; nichts überschrieben.')
    return text.replace(OLD_CHAIR, NEW_CHAIR, 1)


def prepare(resolve):
    import numpy as np
    chair = chairs.validate(resolve)
    old = chair.op('chair_pixel').text
    new = patch_chairs(old)
    result = transaction.prepare(resolve, probe_path=PROBE, session=SESSION, backup=BACKUP, patcher=patch_shader)
    probe = resolve(PROBE)
    try:
        info = dict(probe.fetch(SESSION))
        info.update(chair_old=old, chair_new=new, owned=copy.deepcopy(chair.fetch('chair_owned')))
        info['mask'] = info['new'].split('void main() {')[0]+'''void main() {
    vec2 p=vec2(vUV.x,1.0-vUV.y)*500.0;
    vec4 target=datum(1,0),shape=datum(4,0);
    float d=roundedRect(rotate2(p-target.xy,-target.z),shape.xy*.5,shape.z);
    float band=max(0.0,coverage(d)-coverage(d+5.0));
    float radius=length(p-vec2(100,400));
    float chair=max(0.0,coverage(radius-25.0)-coverage(radius-20.0));
    fragColor=TDOutputSwizzle(vec4(band,coverage(d),chair,1));
}
'''
        probe.op('mask_pixel').text = info['mask']
        probe.store(SESSION, info)
        probe.store('chair_data', np.zeros((1,15,4), dtype=np.float32))
        callbacks = probe.create(routing.symbol('textDAT'), 'chair_callbacks')
        callbacks.text = "def onCook(scriptOp):\n    scriptOp.copyNumpyArray(scriptOp.parent().fetch('chair_data'))\n"
        state = probe.create(routing.symbol('scriptTOP'), 'chair_state')
        state.par.callbacks = callbacks.path
        fmt = getattr(state.par, 'format', None)
        if fmt is None: fmt = getattr(state.par, 'pixelformat', None)
        routing.require(fmt is not None, 'Float-State-Format fehlt.')
        fmt.val = 'rgba32float'
        for version, text in (('old',old), ('new',new)):
            pixel = probe.create(routing.symbol('textDAT'), version+'_chair_pixel')
            pixel.text = text
            render = probe.create(routing.symbol('glslTOP'), version+'_chairs')
            render.inputConnectors[0].connect(probe.op('state'))
            render.inputConnectors[1].connect(state)
            render.par.pixeldat = pixel.path
            render.par.outputresolution = 'custom'
            render.par.resolutionw = render.par.resolutionh = 1000
        chairs.validate(resolve)
        result.update(target_width_cm=5, chair_width_cm=5, continuous=True,
                      outer_footprints_changed=False, chairs_moved=False)
        return result
    except Exception:
        probe.destroy()
        raise


def gpu_check(probe):
    import numpy as np
    from td_builders.motion_design import WIDTH, DEPTH, CORNER
    from td_builders.update_motion_alignment_guides import check_floor
    checks = []
    chair_data = np.zeros((1,15,4), np.float32)
    chair_data[0,0] = (100,400,25,1)
    probe.store('chair_data', chair_data)
    probe.op('chair_state').cook(force=True)
    for rotation, ready in ((0,1), (33,1), (90,1), (0,0)):
        data = np.zeros((6,6,4), np.float32)
        data[0,0] = (120,150,rotation,1)
        data[0,1] = (350,350,rotation,1)
        data[0,2] = (1,1,.5,0)
        data[0,3] = (0,0,0,1)
        data[0,4] = (WIDTH,DEPTH,CORNER,0)
        data[0,5] = (1,1,0,1)
        data[5,0] = (20,10,1,1)
        data[5,1] = (10,ready,1,0)
        probe.store('data', data)
        probe.op('state').cook(force=True)
        images = {}
        for name in ('old_floor','new_floor','old_tabletop','new_tabletop','mask_tabletop','old_chairs','new_chairs'):
            node = probe.op(name)
            routing.digest(node)
            images[name] = node.numpyArray(delayed=False).copy()
            routing.require(np.isfinite(images[name]).all(), 'Nichtendliche Kontur-Ausgabe.')
        if not ready:
            routing.require(all(not images[name].any() for name in ('new_floor','new_tabletop','new_chairs')),
                            'Konturen vor Freigabe sichtbar.')
        else:
            mask = images['mask_tabletop']
            inside = mask[:,:,1] > 0
            target_proof = check_pattern(images['new_floor'][inside,3], mask[inside,0])
            check_floor(images['old_floor'][~inside], images['new_floor'][~inside])
            # Source and target are separated: tabletop feedback/navigation must stay identical.
            check_floor(images['old_tabletop'], images['new_tabletop'])
            chair_proof = check_pattern(images['new_chairs'][:,:,3], mask[:,:,2])
            routing.require(float(images['new_chairs'][:,:,3].sum()) > float(images['old_chairs'][:,:,3].sum()),
                            'Chair-Ring nicht dicker.')
            checks.append(dict(rotation_deg=rotation, target=target_proof, chair=chair_proof,
                               width_cm=5, feedback_unchanged=True))
    checks.append(dict(case='hidden_until_approved', passed=True))
    return checks


def install(resolve):
    comp = transaction.shadow._validate(resolve)
    chair = chairs.validate(resolve)
    probe = resolve(PROBE)
    routing.require(probe is not None, 'Zuerst prepare aufrufen.')
    info = probe.fetch(SESSION, None)
    routing.require(isinstance(info, dict), 'Eigene Prüfregistrierung fehlt.')
    pixel, chair_pixel = comp.op('motion_pixel'), chair.op('chair_pixel')
    routing.require(pixel.text == info['old'] and chair_pixel.text == info['chair_old']
                    and chair.fetch('chair_owned') == info['owned'] and comp.fetch(BACKUP,None) is None,
                    'Shader/Chair-Snapshot seit Vorbereitung verändert.')
    for name, key in (('old_pixel','old'), ('new_pixel','new'), ('mask_pixel','mask'),
                      ('old_chair_pixel','chair_old'), ('new_chair_pixel','chair_new')):
        routing.require(probe.op(name).text == info[key], 'Prüfshader lokal verändert.')
    checks = gpu_check(probe)
    engine, reader = comp.fetch('motion_engine'), chair.fetch('chair_reader', None)
    routing.require(engine is not None, 'Engine fehlt.')
    revision, started = engine.revision, engine.started
    expected = copy.deepcopy(info['owned'])
    routing.require('text_sha256' in expected[chair_pixel.path], 'Chair-DAT-Hash fehlt.')
    expected[chair_pixel.path]['text_sha256'] = hashlib.sha256(info['chair_new'].encode()).hexdigest()
    try:
        pixel.text, chair_pixel.text = info['new'], info['chair_new']
        for node in (comp.op('render_floor'),comp.op('render_tabletop'),comp.op('render_preview'),chair.op('out_chairs')):
            routing.digest(node)
        routing.assert_snapshot(resolve, expected)
        chair.store('chair_owned', expected)
        chairs.validate(resolve)
        routing.require(comp.fetch('motion_engine') is engine and chair.fetch('chair_reader',None) is reader
                        and engine.revision == revision and engine.started == started,
                        'Engine/Reader/Revision verändert.')
    except Exception:
        pixel.text, chair_pixel.text = info['old'], info['chair_old']
        chair.store('chair_owned', info['owned'])
        raise
    comp.store(BACKUP, dict(old=info['old'], chair_old=info['chair_old'], owned=info['owned'], expected=expected,
                           shader_hash=hashlib.sha256(info['new'].encode()).hexdigest(),
                           chair_hash=hashlib.sha256(info['chair_new'].encode()).hexdigest()))
    probe.destroy()
    return dict(passed=True, gpu_checks=checks, target_width_cm=5, chair_width_cm=5,
                targets_changed=False, chairs_moved=False, revision_changed=False, masks_changed=False,
                saved=False, next='separate live_output.verify and physical contour check')


def rollback(resolve):
    comp = transaction.shadow._validate(resolve)
    chair = chairs.validate(resolve)
    info = comp.fetch(BACKUP,None)
    routing.require(isinstance(info,dict), 'Eigene Kontursicherung fehlt.')
    pixel, chair_pixel = comp.op('motion_pixel'), chair.op('chair_pixel')
    routing.require(hashlib.sha256(pixel.text.encode()).hexdigest() == info['shader_hash']
                    and hashlib.sha256(chair_pixel.text.encode()).hexdigest() == info['chair_hash']
                    and chair.fetch('chair_owned') == info['expected'], 'Shader/Snapshot später verändert.')
    pixel.text, chair_pixel.text = info['old'], info['chair_old']
    chair.store('chair_owned', info['owned'])
    chairs.validate(resolve)
    comp.unstore(BACKUP)
    return dict(restored=True, chairs_moved=False, revision_changed=False, saved=False)
