"""Mute the old AISI content without changing masks or other system modes."""
import ast
import copy
import subprocess
import sys
from pathlib import Path
import unittest
from unittest.mock import patch

import numpy as np
import test_motion_live_output as live_fixtures
from test_motion_output_routing import Node
from td_builders import motion_no_legacy_fallback as blank


class NoLegacyFallbackTests(unittest.TestCase):
    def setUp(self):
        self.helper = live_fixtures.LiveOutputTests()
        self.helper.setUp()
        self.addCleanup(self.helper.doCleanups)
        self.helper.prepare()
        self.graph, self.comp = self.helper.graph, self.helper.comp
        create = Node.create
        def create_with_constant(owner, kind, name):
            result = create(owner, kind, name)
            if kind == 'constant':
                result.array = np.zeros_like(result.array)
            return result
        self.create_patch = patch.object(Node, 'create', create_with_constant)
        self.create_patch.start()
        self.addCleanup(self.create_patch.stop)
        self.symbols = dict(containerCOMP='container', selectTOP='select',
                            constantTOP='constant', switchTOP='switch', outTOP='out')

    def prepare(self):
        return blank.prepare(self.graph.get, self.symbols)

    def test_passive_preparation_preserves_every_existing_node_and_flags(self):
        r = blank.live.test.routing
        before = {path:r.signature(node) for path,node in self.graph.items()}
        self.assertTrue(self.prepare()['prepared'])
        for path, value in before.items():
            self.assertEqual(r.signature(self.graph[path]), value, path)
        with self.assertRaises(RuntimeError):
            self.prepare()

    def test_mode_matrix_blanks_only_normal_aisi_and_preserves_original_pixels(self):
        self.prepare()
        r = blank.live.test.routing
        raw = self.graph[r.RAW]
        for mode in (0, 1, 2, 3, None):
            raw.channels = {} if mode is None else {'study/mode':mode}
            for left,right in ((0,0),(1,0),(0,1),(1,1)):
                self.graph[r.LAYOUT+'panel_mode'].channels['state'] = left
                self.graph[r.OUTPUT+'panel_mode'].channels['state'] = right
                expected = int(mode == 2 and left == right == 0)
                owner = self.graph[blank.PATH]
                for role in blank.ROLES:
                    switch = owner.op(role+'_switch')
                    self.assertEqual(switch.par.index.eval(), expected)
                    if expected:
                        self.assertEqual(np.count_nonzero(switch.numpyArray()), 0)
                    else:
                        np.testing.assert_array_equal(switch.numpyArray(), owner.op(role+'_original').numpyArray())

    def test_install_changes_only_three_owned_references_and_keeps_registrations_strict(self):
        r = blank.live.test.routing
        original_live = copy.deepcopy(self.comp.fetch(blank.live.SESSION))
        original_test = copy.deepcopy(self.comp.fetch(blank.live.test.SESSION))
        protected = r.snapshot(self.graph.get)
        self.prepare()
        report = blank.install(self.graph.get)
        self.assertTrue(report['passed'])
        r.assert_snapshot(self.graph.get, protected)
        self.assertEqual(self.comp.fetch(blank.live.test.SESSION), original_test)
        updated = self.comp.fetch(blank.live.SESSION)
        self.assertEqual(updated['expected_protected'], original_live['expected_protected'])
        expected = copy.deepcopy(original_live['expected_owned'])
        for role, node in blank.legacy_nodes(self.comp).items():
            expected[node.path]['parameters']['top'][1] = blank.PATH+'/out_'+role
        self.assertEqual(updated['expected_owned'], expected)
        blank.live.validate(self.graph.get, self.comp)
        self.assertEqual(blank.live.indices(self.comp), dict(floor=0,tabletop=0,simulation_mask=0,simulation_chairs=0))

    def test_gpu_failure_does_not_install_any_reference(self):
        self.prepare()
        previous = copy.deepcopy(self.comp.fetch(blank.live.SESSION))
        self.graph[blank.PATH].op('floor_transparent').array[:] = 1
        with self.assertRaises(RuntimeError):
            blank.install(self.graph.get)
        self.assertEqual(self.comp.fetch(blank.live.SESSION), previous)
        blank.live.validate(self.graph.get, self.comp)

    def test_actual_content_gates_keep_motion_and_other_modes_but_blank_unapproved_aisi(self):
        r = blank.live.test.routing
        switches = [self.comp.op(name+'_switch') for name in ('floor','tabletop','simulation_chairs')]
        baseline = {}
        for mode, approved in ((0,False),(1,False),(2,True)):
            self.graph[r.RAW].channels['study/mode'] = mode
            self.comp.par.Enablemotion = approved
            self.comp.par.Sourceapproved = approved
            baseline[(mode,approved)] = [node.numpyArray().copy() for node in switches]
        self.prepare()
        blank.install(self.graph.get)
        for (mode, approved), images in baseline.items():
            self.graph[r.RAW].channels['study/mode'] = mode
            self.comp.par.Enablemotion = approved
            self.comp.par.Sourceapproved = approved
            for node, image in zip(switches, images):
                np.testing.assert_array_equal(node.numpyArray(), image)
        self.graph[r.RAW].channels['study/mode'] = 2
        self.comp.par.Sourceapproved = False
        for node in switches:
            self.assertEqual(np.count_nonzero(node.numpyArray()), 0)

    def test_rollback_restores_exact_original_references_and_live_registration(self):
        self.prepare()
        original_live = copy.deepcopy(self.comp.fetch(blank.live.SESSION))
        original = {k:n.par.top.val for k,n in blank.legacy_nodes(self.comp).items()}
        blank.install(self.graph.get)
        self.assertTrue(blank.rollback(self.graph.get)['restored'])
        self.assertNotIn(blank.PATH, self.graph)
        self.assertEqual(self.comp.fetch(blank.live.SESSION), original_live)
        self.assertEqual({k:n.par.top.val for k,n in blank.legacy_nodes(self.comp).items()}, original)

    def test_local_edits_are_never_absorbed_or_overwritten(self):
        self.prepare()
        self.comp.op('floor_legacy').par.top = 'local_change'
        with self.assertRaises(RuntimeError):
            blank.install(self.graph.get)
        self.assertEqual(self.comp.op('floor_legacy').par.top.val, 'local_change')

    def test_python39_syntax(self):
        ast.parse(Path('td_builders/motion_no_legacy_fallback.py').read_text(), feature_version=(3,9))

    def test_import_with_td_op_in_builtins_never_runs_old_builder_or_touches_graph(self):
        source = '''import builtins, sys
def forbidden(*args, **kwargs):
    raise AssertionError('Import must not access the live graph')
builtins.op = forbidden
from td_builders import motion_no_legacy_fallback
assert 'td_builders.isolate_aisi_tabletop_targets' not in sys.modules
print('TD-CONTEXT IMPORT OK')
'''
        result = subprocess.run([sys.executable, '-c', source], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('TD-CONTEXT IMPORT OK', result.stdout)
