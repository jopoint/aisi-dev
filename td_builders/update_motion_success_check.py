"""Guarded tabletop success checkmark; no runtime or arrival-rule changes."""
from td_builders import update_motion_feedback_brightness as transaction
from td_builders import update_motion_alignment_guides as alignment
from td_builders import update_motion_redisplay as redisplay
from td_builders import build_motion_output_routing as routing

PROBE='/project1/comp_aisi_motion_success_check_probe'
SESSION='motion_success_check_probe'
BACKUP='motion_success_check_backup'
ANCHOR='float targetEdge(vec2 direction, float rotation, vec2 halfSize, float corner) {'
HELPER='''float successCheck(vec2 offset, vec3 target) {
    // Readable from the long side facing the ROI center. Local +Y faces reader.
    // Use the frozen target orientation, avoiding flips from tracking jitter.
    vec2 normal=rotate2(vec2(0,1),target.z);
    vec2 toCenter=vec2(250)-target.xy;
    float side=dot(toCenter,normal)<-0.001?-1.0:1.0;
    vec2 q=rotate2(offset,-target.z)*side;
    float d=min(segment(q,vec2(-9,0),vec2(-2,7)),
                segment(q,vec2(-2,7),vec2(11,-8)));
    return coverage(d-1.5);
}
'''
TABLE_ANCHOR='        // The global wave also passes over stationary/inactive captured tables.'
OVERLAY='''        // Success acknowledgement survives the completed phase, for three seconds.
        if(target.w>.5 && state.w>.5 && pulse.z<3.0) {
            float checkAlpha=smoothstep(0.0,.18,pulse.z)
                *(1.0-smoothstep(2.8,3.0,pulse.z));
            layer=over(white(successCheck(p-source.xy,target.xyz)
                *checkAlpha*sourceMask*released),layer);
        }
'''
PAIRS=((ANCHOR,HELPER+ANCHOR),(TABLE_ANCHOR,OVERLAY+TABLE_ANCHOR))


def patch_shader(text):
    return redisplay._patch(text,PAIRS)


def prepare(resolve):
    result=transaction.prepare(resolve,probe_path=PROBE,session=SESSION,backup=BACKUP,patcher=patch_shader)
    result.update(duration_seconds=3,position='source navigation center',
                  orientation='readable from ROI-center-facing long side',runtime_changed=False)
    return result


def world_pixel(image, point, mirrored_axes):
    """Map world coordinates using the independently rendered probe-mask axes."""
    import numpy as np
    uv=np.asarray(point,dtype=float)/500.0
    uv=np.where(mirrored_axes,1.0-uv,uv)
    x,y=np.rint(uv*np.array((image.shape[1],image.shape[0]))-.5).astype(int)
    routing.require(0<=x<image.shape[1] and 0<=y<image.shape[0],'Prüfpunkt außerhalb Bild.')
    return float(image[y,x])


def mask_axes(mask, center):
    """Measure array orientation from an asymmetric, known world-space mask."""
    import numpy as np
    routing.require(np.isfinite(mask).all() and float(mask.sum())>0,'Prüfmaske fehlt.')
    yy,xx=np.indices(mask.shape)
    total=float(mask.sum())
    measured=np.array((((xx+.5)*mask).sum()/total/mask.shape[1],
                       ((yy+.5)*mask).sum()/total/mask.shape[0]))*500
    center=np.asarray(center,dtype=float)
    axes=[]
    for observed,expected in zip(measured,center):
        direct=abs(observed-expected)<.25
        mirrored=abs(observed-(500-expected))<.25
        routing.require(direct != mirrored,'Bildachsen aus Prüfmaske nicht eindeutig bestimmt.')
        axes.append(bool(mirrored))
    return axes


def gpu_check(probe):
    import numpy as np
    from td_builders.motion_design import WIDTH,DEPTH,CORNER
    checks=[]
    floor_errors=[]
    def render(phase,age,rotation=0,center=(250,180),valid=1,visibility=1):
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
        floor_errors.append(alignment.check_floor(images['old_floor'],images['new_floor'])['max_float_error'])
        return images
    # numpyArray row order must be measured, not inferred from vUV convention.
    render(0,0,center=(180,180))
    mask_node=probe.op('mask_tabletop')
    routing.digest(mask_node)
    mirrored_axes=mask_axes(mask_node.numpyArray(delayed=False)[:,:,0],(180,180))
    checks.append(dict(case='array_axes_measured_from_independent_mask',mirrored_axes=mirrored_axes))
    for phase,age in ((0,0),(1,0),(2,3),(2,4)):
        images=render(phase,age)
        alignment.check_floor(images['old_tabletop'],images['new_tabletop'])
    checks.append(dict(case='guidance_and_expired_success_unchanged',passed=True))
    sums=[]
    for age in (.5,1,2,2.8,3):
        images=render(1 if age<1 else 2,age)
        alpha=images['new_tabletop'][:,:,3]
        if age>=1 and age<3:
            routing.require(float(alpha.max())>.99 and 100<float(alpha.sum())<800,
                            'Haken nach Abschluss nicht isoliert sichtbar.')
            routing.require(float(np.max(np.abs(images['new_tabletop']-alpha[:,:,None])))<1e-6,
                            'Haken nicht weiß/premultipliziert.')
        sums.append(float(alpha.sum()))
    checks.append(dict(case='white_check_persists_through_completed_until_three_seconds',
                       ages_seconds=[.5,1,2,2.8,3],alpha_sums=sums,passed=True))
    for center in ((250,180),(250,320),(180,250),(320,250),(250,250)):
        for rotation in (0,33,90,180,270):
            images=render(2,1.5,rotation,center)
            image=images['new_tabletop'][:,:,3]
            normal=np.array((-np.sin(np.radians(rotation)),np.cos(np.radians(rotation))))
            side=-1 if np.dot(250-np.array(center),normal)<-.001 else 1
            # The centerline of each stroke must be white at its rotated world position.
            a=np.radians(rotation)
            matrix=np.array(((np.cos(a),-np.sin(a)),(np.sin(a),np.cos(a))))
            for local in ((-9,0),(-2,7),(11,-8),(4.5,-.5)):
                point=np.array(center)+matrix@(np.array(local)*side)
                value=world_pixel(image,point,mirrored_axes)
                routing.require(value>.95,'Haken zur ROI-Längsseite falsch ausgerichtet: '
                                +str(dict(center=center,rotation=rotation,local=local,alpha=value)))
    checks.append(dict(case='readable_from_center_facing_long_side',rotations_deg=[0,33,90,180,270],passed=True))
    images=render(2,1.5,valid=0)
    routing.require(not images['new_tabletop'].any(),'Ungültige Source zeigt Haken.')
    full=render(2,1.5)
    half=render(2,1.5,visibility=.5)
    routing.require(float(np.max(np.abs(full['new_tabletop']*.5-half['new_tabletop'])))<1e-6,
                    'Wiedereinblendung nicht erhalten.')
    checks.append(dict(case='invalid_source_hidden_and_redisplay_preserved',passed=True))
    checks.append(dict(case='floor_precision',rgba8_pixel_equal=True,max_float_error=max(floor_errors)))
    return checks


def install(resolve):
    return transaction.install(resolve,probe_path=PROBE,session=SESSION,backup=BACKUP,check=gpu_check)


def rollback(resolve):
    return transaction.rollback(resolve,backup=BACKUP)
