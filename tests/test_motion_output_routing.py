"""Production insertion/rollback using a small in-memory TD graph model."""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest
import numpy as np

from td_builders.build_motion_output_routing import (
    build,check,uninstall,preflight,snapshot,signature,expected_installed,
    PATH,NAME,BRIDGE,LAYOUT,OUTPUT,MOTION,RAW,GATE)


class Parameter:
    def __init__(self,node,name,value=0):
        self.node,self.name=node,name
        self._val,self._expr=value,''
        self.mode='ParMode.CONSTANT'
        self.bindExpr=''
    @property
    def val(self): return self._val
    @val.setter
    def val(self,value):
        self._val=value; self.mode='ParMode.CONSTANT'
    @property
    def expr(self): return self._expr
    @expr.setter
    def expr(self,value):
        self._expr=value; self.mode='ParMode.EXPRESSION' if value else 'ParMode.CONSTANT'
    def eval(self):
        if self.mode=='ParMode.EXPRESSION':
            return eval(self.expr,{'op':self.node.graph.get,'absTime':SimpleNamespace(frame=10)})
        return self.val


class Parameters:
    def __init__(self,node):
        object.__setattr__(self,'node',node); object.__setattr__(self,'values',{})
    def __getattr__(self,name):
        if name not in self.values:
            self.values[name]=Parameter(self.node,name)
        return self.values[name]
    def __setattr__(self,name,value):
        getattr(self,name).val=value


class Connector:
    def __init__(self,node,index): self.node,self.index=node,index
    def connect(self,source):
        while len(self.node.inputs)<=self.index: self.node.inputs.append(None)
        self.node.inputs[self.index]=source


class Node:
    def __init__(self,graph,path,kind='null'):
        self.graph,self.path,self.type=graph,path,kind
        self.name=path.rsplit('/',1)[-1]
        self.isCOMP=kind=='container'; self.isDAT=False
        self.par=Parameters(self); self.inputs=[]; self.storage={}; self.channels={}
        self.inputConnectors=[Connector(self,i) for i in range(2)]
        self.failure=lambda:''
        self.array=np.full((2,2,4),.25,np.float32)
        graph[path]=self
    @property
    def children(self):
        return [n for p,n in self.graph.items() if p.rsplit('/',1)[0]==self.path]
    def create(self,kind,name): return Node(self.graph,self.path+'/'+name,kind)
    def op(self,name): return self.graph.get(self.path+'/'+name)
    def pars(self): return list(self.par.values.values())
    def appendCustomPage(self,name):
        return SimpleNamespace(appendToggle=lambda name,**kw:[getattr(self.par,name)])
    def store(self,k,v): self.storage[k]=v
    def fetch(self,k,default=None): return self.storage.get(k,default)
    def cook(self,**kw): pass
    def errors(self): return self.failure()
    def __getitem__(self,k):
        return SimpleNamespace(eval=lambda:self.channels[k]) if k in self.channels else None
    def numpyArray(self,**kw):
        if self.type=='select':
            data=self.graph[str(self.par.top.eval())].numpyArray()
            if self.par.values.get('outputresolution') and self.par.outputresolution.eval()=='custom':
                data=np.resize(data,(int(self.par.resolutionh.eval()),int(self.par.resolutionw.eval()),4))
            return data
        if self.type=='switch': return self.inputs[int(self.par.index.eval())].numpyArray()
        if self.inputs:
            if self.type=='comp':
                a,b=(n.numpyArray() for n in self.inputs)
                return a*b if self.par.operand.eval()=='multiply' else a+b
            return self.inputs[0].numpyArray()
        return self.array
    @property
    def width(self): return self.numpyArray().shape[1]
    @property
    def height(self): return self.numpyArray().shape[0]
    def destroy(self):
        for child in list(self.children): child.destroy()
        del self.graph[self.path]


def fixture():
    graph={}
    for path in ('/project1',LAYOUT[:-1],OUTPUT[:-1],'/project1/comp_study_visualization'):
        Node(graph,path,'container')
    def add(path,kind='null',inputs=()):
        node=Node(graph,path,kind)
        node.inputs=list(inputs)
        return node
    floor=add(OUTPUT+'select_floor','render')
    select=add(LAYOUT+'select_floor_for_synth_chairs','select'); select.par.top=floor.path
    chair_source=add(LAYOUT+'select_synth_chairs_regular','render')
    chairs=add(LAYOUT+'composite_floor_with_synth_chairs','comp',(select,chair_source)); chairs.par.operand='add'
    chair_switch=add(LAYOUT+'switch_enable_synth_chairs_regular','switch',(select,chairs))
    chair_switch.par.index=1
    final_floor=add(LAYOUT+'null_floor_with_optional_synth_chairs',inputs=(chair_switch,))
    render=add(LAYOUT+'render_tabletop','render')
    table=add(LAYOUT+'null_tabletop',inputs=(render,))
    mask_source=add(LAYOUT+'null_table_mask','render')
    mask=add(LAYOUT+'mask_tabletop','comp',(table,mask_source)); mask.par.operand='multiply'
    final_table=add(LAYOUT+'null_tabletop_masked',inputs=(mask,))
    for name,source in (('floor',final_floor),('tabletop',final_table),('table_mask',mask_source)):
        sel=add(OUTPUT+('select_central_floor' if name=='floor' else 'select_'+name),'select')
        sel.par.top=source.path
        switch=add(OUTPUT+'switch_'+name,'switch',(sel,)); switch.par.index=0
    for path in (LAYOUT+'panel_mode',OUTPUT+'panel_mode'):
        add(path,'chop').channels={'state':0}
    add(RAW,'chop').channels={'study/mode':2}
    for name in ('floor','tabletop'):
        add(MOTION+'out_'+name,'render').array=np.ones((1,1,4),np.float32)
    return graph


