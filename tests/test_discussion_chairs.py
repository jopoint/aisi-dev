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
from aisi.core.table_geometry import table_world_footprint
from aisi.analysis.rect_groupwork_adaptive_prototype import _polygon_distance
from td_builders.study_target_floor import FLOOR_TARGET_WIDTH_CM, FLOOR_TARGET_DEPTH_CM


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

    def test_pair_has_ten_cm_gap_opposite_rows_and_then_end_seats(self):
        s=state(scene())
        for count in range(1,7):
            p=plan_discussion_chairs(s,count)
            active=[t for t in p.targets if t.table_id in p.active_table_ids]
            a,b=active;angle=math.radians(a.target_rot_deg)
            delta=(b.target_x-a.target_x,b.target_y-a.target_y)
            self.assertAlmostEqual(delta[0]*math.cos(angle)+delta[1]*math.sin(angle),0.)
            self.assertAlmostEqual(math.dist((a.target_x,a.target_y),(b.target_x,b.target_y)),90.)
            by_id={t.table_id:t for t in s.tables}
            physical=[table_world_footprint(by_id[t.table_id],(t.target_x,t.target_y),t.target_rot_deg)
                      for t in active]
            self.assertAlmostEqual(_polygon_distance(*physical),10.)
            padded=[table_world_footprint(replace(by_id[t.table_id],table_type=None,
                    width=FLOOR_TARGET_WIDTH_CM,height=FLOOR_TARGET_DEPTH_CM),
                    (t.target_x,t.target_y),t.target_rot_deg) for t in active]
            self.assertAlmostEqual(_polygon_distance(*padded),0.)
            kinds=Counter(c['seat_kind'] for c in p.chairs)
            self.assertEqual(kinds['regular_long'],min(count,4))
            self.assertEqual(kinds['regular_end'],max(0,count-4))
            if count>=4:
                long_counts=Counter(c['table_id'] for c in p.chairs if c['seat_kind']=='regular_long')
                self.assertEqual(set(long_counts.values()),{2})
        p=plan_discussion_chairs(s,12)
        self.assertEqual(set(Counter(c['table_id'] for c in p.chairs).values()),{3})

    def test_four_table_stage_uses_corner_seats_before_dense_long_sides(self):
        s=state(scene())
        for count in range(7,13):
            with self.subTest(participants=count):
                p=plan_discussion_chairs(s,count)
                kinds=Counter(c['seat_kind'] for c in p.chairs)
                self.assertEqual(kinds['regular_long'],min(count,8))
                self.assertEqual(kinds['regular_corner'],max(0,count-8))
                self.assertEqual(kinds['dense_long'],0)
                self.assertTrue(all(n<=2 for n in Counter(c['table_id'] for c in p.chairs
                    if c['seat_kind']=='regular_long').values()))
                corners=[c for c in p.chairs if c['seat_kind']=='regular_corner']
                self.assertEqual(len(set(c['region_id'] for c in corners)),len(corners))
                validate_discussion_chairs(s,p)
                if count==10:
                    active=[t for t in p.targets if t.table_id in p.active_table_ids]
                    center=(sum(t.target_x for t in active)/4,sum(t.target_y for t in active)/4)
                    vectors=[(c['x_cm']-center[0],c['y_cm']-center[1]) for c in corners]
                    self.assertLess(vectors[0][0]*vectors[1][0]+vectors[0][1]*vectors[1][1],0)
        p=plan_discussion_chairs(s,12)
        corner_index=next(i for i,c in enumerate(p.chairs) if c['seat_kind']=='regular_corner')
        for change in ({'x_cm':-1},{'region_id':'unknown'},{'table_id':p.parked_table_ids[0]}):
            bad=deepcopy(p);bad.chairs[corner_index].update(change)
            with self.assertRaises(LayoutConstraintError): validate_discussion_chairs(s,bad)
        corners=[i for i,c in enumerate(p.chairs) if c['seat_kind']=='regular_corner']
        bad=deepcopy(p);bad.chairs[corners[1]]=dict(bad.chairs[corners[0]],seat_id='duplicate-corner')
        with self.assertRaises(LayoutConstraintError): validate_discussion_chairs(s,bad)

    def test_pentagon_uses_five_gap_seats_instead_of_dense_long_rows(self):
        s=state(scene());poses=None
        for count in (13,14,15):
            with self.subTest(participants=count):
                p=plan_discussion_chairs(s,count)
                kinds=Counter(c['seat_kind'] for c in p.chairs)
                self.assertEqual(kinds['regular_long'],10)
                self.assertEqual(kinds['regular_corner'],count-10)
                self.assertEqual(kinds['dense_long'],0)
                self.assertEqual(set(Counter(c['table_id'] for c in p.chairs
                    if c['seat_kind']=='regular_long').values()),{2})
                gap_keys=[c['region_id'] for c in p.chairs if c['seat_kind']=='regular_corner']
                self.assertEqual(len(gap_keys),len(set(gap_keys)))
                self.assertEqual(len(p.active_table_ids),5)
                self.assertFalse(p.parked_table_ids)
                center=(math.fsum(t.target_x for t in p.targets)/5,
                        math.fsum(t.target_y for t in p.targets)/5)
                radii=[math.dist((c['x_cm'],c['y_cm']),center) for c in p.chairs]
                self.assertLess(max(radii)-min(radii),1e-6)
                validate_discussion_chairs(s,p)
                if poses is not None:self.assertEqual(p.targets,poses)
                poses=p.targets
        corners=[c for c in p.chairs if c['seat_kind']=='regular_corner']
        self.assertEqual(len(corners),5)
        bad=deepcopy(p);bad.chairs[-1]['region_id']='unknown'
        with self.assertRaises(LayoutConstraintError):validate_discussion_chairs(s,bad)
        bad=deepcopy(p);bad.chairs[-1]['x_cm']=-1
        with self.assertRaises(LayoutConstraintError):validate_discussion_chairs(s,bad)

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

    def test_partial_strengths_repair_geometry_preserve_roles_and_return_copies(self):
        s=state(scene())
        for count in (4,6,10,15):
            final=plan_discussion_chairs(s,count)
            poses={t.table_id:t for t in final.targets}
            ready=replace(s,tables=[replace(t,x=poses[t.table_id].target_x,y=poses[t.table_id].target_y,
                rot_deg=poses[t.table_id].target_rot_deg) for t in s.tables])
            stable=transform_discussion_plan(ready,final,.5)
            validate_discussion_chairs(ready,stable)
            self.assertEqual([(t.target_x,t.target_y,t.target_rot_deg) for t in stable.targets],
                             [(t.target_x,t.target_y,t.target_rot_deg) for t in final.targets])
            for strength in (.01,.25,.5,.75,.99):
                with self.subTest(participants=count,strength=strength):
                    partial=transform_discussion_plan(s,final,strength)
                    validate_discussion_chairs(s,partial)
                    self.assertEqual(partial.active_table_ids,final.active_table_ids)
                    self.assertEqual(partial.parked_table_ids,final.parked_table_ids)
                    self.assertEqual([t.table_id for t in partial.targets],[t.table_id for t in s.tables])
                    self.assertEqual([c['seat_id'] for c in partial.chairs],[c['seat_id'] for c in final.chairs])
                    self.assertEqual(partial,transform_discussion_plan(s,final,strength))
                    partial.chairs[0]['x_cm']=-999
                    self.assertNotEqual(partial,transform_discussion_plan(s,final,strength))

    def test_partial_rigid_pair_moves_and_rotates_over_short_path(self):
        s=state(scene(2));final=plan_discussion_chairs(s,6)
        # A feasible pair starts 30 cm left and rotated +20 degrees. The
        # independent midpoint blend shrinks its gap and needs rigid repair.
        poses={t.table_id:t for t in final.targets}
        angle=math.radians(20)
        sources=[]
        for t in s.tables:
            target=poses[t.table_id];x=target.target_x-250;y=target.target_y-250
            sources.append(replace(t,x=220+math.cos(angle)*x-math.sin(angle)*y,
                y=250+math.sin(angle)*x+math.cos(angle)*y,rot_deg=target.target_rot_deg+20))
        moved=replace(s,tables=sources)
        results=[]
        for strength in (.25,.5,.75):
            partial=transform_discussion_plan(moved,final,strength)
            validate_discussion_chairs(moved,partial)
            cx=sum(t.target_x for t in partial.targets)/2
            self.assertAlmostEqual(cx,220+30*strength)
            self.assertAlmostEqual(sum(t.target_y for t in partial.targets)/2,250.)
            self.assertAlmostEqual(math.dist(*[(t.target_x,t.target_y) for t in partial.targets]),90.)
            delta=(partial.targets[0].target_rot_deg-final.targets[0].target_rot_deg+180)%360-180
            self.assertGreater(delta,0);self.assertLess(delta,20)
            results.append(partial.targets)
        self.assertNotEqual(results[0],results[1]);self.assertNotEqual(results[1],results[2])
        self.assertAlmostEqual((results[1][0].target_rot_deg-final.targets[0].target_rot_deg+180)%360-180,10.)

    def test_partial_osc_output_updates_instead_of_rejecting_request(self):
        raw=scene();parameters={'participants':6,'adaptive_layout_preview':True}
        outputs=[]
        for strength in (0.,.25,.5,.75,1.):
            tables,_,chairs,targets,error=prepare_scene_output(raw,'discussion',strength,False,
                activity_parameters=parameters)
            self.assertIsNone(error);self.assertEqual(tables,raw['tables'])
            self.assertEqual(len(chairs),0 if strength==0 else 6)
            self.assertEqual(len(targets),5)
            outputs.append(targets)
        self.assertNotEqual(outputs[1],outputs[2]);self.assertNotEqual(outputs[2],outputs[3])


if __name__=='__main__': unittest.main()
