"""Navigation-circle shadow: local shader patch with isolated GPU comparison.

Manual Textport calls only. No saves, pose changes, masks or routing edits.
"""
import hashlib
import copy

from td_builders import build_motion_output_routing as routing

PATH = '/project1/comp_aisi_motion_v1_5'
PROBE = '/project1/comp_aisi_motion_navigation_shadow_check'
SESSION = 'motion_navigation_shadow_probe'
BACKUP = 'motion_navigation_shadow_backup'
ANCHOR = '                float nav=state.x>0.0?coverage(centerDistance-navRadius):0.0;'
CALL = '                layer*=1.0-navigationShadow(p-source.xy,navRadius,state.x,nav);'
OFFSET_HELPER = '''float navigationShadow(vec2 offset, float radius, float scale, float nav) {
    if(scale<=0.0) return 0.0;
    // Reduce projected background light, then draw the unchanged circle above it.
    // Keep the circle interior/cutout unchanged; offset and softness shrink with it.
    float d=length(offset-vec2(2.5,2.5)*scale);
    return (1.0-smoothstep(radius-2.0*scale,radius+2.0*scale,d))
        *.65*scale*(1.0-nav);
}
'''
HELPER = OFFSET_HELPER.replace(
    '// Keep the circle interior/cutout unchanged; offset and softness shrink with it.',
    '// Centered radial shadow, independent of feedback direction or animation.').replace(
    'length(offset-vec2(2.5,2.5)*scale)', 'length(offset)')


def patch_shader(text):
    if 'navigationShadow(' in text:
        known = HELPER if HELPER in text else OFFSET_HELPER
        routing.require(text.count(known) == 1 and text.count(CALL) == 1
                        and text.count('navigationShadow(') == 2,
                        'Schatten-Code lokal abweichend; nichts überschrieben.')
        return text.replace(known, HELPER, 1)
    routing.require(text.count(ANCHOR) == 1 and text.count('float targetEdge(') == 1
                    and 'navigationShadow(' not in text, 'Navigationscode lokal abweichend; nichts überschrieben.')
    return text.replace('float targetEdge(', HELPER + 'float targetEdge(', 1).replace(ANCHOR, ANCHOR + '\n' + CALL, 1)


def _checked_backup(comp, text):
    previous = comp.fetch(BACKUP, None)
    routing.require(previous is None or (isinstance(previous, dict)
                    and isinstance(previous.get('old'), str)
                    and previous.get('new_sha256') == hashlib.sha256(text.encode()).hexdigest()),
                    'Shader passt nicht zur vorhandenen Schattensicherung.')
    return copy.deepcopy(previous)


def _validate(resolve):
    from td_builders import motion_live_output
    motion_live_output.validate(resolve, resolve(routing.PATH))
    comp = resolve(PATH)
    routing.require(comp is not None and comp.op('motion_pixel') is not None, 'Motion-Shader fehlt.')
    return comp


def prepare(resolve):
    import numpy as np
    comp = _validate(resolve)
    routing.require(resolve(PROBE) is None, 'Eigener Schatten-Prüfzweig existiert bereits.')
    old = comp.op('motion_pixel').text
    new = patch_shader(old)
    routing.require(old != new, 'Schatten bereits installiert.')
    previous = _checked_backup(comp, old)
    reference = new.replace(HELPER, '', 1).replace('\n' + CALL, '', 1)
    kinds = {k: routing.symbol(k) for k in ('containerCOMP', 'scriptTOP', 'textDAT', 'glslTOP')}
    routing.require(all(kinds.values()), 'Benötigter TD-Operatortyp fehlt.')
    probe = resolve('/project1').create(kinds['containerCOMP'], PROBE.rsplit('/', 1)[1])
    try:
        probe.store(SESSION, {'old': old, 'new': new, 'reference': reference, 'previous_backup': previous})
        probe.store('data', np.zeros((6, 6, 4), np.float32))
        callback = probe.create(kinds['textDAT'], 'state_callbacks')
        callback.text = "def onCook(scriptOp):\n    scriptOp.copyNumpyArray(scriptOp.parent().fetch('data'))\n"
        state = probe.create(kinds['scriptTOP'], 'state')
        state.par.callbacks = callback.path
        fmt = getattr(state.par, 'format', None)
        if fmt is None: fmt = getattr(state.par, 'pixelformat', None)
        routing.require(fmt is not None, 'Float-State-Format fehlt.')
        fmt.val = 'rgba32float'
        for version, text in (('old', reference), ('new', new)):
            pixel = probe.create(kinds['textDAT'], version + '_pixel')
            pixel.text = text
            for surface, value in (('floor', 0), ('tabletop', 1)):
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
        _validate(resolve)
        return {'prepared': True, 'probe': PROBE, 'production_shader_changed': False,
                'offset_cm': [0, 0], 'radial': True, 'blur_cm': 2, 'opacity': .65, 'saved': False,
                'next': 'install in a separate Textport entry; GPU proof runs first'}
    except Exception:
        probe.destroy()
        raise


