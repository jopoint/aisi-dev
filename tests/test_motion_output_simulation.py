"""Temporary simulation injection, mode isolation, pixel checks and restoration."""
import ast
from pathlib import Path
import unittest
from unittest.mock import patch
from types import SimpleNamespace
import numpy as np

from test_motion_output_routing import Node,fixture,SYMBOLS
from td_builders import build_motion_output_routing as routing
from td_builders import motion_output_simulation_test as simulation
from td_builders.build_motion_dynamic_mask_preview import mask_expression


class Page:
    def __init__(self,comp,name): self.comp,self.name,self.names=comp,name,[]
    def appendToggle(self,name,**kw):
        self.names.append(name)
        return [getattr(self.comp.par,name)]
    def destroy(self):
        for name in self.names: self.comp.par.values.pop(name,None)
        self.comp.pages.remove(self)


def append_page(comp,name):
    if not hasattr(comp,'pages'): comp.pages=[]
    page=Page(comp,name); comp.pages.append(page)
    return page


class MotionOutputSimulationTests(unittest.TestCase):
    def setUp(self):
        self.clock=SimpleNamespace(frame=100)
        original_symbol=routing.symbol
        patches=[patch.object(Node,'appendCustomPage',append_page),
                 patch.object(Node,'customPages',property(lambda n:getattr(n,'pages',[])),create=True),
                 patch.object(Node,'unstore',lambda n,k:n.storage.pop(k,None),create=True),
                 patch.object(routing,'symbol',lambda n:self.clock if n=='absTime' else original_symbol(n))]
        for item in patches:
            item.start(); self.addCleanup(item.stop)

    def fixture(self):
        graph=fixture()
        original=Node(graph,routing.LAYOUT+'reorder_table_mask','render')
        mask=graph[routing.LAYOUT+'null_table_mask']; mask.type='null'; mask.inputs=[original]
        main=Node(graph,routing.MOTION[:-1],'container')
        main.par.Useosc=True; main.par.Demo=False; main.par.Usedat=False; main.par.Oscpath=routing.RAW
        Node(graph,routing.MOTION+'state','script')
        main.store('motion_live_status',{'fresh':True,'signature':(100,10)})
        sim=Node(graph,simulation.SIM,'container'); sim.store('motion_dynamic_simulation_only',True)
        state=sim.create('select','motion_state'); state.par.top=routing.MOTION+'state'
        adapter=sim.create('text','mask_adapter')
        for row in range(5):
            geo=sim.create('container','mask_item_%d' % row)
            for name in ('tx','ty','rz','sx'):
                getattr(geo.par,name).expr=mask_expression(adapter.path,row,name)
        sim.create('render','reorder_simulation_mask').array=np.full((2,2,4),.75,np.float32)
        sim.create('render','out_tabletop').array=np.full((2,2,4),.75,np.float32)
        routing.build(graph.get,SYMBOLS)
        return graph

    def advance(self,graph,fresh=True):
        self.clock.frame+=1
        main=graph[routing.MOTION[:-1]]
        previous=main.fetch('motion_live_status')
        main.store('motion_live_status',{'fresh':fresh,'signature':(100,previous['signature'][1]+1)})

    def launch(self,graph):
        prepared=simulation.start(graph.get,SYMBOLS)
        self.advance(graph)
        activated=simulation.activate(graph.get)
        self.assertTrue(activated['simulation_test_started'])
        report=simulation.check(graph.get)
        report['bypass_pixel_checks']=prepared['bypass_pixel_checks']
        return report

    def test_start_selects_matching_content_and_mask_without_real_source_approval(self):
        graph=self.fixture(); before=routing.snapshot(graph.get)
        report=self.launch(graph)
        self.assertTrue(report['passed']); self.assertTrue(report['active_in_current_mode'])
        self.assertFalse(graph[routing.PATH].par.Sourceapproved.eval())
        self.assertFalse(graph[routing.PATH].par.Enablemotion.eval())
        self.assertEqual(report['tabletop_max_pixel_error'],0)
        self.assertEqual(report['bypass_pixel_checks'],3)
        expected=before.copy()
        for path in before:
            if path!=routing.LAYOUT+'null_table_mask':
                self.assertEqual(routing.signature(graph[path]),expected[path])
        self.assertEqual(graph[routing.LAYOUT+'mask_tabletop'].inputs[1].path,
                         routing.LAYOUT+'null_table_mask')

    def test_stop_restores_exact_previous_graph_and_base_checker(self):
        graph=self.fixture(); paths=set(graph); before=routing.snapshot(graph.get)
        owned=routing.owned_snapshot(graph[routing.PATH],graph[routing.LAYOUT+routing.BRIDGE])
        simulation.start(graph.get,SYMBOLS)
        report=simulation.stop(graph.get)
        self.assertTrue(report['disabled_production_routing_restored'])
        self.assertEqual(set(graph),paths)
        self.assertEqual(routing.snapshot(graph.get),before)
        self.assertEqual(routing.owned_snapshot(graph[routing.PATH],graph[routing.LAYOUT+routing.BRIDGE]),owned)
        self.assertTrue(routing.check(graph.get)['passed'])

    def test_tracking_study_and_calibration_use_legacy_content_and_original_mask(self):
        graph=self.fixture(); self.launch(graph)
        for mode,lp,op in ((0,0,0),(1,0,0),(2,1,0),(2,0,1)):
            graph[routing.RAW].channels={'study/mode':mode}
            graph[routing.LAYOUT+'panel_mode'].channels={'state':lp}
            graph[routing.OUTPUT+'panel_mode'].channels={'state':op}
            report=simulation.check(graph.get)
            self.assertFalse(report['active_in_current_mode'])
            actual=routing.digest(graph[routing.LAYOUT+'null_table_mask'])
            expected=routing.digest(graph[routing.LAYOUT+'reorder_table_mask'])
            self.assertEqual(actual,expected)

    def test_stale_stream_can_prepare_bypass_but_cannot_activate(self):
        graph=self.fixture(); paths=set(graph)
        graph[routing.MOTION[:-1]].store('motion_live_status',{'fresh':False,'signature':(100,10)})
        report=simulation.start(graph.get,SYMBOLS)
        self.assertTrue(report['simulation_test_prepared'])
        self.assertFalse(report['simulation_test_started'])
        self.advance(graph,fresh=False)
        self.assertFalse(simulation.activate(graph.get)['simulation_test_started'])
        self.assertFalse(graph[routing.PATH].par.Simulationtest.eval())
        simulation.stop(graph.get)
        self.assertEqual(set(graph),paths)

    def test_stop_without_session_verifies_bypass_and_changes_nothing(self):
        graph=self.fixture(); paths=set(graph); before=routing.snapshot(graph.get)
        report=simulation.stop(graph.get)
        self.assertFalse(report['simulation_test_stopped'])
        self.assertTrue(report['disabled_production_routing_verified'])
        self.assertEqual(set(graph),paths)
        self.assertEqual(routing.snapshot(graph.get),before)

    def test_separate_pixel_verification_failure_rolls_back_to_disabled_production(self):
        graph=self.fixture(); paths=set(graph); before=routing.snapshot(graph.get)
        graph[simulation.SIM+'/out_tabletop'].array=np.zeros((2,2,4),np.float32)
        simulation.start(graph.get,SYMBOLS)
        self.advance(graph)
        simulation.activate(graph.get)
        report=simulation.verify(graph.get)
        self.assertFalse(report['passed'])
        self.assertTrue(report['disabled_production_routing_restored'])
        self.assertEqual(set(graph),paths)
        self.assertEqual(routing.snapshot(graph.get),before)
        self.assertTrue(routing.check(graph.get)['passed'])

    def test_changes_to_the_temporary_mask_bridge_are_not_discarded(self):
        graph=self.fixture(); simulation.start(graph.get,SYMBOLS)
        bridge=graph[routing.LAYOUT+simulation.BRIDGE]; bridge.par.top='/local/manual/edit'
        paths=set(graph)
        with self.assertRaisesRegex(RuntimeError,'lokal verändert'): simulation.stop(graph.get)
        self.assertEqual(set(graph),paths)
        self.assertEqual(bridge.par.top.val,'/local/manual/edit')

    def test_existing_simulation_mask_needs_time_dependency_fix(self):
        graph=self.fixture(); paths=set(graph)
        graph[simulation.SIM+'/mask_item_4'].par.tx.expr='some_old_expression'
        with self.assertRaisesRegex(RuntimeError,'Frame-Bindung'): simulation.start(graph.get,SYMBOLS)
        self.assertEqual(set(graph),paths)

    def test_repeated_start_does_not_overwrite_registered_test(self):
        graph=self.fixture(); simulation.start(graph.get,SYMBOLS)
        with self.assertRaisesRegex(RuntimeError,'läuft bereits'): simulation.start(graph.get,SYMBOLS)
        self.assertTrue(simulation.stop(graph.get)['simulation_test_stopped'])

    def test_turning_test_toggle_off_uses_original_mask_and_can_still_be_stopped(self):
        graph=self.fixture(); self.launch(graph)
        graph[routing.PATH].par.Simulationtest=False
        self.assertFalse(simulation.check(graph.get)['active_in_current_mode'])
        self.assertEqual(routing.digest(graph[routing.LAYOUT+'null_table_mask']),
                         routing.digest(graph[routing.LAYOUT+'reorder_table_mask']))
        self.assertTrue(simulation.stop(graph.get)['disabled_production_routing_restored'])

    def add_chairs(self,graph):
        from td_builders.build_motion_layout_chairs import PATH,MARK
        comp=Node(graph,PATH,'container'); comp.store(MARK,True)
        comp.create('render','out_chairs').array=np.full((2,2,4),.6,np.float32)

    def test_generated_chairs_share_gate_and_restore_original_composition_input(self):
        graph=self.fixture(); self.add_chairs(graph)
        before=routing.snapshot(graph.get); paths=set(graph)
        report=self.launch(graph)
        self.assertEqual(report['chair_index'],1)
        composite=graph[routing.LAYOUT+'composite_floor_with_synth_chairs']
        self.assertEqual(composite.inputs[1].path,routing.LAYOUT+simulation.CHAIR_BRIDGE)
        for mode,lp,op in ((0,0,0),(1,0,0),(2,1,0),(2,0,1)):
            graph[routing.RAW].channels={'study/mode':mode}
            graph[routing.LAYOUT+'panel_mode'].channels={'state':lp}
            graph[routing.OUTPUT+'panel_mode'].channels={'state':op}
            report=simulation.check(graph.get)
            self.assertEqual(report['chair_index'],0)
            self.assertEqual(routing.digest(composite.inputs[1]),
                             routing.digest(graph[routing.LAYOUT+'select_synth_chairs_regular']))
        simulation.stop(graph.get)
        self.assertEqual(set(graph),paths)
        self.assertEqual(routing.snapshot(graph.get),before)

    def test_local_changes_to_generated_chair_bridge_are_preserved(self):
        graph=self.fixture(); self.add_chairs(graph); self.launch(graph)
        bridge=graph[routing.LAYOUT+simulation.CHAIR_BRIDGE]
        bridge.par.top='/manual/chair/source'
        with self.assertRaisesRegex(RuntimeError,'lokal verändert'):
            simulation.stop(graph.get)
        self.assertEqual(bridge.par.top.val,'/manual/chair/source')

    def test_prepare_replaces_active_fixture_test_with_disabled_generated_layout_test(self):
        from td_builders import prepare_motion_layout_simulation as prepare
        from td_builders import start_motion_simulation as launcher
        from td_builders import build_motion_layout_chairs as chairs
        graph=self.fixture(); self.launch(graph)
        def build(resolve,symbols):
            self.add_chairs(graph)
            return {'component':chairs.PATH}
        with patch.object(prepare.importlib,'reload',side_effect=lambda m:m),\
                patch.object(chairs,'build',side_effect=build),\
                patch.object(launcher,'start',return_value={'generated_layouts':True}) as start:
            report=prepare.prepare(graph.get,SYMBOLS)
        start.assert_called_once_with(graph.get,table_count=5,generated_layouts=True)
        self.assertTrue(report['previous_test_stopped'])
        self.assertTrue(report['simulation_test_prepared'])
        self.assertFalse(graph[routing.PATH].par.Simulationtest.eval())
        self.assertIn('original_chair_input',graph[routing.PATH].fetch(simulation.SESSION))
        simulation.stop(graph.get)

    def test_prepare_refuses_foreign_chair_component_before_stopping_active_test(self):
        from td_builders import prepare_motion_layout_simulation as prepare
        from td_builders import build_motion_layout_chairs as chairs
        graph=self.fixture(); self.launch(graph)
        Node(graph,chairs.PATH,'container')
        with patch.object(prepare.importlib,'reload',side_effect=lambda m:m):
            with self.assertRaisesRegex(RuntimeError,'lokal verändert'):
                prepare.prepare(graph.get,SYMBOLS)
        self.assertTrue(graph[routing.PATH].par.Simulationtest.eval())

    def test_cannot_activate_inside_preparation_frame_even_if_cached_status_is_fresh(self):
        graph=self.fixture(); simulation.start(graph.get,SYMBOLS)
        report=simulation.activate(graph.get)
        self.assertFalse(report['simulation_test_started'])
        self.assertFalse(graph[routing.PATH].par.Simulationtest.eval())

    def test_activation_has_no_gpu_hash_or_pixel_readback_that_can_block_osc(self):
        graph=self.fixture(); simulation.start(graph.get,SYMBOLS)
        self.advance(graph)
        with patch.object(routing,'digest',side_effect=AssertionError('blocking GPU read during activation')):
            report=simulation.activate(graph.get)
        self.assertTrue(report['simulation_test_started'])
        self.assertFalse(report['active_output_pixels_verified'])

    def test_new_td_frame_alone_does_not_validate_a_frozen_sender(self):
        graph=self.fixture(); simulation.start(graph.get,SYMBOLS)
        self.clock.frame+=1
        report=simulation.activate(graph.get)
        self.assertFalse(report['simulation_test_started'])
        self.assertFalse(graph[routing.PATH].par.Simulationtest.eval())

    def test_activation_cooks_received_osc_before_source_without_any_gpu_read(self):
        graph=self.fixture(); simulation.start(graph.get,SYMBOLS)
        self.clock.frame+=1
        order=[]
        receiver=Node(graph,'/project1/comp_io/oscin1','oscin')
        receiver.cook=lambda **kw:order.append('receiver')
        graph[routing.RAW].inputs=[receiver]
        graph[routing.RAW].cook=lambda **kw:order.append('raw')
        def update_state(**kw):
            self.assertEqual(order,['receiver','raw'])
            graph[routing.MOTION[:-1]].store('motion_live_status',{'fresh':True,'signature':(100,11)})
        graph[routing.MOTION+'state'].cook=update_state
        with patch.object(routing,'digest',side_effect=AssertionError('GPU readback before activation')):
            report=simulation.activate(graph.get)
        self.assertTrue(report['simulation_test_started'])

    def test_python39_syntax(self):
        paths=[Path('td_builders/motion_output_simulation_test.py')]
        paths.extend(Path('td_builders').glob('*_motion_output_simulation_test.py'))
        for path in paths: ast.parse(path.read_text(),feature_version=(3,9))


if __name__=='__main__': unittest.main()
