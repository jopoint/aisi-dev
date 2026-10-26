import unittest

from td_builders.isolate_aisi_tabletop_targets import (
    BACKUP, BRANCH, ROOT, OSC, base_geometry_paths,
    isolate_aisi_tabletop_targets, presence_expression, restore_aisi_tabletop_targets,
    _configure_transparent,
    activate_aisi_tabletop_targets,
)


class Parameter:
    def __init__(self, name, value='', expr=''):
        self.name, self.val, self.expr = name, value, expr
        self.mode = 'expression' if expr else 'constant'
        self.bindExpr, self.style = '', 'String'

    def eval(self):
        if self.name == 'geometry' and hasattr(self, 'graph'):
            return [self.graph[path] for path in self.val.split() if path in self.graph]
        return self.val


class Parameters:
    def __init__(self):
        object.__setattr__(self, 'values', {})

    def __getattr__(self, name):
        return self.values.get(name)

    def __setattr__(self, name, value):
        self.values[name] = Parameter(name, value)
        if name == 'geometry' and getattr(self, '_graph', None) is not None:
            self.values[name].graph = self._graph

    def __getitem__(self, name):
        return self.values.get(name)

    def __setitem__(self, name, value):
        raise TypeError('TD ParCollection accepts only parameter objects here; assign .val')


class Connector:
    def __init__(self, node, index):
        self.node, self.index = node, index

    def connect(self, source):
        while len(self.node.inputs) <= self.index:
            self.node.inputs.append(None)
        self.node.inputs[self.index] = source


class Node:
    def __init__(self, graph, path, kind='node'):
        self.graph, self.path, self.kind = graph, path, kind
        self.par, self.inputs, self.storage = Parameters(), [], {}
        object.__setattr__(self.par, '_graph', graph)
        self.nodeX, self.nodeY = 0, 0
        self.inputConnectors = [Connector(self, i) for i in range(2)]
        graph[path] = self

    def op(self, path):
        return self.graph.get(path if path.startswith('/') else self.path + '/' + path)

    def pars(self):
        return list(self.par.values.values())

    def errors(self):
        return ''

    def findChildren(self):
        return [n for p, n in self.graph.items() if p.startswith(self.path + '/')]

    def create(self, kind, name):
        node = Node(self.graph, self.path + '/' + name, kind)
        if kind == 'switchTOP':
            node.par.index = 0
        if kind == 'constantTOP':
            for channel in ('colorr', 'colorg', 'colorb', 'alpha'):
                setattr(node.par, channel, 1)
        return node

    def copy(self, source, name, includeDocked=False):
        node = self.create(source.kind, name)
        node.inputs = list(source.inputs)
        for p in source.pars():
            node.par.values[p.name] = Parameter(p.name, p.val, p.expr)
        return node

    def fetch(self, key, default):
        return self.storage.get(key, default)

    def store(self, key, value):
        self.storage[key] = value

    def destroy(self):
        for path in list(self.graph):
            if path == self.path or path.startswith(self.path + '/'):
                del self.graph[path]


def fixture():
    graph = {}
    root = Node(graph, ROOT)
    for path in ('comp_output', 'comp_calibration', 'comp_tabletop_calibration'):
        Node(graph, '/project1/' + path)
    for name in ('render_floor', 'render_tabletop', 'render_table_mask',
                 'null_table_mask', 'reorder_table_mask', 'level_invert_mask',
                 'mask_tabletop', 'null_tabletop', 'null_tabletop_masked', 'cam1'):
        root.create('render' if name.startswith('render') else 'node', name)
    for name in ('render_tabletop', 'render_table_mask'):
        root.op(name).par.camera = [root.op('cam1')]
        root.op(name).par.lights = []
    root.op('render_tabletop').par.values['geometry'] = Parameter('geometry', expr=repr(
        ROOT + '/item1/table_source_geo ' + ROOT + '/item1/table_target_tabletop_geo '
        + ROOT + '/item1/table_motion_line_tabletop_geo'))
    root.op('reorder_table_mask').inputs = [root.op('render_table_mask')]
    root.op('mask_tabletop').inputs = [root.op('null_tabletop'), root.op('null_table_mask')]
    root.op('mask_tabletop').kind = 'multiply'
    root.op('null_tabletop_masked').inputs = [root.op('mask_tabletop')]
    for i in range(1, 6):
        item = root.create('item', 'item%d' % i)
        item.create('geo', 'table_target_tabletop_geo')
        item.create('geo', 'table_mask_geo')
        item.create('geo', 'table_source_geo')
        item.create('geo', 'table_motion_line_tabletop_geo')
    symbols = {n: n for n in ('baseCOMP', 'constantTOP', 'switchTOP', 'compositeTOP')}
    return graph, root, symbols


