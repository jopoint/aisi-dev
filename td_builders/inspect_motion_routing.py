"""Read current content insertion points; no parameter writes or forced cooks."""
import builtins
import json
import sys


def inspect(resolve):
    layout='/project1/comp_layout_proposal/'
    output='/project1/comp_output/'
    paths=[layout+name for name in (
        'render_floor','select_floor_for_synth_chairs',
        'composite_floor_with_synth_chairs','switch_enable_synth_chairs_regular',
        'render_tabletop','null_tabletop','mask_tabletop',
        'null_tabletop_masked','null_table_mask',
        'null_floor_with_optional_synth_chairs')]
    paths += [output+name for name in (
        'select_central_floor','select_tabletop','select_table_mask',
        'switch_floor','switch_tabletop','switch_table_mask')]
    report={'read_only':True,'parameters_changed':False,'nodes_changed':False,
            'nodes':[],'study_mode':None}
    raw=resolve('/project1/comp_io/null_osc_raw')
    if raw is not None:
        channel=raw['study/mode']
        report['study_mode']=channel.eval() if channel is not None else None
    seen=set()
    def add(node):
        if node.path in seen:
            return
        seen.add(node.path)
        entry={'path':node.path,'type':str(node.type),
               'inputs':[source.path for source in node.inputs],
               'outputs':[dest.path for dest in node.outputs],'parameters':{}}
        for p in node.pars():
            if p.name in ('top','index','operand','operation','maskchannel',
                          'fit','resolutionw','resolutionh','format'):
                entry['parameters'][p.name]={'value':str(p.eval()),
                    'mode':str(p.mode),'expression':p.expr,'binding':p.bindExpr}
        report['nodes'].append(entry)
    for path in paths:
        node=resolve(path)
        if node is None:
            report['nodes'].append({'path':path,'missing':True})
            continue
        add(node)
        # One upstream hop exposes chair composites and actual mask ordering.
        for source in node.inputs:
            add(source)
    return report


def symbol(name):
    return (globals().get(name) or getattr(builtins,name,None)
            or getattr(sys.modules.get('__main__'),name,None))


if globals().get('__spec__') is None and callable(symbol('op')):
    print(json.dumps(inspect(symbol('op')),ensure_ascii=False,indent=2))
