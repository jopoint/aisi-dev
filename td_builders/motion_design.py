"""Reference v1.5 motion state; world centimetres, horizontal Rect long axis.

This module never writes to existing TouchDesigner nodes or opens network ports.
"""
import math
import time
from collections import namedtuple

from td_builders.motion_geometry_compat import load_geometry

_geometry = load_geometry()
get_table_geometry = _geometry.get_table_geometry
rectangle_footprint = _geometry.rectangle_footprint
transform_local_footprint = _geometry.transform_local_footprint
convex_polygons_intersect = _geometry.convex_polygons_intersect
circle_intersects_convex_polygon = _geometry.circle_intersects_convex_polygon

Pose = namedtuple('Pose', 'x y r')
RECT = get_table_geometry('rect')
WIDTH, DEPTH = RECT.nominal_width, RECT.nominal_depth
CORNER = 6.0
NAV_RADIUS = 29.0


def clamp(value):
    return max(0.0, min(1.0, value))


def smooth(value):
    x = clamp(value)
    return x * x * (3 - 2 * x)


def angle_error(a, b):
    return abs((a - b + 90) % 180 - 90)


def reference_pose(x, y, rotation):
    """v1.5 SVG: short X / long Y -> canonical long X / short Y."""
    return Pose(x, y, rotation + 90)


def td_pose(x, y, rotation):
    """Existing geometry transforms -> screen-down world for the content camera.

    Read the existing item, rather than assuming the OSC-to-item conversion.
    This preserves the live graph's observed double-axis inversion.
    """
    return Pose(250 + x / .0052, 250 - y / .0052, -rotation)


def tables_touch(a, b):
    core = rectangle_footprint(WIDTH - 2 * CORNER, DEPTH - 2 * CORNER)
    ac = transform_local_footprint(core, a.x, a.y, a.r)
    bc = transform_local_footprint(core, b.x, b.y, b.r)
    if convex_polygons_intersect(ac, bc):
        return True
    return (any(circle_intersects_convex_polygon(p, 2 * CORNER, bc) for p in ac)
            or any(circle_intersects_convex_polygon(p, 2 * CORNER, ac) for p in bc))


def metrics(pose, target):
    distance = math.hypot(pose.x - target.x, pose.y - target.y)
    angle = angle_error(pose.r, target.r)
    progress = ((1 - clamp((distance - 8) / 180))
                + (1 - clamp((angle - 5) / 60))) / 2
    return distance, angle, progress, distance <= 8 and angle <= 5


class TableMotion:
    def __init__(self, now):
        self.phase = 'guidance'
        self.since = now
        self.time = now
        self.anchor = None
        self.touching = False
        self.baseline = None
        self.contact = 0.0
        self.approach = 0.0
        self.navigation = 0.0
        self.halo = 0.0
        self.exit_since = None
        self.exit_from = 0.0
        self.pulse_radius = 0.0
        self.pulse_opacity = 0.0
        self.fade_since = None
        self.fade_radius = 0.0
        self.last_motion = now
        self.motion_anchor = None

    def update(self, pose, target, now, valid=True, idle=None):
        if not math.isfinite(now) or now < self.time:
            raise ValueError('Monotonic seconds required')
        dt = now - self.time
        self.time = now
        valid = valid and all(math.isfinite(v) for v in (*pose, *target))
        # A started dissolve is time-locked, including through tracking loss.
        if self.phase == 'dissolve':
            if now - self.since >= 1:
                self.phase = 'completed'
            # Keep visual contact history running, as in visualStep v1.5.
            # Only the success phase is locked; poses may leave contact meanwhile.
            locked = True
        else:
            locked = False
        if not valid:
            # Conservative preview policy: hide invalid surfaces, reset contact.
            # No success/reactivation/idle decision from stale or invalid poses.
            self.touching = False
            self.baseline = None
            self.contact = self.approach = self.navigation = self.halo = 0.0
            self.pulse_opacity = 0.0
            self.exit_since, self.exit_from = None, 0.0
            self.fade_since = None
            self.last_motion = now
            self.motion_anchor = None
            return self
        if self.phase == 'completed' and not locked:
            if (math.hypot(pose.x - self.anchor.x, pose.y - self.anchor.y) > 18
                    or angle_error(pose.r, self.anchor.r) > 12):
                # Reactivation resets the machine, not the separate visual state.
                self.phase, self.since, self.anchor = 'guidance', now, None
        if self.phase == 'guidance' and metrics(pose, target)[3]:
            self.phase, self.since, self.anchor = 'dissolve', now, pose

        touch = tables_touch(pose, target)
        if touch:
            self.exit_since = None
            self.contact += (1 - self.contact) * (1 - math.exp(-dt / .18))
            progress = metrics(pose, target)[2]
            if self.baseline is None:
                self.baseline = progress
            self.navigation = clamp((progress - self.baseline) / max(.000001, 1 - self.baseline))
            self.approach += (self.navigation - self.approach) * (1 - math.exp(-dt / .12))
            self.halo = self.approach
        else:
            if self.touching:
                self.exit_since, self.exit_from = now, self.contact
            self.contact = (self.exit_from * (1 - smooth((now - self.exit_since) / .22))
                            if self.exit_since is not None else 0.0)
            self.baseline = None
            self.approach = self.navigation = 0.0
            # self.halo deliberately retains its last size during exit fade.
        self.touching = touch

        if self.motion_anchor is None:
            self.motion_anchor = pose
        if (math.hypot(pose.x - self.motion_anchor.x, pose.y - self.motion_anchor.y) > .3
                or angle_error(pose.r, self.motion_anchor.r) > .2):
            self.last_motion, self.motion_anchor = now, pose
        idle = now - self.last_motion if idle is None else idle
        phase = (idle - 2) % 4.5 if idle > 2 else 99
        # Complete an interrupted pulse before permitting any new schedule.
        if self.fade_since is not None:
            age = now - self.fade_since
            self.pulse_radius = self.fade_radius + age * 45
            self.pulse_opacity = 1 - smooth(age / .18)
            if self.pulse_opacity == 0:
                self.fade_since = None
        elif idle < .12 and self.pulse_opacity > 0:
            self.fade_since, self.fade_radius = now, self.pulse_radius
        elif phase < 1:
            self.pulse_radius, self.pulse_opacity = phase * 105, 1.0
        else:
            self.pulse_opacity = 0.0
        if self.phase == 'dissolve':
            self.navigation = 1.0
            self.pulse_opacity = 0.0
        return self


