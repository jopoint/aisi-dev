"""Build isolated generated-layout chair rendering; output insertion is separate."""
import builtins
import json
from pathlib import Path
import sys

NAME='comp_aisi_motion_layout_chairs'
PATH='/project1/'+NAME
MARK='motion_generated_layout_chairs'
REPO=Path('C:/dev/Promotion_Prototypen/AISI')


def build(resolve,symbols):
    from td_builders import build_motion_output_routing as routing
    root=resolve('/project1')
    routing.require(root is not None and root.op(NAME) is None,
                    'project1 fehlt oder Chair-Komponente existiert; nichts überschrieben.')
    motion=resolve(routing.MOTION[:-1])
    routing.require(motion is not None and motion.par.Useosc.eval(),'OSC-Motion-Komponente fehlt.')
    comp=root.create(symbols['containerCOMP'],NAME)
    try:
        comp.nodeX,comp.nodeY=2100,-1400
        runtime=comp.create(symbols['textDAT'],'chair_runtime')
        runtime.text=('import sys\n'
            + 'sys.path.insert(0, %r) if %r not in sys.path else None\n'
            % (str(REPO/'src'),str(REPO/'src'))
            + 'sys.path.insert(0, %r) if %r not in sys.path else None\n'
            % (str(REPO),str(REPO))
            + (REPO/'td_builders/motion_chairs.py').read_text(encoding='utf-8'))
        callback=comp.create(symbols['textDAT'],'chair_callbacks')
        callback.text="""def onCook(scriptOp):
    tick=scriptOp.par.Tick.eval()
    scriptOp.copyNumpyArray(scriptOp.parent().op('chair_runtime').module.td_tick(scriptOp.parent()))
"""
        state=comp.create(symbols['scriptTOP'],'chair_state')
        state.appendCustomPage('Runtime').appendFloat('Tick')[0].expr='absTime.seconds'
        state.par.callbacks=callback.path
        fmt=getattr(state.par,'format',None)
        if fmt is None: fmt=getattr(state.par,'pixelformat',None)
        routing.require(fmt is not None,'Script-TOP-Pixelformat fehlt.')
        fmt.val='rgba32float'
        source=comp.create(symbols['selectTOP'],'motion_state')
        source.par.top=routing.MOTION+'state'
        pixel=comp.create(symbols['textDAT'],'chair_pixel')
        pixel.text=(REPO/'td_builders/motion_chairs.frag').read_text(encoding='utf-8')
        render=comp.create(symbols['glslTOP'],'render_chairs')
        render.inputConnectors[0].connect(source)
        render.inputConnectors[1].connect(state)
        render.par.pixeldat=pixel.path
        render.par.outputresolution='custom'
        render.par.resolutionw=2000
        render.par.resolutionh=2000
        out=comp.create(symbols['outTOP'],'out_chairs')
        out.inputConnectors[0].connect(render)
        routing.digest(out)
        comp.store(MARK,True)
        comp.store('chair_owned',{n.path:routing.signature(n) for n in [comp]+list(comp.children)})
        return {'component':comp.path,'chairs':out.path,'compiled':True,
                'production_outputs_changed':False,'saved':False,
                'status':'isolated chairs built; sender and output test still to connect'}
    except Exception:
        comp.destroy()
        raise


def symbol(name):
    return globals().get(name) or getattr(builtins,name,None) or getattr(sys.modules.get('__main__'),name,None)


if callable(symbol('op')) and (globals().get('__spec__') is None or globals().get('p')==str(REPO/'td_builders/build_motion_layout_chairs.py')):
    kinds=('containerCOMP','textDAT','scriptTOP','selectTOP','glslTOP','outTOP')
    print(json.dumps(build(symbol('op'),{k:symbol(k) for k in kinds}),ensure_ascii=False,indent=2))
