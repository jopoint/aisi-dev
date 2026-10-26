"""Explicit generation, frozen targets/chairs and additive OSC integration."""
import copy
import queue
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import numpy as np
from pythonosc.osc_packet import OscPacket
from aisi.app.motion_layout_proposal import generate_proposal
from aisi.app.motion_preview_sim import MotionSimulation, make_scenario
from td_builders.motion_chairs import chair_values, chair_state, CHAIRS
from td_builders.motion_osc import MotionOSCReader, PREFIX


SETTINGS=dict(learning_format='input',transformation_strength=1.,adaptive_layout_preview=True,
              participants=8,number_of_groups=2,presentation_side=None,show_chairs=True)


class MotionLayoutProposalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tables,_=make_scenario(5)
        cls.plans={fmt:generate_proposal(cls.tables,dict(SETTINGS,learning_format=fmt))
                   for fmt in ('input','groupwork','discussion')}

    def simulation(self):
        editor=SimpleNamespace(tables=copy.deepcopy(self.tables),running=True,
            root=SimpleNamespace(after=Mock()),redraw=Mock(),clipboard_status=SimpleNamespace(set=Mock()))
        client=Mock()
        return MotionSimulation(editor,client,targets={}),editor,client

    def test_real_planner_each_format_and_chairs_follow_same_table_ids(self):
        for fmt,p in self.plans.items():
            self.assertEqual(p.learning_format,fmt)
            self.assertEqual([i for i,_ in p.targets],[t['id'] for t in self.tables])
            self.assertEqual(len(p.chairs),8)
            self.assertTrue(all(c[3] in dict(p.targets) for c in p.chairs))

    def test_motion_and_chairs_remain_frozen_during_source_movement_and_reordering(self):
        sim,editor,client=self.simulation()
        p=self.plans['input']; sim.activate_proposal(p)
        revision=sim.revision
        reader=MotionOSCReader()
        for frame in range(3):
            editor.tables.reverse()
            editor.tables[0]['x_cm']+=1
            sim.tick()
            values={m.message.address.lstrip('/'):m.message.params[0]
                    for m in OscPacket(client.send.call_args.args[0].dgram).messages}
            self.assertTrue(all(k.startswith(PREFIX) for k in values))
            snapshot=reader.read(values,frame*.05)
        self.assertTrue(snapshot['fresh'])
        self.assertEqual(dict(p.targets),sim.targets)
        self.assertEqual(sim.revision,revision)
        self.assertEqual(sim.proposal.chairs,p.chairs)
        np.testing.assert_allclose(chair_state(values,snapshot)[0,:8,:3],
                                   np.array([c[:3] for c in p.chairs]),rtol=1e-6)
        sim.activate_proposal(self.plans['discussion'])
        self.assertEqual(sim.revision,revision+1)
        self.assertEqual(sim.proposal,self.plans['discussion'])

    def test_failed_generation_retains_revision_targets_and_chairs_atomically(self):
        sim,editor,_=self.simulation(); sim.activate_proposal(self.plans['input'])
        before=(sim.revision,sim.targets,sim.proposal)
        sim.pending=queue.Queue(); sim.pending.put((None,'invalid participant request'))
        sim.poll_proposal()
        self.assertEqual(before,(sim.revision,sim.targets,sim.proposal))
        self.assertIn('Kein neuer Vorschlag',editor.clipboard_status.set.call_args.args[0])

    def test_table_set_change_during_calculation_prevents_commit(self):
        sim,editor,_=self.simulation(); sim.activate_proposal(self.plans['input'])
        revision=sim.revision
        editor.tables.pop()
        with self.assertRaisesRegex(ValueError,'Tischmenge'):
            sim.activate_proposal(self.plans['discussion'])
        self.assertEqual(revision,sim.revision)
        self.assertEqual(sim.proposal,self.plans['input'])

    def test_settings_pass_through_without_enabling_participant_preview(self):
        target=self.tables[0]
        generator=Mock(return_value=SimpleNamespace(table_targets=[dict(
            x_cm=target['x_cm'],y_cm=target['y_cm'],rotation_deg=target['rotation_deg'])],chairs=[]))
        settings=dict(SETTINGS,adaptive_layout_preview=False,transformation_strength=.4)
        p=generate_proposal([target],settings,generator)
        self.assertFalse(generator.call_args.kwargs['activity_parameters']['adaptive_layout_preview'])
        self.assertEqual(generator.call_args.args[2],.4)
        self.assertEqual(p.chairs,())

    def test_invalid_geometry_cannot_be_published_as_a_valid_proposal(self):
        for targets,chairs in (([dict(x_cm=-100,y_cm=0,rotation_deg=0)]*5,[]),
                               ([dict(x_cm=100,y_cm=100,rotation_deg=0)]*5,[])):
            generator=Mock(return_value=SimpleNamespace(table_targets=targets,chairs=chairs))
            with self.assertRaises(ValueError): generate_proposal(self.tables,SETTINGS,generator)
        with self.assertRaises(ValueError): generate_proposal(self.tables,dict(SETTINGS,participants=16))

    def test_computation_runs_once_off_the_tick_path_and_duplicate_click_is_ignored(self):
        sim,editor,_=self.simulation()
        with patch('aisi.app.motion_preview_sim.threading.Thread') as thread:
            sim.request_proposal(SETTINGS)
            sim.request_proposal(SETTINGS)
            sim.tick(); sim.tick()
        thread.assert_called_once()
        thread.return_value.start.assert_called_once()
        self.assertEqual(sim.targets,{})
        self.assertIsNotNone(sim.pending)

    def test_worker_uses_click_snapshot_then_commits_on_editor_thread(self):
        sim,editor,_=self.simulation(); settings=dict(SETTINGS)
        with patch('aisi.app.motion_layout_proposal.generate_proposal',return_value=self.plans['input']) as generate,\
                patch('aisi.app.motion_preview_sim.threading.Thread') as thread:
            sim.request_proposal(settings)
            editor.tables[0]['x_cm']+=10; settings['learning_format']='discussion'
            thread.call_args.kwargs['target']()
            self.assertEqual(sim.targets,{})
            self.assertEqual(generate.call_args.args[0][0]['x_cm'],self.tables[0]['x_cm'])
            self.assertEqual(generate.call_args.args[1]['learning_format'],'input')
        sim.poll_proposal()
        self.assertEqual(sim.revision,2)
        self.assertEqual(sim.proposal,self.plans['input'])

    def test_table_only_planner_failure_does_not_invoke_legacy_fallback(self):
        with patch('aisi.app.sim_layout_rules._compute_with_aisi_pipeline',side_effect=ValueError('invalid layout')),\
                patch('aisi.app.sim_layout_rules.compute_synthetic_layout') as synthetic:
            with self.assertRaisesRegex(ValueError,'invalid layout'):
                generate_proposal(self.tables,dict(SETTINGS,adaptive_layout_preview=False))
            synthetic.assert_not_called()

    def test_old_partial_and_stale_chairs_are_hidden_and_count_shrink_clears_them(self):
        sim,_,client=self.simulation(); sim.activate_proposal(self.plans['input'])
        reader=MotionOSCReader()
        for index in range(2):
            sim.tick()
            values={m.message.address.lstrip('/'):m.message.params[0]
                    for m in OscPacket(client.send.call_args.args[0].dgram).messages}
            snapshot=reader.read(values,index*.05)
        for suffix in ('frame','revision','0/frame','0/session'):
            bad=dict(values); bad[CHAIRS+suffix]-=1
            self.assertFalse(chair_state(bad,snapshot).any())
        self.assertFalse(chair_state(values,dict(snapshot,fresh=False)).any())
        values.update(chair_values([],sim.session,sim.frame,sim.revision))
        self.assertFalse(chair_state(values,snapshot).any())


if __name__=='__main__': unittest.main()
