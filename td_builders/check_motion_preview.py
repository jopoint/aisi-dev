"""Textport diagnostics, cooking only the new isolated Motion preview."""
import builtins
import json
import sys


def check(resolve):
    root = resolve('/project1/comp_aisi_motion_v1_5')
    if root is None:
        raise RuntimeError('Motion-Preview fehlt; zuerst build_motion_preview.py ausführen.')
    result = {'component': root.path, 'nodes': {}, 'saved': False}
    for name in ('state','render_floor','render_tabletop','render_preview',
                 'out_floor','out_tabletop'):
        node = root.op(name)
        if node is None:
            result['nodes'][name] = {'missing': True}
            continue
        node.cook(force=True)  # Never touches an existing render/projector branch.
        errors = node.errors()
        result['nodes'][name] = {'errors': str(errors) if errors else '',
                               'size': [node.width,node.height]}
    state = root.op('state')
    if state is not None and not state.errors():
        array = state.numpyArray(delayed=False)
        result['state_shape'] = list(array.shape)
        result['source'] = array[0,0].tolist()
        result['target'] = array[0,1].tolist()
        result['navigation_contact_halo_phase'] = array[0,2].tolist()
    result['passed'] = (all(not v.get('missing') and not v.get('errors')
                           for v in result['nodes'].values())
                        and result.get('state_shape') == [6,6,4])
    result['visual_acceptance'] = 'pending manual preview'
    live=root.fetch('motion_live_status',None)
    if live is not None:
        result['live_stream']=live
    return result


def symbol(name):
    return (globals().get(name) or getattr(builtins,name,None)
            or getattr(sys.modules.get('__main__'),name,None))


if callable(symbol('op')):
    print(json.dumps(check(symbol('op')),ensure_ascii=False,indent=2))
elif __name__ == '__main__':
    raise RuntimeError('Im TouchDesigner-Textport ausführen.')
