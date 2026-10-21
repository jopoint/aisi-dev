"""Lesende Textport-Diagnose: Timeline, OSC, AISI-DATs und Instanzwerte."""

import json


def inspect_live_layout_flow(resolve):
    root = resolve('/project1')
    raw = resolve('/project1/comp_io/null_osc_raw')
    report = {
        'timeline_play': getattr(getattr(root, 'time', None), 'play', None),
        'timeline_frame': getattr(getattr(root, 'time', None), 'frame', None),
        'operators': {},
        'osc': {},
    }
    for name in ('table/count', 'chair/count', 'table/0/source_x',
                 'table/0/source_y', 'table/0/target_x', 'table/0/target_y',
                 'chair/0/x', 'chair/0/y', 'study/mode'):
        channel = raw[name] if raw is not None else None
        report['osc'][name] = float(channel.eval()) if channel is not None else None
    for path in (
        '/project1/comp_io/oscin1',
        '/project1/comp_layout_proposal',
        '/project1/comp_layout_proposal/tables_active',
        '/project1/comp_layout_proposal/chairs/chairs_active',
        '/project1/comp_layout_proposal/item1',
    ):
        node = resolve(path)
        if node is None:
            report['operators'][path] = {'missing': True}
            continue
        state = {'allowCooking': getattr(node, 'allowCooking', None),
                 'bypass': getattr(node, 'bypass', None),
                 'errors': str(node.errors())}
        if hasattr(node, 'numRows'):
            state['rows'] = node.numRows
            state['first_rows'] = [
                [str(node[row, col]) for col in range(node.numCols)]
                for row in range(min(3, node.numRows))
            ]
        values = {}
        for parameter in ('active', 'port', 'X', 'Y', 'Rot', 'Targetx', 'Targety', 'Targetrot'):
            par = getattr(node.par, parameter, None)
            if par is not None:
                values[parameter] = par.eval()
        state['parameters'] = values
        report['operators'][path] = state
    return report


try:
    _resolve = op
except NameError:
    if __name__ == '__main__':
        raise RuntimeError('Im TouchDesigner-Python-Textport ausführen')
else:
    print(json.dumps(inspect_live_layout_flow(_resolve), indent=2, default=str))
