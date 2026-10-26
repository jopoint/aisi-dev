"""Focused v1.5 acceptance tests; no assertion of physical projection quality."""
import math
import unittest
from unittest.mock import patch
from dataclasses import dataclass, FrozenInstanceError

from td_builders.motion_design import (
    Pose, TableMotion, MotionLayout, tables_touch, metrics,
    reference_pose, td_pose, demo_pose,
)


class MotionDesignTests(unittest.TestCase):
    def test_python39_geometry_without_slots_or_application_models(self):
        from td_builders.motion_geometry_compat import load_geometry
        def old_dataclass(*args, **kwargs):
            if 'slots' in kwargs:
                raise TypeError('slots unavailable in Python 3.9')
            return dataclass(*args, **kwargs)
        with patch('dataclasses.dataclass', old_dataclass):
            geometry = load_geometry(force_legacy=True)
        rect = geometry.get_table_geometry('rect')
        self.assertEqual(rect.nominal_width,160)
        self.assertEqual(rect.nominal_depth,80)
        self.assertEqual(rect.local_footprint,((-80,-40),(80,-40),(80,40),(-80,40)))
        with self.assertRaises(FrozenInstanceError):
            rect.nominal_width = 1
        for angle in (-179,-90,0,37,180):
            corners = geometry.transform_local_footprint(rect.local_footprint,200,200,angle)
            self.assertTrue(geometry.convex_polygons_intersect(corners,corners))
            self.assertTrue(geometry.circle_intersects_convex_polygon((200,200),6,corners))

    def test_reference_axis_and_existing_td_interface(self):
        self.assertEqual(reference_pose(110, 180, -6), Pose(110, 180, 84))
        p = td_pose(.455296435546875, -.10420280761718749, 178.5760040283203)
        self.assertAlmostEqual(p.x, 337.5570068359375)
        self.assertAlmostEqual(p.y, 270.03900146484375)
        self.assertAlmostEqual(p.r, -178.5760040283203)

    def test_exact_rounded_corner_contact(self):
        origin = reference_pose(0, 0, 0)
        for x, y, expected in ((81,0,False),(80,0,True),(79,0,True),
                               (80,160,False),(76,156,True)):
            self.assertEqual(tables_touch(reference_pose(x,y,0),origin),expected)

    def test_rotated_contact_and_symmetry(self):
        for degrees in (-179,-90,-1,0,37,90,181):
            r=math.radians(degrees)
            target=reference_pose(120,200,degrees)
            at=lambda d:reference_pose(120+d*math.cos(r),200+d*math.sin(r),degrees)
            self.assertTrue(tables_touch(at(80),target))
            self.assertFalse(tables_touch(at(81),target))
            self.assertEqual(tables_touch(at(81),target),tables_touch(target,at(81)))

    def test_no_green_or_shrink_before_contact_after_rotation(self):
        target=Pose(200,200,0)
        s=TableMotion(0)
        s.update(Pose(400,200,40),target,1)
        s.update(Pose(400,200,0),target,2)
        self.assertFalse(s.touching)
        self.assertEqual((s.contact,s.navigation),(0,0))

    def test_contact_baseline_and_reentry(self):
        target=reference_pose(200,200,0)
        s=TableMotion(0)
        s.update(reference_pose(280,200,0),target,1)
        self.assertTrue(s.touching)
        self.assertEqual(s.navigation,0)
        s.update(reference_pose(260,200,0),target,1.1)
        self.assertGreater(s.navigation,0)
        size,alpha=s.halo,s.contact
        s.update(reference_pose(282,200,0),target,1.2)
        self.assertEqual(s.halo,size)
        self.assertEqual(s.contact,alpha)
        self.assertIsNone(s.baseline)
        s.update(reference_pose(282,200,0),target,1.31)
        self.assertGreater(s.contact,0)
        self.assertLess(s.contact,alpha)
        s.update(reference_pose(282,200,0),target,1.43)
        self.assertEqual(s.contact,0)
        s.update(reference_pose(280,200,0),target,1.5)
        self.assertEqual((s.navigation,s.approach),(0,0))

    def test_worsening_reduces_approach(self):
        target=reference_pose(200,200,0)
        s=TableMotion(0)
        s.update(reference_pose(280,200,0),target,.1)
        s.update(reference_pose(220,200,0),target,.2)
        best=s.navigation
        s.update(reference_pose(270,200,0),target,.3)
        self.assertLess(s.navigation,best)

    def test_positive_radius_outside_both_tolerances(self):
        target=reference_pose(200,200,0)
        for pose in (reference_pose(208.001,200,0),reference_pose(200,200,5.001)):
            s=TableMotion(0)
            s.update(reference_pose(280,200,0),target,.1)
            s.update(pose,target,.2)
            self.assertEqual(s.phase,'guidance')
            self.assertGreater(29*(1-s.navigation),0)

    def test_immediate_locked_success_and_reactivation(self):
        target=Pose(200,200,0)
        s=TableMotion(0)
        s.update(target,target,1)
        self.assertEqual((s.phase,s.navigation,s.since),('dissolve',1,1))
        s.update(Pose(300,200,30),target,1.5)
        self.assertEqual((s.phase,s.since),('dissolve',1))
        s.update(Pose(300,200,30),target,2)
        self.assertEqual(s.phase,'completed')
        s.update(Pose(202,200,180),target,2.1)
        self.assertEqual(s.phase,'completed')
        s.update(Pose(219,200,0),target,2.2)
        self.assertEqual(s.phase,'guidance')

    def test_tracking_loss_cannot_complete_or_reactivate(self):
        target=Pose(200,200,0)
        s=TableMotion(0)
        s.update(target,target,1,False)
        self.assertEqual(s.phase,'guidance')
        s.update(Pose(float('nan'),200,0),target,2)
        self.assertEqual(s.phase,'guidance')
        s.update(target,target,3)
        s.update(target,target,4,False)
        self.assertEqual(s.phase,'completed')
        s.update(Pose(400,200,0),target,5,False)
        self.assertEqual(s.phase,'completed')

    def test_reactivation_preserves_continuous_contact_progress(self):
        target=Pose(200,200,90)
        s=TableMotion(0)
        s.update(Pose(200,40,90),target,0)
        s.update(Pose(200,45,90),target,.1)
        baseline=s.baseline
        self.assertIsNotNone(baseline)
        s.update(target,target,.2)
        s.update(target,target,1.3)
        s.update(Pose(200,200,115),target,1.4)
        self.assertEqual(s.phase,'guidance')
        self.assertEqual(s.baseline,baseline)
        # Values also replayed against model.ts + visual.ts from Remotion v1.5.
        self.assertAlmostEqual(s.navigation,.605263157894737)
        s.update(Pose(200,200,110),target,1.5)
        self.assertAlmostEqual(s.navigation,.7039473684210527)

    def test_contact_loss_during_dissolve_resets_visual_baseline(self):
        target=Pose(200,200,90)
        s=TableMotion(0)
        s.update(Pose(200,45,90),target,.1)
        s.update(target,target,.2)
        s.update(Pose(200,400,90),target,.3)
        self.assertEqual(s.phase,'dissolve')
        self.assertIsNone(s.baseline)
        self.assertFalse(s.touching)
        s.update(Pose(200,400,90),target,1.3)
        s.update(Pose(200,45,90),target,1.4)
        self.assertEqual(s.phase,'guidance')
        self.assertEqual(s.navigation,0)
        s.update(Pose(200,100,90),target,1.5)
        self.assertGreater(s.navigation,0)

    def test_pulse_interrupt_radius_and_180ms_fade(self):
        target=Pose(400,400,0)
        source=Pose(100,100,0)
        s=TableMotion(0)
        s.update(source,target,7,idle=2.5)
        radius=s.pulse_radius
        s.update(source,target,7.016,idle=0)
        self.assertEqual((s.pulse_radius,s.pulse_opacity),(radius,1))
        s.update(source,target,7.106,idle=0)
        self.assertGreater(s.pulse_radius,radius)
        self.assertGreater(s.pulse_opacity,0)
        self.assertLess(s.pulse_opacity,1)
        s.update(source,target,7.216,idle=0)
        self.assertEqual(s.pulse_opacity,0)

    def test_global_event_independent_ids_and_no_pose_reveal(self):
        engine=MotionLayout()
        engine.activate('proposal-a',0)
        target=Pose(200,200,0)
        engine.update('a',target,target,1)
        engine.update('b',Pose(400,200,0),target,1)
        engine.activate('proposal-a',2)
        self.assertEqual(engine.started,0)
        self.assertEqual(engine.tables['a'].phase,'dissolve')
        self.assertEqual(engine.tables['b'].phase,'guidance')
        engine.activate('proposal-b',3)
        self.assertEqual(engine.started,3)
        self.assertEqual(engine.tables,{})

    def test_demo_22_seconds_at_irregular_rates(self):
        for hz in (24,60,97):
            target=reference_pose(320,330,32)
            s=TableMotion(0)
            for i in range(22*hz+1):
                t=i/hz
                s.update(demo_pose(t),target,t)
            self.assertEqual(s.phase,'completed')

    def test_symmetry_and_both_tolerances(self):
        t=Pose(200,200,0)
        self.assertTrue(metrics(Pose(200,200,180),t)[3])
        self.assertFalse(metrics(Pose(200,200,6),t)[3])
        self.assertFalse(metrics(Pose(209,200,0),t)[3])


if __name__=='__main__':
    unittest.main()
