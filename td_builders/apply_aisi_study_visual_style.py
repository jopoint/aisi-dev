"""Textport: bestehende AISI-Rect-Konturen an Study angleichen, Floor aktivieren.

Kein Speichern, keine Projektorfenster. Bei Fehlern Änderungen zurückrollen.
"""
import hashlib
import json
import sys
from pathlib import Path

repo = '/Users/Johannes/dev/Promotion_Prototypen/AISI'
if repo not in sys.path:
    sys.path.insert(0, repo)
from td_builders.aisi_study_visual_style import floor_expression, shared_callback_source, adapted_callback

layout = op('/project1/comp_layout_proposal')
study = op('/project1/comp_study_visualization')
floor = layout.op('render_floor')
helper_name = 'aisi_table_visual_style'
assert layout.op(helper_name) is None, 'Style-DAT existiert bereits; nicht erneut ausführen'
raw = op('/project1/comp_io/null_osc_raw')
assert raw['study/mode'].eval() == 2, 'Bitte in der Study Control-UI zuerst AISI wählen'
assert op('/project1/comp_output/panel_mode')['state'].eval() == 0, 'Bitte Calibration ausschalten'
items = [n for n in layout.children if n.name.startswith('item') and n.name[4:].isdigit()]
assert items, 'Keine Tischinstanzen'
roots = [layout.op('table_template')] + items
assert all(n is not None for n in roots)
roles = [('table_source_geo', 'table_outline_inner', 'source_tabletop'),
         ('table_target_floor_geo', 'table_outline_outer', 'target_floor'),
         ('table_target_tabletop_geo', 'table_outline_inner', 'target_tabletop')]
for item in roots:
    for geo_name, sop_name, role in roles:
        geo = item.op(geo_name)
        assert geo is not None and geo.op(sop_name) is not None and geo.op(sop_name + '_callbacks') is not None
        assert geo.op(sop_name + '_callbacks').text.count('def onCook(scriptOp):') == 1


def walk(node):
    yield node
    if node.isCOMP:
        for child in node.children:
            yield from walk(child)


def invariant():
    # Nur Einstellungen vergleichen, keine dynamischen Expressionswerte.
    result = {}
    for path in ['/project1/comp_study_visualization', '/project1/comp_tracking_only',
                 '/project1/comp_output', '/project1/comp_layout_proposal/chairs',
                 '/project1/comp_layout_proposal/table_template/table_mask_geo']:
        root = op(path)
        if root is None:
            continue
        for node in walk(root):
            result[node.path] = {
                'inputs': [s.path for s in node.inputs],
                'pars': [(p.name, str(p.mode), p.expr, str(p.val) if str(p.mode) == 'ParMode.CONSTANT' else None) for p in node.pars()],
                'text': node.text if node.isDAT else None,
            }
    for item in items:
        for node in walk(item.op('table_mask_geo')):
            result[node.path] = {'pars': [(p.name, str(p.mode), p.expr, str(p.val) if str(p.mode) == 'ParMode.CONSTANT' else None) for p in node.pars()],
                                 'text': node.text if node.isDAT else None}
    return result


def image_hash(path):
    node = op(path)
    node.cook(force=True)
    assert not node.errors(), path + ': ' + node.errors()
    return hashlib.sha256(node.numpyArray(delayed=False).tobytes()).hexdigest()

protected_before = invariant()
chair_path = layout.op('render_synth_chairs_regular_floor').path
chair_before = image_hash(chair_path)
mask_path = '/project1/comp_output/switch_table_mask'
mask_before = image_hash(mask_path)
old_floor_expression = floor.par.geometry.expr
assert old_floor_expression, 'Floor-Expression fehlt'
parameters, texts, flags = [], [], []
helper = None
report = {'project': project.name}

def setpar(par, value=None, expression=None):
    parameters.append((par, par.val, par.expr, par.mode))
    if expression is not None:
        par.expr = expression
    else:
        par.val = value

try:
    helper = layout.create(textDAT, helper_name)
    helper.text = shared_callback_source()
    helper.nodeX, helper.nodeY = -250, -600
    for item in roots:
        for geo_name, sop_name, role in roles:
            geo = item.op(geo_name)
            dat = geo.op(sop_name + '_callbacks')
            texts.append((dat, dat.text))
            dat.text = adapted_callback(dat.text, role, helper.path)
            old_material = str(geo.par.material.val or '')
            if role == 'source_tabletop':
                material = study.op('mat_study_source').path
            else:
                material = ''  # Study-Ziele verwenden ebenfalls kein eigenes MAT.
            setpar(geo.par.material, expression=(
                repr(material) + " if parent().par.Tabletype.eval() == 'rect' else " + repr(old_material)))
            if role.startswith('target_'):
                setpar(geo.par.tz, expression="0.001 if parent().par.Tabletype.eval() == 'rect' else " + repr(float(geo.par.tz.eval())))
            # Vorhandene SOPs nutzen, keine zweite Zielgeometrie aufbauen.
            for sop in geo.children:
                if sop.type == 'script':
                    flags.append((sop, sop.display, sop.render))
                    sop.display = sop.name == sop_name
                    sop.render = sop.name == sop_name
            geo.op(sop_name).cook(force=True)
            assert not geo.op(sop_name).errors(), geo.op(sop_name).errors()
    setpar(floor.par.geometry, expression=floor_expression(old_floor_expression))
    report['protected_settings_unchanged'] = invariant() == protected_before
    report['chair_image_unchanged'] = image_hash(chair_path) == chair_before
    report['table_mask_image_unchanged'] = image_hash(mask_path) == mask_before
    floor.cook(force=True)
    assert not floor.errors(), floor.errors()
    array = floor.numpyArray(delayed=False)
    report['floor_has_visible_pixels'] = bool((array[:, :, :3] > 0.01).any())
    report['rect_contours'] = []
    for item in items:
        if item.par.Tabletype.eval() == 'rect':
            report['rect_contours'].append({'item': item.path,
                'source_primitives': item.op('table_source_geo/table_outline_inner').numPrims,
                'floor_target_primitives': item.op('table_target_floor_geo/table_outline_outer').numPrims,
                'tabletop_target_primitives': item.op('table_target_tabletop_geo/table_outline_inner').numPrims})
    report['rect_primitive_counts_correct'] = all(n['source_primitives'] == 4 and n['floor_target_primitives'] == 12
        and n['tabletop_target_primitives'] == 12 for n in report['rect_contours'])
    report['passed'] = all(report[k] for k in ['protected_settings_unchanged', 'chair_image_unchanged',
        'table_mask_image_unchanged', 'floor_has_visible_pixels', 'rect_primitive_counts_correct'])
    assert report['passed'], 'Validierung fehlgeschlagen: ' + json.dumps(report)
except Exception:
    for par, value, expression, mode in reversed(parameters):
        par.val = value
        par.expr = expression or ''
        par.mode = mode
    for dat, text in texts:
        dat.text = text
    for sop, display, render in flags:
        sop.display, sop.render = display, render
    if helper is not None:
        helper.destroy()
    print('Änderungen zurückgerollt. Nichts gespeichert.')
    raise

path = Path('/private/tmp/aisi_floor_study_style_check.json')
path.write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report, indent=2))
print('Bericht:', str(path))
print('Keine .toe gespeichert. Bitte render_floor und render_tabletop nur in Operator-Viewern kontrollieren.')
