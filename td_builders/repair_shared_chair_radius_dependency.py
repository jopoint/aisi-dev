"""Manuelle, rücknehmbare Ring-Radius-Bindung; kein Force-Cook/Speichern."""
import json

ROOT = '/project1/comp_layout_proposal/chairs'
BACKUP_KEY = 'ring_radius_dependency_before_repair'
OLD_RADIUS = 'r_outer = float(template.par.Radius.eval())'
NEW_RADIUS = 'r_outer = float(scriptOp.par.Valuea.eval())'
RADIUS_EXPRESSION = 'parent(2).par.Radius.eval()'


def targets(chairs):
    result = []
    for name in ['chairs_template'] + ['item%d' % i for i in range(1, 16)]:
        instance = chairs.op(name)
        if instance is None:
            raise ValueError('Chair-Basis fehlt: ' + name)
        ring = instance.op('chair_geo/chair_ring')
        callback = instance.op('chair_geo/chair_ring_callbacks')
        if ring is None or callback is None or getattr(ring.par, 'Valuea', None) is None:
            raise ValueError('Ring/Callback/Valuea fehlt: ' + name)
        if OLD_RADIUS not in callback.text and NEW_RADIUS not in callback.text:
            raise ValueError('Unbekannter Ring-Callback: ' + name)
        if OLD_RADIUS in callback.text and callback.text.count(OLD_RADIUS) != 1:
            raise ValueError('Mehrdeutiger Ring-Callback: ' + name)
        if 'constant' not in str(ring.par.Valuea.mode).lower() and 'expression' not in str(ring.par.Valuea.mode).lower():
            raise ValueError('Valuea besitzt eine geschützte Bindung/Export: ' + name)
        result.append((instance, ring, callback))
    return result


def restore_radius_dependency(resolve):
    chairs = resolve(ROOT)
    backup = chairs.fetch(BACKUP_KEY, None)
    if backup is None:
        raise ValueError('Keine Rückfallkopie dieser Radius-Reparatur vorhanden.')
    for saved in backup:
        ring = resolve(saved['ring'])
        callback = resolve(saved['callback'])
        if ring is None or callback is None:
            raise ValueError('Rückfallziel fehlt: ' + saved['ring'])
    for saved in backup:
        ring = resolve(saved['ring'])
        resolve(saved['callback']).text = saved['text']
        ring.par.Valuea.expr = saved['expression'] or ''
        if not saved['expression']:
            ring.par.Valuea.val = saved['value']
    return {'restored_rings': len(backup), 'saved': False}


def repair_radius_dependency(resolve, project_name):
    chairs = resolve(ROOT)
    if chairs is None:
        raise ValueError('chairs COMP fehlt')
    nodes = targets(chairs)  # Alle Ziele prüfen, bevor etwas geändert wird.
    if chairs.fetch(BACKUP_KEY, None) is None:
        chairs.store(BACKUP_KEY, [
            {'ring': ring.path, 'callback': callback.path, 'text': callback.text,
             'expression': ring.par.Valuea.expr, 'value': float(ring.par.Valuea.eval())}
            for _, ring, callback in nodes
        ])
    try:
        for _, ring, callback in nodes:
            ring.par.Valuea.expr = RADIUS_EXPRESSION
            callback.text = callback.text.replace(OLD_RADIUS, NEW_RADIUS)
        for instance, ring, callback in nodes:
            if ring.par.Valuea.expr != RADIUS_EXPRESSION or NEW_RADIUS not in callback.text:
                raise ValueError('Radius-Bindung nicht übernommen: ' + instance.name)
            if abs(float(ring.par.Valuea.eval()) - float(instance.par.Radius.eval())) > 1e-7:
                raise ValueError('Radius-Wert weicht ab: ' + instance.name)
        return {'project': project_name, 'bound_rings': len(nodes),
                'includes_template': True, 'forced_cook': False, 'saved': False}
    except Exception:
        restore_radius_dependency(resolve)
        raise


try:
    _td_resolve = op
    _td_project_name = project.name
except NameError:
    if __name__ == '__main__':
        raise RuntimeError('Im TouchDesigner-Python-Textport ausführen.')
else:
    print(json.dumps(repair_radius_dependency(_td_resolve, _td_project_name), indent=2))
    print('Radius-Abhängigkeit für Template und 15 Instanzen gebunden. '
          'Kein Force-Cook, keine Datei gespeichert. Jetzt 9 → 10 → 9 → 10 prüfen.')
    print('Rücknahme bei Bedarf: restore_radius_dependency(op)')
