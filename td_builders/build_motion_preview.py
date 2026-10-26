"""Textport builder: isolated Motion v1.5 preview; no downstream connections.

Refuses to overwrite an existing component. Never saves the project.
"""
import builtins
import json
import sys
from pathlib import Path

REPO = Path('/Users/Johannes/dev/Promotion_Prototypen/AISI')
NAME = 'comp_aisi_motion_v1_5'


def build(resolve, symbols, repo=REPO, name=NAME):
    root = resolve('/project1')
    if root is None or root.op(name) is not None:
        raise RuntimeError('project1 fehlt oder Motion-COMP existiert bereits; nichts geändert.')
    runtime = (repo / 'td_builders/motion_design.py').read_text(encoding='utf-8')
    shader = (repo / 'td_builders/motion_design.frag').read_text(encoding='utf-8')
    # Resolve canonical geometry before creating nodes; no environment installation.
    for path in (str(repo), str(repo / 'src')):
        if path not in sys.path:
            sys.path.insert(0, path)
    from td_builders.motion_geometry_compat import load_geometry
    load_geometry().get_table_geometry('rect')
    comp = root.create(symbols['containerCOMP'], name)
    try:
        comp.nodeX, comp.nodeY = 200, -1100
        page = comp.appendCustomPage('Motion Preview')
        for name, label, value in (
                ('Layoutrevision', 'Neuen Vorschlag aktivieren: Zähler erhöhen', 1),
                ('Resolution', 'Preview-Auflösung', 1000)):
            p = page.appendInt(name, label=label)[0]
            p.val = value
        for name, label, value in (
                ('Demo', 'Referenzbewegung ab Aktivierung', False),
                ('Valid', 'Tracking / Pose gültig', True),
                ('Usedat', 'Posen aus poses DAT verwenden', False)):
            page.appendToggle(name, label=label)[0].val = value
        for name, value in (('Sourcex',110),('Sourcey',180),('Sourcer',84),
                            ('Targetx',320),('Targety',330),('Targetr',122)):
            page.appendFloat(name, label=name+' (cm / Grad)')[0].val = value
        dat = comp.create(symbols['tableDAT'], 'poses')
        dat.appendRow(['table_id','source_x','source_y','source_r',
                       'target_x','target_y','target_r','valid','active'])
        dat.appendRow(['preview_table',110,180,84,320,330,122,1,1])
        runtime_dat = comp.create(symbols['textDAT'], 'motion_runtime')
        # Embed implementation and canonical-import path; no per-frame disk reads.
        runtime_dat.text = ('import sys\n'
            + 'sys.path.insert(0, %r) if %r not in sys.path else None\n'
            % (str(repo/'src'), str(repo/'src'))
            + 'sys.path.insert(0, %r) if %r not in sys.path else None\n'
            % (str(repo), str(repo)) + runtime)
        pixel = comp.create(symbols['textDAT'], 'motion_pixel')
        pixel.text = shader
        callbacks = comp.create(symbols['textDAT'], 'state_callbacks')
        callbacks.text = '''def onCook(scriptOp):
    tick = scriptOp.par.Tick.eval()  # Explicit TD time dependency, including older builds.
    scriptOp.copyNumpyArray(scriptOp.parent().op('motion_runtime').module.td_tick(scriptOp.parent()))

'''
        state = comp.create(symbols['scriptTOP'], 'state')
        state.appendCustomPage('Runtime').appendFloat('Tick')[0].expr = 'absTime.seconds'
        state.par.callbacks = callbacks.path
        # Use floating point storage: positions/time must never be clamped to 0..1.
        pixel_format = getattr(state.par, 'format', None)
        if pixel_format is None:
            pixel_format = getattr(state.par, 'pixelformat', None)
        if pixel_format is None:
            raise RuntimeError('Script TOP besitzt keinen Pixel-Format-Parameter.')
        pixel_format.val = 'rgba32float'
        for surface, name in enumerate(('floor','tabletop','preview')):
            render = comp.create(symbols['glslTOP'], 'render_'+name)
            render.inputConnectors[0].connect(state)
            render.par.pixeldat = pixel.path
            render.par.outputresolution = 'custom'
            render.par.resolutionw.expr = 'parent().par.Resolution'
            render.par.resolutionh.expr = 'parent().par.Resolution'
            uniform = getattr(render.par, 'vec0name', None)
            value = getattr(render.par, 'vec0valuex', None)
            if uniform is None or value is None:
                uniform = getattr(render.par, 'uniname0', None)
                value = getattr(render.par, 'value0x', None)
            if uniform is None or value is None:
                raise RuntimeError('GLSL TOP besitzt keine unterstützte Uniform-Schnittstelle.')
            uniform.val, value.val = 'uSurface', surface
            render.nodeX, render.nodeY = 220, -surface*180
            if surface < 2:
                out = comp.create(symbols['outTOP'], 'out_'+name)
                # Out TOP has no 'index' parameter. Older builds order outputs
                # alphabetically: out_floor precedes out_tabletop.
                order = getattr(out.par, 'connectorder', None)
                if order is not None:
                    order.val = surface
                out.inputConnectors[0].connect(render)
                out.nodeX, out.nodeY = 440, -surface*180
        comp.par.top = comp.op('render_preview').path
        comp.par.nodeview = 'opviewer'
        comp.par.opviewer = comp.op('render_preview').path
        comp.par.display = False
        comp.par.w, comp.par.h = 650, 650
        return {'component': comp.path, 'floor': comp.op('out_floor').path,
                'tabletop': comp.op('out_tabletop').path,
                'preview': comp.op('render_preview').path,
                'projector_connections_added': False, 'saved': False,
                'python': sys.version,
                'status': 'created; GPU compile and visual acceptance pending'}
    except Exception:
        comp.destroy()  # Roll back this new component only.
        raise


def td_symbol(name):
    return (globals().get(name) or getattr(builtins,name,None)
            or getattr(sys.modules.get('__main__'),name,None))


if callable(td_symbol('op')) and not globals().get('_AISI_MOTION_IMPORT_ONLY',False):
    kinds = ('containerCOMP','textDAT','tableDAT','scriptTOP','glslTOP','outTOP')
    symbols = {name:td_symbol(name) for name in kinds}
    if any(value is None for value in symbols.values()):
        raise RuntimeError('TouchDesigner-Operatortypen nicht verfügbar.')
    print(json.dumps(build(td_symbol('op'),symbols),ensure_ascii=False,indent=2))
elif __name__ == '__main__':
    raise RuntimeError('Im TouchDesigner-Textport ausführen.')
