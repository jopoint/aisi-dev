"""Diagnose the isolated sender/receiver; no routing/parameter changes."""
import builtins
import json
import sys


def inspect(resolve):
    motion=resolve('/project1/comp_aisi_motion_v1_5')
    if motion is None:
        raise RuntimeError('Motion-Komponente fehlt.')
    before=motion.fetch('motion_live_status',None)
    state=motion.op('state'); state.cook(force=True)
    result={'production_routing_changed':False,'parameters_changed':False,'saved':False,
            'live_before_cook':before,'live_after_cook':motion.fetch('motion_live_status',None),
            'state_errors':str(state.errors() or ''),'receiver':{},'raw_metadata':{}}
    receiver=resolve('/project1/comp_io/oscin1')
    if receiver is not None:
        result['receiver']={name:str(getattr(receiver.par,name).eval())
                            for name in ('active','port','protocol')}
    raw=motion.op(str(motion.par.Oscpath.eval()))
    if raw is not None:
        for name in ('session','frame','revision','count'):
            channel=raw['aisi_motion/'+name]
            result['raw_metadata'][name]=channel.eval() if channel is not None else None
    process=motion.fetch('motion_sim_process',None)
    result['owned_sender']={'handle_available':process is not None,
                           'tables':motion.fetch('motion_sim_table_count',None)}
    if process is not None:
        result['owned_sender'].update({'pid':process.pid,'exit_code':process.poll()})
    return result


def symbol(name):
    return (globals().get(name) or getattr(builtins,name,None)
            or getattr(sys.modules.get('__main__'),name,None))


if globals().get('__spec__') is None and callable(symbol('op')):
    print(json.dumps(inspect(symbol('op')),ensure_ascii=False,indent=2))
