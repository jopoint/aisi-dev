"""Dashed rounded target border on both surfaces; original feedback footprint retained."""
from td_builders import build_motion_output_routing as routing
from td_builders import update_motion_feedback_brightness as transaction
from td_builders import update_motion_alignment_guides as alignment

PROBE = '/project1/comp_aisi_motion_target_dashes_check'
SESSION = 'motion_target_dashes_probe'
BACKUP = 'motion_target_dashes_backup'
WIDTH_CM = 5.0
DASH_COUNT = 14
DUTY = .74
FILL = '            float targetFill=targetMask*(1.0-targetLines);'
NEW_FILL = '            float targetFill=targetDashes(rotate2(p-target.xy,-target.z),halfSize,shape.z);'
LAYER = '            layer=white(success?0.0:targetMask);'
NEW_LAYER = '            layer=white(success?0.0:targetFill);'
HELPER = '''float targetDashArc(vec2 local, vec2 halfSize, float corner) {
    // Exact arclength on the inset rounded centerline; pattern stays target-local.
    float radius=max(corner-2.5,.001);
    vec2 straight=halfSize-vec2(corner);
    vec2 p=abs(local), q=p-straight;
    float arc=PI*.5*radius;
    float quarter=straight.x+straight.y+arc;
    float s;
    if(q.x>0.0 && q.y>0.0)
        s=straight.x+radius*atan(q.x,q.y);
    else if(q.x>0.0)
        s=straight.x+arc+straight.y-min(p.y,straight.y);
    else
        s=min(p.x,straight.x);
    if(local.y<=0.0) return local.x>=0.0?s:4.0*quarter-s;
    return local.x>=0.0?2.0*quarter-s:2.0*quarter+s;
}
float targetDashes(vec2 local, vec2 halfSize, float corner) {
    float d=roundedRect(local,halfSize,corner);
    // A 5-cm band wholly inside the unchanged outer footprint.
    float band=max(0.0,coverage(d)-coverage(d+5.0));
    if(band<=0.0) return 0.0;
    float radius=max(corner-2.5,.001);
    vec2 straight=halfSize-vec2(corner);
    float perimeter=4.0*(straight.x+straight.y)+2.0*PI*radius;
    float pitch=perimeter/14.0, dash=pitch*.74;
    float position=targetDashArc(local,halfSize,corner);
    float wrapped=mod(position-dash*.5+pitch*.5,pitch)-pitch*.5;
    return band*coverage(abs(wrapped)-dash*.5);
}
'''


def patch_shader(text):
    routing.require('targetDashes(' not in text and text.count(FILL)==1 and text.count(LAYER)==1
                    and text.count('float targetEdge(')==1 and 'float targetLines=0.0;' in text,
                    'Aktiver Zielshader ist nicht der bestätigte solide Stand; nichts überschrieben.')
    return (text.replace('float targetEdge(',HELPER+'float targetEdge(',1)
                .replace(FILL,NEW_FILL,1).replace(LAYER,NEW_LAYER,1))


def prepare(resolve):
    result=transaction.prepare(resolve,probe_path=PROBE,session=SESSION,backup=BACKUP,patcher=patch_shader)
    probe=resolve(PROBE)
    info=dict(probe.fetch(SESSION))
    info['mask']=info['new'].split('void main() {')[0]+'''void main() {
    vec2 p=vec2(vUV.x,1.0-vUV.y)*500.0;
    vec4 target=datum(1,0),shape=datum(4,0);
    vec2 local=rotate2(p-target.xy,-target.z);
    float d=roundedRect(local,shape.xy*.5,shape.z);
    float outer=coverage(d);
    float band=max(0.0,outer-coverage(d+5.0));
    fragColor=TDOutputSwizzle(vec4(outer,targetDashes(local,shape.xy*.5,shape.z),band,1));
}
'''
    probe.op('mask_pixel').text=info['mask']
    # Identical original feedback/navigation on a transparent target background.
    reference=info['old'].replace(FILL,'            float targetFill=0.0;',1).replace(LAYER,'            layer=vec4(0);',1)
    kinds={name:routing.symbol(name) for name in ('textDAT','glslTOP')}
    pixel=probe.create(kinds['textDAT'],'feedback_reference_pixel');pixel.text=reference
    render=probe.create(kinds['glslTOP'],'feedback_reference')
    render.inputConnectors[0].connect(probe.op('state'))
    render.par.pixeldat=pixel.path
    render.par.outputresolution='custom'
    render.par.resolutionw=render.par.resolutionh=1000
    uniform,val=getattr(render.par,'vec0name',None),getattr(render.par,'vec0valuex',None)
    if uniform is None or val is None:uniform,val=getattr(render.par,'uniname0',None),getattr(render.par,'value0x',None)
    routing.require(uniform is not None and val is not None,'Surface-Uniform fehlt.')
    uniform.val,val.val='uSurface',1
    info['feedback_reference']=reference
    probe.store(SESSION,info)
    result.update(border_width_cm=WIDTH_CM,dashes=DASH_COUNT,dash_fraction=DUTY,
                  surfaces=['floor','tabletop'],outer_footprint_changed=False,
                  feedback_clip='unchanged full target footprint',saved=False)
    return result


