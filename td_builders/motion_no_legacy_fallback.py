"""Mute only legacy content in normal AISI mode; retain original mode/mask gates."""
import copy

from td_builders import motion_live_output as live

PATH = '/project1/comp_aisi_motion_no_legacy_fallback'
SESSION = 'motion_no_legacy_fallback'
ROLES = ('floor', 'tabletop', 'chairs')


def configure_transparent(node):
    """Resolve TD-version-specific Constant TOP channels without script imports."""
    parameters = []
    for names in (('colorr', 'color0r'), ('colorg', 'color0g'),
                  ('colorb', 'color0b'), ('alpha', 'colora', 'color0a')):
        parameter = next((getattr(node.par, name, None) for name in names
                          if getattr(node.par, name, None) is not None), None)
        if parameter is None:
            raise ValueError('Constant-TOP-Farbparameter fehlt: '+ '/'.join(names))
        parameters.append(parameter)
    for parameter in parameters:
        parameter.val = 0


def blank_gate():
    r = live.test.routing
    return ("(int((lambda n: n is not None and n['study/mode'] is not None and "
            "n['study/mode'].eval()==2)(op(%r)) and "
            "all((lambda n: n is not None and n['state'] is not None and n['state'].eval()==0)(op(p)) "
            "for p in %r)), absTime.frame)[0]" %
            (r.RAW, (r.LAYOUT+'panel_mode', r.OUTPUT+'panel_mode')))


def legacy_nodes(comp):
    return dict(floor=comp.op('floor_legacy'), tabletop=comp.op('tabletop_legacy'),
                chairs=comp.op('simulation_chairs_legacy'))


def own_snapshot(owner):
    return {n.path: live.test.routing.signature(n) for n in [owner]+list(owner.children)}


def prepare(resolve, symbols):
    r = live.test.routing
    r.require(resolve(PATH) is None, 'Eigener Leer-Bypass existiert bereits; nichts überschrieben.')
    comp = resolve(r.PATH)
    r.require(comp is not None, 'Motion-Routing fehlt.')
    live.validate(resolve, comp)
    references = {}
    for role, node in legacy_nodes(comp).items():
        r.require(node is not None and str(node.type) == 'select'
                  and str(node.par.top.mode) == 'ParMode.CONSTANT',
                  'Legacy-Select fehlt oder ist lokal dynamisch verändert: '+role)
        source = resolve(r.ref(node.par.top))
        r.require(source is not None, 'Aktuelle Legacy-Quelle fehlt: '+role)
        references[role] = dict(node=node.path, source=source.path, original_value=node.par.top.val)
    original_live = copy.deepcopy(comp.fetch(live.SESSION))
    owner = resolve('/project1').create(symbols['containerCOMP'], PATH.rsplit('/',1)[1])
    try:
        for role, reference in references.items():
            source = owner.create(symbols['selectTOP'], role+'_original')
            source.par.top = reference['source']
            transparent = owner.create(symbols['constantTOP'], role+'_transparent')
            configure_transparent(transparent)
            transparent.par.resolutionw.expr = 'op(%r).width' % source.path
            transparent.par.resolutionh.expr = 'op(%r).height' % source.path
            switch = owner.create(symbols['switchTOP'], role+'_switch')
            switch.inputConnectors[0].connect(source)
            switch.inputConnectors[1].connect(transparent)
            switch.par.index.expr = blank_gate()
            out = owner.create(symbols['outTOP'], 'out_'+role)
            out.inputConnectors[0].connect(switch)
        owner.store(SESSION, dict(phase='prepared', references=references,
                                 original_live=original_live, owned=own_snapshot(owner)))
        live.validate(resolve, comp)
        return dict(prepared=True, component=PATH, production_outputs_changed=False,
                    mode='AISI without approved Motion: transparent content',
                    study_tracking_unchanged=True, masks_changed=False, saved=False,
                    next='install in a separate Textport entry; GPU proof first')
    except Exception:
        owner.destroy()
        raise


