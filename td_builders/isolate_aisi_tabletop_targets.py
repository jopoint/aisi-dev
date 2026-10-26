"""Textport: AISI-Zielkonturen nur auf dem zugehörigen physischen Tisch.

Eigener Renderzweig vor dem bestehenden Tabletop-Ausgang. Keine Änderung an
Geometrie, OSC, Floor, physischer Maske, Kalibrierung oder Projektoren.
Kein Force-Cook, kein Speichern. Rücknahme auch nach erneutem Öffnen möglich.
"""

import builtins
import json
import sys


ROOT = '/project1/comp_layout_proposal'
BRANCH = 'aisi_own_tabletop_targets'
BACKUP = 'aisi_own_tabletop_targets_backup_v1'
OSC = '/project1/comp_io/null_osc_raw'


def mode_expression():
    return ("(lambda raw: raw is not None and raw['study/mode'] is not None "
            "and raw['study/mode'].eval() == 2)(op(%r))" % OSC)


def base_geometry_paths():
    """Native absolute Auswahl: kopierte parent()-Expressions wären kontextfalsch."""
    return ' '.join(ROOT + '/item%d/' % index + role for index in range(1, 6)
                    for role in ('table_source_geo', 'table_motion_line_tabletop_geo'))


def _selection_paths(parameter):
    value = parameter.eval()
    if isinstance(value, (tuple, list)):
        return [node.path for node in value if node is not None]
    if hasattr(value, 'path'):
        return [value.path]
    # Kein String-Fallback: in TD muss die Auswahl reale Operatoren auflösen.
    raise ValueError('Render-Geometrieauswahl ist nicht aufgelöst: ' + str(value))


def presence_expression(index):
    """Slot bleibt an den letzten Vorschlag gebunden, auch bei Tischabgang."""
    if index not in range(5):
        raise ValueError('Nur Slots 0–4 sind unterstützt')
    return ("int((lambda raw: raw is not None and raw['table/count'] is not None "
            "and raw['table/count'].eval() > %d and "
            "(raw['table/%d/source_available'] is None or "
            "raw['table/%d/source_available'].eval() == 1))(op(%r)))"
            % (index, index, index, OSC))


def _symbol(name):
    return (globals().get(name) or getattr(builtins, name, None)
            or getattr(sys.modules.get('__main__'), name, None))


def _configure_transparent(node):
    # Constant TOP verwendet je nach Version „alpha“ statt „colora“.
    # Keine ParCollection-Namen erfinden: erst alle Kanäle auflösen.
    parameters = []
    for names in (('colorr', 'color0r'), ('colorg', 'color0g'),
                  ('colorb', 'color0b'), ('alpha', 'colora', 'color0a')):
        parameter = next((getattr(node.par, name, None) for name in names
                          if getattr(node.par, name, None) is not None), None)
        if parameter is None:
            raise ValueError('Constant-TOP-Farbparameter fehlt (%s). Vorhanden: %s'
                             % ('/'.join(names), ', '.join(p.name for p in node.pars())))
        parameters.append(parameter)
    for parameter in parameters:
        parameter.val = 0


def _one_op(parameter, owner):
    value = parameter.eval()
    if isinstance(value, (tuple, list)):
        if len(value) != 1:
            raise ValueError('Genau eine Tabletop-Kamera benötigt')
        value = value[0]
    node = value if hasattr(value, 'path') else owner.op(str(value))
    if node is None:
        raise ValueError('Tabletop-Kamera fehlt')
    return node


def _snapshot(nodes):
    """Nur Einstellungen prüfen, keine Bilder kochen oder Livewerte abfragen."""
    return {node.path: (
        tuple(n.path for n in node.inputs),
        tuple((p.name, str(p.mode), p.expr, p.bindExpr,
               str(p.val) if 'constant' in str(p.mode).lower() else None)
              for p in node.pars() if p.style != 'Pulse')) for node in nodes}


def _protected_nodes(resolve):
    nodes = []
    for path in ('/project1/comp_output', '/project1/comp_calibration',
                 '/project1/comp_tabletop_calibration'):
        comp = resolve(path)
        if comp is None:
            raise ValueError('Geschützter Projektionsbereich fehlt: ' + path)
        nodes.append(comp)
        nodes.extend(comp.findChildren())
    for name in ('render_floor', 'render_tabletop', 'render_table_mask',
                 'null_table_mask', 'reorder_table_mask', 'level_invert_mask',
                 'mask_tabletop', 'null_tabletop', 'cam1'):
        node = resolve(ROOT + '/' + name)
        if node is None:
            raise ValueError('Bestehender Operator fehlt: ' + name)
        nodes.append(node)
    return nodes


