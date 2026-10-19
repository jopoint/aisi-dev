"""Im TD-Textport ausführen: vorhandenen Chair-Zweig auf 15 sichere Slots erweitern.

Ändert ausschließlich die Chair-DATs und Bindungen bestehender Chair-Instanzen.
Speichert keine Projektdatei und verändert keine Projektor-/Kalibrierungsoperatoren.
"""

CHAIRS_PATH = '/project1/comp_layout_proposal/chairs'
chairs = op(CHAIRS_PATH)
assert chairs is not None, 'chairs COMP fehlt'
active = chairs.op('chairs_active')
active_callbacks = chairs.op('chairs_active_callbacks')
replicator_callbacks = chairs.op('replicator1_callbacks')
template = chairs.op('chairs_template')
assert all(x is not None for x in (active, active_callbacks, replicator_callbacks, template)), 'Chair-Basis unvollständig'
assert template.op('chair_geo') is not None, 'Template-Geometrie fehlt'
assert all(hasattr(template.par, n) for n in ('X', 'Y', 'Radius')), 'Template-Interface abweichend'

# Einmalige Rückfallkopie für diese Textport-Sitzung; keine Dateien überschreiben.
if chairs.fetch('chair_data_before_repair', None) is None:
    chairs.store('chair_data_before_repair', {
        'active_callbacks': active_callbacks.text,
        'replicator_callbacks': replicator_callbacks.text,
    })

active_callbacks.text = '''import math

def onCook(scriptOp):
    scriptOp.clear()
    scriptOp.appendRow(['id', 'x', 'y', 'radius'])
    raw = op('/project1/comp_io/null_osc_raw')

    def value(name):
        channel = raw[name] if raw is not None else None
        if channel is None:
            return None
        result = float(channel.eval())
        return result if math.isfinite(result) else None

    received_count = value('chair/count')
    count = min(15, max(0, int(received_count))) if received_count is not None else 0
    for index in range(15):
        x = value('chair/%d/x' % index)
        y = value('chair/%d/y' % index)
        radius = value('chair/%d/radius' % index)
        valid = index < count and x is not None and y is not None and radius is not None and radius > 0
        scriptOp.appendRow([
            index,
            (x - 250.0) * 0.0052 if valid else 0.0,
            -(y - 250.0) * 0.0052 if valid else 0.0,
            radius * 0.0052 if valid else 0.0,
        ])
    return
'''

replicator_callbacks.text = '''def bind(inst):
    if not inst.name.startswith('item') or not inst.name[4:].isdigit():
        return
    row = int(inst.name[4:])
    for parameter, column in [('X', 'x'), ('Y', 'y'), ('Radius', 'radius')]:
        getattr(inst.par, parameter).expr = "float(op('/project1/comp_layout_proposal/chairs/chairs_active')[%d, '%s'].val)" % (row, column)
    geo = inst.op('chair_geo')
    if geo is not None:
        geo.par.sx.expr = 'float(parent().par.Radius.eval() > 0.0)'
        geo.par.sy.expr = 'float(parent().par.Radius.eval() > 0.0)'

def onReplicate(comp, allOps, newOps, template, master):
    for inst in allOps:
        bind(inst)
    return
'''

active.cook(force=True)
bindings = {'op': op}
exec(replicator_callbacks.text, bindings)
for instance in chairs.children:
    bindings['bind'](instance)
print('Chair-Daten korrigiert:', active.numRows - 1, 'Slots; vorhandene Instanzen laufend gebunden.')
print('Nächster Check: item1…item15, gültige Radien und DAT-Fehler prüfen. Noch nicht gespeichert.')
