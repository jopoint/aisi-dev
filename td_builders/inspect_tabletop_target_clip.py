"""Lesende Diagnose des laufenden Polygon-Clippings, ohne Render-/SOP-Mutation."""

import json
from pathlib import Path
from types import SimpleNamespace

ROOT = '/project1/comp_layout_proposal'
REPORT = Path(r'C:\dev\Promotion_Prototypen\AISI\data\aisi\debug\tabletop_target_clip.json')


class _RecordedPoly:
    def __init__(self, count):
        self.vertices = [SimpleNamespace(point=SimpleNamespace(P=(0, 0, 0))) for _ in range(count)]
    def __getitem__(self, index):
        return self.vertices[index]
    def __iter__(self):
        return iter(self.vertices)


class _RecordedSop:
    """Nur Python-Listen: Original-Callback erzeugt hier keine TD-Geometrie."""
    def __init__(self, geometry):
        self.geometry, self.prims = geometry, []
    def parent(self):
        return self.geometry
    def clear(self):
        self.prims = []
    def appendPoly(self, count, **kwargs):
        primitive = _RecordedPoly(count)
        self.prims.append(primitive)
        return primitive


def inspect_clipping(resolve):
    root = resolve(ROOT)
    raw = resolve('/project1/comp_io/null_osc_raw')
    def channel(name):
        ch = raw[name] if raw is not None else None
        return float(ch.eval()) if ch is not None else None
    report = {'mode': channel('study/mode'), 'table_count': channel('table/count'), 'items': []}
    def pose(geo):
        return tuple(float(geo.par[name].eval()) for name in ('tx', 'ty', 'rz', 'sx', 'sy'))
    for index in range(5):
        item = root.op('item%d' % (index + 1))
        if item is None:
            continue
        entry = {'item': item.path, 'source_available': channel('table/%d/source_available' % index)}
        try:
            source, target = item.op('table_source_geo'), item.op('table_target_tabletop_geo')
            surface, outline = source.op('table_surface'), target.op('table_outline_inner')
            callback = target.op('table_outline_inner_callbacks')
            entry.update(source_pose=pose(source), target_pose=pose(target),
                         source_points=[[float(p.P[i]) for i in range(3)] for p in surface.points],
                         actual_primitives=outline.numPrims,
                         errors={'target': str(target.errors()), 'outline': str(outline.errors()),
                                 'callback': str(callback.errors())})
            # Lokale TD-Callback-Funktionen auf getrenntem Python-Recorder ausführen.
            module = callback.module
            recorder = _RecordedSop(target)
            module._unclipped_target_onCook(recorder)
            polygons = [[(float(v.point.P[0]), float(v.point.P[1])) for v in prim] for prim in recorder.prims]
            source_polygon = [(float(v.point.P[0]), float(v.point.P[1])) for v in surface.prims[0]]
            boundary = module.transform_polygon(source_polygon,
                                                pose(source), pose(target))
            clipped = [module.clip_polygon(p, boundary) for p in polygons]
            entry.update(original_primitives=len(polygons),
                         predicted_own_intersection_primitives=sum(bool(p) for p in clipped),
                         source_polygon_points=source_polygon,
                         source_boundary_in_target=boundary)
        except Exception as exc:
            entry['diagnostic_error'] = type(exc).__name__ + ': ' + str(exc)
        report['items'].append(entry)
    return report


try:
    _resolve = op
except NameError:
    if __name__ == '__main__':
        raise RuntimeError('Im TouchDesigner-Python-Textport ausführen')
else:
    _report = inspect_clipping(_resolve)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(_report, indent=2, default=str), encoding='utf-8')
    print('Lesender Bericht: ' + str(REPORT))
    print('Keine Operatoren/Callbacks geändert, kein Force-Cook, keine Speicherung.')
