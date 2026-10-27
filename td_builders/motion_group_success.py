"""Display-only checkmark barrier, keyed by the existing frozen layout revision."""
import math

KEY = 'motion_group_success_display'


def pop(age):
    x = max(0., min(1., age/.32))-1.
    return max(0., 1.+2.70158*x*x*x+1.70158*x*x)


def step(record, revision, completed, now, visible):
    """Pause display timers while unavailable; never infer arrival from missing IDs."""
    ids = tuple(sorted(completed))
    if record is None or record['revision'] != revision:
        record = dict(revision=revision, ids=ids, last=now, visible=False, ages={}, finish=None)
    if not math.isfinite(now) or now < record['last']:
        raise ValueError('Monotonic display time required')
    dt = now-record['last'] if record['visible'] and visible else 0.
    record['last'] = now
    visible = bool(visible and 1 <= len(ids) <= 5 and ids == record['ids'])
    record['visible'] = visible
    if not visible:
        return record, {identity: 0. for identity in ids}
    for identity, done in completed.items():
        if done:
            record['ages'][identity] = record['ages'][identity]+dt if identity in record['ages'] else 0.
        else:
            record['ages'].pop(identity, None)
    if all(completed.values()):
        record['finish'] = record['finish']+dt if record['finish'] is not None else 0.
    else:
        record['finish'] = None
    scales = {}
    for identity, done in completed.items():
        scale = pop(record['ages'][identity]) if done else 0.
        if record['finish'] is not None and record['finish'] > 1.:
            scale = pop(max(0., 1.32-record['finish']))
        scales[identity] = scale if done else 0.
    return record, scales


def apply(owner, engine, rows, data, now):
    visual = data[5, 1]
    managed = visual[2] > .5
    ready = bool(visual[1] > .5) if managed else True
    age = float(visual[0]) if managed else float(data[5, 0, 1])
    completed = {identity: getattr(engine.tables.get(identity), 'phase', 'guidance') != 'guidance'
                 for identity, *_ in rows}
    healthy = bool(data[5, 0, 2] > .5 and len(rows) > 0
                   and all(data[index, 0, 3] > .5 for index in range(len(rows))))
    record, scales = step(owner.fetch(KEY, None), engine.revision, completed, now,
                          healthy and ready and age >= 3.)
    owner.store(KEY, record)
    owner.storeStartupValue(KEY, None)
    for index, (identity, *_) in enumerate(rows):
        data[index, 5, 2:] = (scales[identity], 1)
