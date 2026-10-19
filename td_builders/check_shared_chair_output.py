"""Manueller Textport-Check; stellt alle veränderten Schalter anschließend wieder her."""
import hashlib
import json
from pathlib import Path
import numpy as np

output = op('/project1/comp_output')
layout = op('/project1/comp_layout_proposal')
debug = layout.op('chair_debug')
preview = layout.op('tables_chairs_virtual_preview')
if debug is None:
    debug = op('/project1/comp_synth_chair_debug')
if preview is None:
    preview = op('/project1/comp_tables_chairs_virtual_preview')
switches = [output.par.Enablesyntheticchairs, debug.par.Enabledebug, preview.par.Enablepreview]
before = [p.eval() for p in switches]
assert all(not p.expr for p in switches), 'Schalter mit Expressions bitte separat prüfen'

def pixels(path):
    node = op(path)
    assert node is not None, 'Node fehlt: ' + path
    node.cook(force=True)
    assert not node.errors(), path + ': ' + node.errors()
    return node.numpyArray(delayed=False).copy()

def signature(path):
    a = pixels(path)
    return hashlib.sha256(a.tobytes()).hexdigest()

protected = ['/project1/comp_output/switch_tabletop', '/project1/comp_output/switch_table_mask']
projectors = ['/project1/comp_output/out_projector_0', '/project1/comp_output/out_projector_1']
report = {'project': project.name}
try:
    for p in switches:
        p.val = False
    base = pixels('/project1/comp_output/select_floor')
    optional_off = pixels('/project1/comp_layout_proposal/null_floor_with_optional_synth_chairs')
    report['floor_off_identical'] = bool(np.array_equal(base, optional_off))
    unchanged = [signature(p) for p in protected]
    off_projectors = [signature(p) for p in projectors]
    output.par.Enablesyntheticchairs = True
    layout.op('switch_enable_synth_chairs_regular').cook(force=True)
    report['regular_enabled_with_debug_and_preview_off'] = int(layout.op('switch_enable_synth_chairs_regular').par.index.eval()) == 1
    a = pixels('/project1/comp_layout_proposal/render_synth_chairs_regular_floor')
    report['chair_render_has_orange'] = bool(np.any((a[:,:,0] > .5) & (a[:,:,1] > .1) & (a[:,:,1] < .8) & (a[:,:,2] < .2)))
    report['tabletop_and_mask_identical'] = unchanged == [signature(p) for p in protected]
    report['projectors_changed'] = [old != signature(p) for old, p in zip(off_projectors, projectors)]
    output.par.Enablesyntheticchairs = False
    for p in switches[1:]:
        p.val = True
    report['floor_off_with_debug_and_preview_on_identical'] = bool(np.array_equal(base, pixels('/project1/comp_layout_proposal/null_floor_with_optional_synth_chairs')))
    report['passed'] = all([
        report['floor_off_identical'],
        report['regular_enabled_with_debug_and_preview_off'],
        report['chair_render_has_orange'],
        report['tabletop_and_mask_identical'],
        all(report['projectors_changed']),
        report['floor_off_with_debug_and_preview_on_identical'],
    ])
finally:
    for p, val in zip(switches, before):
        p.val = val

Path('/private/tmp/aisi_shared_chair_output_check.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
print('Ursprüngliche Schalterzustände wiederhergestellt. Noch keine Datei gespeichert.')