def gpu_check(probe):
    import numpy as np
    from td_builders.motion_design import WIDTH,DEPTH,CORNER
    info=probe.fetch(SESSION)
    routing.require(probe.op('feedback_reference_pixel').text==info['feedback_reference'],'Feedback-Prüfshader lokal verändert.')
    checks=[]
    def render(rotation,overlap=False,feedback=False,phase=0,age=0,reveal=4,visibility=1):
        data=np.zeros((6,6,4),np.float32)
        data[0,0]=(250,250,0,1) if overlap else (100,100,0,1)
        data[0,1]=(275,250,rotation,1) if overlap else (300,300,rotation,1)
        data[0,2]=(0,int(feedback),.5,phase)
        data[0,3]=(0,0,age,1)
        data[0,4]=(WIDTH,DEPTH,CORNER,0)
        data[0,5]=(visibility,1,0,0)
        data[5,0]=(4,reveal,1,1)
        probe.store('data',data);probe.op('state').cook(force=True)
        images={}
        for name in ('old_floor','new_floor','old_tabletop','new_tabletop','mask_tabletop','feedback_reference'):
            node=probe.op(name);routing.digest(node)
            images[name]=node.numpyArray(delayed=False).copy()
            routing.require(np.isfinite(images[name]).all(),'Nichtendliche GPU-Ausgabe.')
        return images
    for rotation in (0,33,90):
        images=render(rotation)
        outer,dashes,band=[images['mask_tabletop'][:,:,i] for i in range(3)]
        outside=outer<=0;interior=(outer>.999)&(band<=1e-6);edge=dashes==1;gaps=(band>.999)&(dashes<1e-6)
        routing.require(interior.sum()>1000 and edge.any() and gaps.any(),'Kontur hat kein offenes Inneres oder keine Strichlücken.')
        routing.require(np.count_nonzero(dashes[outside])==0,'Kontur überschreitet Original-Footprint.')
        routing.require(float(images['new_floor'][interior,3].max())<1e-6,'Zielinneres weiterhin gefüllt.')
        routing.require(float(images['new_floor'][gaps,3].max())<1e-6,'Strichlücken auf Boden nicht transparent.')
        alignment.check_floor(images['old_floor'][edge],images['new_floor'][edge])
        for surface in ('floor','tabletop'):
            alignment.check_floor(images['old_'+surface][outside],images['new_'+surface][outside])
        tabletop=render(rotation,overlap=True)
        tabletop_edge=tabletop['mask_tabletop'][:,:,1]==1
        alignment.check_floor(tabletop['old_tabletop'][tabletop_edge],tabletop['new_tabletop'][tabletop_edge])
        opened=(tabletop['old_tabletop'][:,:,3]>.99)&(tabletop['new_tabletop'][:,:,3]<.01)
        routing.require(int(opened.sum())>100,'Tabletop-Ziel weiterhin solide gefüllt.')
        overlap=render(rotation,overlap=True,feedback=True)
        full=overlap['mask_tabletop'][:,:,0];stripe=overlap['mask_tabletop'][:,:,2]
        inside=(full>.999)&(stripe<1e-6)
        alignment.check_floor(overlap['feedback_reference'][inside],overlap['new_tabletop'][inside])
        green=overlap['new_tabletop'][:,:,1]-np.maximum(overlap['new_tabletop'][:,:,0],overlap['new_tabletop'][:,:,2])
        routing.require(float(green.max())>.1 and float(green[full<=0].max())<=1e-6,'Feedback fehlt oder überschreitet den Ziel-Footprint.')
        checks.append(dict(rotation_deg=rotation,open_center=True,dash_gaps_transparent=True,
                           footprint_preserved=True,tabletop_open_pixels=int(opened.sum()),feedback_preserved=True))
    for age in (0,.09,.18,1):
        images=render(33,overlap=True,phase=1,age=age)
        alignment.check_floor(images['old_tabletop'],images['new_tabletop'])
    checks.append(dict(case='success_unchanged',passed=True))
    full=render(33,overlap=True,feedback=True)
    half=render(33,overlap=True,feedback=True,visibility=.5)
    for surface in ('floor','tabletop'):
        routing.require(float(np.max(np.abs(full['new_'+surface]*.5-half['new_'+surface])))<=1e-6,'Wiedereinblendung verändert.')
    render(33,overlap=True,reveal=1.5)
    checks.append(dict(case='reveal_and_redisplay_preserved',passed=True))
    return checks


def install(resolve):
    return transaction.install(resolve,probe_path=PROBE,session=SESSION,backup=BACKUP,check=gpu_check)


def rollback(resolve):
    return transaction.rollback(resolve,backup=BACKUP)