class MotionLayout:
    """One explicit layout event, independent per-ID completion, no pose trigger."""
    def __init__(self):
        self.revision = None
        self.started = 0.0
        self.tables = {}

    def activate(self, revision, now):
        if revision != self.revision:
            self.revision, self.started = revision, now
            self.tables = {}

    def update(self, table_id, pose, target, now, valid=True):
        if table_id not in self.tables:
            self.tables[table_id] = TableMotion(now)
        return self.tables[table_id].update(pose, target, now, valid)


def demo_pose(age):
    source, target = reference_pose(110, 180, -6), reference_pose(320, 330, 32)
    a, b = smooth((age - 8) / 7), smooth((age - 14) / 4)
    return Pose(source.x + (target.x - source.x) * a,
                source.y + (target.y - source.y) * a,
                source.r + (target.r - source.r) * b)


def td_tick(owner, now=None):
    """Own-COMP callback. Source/target input DAT is the future stable-ID boundary."""
    import numpy as np
    now = time.monotonic() if now is None else float(now)
    engine = owner.fetch('motion_engine', None)
    if engine is None:
        engine = MotionLayout()
        owner.store('motion_engine', engine)
        owner.storeStartupValue('motion_engine', None)
    useosc = getattr(owner.par, 'Useosc', None)
    useosc = bool(useosc.eval()) if useosc is not None else False
    if not useosc:
        engine.activate(('manual',int(owner.par.Layoutrevision.eval())), now)
    age = now - engine.started
    data = np.zeros((6, 6, 4), dtype=np.float32)
    source = Pose(owner.par.Sourcex.eval(), owner.par.Sourcey.eval(), owner.par.Sourcer.eval())
    target = Pose(owner.par.Targetx.eval(), owner.par.Targety.eval(), owner.par.Targetr.eval())
    if owner.par.Demo.eval():
        source = demo_pose(age)
    rows = [('preview_table', source, target, bool(owner.par.Valid.eval()), True)]
    enabled = True
    if useosc:
        from td_builders.motion_osc import MotionOSCReader, PREFIX
        reader = owner.fetch('motion_osc_reader', None)
        if reader is None:
            reader = MotionOSCReader()
            owner.store('motion_osc_reader',reader)
            owner.storeStartupValue('motion_osc_reader',None)
        reader.timeout = float(owner.par.Streamtimeout.eval())
        raw = owner.op(str(owner.par.Oscpath.eval()))
        channels = ({c.name:c.eval() for c in raw.chans() if c.name.startswith(PREFIX)}
                    if raw is not None else {})
        snapshot = reader.read(channels,now)
        enabled = snapshot['fresh']
        if enabled:
            engine.activate(snapshot['layout'],now)
        rows = [(identity,s,t,valid and enabled,active)
                for identity,s,t,valid,active in snapshot['rows']]
        owner.store('motion_live_status',{
            'fresh':enabled,'reason':snapshot['reason'],
            'signature':snapshot['signature'],'ids':[r[0] for r in rows],
            'layout':snapshot['layout'],
        })
        owner.storeStartupValue('motion_live_status',None)
        age = now-engine.started
    elif owner.par.Usedat.eval():
        dat = owner.op('poses')
        rows = []
        for row in range(1, dat.numRows):
            cells = [c.val for c in dat.row(row)]
            if len(cells) != 9:
                raise ValueError('poses: expected nine columns')
            identity = cells[0].strip()
            if not identity or any(r[0] == identity for r in rows):
                raise ValueError('poses: empty or duplicate table_id')
            values = [float(c) for c in cells[1:]]
            rows.append((identity, Pose(*values[:3]), Pose(*values[3:6]),
                         values[6] == 1, values[7] == 1))
    if len(rows) > 5:
        raise ValueError('At most five Rect tables')
    present = {r[0] for r in rows}
    for identity,state in engine.tables.items():
        if identity not in present:
            state.update(Pose(0,0,0),Pose(0,0,0),now,False)
    for index, (identity, source, target, valid, active) in enumerate(rows):
        valid = valid and all(math.isfinite(v) for v in (*source, *target))
        state = engine.update(identity, source, target, now, valid)
        phase = {'guidance': 0, 'dissolve': 1, 'completed': 2}[state.phase]
        # Invalid tables are blank; never upload NaN to the GPU.
        if not valid:
            continue
        success_age = max(0, now - state.since) if phase else 0
        data[index, 0] = (*source, 1)
        data[index, 1] = (*target, int(active))
        data[index, 2] = (1 - state.navigation if phase == 0 else 0,
                          state.contact, state.halo, phase)
        data[index, 3] = (state.pulse_radius, state.pulse_opacity,
                          success_age, 1 - smooth(success_age / .18) if phase else 1)
        data[index, 4] = (WIDTH, DEPTH, CORNER, 0)
    data[5, 0] = (now - engine.started, age, int(enabled), len(rows))
    return data
