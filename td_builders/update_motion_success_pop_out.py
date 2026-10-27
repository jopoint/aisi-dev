"""Replace the success-check fade with a reversed pop after one second."""
from td_builders import update_motion_success_pop as pop
from td_builders import update_motion_feedback_brightness as transaction
from td_builders import update_motion_alignment_guides as alignment
from td_builders import update_motion_redisplay as redisplay
from td_builders.update_motion_target_divisions import check_pattern
from td_builders import build_motion_output_routing as routing

PROBE='/project1/comp_aisi_motion_success_pop_out_check'
SESSION='motion_success_pop_out_probe'
BACKUP='motion_success_pop_out_backup'
OVERLAY='''        // Keep the entrance pop; reverse it after one second, without fading.
        if(target.w>.5 && state.w>.5 && pulse.z<1.32) {
            float checkScale=pulse.z<=1.0?successPop(pulse.z)
                :successPop(max(0.0,1.32-pulse.z));
            if(checkScale>.0001)
                layer=over(white(successCheck((p-source.xy)/checkScale,target.xyz)
                    *sourceMask*released),layer);
        }
'''
PAIRS=((pop.OVERLAY,OVERLAY),)


def patch_shader(text):
    routing.require(text.count(pop.HELPER)==1,'Bestehende Pop-Funktion fehlt oder ist lokal verändert.')
    return redisplay._patch(text,PAIRS)


def prepare(resolve):
    result=transaction.prepare(resolve,probe_path=PROBE,session=SESSION,backup=BACKUP,patcher=patch_shader)
    result.update(exit_starts_seconds=1,exit_duration_seconds=.32,hidden_after_seconds=1.32,
                  fade=False,entrance_pop_changed=False,runtime_changed=False)
    return result


def gpu_check(probe):
    import numpy as np
    from td_builders.motion_design import WIDTH,DEPTH,CORNER
    checks=[]
    errors=[]
    def render(age,phase=2,rotation=0,valid=1,visibility=1):
        data=np.zeros((6,6,4),np.float32)
        data[0,0]=(180,180,rotation,valid)
        data[0,1]=(180,180,rotation,1)
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
    for rotation in (0,33,90):
        samples={}
        for age in (0,.08,.2,.32,.7,1,1.12,1.24,1.32,2,3):
            images=render(age,rotation=rotation)
            image=images['new_tabletop']
            alpha=image[:,:,3]
            expected=0 if age==0 or age>=1.32 else 1
            routing.require(abs(float(alpha.max())-expected)<1e-5,'Haken fadet oder endet nicht bei 1,32 s.')
            routing.require(float(np.max(np.abs(image-alpha[:,:,None])))<1e-6,'Haken nicht weiß/premultipliziert.')
            samples[age]=alpha.copy()
            if 0<age<=1:
                # Remove only the previous fade; the complete entrance geometry stays identical.
                normalized=images['old_tabletop']/(1-age/3)
                check_pattern(image,normalized)
        for entering,exiting in ((.2,1.12),(.08,1.24)):
            # Allow only subpixel Float32 time arithmetic differences in AA pixels.
            check_pattern(samples[exiting],samples[entering])
        routing.require(float(samples[.2].sum())>float(samples[.32].sum())
                        >float(samples[.08].sum()),'Übergröße und Schrumpfen fehlen.')
        checks.append(dict(case='same_pop_reversed_after_one_second_no_fade',rotation_deg=rotation,passed=True))
    images=render(.5,phase=0)
    alignment.check_floor(images['old_tabletop'],images['new_tabletop'])
    full=render(.7)['new_tabletop']
    half=render(.7,visibility=.5)['new_tabletop']
    routing.require(float(np.max(np.abs(full*.5-half)))<1e-6,'Wiedereinblendung verändert.')
    routing.require(not render(.7,valid=0)['new_tabletop'].any(),'Ungültige Source zeigt Haken.')
    checks.append(dict(case='guidance_invalid_source_and_redisplay_preserved',passed=True))
    checks.append(dict(case='floor_precision',rgba8_pixel_equal=True,max_float_error=max(errors)))
    return checks


def install(resolve):
    return transaction.install(resolve,probe_path=PROBE,session=SESSION,backup=BACKUP,check=gpu_check)


def rollback(resolve):
    return transaction.rollback(resolve,backup=BACKUP)
