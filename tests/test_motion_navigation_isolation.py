"""Controlled TD navigation fixtures and rollback on an interrupted probe."""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest
import numpy as np

from td_builders.check_motion_navigation_isolation import (
    check,fixture,pixel_stats,MOTION,MASKED,NAMES)
from td_builders.motion_design import Pose,tables_touch


class NavigationIsolationTests(unittest.TestCase):
    def test_fixtures_cover_both_contact_states_with_only_one_visible_table(self):
        for contact in (False,True):
            data=fixture(contact)
            self.assertEqual(data.shape,(6,6,4))
            self.assertEqual(data.dtype,np.float32)
            self.assertEqual(tables_touch(Pose(*data[4,0,:3]),Pose(*data[4,1,:3])),contact)
            self.assertEqual(int((data[:5,0,3]>.5).sum()),1)
            self.assertEqual(data[4,1,3],1)
            self.assertEqual(data[4,2,3],0)
        self.assertEqual(tuple(fixture(False)[4,2]),(1,0,0,0))

    def test_area_comparison_normalizes_different_top_resolutions(self):
        a=np.zeros((10,10,4),dtype=np.float32)
        a[2:6,3:7]=1
        b=np.repeat(np.repeat(a,2,axis=0),2,axis=1)
        self.assertEqual(pixel_stats(a)['lit_fraction'],pixel_stats(b)['lit_fraction'])
        self.assertEqual(pixel_stats(b)['lit_pixels'],4*pixel_stats(a)['lit_pixels'])

    def test_invalid_pixels_are_rejected(self):
        with self.assertRaises(ValueError):
            pixel_stats(np.full((2,2,4),np.nan))

    def test_failed_creation_restores_local_inputs_and_removes_created_nodes(self):
        nodes={}
        sources={name:SimpleNamespace(par=SimpleNamespace(top=SimpleNamespace(
            mode='ParMode.CONSTANT',val=MOTION+'/'+suffix)))
            for name,suffix in (('motion_state','state'),('motion_tabletop','out_tabletop'))}
        nodes.update(sources)
        def create(kind,name):
            if name==NAMES[1]:
                raise RuntimeError('injected creation failure')
            node=SimpleNamespace(path=MASKED+'/'+name,destroy=lambda:nodes.pop(name))
            nodes[name]=node
            return node
        # Mimic TD assignment of ParCollection.top as updating the Par value.
        class Pars:
            def __init__(self,parameter):
                object.__setattr__(self,'top',parameter)
            def __setattr__(self,name,value):
                self.top.val=value
        for node in sources.values():
            node.par=Pars(node.par.top)
        output=SimpleNamespace(cook=lambda **kw:None,errors=lambda:'',
                               numpyArray=lambda **kw:np.zeros((2,2,4)))
        nodes['out_tabletop']=output
        comp=SimpleNamespace(op=nodes.get,fetch=lambda *args:True,create=create)
        motion=SimpleNamespace(op=lambda name:object())
        report=check({MOTION:motion,MASKED:comp}.get,{'textDAT':object(),'scriptTOP':object()})
        self.assertFalse(report['passed'])
        self.assertEqual(report['failure'],'injected creation failure')
        self.assertTrue(report['local_inputs_restored'])
        self.assertTrue(report['temporary_probes_removed'])

    def test_script_parses_on_touchdesigner_python_39(self):
        source=Path('td_builders/check_motion_navigation_isolation.py').read_text()
        ast.parse(source,feature_version=(3,9))


if __name__=='__main__':
    unittest.main()
