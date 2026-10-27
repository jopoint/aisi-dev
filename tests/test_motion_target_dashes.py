"""Dashed target patch preserves the semantic footprint and all unrelated code."""
import ast
from pathlib import Path
import unittest

from td_builders import update_motion_target_dashes as update


class DashedTargetTests(unittest.TestCase):
    def test_patch_changes_only_target_rendering(self):
        old=Path('td_builders/motion_design.frag').read_text()+'\n// local note\n'
        new=update.patch_shader(old)
        restored=(new.replace(update.HELPER,'',1).replace(update.NEW_FILL,update.FILL,1)
                     .replace(update.NEW_LAYER,update.LAYER,1))
        self.assertEqual(restored,old)
        for fragment in ('*smoothstep(0.0,1.0,state.y)*targetMask;',
                         'float targetMask=coverage(roundedRect(',
                         'float sourceMask=coverage(roundedRect(',
                         'float templateRing=', 'float targetBars=',
                         'floorColor=over(f*(released*pulse.w*redisplay),floorColor);'):
            self.assertEqual(new.count(fragment),old.count(fragment))

    def test_repeated_or_unknown_shader_is_rejected(self):
        old=Path('td_builders/motion_design.frag').read_text()
        for source in (update.patch_shader(old),old+update.FILL,old.replace(update.LAYER,'local edit')):
            with self.assertRaises(RuntimeError):update.patch_shader(source)

    def test_visual_reveal_and_local_edits_survive_dashed_patch(self):
        from td_builders.update_motion_visual_reveal import patch_shader
        old=patch_shader(Path('td_builders/motion_design.frag').read_text())
        new=update.patch_shader(old)
        self.assertIn('clock.y=visualReveal.x;',new)
        self.assertIn('if(visualReveal.y<.5)',new)
        self.assertIn('float radius=max(corner-2.5,.001);',new)

    def test_python39_compatible(self):
        ast.parse(Path('td_builders/update_motion_target_dashes.py').read_text(),feature_version=(3,9))
