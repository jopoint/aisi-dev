"""GPU comparisons of the actual halo function, independent of table clipping.

Optional native runner interface: runner shader state.bin rgba8.bin surface.
It renders 500x500 pixels, using the same six-by-six RGBA32F state texture.
"""
import ast
import os
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
import numpy as np

from td_builders.update_motion_halo_shape import update,patch_shader,PATH,OLD_BLOCK,NEW_BLOCK

SHADER=Path('td_builders/motion_design.frag')
RUNNER=os.environ.get('AISI_MOTION_SHADER_RUNNER','')


class HaloInstallerTests(unittest.TestCase):
    def old_shader(self):
        source=SHADER.read_text()
        start=source.index('float feedbackHalo(')
        end=source.index('float targetEdge(',start)
        return (source[:start]+source[end:]).replace(NEW_BLOCK,OLD_BLOCK)

    def test_compile_failure_restores_previous_shader_without_touching_state(self):
        old=self.old_shader()
        pixel=SimpleNamespace(text=old)
        renderer=SimpleNamespace(path=PATH+'/render_floor',cook=lambda **kw:None,
                                 errors=lambda:'injected compiler error')
        nodes={'motion_pixel':pixel,'state':object(),'render_floor':renderer}
        comp=SimpleNamespace(op=nodes.get)
        with self.assertRaisesRegex(RuntimeError,'injected compiler error'):
            update(lambda path:comp)
        self.assertEqual(pixel.text,old)

    def test_patch_preserves_other_local_shader_edits_and_is_idempotent(self):
        old=self.old_shader()+'\n// retained local note\n'
        new=patch_shader(old,SHADER.read_text())
        self.assertTrue(new.endswith('// retained local note\n'))
        self.assertEqual(new,patch_shader(new,SHADER.read_text()))
        self.assertIn(NEW_BLOCK,new)

    def test_patch_refuses_unexpected_local_halo_changes(self):
        old=self.old_shader().replace('float h=state.z,','float h=0.5,')
        with self.assertRaisesRegex(RuntimeError,'lokal abweichend'):
            patch_shader(old,SHADER.read_text())

    def test_installer_parses_on_td_python_39(self):
        ast.parse(Path('td_builders/update_motion_halo_shape.py').read_text(),feature_version=(3,9))


@unittest.skipUnless(RUNNER and Path(RUNNER).is_file(),'optional native GPU runner not configured')
class HaloGpuTests(unittest.TestCase):
    def render(self,distance,angle,h=.63,t=4,legacy=False):
        source=SHADER.read_text().replace('void main()', 'void contentMain()',1)
        if legacy:
            source+='''
float legacyHalo(vec2 offset,float angle,float h,float t,float distance) {
    float asymmetry=(1.0-h)*(1.0-h);
    float radius=mix(35.0,81.4,smoothstep(0.0,1.0,h));
    vec2 q=rotate2(offset,-angle);
    float g1=blurredEllipse(q,vec2(asymmetry*24.0,sin(t*1.8)*1.4),
        radius*vec2(1.0+asymmetry*.22+.04*sin(t*1.6),1.0-asymmetry*.20+.035*sin(t*1.3+.7)));
    float g2=ellipse(q,vec2(asymmetry*19.0,0),
        radius*vec2(1.0,1.0-asymmetry*.22+.035*sin(t*1.4)))*.8;
    return g2+g1*(1.0-g2);
}
'''
        function='legacyHalo' if legacy else 'feedbackHalo'
        source+='''
void main() {
    vec4 args=datum(0,0);
    vec2 offset=vec2(vUV.x,1.0-vUV.y)*500.0-250.0;
    fragColor=white(%s(offset,args.y,args.z,args.w,args.x));
}
''' % function
        with tempfile.TemporaryDirectory(prefix='aisi-halo-test-') as directory:
            path=Path(directory)
            shader=path/'probe.frag'; shader.write_text(source)
            state=np.zeros((6,6,4),np.float32); state[0,0]=(distance,angle,h,t)
            state.tofile(path/'state.bin')
            result=subprocess.run([RUNNER,str(shader),str(path/'state.bin'),str(path/'pixels.bin'),'1'],
                                  capture_output=True,text=True,timeout=20)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertIn('Render GL status: 0',result.stdout)
            return np.fromfile(path/'pixels.bin',np.uint8).reshape(500,500,4)[:,:,0]

    def test_within_position_tolerance_is_centered_and_direction_independent(self):
        for h,t in ((.1,1),(.63,4),(.95,7)):
            circle=self.render(0,0,h,t)
            # The native runner quantizes to RGBA8; allow one rounding step.
            self.assertLessEqual(np.abs(circle.astype(float)-np.flip(circle,axis=0)).max(),1)
            self.assertLessEqual(np.abs(circle.astype(float)-circle.T).max(),1)
            for distance,angle in ((3,71),(7.99,180)):
                self.assertTrue(np.array_equal(circle,self.render(distance,angle,h,t)))

    def test_crossing_either_side_of_target_has_no_halo_orientation_jump(self):
        left=self.render(2,0)
        right=self.render(2,180)
        self.assertTrue(np.array_equal(left,right))

    def test_round_transition_is_continuous_at_position_tolerance(self):
        inside=self.render(7.99,71).astype(float)
        outside=self.render(8.01,71).astype(float)
        self.assertLessEqual(np.max(np.abs(inside-outside)),1)

    def test_directional_form_at_distance_is_preserved_from_v15(self):
        for distance,angle in ((29,35),(80,180)):
            self.assertTrue(np.array_equal(self.render(distance,angle),
                                           self.render(distance,angle,legacy=True)))


if __name__=='__main__':
    unittest.main()
