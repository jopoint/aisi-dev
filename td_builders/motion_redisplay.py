"""Per-table display fade after completed guidance reactivates; no pose writes."""
import math

KEY = 'motion_redisplay_events'
DURATION = .35


def begin_frame(owner, engine):
    token = (id(engine), engine.revision, engine.started)
    events = owner.fetch(KEY, None)
    if not isinstance(events, dict) or events.get('token') != token:
        events = {'token': token, 'tables': {}}
        owner.store(KEY, events)
        owner.storeStartupValue(KEY, None)
    return events


def visibility(events, identity, previous_phase, phase, now, valid=True):
    if not math.isfinite(now):
        raise ValueError('Nonfinite redisplay time')
    times = events['tables']
    if valid and previous_phase == 'completed' and phase == 'guidance':
        times[identity] = now
    if phase != 'guidance':
        times.pop(identity, None)
        return 1.0
    if identity not in times:
        return 1.0
    t = max(0.0, min(1.0, (now-times[identity])/DURATION))
    if t >= 1:
        times.pop(identity, None)
        return 1.0
    return t*t*(3-2*t)
