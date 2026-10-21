"""AISI-Tabletop-Pfeile am Zielmittelpunkt begrenzen; manuelle TD-Reparatur."""

ROOT = '/project1/comp_layout_proposal'
BACKUP_KEY = 'aisi_arrow_endpoint_before_repair'
RELATIVE_PATH = 'table_motion_line_tabletop_geo/motion_tabletop_helpers'
ANCHOR = '    seg_dx = end_x - sx\n    seg_dy = end_y - sy\n'
MARKER = '    # aisi_target_center_endpoint_v1\n'
CLAMP = MARKER + '''    if dist < math.hypot(end_x - sx, end_y - sy):
        end_x, end_y = tx, ty

'''


def corrected_source(text):
    if text.count(ANCHOR) != 1 or text.count('def points():') != 1:
        raise ValueError('Unbekannter/mehrdeutiger AISI-Tabletop-Pfeil-Callback')
    if MARKER in text:
        if CLAMP + ANCHOR not in text:
            raise ValueError('Abweichende bestehende Pfeilkorrektur')
        return text
    if 'source_inner_poly' not in text or 'end_x, end_y = _ray_polygon_hit(' not in text:
        raise ValueError('Erwartete Source-Innenkontur-Begrenzung fehlt')
    result = text.replace(ANCHOR, CLAMP + ANCHOR)
    compile(result, RELATIVE_PATH, 'exec')
    return result


def _targets(root):
    items = [root.op('table_template')] + [
        child for child in root.children
        if child.name.startswith('item') and child.name[4:].isdigit()
    ]
    if items[0] is None or len(items) < 2:
        raise ValueError('Template oder Tischinstanzen fehlen')
    callbacks = [item.op(RELATIVE_PATH) for item in items]
    if any(node is None for node in callbacks):
        raise ValueError('AISI-Tabletop-Pfeil-Callback fehlt')
    return callbacks


def restore_aisi_arrow_endpoint(resolve):
    root = resolve(ROOT)
    backup = root.fetch(BACKUP_KEY, None) if root is not None else None
    if backup is None:
        raise ValueError('Keine Pfeil-Rückfallkopie vorhanden')
    if any(resolve(path) is None for path, text in backup):
        raise ValueError('Rückfallziel fehlt')
    for path, text in backup:
        resolve(path).text = text
    return {'restored_callbacks': len(backup), 'saved': False}


def repair_aisi_arrow_endpoint(resolve):
    root = resolve(ROOT)
    if root is None:
        raise ValueError('AISI-COMP fehlt')
    callbacks = _targets(root)
    before = [node.text for node in callbacks]
    after = [corrected_source(text) for text in before]
    if root.fetch(BACKUP_KEY, None) is None:
        root.store(BACKUP_KEY, [(node.path, text) for node, text in zip(callbacks, before)])
    try:
        for node, text in zip(callbacks, after):
            node.text = text
    except Exception:
        for node, text in zip(callbacks, before):
            node.text = text
        raise
    return {'changed_callbacks': sum(a != b for a, b in zip(before, after)),
            'forced_cook': False, 'saved': False}


try:
    _resolve = op
except NameError:
    if __name__ == '__main__':
        raise RuntimeError('Im TouchDesigner-Python-Textport ausführen')
else:
    print(repair_aisi_arrow_endpoint(_resolve))
    print('AISI-Pfeilende begrenzt. Kein Force-Cook, keine Speicherung.')
    print('Rücknahme: restore_aisi_arrow_endpoint(op)')
