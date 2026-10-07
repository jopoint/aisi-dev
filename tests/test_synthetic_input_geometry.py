from collections import Counter
from copy import deepcopy
from dataclasses import replace
import unittest
from unittest.mock import patch

from aisi.app.sim_layout_rules import compute_synthetic_layout, validate_synthetic_input_geometry
from aisi.app.sim_room_editor import make_default_tables, scene_payload
from aisi.app.sim_scene_to_osc import prepare_scene_output, send_chairs
from aisi.core.table_geometry import circle_inside_convex_polygon, circle_intersects_convex_polygon
from aisi.generation.adaptive_layout_v1 import LayoutConstraintError


def scene():
    return scene_payload(make_default_tables(), chairs=[], persons=[])


def plan(raw, count=15, side=None):
    return compute_synthetic_layout(raw, 'input', 1.0, {'participants': count, 'presentation_side': side, 'adaptive_layout_preview': True})


class CircleGeometryTests(unittest.TestCase):
    def test_complete_circle_containment_and_corner_collision(self):
        polygon=((0.,0.),(100.,0.),(100.,100.),(0.,100.))
        self.assertTrue(circle_inside_convex_polygon((25,25),25,polygon))
        self.assertFalse(circle_inside_convex_polygon((24,25),25,polygon))
        self.assertFalse(circle_inside_convex_polygon((-30,25),25,polygon))
        self.assertTrue(circle_intersects_convex_polygon((-15,-20),25,polygon))
        self.assertFalse(circle_intersects_convex_polygon((-20,-20),25,polygon))
        self.assertTrue(circle_intersects_convex_polygon((50,50),1,tuple(reversed(polygon))))


class SyntheticInputGeometryTests(unittest.TestCase):
    def test_overcapacity_raises_without_layout_fallback(self):
        with patch('aisi.app.sim_layout_rules.compute_target_layout') as fallback:
            for count in (16,17,30):
                with self.subTest(count=count), self.assertRaises(LayoutConstraintError):
                    plan(scene(),count)
            fallback.assert_not_called()

    def test_osc_preparation_rejects_invalid_request_before_output(self):
        with self.assertRaises(LayoutConstraintError):
            prepare_scene_output(scene(), 'input', 1.0, tracking_only=False,
                                 activity_parameters={'participants':16,'adaptive_layout_preview':True})

    def test_reduced_available_table_capacity_and_five_table_limit(self):
        raw=scene(); raw['tables']=raw['tables'][:2]
        self.assertEqual(len(plan(raw,6).chairs),6)
        with self.assertRaises(LayoutConstraintError): plan(raw,7)
        raw=scene(); extra=deepcopy(raw['tables'][0]); extra['id']='extra'; raw['tables'].append(extra)
        with self.assertRaises(LayoutConstraintError): plan(raw,15)

    def test_cardinal_side_and_diagonal_room_fit_chairs(self):
        raw=scene()
        for table in raw['tables']:
            x,y=table['x_cm']-250,table['y_cm']-250
            table['x_cm']=250+.8*x-.6*y
            table['y_cm']=250+.6*x+.8*y
            table['rotation_deg']+=36.86989765
        for side in (None,'north','east','south','west'):
            with self.subTest(side=side):
                out=plan(raw,15,side)
                validate_synthetic_input_geometry(raw,out)
                self.assertEqual(set(Counter(c['table_id'] for c in out.chairs).values()),{3})
                for c in out.chairs:
                    self.assertGreaterEqual(float(c['x_cm'])-25,0)
                    self.assertLessEqual(float(c['x_cm'])+25,500)

    def test_joint_guard_rejects_blocked_and_displaced_geometry(self):
        raw=scene(); out=plan(raw)
        chairs=deepcopy(out.chairs); chairs[0]['x_cm']=-10
        with self.assertRaises(LayoutConstraintError):
            validate_synthetic_input_geometry(raw,replace(out,chairs=chairs))
        chairs=deepcopy(out.chairs); chairs[1]=deepcopy(chairs[0])
        with self.assertRaises(LayoutConstraintError):
            validate_synthetic_input_geometry(raw,replace(out,chairs=chairs))
        targets=deepcopy(out.table_targets); targets[1]=deepcopy(targets[0])
        with self.assertRaises(LayoutConstraintError):
            validate_synthetic_input_geometry(raw,replace(out,table_targets=targets))

    def test_scene_order_preserves_target_identity_and_chair_order(self):
        raw=scene(); out=plan(raw,5,'north')
        raw['tables'].reverse(); other=plan(raw,5,'north')
        self.assertEqual(out.table_targets,list(reversed(other.table_targets)))
        self.assertEqual(out.chairs,other.chairs)
        self.assertEqual(other,plan(raw,5,'north'))

    def test_fifteen_chair_payloads_use_existing_float_contract_without_network(self):
        messages=[]
        class Recorder:
            def send_message(self,address,value): messages.append((address,value))
        out=plan(scene())
        send_chairs(Recorder(),out.chairs,True)
        self.assertEqual(len(messages),45)
        self.assertEqual(messages[0][0],'/chair/0/x')
        self.assertEqual(messages[-1],('/chair/14/radius',25.0))
        self.assertTrue(all(isinstance(value,float) for _,value in messages))


if __name__=='__main__': unittest.main()
