"""Textport: verify the active test; restore the disabled baseline on pixel failure."""
import builtins
import importlib
import json
import sys

REPO='/Users/Johannes/dev/Promotion_Prototypen/AISI'


def symbol(name):
    return (globals().get(name) or getattr(builtins,name,None)
            or getattr(sys.modules.get('__main__'),name,None))


if callable(symbol('op')) and (globals().get('__spec__') is None
        or globals().get('p')==REPO+'/td_builders/check_motion_output_simulation_test.py'):
    if REPO not in sys.path:
        sys.path.insert(0,REPO)
    from td_builders import motion_output_simulation_test as output_simulation
    importlib.reload(output_simulation)
    try:
        result=output_simulation.verify(symbol('op'))
    except Exception as error:
        result={'passed':False,'failure':str(error),'saved':False}
    print(json.dumps(result,ensure_ascii=False,indent=2))
