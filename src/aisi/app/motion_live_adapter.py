"""Offline-testable live Motion boundary; no sockets, files or TD mutations.

Consumes calibrated FrameEvents directly, rather than the scene adapter's
15-frame retention cache. Coordinates stay in AISI world cm/degrees. The
actual TD mask/coordinate boundary must still be verified before connection.
"""
from __future__ import annotations

from datetime import datetime
import math
from typing import NamedTuple

from aisi.app.vision_live_to_aisi_scene import _tables_from_frame
from aisi_sensing.core.types import FrameEvent


class Pose(NamedTuple):
    x: float
    y: float
    r: float


def pose(values) -> Pose:
    numbers=tuple(values)
    if len(numbers)!=3 or any(isinstance(v,bool) for v in numbers):
        raise ValueError('Expected a three-number pose')
    result=Pose(*(float(v) for v in numbers))
    if not all(math.isfinite(v) for v in result):
        raise ValueError('Nonfinite pose')
    return result


class MotionLiveAdapter:
    """New-frame freshness, stable IDs and explicitly frozen layout targets.

    Caller supplies monotonic ``now`` and local epoch ``wall_now`` explicitly.
    A producer restart requires reset_stream(), then an advancing pair and a
    new layout activation. No pose update activates or recomputes a proposal.
    """
    def __init__(self,timeout: float=.5):
        if not math.isfinite(timeout) or timeout<=0:
            raise ValueError('Positive finite timeout required')
        self.timeout=timeout
        self._last_now=None
        self._revision=0
        self._targets={}
        self._active={}
        self.reset_stream()

    def reset_stream(self):
        self._frame_id=None
        self._captured=None
        self._received=None
        self._confirmed=False
        self._healthy=False
        self._requires_reset=False
        self._calibration=None
        self._sources={}
        self._last_sources={}
        self._targets={}
        self._active={}
        self._reason='waiting for two advancing camera frames'

    def _clock(self,now):
        if not math.isfinite(now) or (self._last_now is not None and now<self._last_now):
            raise ValueError('Monotonic seconds required')
        self._last_now=now

    def ingest(self,frame: FrameEvent,now: float,wall_now: float) -> bool:
        self._clock(now)
        try:
            if self._requires_reset:
                raise ValueError('Stream reset and layout reactivation required')
            if not math.isfinite(wall_now):
                raise ValueError('Finite wall clock required')
            if isinstance(frame.frame_id,bool) or not isinstance(frame.frame_id,int) or frame.frame_id<0:
                raise ValueError('Invalid camera frame ID')
            stamp=datetime.fromisoformat(frame.timestamp_iso.replace('Z','+00:00'))
            if stamp.tzinfo is None:
                raise ValueError('Camera timestamp needs an explicit timezone')
            captured=stamp.timestamp()
            # Vision now_iso() has whole-second precision. Keep that explicit
            # allowance separate from the .5 s monotonic new-frame timeout.
            if not -.05<=wall_now-captured<=self.timeout+1:
                raise ValueError('Old or future camera capture timestamp')
            calibration=frame.world.get('calibration_id')
            if not isinstance(calibration,str) or not calibration.strip():
                raise ValueError('Missing calibration identity')
            tables=_tables_from_frame(frame)
            if len(tables)>5:
                raise ValueError('Motion capacity exceeded')
            sources={identity:pose((t['x_cm'],t['y_cm'],t['rotation_deg']))
                     for identity,t in tables.items()}
            if self._calibration is not None and calibration!=self._calibration:
                self._requires_reset=True
                raise ValueError('Calibration changed; reset and reactivate explicitly')
            if self._frame_id is not None:
                if frame.frame_id<self._frame_id or captured<self._captured:
                    self._requires_reset=True
                    raise ValueError('Camera frame rollback; reset explicitly')
                if frame.frame_id==self._frame_id:
                    if captured!=self._captured or sources!=self._sources:
                        raise ValueError('Camera frame changed without advancing its ID')
                    return False  # Polling the same frame never refreshes time.
            self._confirmed=self._frame_id is not None
            self._frame_id,self._captured,self._received=frame.frame_id,captured,now
            self._calibration,self._sources=calibration,sources
            self._last_sources={k:v for k,v in self._last_sources.items() if k in self._targets}
            self._last_sources.update(sources)
            self._healthy=True
            self._reason='receiving' if self._confirmed else 'waiting for advancing camera frame'
            return True
        except (ValueError,TypeError,KeyError,AttributeError,OverflowError) as error:
            self._healthy=False
            self._reason=str(error)
            return False

    def _fresh(self,now):
        return (self._healthy and self._confirmed and self._received is not None
                and now-self._received<=self.timeout)

    def current_tables(self,now: float):
        """Copy fresh world poses for an explicit proposal request only."""
        self._clock(now)
        if not self._fresh(now):
            raise ValueError('Fresh advancing camera frames required')
        return [dict(id=identity,type='rect',x_cm=p.x,y_cm=p.y,rotation_deg=p.r)
                for identity,p in sorted(self._sources.items())]

    def activate(self,revision: int,targets: dict,active_ids,now: float):
        """Freeze caller-approved world poses; never synthesizes a layout.

        active_ids is explicit: stationary/inactive tables may still be part
        of the proposal and global reveal, without inventing task semantics.
        """
        self._clock(now)
        if not self._fresh(now):
            raise ValueError('Fresh advancing camera frames required for activation')
        if isinstance(revision,bool) or not isinstance(revision,int) or revision<=self._revision:
            raise ValueError('A strictly newer explicit layout revision is required')
        if (not targets or len(targets)>5 or any(not isinstance(k,str) or not k.strip() for k in targets)
                or not set(targets)<=set(self._sources)):
            raise ValueError('Targets must reference currently observed stable table IDs')
        parsed={identity:pose(values) for identity,values in targets.items()}
        active=set(active_ids)
        if not active<=set(parsed):
            raise ValueError('Active IDs must belong to the explicit proposal')
        # Commit only after the complete proposal has been validated.
        self._targets,self._active=parsed,{k:k in active for k in parsed}
        self._revision=revision

    def snapshot(self,now: float):
        self._clock(now)
        fresh=self._fresh(now)
        rows=[]
        for identity,target in sorted(self._targets.items()):
            valid=fresh and identity in self._sources
            # Last pose is retained only as a finite placeholder with valid=0.
            source=self._last_sources[identity]
            rows.append((identity,source,target,valid,self._active[identity]))
        return {'fresh':fresh,'reason':self._reason if fresh or not self._healthy or not self._confirmed
                else 'camera timeout',
                'camera_frame_id':self._frame_id,'calibration_id':self._calibration,
                'revision':self._revision,'rows':rows,
                'coordinate_space':'aisi_world_cm_deg','td_alignment_verified':False}


