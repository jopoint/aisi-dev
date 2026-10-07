"""Textport: vorhandene Ring-Callbacks und Cook-Einstellungen lesen."""
import json
chairs = op('/project1/comp_layout_proposal/chairs')

def walk(node):
    yield node
    if node.isCOMP:
        for child in node.children:
            yield from walk(child)

print('DATEI:', project.name)
for node in walk(chairs.op('chairs_template')):
    if node.name == 'chair_ring_callbacks':
        print('RING-CALLBACK:', node.path, '\n' + node.text)
for root in [chairs.op('chairs_template'), chairs.op('item8')]:
    for node in walk(root):
        if node.type == 'script':
            print('SCRIPT:', node.path)
            print(json.dumps([{'name': p.name, 'value': str(p.eval()), 'expression': p.expr}
                for p in node.pars()], indent=2))
print('DAT-COOK-PARAMETER:', [(p.name, str(p.eval()), p.expr)
    for p in chairs.op('chairs_active').pars() if 'cook' in p.name.lower()])
print('Keine erzwungene Neuberechnung, keine Änderungen, nichts gespeichert.')
