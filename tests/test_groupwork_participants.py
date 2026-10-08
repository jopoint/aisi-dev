from collections import Counter, OrderedDict
from copy import deepcopy
from dataclasses import replace
import unittest
import math
from unittest.mock import patch

from aisi.app.sim_layout_rules import _normalize_scene_for_aisi
from aisi.app.sim_room_editor import make_default_tables, scene_payload
from aisi.core.models import ROI, SceneState, TableState, TableTarget
from aisi.input.scene_loader import build_scene_state_from_dict
from aisi.analysis.rect_groupwork_adaptive_prototype import enumerate_cluster_partitions
from aisi.generation.adaptive_layout_v1 import LayoutConstraintError
from aisi.generation.layout_constraints import evaluate_hard_constraints
from aisi.generation.groupwork_participants import (
    ParticipantCluster, GroupworkPlan, cluster_seating,
    plan_participant_groupwork, validate_groupwork_plan,
    _improve_floor_spacing,
    _cached_cluster_seating,
)


def single_state(rotation=0):
    return SceneState(ROI(0,0,500,500),[TableState('a',250,250,rotation,160,80,table_type='rect')],'groupwork')


def editor_state():
    return build_scene_state_from_dict(_normalize_scene_for_aisi(scene_payload(make_default_tables(),chairs=[],persons=[])),learning_format='groupwork')


class GroupworkSeatTests(unittest.TestCase):
    def test_seating_cache_keeps_labels_copies_and_foreign_geometry_separate(self):
        state=SceneState(ROI(0,0,500,500),[
            TableState('a',130,250,0,160,80,table_type='rect'),
            TableState('b',370,250,0,160,80,table_type='rect')],'groupwork')
        targets=[TableTarget(t.table_id,t.x,t.y,target_rot_deg=0) for t in state.tables]
        cluster=ParticipantCluster('cluster_a','group_0',('a',),3)
        cache=OrderedDict()
        seats,regions=_cached_cluster_seating(state,targets,cluster,(),cache)
        seats[0]['x_cm']=-999
        relabeled=replace(cluster,group_id='group_1')
        repeated,_=_cached_cluster_seating(state,targets,relabeled,(),cache)
        self.assertTrue(all(s['group_id']=='group_1' for s in repeated))
        self.assertTrue(all(s['x_cm']>=0 for s in repeated))
        self.assertEqual(len(cache),1)
        # A newly occupied foreign footprint must never reuse a prior success.
        blocked=[targets[0],replace(targets[1],target_x=130,target_y=180)]
        with self.assertRaises(LayoutConstraintError):
            _cached_cluster_seating(state,blocked,cluster,(),cache)
        # Changes to occupied seating regions and ROI also invalidate the entry.
        with self.assertRaises(LayoutConstraintError):
            _cached_cluster_seating(state,targets,cluster,regions,cache)
        smaller=deepcopy(state);smaller.roi.y_min=200
        with self.assertRaises(LayoutConstraintError):
            _cached_cluster_seating(smaller,targets,cluster,(),cache)

    def test_singleton_uses_regular_ends_before_dense_long_rows(self):
        for rotation in (0,37,90,180):
            state=single_state(rotation)
            target=[TableTarget('a',250,250,target_rot_deg=rotation)]
            for count in range(1,9):
                with self.subTest(rotation=rotation,count=count):
                    cluster=ParticipantCluster('c','group_0',('a',),count)
                    chairs,regions=cluster_seating(state,target,cluster)
                    kinds=Counter(c['seat_kind'] for c in chairs)
                    self.assertEqual(kinds['regular_end'],min(max(0,count-4),2))
                    self.assertEqual(kinds['dense_long'],max(0,count-6))
                    validate_groupwork_plan(state,GroupworkPlan(target,chairs,(cluster,),(count,),{'c':regions}))

    def test_seven_people_may_use_pair_four_plus_singleton_three(self):
        state=SceneState(ROI(0,0,500,500),[
            TableState('a',140,206,0,160,80,table_type='rect'),
            TableState('b',140,294,0,160,80,table_type='rect'),
            TableState('c',390,250,0,160,80,table_type='rect')],'groupwork')
        targets=[TableTarget(t.table_id,t.x,t.y,target_rot_deg=0) for t in state.tables]
        clusters=(ParticipantCluster('pair','group_0',('a','b'),4),
                  ParticipantCluster('single','group_0',('c',),3))
        plan=GroupworkPlan(targets,[],clusters,(7,),{})
        for cluster in clusters:
            chairs,regions=cluster_seating(state,targets,cluster)
            plan.chairs.extend(chairs);plan.regions[cluster.cluster_id]=regions
        validate_groupwork_plan(state,plan)
        self.assertEqual(Counter(c['cluster_id'] for c in plan.chairs),{'pair':4,'single':3})
        self.assertEqual({c['group_id'] for c in plan.chairs},{'group_0'})
        broken=deepcopy(plan);broken.chairs[0]['group_id']='group_1'
        with self.assertRaises(LayoutConstraintError):validate_groupwork_plan(state,broken)
        blocked=deepcopy(plan);blocked.targets[-1]=replace(blocked.targets[-1],target_x=140,target_y=250)
        with self.assertRaises(LayoutConstraintError):validate_groupwork_plan(state,blocked)

    def test_explicit_cluster_topology_is_complete_and_scene_order_independent(self):
        tables=editor_state().tables
        for sizes in ((1,1,1,1,1),(1,2,2),(1,1,1,2)):
            partitions=enumerate_cluster_partitions(tables,sizes)
            self.assertEqual(partitions,enumerate_cluster_partitions(list(reversed(tables)),sizes))
            for partition in partitions:
                self.assertEqual(sorted(map(len,partition)),sorted(sizes))
                self.assertEqual({t.table_id for cluster in partition for t in cluster},{t.table_id for t in tables})


