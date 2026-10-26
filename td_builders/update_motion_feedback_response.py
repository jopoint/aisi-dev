"""White source alignment bars and slightly earlier tabletop halo growth."""
from td_builders import update_motion_feedback_brightness as transaction
from td_builders import update_motion_alignment_guides as alignment
from td_builders import build_motion_output_routing as routing

PROBE='/project1/comp_aisi_motion_feedback_response_check'
SESSION='motion_feedback_response_probe'
BACKUP='motion_feedback_response_backup'
OLD_RADIUS='    float radius=mix(35.0,81.4,smoothstep(0.0,1.0,h));'
NEW_RADIUS='    float radius=mix(35.0,81.4,smoothstep(0.0,1.0,clamp(h*1.2,0.0,1.0)));'
OLD_BARS='''            layer*=1.0-sourceBars*targetMask;
            layer=over(white(sourceBars*(1.0-targetMask)),layer);'''
NEW_BARS='''            layer=over(white(sourceBars),layer);'''
OLD_COMMENT='// Source bars are white off-target and transparent on the white target.'
NEW_COMMENT='// Source bars stay white on both the physical source and the target overlap.'


def patch_shader(text):
    if text.count(NEW_RADIUS)==1 and text.count(NEW_BARS)==1 and OLD_RADIUS not in text and OLD_BARS not in text:
        return text
    routing.require(text.count(OLD_RADIUS)==1 and text.count(OLD_BARS)==1
                    and text.count(OLD_COMMENT)==1 and NEW_RADIUS not in text and NEW_BARS not in text,
                    'Feedback-/Strichcode lokal abweichend; nichts überschrieben.')
    return (text.replace(OLD_RADIUS,NEW_RADIUS,1).replace(OLD_BARS,NEW_BARS,1)
            .replace(OLD_COMMENT,NEW_COMMENT,1))


def prepare(resolve):
    result=transaction.prepare(resolve,probe_path=PROBE,session=SESSION,backup=BACKUP,patcher=patch_shader)
    probe=resolve(PROBE)
    info=dict(probe.fetch(SESSION))
    start=info['old'].index('float feedbackHalo(')
    end=info['old'].index('float navigationShadow(',start)
    previous=info['old'][start:end].replace('float feedbackHalo(', 'float previousFeedbackHalo(',1)
    info['mask']=info['new'].split('void main() {')[0]+previous+'''void main() {
    vec2 p=vec2(vUV.x,1.0-vUV.y)*500.0;
    float h=datum(2,0).z;
    float current=feedbackHalo(p-250.0,0.0,h,4.0,100.0);
    float previous=previousFeedbackHalo(p-250.0,0.0,h,4.0,100.0);
    fragColor=TDOutputSwizzle(vec4(current,previous,0,1));
}
'''
    probe.op('mask_pixel').text=info['mask']
    probe.store(SESSION,info)
    result.update(source_bars='always white',halo_growth_progress_multiplier=1.2,
                  halo_radius_cm=[35,81.4])
    return result


def gpu_check(probe):
    import numpy as np
    from td_builders.motion_design import WIDTH,DEPTH,CORNER
    checks=[]
    floor_errors=[]
    def render(h,contact=0,phase=0,age=0):
        data=np.zeros((6,6,4),np.float32)
        data[0,0]=(250,250,0,1)
        data[0,1]=(265,250,0,1)
        data[0,2]=(0,contact,h,phase)
        data[0,3]=(0,0,age,1)
        data[0,4]=(WIDTH,DEPTH,CORNER,0)
        data[5,0]=(4,4,1,1)
        probe.store('data',data)
        probe.op('state').cook(force=True)
        images={}
        for name in ('old_floor','new_floor','old_tabletop','new_tabletop','mask_tabletop'):
            node=probe.op(name)
            routing.digest(node)
            images[name]=node.numpyArray(delayed=False).copy()
            routing.require(np.isfinite(images[name]).all(),'Nichtendliche GPU-Ausgabe.')
        floor_errors.append(alignment.check_floor(images['old_floor'],images['new_floor'])['max_float_error'])
        return images
    images=render(0)
    old,new=images['old_tabletop'],images['new_tabletop']
    def pixel(image,x): return image[image.shape[0]//2,int(x/500*image.shape[1])]
    for x in (225,275):
        routing.require(float(pixel(old,x)[3])<.01 and bool(np.all(pixel(new,x)>.99)),
                        'Source-Strich auf Zielfläche nicht vollständig weiß.')
    routing.require(float(pixel(new,290)[3])<.01,'Zielstrich nicht mehr ausgespart.')
    checks.append(dict(case='source_bars_white_target_bars_transparent',passed=True))
    samples=[]
    for h in (0,.25,.5,.75,1):
        images=render(h,contact=1)
        halo=images['mask_tabletop']
        new_halo,old_halo=halo[:,:,0],halo[:,:,1]
        if h in (0,1):
            routing.require(np.array_equal(new_halo,old_halo),'Anfangs-/Endgröße des Feedbacks verändert.')
        else:
            difference=new_halo-old_halo
            routing.require(float(difference.min())>=-1e-6 and int((difference>.01).sum())>0,
                            'Feedback wächst nicht früher oder wird kleiner.')
        samples.append(dict(progress=h,new_alpha_sum=float(new_halo.sum()),old_alpha_sum=float(old_halo.sum())))
    checks.append(dict(case='earlier_growth_same_endpoints',samples=samples,passed=True))
    images=render(.5,phase=1,age=.18)
    routing.require(np.array_equal(images['old_tabletop'],images['new_tabletop']),
                    'Erfolgsauflösung nach Verschwinden der Hilfen verändert.')
    checks.append(dict(case='success_after_guides_unchanged',passed=True))
    checks.append(dict(case='floor_precision',rgba8_pixel_equal=True,max_float_error=max(floor_errors)))
    return checks


def install(resolve):
    return transaction.install(resolve,probe_path=PROBE,session=SESSION,backup=BACKUP,check=gpu_check)


def rollback(resolve):
    return transaction.rollback(resolve,backup=BACKUP)
