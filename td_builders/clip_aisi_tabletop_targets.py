"""Textport: eigene Tabletop-Ziele geometrisch beschneiden, ohne neue Render TOPs."""

import json
import math

ROOT = '/project1/comp_layout_proposal'
BACKUP = 'aisi_target_polygon_clip_backup_v1'
MARKER = '# aisi_target_polygon_clip_v2'
OLD_MARKER = '# aisi_target_polygon_clip_v1'


CLIP_FUNCTION_SOURCE = r'''
def transform_polygon(points, source_pose, target_pose):
    """Source-Fläche in lokale Target-Koordinaten, mit bestehenden Geo-Posen."""
    sx, sy, sr, ssx, ssy = source_pose
    tx, ty, tr, tsx, tsy = target_pose
    if abs(tsx) < 1e-12 or abs(tsy) < 1e-12:
        raise ValueError('Target-Skalierung ist null')
    sc, sn = math.cos(math.radians(sr)), math.sin(math.radians(sr))
    tc, tn = math.cos(math.radians(tr)), math.sin(math.radians(tr))
    result = []
    for px, py in points:
        px, py = px * ssx, py * ssy
        dx, dy = sx + sc * px - sn * py - tx, sy + sn * px + sc * py - ty
        result.append(((tc * dx + tn * dy) / tsx, (-tn * dx + tc * dy) / tsy))
    return result


def clip_polygon(subject, boundary):
    """Konvexe kanonische Tischfläche; keine parallele Footprint-Definition."""
    area = sum(p[0] * q[1] - q[0] * p[1]
               for p, q in zip(boundary, boundary[1:] + boundary[:1]))
    if len(boundary) < 3 or abs(area) < 1e-12:
        raise ValueError('Source-Fläche ist leer oder degeneriert')
    sign = 1 if area > 0 else -1
    output = list(subject)
    for a, b in zip(boundary, boundary[1:] + boundary[:1]):
        if not output:
            break
        def side(p):
            return sign * ((b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0]))
        previous, clipped = output[-1], []
        prev_side = side(previous)
        for current in output:
            current_side = side(current)
            if (current_side >= 0) != (prev_side >= 0):
                t = prev_side / (prev_side - current_side)
                clipped.append((previous[0] + t * (current[0] - previous[0]),
                                previous[1] + t * (current[1] - previous[1])))
            if current_side >= 0:
                clipped.append(current)
            previous, prev_side = current, current_side
        output = clipped
    return output if len(output) >= 3 else []


def clip_target_sop(scriptOp):
    raw = op('/project1/comp_io/null_osc_raw')
    if raw is None or raw['study/mode'] is None or raw['study/mode'].eval() != 2:
        return
    target = scriptOp.parent()
    item = target.parent()
    if not item.name.startswith('item') or not item.name[4:].isdigit():
        return
    index = int(item.name[4:]) - 1
    available = raw['table/%d/source_available' % index]
    if available is not None and available.eval() != 1:
        scriptOp.clear()
        return
    source = item.op('table_source_geo')
    surface = source.op('table_surface')
    def pose(geo):
        return tuple(float(geo.par[name].eval()) for name in ('tx', 'ty', 'rz', 'sx', 'sy'))
    if len(surface.prims) != 1:
        raise ValueError('Source-Fläche benötigt genau ein Polygon')
    # Script-SOP kann unbenutzte Punkte enthalten. Nur die tatsächliche Fläche verwenden.
    boundary = transform_polygon([(float(v.point.P[0]), float(v.point.P[1])) for v in surface.prims[0]],
                                 pose(source), pose(target))
    polygons = [clip_polygon([(float(v.point.P[0]), float(v.point.P[1])) for v in prim], boundary)
                for prim in scriptOp.prims]
    scriptOp.clear()
    for points in polygons:
        if not points:
            continue
        polygon = scriptOp.appendPoly(len(points), closed=True, addPoints=True)
        for index, (x, y) in enumerate(points):
            polygon[index].point.P = (x, y, 0)
'''

exec(CLIP_FUNCTION_SOURCE)


def corrected_callback(previous):
    if MARKER in previous:
        return previous
    if OLD_MARKER in previous:
        previous = original_callback(previous)
    if previous.count('def onCook(scriptOp):') != 1:
        raise ValueError('Target-Callback ist nicht eindeutig')
    original = previous.replace('def onCook(scriptOp):', 'def _unclipped_target_onCook(scriptOp):', 1)
    result = original + '\n\n' + MARKER + '\nimport math\n' + CLIP_FUNCTION_SOURCE + '''
def onCook(scriptOp):
    _unclipped_target_onCook(scriptOp)
    clip_target_sop(scriptOp)
'''
    compile(result, '<own-tabletop-target>', 'exec')
    return result


