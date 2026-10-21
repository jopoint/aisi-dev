"""Manuelle AISI-Pfeiltoleranz und schrumpfende Spitzen; kein Speichern."""

ROOT = '/project1/comp_layout_proposal'
BACKUP_KEY = 'aisi_arrow_arrival_before_repair'
MARKER = '# aisi_arrow_arrival_v1'
WRAPPER = '''
# aisi_arrow_arrival_v1
def points():
    result = _aisi_points_before_arrival()
    template = parent(2)
    distance = math.hypot(template.par.Targetx.eval() - template.par.X.eval(),
                          template.par.Targety.eval() - template.par.Y.eval())
    rotation_error = abs((template.par.Targetrot.eval() - template.par.Rot.eval() + 90.0) % 180.0 - 90.0)
    # Gleiche Pose-Toleranzen wie Study; keine zeitliche Arrival-Bestätigung.
    arrived = distance <= 8.0 * 0.0052 and rotation_error <= 5.0
    if arrived:
        result['visible'] = False
        result['length'] = 0.0
    result['head_length'] = min(0.075, result['length'] / 2.0) if result['visible'] else 0.0
    return result
'''


def corrected_source(text):
    if MARKER in text:
        if not text.endswith(WRAPPER):
            raise ValueError('Abweichende bestehende AISI-Toleranzkorrektur')
        return text
    if text.count('def points():') != 1 or 'import math' not in text:
        raise ValueError('Unbekannter AISI-Pfeil-Callback')
    result = text.replace('def points():', 'def _aisi_points_before_arrival():') + WRAPPER
    compile(result, 'aisi_arrow_arrival', 'exec')
    return result


def _targets(root):
    items = [root.op('table_template')] + [child for child in root.children
             if child.name.startswith('item') and child.name[4:].isdigit()]
    if items[0] is None or len(items) < 2:
        raise ValueError('Template oder Instanzen fehlen')
    callbacks, parameters = [], []
    for item in items:
        for surface in ('floor', 'tabletop'):
            geo = item.op('table_motion_line_%s_geo' % surface)
            helper_name = 'motion_%s_helpers' % surface
            callback = geo.op(helper_name) if geo is not None else None
            if callback is None:
                raise ValueError('Pfeil-Callback fehlt: ' + item.path)
            callbacks.append(callback)
            head_length = "op('%s').module.points()['head_length']" % helper_name
            for name in ('head_upper_rect', 'head_lower_rect'):
                node = geo.op(name)
                if node is None:
                    raise ValueError('Pfeilspitze fehlt: ' + geo.path)
                for par_name, original, expression in (
                    ('sizex', .075, head_length), ('tx', -.0375, '-0.5 * (' + head_length + ')'),
                ):
                    par = getattr(node.par, par_name, None)
                    if par is None:
                        raise ValueError('Spitzenparameter fehlt')
                    mode = str(par.mode).lower()
                    if 'constant' in mode:
                        if abs(float(par.eval()) - original) > 1e-8:
                            raise ValueError('Unerwartete Spitzenabmessung: ' + node.path)
                    elif 'expression' not in mode or par.expr != expression:
                        raise ValueError('Spitzenparameter hat unbekannte Bindung: ' + node.path)
                    parameters.append((node, par_name, par, expression))
    return callbacks, parameters


def _restore(resolve, backup):
    if any(resolve(path) is None for path, text in backup['callbacks']):
        raise ValueError('Callback für Rücknahme fehlt')
    if any(resolve(path) is None for path, name, val, expr, mode in backup['parameters']):
        raise ValueError('Spitzenoperator für Rücknahme fehlt')
    for path, text in backup['callbacks']:
        resolve(path).text = text
    for path, name, val, expr, mode in backup['parameters']:
        par = getattr(resolve(path).par, name)
        par.val = val
        par.expr = expr
        par.mode = mode


def restore_aisi_arrow_arrival(resolve):
    root = resolve(ROOT)
    backup = root.fetch(BACKUP_KEY, None) if root is not None else None
    if backup is None:
        raise ValueError('Keine Rückfallkopie vorhanden')
    _restore(resolve, backup)
    return {'restored': True, 'saved': False}


def repair_aisi_arrow_arrival(resolve):
    root = resolve(ROOT)
    if root is None:
        raise ValueError('AISI-COMP fehlt')
    callbacks, parameters = _targets(root)
    texts = [corrected_source(node.text) for node in callbacks]
    before = {'callbacks': [(node.path, node.text) for node in callbacks],
              'parameters': [(node.path, name, par.val, par.expr, par.mode)
                             for node, name, par, expression in parameters]}
    if root.fetch(BACKUP_KEY, None) is None:
        root.store(BACKUP_KEY, before)
    try:
        for node, text in zip(callbacks, texts):
            node.text = text
        for node, name, par, expression in parameters:
            par.expr = expression
    except Exception:
        _restore(resolve, before)
        raise
    return {'callbacks': len(callbacks), 'tip_parameters': len(parameters),
            'forced_cook': False, 'saved': False}


try:
    _resolve = op
except NameError:
    if __name__ == '__main__':
        raise RuntimeError('Im TouchDesigner-Python-Textport ausführen')
else:
    print(repair_aisi_arrow_arrival(_resolve))
    print('AISI-Pfeile: 8 cm / 5 Grad, schrumpfende Spitzen. Keine Speicherung.')
    print('Rücknahme: restore_aisi_arrow_arrival(op)')
