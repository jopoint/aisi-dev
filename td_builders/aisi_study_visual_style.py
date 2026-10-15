"""Gemeinsame Rect-Gestaltung aus vorhandenen Study-Geometriefunktionen."""
import inspect
import math
from td_builders.study_target_floor import (
    rect_target_dash_segments, OUTLINE_THICKNESS_CM, FLOOR_TARGET_WIDTH_CM,
    FLOOR_TARGET_DEPTH_CM, TABLETOP_INNER_WIDTH_CM, TABLETOP_INNER_DEPTH_CM,
    RECT_DEPTH_CM, RECT_WIDTH_CM,
)
from td_builders.study_tabletop_brackets import rect_continuous_outline_segments, TD_UNITS_PER_CM


def floor_expression(previous):
    """Nur AISI ergänzen; bestehende Tracking-/Study-Auswahl unverändert auswerten."""
    previous = '\n'.join(line for line in previous.splitlines() if not line.lstrip().startswith('#')).strip()
    return (
        "(lambda raw: ' '.join(g.path for item in parent().findChildren(name='item*', depth=1) "
        "for g in (item.op('table_target_floor_geo'), item.op('table_motion_line_floor_geo')) if g is not None) "
        "if raw is not None and raw['study/mode'] is not None and raw['study/mode'].eval() == 2 "
        "else (\n" + previous + "\n))(op('/project1/comp_io/null_osc_raw'))"
    )



def rect_floor_join_side(pose, others):
    """Find one exact shared long edge in rendered XY centimeters/yaw."""
    x,y,rotation = pose
    if not all(math.isfinite(value) for value in pose):
        return 0
    angle = math.radians(rotation)
    tangent = (math.cos(angle),math.sin(angle))
    normal = (-tangent[1],tangent[0])
    sides = []
    for ox,oy,other_rotation in others:
        if not all(math.isfinite(value) for value in (ox,oy,other_rotation)):
            continue
        if abs((other_rotation-rotation+90)%180-90)>1e-5:
            continue
        dx,dy = ox-x,oy-y
        along = dx*tangent[0]+dy*tangent[1]
        across = dx*normal[0]+dy*normal[1]
        if abs(along)<1e-5 and abs(abs(across)-RECT_DEPTH_CM)<1e-5:
            sides.append(1 if across>0 else -1)
    # Ambiguous, penetrating and separated tables keep their complete contour.
    return sides[0] if len(sides)==1 else 0


def joined_rect_seam_segments(segments, side):
    """Each table draws half of the same dashed physical shared edge."""
    if side not in (-1,1):
        return ()
    thickness = OUTLINE_THICKNESS_CM*TD_UNITS_PER_CM
    half_stroke = thickness/2
    seam = side*RECT_DEPTH_CM/2*TD_UNITS_PER_CM
    return tuple(type(segment)(segment.width_td,half_stroke,segment.x_td,
                 seam-side*half_stroke/2) for segment in segments
                 if abs(segment.depth_td-thickness)<1e-12 and side*segment.y_td>0)


def joined_rect_floor_segments(segments, side):
    """Clip the padded floor bars at an exact physical shared long edge."""
    if side not in (-1,1):
        return segments
    seam = side*RECT_DEPTH_CM/2*TD_UNITS_PER_CM
    result = []
    for segment in segments:
        lower = segment.y_td-segment.depth_td/2
        upper = segment.y_td+segment.depth_td/2
        if side>0:
            upper = min(upper,seam)
        else:
            lower = max(lower,seam)
        if upper-lower>1e-12:
            result.append(type(segment)(segment.width_td,upper-lower,segment.x_td,(upper+lower)/2))
    result.extend(joined_rect_seam_segments(segments, side))
    return tuple(result)


def floor_join_side_for_geo(geo, resolve=None):
    """Read existing AISI transforms; no new pose channels or saved state."""
    if resolve is None:
        resolve = op
    raw = resolve('/project1/comp_io/null_osc_raw')
    if raw is None or raw['study/mode'] is None or raw['study/mode'].eval()!=2:
        return 0
    count = raw['table/count']
    if count is None or not 1<=count.eval()<=5 or int(count.eval())!=count.eval():
        return 0
    count = int(count.eval())
    item = geo.parent()
    if not item.name.startswith('item') or not item.name[4:].isdigit() or not 1<=int(item.name[4:])<=count:
        return 0
    def pose_for(candidate):
        owner = candidate.parent()
        if owner.par.Tabletype.eval()!='rect':
            return None
        if abs(candidate.par.sx.eval()-1)>1e-9 or abs(candidate.par.sy.eval()-1)>1e-9:
            return None
        return (float(candidate.par.tx.eval())/TD_UNITS_PER_CM,
                float(candidate.par.ty.eval())/TD_UNITS_PER_CM,float(candidate.par.rz.eval()))
    pose = pose_for(geo)
    if pose is None:
        return 0
    others = []
    for sibling in item.parent().children:
        if sibling is item or not sibling.name.startswith('item') or not sibling.name[4:].isdigit():
            continue
        if not 1<=int(sibling.name[4:])<=count:
            continue
        other = sibling.op('table_target_floor_geo')
        if other is not None:
            candidate = pose_for(other)
            if candidate is not None:
                others.append(candidate)
    return rect_floor_join_side(pose,others)

