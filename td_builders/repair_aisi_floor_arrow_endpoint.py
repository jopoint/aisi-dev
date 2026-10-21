"""AISI-Bodenpfeile bis zum Zielmittelpunkt führen; manuell, ohne Speichern."""

ROOT = '/project1/comp_layout_proposal'
RELATIVE_PATH = 'table_motion_line_floor_geo/motion_floor_helpers'
BACKUP_KEY = 'aisi_floor_arrow_endpoint_before_repair'
OLD = '''    end_x, end_y = _ray_polygon_hit(
        tx,
        ty,
        -ux,
        -uy,
        target_poly
    )'''
NEW = '''    # aisi_floor_target_center_v1
    end_x, end_y = tx, ty'''
OLD_VISIBILITY = "        'visible': not overlap"
NEW_VISIBILITY = "        'visible': (tx - start_x) * ux + (ty - start_y) * uy > 0.002"


def corrected_source(text):
    if 'start_x, start_y = _ray_polygon_hit(' not in text:
        raise ValueError('Unbekannter AISI-Bodenpfeil-Callback')
    if NEW in text and OLD not in text:
        result = text
    elif text.count(OLD) == 1:
        result = text.replace(OLD, NEW)
    else:
        raise ValueError('Unbekannter AISI-Bodenpfeil-Endpunkt')
    if result.count(OLD_VISIBILITY) == 1:
        result = result.replace(OLD_VISIBILITY, NEW_VISIBILITY)
    elif result.count(NEW_VISIBILITY) != 1:
        raise ValueError('Unbekannte AISI-Bodenpfeil-Sichtbarkeit')
    compile(result, RELATIVE_PATH, 'exec')
    return result


def restore_aisi_floor_arrow_endpoint(resolve):
    root = resolve(ROOT)
    backup = root.fetch(BACKUP_KEY, None) if root is not None else None
    if backup is None or any(resolve(path) is None for path, text in backup):
        raise ValueError('Rückfallkopie oder Callback fehlt')
    for path, text in backup:
        resolve(path).text = text
    return {'restored_callbacks': len(backup), 'saved': False}


def repair_aisi_floor_arrow_endpoint(resolve):
    root = resolve(ROOT)
    if root is None:
        raise ValueError('AISI-COMP fehlt')
    items = [root.op('table_template')] + [child for child in root.children
             if child.name.startswith('item') and child.name[4:].isdigit()]
    if items[0] is None or len(items) < 2:
        raise ValueError('Template oder Tischinstanzen fehlen')
    callbacks = [item.op(RELATIVE_PATH) for item in items]
    if any(node is None for node in callbacks):
        raise ValueError('Bodenpfeil-Callback fehlt')
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
    print(repair_aisi_floor_arrow_endpoint(_resolve))
    print('AISI-Bodenpfeil bis Zielmitte, auch bei Teil-Overlap außerhalb der Source. Kein Force-Cook, keine Speicherung.')
    print('Rücknahme: restore_aisi_floor_arrow_endpoint(op)')
