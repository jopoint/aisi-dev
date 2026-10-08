from collections import Counter
from copy import deepcopy
from dataclasses import replace
import unittest
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
)


def single_state(rotation=0):
    return SceneState(ROI(0,0,500,500),[TableState('a',250,250,rotation,160,80,table_type='rect')],'groupwork')


def editor_state():
    return build_scene_state_from_dict(_normalize_scene_for_aisi(scene_payload(make_default_tables(),chairs=[],persons=[])),learning_format='groupwork')


class GroupworkSeatTests(unittest.TestCase):
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

    def test_invalid_requests_are_rejected_before_search(self):
        state=editor_state()
        for people,groups in ((0,1),(3,0),(3,4),(10,6),(41,1),(3.5,1)):
            with self.subTest(people=people,groups=groups),self.assertRaises(LayoutConstraintError):
                plan_participant_groupwork(state,people,groups,table_policy='few_tables')


if __name__=='__main__':unittest.main()
