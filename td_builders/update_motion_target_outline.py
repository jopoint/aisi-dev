"""Replace target fill by an inward rounded contour, with guarded GPU proof."""
from td_builders import update_motion_feedback_brightness as transaction
from td_builders import update_motion_alignment_guides as alignment
from td_builders import update_motion_redisplay as redisplay
from td_builders import build_motion_output_routing as routing

PROBE='/project1/comp_aisi_motion_target_outline_check'
SESSION='motion_target_outline_probe'
BACKUP='motion_target_outline_backup'
WIDTH_CM=8.0
HELPER='''float targetOutline(vec2 local, vec2 halfSize, float corner) {
    // The existing outer footprint stays exact. Both contours remain rounded.
    vec2 innerHalf=halfSize-vec2(8.0);
    float innerCorner=min(corner,min(innerHalf.x,innerHalf.y));
    float outer=coverage(roundedRect(local,halfSize,corner));
    float inner=coverage(roundedRect(local,innerHalf,innerCorner));
    return max(0.0,outer-inner);
}
'''
TARGET='            float targetMask=coverage(roundedRect(rotate2(p-target.xy,-target.z),halfSize,shape.z));'
NEW_TARGET=TARGET+'''
            float targetContour=targetOutline(rotate2(p-target.xy,-target.z),halfSize,shape.z);'''
OLD_GUIDES='''                // Knock out target template before drawing the source navigation circle.
                layer*=1.0-max(templateRing,targetBars);'''
NEW_GUIDES='''                // Target guides stay visible: cut out on white contour, white in its open interior.
                float targetGuides=max(templateRing,targetBars);
                layer*=1.0-targetGuides*targetContour;
                layer=over(white(targetGuides*(1.0-targetContour)),layer);'''
PAIRS=(('float targetEdge(',HELPER+'float targetEdge('),
       (TARGET,NEW_TARGET),
       ('            vec4 f=white(targetMask);','            vec4 f=white(targetContour);'),
       ('            layer=white(success?0.0:targetMask);','            layer=white(success?0.0:targetContour);'),
       (OLD_GUIDES,NEW_GUIDES))


def patch_shader(text):
    return redisplay._patch(text,PAIRS)


def prepare(resolve):
    result=transaction.prepare(resolve,probe_path=PROBE,session=SESSION,backup=BACKUP,patcher=patch_shader)
    probe=resolve(PROBE)
    info=dict(probe.fetch(SESSION))
    info['mask']=info['new'].split('void main() {')[0]+'''void main() {
    vec2 p=vec2(vUV.x,1.0-vUV.y)*500.0;
    vec4 target=datum(1,0),shape=datum(4,0);
    vec2 local=rotate2(p-target.xy,-target.z);
    float outer=coverage(roundedRect(local,shape.xy*.5,shape.z));
    float contour=targetOutline(local,shape.xy*.5,shape.z);
    fragColor=TDOutputSwizzle(vec4(outer,outer-contour,contour,1));
}
'''
    probe.op('mask_pixel').text=info['mask']
    probe.store(SESSION,info)
    result.update(contour_width_cm=WIDTH_CM,outer_footprint_changed=False,
                  rounded_inner_and_outer=True,surfaces=['floor','tabletop'],
                  feedback_clip='full original target footprint',target_guides='white in open interior')
    return result


