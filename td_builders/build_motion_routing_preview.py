"""Isolated routing rehearsal; never reconnect existing content/projector nodes."""
import builtins
import json
import sys

NAME = 'comp_aisi_motion_routing_preview'
LAYOUT = '/project1/comp_layout_proposal/'
MOTION = '/project1/comp_aisi_motion_v1_5/'
RAW = '/project1/comp_io/null_osc_raw'
REFERENCED_RESOLUTION = frozenset(('resolutionw', 'resolutionh'))
GATE = ("int(parent().par.Enablemotion.eval() and "
        "(lambda raw: raw is not None and raw['study/mode'] is not None "
        "and raw['study/mode'].eval() == 2)(op(%r)))" % RAW)


def preflight(resolve):
    names = {
        'floor': LAYOUT+'null_floor_with_optional_synth_chairs',
        'tabletop': LAYOUT+'null_tabletop_masked',
        'mask': LAYOUT+'null_table_mask',
        'mask_comp': LAYOUT+'mask_tabletop',
        'chair_comp': LAYOUT+'composite_floor_with_synth_chairs',
        'chair_switch': LAYOUT+'switch_enable_synth_chairs_regular',
        'motion_floor': MOTION+'out_floor',
        'motion_tabletop': MOTION+'out_tabletop',
    }
    nodes = {key: resolve(path) for key, path in names.items()}
    missing = [names[key] for key, node in nodes.items() if node is None]
    if missing:
        raise RuntimeError('Erwartete Knoten fehlen; nichts geändert: '+str(missing))
    mask, chairs = nodes['mask_comp'], nodes['chair_comp']
    if (str(mask.type) != 'comp' or len(mask.inputs) != 2
            or mask.inputs[1] != nodes['mask']
            or mask.inputs[0].path != LAYOUT+'null_tabletop'
            or str(mask.par.operand.eval()) != 'multiply'):
        raise RuntimeError('Maskenreihenfolge weicht vom geprüften Graph ab; nichts geändert.')
    if list(nodes['tabletop'].inputs) != [mask]:
        raise RuntimeError('Tabletop-Ausgang weicht ab; nichts geändert.')
    if str(chairs.type) != 'comp' or len(chairs.inputs) != 2:
        raise RuntimeError('Chair-Komposition weicht ab; nichts geändert.')
    switch = nodes['chair_switch']
    if len(switch.inputs) != 2 or switch.inputs[1] != chairs:
        raise RuntimeError('Chair-Umschaltung weicht ab; nichts geändert.')
    if nodes['floor'].inputs != (switch,) and list(nodes['floor'].inputs) != [switch]:
        raise RuntimeError('Floor-Ausgang weicht ab; nichts geändert.')
    # Resolution expressions are rebound to the original evaluated parameter.
    # All other dynamic parameters/exports still require inspection.
    for node in (mask, chairs):
        dynamic = [p.name for p in node.pars()
                   if str(p.mode) != 'ParMode.CONSTANT'
                   and not (p.name in REFERENCED_RESOLUTION
                            and str(p.mode) == 'ParMode.EXPRESSION')]
        if dynamic:
            raise RuntimeError('Dynamische Composite-Parameter zuerst prüfen: '
                               +node.path+' '+str(dynamic)+'; nichts geändert.')
    nodes['chairs'] = chairs.inputs[1]
    return nodes


def build(resolve, symbols):
    root = resolve('/project1')
    if root is None or root.op(NAME) is not None:
        raise RuntimeError('project1 fehlt oder Routing-Preview existiert; nichts geändert.')
    nodes = preflight(resolve)
    comp = root.create(symbols['containerCOMP'], NAME)
    try:
        comp.appendCustomPage('Routing Preview').appendToggle(
            'Enablemotion', label='Motion nur in dieser Routing-Vorschau')[0].val = False
        comp.nodeX, comp.nodeY = 900, -1100

        def select(name, source):
            node = comp.create(symbols['selectTOP'], name)
            node.par.top = source.path
            return node

        floor = select('floor_legacy', nodes['floor'])
        tabletop = select('tabletop_legacy', nodes['tabletop'])
        motion_floor = select('floor_motion', nodes['motion_floor'])
        motion_tabletop = select('tabletop_motion', nodes['motion_tabletop'])
        mask = select('mask_existing', nodes['mask'])
        chairs = select('chairs_existing', nodes['chairs'])

        def composite(name, original, inputs):
            node = comp.copy(original, name=name, includeDocked=False)
            for p in original.pars():
                if p.name in REFERENCED_RESOLUTION and str(p.mode) == 'ParMode.EXPRESSION':
                    # Never reevaluate a copied relative path in the new parent.
                    getattr(node.par, p.name).expr = 'op(%r).par.%s.eval()' % (original.path, p.name)
            for i, source in enumerate(inputs):
                node.inputConnectors[i].connect(source)
            return node

        masked = composite('tabletop_masked', nodes['mask_comp'], (motion_tabletop, mask))
        with_chairs = composite('floor_with_chairs', nodes['chair_comp'], (motion_floor, chairs))
        optional = comp.create(symbols['switchTOP'], 'floor_optional_chairs')
        optional.inputConnectors[0].connect(motion_floor)
        optional.inputConnectors[1].connect(with_chairs)
        optional.par.index.expr = 'op(%r).par.index.eval()' % nodes['chair_switch'].path
        for name, original, motion in (('floor', floor, optional),
                                        ('tabletop', tabletop, masked)):
            switch = comp.create(symbols['switchTOP'], name+'_switch')
            switch.inputConnectors[0].connect(original)
            switch.inputConnectors[1].connect(motion)
            switch.par.index.expr = GATE
            out = comp.create(symbols['outTOP'], 'out_'+name)
            out.inputConnectors[0].connect(switch)
        comp.store('motion_routing_preview_only', True)
        return {'component': comp.path, 'enabled': False,
                'floor': comp.op('out_floor').path,
                'tabletop': comp.op('out_tabletop').path,
                'existing_nodes_changed': False, 'projector_connections_added': False,
                'saved': False, 'simulation_mask_alignment': 'not verified',
                'status': 'isolated routing preview; production outputs unchanged'}
    except Exception:
        comp.destroy()
        raise


def symbol(name):
    return (globals().get(name) or getattr(builtins, name, None)
            or getattr(sys.modules.get('__main__'), name, None))


if callable(symbol('op')):
    kinds = ('containerCOMP', 'selectTOP', 'switchTOP', 'outTOP')
    print(json.dumps(build(symbol('op'), {k:symbol(k) for k in kinds}),
                     ensure_ascii=False, indent=2))
