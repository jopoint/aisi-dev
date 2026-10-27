"""Native precision, blocked pixels and opaque tabletop must remain protected."""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest

import numpy as np

from td_builders import prepare_motion_under_table_native_probe as native


class NativeProbeTests(unittest.TestCase):
    def scene(self):
        floor_before=np.full((4,4,4),.2)
        floor_before[:,:,3]=1
        floor_after=floor_before.copy()
        floor_after[:,1:,:3]+=.3
        front=np.zeros_like(floor_before)
        front[0]=1
        front[1]=.5
        transmission=np.ones_like(front)
        transmission[:,0]=0
        before=front+floor_before*(1-front[:,:,3:4])
        after=front+floor_after*(1-front[:,:,3:4])
        quantize=lambda a:np.rint(a*255)/255
        return [quantize(before),quantize(after),floor_before,floor_after,front,transmission]

    def test_native_rounding_and_final_composition(self):
        report=native.compare_final(*self.scene(),'rgba8fixed','rgba8fixed')
        self.assertEqual(report['blocked_pixels'],4)
        self.assertEqual(report['opaque_tabletop_pixels'],4)
        self.assertEqual(report['max_rgb_change_on_opaque_tabletop'],0)
        self.assertEqual(report['max_added_rgb_in_blocked_area'],0)
        self.assertGreater(report['additional_pixels'],0)

    def test_mask_violation_refused_even_if_over_equation_matches(self):
        before,after,old_floor,new_floor,front,transmission=self.scene()
        new_floor[2,0,:3]+=.1
        after=front+new_floor*(1-front[:,:,3:4])
        with self.assertRaisesRegex(RuntimeError,'gesperrtem nativen Maskenbereich'):
            native.compare_final(before,after,old_floor,new_floor,front,transmission,'rgba8fixed','rgba8fixed')

    def test_opaque_tabletop_has_stricter_guard_than_rounding_bound(self):
        arrays=self.scene()
        arrays[1][0,2,:3]-=.5/255
        with self.assertRaisesRegex(RuntimeError,'Opakes Tabletop'):
            native.compare_final(*arrays,'rgba8fixed','rgba8fixed')

    def test_incorrect_over_and_nonfinite_images_refused(self):
        for value in (.9,np.nan):
            arrays=self.scene()
            arrays[1][2,2,0]=value
            with self.assertRaises(RuntimeError): native.compare_final(*arrays,'rgba8fixed','rgba8fixed')

    def channels(self):
        return dict(outputred='input1',outputredchan='alpha',outputgreen='input1',outputgreenchan='alpha',
                    outputblue='input1',outputbluechan='alpha',outputalpha='input1',outputalphachan='one',chanmask='15')

    def test_observed_dark_rgb_and_coverage_alpha_reorder(self):
        image=np.zeros((4,4,4),np.float32)
        image[:,:,3]=np.array((0,.25,.5,1))[:,None]
        image[:,:,:3]=image[:,:,3:4]*.098039217
        reordered=np.repeat(image[:,:,3:4],4,axis=2)
        reordered[:,:,3]=1
        self.assertEqual(native.source_mask_convention(image,reordered,self.channels()),'alpha_coverage_to_rgb')
        # RGB lighting is irrelevant: exactly the same alpha mapping still holds.
        image[:,:,:3]=.5
        self.assertEqual(native.source_mask_convention(image,reordered,self.channels()),'alpha_coverage_to_rgb')

    def test_wrong_reorder_channel_or_pixel_mapping_refused(self):
        image=np.zeros((4,4,4),np.float32)
        image[:2,:,3]=1
        reordered=np.repeat(image[:,:,3:4],4,axis=2)
        reordered[:,:,3]=1
        channels=self.channels()
        channels['outputredchan']='red'
        with self.assertRaises(RuntimeError): native.source_mask_convention(image,reordered,channels)
        reordered[3,0,0]=1/255
        with self.assertRaises(RuntimeError): native.source_mask_convention(image,reordered,self.channels())

    def test_effective_format_supports_current_and_older_display_api(self):
        self.assertEqual(native.effective_format(SimpleNamespace(pixelFormatName='rgba16float')),'rgba16float')
        par=SimpleNamespace(menuNames=['useinput','rgba8fixed'],
                            menuLabels=['Use Input','8-bit fixed (RGBA)'],eval=lambda:'useinput')
        node=SimpleNamespace(path='/native',pixelFormat='RGBA 8-bit fixed',par=SimpleNamespace(format=par))
        self.assertEqual(native.effective_format(node),'rgba8fixed')
        node.pixelFormat='unrecognized storage'
        with self.assertRaises(RuntimeError): native.effective_format(node)

    def inherited(self,path,sources=(),kind='null'):
        par=SimpleNamespace(menuNames=['useinput'],menuLabels=['Use Input'],eval=lambda:'useinput')
        return SimpleNamespace(path=path,type=kind,inputs=list(sources),par=SimpleNamespace(format=par))

    def test_td2022_inheritance_single_and_equal_multi_inputs(self):
        explicit=SimpleNamespace(pixelFormatName='rgba8fixed')
        unary=self.inherited('/null',[explicit])
        composed=self.inherited('/composite',[unary,explicit],kind='comp')
        self.assertEqual(native.effective_format(composed),'rgba8fixed')

    def test_td2022_select_traces_referenced_source(self):
        source=self.inherited('/select',kind='select')
        explicit=SimpleNamespace(path='/reference',pixelFormatName='rgba16float')
        source.par.top=SimpleNamespace(eval=lambda:explicit)
        self.assertEqual(native.effective_format(source),'rgba16float')

    def test_mixed_inherited_formats_and_cycles_refused(self):
        mixed=self.inherited('/mixed',[SimpleNamespace(pixelFormatName='rgba8fixed'),
                                       SimpleNamespace(pixelFormatName='rgba32float')],kind='comp')
        with self.assertRaises(RuntimeError): native.effective_format(mixed)
        cyclic=self.inherited('/cyclic')
        cyclic.inputs=[cyclic]
        with self.assertRaises(RuntimeError): native.effective_format(cyclic)

    def switched(self,index,blend=False):
        node=self.inherited('/switch',[SimpleNamespace(pixelFormatName='rgba8fixed'),
                                       SimpleNamespace(pixelFormatName='rgba32float')],kind='switch')
        node.par.index=SimpleNamespace(eval=lambda:index)
        node.par.blend=SimpleNamespace(eval=lambda:blend)
        return node

    def test_switch_uses_selected_format_with_mixed_inputs(self):
        self.assertEqual(native.effective_format(self.switched(0)),'rgba8fixed')
        self.assertEqual(native.effective_format(self.switched(1)),'rgba32float')

    def test_switch_does_not_inspect_unselected_unsupported_input(self):
        node=self.switched(1)
        node.inputs[0]=SimpleNamespace()
        self.assertEqual(native.effective_format(node),'rgba32float')

    def test_blending_switch_format_is_not_guessed(self):
        with self.assertRaisesRegex(RuntimeError,'Blending'):
            native.effective_format(self.switched(1,blend=True))

    def test_switch_fractional_out_of_range_and_nonfinite_indices_refused(self):
        for index in (.5,-1,2,float('nan'),float('inf')):
            with self.assertRaises(RuntimeError): native.effective_format(self.switched(index))

    def test_invalid_projector_and_missing_probe_cannot_mutate_graph(self):
        def resolve(path): self.fail('Invalid index must be rejected first')
        with self.assertRaises(RuntimeError): native.prepare(resolve,projector=4)
        with self.assertRaises(RuntimeError): native.check(lambda path:None)

    def test_cleanup_is_repeatable_and_no_install_api_exists(self):
        result=native.cleanup(lambda path:None)
        self.assertTrue(result['already_absent'])
        self.assertFalse(result['production_outputs_changed'])
        self.assertFalse(hasattr(native,'install'))

    def test_python39_compatible(self):
        ast.parse(Path('td_builders/prepare_motion_under_table_native_probe.py').read_text(encoding='utf-8'),
                  feature_version=(3,9))