def gpu_check(probe):
    import numpy as np
    from td_builders.motion_design import WIDTH,DEPTH,CORNER
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
        probe.store('data',data)
        probe.op('state').cook(force=True)
        images={}
        for name in ('old_floor','new_floor','old_tabletop','new_tabletop','mask_tabletop'):
            node=probe.op(name)
            routing.digest(node)
            images[name]=node.numpyArray(delayed=False).copy()
            routing.require(np.isfinite(images[name]).all(),'Nichtendliche GPU-Ausgabe.')
        return images
    for rotation in (0,33,90):
        images=render(rotation)
        mask=images['mask_tabletop']
        outer,contour=mask[:,:,0],mask[:,:,2]
        outside=outer<=0
        interior=(outer>=.999999)&(contour<=1e-6)
        edge=contour>=.999999
        routing.require(interior.sum()>1000 and edge.any(),'Keine dicke Kontur mit offenem Inneren.')
        routing.require(float(contour[outside].max())==0 and 0<float(contour.sum())<.5*float(outer.sum()),
                        'Kontur überschreitet ursprünglichen Umriss oder bleibt gefüllt.')
        routing.require(float(images['new_floor'][interior,3].max())<1e-6,
                        'Zielinneres auf Boden weiterhin weiß gefüllt.')
        alignment.check_floor(images['old_floor'][edge],images['new_floor'][edge])
        for surface in ('floor','tabletop'):
            alignment.check_floor(images['old_'+surface][outside],images['new_'+surface][outside])
        checks.append(dict(case='rounded_inward_outline',rotation_deg=rotation,
                           width_cm=WIDTH_CM,outer_footprint_preserved=True,floor_interior_open=True))
        overlapping=render(rotation,overlap=True)
        opened=(overlapping['old_tabletop'][:,:,3]>.99)&(overlapping['new_tabletop'][:,:,3]<.01)
        routing.require(int(opened.sum())>100,'Tabletop-Ziel weiterhin durchgehend gefüllt.')
        checks.append(dict(case='tabletop_fill_removed',rotation_deg=rotation,opened_pixels=int(opened.sum())))
    # Ring and target bars must remain visible in the now-open center.
    guides=render(0,overlap=True)['new_tabletop']
    def pixel(image,x): return image[image.shape[0]//2,int(x/500*image.shape[1])]
    routing.require(bool(np.all(pixel(guides,288)>.99)),'Zielring im offenen Inneren unsichtbar.')
    routing.require(float(pixel(guides,300)[3])>.5,'Zielstrich im offenen Inneren unsichtbar.')
    checks.append(dict(case='target_guides_visible_inside_outline',passed=True))
    # The feedback can still fill the semantic target footprint, not just its border.
    feedback=render(33,overlap=True,feedback=True)
    mask=feedback['mask_tabletop'][:,:,0]
    outside=mask<=0
    alignment.check_floor(feedback['old_tabletop'][outside],feedback['new_tabletop'][outside])
    green=feedback['new_tabletop'][:,:,1]-np.maximum(feedback['new_tabletop'][:,:,0],feedback['new_tabletop'][:,:,2])
    routing.require(float(green.max())>.1,'Grünes Feedback verschwunden.')
    routing.require(float(green[outside].max())<=1e-6,'Feedback außerhalb ursprünglicher Zielfläche.')
    checks.append(dict(case='feedback_preserved_and_clipped',passed=True))
    for age in (0,.09,.18,1):
        images=render(33,overlap=True,phase=1,age=age)
        alignment.check_floor(images['old_tabletop'],images['new_tabletop'])
    checks.append(dict(case='tabletop_success_unchanged',passed=True))
    # Reveal remains finite and the accepted redisplay still scales both surfaces.
    render(33,overlap=True,reveal=1.5)
    full=render(33,overlap=True,feedback=True)
    half=render(33,overlap=True,feedback=True,visibility=.5)
    for surface in ('floor','tabletop'):
        routing.require(float(np.max(np.abs(full['new_'+surface]*.5-half['new_'+surface])))<=1e-6,
                        'Weiche Wiedereinblendung verändert.')
    checks.append(dict(case='reveal_and_redisplay_preserved',passed=True))
    return checks


def install(resolve):
    return transaction.install(resolve,probe_path=PROBE,session=SESSION,backup=BACKUP,check=gpu_check)


def rollback(resolve):
    return transaction.rollback(resolve,backup=BACKUP)
