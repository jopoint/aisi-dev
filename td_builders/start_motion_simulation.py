"""Textport: launch the isolated Room Editor with repository Python, not TD Python."""
import builtins
import json
import os
from pathlib import Path
import subprocess
import sys

REPO=Path('/Users/Johannes/dev/Promotion_Prototypen/AISI')


def start(resolve,table_count=3,generated_layouts=False):
    if table_count not in (1,3,5):
        raise ValueError('Motion-Simulation unterstützt 1, 3 oder 5 Tische.')
    comp=resolve('/project1/comp_aisi_motion_v1_5')
    if comp is None or getattr(comp.par,'Useosc',None) is None:
        raise RuntimeError('Zuerst connect_motion_sim_preview.py ausführen.')
    python=REPO/'.venv/bin/python'
    restarted_from=None
    process=comp.fetch('motion_sim_process',None)
    if process is not None and process.poll() is None:
        current_count=comp.fetch('motion_sim_table_count',None)
        current_generated=comp.fetch('motion_sim_generated_layouts',False)
        if current_count==table_count and current_generated==generated_layouts:
            return {'status':'already running','pid':process.pid,'tables':table_count}
        command=process.args
        if not (isinstance(command,(list,tuple)) and len(command)>=3
                and list(command[1:3])==['-m','aisi.app.motion_preview_sim']
                and Path(command[0]).resolve()==python.resolve()):
            raise RuntimeError('Gespeicherter Prozess ist kein eindeutig zugeordneter Motion-Simulator; nichts beendet.')
        restarted_from=process.pid
        process.terminate()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            raise RuntimeError('Alter Motion-Simulator beendet sich noch nicht; keine zweite Instanz gestartet.')
    if not python.exists():
        raise RuntimeError('Repository-Python fehlt: '+str(python))
    folder=Path('/private/tmp/aisi-motion-sim')
    folder.mkdir(parents=True,exist_ok=True)
    log=folder/'sender.log'
    scene=folder/('live_scene.json' if table_count==1 else 'multitable_%d.json' % table_count)
    env=dict(os.environ)
    for name in ('PYTHONHOME','PYTHONEXECUTABLE','__PYVENV_LAUNCHER__'):
        env.pop(name,None)
    env['PYTHONPATH']=str(REPO/'src')
    env['PYTHONUNBUFFERED']='1'
    with log.open('a',encoding='utf-8') as output:
        command=[str(python),'-m','aisi.app.motion_preview_sim',
                 '--tables',str(table_count),'--scene',str(scene)]
        if generated_layouts:
            command.append('--generated-layouts')
        process=subprocess.Popen(command,
            cwd=str(REPO),env=env,stdin=subprocess.DEVNULL,
            stdout=output,stderr=subprocess.STDOUT)
    comp.store('motion_sim_process',process)
    comp.storeStartupValue('motion_sim_process',None)
    comp.store('motion_sim_table_count',table_count)
    comp.storeStartupValue('motion_sim_table_count',None)
    comp.store('motion_sim_generated_layouts',generated_layouts)
    comp.storeStartupValue('motion_sim_generated_layouts',False)
    return {'status':'launched; window and receiving status still to verify',
            'pid':process.pid,'log':str(log),
            'scene':str(scene),'tables':table_count,'generated_layouts':generated_layouts,'restarted_from_pid':restarted_from,
            'saved_td_project':False}


def symbol(name):
    return (globals().get(name) or getattr(builtins,name,None)
            or getattr(sys.modules.get('__main__'),name,None))


if globals().get('__spec__') is None and callable(symbol('op')):
    print(json.dumps(start(symbol('op')),ensure_ascii=False,indent=2))
elif __name__=='__main__':
    raise RuntimeError('Im TD-Textport ausführen.')
