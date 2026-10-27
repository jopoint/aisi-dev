"""Request-local memoization keeps candidates, order and mutable results intact."""
from copy import deepcopy
from dataclasses import replace
import unittest
from unittest.mock import patch

from aisi.core.models import ROI,SceneState,TableState
from aisi.analysis import rect_groupwork_adaptive_prototype as solver


class GroupworkOptionCacheTests(unittest.TestCase):
    def scene(self):
        return SceneState(ROI(0,0,500,500),[
            TableState('a',180,220,90,160,80,table_type='rect'),
            TableState('b',320,220,90,160,80,table_type='rect')],'groupwork')

    def solve(self,scene,cache=None):
        return solver.solve_rect_groupwork_prototype(scene,selection='source_movement',
            cluster_sizes=(2,),candidate_filter=lambda candidate:True,
            disjoint_regions=True,option_cache=cache)

    def test_cached_and_uncached_results_are_identical_and_candidates_reused(self):
        scene, cache = self.scene(), {}
        expected = self.solve(scene)
        with patch.object(solver,'_group_options',wraps=solver._group_options) as generate:
            first = self.solve(scene,cache)
            count = generate.call_count
            self.assertGreater(count,0)
            second = self.solve(scene,cache)
            self.assertEqual(generate.call_count,count)
        self.assertEqual(first,expected)
        self.assertEqual(second,expected)

    def test_results_do_not_share_mutable_targets_across_partitions_or_calls(self):
        scene, cache = self.scene(), {}
        first = self.solve(scene,cache)
        expected = deepcopy(first)
        first.table_targets[0].target_x = -999
        second = self.solve(scene,cache)
        self.assertEqual(second,expected)
        self.assertIsNot(second.table_targets[0],first.table_targets[0])

    def test_changed_source_roi_and_shape_never_reuse_wrong_context(self):
        cache = {}
        self.solve(self.scene(),cache)
        for kind in ('pose','roi','shape','rotation'):
            scene = self.scene()
            if kind == 'pose': scene.tables[0].x += 4
            if kind == 'roi': scene.roi = ROI(0,0,510,510)
            if kind == 'shape': scene.tables[0].width += 2
            if kind == 'rotation': scene.tables[0].rot_deg += 1
            expected = self.solve(scene)
            actual = self.solve(scene,cache)
            self.assertEqual(actual,expected,kind)
