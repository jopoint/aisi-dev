"""Textport-Diagnose: OSC, DAT und Instanzen vergleichen; nichts speichern.

Erfasst zuerst den vorhandenen DAT-Zustand und anschließend einen erzwungenen
Cook. Keine Parameter, Verbindungen oder OSC-Daten werden verändert.
"""
import json
import math

chairs = op('/project1/comp_layout_proposal/chairs')
raw = op('/project1/comp_io/null_osc_raw')
active = chairs.op('chairs_active')
assert raw is not None and active is not None

def value(name):
    channel = raw[name]
    if channel is None:
        return None
    number = float(channel.eval())
    return number if math.isfinite(number) else str(number)

report = {'project': project.name, 'received_count': value('chair/count'),
          'active_before_forced_cook': active.text}
report['received_slots'] = [dict(index=i, x=value('chair/%d/x' % i),
    y=value('chair/%d/y' % i), radius=value('chair/%d/radius' % i)) for i in range(15)]
active.cook(force=True)
report['active_after_forced_cook'] = active.text
report['dat_changed_by_forced_cook'] = report['active_before_forced_cook'] != active.text
report['dat_errors'] = active.errors()
report['instances'] = []
for i in range(1, 16):
    inst = chairs.op('item%d' % i)
    if inst is None:
        report['instances'].append({'name': 'item%d' % i, 'missing': True})
        continue
    geo = inst.op('chair_geo')
    report['instances'].append({'name': inst.name,
        'parameters': {name: {'value': float(getattr(inst.par, name).eval()),
                             'expression': getattr(inst.par, name).expr,
                             'mode': str(getattr(inst.par, name).mode)}
                       for name in ['X', 'Y', 'Radius']},
        'geometry_scale': [float(geo.par.sx.eval()), float(geo.par.sy.eval())],
        'render': bool(geo.par.render.eval()), 'errors': geo.errors()})
report['renders'] = {}
for path in ['/project1/comp_layout_proposal/render_synth_chairs_regular_floor',
             '/project1/comp_layout_proposal/chair_debug/render_synth_chair_debug_preview']:
    render = op(path)
    resolved = render.par.geometry.eval()
    resolved = resolved if isinstance(resolved, (list, tuple)) else [resolved]
    report['renders'][path] = {'geometry_value': str(render.par.geometry.val),
        'resolved_geometry': [getattr(g, 'path', str(g)) for g in resolved],
        'errors': render.errors()}
print(json.dumps(report, indent=2))
print('Keine Parameter geändert und nichts gespeichert; nur chairs_active einmal neu berechnet.')
