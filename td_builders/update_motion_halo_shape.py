"""Update only the owned dynamic Motion shader, keeping all state/history."""
import builtins
import json
from pathlib import Path
import sys

REPO=Path('/Users/Johannes/dev/Promotion_Prototypen/AISI')
PATH='/project1/comp_aisi_motion_v1_5'
OLD_BLOCK='''                float h=state.z, asymmetry=(1.0-h)*(1.0-h);
                float radius=mix(35.0,81.4,smoothstep(0.0,1.0,h));
                vec2 q=rotate2(p-source.xy,-angle);
                float g1=blurredEllipse(q,vec2(asymmetry*24.0,sin(t*1.8)*1.4),
                    radius*vec2(1.0+asymmetry*.22+.04*sin(t*1.6),1.0-asymmetry*.20+.035*sin(t*1.3+.7)));
                float g2=ellipse(q,vec2(asymmetry*19.0,0),
                    radius*vec2(1.0,1.0-asymmetry*.22+.035*sin(t*1.4)))*.8;
                float ga=(g2+g1*(1.0-g2))*smoothstep(0.0,1.0,state.y);'''
NEW_BLOCK='''                float ga=feedbackHalo(p-source.xy,angle,state.z,t,distance)
                    *smoothstep(0.0,1.0,state.y);'''


def patch_shader(old,reference):
    start=reference.index('float feedbackHalo(')
    helper=reference[start:reference.index('float targetEdge(',start)]
    if helper in old and old.count(NEW_BLOCK)==1:
        return old
    if old.count(OLD_BLOCK)!=1 or old.count('float targetEdge(')!=1 or 'feedbackHalo(' in old:
        raise RuntimeError('Halo-Code lokal abweichend; nichts überschrieben.')
    return old.replace('float targetEdge(',helper+'float targetEdge(',1).replace(OLD_BLOCK,NEW_BLOCK,1)


def update(resolve,repo=REPO):
    comp=resolve(PATH)
    pixel=comp.op('motion_pixel') if comp is not None else None
    if pixel is None or comp.op('state') is None:
        raise RuntimeError('Eigene Motion-Komponente fehlt; nichts geändert.')
    old=pixel.text
    new=(repo/'td_builders/motion_design.frag').read_text(encoding='utf-8')
    marker='// AISI v1.5. Shared world-space shader, before any projector warp.'
    if not old.startswith(marker) or not new.startswith(marker):
        raise RuntimeError('Erwarteter eigener Shader fehlt; nichts geändert.')
    new=patch_shader(old,new)  # Preserve all other local shader edits.
    try:
        pixel.text=new
        for name in ('render_floor','render_tabletop','render_preview'):
            node=comp.op(name)
            if node is None:
                raise RuntimeError('Motion-Renderer fehlt: '+name)
            node.cook(force=True)
            if node.errors():
                raise RuntimeError(node.path+': '+str(node.errors()))
        return {'component':comp.path,'shader_updated':old!=new,
                'round_within_cm':8,'directional_from_cm':29,
                'main_engine_reset':False,'mask_nodes_changed':False,
                'production_outputs_changed':False,'saved':False,
                'status':'compiled; manual target-crossing acceptance pending'}
    except Exception:
        pixel.text=old
        raise


def symbol(name):
    return (globals().get(name) or getattr(builtins,name,None)
            or getattr(sys.modules.get('__main__'),name,None))


if globals().get('__spec__') is None and callable(symbol('op')):
    print(json.dumps(update(symbol('op')),ensure_ascii=False,indent=2))