class GroupworkPlanningTests(unittest.TestCase):
    def test_live_four_groups_do_not_send_upper_left_source_into_distant_pair(self):
        poses=((262.857,211.429,175),(132.143,128.571,145),
               (364.286,83.571,175),(177.143,381.429,195),(398.004,367.143,45))
        state=SceneState(ROI(0,0,500,500),[
            TableState(f'table_{i}',x,y,angle,160,80,table_type='rect')
            for i,(x,y,angle) in enumerate(poses)],'groupwork')
        plan=plan_participant_groupwork(state,14,4)
        validate_groupwork_plan(state,plan)
        targets={t.table_id:t for t in plan.targets}
        distances=[math.dist((t.x,t.y),(targets[t.table_id].target_x,
                                       targets[t.table_id].target_y)) for t in state.tables]
        # Previously table_1 travelled 267 cm into a pair; table_0 moved
        # towards its vacated source. Turning the singleton avoids that detour.
        self.assertLess(distances[1],1.)
        self.assertLess(max(distances),120.)
        self.assertLess(sum(distances),200.)
        self.assertIn(('table_1',),[c.table_ids for c in plan.clusters])
        self.assertEqual(plan,plan_participant_groupwork(state,14,4))
        reversed_state=deepcopy(state);reversed_state.tables.reverse()
        reversed_plan=plan_participant_groupwork(reversed_state,14,4)
        self.assertEqual(plan.targets,list(reversed(reversed_plan.targets)))
        self.assertEqual(plan.clusters,reversed_plan.clusters)
        self.assertEqual(plan.chairs,reversed_plan.chairs)

    def test_valid_source_singletons_are_not_moved_only_to_maximize_gap(self):
        state=SceneState(ROI(0,0,500,500),[
            TableState('a',130,250,0,160,80,table_type='rect'),
            TableState('b',370,250,0,160,80,table_type='rect')],'groupwork')
        targets=[TableTarget(t.table_id,t.x,t.y,target_rot_deg=t.rot_deg) for t in state.tables]
        clusters=tuple(ParticipantCluster(f'cluster_{i}',f'group_{i}',(t.table_id,),3)
                       for i,t in enumerate(state.tables))
        plan=GroupworkPlan(targets,[],clusters,(3,3),{})
        for cluster in clusters:
            seats,regions=cluster_seating(state,targets,cluster)
            plan.chairs.extend(seats);plan.regions[cluster.cluster_id]=regions
        validate_groupwork_plan(state,plan)
        with patch('aisi.generation.groupwork_participants.cluster_seating',
                   side_effect=AssertionError('A strictly worse path must not rebuild seating')):
            result=_improve_floor_spacing(state,plan)
        self.assertEqual(result,plan)

    def test_five_singletons_repair_complete_envelopes_after_local_search_failure(self):
        state=editor_state()
        positions=((112.143,233.571),(187.857,131.429),(386.429,134.286),
                   (160.,384.286),(364.286,326.429))
        for i,(table,(x,y)) in enumerate(zip(state.tables,positions)):
            table.table_id=f'repair_{i}';table.x=x;table.y=y
        with patch('aisi.generation.groupwork_participants.solve_rect_groupwork_prototype',side_effect=ValueError('local search exhausted')):
            plan=plan_participant_groupwork(state,15,5,table_policy='few_tables')
        validate_groupwork_plan(state,plan)
        self.assertEqual(len(plan.chairs),15)

    def test_occupied_envelopes_can_skip_legacy_directed_clearance_explicitly(self):
        state=SceneState(ROI(0,0,500,500),[
            TableState('a',250,100,0,160,200),TableState('b',250,310,0,160,200)],'groupwork')
        targets=[TableTarget(t.table_id,t.x,t.y,target_rot_deg=0) for t in state.tables]
        self.assertGreater(evaluate_hard_constraints(state,targets).clearance_violations,0)
        stats=evaluate_hard_constraints(state,targets,clearance_depth_factor=None)
        self.assertEqual(stats.total_violations,0)

    def test_five_people_on_one_available_table_have_two_two_one(self):
        state=single_state()
        plan=plan_participant_groupwork(state,5,1,table_policy='few_tables')
        validate_groupwork_plan(state,plan)
        self.assertEqual(Counter(c['seat_kind'] for c in plan.chairs),{'regular_long':4,'regular_end':1})

    def test_balanced_participant_groups_keep_all_visible_tables_and_identity(self):
        state=editor_state()
        for people,groups in ((3,2),(7,2),(10,2),(15,5)):
            with self.subTest(people=people,groups=groups):
                plan=plan_participant_groupwork(state,people,groups,table_policy='few_tables')
                validate_groupwork_plan(state,plan)
                self.assertEqual(sum(plan.group_sizes),people)
                self.assertLessEqual(max(plan.group_sizes)-min(plan.group_sizes),1)
                self.assertEqual(len(plan.targets),5)
                other=deepcopy(state);other.tables.reverse()
                reversed_plan=plan_participant_groupwork(other,people,groups,table_policy='few_tables')
                self.assertEqual(plan.targets,list(reversed(reversed_plan.targets)))
                self.assertEqual(plan.chairs,reversed_plan.chairs)
                self.assertEqual(plan.clusters,reversed_plan.clusters)
                self.assertEqual(plan.parked_table_ids,tuple(reversed(reversed_plan.parked_table_ids)))
                self.assertEqual(plan,plan_participant_groupwork(state,people,groups,table_policy='few_tables'))

    def test_table_policies_are_explicit_and_produce_different_valid_plans(self):
        state=editor_state()
        compact=plan_participant_groupwork(state,5,1,table_policy='few_tables')
        preferred=plan_participant_groupwork(state,5,1,table_policy='regular_seats')
        for plan in (compact,preferred):validate_groupwork_plan(state,plan)
        self.assertEqual(sum(len(c.table_ids) for c in compact.clusters),1)
        self.assertEqual(sum(len(c.table_ids) for c in preferred.clusters),2)
        self.assertTrue(all(c['seat_kind']=='regular_long' for c in preferred.chairs))

    def test_default_prefers_three_per_singleton_and_pairs_for_larger_groups(self):
        state=editor_state()
        for people,groups,expected_sizes in ((3,1,[1]),(4,1,[2]),(5,1,[2]),(15,2,[2,2])):
            with self.subTest(people=people,groups=groups):
                plan=plan_participant_groupwork(state,people,groups)
                validate_groupwork_plan(state,plan)
                self.assertEqual(sorted(len(c.table_ids) for c in plan.clusters),expected_sizes)
                self.assertTrue(all(c.participants<=3 for c in plan.clusters if len(c.table_ids)==1))
                self.assertFalse(any(c['seat_kind']=='dense_long' for c in plan.chairs))
        # Three remains an optimum: a single available table may still seat
        # five, using ends before density rather than inventing a hard limit.
        fallback=plan_participant_groupwork(single_state(),5,1)
        self.assertEqual([len(c.table_ids) for c in fallback.clusters],[1])
        self.assertEqual(Counter(c['seat_kind'] for c in fallback.chairs),{'regular_long':4,'regular_end':1})

    def test_padded_floor_contours_reject_physically_separate_singletons(self):
        state=SceneState(ROI(0,0,500,500),[
            TableState('a',160,250,0,160,80,table_type='rect'),
            TableState('b',322,250,0,160,80,table_type='rect')],'groupwork')
        targets=[TableTarget(t.table_id,t.x,t.y,target_rot_deg=0) for t in state.tables]
        clusters=tuple(ParticipantCluster(f'cluster_{i}',f'group_{i}',(t.table_id,),2)
                       for i,t in enumerate(state.tables))
        plan=GroupworkPlan(targets,[],clusters,(2,2),{})
        for c in clusters:
            seats,regions=cluster_seating(state,targets,c)
            plan.chairs.extend(seats);plan.regions[c.cluster_id]=regions
        # Physical 160-cm widths are separate, but 170-cm floor contours overlap.
        self.assertEqual(evaluate_hard_constraints(state,targets,clearance_depth_factor=None).overlap_violations,0)
        with self.assertRaisesRegex(LayoutConstraintError,'Bodenkonturen'):
            validate_groupwork_plan(state,plan)

    def test_invalid_requests_are_rejected_before_search(self):
        state=editor_state()
        for people,groups in ((0,1),(3,0),(3,4),(10,6),(41,1),(3.5,1)):
            with self.subTest(people=people,groups=groups),self.assertRaises(LayoutConstraintError):
                plan_participant_groupwork(state,people,groups,table_policy='few_tables')


if __name__=='__main__':unittest.main()
