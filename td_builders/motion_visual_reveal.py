"""Display-only reveal clock; never modifies engine, poses or layout revision."""
KEY = 'motion_visual_reveal_clock'
AUTO = '/project1/comp_aisi_motion_auto_approval'
ROUTING = '/project1/comp_aisi_motion_output_routing'


def clock(record, revision, now, approved):
    if record is None or record['revision'] != revision:
        record = dict(revision=revision, started=None)
    if approved and record['started'] is None:
        record['started'] = now
    age = max(0., now-record['started']) if record['started'] is not None else 0.
    return record, age


def display_state(owner, engine, now, legacy_age, source_enabled):
    auto = owner.op(AUTO)
    if auto is None or not auto.par.Enabled.eval():
        return legacy_age, True, False
    controller = auto.fetch('approval_runtime', None)
    routing = owner.op(ROUTING)
    key = getattr(controller, 'key', None)
    approved = bool(source_enabled and controller is not None and
                    controller.phase == 'active' and key is not None and
                    tuple(key[0]) == engine.revision and routing is not None and
                    routing.par.Enablemotion.eval() and routing.par.Sourceapproved.eval())
    record, age = clock(owner.fetch(KEY, None), engine.revision, now, approved)
    owner.store(KEY, record)
    owner.storeStartupValue(KEY, None)
    return age, approved, True