def inspect_input(source,duration=2.0):
    """Read-only lab probe: skip recorded history, observe only newly appended frames."""
    import time
    from pathlib import Path
    from aisi.app.vision_live_to_aisi_scene import (
        initial_live_offset,read_new_jsonl_lines,_frame_from_json_line)
    if not math.isfinite(duration) or not 0<duration<=30:
        raise ValueError('Probe duration must be between 0 and 30 seconds')
    source=Path(source)
    adapter=MotionLiveAdapter()
    offset,pending=initial_live_offset(source),b''
    end=time.monotonic()+duration
    accepted=0
    error=None
    while time.monotonic()<end:
        try:
            offset,pending,lines=read_new_jsonl_lines(source,offset,pending)
            for line in lines:
                data=_frame_from_json_line(line)
                accepted+=int(adapter.ingest(data,time.monotonic(),time.time()))
                error=None
        except (OSError,ValueError,KeyError,TypeError) as exc:
            error=str(exc)
        time.sleep(min(.05,max(0,end-time.monotonic())))
    status=adapter.snapshot(time.monotonic())
    return {'read_only':True,'input':str(source),'accepted_new_frames':accepted,
            'fresh':status['fresh'],'ready_for_mapping_check':status['fresh'] and error is None,
            'reason':error or status['reason'],'camera_frame_id':status['camera_frame_id'],
            'calibration_id':status['calibration_id'],
            'observed_table_ids':sorted(adapter._sources),
            'layout_activated':False,'td_connected':False,'network_messages_sent':False,
            'td_alignment_verified':False,'physical_validation':'not performed'}


def main():
    import argparse
    import json
    from aisi.app.vision_live_to_aisi_scene import default_input_path
    parser=argparse.ArgumentParser(description='Read-only Motion camera input readiness probe.')
    parser.add_argument('--input',default=str(default_input_path()))
    parser.add_argument('--duration',type=float,default=2)
    args=parser.parse_args()
    print(json.dumps(inspect_input(args.input,args.duration),ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
