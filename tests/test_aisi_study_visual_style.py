"""Fokussierte Regression: geschützte Render-Zweige und kanonische Study-Konturen."""
import json
import unittest
from types import SimpleNamespace
from td_builders.aisi_study_visual_style import floor_expression, shared_callback_source, adapted_callback
from td_builders.study_target_floor import rect_target_dash_segments
from td_builders.study_tabletop_brackets import rect_continuous_outline_segments


class StyleTests(unittest.TestCase):
    def test_serialized_dat_uses_same_canonical_segments(self):
        namespace = {}
        exec(shared_callback_source(), namespace)
        for width, depth in [(170, 90), (150, 70)]:
            self.assertEqual([tuple(vars(s).values()) for s in rect_target_dash_segments(width, depth)],
                             [tuple(s) for s in namespace['rect_target_dash_segments'](width, depth)])
        self.assertEqual([tuple(vars(s).values()) for s in rect_continuous_outline_segments(150, 70)],
                         [tuple(s) for s in namespace['rect_continuous_outline_segments'](150, 70)])

    def test_existing_tracking_study_paths_unchanged(self):
        # Entspricht der geprüften phasenabhängigen Auswahl des Livegraphs.
        previous = "# existing\n(lambda r: 'tracking' if r['study/mode'].eval() == 0 else ('setup' if r['study/phase'].eval() in (0, 1) else ('active' if r['study/phase'].eval() == 2 else '')))(op('/project1/comp_io/null_osc_raw'))"
        updated = floor_expression(previous)
        for mode in [0, 1]:
            for phase in range(4):
                raw = {name: SimpleNamespace(eval=lambda value=value: value) for name, value in
                       [('study/mode', mode), ('study/phase', phase)]}
                env = {'op': lambda path: raw}
                self.assertEqual(eval(previous, env), eval(updated, env))
        # AISI verwendet ausschließlich Geometrien der bestehenden Items.
        geos = {'table_target_floor_geo': SimpleNamespace(path='/item1/target'),
                'table_motion_line_floor_geo': SimpleNamespace(path='/item1/arrow')}
        item = SimpleNamespace(op=lambda name: geos[name])
        raw = {'study/mode': SimpleNamespace(eval=lambda: 2)}
        env = {'op': lambda path: raw, 'parent': lambda: SimpleNamespace(findChildren=lambda **kwargs: [item])}
        self.assertEqual(eval(updated, env), '/item1/target /item1/arrow')

    def test_scout_callback_still_runs_original(self):
        previous = 'def onCook(scriptOp):\n    scriptOp.called = True\n'
        namespace = {}
        exec(adapted_callback(previous, 'target_floor', '/shared'), namespace)
        script = SimpleNamespace(parent=lambda: SimpleNamespace(par=SimpleNamespace(
            Tabletype=SimpleNamespace(eval=lambda: 'summit'))), called=False)
        namespace['onCook'](script)
        self.assertTrue(script.called)


if __name__ == '__main__':
    unittest.main()
