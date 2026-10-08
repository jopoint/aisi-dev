"""Textport: isolierter Floor-/Tabletop-Kontrollviewer, ohne Speichern.

Bestehende Geometrien, Kamera und Floor-TOP werden ausschließlich referenziert.
Keine Verbindungen zu comp_output und keine Änderung bestehender Operatoren.
"""
import json
import builtins
import sys

LAYOUT_PATH = '/project1/comp_layout_proposal'
CONTROL_NAME = 'floor_tabletop_control'
ROLES = ('table_source_geo', 'table_motion_line_tabletop_geo')


def geometry_expression():
    """Resolve the five supported table slots directly, without a child scan."""
    slots = ', '.join('op(%r)' % (LAYOUT_PATH+'/item%d' % index) for index in range(1,6))
    return (
        "' '.join(geo.path for item in (%s) "
        "if item is not None and item.par.Tabletype.eval() == 'rect' "
        "for name in %r for geo in [item.op(name)] if geo is not None)"
        % (slots, ROLES)
    )


def update_control_selection(resolve):
    """Update only this viewer's selection; preserve its nodes and settings."""
    comp = resolve(LAYOUT_PATH+'/'+CONTROL_NAME)
    overlay = comp.op('render_source_and_tabletop_motion') if comp is not None else None
    if overlay is None:
        raise RuntimeError('Bestehender Kontroll-Renderer fehlt; nichts geändert.')
    previous = (overlay, overlay.par.geometry.expr, overlay.par.geometry.mode)
    overlay.par.geometry.expr = geometry_expression()
    return previous, {'control': comp.path, 'updated': overlay.path,
                      'table_slots': 5, 'selection': 'explicit_item_paths', 'saved': False}


def create_control(resolve, symbols):
    layout = resolve(LAYOUT_PATH)
    if layout is None:
        raise RuntimeError('comp_layout_proposal fehlt.')
    if layout.op(CONTROL_NAME) is not None:
        raise RuntimeError('floor_tabletop_control existiert bereits; vorhandenen COMP erhalten.')
    floor = layout.op('null_floor_with_optional_synth_chairs')
    renderer = layout.op('render_floor')
    if floor is None or renderer is None:
        raise RuntimeError('Bestehender Floor-TOP oder render_floor fehlt.')
    items = [layout.op('item%d' % i) for i in range(1,6)]
    items = [n for n in items if n is not None and n.par.Tabletype.eval() == 'rect']
    if not items or any(item.op(role) is None for item in items for role in ROLES):
        raise RuntimeError('Rect-Instanzen mit Source- und Tabletop-Motion-Geometrie fehlen.')
    camera_value = renderer.par.camera.eval()
    if isinstance(camera_value, (list, tuple)):
        if len(camera_value) != 1:
            raise RuntimeError('Die Kontrollansicht benötigt die bestehende einzelne Floor-Kamera.')
        camera_value = camera_value[0]
    camera = camera_value if hasattr(camera_value, 'path') else renderer.op(str(camera_value))
    if camera is None:
        raise RuntimeError('Vorhandene Floor-Kamera nicht auflösbar.')

    comp = layout.create(symbols['containerCOMP'], CONTROL_NAME)
    try:
        comp.nodeX = floor.nodeX + 300
        comp.nodeY = floor.nodeY - 200
        select = comp.create(symbols['selectTOP'], 'select_existing_floor')
        select.par.top = floor.path
        select.nodeX = 0; select.nodeY = 100
        # Copy render settings only; no table or camera duplicates are created.
        overlay = comp.copy(renderer, name='render_source_and_tabletop_motion', includeDocked=False)
        overlay.par.camera = camera.path
        overlay.par.geometry.expr = geometry_expression()
        for name in ('resmode', 'resw', 'resh', 'resmult', 'pixelformat'):
            parameter = getattr(overlay.par, name, None)
            if parameter is not None and getattr(renderer.par, name, None) is not None:
                parameter.expr = 'op(%r).par.%s.eval()' % (renderer.path, name)
        # The overlay must contribute only its geometry, never a background.
        for name in ('bgcolorr', 'bgcolorg', 'bgcolorb', 'bgcolora'):
            parameter = getattr(overlay.par, name, None)
            if parameter is not None:
                parameter.val = 0
        lights = getattr(overlay.par, 'lights', None)
        if lights is not None:
            existing = renderer.par.lights.eval()
            if existing is None or existing == '':
                lights.val = ''
            elif isinstance(existing, (list, tuple)):
                lights.val = ' '.join(n.path for n in existing)
            elif hasattr(existing, 'path'):
                lights.val = existing.path
            elif str(existing).strip():
                resolved = [renderer.op(path) for path in str(existing).split()]
                if any(n is None for n in resolved):
                    raise RuntimeError('Bestehende Render-Lichter nicht auflösbar.')
                lights.val = ' '.join(n.path for n in resolved)
        overlay.nodeX = 0; overlay.nodeY = -100
        composite = comp.create(symbols['compositeTOP'], 'composite_control')
        composite.par.operand = 'add'
        composite.inputConnectors[0].connect(select)
        composite.inputConnectors[1].connect(overlay)
        composite.nodeX = 220; composite.nodeY = 100
        output = comp.create(symbols['outTOP'], 'out_control')
        output.inputConnectors[0].connect(composite)
        output.nodeX = 440; output.nodeY = 100
        comp.par.top = output.path
        comp.par.topfill = 'best'
        comp.par.nodeview = 'opviewer'
        comp.par.opviewer = output.path
        comp.par.w = 700; comp.par.h = 700
        # Keep the panel out of the parent's panel composition; its own viewer
        # and out_control remain available for inspection.
        comp.par.display = False
        return {'control': comp.path, 'output': output.path, 'floor': floor.path,
                'camera': camera.path, 'rect_items': len(items), 'geometry_roles': ROLES,
                'saved': False, 'projector_connections_added': False}
    except Exception:
        # Roll back only the newly created isolated component.
        comp.destroy()
        raise


def _td_symbol(name):
    return (globals().get(name) or getattr(builtins, name, None)
            or getattr(sys.modules.get('__main__'), name, None))


_resolve = _td_symbol('op')
if callable(_resolve):
    _symbols = {name: _td_symbol(name) for name in
                ('containerCOMP', 'selectTOP', 'compositeTOP', 'outTOP')}
    if any(value is None for value in _symbols.values()):
        raise RuntimeError('TouchDesigner-Operatortypen fehlen; bitte im TD-Textport ausführen.')
    if _resolve(LAYOUT_PATH+'/'+CONTROL_NAME) is None:
        _report = create_control(_resolve, _symbols)
    else:
        _aisi_control_geometry_backup, _report = update_control_selection(_resolve)
    print(json.dumps(_report, indent=2))
    print('Kontrolle: floor_tabletop_control (Container COMP) → out_control (Out TOP).')
    print('Keine .toe gespeichert. Keine Projektorausgabe geändert.')
elif __name__ == '__main__':
    raise RuntimeError('Dieses Skript im TouchDesigner-Textport ausführen.')
