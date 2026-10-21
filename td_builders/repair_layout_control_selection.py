"""Nur die Geometry-Auswahl des Kontroll-Renderers reparieren; kein Speichern."""

ROOT = '/project1/comp_layout_proposal/floor_tabletop_control'
RENDERER = ROOT + '/render_source_and_tabletop_motion'
BACKUP_KEY = 'control_geometry_selection_before_repair'
LAYOUT = '/project1/comp_layout_proposal'


def geometry_paths():
    return ' '.join(LAYOUT + '/item%d/' % index + role
                    for index in range(1, 6)
                    for role in ('table_source_geo', 'table_motion_line_tabletop_geo'))


def _restore_parameter(par, before):
    value, expression, binding, mode = before
    par.val = value
    par.expr = expression or ''
    par.bindExpr = binding or ''
    par.mode = mode


def restore_layout_control_selection(resolve):
    root, renderer = resolve(ROOT), resolve(RENDERER)
    backup = root.fetch(BACKUP_KEY, None) if root is not None else None
    if backup is None or renderer is None:
        raise ValueError('Kontroll-Renderer oder Rückfallkopie fehlt')
    par = renderer.par.geometry
    _restore_parameter(par, backup)
    return {'restored': True, 'saved': False}


def repair_layout_control_selection(resolve):
    root, renderer = resolve(ROOT), resolve(RENDERER)
    if root is None or renderer is None:
        raise ValueError('Bestehender Kontroll-Renderer fehlt')
    expected = []
    for index in range(1, 6):
        source = resolve(LAYOUT + '/item%d/table_source_geo' % index)
        if source is not None:
            expected.append(source.path)
    if not expected:
        raise ValueError('Keine bestehenden Source-Geometrien gefunden')
    par = renderer.par.geometry
    if not any(mode in str(par.mode).lower() for mode in ('constant', 'expression')):
        raise ValueError('Geometry-Parameter besitzt eine Bindung/Export')
    before = (par.val, par.expr, par.bindExpr, par.mode)
    if root.fetch(BACKUP_KEY, None) is None:
        root.store(BACKUP_KEY, before)
    try:
        renderer.par.geometry = geometry_paths()
        value = renderer.par.geometry.eval()
        if isinstance(value, (tuple, list)):
            selected = [node.path for node in value]
        elif hasattr(value, 'path'):
            selected = [value.path]
        else:
            raise ValueError('Native Geometry-Auswahl noch leer: ' + str(value))
        if not set(expected).issubset(selected):
            raise ValueError('Source-Geometrien fehlen weiterhin in der Auswahl')
    except Exception:
        _restore_parameter(par, before)
        raise
    return {'source_geometries_selected': len(expected), 'selected': selected,
            'forced_cook': False, 'saved': False, 'projector_changes': False}


try:
    _resolve = op
except NameError:
    if __name__ == '__main__':
        raise RuntimeError('Im TouchDesigner-Python-Textport ausführen')
else:
    print(repair_layout_control_selection(_resolve))
    print('Nur Kontroll-Renderer-Auswahl geändert. Kein Force-Cook, keine Speicherung.')
    print('Rücknahme: restore_layout_control_selection(op)')
