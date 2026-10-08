from collections import Counter
from copy import deepcopy
import unittest
from unittest.mock import patch

from aisi.app.sim_layout_rules import compute_synthetic_layout
from aisi.app.sim_room_editor import make_default_tables, scene_payload
from aisi.app.sim_scene_to_osc import prepare_scene_output, send_chairs, send_tables
from aisi.generation.adaptive_layout_v1 import LayoutConstraintError
from aisi.generation.groupwork_participants import plan_participant_groupwork, transform_groupwork_plan, validate_groupwork_plan
from test_groupwork_participants import editor_state


class Recorder:
    def __init__(self): self.messages = []
    def send_message(self, address, value): self.messages.append((address, value))


class GroupworkPreviewTests(unittest.TestCase):
    def setUp(self):
        self.scene = scene_payload(make_default_tables(), chairs=[], persons=[])
        self.parameters = dict(adaptive_layout_preview=True, participants=5, number_of_groups=1)

    def test_default_adds_pair_above_three_and_keeps_scene_order(self):
        layout = compute_synthetic_layout(self.scene, 'groupwork', 1., self.parameters)
        self.assertEqual(len(layout.active_table_ids), 2)
        self.assertEqual(len(layout.parked_table_ids), 3)
        self.assertEqual(Counter(c['seat_kind'] for c in layout.chairs), {'regular_long':4,'regular_end':1})
        other = deepcopy(self.scene); other['tables'].reverse()
        reversed_layout = compute_synthetic_layout(other, 'groupwork', 1., self.parameters)
        self.assertEqual(layout.table_targets, list(reversed(reversed_layout.table_targets)))
        self.assertEqual(layout.chairs, reversed_layout.chairs)

    def test_zero_is_exact_source_without_solver_or_chairs(self):
        with patch('aisi.generation.groupwork_participants.plan_participant_groupwork', side_effect=AssertionError('no solve')):
            layout = compute_synthetic_layout(self.scene, 'groupwork', 0., self.parameters)
        self.assertEqual(layout.table_targets,[dict(x_cm=t['x_cm'],y_cm=t['y_cm'],rotation_deg=t['rotation_deg']) for t in self.scene['tables']])
        self.assertEqual(layout.chairs, [])

    def test_partial_strength_repairs_without_changing_roles(self):
        state = editor_state()
        for people, groups in ((5,1),(7,2),(15,5)):
            plan = plan_participant_groupwork(state,people,groups)
            for strength in (.25,.5,.75):
                with self.subTest(people=people,groups=groups,strength=strength):
                    result = transform_groupwork_plan(state,plan,strength)
                    validate_groupwork_plan(state,result)
                    self.assertEqual(result,transform_groupwork_plan(state,plan,strength))
                    mutated=transform_groupwork_plan(state,plan,strength); mutated.chairs.clear()
                    self.assertEqual(result,transform_groupwork_plan(state,plan,strength))
                    self.assertEqual(result.clusters,plan.clusters)
                    self.assertEqual(result.parked_table_ids,plan.parked_table_ids)
                    self.assertEqual([t.table_id for t in result.targets],[t.table_id for t in state.tables])

    def test_technical_slot_limit_and_bad_parameters_reject_before_search(self):
        with patch('aisi.generation.groupwork_participants.plan_participant_groupwork', side_effect=AssertionError('no solve')):
            for people,groups in ((16,1),(5.5,1),(5,6),(0,1)):
                with self.subTest(people=people,groups=groups),self.assertRaises(LayoutConstraintError):
                    compute_synthetic_layout(self.scene,'groupwork',1.,dict(self.parameters,participants=people,number_of_groups=groups))

    def test_existing_osc_adapter_owns_groupwork_preview_and_hides_radius(self):
        tables,persons,chairs,targets,reason = prepare_scene_output(self.scene,'groupwork',1.,False,activity_parameters=self.parameters)
        self.assertIsNone(reason); self.assertEqual(len(chairs),5)
        recorder = Recorder(); send_tables(recorder,tables,targets); send_chairs(recorder,chairs,True)
        messages = dict(recorder.messages)
        self.assertEqual(messages['/chair/4/radius'],25.)
        self.assertIs(type(messages['/chair/4/x']),float)
        for i,target in enumerate(targets): self.assertEqual(messages[f'/table/{i}/target_x'],target['x_cm'])
        hidden = Recorder(); send_chairs(hidden,chairs,False)
        self.assertTrue(all(value==0. for address,value in hidden.messages if address.endswith('/radius')))

    def test_normal_modes_remain_without_groupwork_synthesis(self):
        with patch('aisi.app.sim_layout_rules.compute_target_layout',return_value=[]):
            self.assertEqual(compute_synthetic_layout(self.scene,'groupwork',1.,{}).chairs,[])
