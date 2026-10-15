"""Floor-Naht: kanonische Geometrie, Modussperren und rücknehmbarer TD-Helfer."""
import math
from types import SimpleNamespace as NS
import unittest

from aisi.app.sim_scene_to_osc import send_tables
from aisi.core.models import TableState
from aisi.core.table_geometry import table_world_footprint
from aisi.analysis.rect_groupwork_adaptive_prototype import _polygons_overlap_with_positive_area
from td_builders.aisi_study_visual_style import (
    rect_floor_join_side, joined_rect_floor_segments, floor_join_side_for_geo,
    shared_callback_source, TD_UNITS_PER_CM,
)
from td_builders.study_target_floor import rect_target_floor_dash_segments
from td_builders import repair_aisi_joined_floor_contours as repair


def parameter(value):
    return NS(eval=lambda:value)


class Scene:
    def __init__(self):
        self.storage={};self.children=[];self.scripts={};self.name='comp_layout_proposal'
        self.raw={'study/mode':parameter(2),'table/count':parameter(2)}
        self.style=Style(self)
        self.items=[Item(self,'table_template',0),Item(self,'item1',0),Item(self,'item2',80)]
        self.children=[*self.items,self.style]
    def op(self,name): return next((n for n in self.children if n.name==name),None)
    def fetch(self,key,default): return self.storage.get(key,default)
    def store(self,key,value): self.storage[key]=value
    def resolve(self,path):
        if path==repair.ROOT:return self
        if path==repair.STYLE:return self.style
        if path=='/project1/comp_io/null_osc_raw':return self.raw
        return self.scripts.get(path)


class Style:
    name='aisi_table_visual_style'
    def __init__(self,scene):self.scene=scene;self.text=shared_callback_source(join_aware=False)
    @property
    def module(self):
        namespace={'op':self.scene.resolve};exec(self.text,namespace)
        return NS(**namespace)


class Item:
    def __init__(self,scene,name,y):
        self.scene=scene;self.name=name;self.path=repair.ROOT+'/'+name
        self.par=NS(Tabletype=parameter('rect'))
        self.geo=Geo(self,y);self.script=Script(self.geo)
        self.callback=NS(text=f'op({repair.STYLE!r}).module.paint(scriptOp, "target_floor")')
    def parent(self):return self.scene
    def op(self,path):
        return {'table_target_floor_geo':self.geo,
                'table_target_floor_geo/table_outline_outer':self.script,
                'table_target_floor_geo/table_outline_outer_callbacks':self.callback}.get(path)


class Geo:
    def __init__(self,item,y):
        self.item=item;self.path=item.path+'/table_target_floor_geo'
        self.par=NS(tx=parameter(0.),ty=parameter(y*TD_UNITS_PER_CM),rz=parameter(0.),
                    sx=parameter(1.),sy=parameter(1.))
    def parent(self):return self.item


class Script:
    def __init__(self,geo):
        self.geo=geo;self.path=geo.path+'/table_outline_outer'
        self.par=NS();self.customPages=[];self.fail=False
        geo.item.scene.scripts[self.path]=self
    def parent(self):return self.geo
    def appendCustomPage(self,name):
        page=Page(self,name);self.customPages.append(page);return page


class Page:
    def __init__(self,script,name):self.script=script;self.name=name;self.pars=[]
    def appendFloat(self,name,**kwargs):
        if self.script.fail:raise RuntimeError('injected failure')
        par=NS(name=name,expr='')
        par.eval=lambda:eval(par.expr,{'op':self.script.geo.item.scene.resolve,'parent':self.script.parent})
        setattr(self.script.par,name,par);self.pars.append(par)
    def destroy(self):
        for par in self.pars:delattr(self.script.par,par.name)
        self.script.customPages.remove(self)