def shared_callback_source(*, join_aware=True, shared_seam=True):
    """Selbstständiger DAT-Code; keine Dateisystemimporte im gespeicherten Graph."""
    header = (
        "from collections import namedtuple\n"
        "DashSegment = namedtuple('DashSegment', 'width_td depth_td x_td y_td')\n"
        "ContinuousOutlineSegment = namedtuple('ContinuousOutlineSegment', 'side width_td depth_td x_td y_td')\n"
        f"TD_UNITS_PER_CM = {TD_UNITS_PER_CM!r}\n"
        f"OUTLINE_THICKNESS_CM = {OUTLINE_THICKNESS_CM!r}\n"
        f"DEFAULT_OUTLINE_THICKNESS_CM = {OUTLINE_THICKNESS_CM!r}\n"
    )
    functions = inspect.getsource(rect_target_dash_segments) + '\n' + inspect.getsource(rect_continuous_outline_segments)
    dispatch = f'''
def paint(scriptOp, role):
    scriptOp.clear()
    if role == 'source_tabletop':
        segments = rect_continuous_outline_segments({TABLETOP_INNER_WIDTH_CM!r}, {TABLETOP_INNER_DEPTH_CM!r})
    elif role == 'target_tabletop':
        segments = rect_target_dash_segments({TABLETOP_INNER_WIDTH_CM!r}, {TABLETOP_INNER_DEPTH_CM!r})
    elif role == 'target_floor':
        segments = rect_target_dash_segments({FLOOR_TARGET_WIDTH_CM!r}, {FLOOR_TARGET_DEPTH_CM!r})
    else:
        raise ValueError('Unbekannte Darstellungsrolle: ' + role)
    for segment in segments:
        half_x, half_y = segment.width_td / 2, segment.depth_td / 2
        polygon = scriptOp.appendPoly(4, closed=True, addPoints=True)
        for index, (dx, dy) in enumerate([(-half_x, -half_y), (half_x, -half_y), (half_x, half_y), (-half_x, half_y)]):
            polygon[index].point.P = (segment.x_td + dx, segment.y_td + dy, 0)
'''
    if not join_aware:
        return header + functions + dispatch
    clip_source = inspect.getsource(joined_rect_floor_segments)
    if not shared_seam:
        clip_source = clip_source.replace('    result.extend(joined_rect_seam_segments(segments, side))\n', '')
    dependencies = ('import math\n' + f'RECT_DEPTH_CM = {RECT_DEPTH_CM!r}\n'
        + inspect.getsource(rect_floor_join_side) + '\n'
        + (inspect.getsource(joined_rect_seam_segments) + '\n' if shared_seam else '')
        + clip_source + '\n'
        + inspect.getsource(floor_join_side_for_geo))
    dispatch = dispatch.replace('    for segment in segments:',
        "    if role == 'target_floor':\n"
        "        binding = getattr(scriptOp.par, 'Joiningside', None)\n"
        "        if binding is not None:\n"
        "            segments = joined_rect_floor_segments(segments, binding.eval())\n"
        "    for segment in segments:")
    return header + functions + dependencies + dispatch


def adapted_callback(previous, role, shared_path):
    """Bestehende Scout-Kontur erhalten, Rect an zentralen Style-DAT delegieren."""
    assert previous.count('def onCook(scriptOp):') == 1
    previous = previous.replace('def onCook(scriptOp):', 'def _legacy_onCook(scriptOp):', 1)
    return previous + f'''

# aisi_study_visual_style: Rect verwendet die vorhandene Study-Gestaltung.
def onCook(scriptOp):
    if scriptOp.parent().par.Tabletype.eval() == 'rect':
        op({shared_path!r}).module.paint(scriptOp, {role!r})
    else:
        _legacy_onCook(scriptOp)
'''
