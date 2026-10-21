"""AISI-Positionsumsetzung an Tracking angleichen; manuell, ohne Speichern."""

import re


ROOT = '/project1/comp_layout_proposal'
BACKUP_KEY = 'aisi_world_axes_before_repair'
TABLE_CALLBACK = ROOT + '/tables_active_callbacks'
CHAIR_CALLBACK = ROOT + '/chairs/chairs_active_callbacks'


def corrected_callbacks(table_text, chair_text):
    """Nur die vier Tisch- und zwei Chair-Positionsausdrücke ersetzen."""
    replacements = (
        (r"\(\s*values\['source_x'\] - ROI_CENTER_CM\s*\) \* TD_SCALE",
         "(ROI_CENTER_CM - values['source_x']) * TD_SCALE"),
        (r"-\(\s*values\['source_y'\] - ROI_CENTER_CM\s*\) \* TD_SCALE",
         "(values['source_y'] - ROI_CENTER_CM) * TD_SCALE"),
        (r"\(\s*values\['target_x'\] - ROI_CENTER_CM\s*\) \* TD_SCALE",
         "(ROI_CENTER_CM - values['target_x']) * TD_SCALE"),
        (r"-\(\s*values\['target_y'\] - ROI_CENTER_CM\s*\) \* TD_SCALE",
         "(values['target_y'] - ROI_CENTER_CM) * TD_SCALE"),
    )
    for pattern, replacement in replacements:
        if replacement in table_text:
            continue
        table_text, count = re.subn(pattern, lambda _: replacement, table_text)
        if count != 1:
            raise ValueError('Unbekannte/mehrdeutige Tisch-Positionsumsetzung')
    for before, after in (
        ('(x - 250.0) * 0.0052', '(250.0 - x) * 0.0052'),
        ('-(y - 250.0) * 0.0052', '(y - 250.0) * 0.0052'),
    ):
        if before not in chair_text and after in chair_text:
            continue
        if chair_text.count(before) != 1:
            raise ValueError('Unbekannte/mehrdeutige Chair-Positionsumsetzung')
        chair_text = chair_text.replace(before, after)
    compile(table_text, TABLE_CALLBACK, 'exec')
    compile(chair_text, CHAIR_CALLBACK, 'exec')
    return table_text, chair_text


def restore_aisi_world_axes(resolve):
    root = resolve(ROOT)
    backup = root.fetch(BACKUP_KEY, None) if root is not None else None
    if backup is None:
        raise ValueError('Keine Rückfallkopie vorhanden')
    nodes = [resolve(path) for path in (TABLE_CALLBACK, CHAIR_CALLBACK)]
    if any(node is None for node in nodes):
        raise ValueError('Callback für Rücknahme fehlt')
    for node, text in zip(nodes, backup):
        node.text = text
    return {'restored_callbacks': 2, 'saved': False}


def repair_aisi_world_axes(resolve):
    root = resolve(ROOT)
    nodes = [resolve(path) for path in (TABLE_CALLBACK, CHAIR_CALLBACK)]
    if root is None or any(node is None for node in nodes):
        raise ValueError('AISI-Daten-Callbacks fehlen')
    original = tuple(node.text for node in nodes)
    corrected = corrected_callbacks(*original)  # Vollständig vor Mutation prüfen.
    if root.fetch(BACKUP_KEY, None) is None:
        root.store(BACKUP_KEY, original)
    try:
        for node, text in zip(nodes, corrected):
            node.text = text
    except Exception:
        for node, text in zip(nodes, original):
            node.text = text
        raise
    return {'changed_callbacks': sum(a != b for a, b in zip(original, corrected)),
            'forced_cook': False, 'saved': False}


try:
    _resolve = op
except NameError:
    if __name__ == '__main__':
        raise RuntimeError('Im TouchDesigner-Textport ausführen')
else:
    print(repair_aisi_world_axes(_resolve))
    print('Nur AISI-Positionen geändert. Kein Force-Cook und keine Speicherung.')
    print('Rücknahme: restore_aisi_world_axes(op)')
