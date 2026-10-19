"""Textport: geprüfte Chair-Redundanzen mit Sicherung und Abbruchprüfung entfernen.

Keine .toe speichern; keine Projektorfenster öffnen. Bei einer externen
Referenz wird vor der ersten Änderung abgebrochen.
"""
import hashlib
import json
import tempfile
from pathlib import Path

layout = op('/project1/comp_layout_proposal')
output = op('/project1/comp_output')
debug = layout.op('chair_debug')
preview = layout.op('tables_chairs_virtual_preview')
assert debug is not None and preview is not None, 'Zentrale Viewer fehlen'
migration = json.loads(Path('/private/tmp/aisi_shared_chair_migration.json').read_text())
assert migration.get('passed') and migration.get('project') == project.name, 'Erfolgreicher Migrationscheck dieser Datei fehlt'

old_paths = ['/project1/comp_synth_chair_debug', '/project1/comp_tables_chairs_virtual_preview']
legacy_names = ['render_synth_chairs_regular_floor', 'select_synth_chairs_regular',
                'composite_floor_with_synth_chairs', 'switch_enable_synth_chairs_regular',
                'null_floor_with_optional_synth_chairs']
redundant_names = ['geo_synth_chair_%02d' % i for i in range(8)] + [
    'select_synth_chair_osc', 'null_synth_chair_osc_inputs', 'mat_synth_chair_debug_orange']
targets = [op(p) for p in old_paths] + [output.op(n) for n in legacy_names] + [debug.op(n) for n in redundant_names]
assert all(n is not None for n in targets), 'Bereinigungsziel fehlt; Zustand zuerst prüfen'
paths = [n.path for n in targets]

def discarded(path):
    return any(path == p or path.startswith(p + '/') for p in paths)

def walk(node):
    yield node
    if node.isCOMP:
        for child in node.children:
            yield from walk(child)

def matches(value):
    # Absolute Pfade sowie die eindeutigen alten Container-/Geometrienamen.
    tokens = old_paths + paths + [p.rsplit('/', 1)[1] for p in old_paths] + redundant_names
    return isinstance(value, str) and any(t in value for t in tokens)

references = []
for node in walk(op('/project1')):
    if discarded(node.path):
        continue
    for source in node.inputs:
        if discarded(source.path):
            references.append([node.path, 'input', source.path])
    for par in node.pars():
        for kind, value in [('expression', par.expr), ('value', par.val)]:
            if matches(value):
                references.append([node.path, kind + ':' + par.name, str(value)])
        # Erfasst auch OP-Parameter mit relativen Pfaden und Bindings.
        try:
            value = par.eval()
            values = value if isinstance(value, (list, tuple)) else [value]
            for resolved in values:
                if hasattr(resolved, 'path') and discarded(resolved.path):
                    references.append([node.path, 'resolved:' + par.name, resolved.path])
        except Exception:
            pass
    if node.isDAT:
        try:
            value = node.text
        except Exception:
            value = ''
        if matches(value):
            references.append([node.path, 'DAT text', value])

report_path = Path('/private/tmp/aisi_shared_chair_cleanup.json')
report = {'project': project.name, 'targets': paths, 'external_references': references}
report_path.write_text(json.dumps(report, indent=2))
if references:
    print(json.dumps(report, indent=2))
    raise RuntimeError('Externe Referenzen vorhanden; nichts entfernt. Ergebnis: ' + str(report_path))

protected = [output.op('select_floor').path, layout.op('null_floor_with_optional_synth_chairs').path,
             output.op('switch_tabletop').path, output.op('switch_table_mask').path,
             output.op('out_projector_0').path, output.op('out_projector_1').path,
             debug.op('render_synth_chair_debug_preview').path,
             debug.op('null_synth_chair_debug_preview').path,
             preview.op('composite_tables_and_synth_chairs').path,
             preview.op('null_tables_chairs_virtual_preview').path]

def signature(path):
    node = op(path)
    node.cook(force=True)
    assert not node.errors(), path + ': ' + node.errors()
    array = node.numpyArray(delayed=False)
    return [list(array.shape), hashlib.sha256(array.tobytes()).hexdigest()]

before = {p: signature(p) for p in protected}
# Wiederherstellbare COMP-Snapshots, bevor irgendein Operator entfernt wird.
backup = Path(tempfile.mkdtemp(prefix='aisi_chair_cleanup_'))
for comp in [op(p) for p in old_paths] + [output, debug]:
    filename = backup / (comp.name + '.tox')
    comp.save(str(filename))
    assert filename.is_file() and filename.stat().st_size > 0, 'Sicherung fehlt: ' + str(filename)
report['backup_directory'] = str(backup)
report_path.write_text(json.dumps(report, indent=2))
for node in targets:
    node.destroy()
report['images_identical'] = {p: before[p] == signature(p) for p in protected}
report['removed'] = all(op(p) is None for p in paths)
report['passed'] = report['removed'] and all(report['images_identical'].values())
report_path.write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
print('Keine .toe gespeichert. Sicherungen:', str(backup))
assert report['passed'], 'Bildvergleich fehlgeschlagen; nicht speichern, Sicherungen erhalten'
