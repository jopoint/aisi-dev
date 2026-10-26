"""Motion preview transport and fail-closed freshness, without opening sockets."""
from pathlib import Path
from itertools import product,combinations
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from pythonosc.osc_packet import OscPacket
from td_builders.motion_design import Pose,td_tick,MotionLayout
from td_builders.motion_osc import frame_values,MotionOSCReader,PREFIX
from aisi.app.motion_preview_sim import bundle_for,MotionSimulation,make_scenario
from aisi.app.sim_room_editor import SimRoomEditor
from aisi.core.table_geometry import world_footprint,polygon_inside_roi,convex_polygons_intersect


def packet_channels(bundle):
    return {timed.message.address.lstrip('/'):timed.message.params[0]
            for timed in OscPacket(bundle.dgram).messages}


def rows(identity='table_0', x=110):
    return [(identity,Pose(x,180,84),Pose(320,330,122),True,True)]


class MotionOSCTests(unittest.TestCase):
    def test_multitable_fixtures_are_safe_for_independent_completion_orders(self):
        for count in (1,3,5):
            tables,targets=make_scenario(count)
            self.assertEqual(len(tables),count)
            self.assertEqual({t['id'] for t in tables},set(targets))
            # Every combination of source and achieved target must stay separate.
            for completed in product((False,True),repeat=count):
                polygons=[]
                for table,done in zip(tables,completed):
                    pose=targets[table['id']] if done else Pose(
                        table['x_cm'],table['y_cm'],table['rotation_deg'])
                    polygon=world_footprint('rect',*pose)
                    self.assertTrue(polygon_inside_roi(polygon),(count,completed,table['id']))
                    polygons.append(polygon)
                for first,second in combinations(polygons,2):
                    self.assertFalse(convex_polygons_intersect(first,second),(count,completed))

    def test_multitable_packet_identity_reordering_removal_and_independent_success(self):
        for count in (3,5):
            tables,targets=make_scenario(count)
            class Client:
                def send(self,bundle): self.values=packet_channels(bundle)
            editor=SimpleNamespace(running=True,tables=tables,selected_id='table_0',
                save_now=lambda:None,redraw=lambda:None,
                root=SimpleNamespace(after=lambda *a:None))
            client=Client()
            sim=MotionSimulation(editor,client,targets=targets)
            self.assertEqual(sum(sim.active.values()),count-1)
            self.assertFalse(sim.active['table_2'])
            reader=MotionOSCReader()
            sim.tick()
            reader.read(client.values,0)
            sim.tick()
            snapshot=reader.read(client.values,.05)
            self.assertTrue(snapshot['fresh'])
            self.assertEqual(len(snapshot['rows']),count)
            layout=MotionLayout()
            layout.activate(snapshot['layout'],.05)
            for identity,source,target,valid,active in snapshot['rows']:
                layout.update(identity,source,target,.05,valid)
            sim.set_target_pose()
            editor.tables.reverse()
            sim.tick()
            snapshot=reader.read(client.values,.1)
            for identity,source,target,valid,active in snapshot['rows']:
                layout.update(identity,source,target,.1,valid)
                self.assertEqual(target,targets[identity])
            self.assertEqual(layout.tables['table_0'].phase,'dissolve')
            self.assertEqual(layout.tables['table_1'].phase,'guidance')
            # Keep old CHOP channels while a table vanishes.
            retained=dict(client.values)
            editor.tables[:]=[t for t in editor.tables if t['id']!='table_1']
            sim.tick()
            retained.update(client.values)
            snapshot=reader.read(retained,.15)
            self.assertTrue(snapshot['fresh'])
            self.assertNotIn('table_1',[r[0] for r in snapshot['rows']])
            self.assertEqual(len(snapshot['rows']),count-1)

    def test_bundle_is_additive_and_preserves_exact_id_and_pairing(self):
        data=frame_values(rows('rect/a b'),123,1,1)
        decoded=packet_channels(bundle_for(data))
        self.assertTrue(all(name.startswith(PREFIX) for name in decoded))
        self.assertEqual(decoded,data)
        reader=MotionOSCReader()
        self.assertFalse(reader.read(decoded,0)['fresh'])
        decoded.update(packet_channels(bundle_for(frame_values(rows('rect/a b'),123,2,1))))
        result=reader.read(decoded,.05)
        self.assertTrue(result['fresh'])
        self.assertEqual(result['rows'][0][0],'rect/a b')
        self.assertEqual(result['rows'][0][1],Pose(110,180,84))

    def test_retained_frozen_startup_and_stopped_sender_never_remain_valid(self):
        reader=MotionOSCReader()
        a=frame_values(rows(),123,1,1)
        self.assertFalse(reader.read(a,0)['fresh'])
        self.assertFalse(reader.read(a,1)['fresh'])
        b=frame_values(rows(),123,2,1)
        self.assertTrue(reader.read(b,1.05)['fresh'])
        self.assertFalse(reader.read(b,1.56)['fresh'])
        c=frame_values(rows(),123,3,1)
        self.assertTrue(reader.read(c,1.6)['fresh'])
        self.assertEqual(reader.read(c,1.7)['layout'],('osc',123,1))

    def test_counts_exclude_retained_old_table_channels(self):
        reader=MotionOSCReader()
        channels=frame_values(rows('a')+rows('b'),123,1,1)
        reader.read(channels,0)
        channels.update(frame_values(rows('a'),123,2,1))
        result=reader.read(channels,.05)
        self.assertTrue(result['fresh'])
        self.assertEqual([r[0] for r in result['rows']],['a'])
        channels.update(frame_values([],123,3,1))
        result=reader.read(channels,.1)
        self.assertTrue(result['fresh'])
        self.assertEqual(result['rows'],[])

    def test_mixed_incomplete_frame_rejected(self):
        reader=MotionOSCReader()
        reader.read(frame_values(rows(),123,1,1),0)
        values=frame_values(rows(),123,2,1)
        values[PREFIX+'table/table_0/frame']=1
        self.assertFalse(reader.read(values,.05)['fresh'])

    def test_new_sender_needs_its_own_second_frame(self):
        reader=MotionOSCReader()
        reader.read(frame_values(rows(),123,1,1),0)
        self.assertTrue(reader.read(frame_values(rows(),123,2,1),.05)['fresh'])
        self.assertFalse(reader.read(frame_values(rows(),456,1,1),.1)['fresh'])
        self.assertTrue(reader.read(frame_values(rows(),456,2,1),.15)['fresh'])

    def test_pose_changes_do_not_change_layout_event(self):
        reader=MotionOSCReader()
        reader.read(frame_values(rows(),123,1,1),0)
        a=reader.read(frame_values(rows(x=120),123,2,1),.05)
        b=reader.read(frame_values(rows(x=130),123,3,1),.1)
        self.assertEqual(a['layout'],b['layout'])
        c=reader.read(frame_values(rows(x=130),123,4,2),.15)
        self.assertNotEqual(b['layout'],c['layout'])

    def test_replayed_frame_and_unannounced_target_change_rejected(self):
        reader=MotionOSCReader()
        reader.read(frame_values(rows(),123,1,1),0)
        reader.read(frame_values(rows(),123,3,1),.05)
        self.assertFalse(reader.read(frame_values(rows(),123,2,1),.1)['fresh'])
        changed=[('table_0',Pose(110,180,84),Pose(321,330,122),True,True)]
        self.assertFalse(reader.read(frame_values(changed,123,4,1),.15)['fresh'])
        self.assertTrue(reader.read(frame_values(changed,123,4,2),.2)['fresh'])

    def test_simulation_sends_actual_editor_pose_and_explicit_activation(self):
        class Client:
            def send(self,bundle): self.values=packet_channels(bundle)
        editor=SimpleNamespace(running=True,tables=[dict(id='table_0',type='rect',
            x_cm=110,y_cm=180,rotation_deg=84)],root=SimpleNamespace(after=lambda *a:None))
        client=Client()
        simulation=MotionSimulation(editor,client)
        reader=MotionOSCReader()
        simulation.tick()
        self.assertFalse(reader.read(client.values,0)['fresh'])
        editor.tables[0]['x_cm']=130
        simulation.tick()
        result=reader.read(client.values,.05)
        self.assertTrue(result['fresh'])
        self.assertEqual(result['rows'][0][1].x,130)
        layout=result['layout']
        simulation.paused=True
        simulation.tick()
        self.assertFalse(reader.read(client.values,.6)['fresh'])
        simulation.paused=False
        simulation.activate()
        simulation.tick()
        self.assertNotEqual(reader.read(client.values,.65)['layout'],layout)

    def test_room_editor_save_respects_isolated_path(self):
        with TemporaryDirectory() as folder:
            path=Path(folder)/'preview.json'
            editor=object.__new__(SimRoomEditor)
            editor.scene_path=path
            editor.tables,editor.chairs,editor.persons=[],[],[]
            editor.jitter_enabled=editor.occlusion_enabled=False
            with patch('aisi.app.sim_room_editor.scene_file_path',side_effect=AssertionError('default touched')):
                editor.save_now()
            self.assertTrue(path.exists())

    def test_actual_td_matrix_hides_stale_stream_and_does_not_reveal_on_movement(self):
        class Par:
            def __init__(self,value): self.value=value
            def eval(self): return self.value
        class Channel:
            def __init__(self,name,value): self.name,self.value=name,value
            def eval(self): return self.value
        class Owner:
            def __init__(self):
                self.saved={}
                self.channels={}
                self.par=SimpleNamespace(**{k:Par(v) for k,v in dict(
                    Useosc=True,Layoutrevision=1,Sourcex=110,Sourcey=180,Sourcer=84,
                    Targetx=320,Targety=330,Targetr=122,Demo=False,Usedat=False,
                    Valid=True,Streamtimeout=.5,Oscpath='/raw').items()})
            def fetch(self,k,d):return self.saved.get(k,d)
            def store(self,k,v):self.saved[k]=v
            def storeStartupValue(self,k,v):pass
            def op(self,path):return SimpleNamespace(chans=lambda:[Channel(k,v) for k,v in self.channels.items()])
        owner=Owner()
        def tick(frame,t,x=110):
            owner.channels.update(frame_values(rows(x=x),123,frame,1))
            with patch('td_builders.motion_design.time.monotonic',return_value=t):
                return td_tick(owner)
        self.assertEqual(tick(1,0)[5,0,2],0)
        active=tick(2,.05)
        self.assertEqual(active[5,0,2],1)
        self.assertEqual(active[0,0,0],110)
        moved=tick(3,.1,120)
        self.assertAlmostEqual(float(moved[5,0,1]),.05,places=5)
        self.assertEqual(moved[0,0,0],120)
        stale=tick(3,.7,120)
        self.assertEqual(stale[5,0,2],0)
        self.assertEqual(stale[:5].max(),0)


if __name__=='__main__':
    unittest.main()
