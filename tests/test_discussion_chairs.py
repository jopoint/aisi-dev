from copy import deepcopy
from dataclasses import replace
import unittest
from unittest.mock import patch

from aisi.app.sim_room_editor import make_default_tables, scene_payload
from aisi.app.sim_layout_rules import compute_synthetic_layout, _normalize_scene_for_aisi
from aisi.app.sim_scene_to_osc import prepare_scene_output, send_chairs
from aisi.input.scene_loader import build_scene_state_from_dict
from aisi.generation.discussion_chairs import plan_discussion_chairs, validate_discussion_chairs
from aisi.generation.adaptive_layout_v1 import LayoutConstraintError


def scene(n=5):
    return scene_payload(make_default_tables()[:n], chairs=[], persons=[])


def state(raw):
    return build_scene_state_from_dict(_normalize_scene_for_aisi(raw), learning_format='discussion')


class DiscussionChairTests(unittest.TestCase):
    def test_counts_geometry_and_scene_order(self):
        for n in range(1,6):
            s=state(scene(n))
            for count in range(1,3*n+1):
                with self.subTest(tables=n,participants=count):
                    p=plan_discussion_chairs(s,count)
                    validate_discussion_chairs(s,p)
                    self.assertEqual(len(p.chairs),count)
                    self.assertEqual([t.table_id for t in p.targets],[t.table_id for t in s.tables])
                    self.assertTrue(all(c['radius_cm']==25 for c in p.chairs))
            reversed_state=replace(s,tables=list(reversed(s.tables)))
            a=plan_discussion_chairs(s,3*n);b=plan_discussion_chairs(reversed_state,3*n)
            self.assertEqual(a.targets,list(reversed(b.targets)))
            self.assertEqual(a.chairs,b.chairs)
            a.chairs[0]['x_cm']=-999
            self.assertNotEqual(a.chairs,plan_discussion_chairs(s,3*n).chairs)

    def test_tangency_and_corner_tolerance_do_not_allow_penetration(self):
        s=state(scene(1));p=plan_discussion_chairs(s,3)
        validate_discussion_chairs(s,p)  # All three touch their own table.
        for change in ({'y_cm':p.chairs[0]['y_cm']-0.01},
                       {'x_cm':p.chairs[0]['x_cm']-2},
                       {'x_cm':-1}, {'radius_cm':26}):
            bad=deepcopy(p);bad.chairs[0].update(change)
            with self.subTest(change=change),self.assertRaises(LayoutConstraintError):
                validate_discussion_chairs(s,bad)
        bad=deepcopy(p);bad.chairs[1].update(x_cm=p.chairs[0]['x_cm'],y_cm=p.chairs[0]['y_cm'])
        with self.assertRaises(LayoutConstraintError): validate_discussion_chairs(s,bad)

    def test_capacity_and_bad_counts(self):
        for n in range(1,6):
            with self.assertRaisesRegex(LayoutConstraintError,'Kapazität'):
                plan_discussion_chairs(state(scene(n)),3*n+1)
        for count in (0,-1,True,2.5,'3',16):
            with self.subTest(count=count),self.assertRaises(LayoutConstraintError):
                compute_synthetic_layout(scene(),'discussion',1.,{'participants':count,'adaptive_layout_preview':True})

    def test_adapter_and_zero_strength(self):
        raw=scene()
        p=compute_synthetic_layout(raw,'discussion',1.,{'participants':15,'adaptive_layout_preview':True})
        self.assertEqual(len(p.chairs),15)
        self.assertEqual(len(p.table_targets),5)
        self.assertEqual(p.parked_table_ids,())
        with patch('aisi.generation.discussion_chairs.plan_discussion_chairs',side_effect=AssertionError):
            zero=compute_synthetic_layout(raw,'discussion',0.,{'participants':15,'adaptive_layout_preview':True})
        self.assertEqual(zero.chairs,[])
        for source,target in zip(raw['tables'],zero.table_targets):
            self.assertEqual((source['x_cm'],source['y_cm'],source['rotation_deg']),
                             (target['x_cm'],target['y_cm'],target['rotation_deg']))

    def test_osc_output_without_network_and_tracking_isolation(self):
        raw=scene();parameters={"participants":15,"adaptive_layout_preview":True}
        tables,persons,chairs,targets,error=prepare_scene_output(raw,"discussion",1.,False,activity_parameters=parameters)
        self.assertEqual(tables,raw["tables"])
        self.assertEqual(len(targets),5)
        self.assertEqual(len(chairs),15)
        self.assertIsNone(error)
        messages=[]
        class Recorder:
            def send_message(self,address,value): messages.append((address,value))
        send_chairs(Recorder(),chairs,True)
        self.assertEqual(len(messages),45)
        self.assertEqual(messages[-1],("/chair/14/radius",25.))
        self.assertTrue(all(type(value) is float for _,value in messages))
        messages.clear();send_chairs(Recorder(),chairs,False)
        self.assertTrue(all(value==0. for address,value in messages if address.endswith("/radius")))
        with patch("aisi.app.sim_scene_to_osc.compute_synthetic_layout",side_effect=AssertionError):
            tracked=prepare_scene_output(raw,"discussion",1.,True,activity_parameters=parameters)
        self.assertEqual(tracked[2],[])

    def test_normal_output_retains_existing_pipeline(self):
        with patch("aisi.app.sim_scene_to_osc.compute_target_layout",return_value=[]) as existing, patch("aisi.app.sim_scene_to_osc.compute_synthetic_layout",side_effect=AssertionError):
            prepare_scene_output(scene(),"discussion",1.,False)
        existing.assert_called_once()

    def test_partial_poses_are_checked(self):
        raw=scene(1)
        p=compute_synthetic_layout(raw,'discussion',.9,{'participants':3,'adaptive_layout_preview':True})
        self.assertEqual(len(p.chairs),3)
        s=state(raw);p=plan_discussion_chairs(s,3)
        p.targets[0].target_x=0
        with self.assertRaises(LayoutConstraintError): plan_discussion_chairs(s,3,p.targets)


if __name__=='__main__': unittest.main()
