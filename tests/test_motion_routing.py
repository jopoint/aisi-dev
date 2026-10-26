"""Routing preconditions and mode isolation without a TouchDesigner process."""
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, MagicMock

from td_builders.build_motion_routing_preview import GATE, LAYOUT, MOTION, preflight, build


def par(value, mode='ParMode.CONSTANT', name='operand'):
    return SimpleNamespace(eval=lambda:value, mode=mode, name=name)


def fixture():
    def node(name, kind='null'):
        return SimpleNamespace(path=LAYOUT+name, type=kind, inputs=[],
                               par=SimpleNamespace(), pars=lambda:[])
    nodes={}
    for name in ('null_floor_with_optional_synth_chairs','null_tabletop_masked',
                 'null_table_mask','null_tabletop','chair_source'):
        n=node(name)
        nodes[n.path]=n
    mask=node('mask_tabletop','comp')
    mask.inputs=[nodes[LAYOUT+'null_tabletop'], nodes[LAYOUT+'null_table_mask']]
    mask.par.operand=par('multiply')
    nodes[LAYOUT+'null_tabletop_masked'].inputs=[mask]
    chairs=node('composite_floor_with_synth_chairs','comp')
    chairs.inputs=[node('floor_source'), nodes[LAYOUT+'chair_source']]
    switch=node('switch_enable_synth_chairs_regular','switch')
    switch.inputs=[node('select_floor_for_synth_chairs'),chairs]
    nodes[LAYOUT+'null_floor_with_optional_synth_chairs'].inputs=[switch]
    for n in (mask,chairs,switch):
        nodes[n.path]=n
    for name in ('out_floor','out_tabletop'):
        nodes[MOTION+name]=node(name)
    return nodes


class MotionRoutingTests(unittest.TestCase):
    def test_mode_gate_keeps_tracking_study_missing_mode_and_disabled_legacy(self):
        for enabled in (False, True):
            owner=SimpleNamespace(par=SimpleNamespace(Enablemotion=par(enabled)))
            for mode in (None,0,1,2,3):
                raw={} if mode is None else {'study/mode':par(mode)}
                class Channels(dict):
                    def __getitem__(self,key): return self.get(key)
                result=eval(GATE,{'parent':lambda:owner, 'op':lambda path:Channels(raw)})
                self.assertEqual(result,int(enabled and mode==2))
            self.assertEqual(eval(GATE,{'parent':lambda:owner,'op':lambda path:None}),0)

    def test_preflight_uses_existing_chair_input_and_does_not_modify_graph(self):
        nodes=fixture()
        before={p:list(n.inputs) for p,n in nodes.items()}
        result=preflight(nodes.get)
        self.assertIs(result['chairs'],nodes[LAYOUT+'chair_source'])
        self.assertEqual(before,{p:list(n.inputs) for p,n in nodes.items()})

    def test_preflight_rejects_different_mask_order(self):
        nodes=fixture()
        nodes[LAYOUT+'mask_tabletop'].inputs.reverse()
        with self.assertRaisesRegex(RuntimeError,'Maskenreihenfolge'):
            preflight(nodes.get)

    def test_preflight_rejects_relative_dynamic_composite_parameters(self):
        nodes=fixture()
        nodes[LAYOUT+'mask_tabletop'].pars=lambda:[par('multiply','ParMode.EXPRESSION')]
        with self.assertRaisesRegex(RuntimeError,'Dynamische Composite'):
            preflight(nodes.get)

    def test_preflight_accepts_resolution_expressions_but_rejects_exports_and_bindings(self):
        nodes=fixture()
        original=nodes[LAYOUT+'composite_floor_with_synth_chairs']
        original.pars=lambda:[par(2000,'ParMode.EXPRESSION',name)
                              for name in ('resolutionw','resolutionh')]
        self.assertIs(preflight(nodes.get)['chair_comp'],original)
        for mode in ('ParMode.EXPORT','ParMode.BIND'):
            original.pars=lambda:[par(2000,mode,'resolutionw')]
            with self.assertRaisesRegex(RuntimeError,'Dynamische Composite'):
                preflight(nodes.get)

    def test_failed_build_destroys_only_new_component(self):
        nodes=fixture()
        own=Mock()
        own.appendCustomPage.side_effect=RuntimeError('TD API failure')
        root=Mock()
        root.op.return_value=None
        root.create.return_value=own
        nodes['/project1']=root
        with self.assertRaisesRegex(RuntimeError,'TD API failure'):
            build(nodes.get,{'containerCOMP':'container'})
        own.destroy.assert_called_once_with()
        root.destroy.assert_not_called()

    def test_build_connects_only_new_nodes_and_keeps_production_inputs(self):
        nodes=fixture()
        original=nodes[LAYOUT+'composite_floor_with_synth_chairs']
        dimensions={'resolutionw':2000, 'resolutionh':1500}
        resolution=[]
        for name in dimensions:
            p=par(0,'ParMode.EXPRESSION',name)
            p.expr="op('../render_floor').width" if name=='resolutionw' else "op('../render_floor').height"
            p.eval=lambda name=name:dimensions[name]
            setattr(original.par,name,p)
            resolution.append(p)
        original.pars=lambda:resolution
        before={path:list(node.inputs) for path,node in nodes.items()}
        created={}
        comp=MagicMock(path='/project1/test_routing')
        def create(kind,name):
            node=MagicMock(path=comp.path+'/'+name)
            node.inputConnectors=[Mock(),Mock()]
            created[name]=node
            return node
        comp.create.side_effect=create
        comp.copy.side_effect=lambda original,name,includeDocked:create('copy',name)
        comp.op.side_effect=created.get
        root=Mock()
        root.op.return_value=None
        root.create.return_value=comp
        nodes['/project1']=root
        report=build(nodes.get,{name:name for name in
                               ('containerCOMP','selectTOP','switchTOP','outTOP')})
        self.assertFalse(report['existing_nodes_changed'])
        self.assertEqual(before,{p:list(nodes[p].inputs) for p in before})
        created['tabletop_masked'].inputConnectors[0].connect.assert_called_once_with(
            created['tabletop_motion'])
        created['tabletop_masked'].inputConnectors[1].connect.assert_called_once_with(
            created['mask_existing'])
        created['floor_with_chairs'].inputConnectors[1].connect.assert_called_once_with(
            created['chairs_existing'])
        self.assertEqual(created['floor_switch'].par.index.expr,GATE)
        self.assertEqual(created['tabletop_switch'].par.index.expr,GATE)
        for name in dimensions:
            expression=getattr(created['floor_with_chairs'].par,name).expr
            self.assertEqual(expression,'op(%r).par.%s.eval()' % (original.path,name))
            self.assertEqual(eval(expression,{'op':nodes.get}),dimensions[name])
            dimensions[name]+=123
            self.assertEqual(eval(expression,{'op':nodes.get}),dimensions[name])
            self.assertIn('../render_floor',getattr(original.par,name).expr)
        comp.destroy.assert_not_called()


if __name__=='__main__':
    unittest.main()
