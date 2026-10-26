"""Pixel measurements report cropping separately from mask multiplication."""
from pathlib import Path
import importlib.util
from types import SimpleNamespace
import unittest
from unittest.mock import patch, Mock
import numpy as np

from td_builders.check_motion_aligned_routing import coverage_shader,measure,check,create_mask_probe


class MotionAlignedRoutingTests(unittest.TestCase):
    def images(self):
        source=np.zeros((10,10,4),dtype=np.float32)
        source[2:8,2:8]=1
        mask=source.copy()
        return source,source*mask,mask

    def test_matching_mask_retains_content_without_outside_light(self):
        report=measure(*self.images())
        self.assertEqual(report['interior_retained_fraction'],1)
        self.assertEqual(report['lit_pixels_outside_mask'],0)
        self.assertEqual(report['mask_outside_nominal_pixels'],0)

    def test_cropped_shape_is_quantified_instead_of_declared_aligned(self):
        source,_,mask=self.images()
        mask[2:5]=0
        report=measure(source,source*mask,mask)
        self.assertEqual(report['interior_retained_fraction'],.5)
        self.assertEqual(report['lit_pixels_outside_mask'],0)

    def test_light_outside_mask_is_detected(self):
        source,masked,mask=self.images()
        masked[0,0,:3]=1
        self.assertEqual(measure(source,masked,mask)['lit_pixels_outside_mask'],1)

    def test_empty_nonfinite_and_different_rasters_are_rejected(self):
        source,masked,mask=self.images()
        with self.assertRaises(ValueError): measure(source,masked[:5],mask)
        with self.assertRaises(ValueError): measure(source*0,masked,mask)
        masked[0,0,0]=float('nan')
        with self.assertRaises(ValueError): measure(source,masked,mask)

    def test_probe_reuses_shared_shader_and_rejects_unknown_entrypoint(self):
        source=Path('td_builders/motion_design.frag').read_text()
        probe=coverage_shader(source)
        self.assertIn(source.replace('void main()','void renderContent()',1),probe)
        self.assertEqual(probe.count('void main()'),1)
        with self.assertRaises(ValueError): coverage_shader(source+source)

    def test_failed_preflight_restores_local_routing(self):
        parameters={s:SimpleNamespace(par=SimpleNamespace(
            top=SimpleNamespace(mode='ParMode.CONSTANT',val='/project1/comp_aisi_motion_v1_5/out_'+s)))
            for s in ('floor','tabletop')}
        flag=SimpleNamespace(mode='ParMode.CONSTANT',val=True)
        route=SimpleNamespace(fetch=lambda *args:True,par=SimpleNamespace(Enablemotion=flag),
            op=lambda name:parameters.get(name.replace('_motion','')))
        snapshot=SimpleNamespace(fetch=lambda *args:True,op=lambda name:None)
        def resolve(path): return snapshot if path.endswith('aligned_snapshot') else route
        with patch('td_builders.build_motion_aligned_snapshot.preflight',side_effect=RuntimeError('drift')):
            report=check(resolve,{})
        self.assertFalse(report['passed'])
        self.assertEqual(report['failure'],'drift')
        self.assertTrue(report['local_routing_restored'])
        self.assertTrue(flag.val)
        self.assertTrue(report['temporary_probes_removed'])
        for s,node in parameters.items():
            self.assertEqual(node.par.top,'/project1/comp_aisi_motion_v1_5/out_'+s)

    def test_snapshot_import_with_td_builtins_does_not_start_builder(self):
        self.assert_import_has_no_td_calls('build_motion_aligned_snapshot')

    def test_checker_import_with_td_builtins_does_not_start_check(self):
        self.assert_import_has_no_td_calls('check_motion_aligned_routing')

    def assert_import_has_no_td_calls(self,name):
        path=Path('td_builders')/(name+'.py')
        spec=importlib.util.spec_from_file_location('aisi_import_test_'+name,path)
        module=importlib.util.module_from_spec(spec)
        resolve=Mock(side_effect=AssertionError('Import touched TD graph'))
        with patch('builtins.op',resolve,create=True):
            spec.loader.exec_module(module)
        resolve.assert_not_called()

    def test_textport_exec_still_dispatches_with_nonstandard_module_name(self):
        root=SimpleNamespace(op=lambda name:object())  # Snapshot already exists.
        resolve=Mock(return_value=root)
        path=Path('td_builders/build_motion_aligned_snapshot.py')
        namespace={'__name__':'TouchDesignerTextport','__spec__':None,'op':resolve}
        with self.assertRaisesRegex(RuntimeError,'Snapshot existiert'):
            exec(compile(path.read_text(),str(path),'exec'),namespace)
        resolve.assert_called_once_with('/project1')

    def test_mask_probe_uses_local_select_when_cables_cannot_cross_networks(self):
        class Node:
            def __init__(self,parent,name):
                self.parent=parent
                self.path=parent.path+'/'+name
                self.par=SimpleNamespace()
                self.inputs=[]
                self.inputConnectors=[Connector(self,i) for i in range(2)]
        class Connector:
            def __init__(self,node,index): self.node,self.index=node,index
            def connect(self,source):
                if source.parent is not self.node.parent:
                    raise ValueError('Cross-network TOP cable')
                while len(self.node.inputs)<=self.index: self.node.inputs.append(None)
                self.node.inputs[self.index]=source
        route=SimpleNamespace(path='/project1/routing')
        external=Node(route,'mask_existing')
        original=Node(route,'tabletop_masked')
        route.op=lambda name:external if name=='mask_existing' else original
        snapshot=SimpleNamespace(path='/project1/snapshot')
        snapshot.create=lambda kind,name:Node(snapshot,name)
        snapshot.copy=lambda source,name,includeDocked:Node(snapshot,name)
        probe=Node(snapshot,'probe')
        # Reproduce the original failure with a genuinely separate parent.
        with self.assertRaisesRegex(ValueError,'Cross-network'):
            Node(snapshot,'bad_copy').inputConnectors[1].connect(external)
        created=[]
        masked,local_mask=create_mask_probe(snapshot,route,probe,'selectTOP',created)
        self.assertEqual(masked.inputs,[probe,local_mask])
        self.assertEqual(local_mask.par.top,external.path)
        self.assertEqual(created,[local_mask,masked])
        self.assertFalse(original.inputs)
        self.assertFalse(external.inputs)

    def test_unconnected_probe_is_reported_before_cooking(self):
        local=SimpleNamespace(par=SimpleNamespace())
        masked=SimpleNamespace(inputs=[],inputConnectors=[Mock(),Mock()])
        snapshot=SimpleNamespace(create=lambda *args:local,copy=lambda *args,**kwargs:masked)
        route=SimpleNamespace(op=lambda name:SimpleNamespace(path='/other/mask'))
        created=[]
        with self.assertRaisesRegex(RuntimeError,'Probe-Verbindungen'):
            create_mask_probe(snapshot,route,object(),'selectTOP',created)
        self.assertEqual(created,[local,masked])


if __name__=='__main__':
    unittest.main()