def registered(resolve):
    r = live.test.routing
    owner = resolve(PATH)
    r.require(owner is not None, 'Eigener Leer-Bypass fehlt.')
    info = owner.fetch(SESSION, None)
    r.require(isinstance(info, dict) and own_snapshot(owner) == info['owned'],
              'Eigener Leer-Bypass wurde lokal verändert; nichts überschrieben.')
    return owner, info


def gpu_check(resolve, owner):
    import numpy as np
    r = live.test.routing
    checks = []
    for role in ROLES:
        switch, source = owner.op(role+'_switch'), owner.op(role+'_original')
        expression = switch.par.index.expr
        try:
            r.digest(source)
            original = source.numpyArray(delayed=False).copy()
            switch.par.index = 0
            r.digest(switch)
            bypass = switch.numpyArray(delayed=False).copy()
            r.require(np.array_equal(original, bypass), role+': Originalzweig nicht pixelgleich.')
            switch.par.index = 1
            r.digest(switch)
            blank = switch.numpyArray(delayed=False).copy()
            r.require(blank.shape == original.shape and np.isfinite(blank).all()
                      and np.count_nonzero(blank) == 0, role+': Leerzweig nicht vollständig RGBA-null.')
            checks.append(dict(surface=role, legacy_pixel_equal=True, transparent_rgba_zero=True))
        finally:
            switch.par.index.expr = expression
    return checks


def install(resolve):
    r = live.test.routing
    owner, info = registered(resolve)
    r.require(info['phase'] == 'prepared', 'Leer-Bypass bereits installiert.')
    comp = resolve(r.PATH)
    live.validate(resolve, comp)
    r.require(comp.fetch(live.SESSION) == info['original_live'],
              'Live-Registrierung seit Vorbereitung verändert.')
    checks = gpu_check(resolve, owner)
    expected_live = copy.deepcopy(info['original_live'])
    for role, reference in info['references'].items():
        expected_live['expected_owned'][reference['node']]['parameters']['top'][1] = PATH+'/out_'+role
    try:
        for role, reference in info['references'].items():
            resolve(reference['node']).par.top = PATH+'/out_'+role
        comp.store(live.SESSION, expected_live)
        live.validate(resolve, comp)
        info['phase'], info['expected_live'] = 'installed', expected_live
        owner.store(SESSION, info)
        return dict(passed=True, installed=True, gpu_checks=checks,
                    existing_selects_changed=[v['node'] for v in info['references'].values()],
                    calibration_changed=False, masks_changed=False, engine_reset=False,
                    study_tracking_unchanged=True, saved=False,
                    next='check AISI waiting/failure and modes 0/1 in separate TD frames')
    except Exception:
        for reference in info['references'].values():
            resolve(reference['node']).par.top = reference['original_value']
        comp.store(live.SESSION, info['original_live'])
        live.validate(resolve, comp)
        raise


def status(resolve):
    owner, info = registered(resolve)
    comp = resolve(live.test.routing.PATH)
    live.validate(resolve, comp)
    return dict(phase=info['phase'], blank_legacy_indices={
        role:int(owner.op(role+'_switch').par.index.eval()) for role in ROLES},
        motion_indices=live.indices(comp), source_approved=bool(comp.par.Sourceapproved.eval()),
        saved=False)


def rollback(resolve):
    r = live.test.routing
    owner, info = registered(resolve)
    comp = resolve(r.PATH)
    live.validate(resolve, comp)
    if info['phase'] == 'installed':
        r.require(comp.fetch(live.SESSION) == info['expected_live'],
                  'Live-Registrierung später verändert; nichts überschrieben.')
        for reference in info['references'].values():
            resolve(reference['node']).par.top = reference['original_value']
        comp.store(live.SESSION, info['original_live'])
        live.validate(resolve, comp)
    owner.destroy()
    return dict(restored=True, masks_changed=False, saved=False)
