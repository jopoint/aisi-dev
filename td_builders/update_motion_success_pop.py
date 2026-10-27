"""Pop the existing success check, then fade immediately over three seconds."""
from td_builders import update_motion_success_check as success
from td_builders import update_motion_feedback_brightness as transaction
from td_builders import update_motion_alignment_guides as alignment
from td_builders import update_motion_redisplay as redisplay
from td_builders import build_motion_output_routing as routing

PROBE='/project1/comp_aisi_motion_success_pop_check'
SESSION='motion_success_pop_probe'
BACKUP='motion_success_pop_backup'
ANCHOR='float successCheck(vec2 offset, vec3 target) {'
HELPER='''float successPop(float age) {
    // Ease-out-back: grow from zero, overshoot slightly, settle after 0.32 s.
    float x=clamp(age/.32,0.0,1.0)-1.0;
    return max(0.0,1.0+2.70158*x*x*x+1.70158*x*x);
}
'''
OVERLAY='''        // Pop and immediately fade the acknowledgement over three seconds.
        if(target.w>.5 && state.w>.5 && pulse.z<3.0) {
            float checkScale=successPop(pulse.z);
            float checkAlpha=clamp(1.0-pulse.z/3.0,0.0,1.0);
            if(checkScale>.0001)
                layer=over(white(successCheck((p-source.xy)/checkScale,target.xyz)
                    *checkAlpha*sourceMask*released),layer);
        }
'''
PAIRS=((ANCHOR,HELPER+ANCHOR),(success.OVERLAY,OVERLAY))


def patch_shader(text):
    return redisplay._patch(text,PAIRS)


def prepare(resolve):
    result=transaction.prepare(resolve,probe_path=PROBE,session=SESSION,backup=BACKUP,patcher=patch_shader)
    result.update(duration_seconds=3,pop_seconds=.32,fade='immediate linear fade',runtime_changed=False)
    return result


def gpu_check(probe):
    import numpy as np
    from td_builders.motion_design import WIDTH,DEPTH,CORNER
    checks=[]
    errors=[]
    def render(age,phase=2,rotation=0,center=(180,180),valid=1,visibility=1):
        data=np.zeros((6,6,4),np.float32)
        data[0,0]=(*center,rotation,valid)
        data[0,1]=(*center,rotation,1)
        data[0,2]=(0,0,0,phase)
        data[0,3]=(0,0,age,1)
        data[0,4]=(WIDTH,DEPTH,CORNER,0)
        data[0,5]=(visibility,1,0,0)
        data[5,0]=(4,4,1,1)
        probe.store('data',data)
        probe.op('state').cook(force=True)
        images={}
        for name in ('old_floor','new_floor','old_tabletop','new_tabletop'):
            node=probe.op(name)
            routing.digest(node)
            images[name]=node.numpyArray(delayed=False).copy()
            routing.require(np.isfinite(images[name]).all(),'Nichtendliche GPU-Ausgabe.')
        errors.append(alignment.check_floor(images['old_floor'],images['new_floor'])['max_float_error'])
        return images
    render(1)
    mask_node=probe.op('mask_tabletop')
    routing.digest(mask_node)
    axes=success.mask_axes(mask_node.numpyArray(delayed=False)[:,:,0],(180,180))
    widths={}
    samples=[]
    for age in (0,.08,.16,.2,.32,.8,1.5,2.5,3,4):
        image=render(age)['new_tabletop']
        alpha=image[:,:,3]
        expected=max(0,1-age/3) if age>0 else 0
        routing.require(abs(float(alpha.max())-expected)<1e-5,'Haken fadet nicht sofort über drei Sekunden.')
        routing.require(float(np.max(np.abs(image-alpha[:,:,None])))<1e-6,'Haken nicht weiß/premultipliziert.')
        if age in (.08,.2,.32):
            y,x=np.nonzero(alpha>expected*.5)
            widths[age]=int(x.max()-x.min()+1)
        samples.append(dict(age_seconds=age,max_alpha=float(alpha.max())))
    routing.require(widths[.08]<widths[.32]<widths[.2],'Aufploppen ohne messbare Übergröße/Zurückfedern.')
    checks.append(dict(case='pop_overshoot_then_settle',widths_pixels=widths,passed=True))
    checks.append(dict(case='immediate_three_second_fade',samples=samples,passed=True))
    for center in ((180,180),(320,320),(250,250)):
        for rotation in (0,33,90,180,270):
            image=render(1.5,rotation=rotation,center=center)['new_tabletop'][:,:,3]
            a=np.radians(rotation)
            matrix=np.array(((np.cos(a),-np.sin(a)),(np.sin(a),np.cos(a))))
            normal=matrix@np.array((0,1))
            side=-1 if np.dot(250-np.array(center),normal)<-.001 else 1
            for local in ((-9,0),(-2,7),(11,-8)):
                point=np.array(center)+matrix@(np.array(local)*side)
                routing.require(success.world_pixel(image,point,axes)>.475,'Haken-Ausrichtung verändert.')
    checks.append(dict(case='orientation_preserved',passed=True))
    images=render(0,phase=0)
    alignment.check_floor(images['old_tabletop'],images['new_tabletop'])
    full=render(1.5)['new_tabletop']
    half=render(1.5,visibility=.5)['new_tabletop']
    routing.require(float(np.max(np.abs(full*.5-half)))<1e-6,'Wiedereinblendung verändert.')
    routing.require(not render(1.5,valid=0)['new_tabletop'].any(),'Ungültige Source zeigt Haken.')
    checks.append(dict(case='guidance_invalid_source_and_redisplay_preserved',passed=True))
    checks.append(dict(case='floor_precision',rgba8_pixel_equal=True,max_float_error=max(errors)))
    return checks


def install(resolve):
    return transaction.install(resolve,probe_path=PROBE,session=SESSION,backup=BACKUP,check=gpu_check)


def rollback(resolve):
    return transaction.rollback(resolve,backup=BACKUP)
