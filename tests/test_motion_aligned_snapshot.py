"""Static legacy-slot alignment; no assertion of live identity or freshness."""
import copy
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from td_builders import build_motion_aligned_snapshot as snapshot


def masks_for(rows):
    return [{'slot':slot,'pose':list(source),'scale':[1,1,1],'tilt':[0,0],
             'render':True} for slot,source,target in rows]


class MotionAlignedSnapshotTests(unittest.TestCase):
    def test_reported_pose_maps_to_existing_screen_coordinates(self):
        actual=snapshot.screen_pose((.455296435546875,-.10420280761718749,178.5760040283203))
        self.assertAlmostEqual(actual[0],337.5570068359375)
        self.assertAlmostEqual(actual[1],270.03900146484375)
        self.assertAlmostEqual(actual[2],-178.5760040283203)

    def test_strict_slots_source_and_target_stay_paired(self):
        rows=snapshot.parse_rows([list(snapshot.HEADER),
            ['2','rect','-.4','.7','179','-.5','.8','180'],
            ['0','rect','.4','-.1','178','.5','-.2','179']])
        self.assertEqual(rows[0],(2,(-.4,.7,179),(-.5,.8,180)))
        self.assertEqual(rows[1][0],0)
        self.assertFalse(snapshot.compare_masks(rows,list(reversed(masks_for(rows)))))

    def test_invalid_rows_do_not_become_snapshot(self):
        row=['0','rect','0','0','0','1','1','0']
        for change in ((0,'real_track_0'),(0,'01'),(0,'5'),(1,'summit'),(2,'nan')):
            invalid=list(row)
            invalid[change[0]]=change[1]
            with self.assertRaises(ValueError):
                snapshot.parse_rows([list(snapshot.HEADER),invalid])
        with self.assertRaises(ValueError):
            snapshot.parse_rows([list(snapshot.HEADER),row,row])

    def test_actual_mask_pose_visibility_and_scale_are_checked(self):
        rows=[(0,(.4,.2,179),(.8,.2,179))]
        correct=masks_for(rows)
        for key,value in (('pose',[.5,.2,179]),('scale',[.5,1,1]),
                          ('tilt',[1,0]),('render',False),('pose',[float('nan'),0,0])):
            invalid=copy.deepcopy(correct)
            invalid[0][key]=value
            self.assertTrue(snapshot.compare_masks(rows,invalid),(key,value))
        extra={'slot':5,'pose':[0,0,0],'scale':[1,1,1],'tilt':[0,0],'render':True}
        self.assertTrue(snapshot.compare_masks(rows,correct+[extra]))
        extra['scale'][0]=0
        self.assertFalse(snapshot.compare_masks(rows,correct+[extra]))

    def test_mask_comparison_is_axially_symmetric(self):
        rows=[(0,(.4,.2,179),(.8,.2,179))]
        masks=masks_for(rows)
        masks[0]['pose'][2]-=180
        self.assertFalse(snapshot.compare_masks(rows,masks))

    def test_reported_subpixel_deltas_use_exact_mask_source_and_keep_targets(self):
        sources=[(.455296435546875,-.10420280761718749,178.5760040283203),
                 (.4228691955566406,.7102524291992187,179.3780059814453),
                 (-.4347408203125,.7249891479492188,179.1230010986328),
                 (.00442003173828125,-.6596668060302734,-179.87600708007812),
                 (-.38547078857421874,-.10117640380859375,177.46099853515625)]
        observed=[(.4553640380859375,-.10420796508789062,178.57699584960938),
                  (.42287443237304684,.7101535644531249,179.36099243164062),
                  (-.43474605712890624,.72475,179.12100219726562),
                  (.0042744323730468745,-.6596616088867188,-179.88299560546875),
                  (-.3854812622070312,-.10113482666015625,177.45399475097656)]
        rows=[(i,source,(.1*i,.2,90)) for i,source in enumerate(sources)]
        masks=masks_for(rows)
        for mask,pose in zip(masks,observed): mask['pose']=list(pose)
        self.assertEqual(len(snapshot.compare_masks(rows,masks)),5)
        aligned,deltas,problems=snapshot.align_rows(rows,list(reversed(masks)),.25)
        self.assertFalse(problems)
        self.assertEqual([r[1] for r in aligned],observed)
        self.assertEqual([r[2] for r in aligned],[r[2] for r in rows])
        self.assertEqual([r[1] for r in rows],sources)
        self.assertTrue(all(d['max_edge_displacement_cm']<.25 for d in deltas))
        self.assertAlmostEqual(max(d['distance_cm'] for d in deltas),.0460010153,places=7)

    def test_pixel_budget_combines_translation_and_rotation_at_the_table_edge(self):
        rows=[(0,(0,0,0),(1,0,0))]
        masks=masks_for(rows)
        masks[0]['pose']=[.2*.0052,0,.1]
        self.assertTrue(snapshot.compare_masks(rows,masks,pixel_cm=.25))
        masks[0]['pose']=[0,0,.1]
        self.assertFalse(snapshot.compare_masks(rows,masks,pixel_cm=.25))
        masks[0]['pose']=[.2*.0052,0,0]
        self.assertFalse(snapshot.compare_masks(rows,masks,pixel_cm=.25))
        masks[0]['pose']=[.26*.0052,0,0]
        aligned,deltas,problems=snapshot.align_rows(rows,masks,.25)
        self.assertTrue(problems)
        self.assertEqual(aligned,rows)

    def test_invalid_pixel_budget_is_rejected(self):
        for budget in (0,-1,float('nan'),float('inf')):
            with self.assertRaises(ValueError):
                snapshot.compare_masks([],[],pixel_cm=budget)

    def test_preflight_uses_renderer_pixel_size_and_returns_mask_pose(self):
        def p(value): return SimpleNamespace(eval=lambda:value)
        cells=[list(snapshot.HEADER),['0','rect','0','0','0','.1','.2','30']]
        table=SimpleNamespace(numRows=2,row=lambda i:[SimpleNamespace(val=v) for v in cells[i]])
        camera=SimpleNamespace(path=snapshot.BASE+'cam1',par=SimpleNamespace(
            projection=p('ortho'),orthowidth=p(2.6),
            **{name:p(0) for name in ('tx','ty','rx','ry','rz')}))
        geo=SimpleNamespace(path='/project1/comp_study_visualization/rect_setup_mask_geo_00',
            inputs=[],render=True,par=SimpleNamespace(**{name:p(value) for name,value in
                {'tx':.0001,'ty':0,'rz':.01,'sx':1,'sy':1,'sz':1,'rx':0,'ry':0}.items()}))
        renderer=SimpleNamespace(width=2000,height=2000,
            par=SimpleNamespace(camera=p(camera),geometry=p([geo,geo])))
        nodes={snapshot.BASE+'tables_active':table,snapshot.BASE+'cam1':camera,
               snapshot.BASE+'render_table_mask':renderer}
        rows,report=snapshot.preflight(nodes.get)
        self.assertTrue(report['pose_alignment_passed'])
        self.assertEqual(rows,[(0,(.0001,0,.01),(.1,.2,30))])
        self.assertEqual(report['slot_match_pixel_cm'],.25)
        self.assertEqual(report['mask_geometry_duplicates'],1)

    def test_mismatch_reports_without_creating_or_changing_nodes(self):
        root=SimpleNamespace(op=lambda name:None,create=Mock())
        report={'pose_alignment_passed':False,'problems':['mismatch']}
        with patch.object(snapshot,'preflight',return_value=([],report)):
            actual=snapshot.build(lambda path:root,{})
        root.create.assert_not_called()
        self.assertFalse(actual['existing_nodes_changed'])
        self.assertIn('static snapshot',actual['tracking_freshness'])


if __name__=='__main__':
    unittest.main()