SYMBOLS={k:v for k,v in (('containerCOMP','container'),('selectTOP','select'),
                         ('switchTOP','switch'),('outTOP','out'))}


class MotionOutputRoutingTests(unittest.TestCase):
    def test_build_preserves_original_mask_chairs_and_projector_graph_pixel_bypass(self):
        graph=fixture(); before=snapshot(graph.get)
        report=build(graph.get,SYMBOLS)
        self.assertTrue(report['installed']); self.assertFalse(report['enabled'])
        self.assertEqual(report['bypass_pixel_checks'],3)
        self.assertEqual({p:signature(graph[p]) for p in before},expected_installed(before))
        self.assertEqual(graph[LAYOUT+'mask_tabletop'].inputs[0].path,LAYOUT+'null_tabletop')
        self.assertEqual(graph[LAYOUT+'mask_tabletop'].inputs[1].path,LAYOUT+'null_table_mask')
        self.assertTrue(check(graph.get)['passed'])

    def test_gate_requires_both_flags_aisi_mode_and_both_calibration_panels_off(self):
        graph=fixture(); build(graph.get,SYMBOLS); comp=graph[PATH]
        for enabled in (False,True):
            for approved in (False,True):
                comp.par.Enablemotion=enabled; comp.par.Sourceapproved=approved
                for mode in (0,1,2,3,None):
                    graph[RAW].channels={} if mode is None else {'study/mode':mode}
                    for lp,op in ((0,0),(1,0),(0,1),(1,1)):
                        graph[LAYOUT+'panel_mode'].channels={'state':lp}
                        graph[OUTPUT+'panel_mode'].channels={'state':op}
                        expected=int(enabled and approved and mode==2 and lp==0 and op==0)
                        actual=eval(GATE,{'op':graph.get,'absTime':SimpleNamespace(frame=1)})
                        self.assertEqual(actual,expected)
        del graph[RAW]
        self.assertEqual(eval(GATE,{'op':graph.get,'absTime':SimpleNamespace(frame=1)}),0)

    def test_uninstall_restores_all_original_nodes_and_removes_only_owned_nodes(self):
        graph=fixture(); before=snapshot(graph.get); paths=set(graph)
        build(graph.get,SYMBOLS)
        self.assertTrue(uninstall(graph.get)['original_graph_restored'])
        self.assertEqual(set(graph),paths)
        self.assertEqual(snapshot(graph.get),before)

    def test_failure_after_reconnection_rolls_back_originals_and_own_nodes(self):
        graph=fixture(); before=snapshot(graph.get); paths=set(graph)
        graph[OUTPUT+'switch_tabletop'].failure=lambda:(
            'injected output error' if str(graph[LAYOUT+'select_floor_for_synth_chairs'].par.top.val)
            ==PATH+'/out_floor' else '')
        with self.assertRaisesRegex(RuntimeError,'injected output error'):
            build(graph.get,SYMBOLS)
        self.assertEqual(set(graph),paths)
        self.assertEqual(snapshot(graph.get),before)

    def test_preflight_refuses_changed_mask_and_floor_reference_without_mutations(self):
        for change in ('mask','floor'):
            graph=fixture()
            if change=='mask': graph[LAYOUT+'mask_tabletop'].inputs.reverse()
            else: graph[LAYOUT+'select_floor_for_synth_chairs'].par.top='/some/local/edit'
            before=snapshot(graph.get); paths=set(graph)
            with self.assertRaises(RuntimeError): preflight(graph.get)
            self.assertEqual(set(graph),paths)
            self.assertEqual(snapshot(graph.get),before)

    def test_repeated_build_does_not_overwrite_existing_installation(self):
        graph=fixture(); build(graph.get,SYMBOLS)
        with self.assertRaisesRegex(RuntimeError,'existieren bereits'): build(graph.get,SYMBOLS)
        self.assertTrue(check(graph.get)['passed'])

    def test_subsequent_protected_edit_is_detected_and_not_overwritten(self):
        graph=fixture(); build(graph.get,SYMBOLS)
        graph[OUTPUT+'switch_floor'].par.index=1
        with self.assertRaisesRegex(RuntimeError,'Unerwartete'): uninstall(graph.get)
        self.assertEqual(graph[OUTPUT+'switch_floor'].par.index.val,1)
        self.assertIn(PATH,graph)

    def test_changed_owned_bridge_or_added_local_node_is_preserved(self):
        for change in ('bridge','new_node'):
            graph=fixture(); build(graph.get,SYMBOLS)
            if change=='bridge': graph[LAYOUT+BRIDGE].par.top='/another/local/source'
            else: graph[PATH].create('null','user_added_work')
            paths=set(graph)
            with self.assertRaisesRegex(RuntimeError,'lokal verändert'):
                uninstall(graph.get)
            self.assertEqual(set(graph),paths)

    def test_uninstall_allows_the_two_control_values_to_have_been_changed(self):
        graph=fixture(); build(graph.get,SYMBOLS)
        graph[PATH].par.Enablemotion=True; graph[PATH].par.Sourceapproved=True
        self.assertTrue(uninstall(graph.get)['removed'])

    def test_python39_syntax(self):
        for name in ('build','check','remove'):
            ast.parse(Path('td_builders/'+name+'_motion_output_routing.py').read_text(),feature_version=(3,9))


if __name__=='__main__': unittest.main()
