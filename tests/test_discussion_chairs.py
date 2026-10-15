from collections import Counter
from copy import deepcopy
from dataclasses import replace
import math
import unittest
from unittest.mock import patch

from aisi.app.sim_room_editor import make_default_tables, scene_payload
from aisi.app.sim_layout_rules import compute_synthetic_layout, _normalize_scene_for_aisi
from aisi.app.sim_scene_to_osc import prepare_scene_output, send_chairs
from aisi.input.scene_loader import build_scene_state_from_dict
from aisi.generation.discussion_chairs import (
    plan_discussion_chairs, validate_discussion_chairs, transform_discussion_plan,
)
from aisi.generation.adaptive_layout_v1 import LayoutConstraintError


def scene(n=5):
    return scene_payload(make_default_tables()[:n], chairs=[], persons=[])


def state(raw):
    return build_scene_state_from_dict(_normalize_scene_for_aisi(raw), learning_format='discussion')


class DiscussionChairTests(unittest.TestCase):
    def test_counts_topologies_geometry_scene_order_and_copies(self):
        s=state(scene())
        tier_poses={}
        for count in range(1,16):
            with self.subTest(participants=count):
                p=plan_discussion_chairs(s,count)
                validate_discussion_chairs(s,p)
                required=2 if count<=6 else 4 if count<=12 else 5
                self.assertEqual(len(p.active_table_ids),required)
                self.assertEqual(len(p.parked_table_ids),5-required)
                if required in tier_poses:
                    self.assertEqual(p.targets,tier_poses[required])
                else:
                    tier_poses[required]=deepcopy(p.targets)
                self.assertEqual(len(p.chairs),count)
                self.assertEqual([t.table_id for t in p.targets],[t.table_id for t in s.tables])
                self.assertTrue(all(c['radius_cm']==25 for c in p.chairs))
                reversed_state=replace(s,tables=list(reversed(s.tables)))
                other=plan_discussion_chairs(reversed_state,count)
                self.assertEqual(p.targets,list(reversed(other.targets)))
                self.assertEqual(p.chairs,other.chairs)
                p.chairs[0]['x_cm']=-999
                self.assertNotEqual(p.chairs,plan_discussion_chairs(s,count).chairs)

    def test_pair_has_shared_long_edge_opposite_rows_and_then_end_seats(self):
        s=state(scene())
        for count in range(1,7):
            p=plan_discussion_chairs(s,count)
            active=[t for t in p.targets if t.table_id in p.active_table_ids]
            a,b=active;angle=math.radians(a.target_rot_deg)
            delta=(b.target_x-a.target_x,b.target_y-a.target_y)
            self.assertAlmostEqual(delta[0]*math.cos(angle)+delta[1]*math.sin(angle),0.)
            self.assertAlmostEqual(math.dist((a.target_x,a.target_y),(b.target_x,b.target_y)),80.)
            kinds=Counter(c['seat_kind'] for c in p.chairs)
            self.assertEqual(kinds['regular_long'],min(count,4))
            self.assertEqual(kinds['regular_end'],max(0,count-4))
            if count>=4:
                long_counts=Counter(c['table_id'] for c in p.chairs if c['seat_kind']=='regular_long')
                self.assertEqual(set(long_counts.values()),{2})
        p=plan_discussion_chairs(s,12)
        self.assertEqual(set(Counter(c['table_id'] for c in p.chairs).values()),{3})

    def test_tangency_corner_tolerance_and_collisions(self):
        s=state(scene())
        for count in (6,12,15):
            p=plan_discussion_chairs(s,count);validate_discussion_chairs(s,p)
            owner=next(t for t in p.targets if t.table_id==p.chairs[0]['table_id'])
            dx=p.chairs[0]['x_cm']-owner.target_x;dy=p.chairs[0]['y_cm']-owner.target_y
            distance=math.hypot(dx,dy)
            bad=deepcopy(p)
            bad.chairs[0]['x_cm']-=dx/distance*.01
            bad.chairs[0]['y_cm']-=dy/distance*.01
            with self.subTest(count=count),self.assertRaises(LayoutConstraintError): validate_discussion_chairs(s,bad)
            for change in ({'x_cm':-1},{'radius_cm':26}):
                bad=deepcopy(p);bad.chairs[0].update(change)
                with self.assertRaises(LayoutConstraintError): validate_discussion_chairs(s,bad)
            bad=deepcopy(p);bad.chairs[1].update(x_cm=p.chairs[0]['x_cm'],y_cm=p.chairs[0]['y_cm'])
            with self.assertRaises(LayoutConstraintError): validate_discussion_chairs(s,bad)
        p=plan_discussion_chairs(s,6)
        bad=deepcopy(p);parked=next(t for t in bad.targets if t.table_id in bad.parked_table_ids)
        active=next(t for t in bad.targets if t.table_id in bad.active_table_ids)
        parked.target_x=active.target_x;parked.target_y=active.target_y
        with self.assertRaises(LayoutConstraintError): validate_discussion_chairs(s,bad)

    def test_table_availability_and_bad_counts(self):
        for n,count in ((1,1),(2,7),(3,7),(4,13)):
            with self.subTest(tables=n,count=count),self.assertRaisesRegex(LayoutConstraintError,'benötigt'):
                plan_discussion_chairs(state(scene(n)),count)
        for n,count in ((2,6),(3,6),(4,12),(5,15)):
            p=plan_discussion_chairs(state(scene(n)),count)
            self.assertEqual(len(p.chairs),count)
        for count in (0,-1,True,2.5,'3',16):
            with self.subTest(count=count),self.assertRaises(LayoutConstraintError):
                compute_synthetic_layout(scene(),'discussion',1.,{'participants':count,'adaptive_layout_preview':True})

    def test_default_count_and_explicit_count_override(self):
        for n in range(2,6):
            with self.subTest(tables=n):
                default=compute_synthetic_layout(scene(n),'discussion',1.,{'adaptive_layout_preview':True})
                self.assertEqual(len(default.chairs),2*n)
        explicit=compute_synthetic_layout(scene(),'discussion',1.,{'participants':15,'adaptive_layout_preview':True})
        self.assertEqual(set(Counter(c['table_id'] for c in explicit.chairs).values()),{3})

    def test_zero_strength_preserves_exact_sources_without_solver(self):
        raw=scene()
        with patch('aisi.generation.discussion_chairs.plan_discussion_chairs',side_effect=AssertionError):
            zero=compute_synthetic_layout(raw,'discussion',0.,{'participants':15,'adaptive_layout_preview':True})
        self.assertEqual(zero.chairs,[])
        for source,target in zip(raw['tables'],zero.table_targets):
            self.assertEqual((source['x_cm'],source['y_cm'],source['rotation_deg']),
                             (target['x_cm'],target['y_cm'],target['rotation_deg']))

    def test_osc_output_without_network_and_tracking_isolation(self):
        raw=scene();parameters={'participants':6,'adaptive_layout_preview':True}
        tables,persons,chairs,targets,error=prepare_scene_output(raw,'discussion',1.,False,activity_parameters=parameters)
        self.assertEqual(tables,raw['tables']);self.assertEqual(len(targets),5)
        self.assertEqual(len(chairs),6);self.assertIsNone(error)
        messages=[]
        class Recorder:
            def send_message(self,address,value): messages.append((address,value))
        send_chairs(Recorder(),chairs,True)
        self.assertEqual(len(messages),18)
        self.assertEqual(messages[-1],('/chair/5/radius',25.))
        self.assertTrue(all(type(value) is float for _,value in messages))
        messages.clear();send_chairs(Recorder(),chairs,False)
        self.assertTrue(all(value==0. for address,value in messages if address.endswith('/radius')))
        with patch('aisi.app.sim_scene_to_osc.compute_synthetic_layout',side_effect=AssertionError):
            tracked=prepare_scene_output(raw,'discussion',1.,True,activity_parameters=parameters)
        self.assertEqual(tracked[2],[])

    def test_normal_output_retains_existing_pipeline(self):
        with patch('aisi.app.sim_scene_to_osc.compute_target_layout',return_value=[]) as existing, patch('aisi.app.sim_scene_to_osc.compute_synthetic_layout',side_effect=AssertionError):
            prepare_scene_output(scene(),'discussion',1.,False)
        existing.assert_called_once()

    def test_partial_poses_preserve_roles_or_are_explicitly_rejected(self):
        s=state(scene())
        for count in (4,10,15):
            final=plan_discussion_chairs(s,count)
            poses={t.table_id:t for t in final.targets}
            ready=replace(s,tables=[replace(t,x=poses[t.table_id].target_x,y=poses[t.table_id].target_y,
                                           rot_deg=poses[t.table_id].target_rot_deg) for t in s.tables])
            partial=transform_discussion_plan(ready,final,.5)
            validate_discussion_chairs(ready,partial)
            try:
                moving=transform_discussion_plan(s,final,.5)
            except LayoutConstraintError as exc:
                self.assertIn('Teilstärke',str(exc))
            else:
                validate_discussion_chairs(s,moving)
            self.assertEqual(set(partial.active_table_ids),set(final.active_table_ids))
            self.assertEqual(set(partial.parked_table_ids),set(final.parked_table_ids))
            self.assertEqual([t.table_id for t in partial.targets],[t.table_id for t in s.tables])


if __name__=='__main__': unittest.main()