class JoinedFloorTests(unittest.TestCase):
    def test_exact_contact_detection_rejects_gap_penetration_and_offset(self):
        for angle in (0,37,90,180):
            normal=(-math.sin(math.radians(angle)),math.cos(math.radians(angle)))
            other=(80*normal[0],80*normal[1],angle+180)
            self.assertEqual(rect_floor_join_side((0,0,angle),[other]),1)
            self.assertEqual(rect_floor_join_side(other,[(0,0,angle)]),1)  # reversed local normal
        for other in ((0,79.99,0),(0,80.01,0),(1,80,0),(0,80,1),(0,0,0)):
            self.assertEqual(rect_floor_join_side((0,0,0),[other]),0)
        self.assertEqual(rect_floor_join_side((0,0,0),[(0,80,0),(0,-80,0)]),0)

    def test_padded_contours_overlap_but_clipped_bars_do_not(self):
        segments=rect_target_floor_dash_segments()
        def polygons(parts,center,rotation):
            angle=math.radians(rotation)
            for part in parts:
                x,y=part.x_td/TD_UNITS_PER_CM,part.y_td/TD_UNITS_PER_CM
                point=(center[0]+x*math.cos(angle)-y*math.sin(angle),
                       center[1]+x*math.sin(angle)+y*math.cos(angle))
                proxy=TableState('bar',*point,width=part.width_td/TD_UNITS_PER_CM,
                                 height=part.depth_td/TD_UNITS_PER_CM)
                yield table_world_footprint(proxy,point,rotation)
        for angle in (0,37,90):
            normal=(-math.sin(math.radians(angle)),math.cos(math.radians(angle)))
            center=(80*normal[0],80*normal[1])
            physical=TableState('rect',0,0,table_type='rect')
            self.assertFalse(_polygons_overlap_with_positive_area(
                table_world_footprint(physical,(0,0),angle),table_world_footprint(physical,center,angle)))
            a=list(polygons(segments,(0,0),angle));b=list(polygons(segments,center,angle))
            self.assertTrue(any(_polygons_overlap_with_positive_area(x,y) for x in a for y in b))
            left=joined_rect_floor_segments(segments,1);right=joined_rect_floor_segments(segments,-1)
            self.assertEqual((len(left),len(right)),(8,8))
            a=list(polygons(left,(0,0),angle));b=list(polygons(right,center,angle))
            self.assertFalse(any(_polygons_overlap_with_positive_area(x,y) for x in a for y in b))
        self.assertEqual(joined_rect_floor_segments(segments,0),segments)

    def test_mode_count_and_scale_guards_read_rendered_poses(self):
        scene=Scene();geo=scene.items[1].geo
        self.assertEqual(floor_join_side_for_geo(geo,scene.resolve),1)
        scene.items[2].geo.par.ty=parameter(81*TD_UNITS_PER_CM)
        self.assertEqual(floor_join_side_for_geo(geo,scene.resolve),0)
        scene.items[2].geo.par.ty=parameter(80*TD_UNITS_PER_CM)
        for mode in (0,1):
            scene.raw['study/mode']=parameter(mode)
            self.assertEqual(floor_join_side_for_geo(geo,scene.resolve),0)
        scene.raw['study/mode']=parameter(2);scene.raw['table/count']=parameter(1)
        self.assertEqual(floor_join_side_for_geo(geo,scene.resolve),0)
        scene.raw['table/count']=parameter(2);geo.par.sx=parameter(1.01)
        self.assertEqual(floor_join_side_for_geo(geo,scene.resolve),0)

    def test_existing_osc_axes_and_yaw_produce_the_same_join(self):
        scene=Scene();angle=37.;normal=(-math.sin(math.radians(angle)),math.cos(math.radians(angle)))
        poses=[(200.,200.),(200+80*normal[0],200+80*normal[1])]
        tables=[dict(id=f'table_{i}',x_cm=x,y_cm=y,rotation_deg=angle,
                     width_cm=160.,height_cm=80.,table_type='rect') for i,(x,y) in enumerate(poses)]
        targets=[dict(x_cm=x,y_cm=y,rotation_deg=angle) for x,y in poses]
        messages={}
        class Recorder:
            def send_message(self,address,value):messages[address]=value
        send_tables(Recorder(),tables,targets)
        for i,item in enumerate(scene.items[1:]):
            item.geo.par.tx=parameter((messages[f'/table/{i}/target_x']-250)*TD_UNITS_PER_CM)
            item.geo.par.ty=parameter(-(messages[f'/table/{i}/target_y']-250)*TD_UNITS_PER_CM)
            item.geo.par.rz=parameter(messages[f'/table/{i}/target_rot'])
        self.assertEqual([floor_join_side_for_geo(item.geo,scene.resolve) for item in scene.items[1:]],[-1,1])

    def test_serialized_code_and_missing_binding_fallback(self):
        namespace={};exec(shared_callback_source(),namespace)
        segments=namespace['rect_target_dash_segments'](170,90)
        expected=joined_rect_floor_segments(rect_target_floor_dash_segments(),1)
        self.assertEqual([tuple(vars(p).values()) for p in expected],list(namespace['joined_rect_floor_segments'](segments,1)))
        class Painter:
            par=NS()
            def clear(self):self.points=[]
            def appendPoly(self,*args,**kwargs):
                polygon=[NS(point=NS(P=None)) for _ in range(4)];self.points.append(polygon);return polygon
        old={};exec(shared_callback_source(join_aware=False),old)
        for role in ('source_tabletop','target_tabletop','target_floor'):
            a=Painter();b=Painter();old['paint'](a,role);namespace['paint'](b,role)
            self.assertEqual([[p.point.P for p in poly] for poly in a.points],[[p.point.P for p in poly] for poly in b.points])
        painter=Painter();painter.par=NS(Joiningside=parameter(1))
        namespace['paint'](painter,'target_floor');self.assertEqual(len(painter.points),8)
        namespace['paint'](painter,'target_tabletop');self.assertEqual(len(painter.points),12)

    def test_manual_helper_is_idempotent_and_reversible(self):
        scene=Scene();original=scene.style.text
        result=repair.repair_joined_floor_contours(scene.resolve,'offline')
        self.assertFalse(result['saved']);self.assertEqual(result['bound_contours'],3)
        self.assertEqual([row['side'] for row in result['join_sides']],[1,-1])
        repair.repair_joined_floor_contours(scene.resolve,'offline')
        self.assertTrue(all(len(item.script.customPages)==1 for item in scene.items))
        repair.restore_joined_floor_contours(scene.resolve)
        self.assertEqual(scene.style.text,original)
        self.assertTrue(all(not item.script.customPages for item in scene.items))

    def test_preflight_and_partial_failure_preserve_original(self):
        scene=Scene();original=scene.style.text
        scene.items[2].callback.text='unknown'
        with self.assertRaises(ValueError):repair.repair_joined_floor_contours(scene.resolve,'offline')
        self.assertEqual(scene.style.text,original)
        self.assertTrue(all(not item.script.customPages for item in scene.items))
        scene=Scene();original=scene.style.text;scene.items[1].script.fail=True
        with self.assertRaises(RuntimeError):repair.repair_joined_floor_contours(scene.resolve,'offline')
        self.assertEqual(scene.style.text,original)
        self.assertTrue(all(not item.script.customPages for item in scene.items))


if __name__=='__main__':unittest.main()