def gpu_check(probe):
    import numpy as np
    from td_builders.motion_design import WIDTH, DEPTH, CORNER
    checks = []
    first_alpha = None
    for scale, success, feedback in ((1, False, False), (.35, False, False),
                                     (0, False, False), (1, True, False), (1, False, True)):
        data = np.zeros((6, 6, 4), np.float32)
        data[0, 0] = (250, 250, 0, 1)
        data[0, 1] = (285, 250, 0, 1)  # White target surrounds the complete nav circle.
        data[0, 2] = (scale, int(feedback), .63 if feedback else 0, int(success))
        data[0, 3] = (0, 0, 0, 1)
        data[0, 4] = (WIDTH, DEPTH, CORNER, 0)
        data[5, 0] = (4, 4, 1, 1)
        probe.store('data', data)
        probe.op('state').cook(force=True)
        images = {}
        for version in ('old', 'new'):
            for surface in ('floor', 'tabletop'):
                node = probe.op(version + '_' + surface)
                routing.digest(node)
                images[version + '_' + surface] = node.numpyArray(delayed=False).copy()
        routing.require(np.array_equal(images['old_floor'], images['new_floor']), 'Bodenausgabe verändert.')
        old, new = images['old_tabletop'], images['new_tabletop']
        if scale == 0 or success:
            routing.require(np.array_equal(old, new), 'Ohne Navigation oder bei Erfolg darf kein Schatten entstehen.')
            changed = 0
        else:
            y, x = np.mgrid[:old.shape[0], :old.shape[1]]
            radius = np.hypot((x + .5) * 500 / old.shape[1] - 250,
                              (y + .5) * 500 / old.shape[0] - 250)
            inner = radius < 29 * scale - .36
            far = radius > 36 * scale + 1
            routing.require(np.any(inner) and np.array_equal(old[inner], new[inner]), 'Kreisinneres verändert.')
            routing.require(np.array_equal(old[far], new[far]), 'Schatten wirkt außerhalb des Kreises zu weit.')
            delta = np.max(old[:, :, :3] - new[:, :, :3], axis=2)
            changed = int((delta > .03).sum())
            routing.require(changed > 0 and float(delta.max()) > .1 * scale,
                            'Kein sichtbarer Kontrast auf weißer Zielfläche.')
            routing.require(float(np.max(new - old)) <= 1e-6, 'Schatten fügt unerwartet Licht hinzu.')
            alpha = old[:, :, 3] - new[:, :, 3]
            tolerance = 1 / 255 + 1e-5
            routing.require(max(float(np.max(np.abs(alpha - np.flipud(alpha)))),
                                float(np.max(np.abs(alpha - np.fliplr(alpha)))),
                                float(np.max(np.abs(alpha - alpha.T)))) <= tolerance,
                            'Schatten nicht gleichmäßig um den Kreismittelpunkt.')
            if scale == 1:
                if first_alpha is None: first_alpha = alpha.copy()
                else: routing.require(float(np.max(np.abs(first_alpha - alpha))) <= tolerance,
                                      'Grünes Feedback verändert den Schatten.')
        checks.append({'nav_scale': scale, 'success': success, 'floor_pixel_equal': True,
                       'circle_interior_unchanged': True, 'shadow_pixels': changed,
                       'radial_shadow': True, 'feedback_active': feedback})
    return checks


def install(resolve):
    comp = _validate(resolve)
    probe = resolve(PROBE)
    routing.require(probe is not None, 'Zuerst prepare aufrufen.')
    info = probe.fetch(SESSION, None)
    routing.require(isinstance(info, dict), 'Eigene Prüfregistrierung fehlt.')
    pixel = comp.op('motion_pixel')
    routing.require(pixel.text == info['old']
                    and _checked_backup(comp, pixel.text) == info.get('previous_backup'),
                    'Shader oder Schattensicherung seit Vorbereitung verändert.')
    # Exact isolated shader texts must still be the two registered versions.
    routing.require(probe.op('old_pixel').text == info.get('reference', info['old'])
                    and probe.op('new_pixel').text == info['new'], 'Prüfshader lokal verändert.')
    checks = gpu_check(probe)
    engine, reader = comp.fetch('motion_engine', None), comp.fetch('motion_osc_reader', None)
    revision = getattr(engine, 'revision', None)
    try:
        pixel.text = info['new']
        for name in ('render_floor', 'render_tabletop', 'render_preview'):
            routing.digest(comp.op(name))
        _validate(resolve)
        routing.require(comp.fetch('motion_engine', None) is engine
                        and comp.fetch('motion_osc_reader', None) is reader
                        and getattr(engine, 'revision', None) == revision, 'Motion-State/Revision verändert.')
    except Exception:
        pixel.text = info['old']
        raise
    previous = info.get('previous_backup')
    comp.store(BACKUP, {'old': previous['old'] if previous is not None else info['old'],
                        'new_sha256': hashlib.sha256(info['new'].encode()).hexdigest()})
    probe.destroy()
    return {'passed': True, 'gpu_checks': checks, 'engine_reset': False,
            'targets_changed': False, 'masks_changed': False, 'saved': False,
            'next': 'separate live_output.verify and physical contrast check'}


def rollback(resolve):
    comp = _validate(resolve)
    info = comp.fetch(BACKUP, None)
    routing.require(isinstance(info, dict), 'Eigene Schattensicherung fehlt.')
    pixel = comp.op('motion_pixel')
    routing.require(hashlib.sha256(pixel.text.encode()).hexdigest() == info['new_sha256'],
                    'Shader nach Schatteninstallation verändert; nichts überschrieben.')
    pixel.text = info['old']
    comp.unstore(BACKUP)
    return {'restored': True, 'saved': False}
