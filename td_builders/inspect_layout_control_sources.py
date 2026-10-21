"""Lesende Diagnose fehlender Source-Konturen im Kontrollviewer."""

import json
from pathlib import Path


ROOT = '/project1/comp_layout_proposal'


def _value(parameter):
    value = parameter.eval()
    if isinstance(value, (tuple, list)):
        return [getattr(node, 'path', str(node)) for node in value]
    return getattr(value, 'path', str(value))


def describe(node):
    if node is None:
        return {'missing': True}
    result = {'path': node.path, 'type': node.type, 'errors': str(node.errors()),
              'inputs': [n.path for n in node.inputs], 'parameters': {}}
    for name in ('geometry', 'camera', 'lights', 'material', 'render', 'display',
                 'tx', 'ty', 'tz', 'rz', 'sx', 'sy', 'sz', 'Tabletype',
                 'X', 'Y', 'Rot', 'Targetx', 'Targety', 'Targetrot',
                 'operand', 'bgcolora', 'alpha', 'diffr', 'diffg', 'diffb'):
        par = getattr(node.par, name, None)
        if par is not None:
            result['parameters'][name] = {'value': _value(par), 'expr': par.expr, 'mode': str(par.mode)}
    for name in ('render', 'display', 'allowCooking', 'bypass', 'numPrims', 'numPoints'):
        value = getattr(node, name, None)
        if isinstance(value, (bool, int, float, str)):
            result[name] = value
    return result


def inspect_control_sources(resolve):
    paths = [ROOT + '/' + name for name in (
        'floor_tabletop_control/render_source_and_tabletop_motion',
        'floor_tabletop_control/composite_control', 'floor_tabletop_control/out_control',
        'render_tabletop', 'light1', 'cam1', 'tables_active')]
    paths.append('/project1/comp_study_visualization/mat_study_source')
    for index in range(1, 6):
        item = ROOT + '/item%d' % index
        if resolve(item) is None:
            continue
        paths.extend((item, item + '/table_source_geo',
                      item + '/table_source_geo/table_outline_inner',
                      item + '/table_source_geo/out1'))
    report = [describe(resolve(path)) for path in paths]
    layout = resolve(ROOT)
    raw = resolve('/project1/comp_io/null_osc_raw')
    osc = {}
    if raw is not None:
        for name in ('study/mode', 'table/count'):
            channel = raw[name]
            osc[name] = float(channel.eval()) if channel is not None else None
    return {'osc': osc, 'layout': describe(layout), 'operators': report}


try:
    _resolve = op
except NameError:
    if __name__ == '__main__':
        raise RuntimeError('Im TouchDesigner-Python-Textport ausführen')
else:
    report = inspect_control_sources(_resolve)
    destination = Path(r'C:\dev\Promotion_Prototypen\AISI\data\aisi\debug\layout_control_sources.json')
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    print('Lesender Bericht:', str(destination))
    print('Keine Operatoren geändert, kein Force-Cook, keine .toe gespeichert.')
