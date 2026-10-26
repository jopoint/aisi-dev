"""Live chair promotion is gated, reversible and preserves original masks."""
import ast
import copy
from pathlib import Path
from unittest.mock import patch
import unittest

import test_motion_output_simulation as fixtures
from test_motion_output_routing import Node,SYMBOLS
from td_builders import motion_output_simulation_test as simulation
from td_builders import motion_live_output as live
from td_builders.build_motion_layout_chairs import PATH as CHAIRS,MARK


class LiveOutputTests(unittest.TestCase):
    def setUp(self):
        self.helper=fixtures.MotionOutputSimulationTests()
        self.helper.setUp()
        self.addCleanup(self.helper.doCleanups)
        self.graph=self.helper.fixture()
        chairs=Node(self.graph,CHAIRS,'container'); chairs.store(MARK,True)
        Node(self.graph,CHAIRS+'/out_chairs','render')
        Node(self.graph,CHAIRS+'/chair_state','script')
        simulation.start(self.graph.get,SYMBOLS)
        self.comp=self.graph[live.test.routing.PATH]
        self.proof={'passed':True,'live_stream':{'fresh':True,'signature':(123,10),
                    'layout':('osc',123,2),'ids':['table_00']},'mask_pixels':{'passed':True}}
        self.proof_patch=patch.object(live.masks,'check',side_effect=lambda *a,**k:copy.deepcopy(self.proof))
        self.proof_patch.start(); self.addCleanup(self.proof_patch.stop)
        self.current_patch=patch.object(live.masks,'current_stream',side_effect=lambda *a:copy.deepcopy(self.proof))
        self.current_patch.start(); self.addCleanup(self.current_patch.stop)

    def prepare(self):
        return live.prepare(self.graph.get)

    def activate(self):
        self.helper.clock.frame+=1
        fresh=copy.deepcopy(self.proof)
        fresh['live_stream']['signature']=(123,11)
        with patch.object(live.masks,'current_sources',return_value=fresh):
            return live.activate(self.graph.get)

    def test_prepare_changes_one_owned_expression_and_keeps_original_registration(self):
        before=simulation.own_snapshot(self.graph.get,self.comp)
        previous=copy.deepcopy(self.comp.fetch(simulation.SESSION))
        report=self.prepare()
        self.assertTrue(report['passed'])
        after=simulation.own_snapshot(self.graph.get,self.comp)
        differences=[p for p in before if before[p]!=after[p]]
        self.assertEqual(differences,[self.comp.path+'/simulation_chairs_switch'])
        self.assertEqual(previous,self.comp.fetch(simulation.SESSION))
        self.assertEqual(live.indices(self.comp),dict(floor=0,tabletop=0,simulation_mask=0,simulation_chairs=0))

    def test_failed_mask_proof_leaves_everything_unchanged(self):
        before=simulation.own_snapshot(self.graph.get,self.comp)
        self.proof['passed']=False
        self.assertFalse(self.prepare()['live_prepared'])
        self.assertEqual(before,simulation.own_snapshot(self.graph.get,self.comp))
        self.assertIsNone(self.comp.fetch(live.SESSION))

    def test_local_chair_edit_is_rejected_without_overwrite(self):
        switch=self.comp.op('simulation_chairs_switch')
        switch.par.index.expr='0'
        with self.assertRaises(RuntimeError): self.prepare()
        self.assertEqual(switch.par.index.expr,'0')

    def test_prepare_refuses_enabled_flags_and_repeated_installation(self):
        self.comp.par.Sourceapproved=True
        with self.assertRaises(RuntimeError): self.prepare()
        self.comp.par.Sourceapproved=False
        self.prepare()
        with self.assertRaises(RuntimeError): self.prepare()

    def test_prepare_bypass_failure_restores_expression_and_registration(self):
        before=simulation.own_snapshot(self.graph.get,self.comp)
        real_digest=live.test.routing.digest
        def digest(node):
            data=real_digest(node)
            if self.comp.op('simulation_chairs_switch').par.index.expr==simulation.content_gate():
                data[1]='injected difference'
            return data
        with patch.object(live.test.routing,'digest',side_effect=digest):
            with self.assertRaises(RuntimeError): self.prepare()
        self.assertEqual(before,simulation.own_snapshot(self.graph.get,self.comp))
        self.assertIsNone(self.comp.fetch(live.SESSION))

    def test_activate_requires_later_frame_and_advancing_same_source_and_layout(self):
        self.prepare()
        self.assertFalse(live.activate(self.graph.get)['passed'])
        self.helper.clock.frame+=1
        for signature,layout,ids in (((123,10),('osc',123,2),['table_00']),
                                    ((124,11),('osc',124,2),['table_00']),
                                    ((123,11),('osc',123,3),['table_00']),
                                    ((123,11),('osc',123,2),['another'])):
            proof=copy.deepcopy(self.proof)
            proof['live_stream'].update(signature=signature,layout=layout,ids=ids)
            with patch.object(live.masks,'current_sources',return_value=proof):
                with self.assertRaises(RuntimeError): live.activate(self.graph.get)
            self.assertFalse(self.comp.par.Sourceapproved.eval())
            self.assertFalse(self.comp.par.Enablemotion.eval())

    def test_live_selects_content_chairs_and_original_mask_with_mode_calibration_gates(self):
        self.prepare()
        self.assertTrue(self.activate()['passed'])
        routing=live.test.routing
        for mode,lp,op in ((2,0,0),(0,0,0),(1,0,0),(2,1,0),(2,0,1)):
            self.graph[routing.RAW].channels['study/mode']=mode
            self.graph[routing.LAYOUT+'panel_mode'].channels['state']=lp
            self.graph[routing.OUTPUT+'panel_mode'].channels['state']=op
            selected=live.indices(self.comp)
            expected=int(mode==2 and lp==op==0)
            self.assertEqual(selected,dict(floor=expected,tabletop=expected,
                                          simulation_chairs=expected,simulation_mask=0))

    def test_failed_verification_disables_both_flags_without_rewiring(self):
        self.prepare(); self.activate()
        before=simulation.own_snapshot(self.graph.get,self.comp)
        self.proof['passed']=False
        with self.assertRaises(RuntimeError): live.verify(self.graph.get)
        self.assertFalse(self.comp.par.Enablemotion.eval())
        self.assertFalse(self.comp.par.Sourceapproved.eval())
        self.assertEqual(before,simulation.own_snapshot(self.graph.get,self.comp))

    def test_verify_requires_fresh_same_proposal_and_complete_chairs(self):
        self.prepare(); self.activate()
        self.proof['live_stream']['signature']=(123,11)
        raw=self.graph[live.test.routing.RAW]
        raw.channels.update({'aisi_motion/chairs/count':2,'aisi_motion/chairs/visible':1})
        status={'fresh':True,'layout':('osc',123,2),'signature':(123,11),'visible_chairs':2}
        self.graph[CHAIRS].store('chair_live_status',status)
        self.assertTrue(live.verify(self.graph.get)['passed'])
        for key,value in (('fresh',False),('layout',('osc',123,1)),
                          ('signature',(123,9)),('visible_chairs',1)):
            with self.subTest(key=key):
                self.comp.par.Enablemotion=True; self.comp.par.Sourceapproved=True
                self.graph[CHAIRS].store('chair_live_status',dict(status,**{key:value}))
                with self.assertRaises(RuntimeError): live.verify(self.graph.get)
                self.assertFalse(self.comp.par.Enablemotion.eval())

    def test_verify_samples_pair_after_gpu_work_and_recooks_cached_chair_state(self):
        self.prepare(); self.activate()
        self.proof['source_mask_matches']=[{'original_mask':'original','max_edge_error_cm':0.01}]
        raw=self.graph[live.test.routing.RAW]
        raw.channels.update({'aisi_motion/chairs/count':2,'aisi_motion/chairs/visible':1})
        events=[]
        original_digest=live.test.routing.digest
        def digest(node):
            events.append('gpu')
            self.graph[CHAIRS].store('chair_live_status',{'fresh':False})
            return original_digest(node)
        def current(resolve):
            events.append('camera')
            proof=copy.deepcopy(self.proof)
            proof['live_stream']['signature']=(123,12)
            return proof
        def cook(**kw):
            events.append('chairs')
            self.graph[CHAIRS].store('chair_live_status',{
                'fresh':True,'signature':(123,12),'layout':('osc',123,2),'visible_chairs':2})
        self.graph[CHAIRS+'/chair_state'].cook=cook
        with patch.object(live.test.routing,'digest',side_effect=digest), \
                patch.object(live.masks,'current_stream',side_effect=current):
            report=live.verify(self.graph.get)
        self.assertTrue(report['passed'])
        self.assertEqual(events[-2:],['camera','chairs'])
        self.assertEqual(report['mask_pixel_signature'],(123,10))
        self.assertEqual(report['live_stream']['signature'],(123,12))
        self.assertEqual(report['source_mask_matches'],self.proof['source_mask_matches'])

    def test_verify_rejects_stale_or_changed_source_after_gpu_work(self):
        self.prepare(); self.activate()
        for change in ({'passed':False},{'layout':('osc',124,2)},
                       {'layout':('osc',123,3)},{'ids':['another']}):
            with self.subTest(change=change):
                self.comp.par.Enablemotion=True; self.comp.par.Sourceapproved=True
                current=copy.deepcopy(self.proof)
                if 'passed' in change: current.update(change)
                else: current['live_stream'].update(change)
                with patch.object(live.masks,'current_stream',return_value=current):
                    with self.assertRaises(RuntimeError): live.verify(self.graph.get)
                self.assertFalse(self.comp.par.Enablemotion.eval())
                self.assertFalse(self.comp.par.Sourceapproved.eval())

    def test_rollback_restores_only_own_expression_and_original_test_registration(self):
        before=simulation.own_snapshot(self.graph.get,self.comp)
        registered=copy.deepcopy(self.comp.fetch(simulation.SESSION))
        self.prepare(); self.activate()
        report=live.rollback(self.graph.get)
        self.assertTrue(report['original_test_registration_preserved'])
        self.assertEqual(before,simulation.own_snapshot(self.graph.get,self.comp))
        self.assertEqual(registered,self.comp.fetch(simulation.SESSION))
        self.assertIsNone(self.comp.fetch(live.SESSION))

    def test_local_edit_blocks_rollback(self):
        self.prepare()
        self.comp.op('simulation_chairs_switch').par.index.expr='0'
        with self.assertRaises(RuntimeError): live.rollback(self.graph.get)
        self.assertEqual(self.comp.op('simulation_chairs_switch').par.index.expr,'0')

    def test_td_scripts_parse_on_python39(self):
        for name in ('motion_live_output.py','check_motion_live_masks.py'):
            ast.parse(Path('td_builders',name).read_text(encoding='utf-8'),feature_version=(3,9))
