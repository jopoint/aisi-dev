import unittest
from types import SimpleNamespace
from td_builders.repair_aisi_source_presence import gated_expression


class AisiSourcePresenceTests(unittest.TestCase):
    def evaluate(self, available, base='True', name='item2'):
        raw = {} if available is None else {'table/1/source_available': SimpleNamespace(eval=lambda: available)}
        class Raw:
            def __getitem__(self, key): return raw.get(key)
        return eval(gated_expression(base), {'op': lambda path: Raw(),
                    'parent': lambda: SimpleNamespace(name=name)})

    def test_source_hides_and_recovers_at_its_own_slot(self):
        self.assertEqual(self.evaluate(0), 0)
        self.assertEqual(self.evaluate(1), 1)
        self.assertEqual(self.evaluate(None), 1)
        self.assertEqual(self.evaluate(0, name='item1'), 1)

    def test_preserves_existing_visibility_and_template_is_safe(self):
        self.assertEqual(self.evaluate(1, 'False'), 0)
        self.assertEqual(self.evaluate(0, 'False'), 0)
        self.assertEqual(self.evaluate(0, name='table_template'), 1)
        expr = gated_expression('True')
        self.assertEqual(gated_expression(expr), expr)


if __name__ == '__main__':
    unittest.main()
