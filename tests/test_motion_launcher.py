"""Safe count switches affect only the explicitly owned simulator process."""
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock,patch
import importlib

from td_builders import start_motion_simulation as launcher


class MotionLauncherTests(unittest.TestCase):
    def test_import_inside_td_does_not_launch_default_three_table_sender(self):
        with patch.object(launcher.builtins,'op',Mock(),create=True),\
                patch.object(launcher.subprocess,'Popen') as popen:
            importlib.reload(launcher)
        popen.assert_not_called()

    def test_count_switch_restarts_only_owned_process_and_passes_requested_count(self):
        with TemporaryDirectory() as folder:
            root=Path(folder)
            python=root/'.venv/bin/python'
            python.parent.mkdir(parents=True)
            python.touch()
            old=Mock(pid=10,args=[str(python),'-m','aisi.app.motion_preview_sim'])
            old.poll.return_value=None
            old.wait.return_value=0
            saved={'motion_sim_process':old}
            comp=SimpleNamespace(par=SimpleNamespace(Useosc=True),
                fetch=lambda k,d:saved.get(k,d),store=lambda k,v:saved.update({k:v}),
                storeStartupValue=lambda *args:None)
            new=Mock(pid=11)
            def local_path(value):
                return root/'runtime' if str(value)=='/private/tmp/aisi-motion-sim' else Path(value)
            with patch.object(launcher,'REPO',root),patch.object(launcher,'Path',side_effect=local_path),\
                    patch.object(launcher.subprocess,'Popen',return_value=new) as popen:
                report=launcher.start(lambda path:comp,table_count=3)
            old.terminate.assert_called_once_with()
            old.wait.assert_called_once_with(timeout=3)
            command=popen.call_args.args[0]
            self.assertEqual(command[command.index('--tables')+1],'3')
            self.assertEqual(report['restarted_from_pid'],10)
            self.assertIs(saved['motion_sim_process'],new)

    def test_unrelated_process_is_never_terminated(self):
        old=Mock(pid=10,args=['/usr/bin/python3','-m','another_app'])
        old.poll.return_value=None
        comp=SimpleNamespace(par=SimpleNamespace(Useosc=True),
            fetch=lambda k,d:old if k=='motion_sim_process' else d)
        with patch.object(launcher.subprocess,'Popen') as popen:
            with self.assertRaisesRegex(RuntimeError,'nichts beendet'):
                launcher.start(lambda path:comp,3)
        old.terminate.assert_not_called()
        popen.assert_not_called()

    def test_same_count_keeps_running_instance(self):
        old=Mock(pid=10)
        old.poll.return_value=None
        saved={'motion_sim_process':old,'motion_sim_table_count':3}
        comp=SimpleNamespace(par=SimpleNamespace(Useosc=True),fetch=lambda k,d:saved.get(k,d))
        with patch.object(launcher.subprocess,'Popen') as popen:
            report=launcher.start(lambda path:comp,3)
        self.assertEqual(report['status'],'already running')
        old.terminate.assert_not_called()
        popen.assert_not_called()

    def test_generated_layout_mode_restarts_owned_fixture_sender_and_sets_cli_flag(self):
        with TemporaryDirectory() as folder:
            root=Path(folder); python=root/'.venv/bin/python'
            python.parent.mkdir(parents=True); python.touch()
            old=Mock(pid=10,args=[str(python),'-m','aisi.app.motion_preview_sim'])
            old.poll.return_value=None
            saved={'motion_sim_process':old,'motion_sim_table_count':5}
            comp=SimpleNamespace(par=SimpleNamespace(Useosc=True),
                fetch=lambda k,d:saved.get(k,d),store=lambda k,v:saved.update({k:v}),
                storeStartupValue=lambda *a:None)
            def local_path(value):
                return root/'runtime' if str(value)=='/private/tmp/aisi-motion-sim' else Path(value)
            with patch.object(launcher,'REPO',root),patch.object(launcher,'Path',side_effect=local_path),\
                    patch.object(launcher.subprocess,'Popen',return_value=Mock(pid=11)) as popen:
                launcher.start(lambda path:comp,5,generated_layouts=True)
            self.assertIn('--generated-layouts',popen.call_args.args[0])
            old.terminate.assert_called_once()
            self.assertTrue(saved['motion_sim_generated_layouts'])
