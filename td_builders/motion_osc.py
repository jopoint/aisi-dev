"""Optional simulation stream on the existing OSC receiver, Python 3.9 safe.

No network listener. New prefix only; existing table/study channels untouched.
"""
import math
from urllib.parse import quote, unquote

PREFIX = 'aisi_motion/'
MAX_COUNTER = 8_000_000  # Exact in float32 CHOP channels.


def frame_values(rows, session, frame, revision):
    """Ordered channels for one OSC bundle; global frame is the commit marker."""
    if not (1 <= session <= MAX_COUNTER and 1 <= frame <= MAX_COUNTER):
        raise ValueError('session/frame outside exact float32 counter range')
    if not 1 <= revision <= MAX_COUNTER or len(rows) > 5:
        raise ValueError('Invalid revision or table capacity')
    values = {}
    ids = set()
    for identity, source, target, valid, active in rows:
        if not identity or identity in ids:
            raise ValueError('Empty/duplicate table_id')
        ids.add(identity)
        if not all(math.isfinite(v) for v in (*source,*target)):
            raise ValueError('Nonfinite pose')
        base = PREFIX + 'table/' + quote(identity,safe='') + '/'
        for name,value in zip(('source_x','source_y','source_r',
                               'target_x','target_y','target_r'),(*source,*target)):
            values[base+name] = float(value)
        values[base+'valid'],values[base+'active'] = int(valid),int(active)
        values[base+'session'],values[base+'frame'] = session,frame
    values[PREFIX+'count'] = len(rows)
    values[PREFIX+'revision'] = revision
    values[PREFIX+'session'] = session
    values[PREFIX+'frame'] = frame
    return values


class MotionOSCReader:
    def __init__(self, timeout=.5):
        self.timeout = timeout
        self.signature = None
        self.received = None
        self.confirmed = False
        self.layout = None
        self.rows = []

    def read(self, channels, now):
        """Reject retained startup values, incomplete packets and stale frames."""
        from td_builders.motion_design import Pose
        try:
            session = channels[PREFIX+'session']
            frame = channels[PREFIX+'frame']
            revision = channels[PREFIX+'revision']
            count = channels[PREFIX+'count']
            if any(not math.isfinite(v) or int(v) != v for v in (session,frame,revision,count)):
                raise ValueError('Invalid integer metadata')
            if not (1 <= session <= MAX_COUNTER and 1 <= frame <= MAX_COUNTER
                    and 1 <= revision <= MAX_COUNTER and 0 <= count <= 5):
                raise ValueError('Metadata out of range')
            signature = (session,frame)
            rows = []
            for name,value in channels.items():
                if not name.startswith(PREFIX+'table/') or not name.endswith('/frame'):
                    continue
                base = name[:-len('frame')]
                if value != frame or channels.get(base+'session') != session:
                    continue  # Retained channel from a missing table or old sender.
                identity = unquote(base[len(PREFIX+'table/'):-1])
                numbers = [channels[base+k] for k in (
                    'source_x','source_y','source_r','target_x','target_y','target_r','valid','active')]
                if not identity or not all(math.isfinite(v) for v in numbers):
                    raise ValueError('Invalid pose or identity')
                if numbers[6] not in (0,1) or numbers[7] not in (0,1):
                    raise ValueError('Invalid visibility metadata')
                rows.append((identity,Pose(*numbers[:3]),Pose(*numbers[3:6]),
                             bool(numbers[6]),bool(numbers[7])))
            if len(rows) != count or len({r[0] for r in rows}) != count:
                raise ValueError('Incomplete table set')
            if signature != self.signature:
                if self.signature is not None and session == self.signature[0] and frame < self.signature[1]:
                    raise ValueError('Out-of-order frame')
                if self.layout == ('osc',int(session),int(revision)):
                    targets = {row[0]:row[2] for row in self.rows}
                    if any(identity in targets and target != targets[identity]
                           for identity,source,target,valid,active in rows):
                        raise ValueError('Target changed without layout activation')
                # A frozen first frame may have been retained in a saved .toe.
                # Require a subsequent frame from this same sender session.
                self.confirmed = self.signature is not None and self.signature[0] == session
                self.signature, self.received = signature,now
                self.layout = ('osc',int(session),int(revision))
                self.rows = sorted(rows,key=lambda r:r[0])
            fresh = self.confirmed and self.received is not None and now-self.received <= self.timeout
            reason = 'receiving' if fresh else 'waiting for advancing frame / timeout'
        except (KeyError,ValueError,TypeError,OverflowError) as error:
            fresh,reason = False,'invalid/incomplete stream: '+str(error)
        return {'fresh':fresh,'reason':reason,'layout':self.layout,
                'rows':self.rows,'signature':self.signature}
