"""Textport: replace owned fixture sender with explicitly activated layouts.

Stops the registered simulation output test first, builds/reuses isolated
chairs, replaces only the owned sender, then prepares the OFF output branch.
Activate in a later Textport entry, exactly as for the existing GPU test.
"""
import builtins
import importlib
import json
import sys


def prepare(resolve,symbols):
    from td_builders import motion_output_simulation_test as output_test
    from td_builders import start_motion_simulation as launcher
    from td_builders import build_motion_layout_chairs as chairs
    output_test=importlib.reload(output_test)
    launcher=importlib.reload(launcher)
    routing=output_test.routing
    routing.require(resolve(routing.PATH) is not None,'Produktives Motion-Routing fehlt.')
    existing=resolve(chairs.PATH)
    if existing is not None:
        expected=existing.fetch('chair_owned',None)
        actual={n.path:routing.signature(n) for n in [existing]+list(existing.children)}
        routing.require(existing.fetch(chairs.MARK,False) and expected==actual,
                        'Chair-Komponente lokal verändert; nichts überschrieben.')
    previous=output_test.stop(resolve)
    chair_report=chairs.build(resolve,symbols) if existing is None else {'component':existing.path,'reused':True}
    sender=launcher.start(resolve,table_count=5,generated_layouts=True)
    report=output_test.start(resolve,symbols)
    report.update({'previous_test_stopped':previous['simulation_test_stopped'],
                   'chairs':chair_report,'sender':sender,'layout_generation':'explicit activation only',
                   'next':'activate in a later Textport entry; then activate a proposal in the Room Editor'})
    return report


def symbol(name):
    return globals().get(name) or getattr(builtins,name,None) or getattr(sys.modules.get('__main__'),name,None)


if callable(symbol('op')) and (globals().get('__spec__') is None or str(globals().get('p','')).endswith('/prepare_motion_layout_simulation.py')):
    kinds=('containerCOMP','textDAT','scriptTOP','selectTOP','glslTOP','switchTOP','outTOP')
    print(json.dumps(prepare(symbol('op'),{k:symbol(k) for k in kinds}),ensure_ascii=False,indent=2))
