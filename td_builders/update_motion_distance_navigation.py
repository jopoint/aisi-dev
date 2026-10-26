"""Distance-only navigation radius and a near-target contracting arrow."""
from td_builders import update_motion_feedback_brightness as transaction
from td_builders import update_motion_alignment_guides as alignment
from td_builders import build_motion_output_routing as routing

PROBE = '/project1/comp_aisi_motion_distance_navigation_check'
SESSION = 'motion_distance_navigation_probe'
BACKUP = 'motion_distance_navigation_backup'
OLD_SCALE = '                            : .5+.5*clamp(state.x,0.0,1.0);'
NEW_SCALE = '                            : .5+.5*smoothstep(8.0,65.0,distance);'
OLD_ARROW = '''                float hole=0.0;
                if(distance>=3.0 && state.x>0.0)
                    hole=arrow(rotate2(p-source.xy,-angle)/state.x-vec2(5,0));'''
NEW_ARROW = '''                float hole=0.0;
                float arrowScale=state.x*smoothstep(0.0,12.0,distance);
                if(distance>.001 && arrowScale>.0001) {
                    float arrowAngle=degrees(atan(delta.y,delta.x));
                    hole=arrow(rotate2(p-source.xy,-arrowAngle)/arrowScale-vec2(5,0));
                }'''


def patch_shader(text):
    if text.count(NEW_SCALE)==1 and text.count(NEW_ARROW)==1 and OLD_SCALE not in text and OLD_ARROW not in text:
        return text
    routing.require(text.count(OLD_SCALE)==1 and text.count(OLD_ARROW)==1
                    and NEW_SCALE not in text and NEW_ARROW not in text,
                    'Navigationscode lokal abweichend; nichts überschrieben.')
    return text.replace(OLD_SCALE,NEW_SCALE,1).replace(OLD_ARROW,NEW_ARROW,1)


def prepare(resolve):
    result = transaction.prepare(resolve, probe_path=PROBE, session=SESSION,
                                 backup=BACKUP, patcher=patch_shader)
    probe = resolve(PROBE)
    info = dict(probe.fetch(SESSION))
    # Probe exactly the production arrow expression in isolation, also where a
    # white target would otherwise hide its transparent cutout.
    diagnostic = info['new'].split('void main() {')[0]+'''void main() {
    vec2 p=vec2(vUV.x,1.0-vUV.y)*500.0;
    vec4 source=datum(0,0), target=datum(1,0), state=datum(2,0);
    vec2 delta=target.xy-source.xy;
    float distance=length(delta);
    state.x=.5+.5*smoothstep(8.0,65.0,distance);
'''+NEW_ARROW+'''
    fragColor=TDOutputSwizzle(white(hole));
}
'''
    info['mask'] = diagnostic
    probe.op('mask_pixel').text = diagnostic
    probe.store(SESSION,info)
    result.update(radius_distance_cm=[8,65], arrow_contraction_distance_cm=12)
    return result


def gpu_check(probe):
    import numpy as np
    from td_builders.motion_design import WIDTH, DEPTH, CORNER
    checks = []
    floor_errors = []
    def render(dx,dy,progress=0,rotation=0,phase=0,age=0):
        data = np.zeros((6,6,4),np.float32)
        data[0,0] = (250,250,0,1)
        data[0,1] = (250+dx,250+dy,rotation,1)
        data[0,2] = (progress,0,0,phase)
        data[0,3] = (0,0,age,1)
        data[0,4] = (WIDTH,DEPTH,CORNER,0)
        data[5,0] = (4,4,1,1)
        probe.store('data',data)
        probe.op('state').cook(force=True)
        images = {}
        for name in ('old_floor','new_floor','old_tabletop','new_tabletop','mask_tabletop'):
            node=probe.op(name)
            routing.digest(node)
            images[name]=node.numpyArray(delayed=False).copy()
            routing.require(np.isfinite(images[name]).all(),'Nichtendliche GPU-Ausgabe.')
        floor_errors.append(alignment.check_floor(images['old_floor'],images['new_floor'])['max_float_error'])
        return images
    for distance in (0,6,8,25,40,65,120):
        a=render(distance,0,0)
        b=render(distance,0,1)
        routing.require(np.array_equal(a['new_tabletop'],b['new_tabletop']),
                        'Kreisgröße hängt weiterhin vom Orientierungs-/Fortschrittswert ab.')
    checks.append(dict(case='distance_only_independent_of_progress',distances_cm=[0,6,8,25,40,65,120],passed=True))
    # Central white disk is visible beyond any clipped target at distance 120.
    image=render(120,0)['new_tabletop']
    routing.require(float(image[500,550,3])>.99 and float(image[500,564,3])<.01,
                    'Ferner Kreisradius ist nicht 29 cm.')
    # Exact production arrow diagnostics: decreasing size and aim on both sides.
    sums=[]
    for distance in (12,6,2,0):
        arrow_image=render(distance,0)['mask_tabletop'][:,:,3]
        sums.append(float(arrow_image.sum()))
    routing.require(sums[0]>sums[1]>sums[2]>=sums[3] and sums[3]==0,
                    'Pfeil schrumpft in Zielnähe nicht auf null.')
    checks.append(dict(case='arrow_contracts_to_zero',distances_cm=[12,6,2,0],arrow_alpha_sums=sums,passed=True))
    for dx,dy in ((6,0),(-6,0),(0,6),(0,-6)):
        arrow_image=render(dx,dy)['mask_tabletop'][:,:,3]
        y,x=np.mgrid[:arrow_image.shape[0],:arrow_image.shape[1]]
        # Only horizontal centroid tests require no array-origin assumption.
        if dx:
            center=float((((x+.5)*500/arrow_image.shape[1]-250)*arrow_image).sum()/arrow_image.sum())
            routing.require(center*dx>0,'Pfeil zeigt vom Zielmittelpunkt weg.')
    checks.append(dict(case='arrow_aims_at_target_both_sides',passed=True))
    # The new arrow/radius do not alter the accepted success contraction.
    for age in (0,.09,.18,1):
        images=render(0,0,phase=1,age=age)
        routing.require(np.array_equal(images['old_tabletop'],images['new_tabletop']),
                        'Erfolgsanimation verändert.')
    for rotation in (0,33,90): render(25,0,rotation=rotation)
    checks.append(dict(case='success_animation_unchanged',passed=True))
    checks.append(dict(case='floor_precision',rgba8_pixel_equal=True,max_float_error=max(floor_errors)))
    return checks


def install(resolve):
    return transaction.install(resolve,probe_path=PROBE,session=SESSION,backup=BACKUP,check=gpu_check)


def rollback(resolve):
    return transaction.rollback(resolve,backup=BACKUP)
