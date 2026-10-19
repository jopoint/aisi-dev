"""Textport: AISI-Geometrien und bestehende Study-Gestaltung lesen."""
import json
from pathlib import Path

layout = op('/project1/comp_layout_proposal')
study = op('/project1/comp_study_visualization')

def walk(node):
    yield node
    if node.isCOMP:
        for child in node.children:
            yield from walk(child)

def describe(node):
    result = {'path': node.path, 'type': node.type,
        'parameters': [{'name': p.name, 'value': str(p.eval()), 'expression': p.expr,
                        'mode': str(p.mode)} for p in node.pars()
            if p.name in ['geometry', 'material', 'tx', 'ty', 'tz', 'rz', 'sx', 'sy',
                          'Tabletype', 'callbacks', 'sizex', 'sizey', 'render',
                          'diffr', 'diffg', 'diffb', 'colorr', 'colorg', 'colorb']],
        'errors': node.errors()}
    if node.isDAT and 'callbacks' in node.name:
        result['callback_text'] = node.text
    return result

report = {'project': project.name, 'renderers': [describe(layout.op(n))
    for n in ['render_floor', 'render_tabletop']], 'aisi': [], 'study': []}
# Template plus ein existierendes Item: dieselbe Pipeline erweitern.
for name in ['item1', 'tables_template', 'table_template']:
    item = layout.op(name)
    if item is not None:
        report['aisi'].append(describe(item))
        for child in item.children:
            if child.name in ['table_target_floor_geo', 'table_source_geo',
                              'table_target_tabletop_geo', 'table_motion_line_floor_geo',
                              'table_motion_line_tabletop_geo']:
                report['aisi'].extend(describe(n) for n in walk(child))
for name in ['rect_target_floor_geo', 'rect_target_tabletop_geo',
             'rect_floor_outer_outline_geo', 'rect_tabletop_inner_outline_geo',
             'rect_motion_line_floor_geo', 'rect_motion_line_tabletop_geo', 'mat_study_source']:
    node = study.op(name)
    if node is not None:
        report['study'].extend(describe(n) for n in walk(node))
report['table_replicator'] = [
    {'path': n.path, 'type': n.type, 'parameters': [
        {'name': p.name, 'value': str(p.eval()), 'expression': p.expr}
        for p in n.pars() if p.name in ['master', 'callbacks', 'template']]}
    for n in layout.children if n.type == 'replicator']
report_path = Path('/private/tmp/aisi_study_visual_style.json')
report_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
print('DATEI:', project.name)
print('VOLLSTÄNDIGER BERICHT:', str(report_path))
print('Projekt nur gelesen; keine Operatoren geändert und keine .toe gespeichert.')
