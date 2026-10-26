"""Read-only inspection of existing live input; no new receiver or node."""
import builtins
import json
import sys


def inspect_live(resolve):
    report = {'read_only': True, 'io_nodes': [], 'metadata': {}, 'export_rows': []}
    io = resolve('/project1/comp_io')
    if io is not None:
        for node in io.children:
            entry = {'path':node.path,'type':str(node.type),
                     'inputs':[source.path for source in node.inputs]}
            if str(node.type) == 'oscin':
                entry['parameters'] = {p.name:str(p.eval()) for p in node.pars()
                    if p.name in ('port','active','timeslice','protocol','address',
                                  'localaddress','netaddress','callbacks','callbackdat')}
            report['io_nodes'].append(entry)
    raw = resolve('/project1/comp_io/null_osc_raw')
    if raw is not None:
        for channel in raw.chans():
            name = channel.name.lower()
            if (not name.startswith(('chair/','person/'))
                    and any(token in name for token in (
                        'available','count','time','stamp','frame','revision',
                        'proposal','sequence','identity','table_id','heartbeat'))):
                report['metadata'][channel.name] = channel.eval()
    exports = resolve('/project1/comp_io/null_osc_raw_export')
    if exports is not None and exports.isDAT:
        for row in range(min(exports.numRows,18)):
            report['export_rows'].append([cell.val[:250] for cell in exports.row(row)])
    layout = resolve('/project1/comp_layout_proposal')
    report['layout_dat_names'] = ([node.path for node in layout.children if node.isDAT]
                                  if layout is not None else [])
    return report


def symbol(name):
    return (globals().get(name) or getattr(builtins,name,None)
            or getattr(sys.modules.get('__main__'),name,None))


if callable(symbol('op')):
    print(json.dumps(inspect_live(symbol('op')),ensure_ascii=False,indent=2))
elif __name__ == '__main__':
    raise RuntimeError('Im TouchDesigner-Textport ausführen.')
