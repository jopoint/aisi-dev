"""Read stored per-table feedback state without cooking or changing TD nodes."""
import builtins
import json
import math
import sys


def inspect(resolve):
    comp = resolve('/project1/comp_aisi_motion_v1_5')
    if comp is None:
        raise RuntimeError('Motion-COMP fehlt.')
    engine = comp.fetch('motion_engine', None)
    reader = comp.fetch('motion_osc_reader', None)
    result = {'read_only': True, 'live': comp.fetch('motion_live_status', None),
              'tables': []}
    for identity, source, target, valid, active in (reader.rows if reader else []):
        state = engine.tables.get(identity) if engine else None
        distance = math.hypot(source.x-target.x, source.y-target.y)
        angle = abs((source.r-target.r+90) % 180-90)
        progress = ((1-max(0,min(1,(distance-8)/180)))
                    +(1-max(0,min(1,(angle-5)/60))))/2
        row = {'id': identity, 'source': list(source), 'target': list(target),
               'valid': valid, 'active': active, 'distance_cm': distance,
               'angle_deg': angle, 'progress': progress}
        if state is not None:
            row.update({name: getattr(state, name) for name in
                        ('phase','touching','baseline','navigation','halo','contact')})
            row['success_anchor'] = list(state.anchor) if state.anchor else None
        result['tables'].append(row)
    return result


def symbol(name):
    return (globals().get(name) or getattr(builtins,name,None)
            or getattr(sys.modules.get('__main__'),name,None))


if callable(symbol('op')):
    print(json.dumps(inspect(symbol('op')),ensure_ascii=False,indent=2))
