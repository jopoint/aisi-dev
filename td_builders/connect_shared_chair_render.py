"""Im TD-Textport ausführen: vorhandene Renderer auf gemeinsame Chairs umstellen.

Keine Projektdatei speichern, keine Projektorfenster öffnen. Die bestehenden
Kameras, Ausgabe-Schalter und nachgelagerten Projektorpfade bleiben erhalten.
"""

layout = op('/project1/comp_layout_proposal')
chairs = layout.op('chairs')
floor = layout.op('render_floor')
regular = layout.op('render_synth_chairs_regular_floor')
debug = op('/project1/comp_synth_chair_debug/render_synth_chair_debug_preview')
composite = layout.op('composite_floor_with_synth_chairs')
chair_select = layout.op('select_synth_chairs_regular')
assert all(x is not None for x in (chairs, floor, regular, debug, composite, chair_select)), 'Erwartete Renderstruktur fehlt'
assert all(chairs.op('item%d/chair_geo' % i) is not None for i in range(1, 16)), 'Die 15 Chair-Instanzen sind noch nicht vollständig'
assert len(composite.inputs) == 2, 'Composite benötigt zwei Eingänge'
assert composite.inputs[1] == chair_select, 'Composite-Eingang 1 weicht vom erwarteten Chair-Select ab'

material = chairs.op('mat_chair_orange')
if material is None:
    material = chairs.create('constantMAT', 'mat_chair_orange')
material.par.colorr = 1.0
material.par.colorg = 0.24
material.par.colorb = 0.02

# Dasselbe Material für bestehende und künftig replizierte Geometrie.
for inst in [chairs.op('chairs_template')] + [chairs.op('item%d' % i) for i in range(1, 16)]:
    inst.op('chair_geo').par.material = material.path
    inst.op('chair_geo').par.sx.expr = 'float(parent().par.Radius.eval() > 0.0)'
    inst.op('chair_geo').par.sy.expr = 'float(parent().par.Radius.eval() > 0.0)'

callback = chairs.op('replicator1_callbacks')
if 'geo.par.material' not in callback.text:
    callback.text = callback.text.replace(
        '    if geo is not None:\n',
        "    if geo is not None:\n        geo.par.material = '/project1/comp_layout_proposal/chairs/mat_chair_orange'\n",
    )

# Pattern ausschließlich für Instanzen; das Template wird nicht gerendert.
geometry = chairs.path + '/item*/chair_geo'
regular.par.geometry = geometry
regular.par.camera.expr = "op('/project1/comp_layout_proposal/render_floor').par.camera.eval()"
regular.par.outputresolution = 'custom'
regular.par.resolutionw.expr = "op('/project1/comp_layout_proposal/render_floor').width"
regular.par.resolutionh.expr = "op('/project1/comp_layout_proposal/render_floor').height"
debug.par.geometry = geometry
chair_select.par.top = regular.path
old_select = op('/project1/comp_output/select_synth_chairs_regular')
if old_select is not None:
    old_select.par.top = regular.path
composite.par.operand = 'add'

print('GEMEINSAME GEOMETRIE:', geometry)
print('FLOOR:', regular.par.camera.eval(), regular.width, regular.height)
print('COMPOSITE:', composite.par.operand.eval())
print('DEBUG:', debug.par.camera.eval(), debug.width, debug.height)
print('Keine Datei gespeichert; alte Geometrien für die spätere Referenzprüfung noch vorhanden.')
