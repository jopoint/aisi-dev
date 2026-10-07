from pathlib import Path
from contextlib import redirect_stdout
from io import StringIO
import runpy
from types import SimpleNamespace
import unittest
from unittest.mock import patch


inspect_chair_state = runpy.run_path(str(Path(__file__).resolve().parents[1] /
                                       'td_builders/inspect_shared_chair_live_state.py'))['inspect_chair_state']


class Parameter:
    expr = ''
    mode = 'EXPRESSION'

    def __init__(self, value):
        self.value = value

    def eval(self):
        return self.value


class Active:
    numRows = 16

    def __init__(self, rows):
        self.rows = rows

    def __getitem__(self, key):
        row, column = key
        return SimpleNamespace(val=str(self.rows[row - 1][column]))

    def errors(self):
        return []


def fixture(count):
    values = {'chair/count': Parameter(count)}
    rows, instances = [], {}
    for index in range(15):
        valid = index < count
        for name, value in (('x', 100 + index * 10), ('y', 200), ('radius', 25 if valid else 0)):
            values[f'chair/{index}/{name}'] = Parameter(value)
        row = {'x': (index * 10 - 150) * .0052, 'y': .26, 'radius': .13} if valid else {'x': 0., 'y': 0., 'radius': 0.}
        rows.append(row)
        parameters = SimpleNamespace(**{name: Parameter(row[column]) for name, column in (('X', 'x'), ('Y', 'y'), ('Radius', 'radius'))})
        instances[f'item{index + 1}'] = SimpleNamespace(par=parameters, op=lambda _: None)
    active = Active(rows)
    chairs = SimpleNamespace(op=lambda name: active if name == 'chairs_active' else instances.get(name))
    raw = type('Raw', (), {'__getitem__': lambda self, name: values.get(name)})()
    return values, rows, instances, lambda path: raw if path.endswith('null_osc_raw') else chairs if path.endswith('/chairs') else None


class SharedChairLiveInspectionTests(unittest.TestCase):
    def test_textport_builtins_start_the_check_without_global_op_or_project(self):
        _, _, _, resolve = fixture(10)
        output = StringIO()
        path = Path(__file__).resolve().parents[1] / 'td_builders/inspect_shared_chair_live_state.py'
        with patch('builtins.op', resolve, create=True), patch('builtins.project', SimpleNamespace(name='textport.toe'), create=True), redirect_stdout(output):
            runpy.run_path(str(path))
        self.assertIn('"project": "textport.toe"', output.getvalue())
        self.assertIn('"received_count": 10.0', output.getvalue())
        self.assertIn('kein Force-Cook', output.getvalue())

    def test_counts_nine_and_ten_are_distinguished_without_cooking_api(self):
        for count in (9, 10):
            with self.subTest(count=count):
                _, _, _, resolve = fixture(count)
                report = inspect_chair_state(resolve, 'test.toe')
                self.assertEqual(report['summary']['dat_positive_radii'], count)
                self.assertEqual(report['summary']['dat_osc_mismatch_indices'], [])
                self.assertEqual(report['summary']['instance_dat_mismatch_indices'], [])

    def test_stale_dat_is_distinguished_from_missing_osc_channel(self):
        values, rows, _, resolve = fixture(10)
        rows[9]['radius'] = 0
        report = inspect_chair_state(resolve, 'test.toe')
        self.assertEqual(report['summary']['dat_osc_mismatch_indices'], [9])
        values['chair/9/radius'] = None
        report = inspect_chair_state(resolve, 'test.toe')
        self.assertIsNone(report['slots'][9]['osc']['radius'])

    def test_wrong_instance_position_is_reported_separately(self):
        _, _, instances, resolve = fixture(10)
        instances['item9'].par.X.value = 99
        report = inspect_chair_state(resolve, 'test.toe')
        self.assertEqual(report['summary']['dat_osc_mismatch_indices'], [])
        self.assertEqual(report['summary']['instance_dat_mismatch_indices'], [8])


if __name__ == '__main__':
    unittest.main()
