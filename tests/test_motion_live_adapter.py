"""Synthetic camera -> stable-ID Motion boundary; no live/room claim."""
from datetime import datetime,timezone
import copy
import math
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from aisi.app.motion_live_adapter import MotionLiveAdapter,Pose,inspect_input
from aisi.app.vision_live_to_aisi_scene import read_new_jsonl_lines
from aisi_sensing.core.types import DetectedEntity,FrameEvent,Pose2D
from td_builders.motion_osc import frame_values,MotionOSCReader

EPOCH=datetime(2026,10,23,12,tzinfo=timezone.utc).timestamp()


def frame(index,ids=('a','b'),stamp=None):
    return FrameEvent(
        timestamp_iso=stamp or '2026-10-23T12:00:00Z',frame_id=index,
        furniture=[DetectedEntity(identity,'table',Pose2D(100+30*i,200,math.pi/2))
                   for i,identity in enumerate(ids)],people=[],
        world={'homography_applied':True,'calibration_id':'lab_rect_v1',
               'calibration_plane':'rect_tabletop','plane_height_cm':74})


class MotionLiveAdapterTests(unittest.TestCase):
    def ready(self):
        adapter=MotionLiveAdapter()
        self.assertTrue(adapter.ingest(frame(10),0,EPOCH+.1))
        self.assertTrue(adapter.ingest(frame(11),.1,EPOCH+.2))
        return adapter

    def activate(self,adapter,now=.1):
        adapter.activate(1,{'a':(200,300,90),'b':(300,300,0)},['a'],now)

    def test_retained_first_frame_cannot_activate(self):
        adapter=MotionLiveAdapter()
        adapter.ingest(frame(1),0,EPOCH)
        with self.assertRaisesRegex(ValueError,'Fresh'):
            self.activate(adapter,0)

    def test_polling_same_camera_frame_never_refreshes_timeout(self):
        adapter=self.ready(); self.activate(adapter)
        for now in (.2,.4,.61):
            self.assertFalse(adapter.ingest(frame(11),now,EPOCH+now))
        snapshot=adapter.snapshot(.61)
        self.assertFalse(snapshot['fresh'])
        self.assertTrue(all(not r[3] for r in snapshot['rows']))

    def test_whole_second_capture_stamp_allows_existing_vision_precision(self):
        adapter=MotionLiveAdapter()
        self.assertTrue(adapter.ingest(frame(1),0,EPOCH+.99))
        self.assertTrue(adapter.ingest(frame(2),.01,EPOCH+1.01))
        self.assertTrue(adapter.snapshot(.01)['fresh'])

    def test_stale_or_future_capture_cannot_look_fresh_from_polling(self):
        for wall in (EPOCH+2,EPOCH-1):
            adapter=MotionLiveAdapter()
            self.assertFalse(adapter.ingest(frame(1),0,wall))
            self.assertFalse(adapter.ingest(frame(2),.1,wall))
            self.assertFalse(adapter.snapshot(.1)['fresh'])

    def test_timezone_and_calibration_metadata_are_required(self):
        for field,value in (('timestamp_iso','2026-10-23T12:00:00'),
                            ('homography_applied',False),('calibration_plane','floor'),
                            ('calibration_id',None)):
            data=frame(1)
            if field=='timestamp_iso':
                data.timestamp_iso=value
            else:
                data.world[field]=value
            adapter=MotionLiveAdapter()
            self.assertFalse(adapter.ingest(data,0,EPOCH))

    def test_stable_id_pairing_survives_reordered_frame_entities(self):
        adapter=self.ready(); self.activate(adapter)
        data=frame(12)
        data.furniture.reverse()
        self.assertTrue(adapter.ingest(data,.2,EPOCH+.3))
        rows=adapter.snapshot(.2)['rows']
        self.assertEqual(rows[0],('a',Pose(100,200,90),Pose(200,300,90),True,True))
        self.assertEqual(rows[1],('b',Pose(130,200,90),Pose(300,300,0),True,False))

    def test_missing_table_invalidates_only_its_own_row_immediately(self):
        adapter=self.ready(); self.activate(adapter)
        adapter.ingest(frame(12,('b',)),.2,EPOCH+.3)
        rows=adapter.snapshot(.2)['rows']
        self.assertFalse(rows[0][3]); self.assertTrue(rows[1][3])
        self.assertEqual(rows[0][2],Pose(200,300,90))

    def test_unbound_new_track_cannot_inherit_an_old_target(self):
        adapter=self.ready(); self.activate(adapter)
        adapter.ingest(frame(12,('c','b')),.2,EPOCH+.3)
        rows=adapter.snapshot(.2)['rows']
        self.assertEqual([r[0] for r in rows],['a','b'])
        self.assertFalse(rows[0][3])

    def test_poses_do_not_change_targets_revision_or_activation_flags(self):
        adapter=self.ready(); targets={'a':[200,300,90]}
        adapter.activate(1,targets,['a'],.1)
        targets['a'][0]=999  # Caller mutation must not alter frozen proposal.
        data=frame(12); data.furniture[0].pose.x=220
        adapter.ingest(data,.2,EPOCH+.3)
        snapshot=adapter.snapshot(.2)
        self.assertEqual(snapshot['revision'],1)
        self.assertEqual(snapshot['rows'][0][2],Pose(200,300,90))

    def test_explicit_new_revision_is_required_and_rejected_proposals_are_atomic(self):
        adapter=self.ready(); self.activate(adapter)
        before=copy.deepcopy(adapter.snapshot(.1))
        for revision,targets,active in ((1,{'a':(0,0,0)},['a']),
                                       (2,{'unknown':(0,0,0)},[]),
                                       (2,{'a':(float('nan'),0,0)},[]),
                                       (2,{'a':(0,0,0)},['unknown'])):
            with self.assertRaises(ValueError):
                adapter.activate(revision,targets,active,.1)
            self.assertEqual(adapter.snapshot(.1),before)
        adapter.activate(2,{'a':(210,310,90)},['a'],.1)
        self.assertEqual(adapter.snapshot(.1)['revision'],2)

    def test_camera_restart_or_calibration_change_requires_reset_and_reactivation(self):
        for change in ('restart','calibration'):
            adapter=self.ready(); self.activate(adapter)
            data=frame(1 if change=='restart' else 12)
            if change=='calibration':
                data.world['calibration_id']='different'
            self.assertFalse(adapter.ingest(data,.2,EPOCH+.3))
            self.assertFalse(adapter.ingest(frame(13),.3,EPOCH+.4))
            self.assertFalse(adapter.snapshot(.3)['fresh'])
            adapter.reset_stream()
            adapter.ingest(frame(1),.4,EPOCH+.5)
            adapter.ingest(frame(2),.5,EPOCH+.6)
            self.assertEqual(adapter.snapshot(.5)['rows'],[])
            with self.assertRaises(ValueError):
                self.activate(adapter,.5)  # Revision 1 must not be reused.
            adapter.activate(2,{'a':(200,300,90)},['a'],.5)

    def test_invalid_count_duplicate_id_and_nonfinite_pose_are_hidden(self):
        inputs=[frame(12,tuple('abcdef')),frame(12,('a','a')),frame(12)]
        inputs[-1].furniture[0].pose.x=float('nan')
        for data in inputs:
            adapter=self.ready(); self.activate(adapter)
            self.assertFalse(adapter.ingest(data,.2,EPOCH+.3))
            self.assertTrue(all(not r[3] for r in adapter.snapshot(.2)['rows']))

    def test_synthetic_new_osc_prefix_roundtrip_keeps_invalid_ids_and_targets(self):
        adapter=self.ready(); self.activate(adapter)
        reader=MotionOSCReader()
        for index,now in ((1,.1),(2,.2)):
            rows=adapter.snapshot(now)['rows']
            values=frame_values(rows,100,index,1)
            status=reader.read(values,now)
        self.assertTrue(status['fresh'])
        self.assertEqual(status['rows'],rows)
        self.assertTrue(all(k.startswith('aisi_motion/') for k in values))
        adapter.ingest(frame(12,('b',)),.3,EPOCH+.4)
        rows=adapter.snapshot(.3)['rows']
        status=reader.read(frame_values(rows,100,3,1),.3)
        self.assertTrue(status['fresh'])
        self.assertFalse(status['rows'][0][3])

    def test_nonmonotonic_clock_is_rejected(self):
        adapter=self.ready()
        with self.assertRaises(ValueError):
            adapter.snapshot(0)

    def test_read_only_probe_skips_history_and_requires_new_appended_frames(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'camera.jsonl'
            history=json.dumps(frame(1).to_dict())+'\n'
            path.write_bytes(history.encode())
            called=[]
            def append_new(source,offset,pending):
                called.append(offset)
                if len(called)==1:
                    self.assertEqual(offset,len(history.encode()))
                    with path.open('a') as handle:
                        for index in (10,11):
                            data=frame(index,stamp=datetime.now(timezone.utc).isoformat())
                            handle.write(json.dumps(data.to_dict())+'\n')
                return read_new_jsonl_lines(source,offset,pending)
            with patch('aisi.app.vision_live_to_aisi_scene.read_new_jsonl_lines',side_effect=append_new):
                report=inspect_input(path,.01)
            self.assertTrue(report['ready_for_mapping_check'])
            self.assertEqual(report['accepted_new_frames'],2)
            self.assertFalse(report['td_connected'])
            self.assertFalse(report['network_messages_sent'])

    def test_saved_history_alone_never_passes_readiness_probe(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'camera.jsonl'
            path.write_text(json.dumps(frame(1).to_dict())+'\n')
            report=inspect_input(path,.01)
            self.assertEqual(report['accepted_new_frames'],0)
            self.assertFalse(report['ready_for_mapping_check'])


if __name__=='__main__':
    unittest.main()