def _copy_renderer(branch, source, name, camera, geometry):
    render = branch.copy(source, name=name, includeDocked=False)
    render.par.camera = camera.path
    render.par.geometry = geometry
    # Relative Kamera-/Lichtpfade der Kopie nicht versehentlich neu auflösen.
    lights = source.par.lights.eval()
    if isinstance(lights, (list, tuple)):
        render.par.lights = ' '.join(node.path for node in lights)
    elif hasattr(lights, 'path'):
        render.par.lights = lights.path
    elif lights:
        raise ValueError('Lichtauswahl nicht eindeutig auflösbar')
    else:
        render.par.lights = ''
    for parameter in ('resmode', 'resw', 'resh', 'resmult', 'pixelformat'):
        if getattr(source.par, parameter, None) is not None:
            render.par[parameter].expr = 'op(%r).par.%s.eval()' % (source.path, parameter)
    return render


def restore_aisi_tabletop_targets(resolve):
    root = resolve(ROOT)
    backup = root.fetch(BACKUP, None) if root is not None else None
    if backup is None:
        raise ValueError('Keine Tabletop-Rückfallkopie vorhanden')
    output, original = resolve(backup['output']), resolve(backup['original'])
    if output is None or original is None:
        raise ValueError('Ursprünglicher Tabletop-Pfad fehlt')
    output.inputConnectors[0].connect(original)
    branch = root.op(BRANCH)
    if branch is not None:
        branch.destroy()
    root.store(BACKUP, None)
    return {'restored': True, 'saved': False}


def activate_aisi_tabletop_targets(resolve):
    root = resolve(ROOT)
    branch = root.op(BRANCH) if root is not None else None
    backup = root.fetch(BACKUP, None) if root is not None else None
    if branch is None or backup is None:
        raise ValueError('Vorbereiteter Zweig fehlt')
    errors = [(node.path, node.errors()) for node in branch.findChildren() if node.errors()]
    if errors:
        raise ValueError('Tabletop-Vorschau meldet Fehler: ' + str(errors))
    output, original = resolve(backup['output']), resolve(backup['original'])
    if output.inputs not in ([original], [branch.op('select_mode')]):
        raise ValueError('Ausgang wurde zwischenzeitlich anderweitig geändert')
    output.inputConnectors[0].connect(branch.op('select_mode'))
    return {'activated': True, 'saved': False}


