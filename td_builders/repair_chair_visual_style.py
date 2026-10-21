"""Chair-Ringe weiß und so stark wie Zielkonturen; manuell, ohne Speichern."""

import re

ROOT = '/project1/comp_layout_proposal/chairs'
STYLE = '/project1/comp_layout_proposal/aisi_table_visual_style'
BACKUP_KEY = 'chair_visual_style_before_repair'


def corrected_ring_source(text, thickness_td):
    if not 0 < thickness_td < .13:
        raise ValueError('Unplausible Konturstärke')
    result, count = re.subn(r'^THICKNESS = [^\n]+',
                            'THICKNESS = %.10g  # Stärke der Ziel-Tischkonturen' % thickness_td,
                            text, flags=re.MULTILINE)
    if count != 1 or 'r_inner = max(r_outer - THICKNESS, 0.001)' not in text:
        raise ValueError('Unbekannter Chair-Ring-Callback')
    compile(result, 'chair_ring_callbacks', 'exec')
    return result


def _restore(resolve, backup):
    if any(resolve(path) is None for path, text in backup['texts']):
        raise ValueError('Ring-Callback für Rücknahme fehlt')
    material = resolve(backup['material'])
    if material is None:
        raise ValueError('Chair-Material für Rücknahme fehlt')
    for path, text in backup['texts']:
        resolve(path).text = text
    for name, value, expression, mode in backup['colors']:
        par = getattr(material.par, name)
        par.val = value
        par.expr = expression
        par.mode = mode


def restore_chair_visual_style(resolve):
    root = resolve(ROOT)
    backup = root.fetch(BACKUP_KEY, None) if root is not None else None
    if backup is None:
        raise ValueError('Keine Chair-Style-Rückfallkopie vorhanden')
    _restore(resolve, backup)
    return {'restored': True, 'saved': False}


def repair_chair_visual_style(resolve):
    root, style = resolve(ROOT), resolve(STYLE)
    if root is None or style is None:
        raise ValueError('Chair-COMP oder gemeinsamer Zielkontur-Style fehlt')
    thickness_cm = float(style.module.OUTLINE_THICKNESS_CM)
    thickness_td = thickness_cm * float(style.module.TD_UNITS_PER_CM)
    material = root.op('mat_chair_orange')
    if material is None:
        raise ValueError('Bestehendes Chair-Material fehlt')
    callbacks = []
    for name in ['chairs_template'] + ['item%d' % i for i in range(1, 16)]:
        item = root.op(name)
        geo = item.op('chair_geo') if item is not None else None
        callback = item.op('chair_geo/chair_ring_callbacks') if item is not None else None
        bound = geo.par.material.eval() if geo is not None else None
        if geo is None or callback is None or getattr(bound, 'path', str(bound)) != material.path:
            raise ValueError('Chair-Struktur/Material abweichend: ' + name)
        callbacks.append(callback)
    texts = [corrected_ring_source(node.text, thickness_td) for node in callbacks]
    colors = [getattr(material.par, name) for name in ('colorr', 'colorg', 'colorb')]
    if any('constant' not in str(par.mode).lower() for par in colors):
        raise ValueError('Chair-Materialfarbe besitzt eine Bindung')
    backup = {'texts': [(node.path, node.text) for node in callbacks],
              'material': material.path,
              'colors': [(par.name, par.val, par.expr, par.mode) for par in colors]}
    if root.fetch(BACKUP_KEY, None) is None:
        root.store(BACKUP_KEY, backup)
    try:
        for node, text in zip(callbacks, texts):
            node.text = text
        for par in colors:
            par.val = 1.0
    except Exception:
        _restore(resolve, backup)
        raise
    return {'rings': len(callbacks), 'color': 'white', 'thickness_cm': thickness_cm,
            'forced_cook': False, 'saved': False}


try:
    _resolve = op
except NameError:
    if __name__ == '__main__':
        raise RuntimeError('Im TouchDesigner-Python-Textport ausführen')
else:
    print(repair_chair_visual_style(_resolve))
    print('Chair-Ringe weiß, Stärke aus Zielkontur-Style. Keine Speicherung.')
    print('Rücknahme: restore_chair_visual_style(op)')
