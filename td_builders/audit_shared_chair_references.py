"""Read-only Textport-Prüfung der noch externen Chair-Komponenten."""
import json
from pathlib import Path

root = op('/project1')
assert root is not None
targets = [
    '/project1/comp_synth_chair_debug',
    '/project1/comp_tables_chairs_virtual_preview',
]

def walk(node):
    yield node
    if node.isCOMP:
        for child in node.children:
            yield from walk(child)

nodes = list(walk(root))
report = {'project': project.name, 'targets': {}}
for target in targets:
    comp = op(target)
    assert comp is not None, 'Komponente fehlt: ' + target
    token = target.rsplit('/', 1)[1]
    external = []
    internal = []
    for node in nodes:
        references = []
        for source in node.inputs:
            if source.path == target or source.path.startswith(target + '/'):
                references.append({'kind': 'input', 'value': source.path})
        for par in node.pars():
            for kind, value in [('expression', par.expr), ('value', str(par.val))]:
                if value and token in value:
                    references.append({'kind': kind, 'parameter': par.name, 'value': value})
        if node.isDAT:
            try:
                if token in node.text:
                    references.append({'kind': 'DAT text', 'value': node.text})
            except Exception:
                pass
        if references:
            item = {'node': node.path, 'references': references}
            (internal if node.path == target or node.path.startswith(target + '/') else external).append(item)
    report['targets'][target] = {
        'children': [{'path': c.path, 'type': c.type} for c in comp.children],
        'custom_parameters': [{'name': p.name, 'value': str(p.eval()), 'expression': p.expr} for p in comp.customPars],
        'external_references': external,
        'internal_references': internal,
    }

path = Path('/private/tmp/aisi_shared_chair_references.json')
path.write_text(json.dumps(report, indent=2))
print('DATEI:', project.name)
for target, result in report['targets'].items():
    print('KOMPONENTE:', target)
    print('EXTERNE REFERENZEN:', [(r['node'], [(v['kind'], v.get('parameter', '')) for v in r['references']]) for r in result['external_references']])
print('Vollständiges Ergebnis:', str(path))
print('Keine Operatoren geändert, gelöscht oder gespeichert.')
