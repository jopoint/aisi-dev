"""Textport: isolierter Radius-null-Test; Callback immer wiederherstellen.

Keine OSC-Nachrichten, keine neuen Operatoren, kein Speichern.
"""
import hashlib
import json

chairs = op('/project1/comp_layout_proposal/chairs')
active = chairs.op('chairs_active')
callbacks = chairs.op('chairs_active_callbacks')
original = callbacks.text
needle = "raw = op('/project1/comp_io/null_osc_raw')"
assert original.count(needle) == 1, 'Callback abweichend; nichts geändert'
active.cook(force=True)
instances = [chairs.op('item%d' % i) for i in range(1, 16)]
assert all(n is not None for n in instances)

def radii():
    return [float(n.par.Radius.eval()) for n in instances]

def signature(path):
    render = op(path)
    render.cook(force=True)
    assert not render.errors(), render.errors()
    return hashlib.sha256(render.numpyArray(delayed=False).tobytes()).hexdigest()

before = radii()
assert before[0] > 0 and sum(r > 0 for r in before) >= 2, 'Mindestens zwei gültige Chairs und Chair 0 erforderlich'
paths = ['/project1/comp_layout_proposal/render_synth_chairs_regular_floor',
         '/project1/comp_layout_proposal/chair_debug/render_synth_chair_debug_preview']
images = [signature(p) for p in paths]
wrapper = '''class _ZeroRadiusChannel:
    def eval(self):
        return 0.0

class _ZeroRadiusRaw:
    def __init__(self, source):
        self.source = source
    def __getitem__(self, name):
        return _ZeroRadiusChannel() if name == 'chair/0/radius' else self.source[name]

'''
report = {'project': project.name, 'test_scope': 'isolierter TD-Test; kein echter OSC-Radius-null-Test'}
try:
    callbacks.text = wrapper + original.replace(needle, "raw = _ZeroRadiusRaw(op('/project1/comp_io/null_osc_raw'))")
    active.cook(force=True)
    assert not active.errors(), active.errors()
    after = radii()
    geo = instances[0].op('chair_geo')
    report['first_chair_radius_zero'] = after[0] == 0
    report['first_chair_hidden'] = float(geo.par.sx.eval()) == 0 and float(geo.par.sy.eval()) == 0
    report['other_radii_unchanged'] = before[1:] == after[1:]
    report['positive_chairs_before'] = sum(r > 0 for r in before)
    report['positive_chairs_during_test'] = sum(r > 0 for r in after)
    report['both_raw_render_images_changed'] = all(signature(p) != old for p, old in zip(paths, images))
finally:
    callbacks.text = original
    active.cook(force=True)
    for p in paths:
        signature(p)
    report['callback_restored'] = callbacks.text == original
    report['first_chair_restored'] = float(instances[0].par.Radius.eval()) > 0
report['passed'] = all(report[k] for k in ['first_chair_radius_zero', 'first_chair_hidden',
    'other_radii_unchanged', 'both_raw_render_images_changed', 'callback_restored', 'first_chair_restored'])
print(json.dumps(report, indent=2))
print('Callback wiederhergestellt. Keine Operatoren angelegt und nichts gespeichert.')
