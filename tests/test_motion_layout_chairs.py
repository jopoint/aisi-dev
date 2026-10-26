"""TD 3.9 syntax and optional native two-input shader verification."""
import ast
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import numpy as np

RUNNER=os.environ.get('AISI_MOTION_CHAIR_RUNNER','')


class ChairSyntaxTests(unittest.TestCase):
    def test_td_scripts_parse_on_python_39(self):
        for name in ('motion_chairs.py','build_motion_layout_chairs.py',
                     'prepare_motion_layout_simulation.py','motion_output_simulation_test.py',
                     'start_motion_simulation.py'):
            ast.parse(Path('td_builders',name).read_text(),feature_version=(3,9))


class ChairBuilderTests(unittest.TestCase):
    def graph(self):
        from test_motion_output_routing import Node,fixture
        from td_builders import build_motion_output_routing as routing
        graph=fixture()
        motion=Node(graph,routing.MOTION[:-1],'container'); motion.par.Useosc=True
        Node(graph,routing.MOTION+'state','script')
        return graph

    def build(self,graph):
        from test_motion_output_routing import Node
        from td_builders.build_motion_layout_chairs import build
        symbols=dict(containerCOMP='container',textDAT='text',scriptTOP='script',
                     selectTOP='select',glslTOP='glsl',outTOP='out')
        def page(node,name):
            return SimpleNamespace(appendFloat=lambda n:[getattr(node.par,n)])
        with patch.object(Node,'appendCustomPage',page):
            return build(graph.get,symbols)

    def test_builder_is_isolated_and_has_two_ordered_shader_inputs(self):
        from td_builders import build_motion_output_routing as routing
        from td_builders.build_motion_layout_chairs import PATH
        graph=self.graph(); before=routing.snapshot(graph.get)
        self.assertTrue(self.build(graph)['compiled'])
        self.assertEqual(routing.snapshot(graph.get),before)
        self.assertEqual([n.path for n in graph[PATH+'/render_chairs'].inputs],
                         [PATH+'/motion_state',PATH+'/chair_state'])

    def test_compile_failure_removes_only_new_component(self):
        from td_builders import build_motion_output_routing as routing
        graph=self.graph(); paths=set(graph)
        with patch.object(routing,'digest',side_effect=RuntimeError('compile failed')):
            with self.assertRaisesRegex(RuntimeError,'compile failed'): self.build(graph)
        self.assertEqual(set(graph),paths)


@unittest.skipUnless(RUNNER and Path(RUNNER).is_file(),'optional two-input native GPU runner not configured')
class ChairGpuTests(unittest.TestCase):
    def render(self,enabled=1,age=4,occupied=False,visible=1):
        state=np.zeros((6,6,4),np.float32); state[5,0]=(4,age,enabled,1)
        if occupied:
            state[0,0]=(100,100,0,1); state[0,4]=(160,80,6,0)
        chairs=np.zeros((1,16,4),np.float32); chairs[0,0]=(100,100,25,visible)
        with tempfile.TemporaryDirectory(prefix='aisi-chair-test-') as folder:
            folder=Path(folder)
            state.tofile(folder/'state.bin'); chairs.tofile(folder/'chairs.bin')
            result=subprocess.run([RUNNER,'td_builders/motion_chairs.frag',str(folder/'state.bin'),
                str(folder/'pixels.bin'),'0',str(folder/'chairs.bin')],capture_output=True,text=True,timeout=20)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertIn('Render GL status: 0',result.stdout)
            return np.fromfile(folder/'pixels.bin',np.uint8).reshape(500,500,4)

    def test_actual_shader_draws_white_ring_at_world_position_with_empty_center(self):
        pixels=self.render()
        lit=pixels[:,:,0]>127
        self.assertGreater(lit.sum(),250)
        self.assertLess(lit.sum(),500)
        self.assertFalse(lit[395:405,95:105].any())
        self.assertTrue(lit[395:405,121:126].any())
        self.assertFalse(lit[75:125,75:125].any())
        np.testing.assert_array_equal(pixels[:,:,0],pixels[:,:,1])
        np.testing.assert_array_equal(pixels[:,:,0],pixels[:,:,3])

    def test_stale_tracking_and_hidden_chairs_leave_no_projection(self):
        self.assertFalse(self.render(enabled=0).any())
        self.assertFalse(self.render(visible=0).any())

    def test_chairs_respect_reveal_and_current_source_footprint(self):
        self.assertFalse(self.render(age=0).any())
        self.assertFalse(self.render(occupied=True).any())
        self.assertTrue(self.render(age=3).any())
