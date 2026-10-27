"""Calibrated comparison remains disconnected and respects mask transmission."""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np

from td_builders import prepare_motion_under_table_projector_probe as probe


class ProjectorProbeTests(unittest.TestCase):
    def test_added_pixels_follow_transmission_and_blocked_area_stays_dark(self):
        before=np.full((4,4,3),.1)
        transmission=np.ones_like(before)
        transmission[:2]=0
        extra=.4*transmission
        result=probe.compare_rgb(before,before+extra,extra,transmission)
        self.assertEqual(result['blocked_pixels'],8)
        self.assertEqual(result['additional_pixels'],8)
        self.assertEqual(result['additional_pixels_in_clear_area'],8)
        self.assertEqual(result['max_added_rgb_in_blocked_area'],0)

    def test_even_matching_extra_cannot_light_blocked_pixels(self):
        zero=np.zeros((3,3,3))
        light=zero.copy()
        light[1,1]=.2
        with self.assertRaisesRegex(RuntimeError,'vollständig gesperrtem'):
            probe.compare_rgb(zero,light,light,zero)

    def test_wrong_difference_nan_and_darkening_are_refused(self):
        zero=np.zeros((3,3,3))
        one=np.ones_like(zero)
        for after,extra in ((one,zero),(np.full_like(zero,np.nan),zero),(-one,-one)):
            with self.assertRaises(RuntimeError): probe.compare_rgb(zero,after,extra,one)

    def test_invalid_projector_refused_without_graph_access(self):
        def resolve(path): self.fail('Must reject index before graph access')
        for action in (probe.prepare,probe.check):
            with self.assertRaises(RuntimeError): action(resolve,projector=3)

    def test_only_static_top_copy_allowed(self):
        original=SimpleNamespace(isTOP=True,type='glsl',path='/original',
                                 pars=lambda:[SimpleNamespace(mode='ParMode.EXPRESSION')])
        with self.assertRaisesRegex(RuntimeError,'dynamische Parameter'):
            probe.copy_top(None,original,'copy',[])

    def test_top_input_count_cannot_change_incidentally(self):
        original=SimpleNamespace(isTOP=True,type='comp',path='/original',pars=lambda:[],inputs=[1,2])
        with self.assertRaisesRegex(RuntimeError,'Anzahl'):
            probe.copy_top(None,original,'copy',[1])

    def test_local_sources_use_select_references_across_networks(self):
        parent=SimpleNamespace()
        source=SimpleNamespace(path='/other/source',parent=lambda:'other')
        select=SimpleNamespace(par=SimpleNamespace(top=None))
        parent.op=lambda name:None
        parent.create=lambda kind,name:select
        with patch.object(probe.routing,'symbol',return_value='selectTOP'):
            self.assertIs(probe.local_source(parent,source),select)
        self.assertEqual(select.par.top,source.path)

    def test_no_productive_install_api(self):
        self.assertFalse(hasattr(probe,'install'))

    def test_python39_compatible(self):
        ast.parse(Path('td_builders/prepare_motion_under_table_projector_probe.py').read_text(encoding='utf-8'),
                  feature_version=(3,9))
