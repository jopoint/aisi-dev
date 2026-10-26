"""Clip the tabletop feedback halo to the actual target, via manual TD calls."""
import hashlib

from td_builders import build_motion_output_routing as routing
from td_builders import update_motion_navigation_shadow as shadow

PROBE = '/project1/comp_aisi_motion_feedback_clip_check'
SESSION = 'motion_feedback_clip_probe'
BACKUP = 'motion_feedback_clip_backup'
OLD = '                    *smoothstep(0.0,1.0,state.y);'
NEW = '                    *smoothstep(0.0,1.0,state.y)*targetMask;'


def patch_shader(text):
    if text.count(NEW) == 1 and OLD not in text:
        return text
    routing.require(text.count(OLD) == 1 and NEW not in text
                    and text.count('float ga=feedbackHalo(') == 1,
                    'Feedback-Code lokal abweichend; nichts überschrieben.')
    return text.replace(OLD, NEW, 1)


def prepare(resolve):
    import numpy as np
    comp = shadow._validate(resolve)
    routing.require(resolve(PROBE) is None, 'Eigener Feedback-Prüfzweig existiert bereits.')
    routing.require(comp.fetch(BACKUP, None) is None, 'Feedback-Sicherung existiert bereits.')
    old = comp.op('motion_pixel').text
    new = patch_shader(old)
    routing.require(new != old, 'Feedback-Begrenzung bereits installiert.')
    routing.require(old.count('void main() {') == 1, 'Shader-Hauptfunktion lokal abweichend.')
    # Use exactly the actual shader's coordinate and contour functions for the probe mask.
    mask = old.split('void main() {')[0] + '''void main() {
    vec2 p=vec2(vUV.x,1.0-vUV.y)*500.0;
    vec4 target=datum(1,0), shape=datum(4,0);
    float a=coverage(roundedRect(rotate2(p-target.xy,-target.z),shape.xy*.5,shape.z));
    fragColor=TDOutputSwizzle(vec4(a));
}
'''
    kinds = {k: routing.symbol(k) for k in ('containerCOMP', 'scriptTOP', 'textDAT', 'glslTOP')}
    routing.require(all(kinds.values()), 'Benötigter TD-Operatortyp fehlt.')
    probe = resolve('/project1').create(kinds['containerCOMP'], PROBE.rsplit('/', 1)[1])
    try:
        probe.store(SESSION, {'old': old, 'new': new, 'mask': mask})
        probe.store('data', np.zeros((6, 6, 4), np.float32))
        callback = probe.create(kinds['textDAT'], 'state_callbacks')
        callback.text = "def onCook(scriptOp):\n    scriptOp.copyNumpyArray(scriptOp.parent().fetch('data'))\n"
        state = probe.create(kinds['scriptTOP'], 'state')
        state.par.callbacks = callback.path
        fmt = getattr(state.par, 'format', None)
        if fmt is None: fmt = getattr(state.par, 'pixelformat', None)
        routing.require(fmt is not None, 'Float-State-Format fehlt.')
        fmt.val = 'rgba32float'
        for version, text in (('old', old), ('new', new), ('mask', mask)):
            pixel = probe.create(kinds['textDAT'], version + '_pixel')
            pixel.text = text
            for surface, value in (('floor', 0), ('tabletop', 1)):
                if version == 'mask' and surface == 'floor': continue
                node = probe.create(kinds['glslTOP'], version + '_' + surface)
                node.inputConnectors[0].connect(state)
                node.par.pixeldat = pixel.path
                node.par.outputresolution = 'custom'
                node.par.resolutionw = node.par.resolutionh = 1000
                uniform, val = getattr(node.par, 'vec0name', None), getattr(node.par, 'vec0valuex', None)
                if uniform is None or val is None:
                    uniform, val = getattr(node.par, 'uniname0', None), getattr(node.par, 'value0x', None)
                routing.require(uniform is not None and val is not None, 'Surface-Uniform fehlt.')
                uniform.val, val.val = 'uSurface', value
        shadow._validate(resolve)
        return {'prepared': True, 'probe': PROBE, 'production_shader_changed': False,
                'saved': False, 'next': 'install in a separate Textport entry; GPU proof runs first'}
    except Exception:
        probe.destroy()
        raise


