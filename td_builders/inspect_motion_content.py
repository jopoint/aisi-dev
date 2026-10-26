"""Read-only Textport audit before installing the AISI motion component.

No parameter writes, forced cooks, network changes, or project saves.
Run with exec(compile(open(path, encoding='utf-8').read(), path, 'exec')).
"""
import json
import builtins
import sys


def parameter_state(parameter):
    return {
        'mode': str(parameter.mode),
        'value': str(parameter.val),
        'expression': parameter.expr,
        'binding': parameter.bindExpr,
    }


def node_state(node):
    result = {
        'path': node.path,
        'type': str(node.type),
        'inputs': [source.path for source in node.inputs],
        'parameters': {},
    }
    for parameter in node.pars():
        if (parameter.isCustom or parameter.name in {
                'top', 'chop', 'dat', 'index', 'camera', 'geometry',
                'resw', 'resh', 'resolutionw', 'resolutionh',
                'tx', 'ty', 'rz', 'port', 'active'}):
            result['parameters'][parameter.name] = parameter_state(parameter)
    return result


def inspect_motion_content(resolve, project_name):
    roots = (
        '/project1/comp_io',
        '/project1/comp_layout_proposal',
        '/project1/comp_output',
        '/project1/comp_tracking_only',
        '/project1/comp_study_visualization',
    )
    report = {'project': str(project_name), 'read_only': True,
              'missing': [], 'nodes': [], 'osc_channels': []}
    seen = set()

    def add(node):
        if node is not None and node.path not in seen:
            seen.add(node.path)
            report['nodes'].append(node_state(node))

    for path in roots:
        root = resolve(path)
        if root is None:
            report['missing'].append(path)
            continue
        add(root)
        for child in root.children:
            name = child.name.lower()
            if (not child.isCOMP or
                    any(token in name for token in ('projector', 'content', 'motion'))):
                add(child)
                if child.isCOMP:
                    for inner in child.children:
                        if not inner.isCOMP:
                            add(inner)
        # Inspect one existing table without altering template/instances.
        if path.endswith('comp_layout_proposal'):
            for name in ('table_template', 'item1'):
                item = root.op(name)
                add(item)
                if item is not None:
                    for child in item.children:
                        add(child)

    raw = resolve('/project1/comp_io/null_osc_raw')
    if raw is not None:
        # List channel names only. No forced cook or pose evaluation.
        report['osc_channels'] = [channel.name for channel in raw.chans()
                                  if channel.name.startswith(
                                      ('table/', 'vision/table/', 'study/', 'layout/'))]
    return report


def _td_symbol(name):
    return (globals().get(name) or getattr(builtins, name, None)
            or getattr(sys.modules.get('__main__'), name, None))


def inspect_motion_summary(resolve):
    """Compact follow-up when the full Textport report was truncated."""
    report = {'nodes': [], 'io_dat_names': [], 'osc_values': {}}
    base = '/project1/comp_layout_proposal/'
    paths = [base + name for name in (
        'render_floor', 'render_tabletop', 'cam1',
        'null_tabletop_masked', 'null_table_mask',
        'null_floor_with_optional_synth_chairs', 'item1')]
    for path in paths:
        node = resolve(path)
        if node is None:
            report['nodes'].append({'path': path, 'missing': True})
            continue
        state = {'path': path, 'type': str(node.type),
                 'inputs': [n.path for n in node.inputs], 'parameters': {}}
        for p in node.pars():
            if p.isCustom or p.name in (
                    'camera', 'geometry', 'projection', 'orthowidth',
                    'resw', 'resh', 'resolutionw', 'resolutionh',
                    'tx', 'ty', 'tz', 'rx', 'ry', 'rz'):
                state['parameters'][p.name] = {
                    'evaluated': str(p.eval()), 'expression': p.expr}
        report['nodes'].append(state)
    io = resolve('/project1/comp_io')
    if io is not None:
        report['io_dat_names'] = [n.path for n in io.children if n.isDAT]
    raw = resolve('/project1/comp_io/null_osc_raw')
    if raw is not None:
        names = ('study/mode', 'table/count', 'table/0/source_available',
                 'table/0/source_x', 'table/0/source_y', 'table/0/source_rot',
                 'table/0/target_x', 'table/0/target_y', 'table/0/target_rot',
                 'table/0/width', 'table/0/height', 'table/0/type_id')
        for name in names:
            channel = raw[name]
            report['osc_values'][name] = channel.eval() if channel is not None else None
    return report


_resolve = _td_symbol('op')
_project = _td_symbol('project')
if callable(_resolve) and _project is not None:
    print('AISI_MOTION_AUDIT_BEGIN')
    print(json.dumps(inspect_motion_summary(_resolve),
                     ensure_ascii=False, indent=2))
    print('AISI_MOTION_AUDIT_END')
elif __name__ == '__main__':
    print('TD-Kontext nicht auflösbar. Im Textport direkt ausführen:')
    print("print(json.dumps(inspect_motion_content(op, project.name), ensure_ascii=False, indent=2))")
