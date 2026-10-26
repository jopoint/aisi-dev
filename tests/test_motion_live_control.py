"""Offline live proposals, content/mask coordinates and transport isolation."""
import copy
import unittest

import numpy as np

from aisi.app.motion_layout_proposal import MotionProposal,generate_proposal
from aisi.app.motion_live_control import MotionLiveSession,content_pose
from test_motion_live_adapter import frame,EPOCH
from td_builders.motion_design import Pose,td_pose
from td_builders.motion_osc import MotionOSCReader
from td_builders.motion_chairs import chair_state


class MotionLiveControlTests(unittest.TestCase):
    def ready(self):
        session=MotionLiveSession()
        session.adapter.ingest(frame(10),0,EPOCH)
        session.adapter.ingest(frame(11),.1,EPOCH+.1)
        return session

    def proposal(self):
        return MotionProposal((('a',Pose(200,100,90)),('b',Pose(400,350,0))),
                              ((200,75,25,'a'),),True,'input')

    def test_world_sources_are_copied_and_only_fresh_sources_can_be_requested(self):
        session=self.ready()
        tables=session.adapter.current_tables(.1)
        tables[0]['x_cm']=0
        self.assertEqual(session.adapter.current_tables(.1)[0]['x_cm'],100)
        with self.assertRaises(ValueError): session.adapter.current_tables(.61)

    def test_content_boundary_matches_observed_original_mask_and_preserves_world(self):
        world=Pose(401.76873779296875,100.10797119140625,90.26195526123047)
        result=content_pose(world)
        expected=td_pose(-.7891974365234374,-.7794385498046875,-90.26195526123047)
        np.testing.assert_allclose(result,expected,atol=1e-10)
        np.testing.assert_allclose(result,(500-world.x,500-world.y,world.r))
        self.assertEqual(world.x,401.76873779296875)

    def test_start_has_no_proposal_or_fixture_targets(self):
        session=self.ready()
        values=session.values(.1)
        self.assertEqual(values['aisi_motion/count'],0)
        self.assertEqual(values['aisi_motion/chairs/count'],0)
        self.assertEqual(session.revision,1)
        self.assertIsNone(session.proposal)

    def test_targets_chairs_and_revision_frozen_during_movement_and_frame_ticks(self):
        session=self.ready()
        proposal=self.proposal()
        session.commit(proposal,.1)
        session.values(.11)
        moving=frame(12)
        moving.furniture[0].pose.x+=10
        session.adapter.ingest(moving,.2,EPOCH+.2)
        values=session.values(.2)
        self.assertEqual(session.revision,2)
        self.assertEqual(session.proposal,proposal)
        self.assertEqual(values['aisi_motion/table/a/source_x'],390)
        self.assertEqual(values['aisi_motion/table/a/target_x'],300)
        self.assertEqual(values['aisi_motion/chairs/0/x'],300)
        self.assertEqual(values['aisi_motion/chairs/0/y'],425)

    def test_stale_camera_blanks_chairs_and_sources_even_if_transport_keeps_advancing(self):
        session=self.ready()
        session.commit(self.proposal(),.1)
        session.values(.1)
        values=session.values(.7)
        self.assertEqual(values['aisi_motion/table/a/valid'],0)
        self.assertEqual(values['aisi_motion/chairs/visible'],0)
        self.assertEqual(values['aisi_motion/camera/fresh'],0)
        self.assertEqual(session.revision,2)

    def test_removed_id_is_hidden_and_never_replaced_by_another_source(self):
        session=self.ready()
        session.commit(self.proposal(),.1)
        session.adapter.ingest(frame(12,('b','new')),.2,EPOCH+.2)
        values=session.values(.2)
        self.assertEqual(values['aisi_motion/table/a/valid'],0)
        self.assertEqual(values['aisi_motion/table/b/valid'],1)
        self.assertNotIn('aisi_motion/table/new/source_x',values)
        self.assertEqual(session.revision,2)

    def test_inventory_change_and_stale_activation_preserve_entire_previous_proposal(self):
        for stale in (False,True):
            with self.subTest(stale=stale):
                session=self.ready()
                session.commit(self.proposal(),.1)
                before=copy.deepcopy(session.proposal)
                if not stale: session.adapter.ingest(frame(12,('b',)),.2,EPOCH+.2)
                with self.assertRaises(ValueError):
                    session.commit(self.proposal(),.7 if stale else .2)
                self.assertEqual(session.proposal,before)
                self.assertEqual(session.revision,2)

    def test_full_proposal_reactivation_commits_once_to_existing_osc_and_chair_readers(self):
        session=self.ready()
        session.commit(self.proposal(),.1)
        reader=MotionOSCReader()
        reader.read(session.values(.11),.11)
        values=session.values(.12)
        snapshot=reader.read(values,.12)
        self.assertTrue(snapshot['fresh'])
        self.assertTrue(all(k.startswith('aisi_motion/') for k in values))
        self.assertEqual({row[0] for row in snapshot['rows']},{'a','b'})
        np.testing.assert_allclose(chair_state(values,snapshot)[0,0,:3],(300,425,25))
        proposal=MotionProposal(self.proposal().targets,((210,75,25,'a'),),True,'discussion')
        session.commit(proposal,.13)
        self.assertEqual(session.revision,3)
        values=session.values(.14)
        self.assertEqual(values['aisi_motion/chairs/0/x'],290)
        self.assertEqual(reader.read(values,.14)['layout'][2],3)

    def test_real_input_planner_with_one_camera_table_and_two_participants(self):
        session=MotionLiveSession()
        session.adapter.ingest(frame(10,('a',)),0,EPOCH)
        session.adapter.ingest(frame(11,('a',)),.1,EPOCH+.1)
        proposal=generate_proposal(session.adapter.current_tables(.1),dict(
            learning_format='input',participants=2,number_of_groups=1,
            transformation_strength=1.,adaptive_layout_preview=True,show_chairs=True))
        session.commit(proposal,.1)
        self.assertEqual(len(session.proposal.chairs),2)
        self.assertEqual(session.values(.1)['aisi_motion/count'],1)

    def test_initially_arrived_table_reactivates_after_departure_without_new_proposal(self):
        from td_builders.motion_design import MotionLayout
        session=MotionLiveSession()
        session.adapter.ingest(frame(10,('a',)),0,EPOCH)
        session.adapter.ingest(frame(11,('a',)),.1,EPOCH+.1)
        proposal=MotionProposal((('a',Pose(100,200,90)),),((125,200,25,'a'),),True,'input')
        session.commit(proposal,.1)
        layout=MotionLayout(); layout.activate(('osc',session.session,session.revision),.1)
        source=content_pose((100,200,90)); target=source
        state=layout.update('a',source,target,.1)
        self.assertEqual(state.phase,'dissolve')
        session.adapter.ingest(frame(12,('a',)),1.3,EPOCH+1.3)
        layout.update('a',source,target,1.3)
        self.assertEqual(state.phase,'completed')
        moving=frame(13,('a',)); moving.furniture[0].pose.x+=25
        session.adapter.ingest(moving,1.4,EPOCH+1.4)
        values=session.values(1.4)
        self.assertEqual(values['aisi_motion/table/a/active'],1)
        layout.activate(('osc',session.session,session.revision),1.4)
        layout.update('a',content_pose((125,200,90)),target,1.4)
        self.assertEqual(state.phase,'guidance')
        self.assertEqual(session.revision,2)
        self.assertEqual(session.proposal,proposal)
        self.assertEqual(layout.started,.1)
