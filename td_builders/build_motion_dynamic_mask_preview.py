"""Room Editor Motion with copied physical mask shapes; isolated test only."""
import builtins
import json
from pathlib import Path
import sys

REPO=Path('/Users/Johannes/dev/Promotion_Prototypen/AISI')
NAME='comp_aisi_motion_dynamic_mask_preview'
MOTION='/project1/comp_aisi_motion_v1_5'
LAYOUT='/project1/comp_layout_proposal/'


def mask_expression(adapter_path,row,parameter,timed=True):
    expression='op(%r).module.value(%d,%r)' % (adapter_path,row,parameter)
    # numpyArray() inside a DAT module does not reliably expose TOP dirtiness
    # to the calling Geo parameter. Keep the value and add a TD time dependency.
    return '(%s, absTime.frame)[0]' % expression if timed else expression


def absolute_ops(parameter):
    value=parameter.eval()
    if value is None:
        return ''
    values=value if isinstance(value,(list,tuple)) else [value]
    if not values:
        return ''
    paths=[]
    for item in values:
        if hasattr(item,'path'):
            paths.append(item.path)
        elif isinstance(item,str) and (not item or item.startswith('/')):
            paths.append(item)
        else:
            raise RuntimeError('OP-Referenz vor dem Kopieren nicht absolut auflösbar: '+parameter.name)
    return ' '.join(paths)


def surface_parameter(sop):
    parameter=getattr(sop.par,'sops',None)
    if parameter is None:
        parameter=getattr(sop.par,'soppath',None)
    if parameter is None:
        raise RuntimeError('Select SOP besitzt keinen bekannten Quellparameter.')
    return parameter


def build(resolve,symbols):
    root=resolve('/project1')
    if root is None or root.op(NAME) is not None:
        raise RuntimeError('project1 fehlt oder dynamischer Prüfzweig existiert; nichts geändert.')
    motion=resolve(MOTION)
    original_render=resolve(LAYOUT+'render_table_mask')
    original_reorder=resolve(LAYOUT+'reorder_table_mask')
    original_multiply=resolve(LAYOUT+'mask_tabletop')
    original_geo=resolve('/project1/comp_study_visualization/rect_setup_mask_geo_00')
    if any(n is None for n in (motion,original_render,original_reorder,original_multiply,original_geo)):
        raise RuntimeError('Erwartete Motion-/Maskenknoten fehlen; nichts geändert.')
    if not motion.par.Useosc.eval() or motion.par.Demo.eval():
        raise RuntimeError('Motion-Hauptkomponente verwendet noch keine Room-Editor-OSC-Posen.')
    surface=original_geo.op('select_table_surface')
    if surface is None or str(surface.type) != 'select':
        raise RuntimeError('Kopierbare Select-SOP-Maskenfläche fehlt.')
    shape_path=absolute_ops(surface_parameter(surface))
    if not shape_path:
        raise RuntimeError('Bestehende Maskenfläche nicht aufgelöst.')
    render_references={}
    for name in ('camera','lights','material'):
        p=getattr(original_render.par,name,None)
        if p is not None:
            render_references[name]=absolute_ops(p)
    material=getattr(original_geo.par,'material',None)
    geo_material=absolute_ops(material) if material is not None else None
    comp=root.create(symbols['containerCOMP'],NAME)
    try:
        comp.nodeX,comp.nodeY=1500,-1100
        def select(name,path):
            node=comp.create(symbols['selectTOP'],name)
            node.par.top=path
            return node
        state=select('motion_state',MOTION+'/state')
        floor=select('motion_floor',MOTION+'/out_floor')
        tabletop=select('motion_tabletop',MOTION+'/out_tabletop')
        adapter=comp.create(symbols['textDAT'],'mask_adapter')
        adapter.text=(REPO/'td_builders/motion_sim_mask.py').read_text(encoding='utf-8')+'''
def value(row, parameter):
    data=op(%r).numpyArray(delayed=False)
    return mask_transform(data,row)[('tx','ty','rz','sx').index(parameter)]
''' % state.path
        geos=[]
        for row in range(5):
            geo=comp.copy(original_geo,name='mask_item_%d' % row,includeDocked=False)
            copied=surface_parameter(geo.op('select_table_surface'))
            copied.expr=''
            copied.val=shape_path
            if geo_material is not None:
                geo.par.material=geo_material
            for parameter in ('tx','ty','rz','sx'):
                getattr(geo.par,parameter).expr=mask_expression(adapter.path,row,parameter)
            geo.render=True
            geos.append(geo)
        renderer=comp.copy(original_render,name='render_simulation_mask',includeDocked=False)
        for name,path in render_references.items():
            p=getattr(renderer.par,name)
            p.expr=''
            p.val=path
        renderer.par.geometry.expr=''
        renderer.par.geometry=' '.join(g.path for g in geos)
        reorder=comp.copy(original_reorder,name='reorder_simulation_mask',includeDocked=False)
        reorder.inputConnectors[0].connect(renderer)
        masked=comp.copy(original_multiply,name='tabletop_masked',includeDocked=False)
        for p in original_multiply.pars():
            if str(p.mode) != 'ParMode.CONSTANT':
                getattr(masked.par,p.name).expr='op(%r).par.%s.eval()' % (original_multiply.path,p.name)
        masked.inputConnectors[0].connect(tabletop)
        masked.inputConnectors[1].connect(reorder)
        if list(masked.inputs) != [tabletop,reorder]:
            raise RuntimeError('Lokale Multiply-Eingänge unvollständig.')
        for name,source in (('floor',floor),('tabletop',masked)):
            out=comp.create(symbols['outTOP'],'out_'+name)
            out.inputConnectors[0].connect(source)
        checked={}
        for name in ('render_simulation_mask','reorder_simulation_mask','tabletop_masked',
                     'out_floor','out_tabletop'):
            node=comp.op(name)
            node.cook(force=True)
            if node.errors():
                raise RuntimeError(node.path+': '+str(node.errors()))
            checked[name]=[node.width,node.height]
        comp.store('motion_dynamic_simulation_only',True)
        return {'component':comp.path,'source':MOTION,
                'tabletop':comp.op('out_tabletop').path,'floor':comp.op('out_floor').path,
                'pose_source':'same advancing state TOP for content and copied masks',
                'mask_shape_source':shape_path,'original_nodes_changed':False,
                'production_outputs_changed':False,'saved':False,
                'node_sizes':checked,'live_stream':motion.fetch('motion_live_status',None),
                'status':'dynamic simulation built and cooked; movement acceptance pending'}
    except Exception:
        comp.destroy()
        raise


def symbol(name):
    return (globals().get(name) or getattr(builtins,name,None)
            or getattr(sys.modules.get('__main__'),name,None))


if globals().get('__spec__') is None and callable(symbol('op')):
    kinds=('containerCOMP','selectTOP','textDAT','outTOP')
    print(json.dumps(build(symbol('op'),{k:symbol(k) for k in kinds}),ensure_ascii=False,indent=2))
