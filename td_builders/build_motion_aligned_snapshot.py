"""Validate current mask poses, then build a separate static Motion snapshot.

Never updates existing poses, masks, routing, simulator, or projector outputs.
Legacy slot labels are snapshot keys, not persistent tracking identities.
"""
import builtins
import json
import math
from pathlib import Path
import sys

REPO = Path('/Users/Johannes/dev/Promotion_Prototypen/AISI')
BASE = '/project1/comp_layout_proposal/'
NAME = 'comp_aisi_motion_aligned_snapshot'
HEADER = ('id','type','x','y','rot','target_x','target_y','target_rot')


def parse_rows(rows):
    if not rows or tuple(rows[0]) != HEADER:
        raise ValueError('Unerwartete tables_active-Spalten; keine Zuordnung erfunden.')
    result = []
    seen = set()
    for row in rows[1:]:
        if len(row) != len(HEADER):
            raise ValueError('Unvollständige Tischzeile.')
        identity, kind = row[:2]
        if not str(identity).isdigit() or str(int(identity)) != str(identity):
            raise ValueError('Tisch-ID ist kein eindeutiger Legacy-Slot.')
        slot = int(identity)
        if slot in seen or slot not in range(5) or kind != 'rect':
            raise ValueError('Doppelter/ungültiger Slot oder nicht unterstützter Tischtyp.')
        seen.add(slot)
        values = tuple(float(v) for v in row[2:])
        if not all(math.isfinite(v) for v in values):
            raise ValueError('Nicht endliche Tischpose.')
        result.append((slot, values[:3], values[3:]))
    if not result or len(result) > 5:
        raise ValueError('Ein bis fünf Rect-Tische erforderlich.')
    return result


def screen_pose(pose):
    # Reuse the one established TD-to-content boundary; no second transform.
    for path in (str(REPO), str(REPO/'src')):
        if path not in sys.path:
            sys.path.insert(0,path)
    from td_builders.motion_design import td_pose
    return tuple(td_pose(*pose))


def angle_error(a, b):
    return abs((a-b+90) % 180-90)


def pose_difference(actual, desired):
    a, b = screen_pose(actual), screen_pose(desired)
    from td_builders.motion_design import WIDTH, DEPTH
    distance = math.hypot(a[0]-b[0],a[1]-b[1])
    angle = angle_error(a[2],b[2])
    radius = math.hypot(WIDTH,DEPTH)/2
    return {'distance_cm':distance, 'angle_deg':angle,
            'max_edge_displacement_cm':distance+2*radius*math.sin(math.radians(angle)/2)}


def compare_masks(rows, masks, pixel_cm=None):
    """Match renderer geometry suffixes and actual transforms, not list order."""
    if pixel_cm is not None and (not math.isfinite(pixel_cm) or pixel_cm <= 0):
        raise ValueError('Positives endliches Pixelmaß erforderlich.')
    expected = {slot:source for slot,source,target in rows}
    active = {}
    problems = []
    for mask in masks:
        sx, sy, sz = mask['scale']
        if not all(math.isfinite(v) for v in (*mask['scale'],*mask['pose'],*mask['tilt'])):
            problems.append('Maske %s enthält nicht endliche Werte.' % mask['slot'])
            continue
        if abs(sx) < 1e-8 or not mask['render']:
            continue
        slot = mask['slot']
        if slot in active:
            problems.append('Mehrere aktive Masken für Slot %s.' % slot)
        active[slot] = mask
        if any(abs(v-1) > 1e-6 for v in (sx,sy,sz)) or any(
                abs(v) > 1e-6 for v in mask['tilt']):
            problems.append('Maske %s hat zusätzliche Skalierung/Neigung.' % slot)
    if set(active) != set(expected):
        problems.append('Aktive Masken-Slots %s passen nicht zu Tisch-Slots %s.'
                        % (sorted(active), sorted(expected)))
    for slot in set(active) & set(expected):
        actual, desired = active[slot]['pose'], expected[slot]
        different = (math.hypot(actual[0]-desired[0],actual[1]-desired[1]) > 1e-5
                     or angle_error(actual[2],desired[2]) > .001)
        if pixel_cm is not None:
            different = pose_difference(actual,desired)['max_edge_displacement_cm'] > pixel_cm
        if different:
            problems.append('Maske und AISI-Source-Pose weichen bei Slot %s ab.' % slot)
    return problems


def align_rows(rows, masks, pixel_cm):
    problems = compare_masks(rows,masks,pixel_cm=pixel_cm)
    by_slot = {m['slot']:m for m in masks if m['render'] and abs(m['scale'][0]) > 1e-8}
    deltas = [{'slot':slot,**pose_difference(by_slot[slot]['pose'],source)}
              for slot,source,target in rows if slot in by_slot
              and all(math.isfinite(v) for v in by_slot[slot]['pose'])]
    # Pixel tolerance only establishes slot correspondence. The snapshot uses
    # the exact mask pose, not the approximately matching legacy source pose.
    aligned = ([(slot,tuple(by_slot[slot]['pose']),target) for slot,source,target in rows]
               if not problems else rows)
    return aligned, deltas, problems


