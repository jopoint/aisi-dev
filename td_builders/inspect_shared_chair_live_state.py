"""Manueller Textport-Check ohne Force-Cook, Änderungen oder Speichern.

Bei sichtbar fehlerhaftem Count zuerst diesen Check ausführen. Der frühere
diagnose_shared_chair_count.py erzwingt eine Neuberechnung und kann damit
das zu untersuchende Aktualisierungsproblem verdecken.
"""
import json
import math


def inspect_chair_state(resolve, project_name):
    root = '/project1/comp_layout_proposal'
    chairs = resolve(root + '/chairs')
    raw = resolve('/project1/comp_io/null_osc_raw')
    active = chairs.op('chairs_active') if chairs is not None else None
    if raw is None or active is None:
        return {'project': project_name, 'error': 'OSC-Raw oder chairs_active fehlt'}

    def channel(name):
        item = raw[name]
        if item is None:
            return None
        value = float(item.eval())
        return value if math.isfinite(value) else None

    def cell(row, column):
        try:
            return float(active[row, column].val)
        except (TypeError, ValueError, IndexError, KeyError, AttributeError):
            return None

    def parameters(node, names):
        if node is None:
            return None
        result = {}
        for name in names:
            parameter = getattr(node.par, name, None)
            if parameter is not None:
                result[name] = {'value': str(parameter.eval()), 'expression': parameter.expr,
                                'mode': str(parameter.mode)}
        return result

    # Zuerst OSC/DAT aufnehmen; danach erst Instanzparameter auswerten.
    # Auch lesende Parameterabfragen können TD-Abhängigkeiten auswerten.
    received_count = channel('chair/count')
    rows = []
    for index in range(15):
        incoming = {name: channel('chair/%d/%s' % (index, name)) for name in ('x', 'y', 'radius')}
        valid = (received_count is not None and index < received_count
                 and all(value is not None for value in incoming.values()) and incoming['radius'] > 0)
        expected = {'x': (incoming['x'] - 250) * .0052,
                    'y': -(incoming['y'] - 250) * .0052,
                    'radius': incoming['radius'] * .0052} if valid else {'x': 0., 'y': 0., 'radius': 0.}
        actual = {name: cell(index + 1, name) for name in expected}
        rows.append({'index': index, 'osc': incoming, 'expected_dat': expected, 'dat': actual,
                     'dat_matches_osc': all(actual[name] is not None and abs(actual[name] - value) < 1e-6
                                            for name, value in expected.items())})
    report = {'project': project_name, 'received_count': received_count, 'dat_rows': active.numRows,
              'slots': rows, 'dat_errors': active.errors()}
    for row in rows:
        instance = chairs.op('item%d' % (row['index'] + 1))
        if instance is None:
            row['missing_instance'] = True
            continue
        row['instance'] = parameters(instance, ('X', 'Y', 'Radius'))
        row['instance_matches_dat'] = all(
            parameter in row['instance'] and row['dat'][column] is not None
            and abs(float(row['instance'][parameter]['value']) - row['dat'][column]) < 1e-6
            for parameter, column in (('X', 'x'), ('Y', 'y'), ('Radius', 'radius'))
        )
        geo = instance.op('chair_geo')
        row['geometry'] = parameters(geo, ('tx', 'ty', 'sx', 'sy', 'render'))
        row['geometry_errors'] = geo.errors() if geo is not None else ['chair_geo fehlt']
        ring = instance.op('chair_geo/chair_ring')
        row['ring_parameters'] = parameters(ring, ('Valuea', 'Valueb', 'callbacks'))
    report['summary'] = {
        'dat_positive_radii': sum(row['dat']['radius'] is not None and row['dat']['radius'] > 0 for row in rows),
        'dat_osc_mismatch_indices': [row['index'] for row in rows if not row['dat_matches_osc']],
        'instance_dat_mismatch_indices': [row['index'] for row in rows if not row.get('instance_matches_dat', False)],
    }
    render = resolve(root + '/render_synth_chairs_regular_floor')
    if render is not None:
        report['render'] = parameters(render, ('geometry', 'camera'))
        resolved = render.par.geometry.eval()
        resolved = resolved if isinstance(resolved, (list, tuple)) else [resolved]
        report['render_geometry_paths'] = [getattr(item, 'path', str(item)) for item in resolved]
        report['render_errors'] = render.errors()
    return report


# TouchDesigner stellt op/project auch als Builtins bereit. Eine Prüfung
# ausschließlich in globals() überspringt deshalb den Textport-Einstieg.
try:
    _td_resolve = op
    _td_project_name = project.name
except NameError:
    if __name__ == '__main__':
        raise RuntimeError('Diesen Check im TouchDesigner-Python-Textport ausführen.')
else:
    print(json.dumps(inspect_chair_state(_td_resolve, _td_project_name), indent=2))
    print('Nur gelesen: kein Force-Cook, keine Parameteränderung, kein Speichern. '
          'Bitte auch angeben, ob sich das sichtbare Bild durch die Abfrage verändert hat.')
