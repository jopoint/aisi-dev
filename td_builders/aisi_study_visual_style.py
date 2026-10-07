"""Gemeinsame Rect-Gestaltung aus vorhandenen Study-Geometriefunktionen."""
import inspect
from td_builders.study_target_floor import (
    rect_target_dash_segments, OUTLINE_THICKNESS_CM, FLOOR_TARGET_WIDTH_CM,
    FLOOR_TARGET_DEPTH_CM, TABLETOP_INNER_WIDTH_CM, TABLETOP_INNER_DEPTH_CM,
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


def shared_callback_source():
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
    return header + functions + dispatch


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