def original_callback(text):
    for marker in (MARKER, OLD_MARKER):
        if marker in text:
            text = text.split(marker, 1)[0].rstrip() + '\n'
            return text.replace('def _unclipped_target_onCook(scriptOp):', 'def onCook(scriptOp):', 1)
    return text


def restore_clipped_aisi_tabletop_targets(resolve):
    root = resolve(ROOT)
    backup = root.fetch(BACKUP, None) if root is not None else None
    if not backup:
        raise ValueError('Callback-Rückfallkopie fehlt')
    items = [root.op('table_template')] + [c for c in root.children
             if c.name.startswith('item') and c.name[4:].isdigit()]
    for item in items:
        node = item.op('table_target_tabletop_geo/table_outline_inner_callbacks')
        if node is not None and any(marker in node.text for marker in (MARKER, OLD_MARKER)):
            # Neue Replikate erben die Template-Korrektur, sind aber nicht in der alten Sicherung.
            node.text = backup.get(node.path, original_callback(node.text))
    root.store(BACKUP, None)
    return {'restored': True, 'saved': False}


def apply_target_clipping(resolve):
    root = resolve(ROOT)
    if root is None:
        raise ValueError('Layout-COMP fehlt')
    items = [root.op('table_template')] + [c for c in root.children
             if c.name.startswith('item') and c.name[4:].isdigit()]
    if items[0] is None or len(items) < 2:
        raise ValueError('Template/Tischinstanzen fehlen')
    nodes, texts = [], []
    for item in items:
        callback = item.op('table_target_tabletop_geo/table_outline_inner_callbacks')
        surface = item.op('table_source_geo/table_surface')
        outline = item.op('table_target_tabletop_geo/table_outline_inner')
        if callback is None or surface is None or outline is None:
            raise ValueError('Target-Callback oder kanonische Source-Fläche fehlt')
        # Tatsächliche TD-SOP-API vor Callback-Mutation prüfen, keine Mock-Annahme.
        if len(surface.prims) != 1 or len(tuple(surface.prims[0])) < 3:
            raise ValueError('Kanonische Source-Fläche benötigt ein Flächenpolygon: ' + surface.path)
        for primitive in outline.prims:
            # TD-Poly liefert Vertex-Objekte direkt durch Iteration, nicht .vertices.
            for vertex in primitive:
                float(vertex.point.P[0]), float(vertex.point.P[1])
        nodes.append(callback)
        texts.append(corrected_callback(callback.text))
    # Eigenen teuren Vorschauzweig vollständig entfernen; keine fremden Knoten.
    old_branch = root.op('aisi_own_tabletop_targets')
    if old_branch is not None:
        old_backup = root.fetch('aisi_own_tabletop_targets_backup_v1', None)
        if not old_backup:
            raise ValueError('Alter Vorschauzweig ohne Rückfallkopie; nichts geändert')
        output, original = resolve(old_backup['output']), resolve(old_backup['original'])
        if output is None or original is None or output.inputs not in ([original], [old_branch.op('select_mode')]):
            raise ValueError('Alter Tabletop-Ausgang ist nicht eindeutig')
        output.inputConnectors[0].connect(original)
        old_branch.destroy()
        root.store('aisi_own_tabletop_targets_backup_v1', None)
    before = {node.path: node.text for node in nodes}
    if root.fetch(BACKUP, None) is None:
        root.store(BACKUP, before)
    try:
        for node, text in zip(nodes, texts):
            node.text = text
    except Exception:
        for node in nodes:
            node.text = before[node.path]
        raise
    return {'clipped_callbacks': len(nodes), 'additional_renderers': 0,
            'render_mask_projector_parameters_changed': False,
            'forced_cook': False, 'saved': False}


try:
    _resolve = op
except NameError:
    if __name__ == '__main__':
        raise RuntimeError('Im TouchDesigner-Python-Textport ausführen')
else:
    print(json.dumps(apply_target_clipping(_resolve), indent=2))
    print('Nur Target-SOP-Callbacks angepasst. Keine Render-/Kalibrierungsänderung.')
    print('Rücknahme: restore_clipped_aisi_tabletop_targets(op)')
