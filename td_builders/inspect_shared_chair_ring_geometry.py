"""Manueller Textport: tatsächliche Ringpunkte gegen Chair-Radius prüfen.

Kein Force-Cook, keine Parameteränderung und kein Speichern. Das Lesen von
SOP-Punkten kann reguläre TD-Abhängigkeiten auswerten; Bildänderung melden.
"""
import json
import math


def inspect_ring_geometry(resolve, project_name):
    chairs = resolve('/project1/comp_layout_proposal/chairs')
    if chairs is None:
        return {'project': project_name, 'error': 'chairs COMP fehlt'}
    rows = []
    for index in range(15):
        instance = chairs.op('item%d' % (index + 1))
        ring = instance.op('chair_geo/chair_ring') if instance is not None else None
        if instance is None or ring is None:
            rows.append({'index': index, 'missing_ring': True})
            continue
        requested = float(instance.par.Radius.eval())
        points = [(float(point.P[0]), float(point.P[1])) for point in ring.points]
        actual = max((math.hypot(x, y) for x, y in points), default=0.)
        rows.append({'index': index, 'item': instance.name,
                     'requested_radius_td': requested, 'point_count': len(points),
                     'actual_outer_radius_td': actual,
                     'active_radius_mismatch': requested > 0 and abs(actual - requested) > 1e-6,
                     'ring_errors': ring.errors()})
    return {'project': project_name, 'rings': rows,
            'active_mismatch_indices': [row['index'] for row in rows if row.get('active_radius_mismatch')]}


try:
    _td_resolve = op
    _td_project_name = project.name
except NameError:
    if __name__ == '__main__':
        raise RuntimeError('Im TouchDesigner-Python-Textport ausführen.')
else:
    print(json.dumps(inspect_ring_geometry(_td_resolve, _td_project_name), indent=2))
    print('Nur Ringpunkte gelesen; kein Force-Cook, keine Änderung, kein Speichern. '
          'Bitte angeben, ob jetzt zehn Kreise sichtbar sind.')
