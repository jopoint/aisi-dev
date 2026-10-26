"""Textport: prepare the disabled simulation branch; activate in a later frame."""
import builtins
import importlib
import json
import sys

REPO='C:/dev/Promotion_Prototypen/AISI'


def symbol(name):
    return (globals().get(name) or getattr(builtins,name,None)
            or getattr(sys.modules.get('__main__'),name,None))


if callable(symbol('op')) and (globals().get('__spec__') is None
        or globals().get('p')==REPO+'/td_builders/start_motion_output_simulation_test.py'):
    if REPO not in sys.path:
        sys.path.insert(0,REPO)
    from td_builders import motion_output_simulation_test as output_simulation
    importlib.reload(output_simulation)
    print(json.dumps(output_simulation.start(symbol('op'),{k:symbol(k) for k in ('selectTOP','switchTOP','outTOP')}),
                     ensure_ascii=False,indent=2))
