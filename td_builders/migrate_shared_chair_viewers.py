"""Textport: Viewer kontrolliert unter comp_layout_proposal migrieren.

Kopiert zunächst die bestehende Viewer-Struktur, korrigiert lokale Pfade und
vergleicht ihre Bilder. Originale bleiben bis zur separaten Bereinigung stehen.
Keine Projektdatei speichern und keine Projektorfenster öffnen.
"""
import hashlib
import json
from pathlib import Path

layout = op('/project1/comp_layout_proposal')
mapping = {
    '/project1/comp_synth_chair_debug': layout.path + '/chair_debug',
    '/project1/comp_tables_chairs_virtual_preview': layout.path + '/tables_chairs_virtual_preview',
}
assert all(op(p) is not None for p in mapping), 'Originale fehlen'
assert all(op(p) is None for p in mapping.values()), 'Zielkomponenten existieren bereits; nicht nochmals ausführen'

def walk(node):
    yield node
    if node.isCOMP:
        for child in node.children:
            yield from walk(child)

def image_hash(path):
    node = op(path)
    assert node is not None, 'Bildquelle fehlt: ' + path
    node.cook(force=True)
    assert not node.errors(), path + ': ' + node.errors()
    a = node.numpyArray(delayed=False)
    return [list(a.shape), hashlib.sha256(a.tobytes()).hexdigest()]

protected = [
    '/project1/comp_output/select_floor',
    '/project1/comp_layout_proposal/null_floor_with_optional_synth_chairs',
    '/project1/comp_output/switch_tabletop',
    '/project1/comp_output/switch_table_mask',
    '/project1/comp_output/out_projector_0',
    '/project1/comp_output/out_projector_1',
]
before = {p: image_hash(p) for p in protected}

def relocated(value):
    for old, new in mapping.items():
        value = value.replace(old, new)
    return value

for old, new in mapping.items():
    comp = layout.copy(op(old), name=new.rsplit('/', 1)[1], includeDocked=False)
    assert comp.path == new, 'Unerwarteter Zielname: ' + comp.path
    for node in walk(comp):
        for par in node.pars():
            expr = par.expr
            if expr and any(p in expr for p in mapping):
                par.expr = relocated(expr)
            elif isinstance(par.val, str) and any(p in par.val for p in mapping):
                par.val = relocated(par.val)
        if node.isDAT:
            try:
                original = node.text
                if any(p in original for p in mapping):
                    node.text = relocated(original)
            except Exception:
                pass

debug = op(mapping['/project1/comp_synth_chair_debug'])
preview = op(mapping['/project1/comp_tables_chairs_virtual_preview'])
debug.op('render_synth_chair_debug_preview').par.geometry = layout.path + '/chairs/item*/chair_geo'
debug.op('render_synth_chair_debug_preview').par.camera = debug.op('cam_synth_chair_debug_preview').path
preview.op('select_synthetic_chair_render').par.top = debug.op('render_synth_chair_debug_preview').path
debug.nodeX, debug.nodeY = -750, -1000
preview.nodeX, preview.nodeY = -500, -1000

# Den verbliebenen alten Render ebenfalls von den alten acht Geometrien lösen.
legacy = op('/project1/comp_output/render_synth_chairs_regular_floor')
if legacy is not None:
    legacy.par.geometry = layout.path + '/chairs/item*/chair_geo'

pairs = [
    ('/project1/comp_synth_chair_debug/render_synth_chair_debug_preview', debug.op('render_synth_chair_debug_preview').path),
    ('/project1/comp_synth_chair_debug/null_synth_chair_debug_preview', debug.op('null_synth_chair_debug_preview').path),
    ('/project1/comp_tables_chairs_virtual_preview/composite_tables_and_synth_chairs', preview.op('composite_tables_and_synth_chairs').path),
    ('/project1/comp_tables_chairs_virtual_preview/null_tables_chairs_virtual_preview', preview.op('null_tables_chairs_virtual_preview').path),
]
report = {
    'project': project.name,
    'new_paths': list(mapping.values()),
    'viewer_images_identical': {new: image_hash(old) == image_hash(new) for old, new in pairs},
    'floor_tabletop_mask_projectors_identical': {p: before[p] == image_hash(p) for p in protected},
}
report['passed'] = all(report['viewer_images_identical'].values()) and all(report['floor_tabletop_mask_projectors_identical'].values())
Path('/private/tmp/aisi_shared_chair_migration.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
print('Originale noch vorhanden. Erst nach erfolgreichem Vergleich und Referenzprüfung entfernen. Nicht gespeichert.')