def gpu_check(probe):
    import numpy as np
    from td_builders.motion_design import WIDTH, DEPTH, CORNER
    checks = []
    for rotation, reveal, success, feedback in ((0, 4, False, 1), (33, 4, False, 1),
            (90, 4, False, 1), (33, 1.5, False, 1), (33, 4, True, 1), (33, 4, False, 0)):
        data = np.zeros((6, 6, 4), np.float32)
        data[0, 0] = (250, 250, 0, 1)
        data[0, 1] = (285, 250, rotation, 1)
        data[0, 2] = (1, feedback, .63, int(success))
        data[0, 3] = (0, 0, 0, 1)
        data[0, 4] = (WIDTH, DEPTH, CORNER, 0)
        data[5, 0] = (4, reveal, 1, 1)
        probe.store('data', data)
        probe.op('state').cook(force=True)
        images = {}
        for name in ('old_floor', 'new_floor', 'old_tabletop', 'new_tabletop', 'mask_tabletop'):
            node = probe.op(name)
            routing.digest(node)
            images[name] = node.numpyArray(delayed=False).copy()
        old, new = images['old_tabletop'], images['new_tabletop']
        mask = images['mask_tabletop'][:, :, 0]
        routing.require(np.array_equal(images['old_floor'], images['new_floor']), 'Bodenausgabe verändert.')
        inside, outside = mask >= 1, mask <= 0
        routing.require(inside.any() and outside.any() and np.array_equal(old[inside], new[inside]),
                        'Darstellung im Zielinneren verändert.')
        if success or not feedback:
            routing.require(np.array_equal(old, new), 'Erfolg oder deaktiviertes Feedback verändert.')
            removed = 0
        else:
            green_old = old[:, :, 1] - np.maximum(old[:, :, 0], old[:, :, 2])
            green_new = new[:, :, 1] - np.maximum(new[:, :, 0], new[:, :, 2])
            removed = int(((green_old > .03) & outside).sum())
            routing.require(removed > 0, 'Prüffall zeigt kein überstehendes Feedback.')
            routing.require(float(green_new[outside].max()) <= 1e-6,
                            'Grünes Feedback außerhalb der Zielfläche.')
        checks.append({'rotation_deg': rotation, 'reveal_wave': reveal < 3, 'success': success,
                       'feedback_active': bool(feedback), 'floor_pixel_equal': True,
                       'target_interior_unchanged': True, 'removed_outside_green_pixels': removed})
    return checks


def install(resolve):
    comp = shadow._validate(resolve)
    probe = resolve(PROBE)
    routing.require(probe is not None, 'Zuerst prepare aufrufen.')
    info = probe.fetch(SESSION, None)
    routing.require(isinstance(info, dict), 'Eigene Prüfregistrierung fehlt.')
    pixel = comp.op('motion_pixel')
    routing.require(pixel.text == info['old'] and comp.fetch(BACKUP, None) is None,
                    'Shader oder Feedback-Sicherung seit Vorbereitung verändert.')
    for version in ('old', 'new', 'mask'):
        routing.require(probe.op(version + '_pixel').text == info[version], 'Prüfshader lokal verändert.')
    checks = gpu_check(probe)
    engine, reader = comp.fetch('motion_engine', None), comp.fetch('motion_osc_reader', None)
    revision = getattr(engine, 'revision', None)
    try:
        pixel.text = info['new']
        for name in ('render_floor', 'render_tabletop', 'render_preview'):
            routing.digest(comp.op(name))
        shadow._validate(resolve)
        routing.require(comp.fetch('motion_engine', None) is engine
                        and comp.fetch('motion_osc_reader', None) is reader
                        and getattr(engine, 'revision', None) == revision, 'Motion-State/Revision verändert.')
    except Exception:
        pixel.text = info['old']
        raise
    comp.store(BACKUP, {'old': info['old'], 'new_sha256': hashlib.sha256(info['new'].encode()).hexdigest()})
    probe.destroy()
    return {'passed': True, 'gpu_checks': checks, 'engine_reset': False,
            'targets_changed': False, 'masks_changed': False, 'saved': False,
            'next': 'separate live_output.verify and physical tabletop check'}


def rollback(resolve):
    comp = shadow._validate(resolve)
    info = comp.fetch(BACKUP, None)
    routing.require(isinstance(info, dict), 'Eigene Feedback-Sicherung fehlt.')
    pixel = comp.op('motion_pixel')
    routing.require(hashlib.sha256(pixel.text.encode()).hexdigest() == info['new_sha256'],
                    'Shader nach Feedbackinstallation verändert; nichts überschrieben.')
    pixel.text = info['old']
    comp.unstore(BACKUP)
    return {'restored': True, 'saved': False}