def preflight(resolve):
    table, renderer, camera = (resolve(BASE+n) for n in
                               ('tables_active','render_table_mask','cam1'))
    if any(n is None for n in (table,renderer,camera)):
        raise ValueError('Tischliste, Maskenrenderer oder Kamera fehlt.')
    rows = parse_rows([[c.val for c in table.row(i)] for i in range(table.numRows)])
    if (camera.par.projection.eval() != 'ortho'
            or abs(camera.par.orthowidth.eval()-2.6) > 1e-6
            or any(abs(getattr(camera.par,p).eval()) > 1e-6
                   for p in ('tx','ty','rx','ry','rz'))):
        raise ValueError('Kamera weicht von der geprüften ROI-Abbildung ab.')
    cameras = renderer.par.camera.eval()
    cameras = cameras if isinstance(cameras,(list,tuple)) else [cameras]
    if [getattr(c,'path',str(c)) for c in cameras] != [camera.path]:
        raise ValueError('Maskenrenderer verwendet eine andere Kamera.')
    width, height = int(renderer.width), int(renderer.height)
    if width != height or width <= 0:
        raise ValueError('Maskenbild hat kein quadratisches ROI-Raster.')
    geos = renderer.par.geometry.eval()
    if not isinstance(geos,(list,tuple)):
        raise ValueError('Masken-Geometrie konnte nicht als Operatorliste gelesen werden.')
    masks, seen = [], set()
    for geo in geos:
        if geo.path in seen:
            continue  # Report duplication, without changing the existing list.
        seen.add(geo.path)
        prefix = '/project1/comp_study_visualization/rect_setup_mask_geo_'
        if not geo.path.startswith(prefix) or not geo.path[len(prefix):].isdigit():
            raise ValueError('Nicht geprüfte Maskengeometrie: '+geo.path)
        if geo.inputs:
            raise ValueError('Zusätzliche Parenting-Verbindungen: '+geo.path)
        masks.append({'path':geo.path, 'slot':int(geo.path[len(prefix):]),
            'pose':[float(getattr(geo.par,p).eval()) for p in ('tx','ty','rz')],
            'scale':[float(getattr(geo.par,p).eval()) for p in ('sx','sy','sz')],
            'tilt':[float(getattr(geo.par,p).eval()) for p in ('rx','ry')],
            'render':bool(geo.render)})
    # The shared ROI is 500 cm across. This is a raster association check,
    # unrelated to the position/rotation tolerances used for Motion success.
    rows, deltas, problems = align_rows(rows,masks,pixel_cm=500.0/width)
    return rows, {'pose_alignment_passed':not problems, 'problems':problems,
                  'actual_masks':masks, 'mask_geometry_duplicates':len(geos)-len(seen),
                  'snapshot_resolution':width, 'slot_match_pixel_cm':500.0/width,
                  'legacy_source_differences':deltas,
                  'snapshot_source':'exact current mask poses; legacy targets unchanged'}


def build(resolve, symbols):
    root = resolve('/project1')
    if root is None or root.op(NAME) is not None:
        raise RuntimeError('project1 fehlt oder Snapshot existiert; nichts geändert.')
    rows, report = preflight(resolve)
    report.update({'existing_nodes_changed':False, 'saved':False,
                   'tracking_freshness':'not established; static snapshot only',
                   'persistent_table_ids':'not established; legacy slot labels only'})
    if not report['pose_alignment_passed']:
        report['status']='Pose-Abgleich fehlgeschlagen; nichts angelegt oder verändert.'
        return report
    namespace={'__name__':'aligned_snapshot_builder','_AISI_MOTION_IMPORT_ONLY':True}
    builder=REPO/'td_builders/build_motion_preview.py'
    exec(compile(builder.read_text(encoding='utf-8'),str(builder),'exec'),namespace)
    namespace['build'](resolve,symbols,repo=REPO,name=NAME)
    comp=root.op(NAME)
    try:
        dat=comp.op('poses')
        header=[c.val for c in dat.row(0)]
        dat.clear()
        dat.appendRow(header)
        for slot, source, target in rows:
            s,t = screen_pose(source),screen_pose(target)
            active = math.hypot(s[0]-t[0],s[1]-t[1]) > 8 or angle_error(s[2],t[2]) > 5
            dat.appendRow(['legacy_slot_%d' % slot,*s,*t,1,int(active)])
        comp.par.Resolution=report['snapshot_resolution']
        comp.par.Demo=False
        comp.par.Usedat=True
        comp.unstore('motion_engine')
        comp.store('motion_static_snapshot',True)
        report.update({'component':comp.path, 'status':'static aligned-pose snapshot created',
                       'preview':comp.op('render_preview').path,
                       'routing_changed':False,'physical_validation':'not performed',
                       'mask_shape_alignment':'not established by pose check'})
        return report
    except Exception:
        comp.destroy()
        raise


def symbol(name):
    return (globals().get(name) or getattr(builtins,name,None)
            or getattr(sys.modules.get('__main__'),name,None))


# Textport exec has no import spec. A regular import must only define helpers,
# even when TouchDesigner exposes op through builtins or __main__.
if globals().get('__spec__') is None and callable(symbol('op')):
    kinds=('containerCOMP','textDAT','tableDAT','scriptTOP','glslTOP','outTOP')
    print(json.dumps(build(symbol('op'),{k:symbol(k) for k in kinds}),ensure_ascii=False,indent=2))