def isolate_aisi_tabletop_targets(resolve, symbols, activate=True):
    root = resolve(ROOT)
    if root is None:
        raise ValueError('Layout-COMP fehlt')
    existing = root.op(BRANCH)
    output = root.op('null_tabletop_masked')
    if existing is not None:
        if root.fetch(BACKUP, None) and output is not None and output.inputs == [existing.op('select_mode')]:
            if existing.fetch('revision', None) == 2:
                return {'already_applied': True, 'saved': False}
            # Eigene alte fehlerhafte Version zuerst auf Original zurücknehmen.
            restore_aisi_tabletop_targets(resolve)
        elif existing.fetch('revision', None) == 2 and output.inputs == [root.op('mask_tabletop')]:
            return {'already_prepared': True, 'activated': False, 'saved': False}
        else:
            raise ValueError('Gleichnamiger Zweig existiert; nichts überschrieben')
    renderer, mask_render = root.op('render_tabletop'), root.op('render_table_mask')
    mask, reorder = root.op('mask_tabletop'), root.op('reorder_table_mask')
    if any(n is None for n in (output, renderer, mask_render, mask, reorder)):
        raise ValueError('Bestehender Tabletop-/Maskenpfad unvollständig')
    if output.inputs != [mask] or mask.inputs != [root.op('null_tabletop'), root.op('null_table_mask')]:
        raise ValueError('Unerwartete Tabletop-Verschaltung; nichts geändert')
    if 'expression' not in str(renderer.par.geometry.mode).lower() or not renderer.par.geometry.expr:
        raise ValueError('Modusabhängige Tabletop-Geometrieexpression fehlt')
    camera = _one_op(renderer.par.camera, renderer)
    if _one_op(mask_render.par.camera, mask_render).path != camera.path:
        raise ValueError('Inhalts- und Maskenkamera unterscheiden sich')
    if reorder.inputs != [mask_render]:
        raise ValueError('Unerwarteter Masken-Reorder')
    items = [root.op('item%d' % i) for i in range(1, 6)]
    active_items = [item for item in items if item is not None]
    if not active_items or any(item.op(role) is None for item in active_items
                               for role in ('table_mask_geo', 'table_target_tabletop_geo')):
        raise ValueError('Tischinstanzen mit bestehenden Flächenmasken fehlen')
    protected = _protected_nodes(resolve)
    before = _snapshot(protected)
    backup = {'output': output.path, 'original': mask.path}
    branch = root.create(symbols['baseCOMP'], BRANCH)
    try:
        branch.nodeX, branch.nodeY = output.nodeX - 200, output.nodeY - 300
        blank = branch.create(symbols['constantTOP'], 'transparent')
        _configure_transparent(blank)
        base = _copy_renderer(branch, renderer, 'render_sources_and_motion', camera, base_geometry_paths())
        expected_sources = {item.op('table_source_geo').path for item in active_items
                            if item.op('table_source_geo') is not None}
        if not expected_sources or not expected_sources.issubset(_selection_paths(base.par.geometry)):
            raise ValueError('Source-Auswahl im neuen Zweig unvollständig; Ausgang bleibt unverändert')
        base_masked = branch.copy(mask, name='mask_sources_and_motion', includeDocked=False)
        base_masked.inputConnectors[0].connect(base)
        base_masked.inputConnectors[1].connect(root.op('null_table_mask'))
        combined = base_masked
        for index in range(5):
            prefix = 'slot%d_' % index
            item_path = ROOT + '/item%d' % (index + 1)
            target = _copy_renderer(branch, renderer, prefix + 'render_target', camera,
                                    item_path + '/table_target_tabletop_geo')
            surface = _copy_renderer(branch, mask_render, prefix + 'render_surface', camera,
                                     item_path + '/table_mask_geo')
            if items[index] is not None:
                if _selection_paths(target.par.geometry) != [item_path + '/table_target_tabletop_geo']:
                    raise ValueError('Zielauswahl nicht aufgelöst: ' + item_path)
                if _selection_paths(surface.par.geometry) != [item_path + '/table_mask_geo']:
                    raise ValueError('Source-Maskenauswahl nicht aufgelöst: ' + item_path)
            own_mask = branch.copy(reorder, name=prefix + 'surface_mask', includeDocked=False)
            own_mask.inputConnectors[0].connect(surface)
            clipped = branch.copy(mask, name=prefix + 'clip_target', includeDocked=False)
            clipped.inputConnectors[0].connect(target)
            clipped.inputConnectors[1].connect(own_mask)
            visible = branch.create(symbols['switchTOP'], prefix + 'source_available')
            visible.inputConnectors[0].connect(blank)
            visible.inputConnectors[1].connect(clipped)
            visible.par.index.expr = presence_expression(index)
            added = branch.create(symbols['compositeTOP'], prefix + 'add')
            added.par.operand = 'add'
            added.inputConnectors[0].connect(combined)
            added.inputConnectors[1].connect(visible)
            combined = added
        selector = branch.create(symbols['switchTOP'], 'select_mode')
        selector.inputConnectors[0].connect(mask)
        selector.inputConnectors[1].connect(combined)
        selector.par.index.expr = 'int(%s)' % mode_expression()
        # Erst den fertigen Zweig anschließen. Physische Maske/Projektoren bleiben unverändert.
        root.store(BACKUP, backup)
        branch.store('revision', 2)
        if activate:
            output.inputConnectors[0].connect(selector)
        if before != _snapshot(protected):
            raise ValueError('Geschützte Einstellungen verändert; Rücknahme')
    except Exception:
        output.inputConnectors[0].connect(mask)
        branch.destroy()
        root.store(BACKUP, None)
        raise
    return {'prepared': True, 'activated': activate, 'slots': 5, 'target_renderers': 5, 'surface_renderers': 5,
            'source_geometries_selected': len(expected_sources),
            'protected_settings_unchanged': True, 'forced_cook': False, 'saved': False,
            'study_tracking_original_path': True}


_resolve = _symbol('op')
if callable(_resolve):
    raise RuntimeError('Renderzweig wegen Live-Performance verworfen. Bestehenden Zweig mit '
                       'restore_aisi_tabletop_targets(op) entfernen; anschließend '
                       'clip_aisi_tabletop_targets.py verwenden.')
elif __name__ == '__main__':
    raise RuntimeError('Im TouchDesigner-Python-Textport ausführen')
