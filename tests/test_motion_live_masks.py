"""Fail-closed pose and pixel checks without TD or camera access."""
import unittest
from types import SimpleNamespace
from unittest.mock import Mock
import numpy as np
from td_builders.check_motion_live_masks import match_sources,compare_pixels,current_stream
from td_builders.motion_design import Pose


class LiveMaskChecks(unittest.TestCase):
    def stream_fixture(self):
        from td_builders import build_motion_output_routing as routing
        status=dict(fresh=True,signature=(123,10),layout=('osc',123,2),ids=['a'])
        snapshot=dict(fresh=True,signature=(123,10),rows=[('a',None,None,True,True)])
        channels={'aisi_motion/camera/fresh':1,'aisi_motion/camera/session':123,
                  'aisi_motion/camera/frame':10}
        raw=Mock(inputs=[])
        raw.chans.side_effect=lambda:[SimpleNamespace(name=k,eval=lambda v=v:v) for k,v in channels.items()]
        state=Mock(); state.errors.return_value=''
        reader=Mock(); reader.read.return_value=snapshot
        motion=Mock(); motion.par.Oscpath.eval.return_value=routing.RAW
        motion.op.return_value=state
        motion.fetch.side_effect=lambda key,default=None:{'motion_live_status':status,
                                                        'motion_osc_reader':reader}.get(key,default)
        comp=Mock(); comp.par.Sourceapproved.eval.return_value=False
        graph={routing.PATH:comp,routing.MOTION[:-1]:motion,routing.RAW:raw}
        return graph.__getitem__,status,snapshot,channels

    def test_post_gpu_stream_sample_never_reads_mask_geometry(self):
        resolve,status,snapshot,channels=self.stream_fixture()
        report=current_stream(resolve)
        self.assertTrue(report['passed'])
        self.assertEqual(report['live_stream'],status)

    def test_stream_sample_rejects_unbound_camera_missing_source_or_changed_frame(self):
        for kind in ('camera','source','frame'):
            with self.subTest(kind=kind):
                resolve,status,snapshot,channels=self.stream_fixture()
                if kind=='camera': channels['aisi_motion/camera/frame']=9
                elif kind=='source': snapshot['rows']=[('a',None,None,False,True)]
                else: snapshot['signature']=(123,9)
                with self.assertRaises(RuntimeError): current_stream(resolve)

    def test_stream_sample_keeps_waiting_when_main_is_not_fresh(self):
        resolve,status,snapshot,channels=self.stream_fixture()
        status['fresh']=False
        self.assertFalse(current_stream(resolve)['passed'])

    def test_unique_axial_correspondence_and_unordered_masks(self):
        rows=[('b',Pose(300,200,30),None,True,True),('a',Pose(100,100,90),None,True,True)]
        masks=[dict(path='mask0',pose=(100,100,-90)),dict(path='mask1',pose=(300,200,30))]
        matches=match_sources(rows,masks,.25)
        self.assertEqual([m['original_mask'] for m in matches],['mask1','mask0'])

    def test_ambiguous_invalid_missing_or_shifted_sources_fail(self):
        rows=[('a',Pose(100,100,90),None,True,True)]
        for mask_set in ([],[dict(path='x',pose=(101,100,90))],
                         [dict(path='x',pose=(100,100,float('nan')))],[dict(path='x',pose=(100,100,91))]):
            with self.assertRaises(ValueError): match_sources(rows,mask_set,.25)
        with self.assertRaises(ValueError):
            match_sources([('a',Pose(100,100,90),None,False,True)],
                          [dict(path='x',pose=(100,100,90))],.25)
        with self.assertRaises(ValueError):
            match_sources(rows*2,[dict(path='x',pose=(100,100,90)),dict(path='y',pose=(100,100,90))],.25)

    def test_pixels_allow_only_one_pixel_boundary_and_report_raw_difference(self):
        image=np.zeros((20,20,4),np.float32); image[4:10,4:10,:3]=1
        shifted=np.zeros_like(image); shifted[4:10,5:11,:3]=1
        report=compare_pixels(image,shifted)
        self.assertTrue(report['passed'])
        self.assertEqual(report['max_rgba_difference'],1)
        shifted=np.zeros_like(image); shifted[4:10,6:12,:3]=1
        self.assertFalse(compare_pixels(image,shifted)['passed'])

    def test_empty_nonfinite_or_mismatched_rasters_never_pass(self):
        empty=np.zeros((20,20,4),np.float32)
        for other in (empty.copy(),np.ones((10,10,4)),np.full_like(empty,np.nan)):
            with self.assertRaises(ValueError): compare_pixels(empty,other)
