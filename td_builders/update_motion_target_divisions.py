"""White target surface with three clean rounded transparent dividing lines."""
from td_builders import update_motion_target_outline as outline
from td_builders import update_motion_feedback_brightness as transaction
from td_builders import update_motion_alignment_guides as alignment
from td_builders import update_motion_redisplay as redisplay
from td_builders import build_motion_output_routing as routing

PROBE='/project1/comp_aisi_motion_target_divisions_check'
SESSION='motion_target_divisions_probe'
BACKUP='motion_target_divisions_backup'
HELPER='''float targetDividers(vec2 local, vec2 halfSize, float corner) {
    float lines=0.0;
    for(int j=1;j<=3;j++) {
        vec2 ringHalf=halfSize-vec2(10.0*float(j));
        if(min(ringHalf.x,ringHalf.y)<=.5) continue;
        float radius=max(0.0,min(corner,min(ringHalf.x,ringHalf.y)-.5));
        float distance=roundedRect(local,ringHalf,radius);
        lines=max(lines,coverage(abs(distance)-.5));
    }
    return lines;
}
'''
OLD_TARGET='            float targetContour=targetOutline(rotate2(p-target.xy,-target.z),halfSize,shape.z);'
NEW_TARGET='''            float targetLines=targetDividers(rotate2(p-target.xy,-target.z),halfSize,shape.z)*targetMask;
            float targetFill=targetMask*(1.0-targetLines);'''
NEW_GUIDES='''                // Dividing lines stay transparent through feedback; navigation draws above them.
                layer*=1.0-targetLines;
                // Target guides cut out on white, and remain white where a dividing line crosses.
                float targetGuides=max(templateRing,targetBars);
                layer*=1.0-targetGuides*targetFill;
                layer=over(white(targetGuides*(1.0-targetFill)),layer);'''
PAIRS=((outline.HELPER,HELPER),(OLD_TARGET,NEW_TARGET),
       ('            vec4 f=white(targetContour);','            vec4 f=white(targetFill);'),
       ('            layer=white(success?0.0:targetContour);','            layer=white(success?0.0:targetMask);'),
       (outline.NEW_GUIDES,NEW_GUIDES))


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
    float lines=targetDividers(local,shape.xy*.5,shape.z)*outer;
    fragColor=TDOutputSwizzle(vec4(outer,lines,outer*(1.0-lines),1));
}
'''
    probe.op('mask_pixel').text=info['mask']
    probe.store(SESSION,info)
    result.update(white_fill_restored=True,division_insets_cm=[10,20,30],line_width_cm=1,
                  rounded_corners='same canonical radius on all rectangles',
                  surfaces=['floor','tabletop'],outer_footprint_changed=False)
    return result


def check_pattern(actual,expected):
    import numpy as np
    routing.require(actual.shape==expected.shape and np.isfinite(actual).all() and np.isfinite(expected).all(),
                    'Ungültige Linien-Prüfbilder.')
    difference=np.abs(actual-expected)
    maximum=float(difference.max())
    # Independent GLSL compiler contexts can differ at the antialiased SDF edge.
    # Flat white/open regions are not allowed this edge-only tolerance.
    flat=(expected<=1e-6)|(expected>=1-1e-6)
    routing.require(not flat.any() or float(difference[flat].max())<=1e-6,
                    'Weiße/transparente Zwischenflächen weichen ab.')
    steps=np.abs(np.rint(np.clip(actual,0,1)*255)-np.rint(np.clip(expected,0,1)*255))
    max_steps=int(steps.max())
    routing.require(maximum<=1e-4 and max_steps<=1,
                    'Bodenfläche folgt nicht dem gerundeten Linienmuster: Floatfehler=%r' % maximum)
    return dict(pattern_max_float_error=maximum,pattern_rgba8_max_difference=max_steps)


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
        outer,lines,fill=(images['mask_tabletop'][:,:,i] for i in range(3))
        inside=outer>=.999999
        outside=outer<=0
        routing.require(float(fill.sum())>.85*float(outer.sum()) and int((lines>.5).sum())>100,
                        'Weiße Fläche mit Trennlinien nicht wiederhergestellt.')
        pattern_proof=check_pattern(images['new_floor'][inside,3],fill[inside])
        for surface in ('floor','tabletop'):
            alignment.check_floor(images['old_'+surface][outside],images['new_'+surface][outside])
        checks.append(dict(case='white_fill_with_rounded_divisions',rotation_deg=rotation,
                           outer_footprint_preserved=True,white_fraction=float(fill.sum()/outer.sum()),
                           **pattern_proof))
        overlapping=render(rotation,overlap=True)
        restored=(overlapping['old_tabletop'][:,:,3]<.01)&(overlapping['new_tabletop'][:,:,3]>.99)
        routing.require(int(restored.sum())>500,'Tabletop-Füllung nicht wiederhergestellt.')
        checks.append(dict(case='tabletop_fill_restored',rotation_deg=rotation,restored_pixels=int(restored.sum())))
    # Each of the three nested lines must cross the long axis at the expected inset.
    images=render(0)
    floor=images['new_floor']
    # Find the diagnostic target center row without assuming numpy image origin.
    rows=np.flatnonzero(images['mask_tabletop'][:,600,0]>.99)
    row=int(round((int(rows[0])+int(rows[-1]))/2))
    for x in (350,360,370):
        routing.require(float(floor[row,int(x/500*floor.shape[1]),3])<.2,'Eine der drei Trennlinien fehlt.')
    for x in (340,355,365,375):
        routing.require(float(floor[row,int(x/500*floor.shape[1]),3])>.99,'Weiße Zwischenfläche fehlt.')
    checks.append(dict(case='three_nested_lines_and_white_intervals',passed=True))
    # Existing guide contrast returns to cutouts over the white base.
    guides=render(0,overlap=True)['new_tabletop']
    def pixel(image,x): return image[image.shape[0]//2,int(x/500*image.shape[1])]
    routing.require(float(pixel(guides,288)[3])<.01 and float(pixel(guides,300)[3])<.5,
                    'Zielschablone/-striche auf weißem Grund nicht ausgespart.')
    checks.append(dict(case='target_guides_contrast_preserved',passed=True))
    feedback=render(33,overlap=True,feedback=True)
    green=feedback['new_tabletop'][:,:,1]-np.maximum(feedback['new_tabletop'][:,:,0],feedback['new_tabletop'][:,:,2])
    routing.require(float(green.max())>.1,'Grünes Feedback verschwunden.')
    outside=feedback['mask_tabletop'][:,:,0]<=0
    routing.require(float(green[outside].max())<=1e-6,'Feedback außerhalb Zielumriss.')
    for age in (0,.09,.18,1):
        success=render(33,overlap=True,phase=1,age=age)
        alignment.check_floor(success['old_tabletop'],success['new_tabletop'])
    render(33,overlap=True,reveal=1.5)
    full=render(33,overlap=True,feedback=True)
    half=render(33,overlap=True,feedback=True,visibility=.5)
    for surface in ('floor','tabletop'):
        routing.require(float(np.max(np.abs(full['new_'+surface]*.5-half['new_'+surface])))<=1e-6,
                        'Weiche Wiedereinblendung verändert.')
    checks.append(dict(case='feedback_success_reveal_redisplay_preserved',passed=True))
    return checks


def install(resolve):
    return transaction.install(resolve,probe_path=PROBE,session=SESSION,backup=BACKUP,check=gpu_check)


def rollback(resolve):
    return transaction.rollback(resolve,backup=BACKUP)
