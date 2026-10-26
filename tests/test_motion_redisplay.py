"""Reappearance preserves actual engine state, IDs, proposals and revision."""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from td_builders import motion_redisplay as fade
from td_builders import update_motion_redisplay as update
from td_builders.motion_design import td_tick


class RedisplayTests(unittest.TestCase):
    def owner(self):
        class Par:
            def __init__(self,value): self.val=value
            def eval(self): return self.val
        storage={}
        owner=SimpleNamespace(par=SimpleNamespace(**{k:Par(v) for k,v in dict(
            Useosc=False,Layoutrevision=2,Sourcex=250,Sourcey=250,Sourcer=0,
            Targetx=250,Targety=250,Targetr=0,Demo=False,Usedat=False,Valid=True).items()}))
        owner.fetch=lambda key,default=None:storage.get(key,default)
        owner.store=lambda key,value:storage.update({key:value})
        owner.storeStartupValue=lambda *args:None
        return owner

    def test_actual_td_state_reactivates_softly_without_new_proposal(self):
        owner=self.owner()
        td_tick(owner,0)
        engine=owner.fetch('motion_engine')
        revision,started=engine.revision,engine.started
        table=engine.tables['preview_table']
        self.assertEqual(table.phase,'dissolve')
        td_tick(owner,1)
        self.assertEqual(table.phase,'completed')
        owner.par.Sourcex.val=270
        first=td_tick(owner,1.01)
        middle=td_tick(owner,1.185)
        end=td_tick(owner,1.361)
        self.assertEqual(first[0,5,0],0)
        self.assertAlmostEqual(middle[0,5,0],.5,places=5)
        self.assertEqual(end[0,5,0],1)
        self.assertEqual(end[0,5,1],1)
        self.assertIs(owner.fetch('motion_engine'),engine)
        self.assertIs(engine.tables['preview_table'],table)
        self.assertEqual((engine.revision,engine.started),(revision,started))
        self.assertEqual(tuple(end[0,1,:3]),(250,250,0))

    def test_initial_guidance_is_full_and_small_exit_does_not_reactivate(self):
        owner=self.owner()
        owner.par.Sourcex.val=300
        self.assertEqual(td_tick(owner,0)[0,5,0],1)
        owner.par.Sourcex.val=250
        td_tick(owner,.1)
        td_tick(owner,1.1)
        owner.par.Sourcex.val=267
        self.assertEqual(td_tick(owner,1.2)[0,2,3],2)
        self.assertFalse(owner.fetch(fade.KEY)['tables'])

    def test_invalid_tracking_hides_state_without_triggering_redisplay(self):
        owner=self.owner()
        td_tick(owner,0)
        td_tick(owner,1)
        owner.par.Sourcex.val=300
        owner.par.Valid.val=False
        self.assertEqual(td_tick(owner,1.1)[:5].max(),0)
        self.assertFalse(owner.fetch(fade.KEY)['tables'])

    def test_fade_does_not_restart_each_frame_and_is_per_id(self):
        events={'tables':{}}
        self.assertEqual(fade.visibility(events,'a','completed','guidance',1),0)
        self.assertAlmostEqual(fade.visibility(events,'a','guidance','guidance',1.175),.5)
        self.assertEqual(fade.visibility(events,'b','guidance','guidance',1.175),1)
        self.assertEqual(fade.visibility(events,'a','guidance','guidance',1.36),1)
        self.assertFalse(events['tables'])

    def test_new_revision_clears_old_fade_without_engine_mutation(self):
        owner=self.owner()
        engine=SimpleNamespace(revision=2,started=0)
        old=fade.begin_frame(owner,engine)
        old['tables']['a']=1
        engine.revision=3
        fresh=fade.begin_frame(owner,engine)
        self.assertFalse(fresh['tables'])
        self.assertIsNot(fresh,old)
        self.assertEqual(engine.revision,3)

    def test_runtime_and_shader_patch_preserve_local_edits(self):
        for path,patcher,pairs in (
            ('td_builders/motion_design.py',update.patch_runtime,
             ((update.RUNTIME_LOOP,update.NEW_LOOP),(update.RUNTIME_UPDATE,update.NEW_UPDATE),
              (update.RUNTIME_UPLOAD,update.NEW_UPLOAD))),
            ('td_builders/motion_design.frag',update.patch_shader,
             ((update.SHADER_STATE,update.NEW_STATE),(update.SHADER_FLOOR,update.NEW_FLOOR),
              (update.SHADER_TABLE,update.NEW_TABLE)))):
            old=Path(path).read_text(encoding='utf-8')
            for original,new in pairs: old=old.replace(new,original)
            old+='\n# local note\n' if path.endswith('.py') else '\n// local note\n'
            new=patcher(old)
            recovered=new
            for original,installed in pairs: recovered=recovered.replace(installed,original)
            self.assertEqual(recovered,old)
            self.assertEqual(patcher(new),new)
            with self.assertRaises(RuntimeError): patcher(old+pairs[0][0])

    def test_python39_compatible(self):
        for path in ('td_builders/motion_redisplay.py','td_builders/update_motion_redisplay.py'):
            ast.parse(Path(path).read_text(encoding='utf-8'),feature_version=(3,9))

    def installation_fixture(self):
        info=dict(old='old shader',new='new shader',mask='mask',
                  runtime_old='old runtime',runtime_new='new runtime')
        pixel=SimpleNamespace(text=info['old'])
        runtime=SimpleNamespace(text=info['runtime_old'],module=SimpleNamespace(td_tick=lambda:None))
        state=SimpleNamespace(cook=lambda **kwargs:None,errors=lambda:'')
        nodes=dict(motion_pixel=pixel,motion_runtime=runtime,state=state)
        storage=dict(motion_engine=SimpleNamespace(revision=2),motion_osc_reader=object(),
                     older_backup='preserve')
        comp=SimpleNamespace(op=lambda name:nodes.get(name,object()),
                             fetch=lambda key,default=None:storage.get(key,default),
                             store=lambda key,value:storage.update({key:value}),
                             unstore=lambda key:storage.pop(key,None))
        probe=SimpleNamespace(fetch=lambda key,default=None:info,
                              op=lambda name:SimpleNamespace(text=info[name.removesuffix('_pixel')]),
                              destroy=lambda:None)
        return pixel,runtime,storage,comp,probe

    def test_failed_gpu_proof_changes_neither_runtime_nor_shader(self):
        pixel,runtime,storage,comp,probe=self.installation_fixture()
        with patch.object(update.transaction.shadow,'_validate',return_value=comp), \
                patch.object(update,'gpu_check',side_effect=RuntimeError('GPU failed')):
            with self.assertRaisesRegex(RuntimeError,'GPU failed'): update.install(lambda path:probe)
        self.assertEqual((pixel.text,runtime.text),('old shader','old runtime'))
        self.assertNotIn(update.BACKUP,storage)

    def test_compile_failure_restores_both_dats(self):
        pixel,runtime,storage,comp,probe=self.installation_fixture()
        with patch.object(update.transaction.shadow,'_validate',return_value=comp), \
                patch.object(update,'gpu_check',return_value=[]), \
                patch.object(update.routing,'digest',side_effect=RuntimeError('compile failed')):
            with self.assertRaisesRegex(RuntimeError,'compile failed'): update.install(lambda path:probe)
        self.assertEqual((pixel.text,runtime.text),('old shader','old runtime'))
        self.assertNotIn(update.BACKUP,storage)
        self.assertEqual(storage['older_backup'],'preserve')

    def test_success_and_rollback_preserve_engine_and_older_backup(self):
        pixel,runtime,storage,comp,probe=self.installation_fixture()
        before=storage.copy()
        with patch.object(update.transaction.shadow,'_validate',return_value=comp), \
                patch.object(update,'gpu_check',return_value=[]),patch.object(update.routing,'digest'):
            self.assertTrue(update.install(lambda path:probe)['passed'])
            self.assertEqual((pixel.text,runtime.text),('new shader','new runtime'))
            self.assertTrue(update.rollback(None)['restored'])
        self.assertEqual((pixel.text,runtime.text),('old shader','old runtime'))
        self.assertEqual(storage,before)
