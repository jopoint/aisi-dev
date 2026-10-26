"""A snapshot starts at contact progress zero; a trajectory must retain history."""
from types import SimpleNamespace
import unittest
import numpy as np

from td_builders.motion_sim_mask import mask_transform
from td_builders.motion_design import Pose,TableMotion,MotionLayout,td_pose
from td_builders.build_motion_dynamic_mask_preview import absolute_ops,mask_expression
from td_builders.update_motion_mask_dependencies import update,PATH


class MotionDynamicMaskTests(unittest.TestCase):
    def state(self):
        a=np.zeros((6,6,4),dtype=np.float32)
        a[5,0,2]=1
        a[0,0]=(250,250,35,1)
        return a

    def test_mask_transform_is_inverse_of_existing_content_boundary(self):
        a=self.state()
        for pose in ((110,180,84),(337.557,270.039,-178.576),(400,400,90)):
            a[0,0]=(*pose,1)
            x,y,r,visible=mask_transform(a,0)
            self.assertEqual(visible,1)
            self.assertTrue(np.allclose(td_pose(x,y,r),a[0,0,:3],rtol=0,atol=1e-6))

    def test_mask_uses_advancing_source_and_ignores_completion_phase(self):
        a=self.state()
        before=mask_transform(a,0)
        a[0,0]=(300,350,95,1)
        a[0,2,3]=2
        after=mask_transform(a,0)
        self.assertNotEqual(before,after)
        self.assertEqual(after[3],1)
        self.assertEqual(after[:3],(.26,-.52,-95))

    def test_stale_invalid_removed_or_nan_source_hides_copied_mask(self):
        for field,value in (((5,0,2),0),((0,0,3),0),((0,0,0),float('nan'))):
            a=self.state()
            a[field]=value
            self.assertEqual(mask_transform(a,0)[3],0)
        self.assertEqual(mask_transform(None,0)[3],0)
        self.assertEqual(mask_transform(self.state(),5)[3],0)

    def test_static_contact_is_not_a_progress_growth_test(self):
        target=Pose(200,200,0)
        near=Pose(220,200,0)
        static=TableMotion(0)
        static.update(near,target,.1)
        static.update(near,target,1)
        self.assertEqual((static.navigation,static.halo),(0,0))
        moving=TableMotion(0)
        moving.update(Pose(360,200,0),target,.1)
        moving.update(near,target,1)
        self.assertGreater(moving.navigation,.9)
        self.assertGreater(moving.halo,.9)
        self.assertEqual(moving.phase,'guidance')

    def test_two_live_trajectories_keep_different_progress(self):
        layout=MotionLayout()
        layout.activate('proposal',0)
        for name,y in (('a',200),('b',400)):
            layout.update(name,Pose(360,y,0),Pose(200,y,0),.1)
        a=layout.update('a',Pose(220,200,0),Pose(200,200,0),1)
        b=layout.update('b',Pose(360,400,0),Pose(200,400,0),1)
        self.assertGreater(a.halo,.9)
        self.assertEqual(b.halo,0)

    def test_copied_op_paths_are_resolved_before_changing_parent(self):
        p=SimpleNamespace(name='sops',eval=lambda:[SimpleNamespace(path='/study/surface')])
        self.assertEqual(absolute_ops(p),'/study/surface')
        p.eval=lambda:'../surface'
        with self.assertRaisesRegex(RuntimeError,'absolut'):
            absolute_ops(p)

    def test_time_dependency_preserves_pose_value_and_reads_td_clock(self):
        frames=[]
        class Clock:
            @property
            def frame(self):
                frames.append(12)
                return 12
        values={'tx':.52,'ty':-.26,'rz':-90,'sx':1}
        adapter=SimpleNamespace(module=SimpleNamespace(value=lambda row,p:values[p]))
        for name,value in values.items():
            expr=mask_expression('/mask_adapter',4,name)
            self.assertEqual(eval(expr,{'op':lambda path:adapter,'absTime':Clock()}),value)
        self.assertEqual(len(frames),4)

    def dependency_fixture(self):
        adapter=SimpleNamespace(path=PATH+'/mask_adapter')
        nodes={'mask_adapter':adapter}
        for row in range(5):
            pars={name:SimpleNamespace(mode='ParMode.EXPRESSION',
                expr=mask_expression(adapter.path,row,name,timed=False))
                for name in ('tx','ty','rz','sx')}
            nodes['mask_item_%d' % row]=SimpleNamespace(path=PATH+'/mask_item_%d' % row,
                                                      par=SimpleNamespace(**pars))
        comp=SimpleNamespace(path=PATH,fetch=lambda *args:True,op=nodes.get)
        return comp,nodes

    def test_installer_updates_only_owned_pose_expressions_and_is_idempotent(self):
        comp,nodes=self.dependency_fixture()
        self.assertEqual(update(lambda path:comp)['pose_expressions_updated'],20)
        self.assertEqual(update(lambda path:comp)['pose_expressions_updated'],0)
        self.assertIn('absTime.frame',nodes['mask_item_4'].par.tx.expr)

    def test_installer_preserves_an_unexpected_local_edit_without_partial_changes(self):
        comp,nodes=self.dependency_fixture()
        first=nodes['mask_item_0'].par.tx.expr
        nodes['mask_item_4'].par.sx.expr='custom_visibility'
        with self.assertRaisesRegex(RuntimeError,'Abweichende'):
            update(lambda path:comp)
        self.assertEqual(nodes['mask_item_0'].par.tx.expr,first)
        self.assertEqual(nodes['mask_item_4'].par.sx.expr,'custom_visibility')


if __name__=='__main__':
    unittest.main()
