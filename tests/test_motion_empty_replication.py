"""Absent runtime replicas must not conceal edits to protected TD nodes."""
import copy
from types import SimpleNamespace
import unittest

from test_motion_output_routing import Node,fixture
from td_builders import build_motion_output_routing as routing


class EmptyReplicationTests(unittest.TestCase):
    def graph(self):
        graph=fixture()
        for name,kind in (('table_template','container'),('replicate_tables','replicator'),
                          ('tables_active','script'),('tables_active_callbacks','text'),
                          ('replicator_callbacks','text')):
            node=Node(graph,routing.LAYOUT+name,kind)
            if kind=='text':
                node.isDAT=True
                node.text='original callback'
        table=graph[routing.LAYOUT+'tables_active']
        table.numRows=1
        table.numCols=8
        table.channels={(0,col):SimpleNamespace(eval=lambda:None)
                        for col in range(8)}
        # Node.__getitem__ returns channel wrappers; use a table-specific type.
        class TableNode(Node):
            def __getitem__(self,key):
                return SimpleNamespace(val=self.header[key[1]])
        table.__class__=TableNode
        table.header=('id','type','x','y','rot','target_x','target_y','target_rot')
        replicator=graph[routing.LAYOUT+'replicate_tables']
        replicator.par.template=table.path
        replicator.par.master=routing.LAYOUT+'table_template'
        replicator.par.callbacks=routing.LAYOUT+'replicator_callbacks'
        replicator.par.namefromtable='rowindex'
        graph[routing.RAW].channels['table/count']=0
        for index in range(1,6):
            Node(graph,routing.LAYOUT+'item%d'%index,'container')
            Node(graph,routing.LAYOUT+'item%d/table_mask_geo'%index,'geo')
        expected=routing.snapshot(graph.get)
        for index in range(1,6):
            graph[routing.LAYOUT+'item%d'%index].destroy()
        return graph,expected

    def test_empty_replication_passes_without_mutating_saved_snapshot_or_graph(self):
        graph,expected=self.graph()
        saved=copy.deepcopy(expected)
        before=routing.snapshot(graph.get)
        routing.assert_snapshot(graph.get,expected)
        self.assertEqual(expected,saved)
        self.assertEqual(routing.snapshot(graph.get),before)

    def test_nonzero_count_and_nonempty_table_fail(self):
        for change in ('count','rows','header'):
            with self.subTest(change=change):
                graph,expected=self.graph()
                if change=='count': graph[routing.RAW].channels['table/count']=1
                elif change=='rows': graph[routing.LAYOUT+'tables_active'].numRows=2
                else: graph[routing.LAYOUT+'tables_active'].header=('wrong',)*8
                with self.assertRaises(RuntimeError): routing.assert_snapshot(graph.get,expected)

    def test_recipe_or_template_changes_fail(self):
        for name in ('table_template','replicate_tables','tables_active_callbacks','replicator_callbacks'):
            with self.subTest(name=name):
                graph,expected=self.graph()
                node=graph[routing.LAYOUT+name]
                if node.isDAT: node.text='local edit'
                else: node.par.local_edit=1
                with self.assertRaises(RuntimeError): routing.assert_snapshot(graph.get,expected)

    def test_missing_static_node_fails(self):
        graph,expected=self.graph()
        graph[routing.LAYOUT+'render_tabletop'].destroy()
        with self.assertRaises(RuntimeError): routing.assert_snapshot(graph.get,expected)

    def test_present_modified_instance_is_never_exempted(self):
        graph,expected=self.graph()
        Node(graph,routing.LAYOUT+'item1','container').par.local_edit=1
        with self.assertRaises(RuntimeError): routing.assert_snapshot(graph.get,expected)

    def test_modified_mask_is_never_exempted(self):
        graph,expected=self.graph()
        graph[routing.LAYOUT+'mask_tabletop'].inputs.reverse()
        with self.assertRaises(RuntimeError): routing.assert_snapshot(graph.get,expected)

    def test_missing_descendant_of_present_root_fails(self):
        graph,expected=self.graph()
        Node(graph,routing.LAYOUT+'item1','container')
        with self.assertRaises(RuntimeError): routing.assert_snapshot(graph.get,expected)
