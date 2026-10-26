"""Additive chair transport, tied to the same advancing Motion layout/frame."""
import math
from td_builders.motion_osc import PREFIX, MAX_COUNTER, MotionOSCReader

CHAIRS = PREFIX+'chairs/'


def chair_values(chairs, session, frame, revision, visible=True):
    if len(chairs)>15 or any(type(n) is not int or not 1 <= n <= MAX_COUNTER for n in (session,frame,revision)):
        raise ValueError('Invalid chair count/counters')
    values={}
    for i,(x,y,r,_) in enumerate(chairs):
        if not all(math.isfinite(v) for v in (x,y,r)) or r <= 0:
            raise ValueError('Invalid chair geometry')
        base=CHAIRS+str(i)+'/'
        for name,value in (('x',x),('y',y),('radius',r),('session',session),('frame',frame),('revision',revision)):
            values[base+name]=float(value) if name in ('x','y','radius') else value
    values.update({CHAIRS+'count':len(chairs),CHAIRS+'visible':int(visible),
                   CHAIRS+'session':session,CHAIRS+'frame':frame,CHAIRS+'revision':revision})
    return values


def chair_state(channels, snapshot):
    """Reject partial/old chair packets instead of retaining the old layout."""
    import numpy as np
    data=np.zeros((1,16,4),dtype=np.float32)
    try:
        if not snapshot['fresh']:
            return data
        session,frame=snapshot['signature']
        revision=snapshot['layout'][2]
        if any(channels[CHAIRS+k]!=v for k,v in (('session',session),('frame',frame),('revision',revision))):
            return data
        count=channels[CHAIRS+'count']
        visible=channels[CHAIRS+'visible']
        if not math.isfinite(count) or int(count)!=count or not 0 <= count <= 15 or visible not in (0,1):
            return data
        rows=[]
        for i in range(int(count)):
            base=CHAIRS+str(i)+'/'
            if any(channels[base+k]!=v for k,v in (('session',session),('frame',frame),('revision',revision))):
                return data
            x,y,r=[channels[base+k] for k in ('x','y','radius')]
            if not all(math.isfinite(v) for v in (x,y,r)) or not r>0:
                return data
            rows.append((x,y,r,visible))
        for i,row in enumerate(rows):
            data[0,i]=row
    except (KeyError,TypeError,ValueError,OverflowError):
        return np.zeros_like(data)
    return data


def td_tick(owner):
    import time
    from td_builders.build_motion_output_routing import MOTION
    motion=owner.op(MOTION[:-1])
    raw=owner.op(str(motion.par.Oscpath.eval()))
    channels={c.name:c.eval() for c in raw.chans() if c.name.startswith(PREFIX)} if raw is not None else {}
    reader=owner.fetch('chair_reader',None)
    if reader is None:
        reader=MotionOSCReader()
        owner.store('chair_reader',reader)
        owner.storeStartupValue('chair_reader',None)
    reader.timeout=float(motion.par.Streamtimeout.eval())
    snapshot=reader.read(channels,time.monotonic())
    data=chair_state(channels,snapshot)
    status={k:v for k,v in snapshot.items() if k!='rows'}
    status['visible_chairs']=int((data[0,:,3]>.5).sum())
    owner.store('chair_live_status',status)
    owner.storeStartupValue('chair_live_status',None)
    return data
