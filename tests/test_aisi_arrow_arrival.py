import unittest
from types import SimpleNamespace

from td_builders.repair_aisi_arrow_arrival import corrected_source
from td_builders.study_motion_lines import rect_motion_segments


SOURCE = '''import math
def points():
    return {'visible': True, 'length': length, 'sx': 0.0, 'sy': 0.0, 'ex': length, 'ey': 0.0}
'''


class AisiArrowArrivalTests(unittest.TestCase):
    def evaluate(self, cm, degrees, length=.1):
        class Par:
            def __init__(self, value): self.value = value
            def eval(self): return self.value
        pose = dict(X=0, Y=0, Targetx=cm * .0052, Targety=0, Rot=0, Targetrot=degrees)
        template = SimpleNamespace(par=SimpleNamespace(**{k: Par(v) for k, v in pose.items()}))
        env = {'length': length, 'parent': lambda depth: template}
        exec(corrected_source(SOURCE), env)
        return env['points']()

    def test_matches_study_joint_arrival_tolerances(self):
        for cm in (0, 7.99, 8, 8.01, 20):
            for angle in (0, 4.99, 5, 5.01, 179, 185, 185.01):
                with self.subTest(cm=cm, angle=angle):
                    expected = rect_motion_segments(0, 0, 0, cm * .0052, 0, angle)['arrived']
                    result = self.evaluate(cm, angle)
                    self.assertEqual(not result['visible'], bool(expected))
                    if expected:
                        self.assertEqual(result['length'], 0)
                        self.assertEqual(result['head_length'], 0)

    def test_tip_shrinks_with_shaft_outside_joint_tolerance(self):
        for length in (.001, .02, .1, .2):
            result = self.evaluate(4, 15, length)
            self.assertTrue(result['visible'])
            self.assertAlmostEqual(result['head_length'], min(.075, length / 2))

    def test_preserves_existing_invisibility(self):
        env = {'length': .1, 'parent': lambda depth: SimpleNamespace(par=SimpleNamespace(
            **{k: SimpleNamespace(eval=lambda v=v: v) for k, v in dict(
                X=0, Y=0, Targetx=1, Targety=0, Rot=0, Targetrot=0).items()}))}
        exec(corrected_source(SOURCE.replace("'visible': True", "'visible': False")), env)
        self.assertFalse(env['points']()['visible'])
        self.assertEqual(env['points']()['head_length'], 0)

    def test_idempotent_and_unknown_callback_rejected(self):
        patched = corrected_source(SOURCE)
        self.assertEqual(corrected_source(patched), patched)
        with self.assertRaises(ValueError):
            corrected_source('pass')


if __name__ == '__main__':
    unittest.main()
