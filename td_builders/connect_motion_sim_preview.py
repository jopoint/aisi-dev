"""Update only the owned Motion COMP for Room Editor OSC preview; no receiver changes."""
import builtins
import json
from pathlib import Path
import sys

REPO=Path('C:/dev/Promotion_Prototypen/AISI')


def connect(resolve):
    comp=resolve('/project1/comp_aisi_motion_v1_5')
    raw=resolve('/project1/comp_io/null_osc_raw')
    if comp is None or raw is None:
        raise RuntimeError('Motion-COMP oder bestehender OSC-Eingang fehlt.')
    runtime=comp.op('motion_runtime')
    pixel=comp.op('motion_pixel')
    if runtime is None or pixel is None:
        raise RuntimeError('Motion-Code-DATs fehlen; nichts verändert.')
    for path in (str(REPO),str(REPO/'src')):
        if path not in sys.path:
            sys.path.insert(0,path)
    from td_builders.motion_geometry_compat import load_geometry
    load_geometry().get_table_geometry('rect')
    old_runtime,old_pixel=runtime.text,pixel.text
    backup=[(p,p.val,p.expr,p.mode) for p in comp.customPars]
    new_page=None
    try:
        if getattr(comp.par,'Useosc',None) is None:
            new_page=comp.appendCustomPage('Motion Live')
            new_page.appendToggle('Useosc',label='Room-Editor-OSC verwenden')[0].val=False
            new_page.appendStr('Oscpath',label='Bestehender OSC-Eingang')[0].val=raw.path
            new_page.appendFloat('Streamtimeout',label='Zeitlimit ohne neue Frames (s)')[0].val=.5
        runtime.text=('import sys\n'
            +'sys.path.insert(0,%r) if %r not in sys.path else None\n' % (str(REPO),str(REPO))
            +'sys.path.insert(0,%r) if %r not in sys.path else None\n' % (str(REPO/'src'),str(REPO/'src'))
            +(REPO/'td_builders/motion_design.py').read_text(encoding='utf-8'))
        pixel.text=(REPO/'td_builders/motion_design.frag').read_text(encoding='utf-8')
        comp.par.Demo=False
        comp.par.Usedat=False
        comp.par.Useosc=True
        # Drop only this component's old demo/stream history.
        comp.unstore('motion_engine')
        comp.unstore('motion_osc_reader')
        return {'component':comp.path,'source':raw.path,'prefix':'/aisi_motion/',
                'timeout_s':comp.par.Streamtimeout.eval(),
                'projector_connections_added':False,'receiver_settings_changed':False,
                'saved':False,'status':'waiting for advancing simulation frames'}
    except Exception:
        runtime.text,pixel.text=old_runtime,old_pixel
        for p,val,expr,mode in backup:
            p.val=val
            p.expr=expr or ''
            p.mode=mode
        if new_page is not None:
            new_page.destroy()
        raise


def symbol(name):
    return (globals().get(name) or getattr(builtins,name,None)
            or getattr(sys.modules.get('__main__'),name,None))


if callable(symbol('op')):
    print(json.dumps(connect(symbol('op')),ensure_ascii=False,indent=2))
elif __name__=='__main__':
    raise RuntimeError('Im TD-Textport ausführen.')