class TabletopTargetIsolationTests(unittest.TestCase):
    def test_base_uses_absolute_native_paths_independent_of_parent_context(self):
        paths = base_geometry_paths().split()
        self.assertEqual(len(paths), 10)
        for index in range(1, 6):
            self.assertIn(ROOT + '/item%d/table_source_geo' % index, paths)
            self.assertIn(ROOT + '/item%d/table_motion_line_tabletop_geo' % index, paths)
        self.assertNotIn('target', base_geometry_paths())
        self.assertNotIn('parent()', base_geometry_paths())

    def test_missing_sources_and_removed_slots_are_hidden_without_reassignment(self):
        class Channel:
            def __init__(self, value): self.value = value
            def eval(self): return self.value
        class Raw(dict):
            def __getitem__(self, key): return self.get(key)
        raw = Raw({'table/count': Channel(4), 'table/0/source_available': Channel(0),
                   'table/1/source_available': Channel(1)})
        self.assertEqual([eval(presence_expression(i), {'op': lambda _: raw}) for i in range(5)],
                         [0, 1, 1, 1, 0])
        self.assertEqual(eval(presence_expression(1), {'op': lambda _: None}), 0)

    def test_each_target_uses_only_its_own_source_mask_and_original_modes_survive(self):
        graph, root, symbols = fixture()
        original = root.op('mask_tabletop')
        report = isolate_aisi_tabletop_targets(graph.get, symbols)
        branch = root.op(BRANCH)
        self.assertTrue(report['protected_settings_unchanged'])
        self.assertEqual([branch.op('transparent').par[n].val
                          for n in ('colorr', 'colorg', 'colorb', 'alpha')], [0, 0, 0, 0])
        self.assertIs(root.op('null_tabletop_masked').inputs[0], branch.op('select_mode'))
        self.assertIs(branch.op('select_mode').inputs[0], original)
        for i in range(5):
            target = branch.op('slot%d_render_target' % i)
            surface = branch.op('slot%d_render_surface' % i)
            self.assertEqual(target.par.geometry.val, ROOT + '/item%d/table_target_tabletop_geo' % (i + 1))
            self.assertEqual(surface.par.geometry.val, ROOT + '/item%d/table_mask_geo' % (i + 1))
            clipped = branch.op('slot%d_clip_target' % i)
            self.assertIs(clipped.inputs[0], target)
            self.assertIs(clipped.inputs[1].inputs[0], surface)
            self.assertEqual(target.par.camera.val, root.op('cam1').path)
        class Channel:
            def __init__(self, value): self.value = value
            def eval(self): return self.value
        for mode in (0, 1, 2):
            raw = {'study/mode': Channel(mode)}
            self.assertEqual(eval(branch.op('select_mode').par.index.expr, {'op': lambda _: raw}), int(mode == 2))
        self.assertTrue(isolate_aisi_tabletop_targets(graph.get, symbols)['already_applied'])
        self.assertTrue(restore_aisi_tabletop_targets(graph.get)['restored'])
        self.assertIs(root.op('null_tabletop_masked').inputs[0], original)
        self.assertIsNone(root.op(BRANCH))
        self.assertIsNone(root.fetch(BACKUP, None))

    def test_unexpected_graph_is_rejected_before_changes(self):
        graph, root, symbols = fixture()
        root.op('null_tabletop_masked').inputs = [root.op('render_floor')]
        with self.assertRaises(ValueError):
            isolate_aisi_tabletop_targets(graph.get, symbols)
        self.assertIsNone(root.op(BRANCH))

    def test_constant_alpha_alias_and_absent_parameter_are_checked(self):
        node = Node({}, '/constant')
        for name in ('colorr', 'colorg', 'colorb', 'colora'):
            setattr(node.par, name, 1)
        _configure_transparent(node)
        self.assertEqual(node.par.colora.val, 0)
        del node.par.values['colora']
        node.par.colorr.val = 1
        with self.assertRaisesRegex(ValueError, 'Vorhanden:'):
            _configure_transparent(node)
        self.assertEqual(node.par.colorr.val, 1)

    def test_preview_keeps_original_output_until_explicit_activation(self):
        graph, root, symbols = fixture()
        report = isolate_aisi_tabletop_targets(graph.get, symbols, activate=False)
        self.assertFalse(report['activated'])
        self.assertEqual(report['source_geometries_selected'], 5)
        self.assertEqual(root.op('null_tabletop_masked').inputs, [root.op('mask_tabletop')])
        self.assertTrue(activate_aisi_tabletop_targets(graph.get)['activated'])
        self.assertEqual(root.op('null_tabletop_masked').inputs, [root.op(BRANCH).op('select_mode')])

    def test_context_error_in_preview_prevents_activation(self):
        graph, root, symbols = fixture()
        isolate_aisi_tabletop_targets(graph.get, symbols, activate=False)
        root.op(BRANCH).op('render_sources_and_motion').errors = lambda: 'Geometry expression error'
        with self.assertRaisesRegex(ValueError, 'Geometry expression error'):
            activate_aisi_tabletop_targets(graph.get)
        self.assertEqual(root.op('null_tabletop_masked').inputs, [root.op('mask_tabletop')])

    def test_overlapping_target_images_do_not_leak_onto_foreign_surface(self):
        graph, root, symbols = fixture()
        isolate_aisi_tabletop_targets(graph.get, symbols)
        class Channel:
            def __init__(self, value): self.value = value
            def eval(self): return self.value
        raw = {'study/mode': Channel(2), 'table/count': Channel(2),
               'table/0/source_available': Channel(1), 'table/1/source_available': Channel(1)}
        def evaluate(node):
            if node.kind == 'constantTOP':
                return [0, 0]
            if node.kind == 'switchTOP':
                return evaluate(node.inputs[eval(node.par.index.expr, {'op': lambda _: raw})])
            if node.kind == 'compositeTOP':
                a, b = [evaluate(n) for n in node.inputs]
                return [x + y for x, y in zip(a, b)]
            if node.kind == 'multiply':
                a, b = [evaluate(n) for n in node.inputs]
                return [x * y for x, y in zip(a, b)]
            if node.kind == 'render':
                path = node.par.geometry.val
                if path.endswith('/table_target_tabletop_geo'):
                    return [1, 1] if '/item1/' in path else [2, 2]
                if path.endswith('/table_mask_geo'):
                    return [1, 0] if '/item1/' in path else [0, 1]
                return [0, 0]  # Kein Source-/Pfeilpixel in dieser Stichprobe.
            if node is root.op('null_table_mask'):
                return [1, 1]
            return evaluate(node.inputs[0])
        output = root.op('null_tabletop_masked')
        # Beide Ziele schneiden beide Tischflächen: die gemeinsame Maske wäre [3, 3].
        self.assertEqual(evaluate(output), [1, 2])
        raw['table/0/source_available'] = Channel(0)
        self.assertEqual(evaluate(output), [0, 2])
        raw['table/0/source_available'] = Channel(1)
        raw['table/count'] = Channel(1)
        self.assertEqual(evaluate(output), [1, 0])

    def test_partial_creation_failure_rolls_back_output_and_new_nodes(self):
        graph, root, symbols = fixture()
        original_create = root.create
        def create(kind, name):
            branch = original_create(kind, name)
            branch.copy = lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError('creation failed'))
            return branch
        root.create = create
        with self.assertRaises(RuntimeError):
            isolate_aisi_tabletop_targets(graph.get, symbols)
        self.assertIsNone(root.op(BRANCH))
        self.assertEqual(root.op('null_tabletop_masked').inputs, [root.op('mask_tabletop')])


if __name__ == '__main__':
    unittest.main()
