"""Earlier navigation size match and later alignment bars; display-only patch."""
from td_builders import update_motion_feedback_brightness as transaction
from td_builders import update_motion_alignment_guides as alignment
from td_builders import build_motion_output_routing as routing

PROBE = '/project1/comp_aisi_motion_alignment_timing_check'
SESSION = 'motion_alignment_timing_probe'
BACKUP = 'motion_alignment_timing_backup'
OLD_RADIUS = ': .5+.5*smoothstep(8.0,65.0,distance);'
NEW_RADIUS = ': .5+.5*smoothstep(20.0,65.0,distance);'
OLD_GUIDES = 'float guides=(1.0-smoothstep(25.0,65.0,distance))'
NEW_GUIDES = 'float guides=(1.0-smoothstep(15.0,45.0,distance))'


def patch_shader(text):
    if text.count(NEW_RADIUS)==1 and text.count(NEW_GUIDES)==1 and OLD_RADIUS not in text and OLD_GUIDES not in text:
        return text
    routing.require(text.count(OLD_RADIUS)==1 and text.count(OLD_GUIDES)==1
                    and NEW_RADIUS not in text and NEW_GUIDES not in text,
                    'Abstandssteuerung lokal abweichend; nichts überschrieben.')
    return text.replace(OLD_RADIUS,NEW_RADIUS,1).replace(OLD_GUIDES,NEW_GUIDES,1)


def prepare(resolve):
    result=transaction.prepare(resolve,probe_path=PROBE,session=SESSION,backup=BACKUP,patcher=patch_shader)
    probe=resolve(PROBE)
    info=dict(probe.fetch(SESSION))
    # Read the exact production expressions instead of maintaining a second curve.
    text=info['new']
    start=text.index('            state.x=success ?')
    end=text.index('            vec2 targetLocal=',start)
    expression=text[start:end]
    info['mask']=text.split('void main() {')[0]+'''void main() {
    vec4 source=datum(0,0), target=datum(1,0), state=datum(2,0), pulse=datum(3,0);
    float distance=length(target.xy-source.xy);
    bool success=state.w>.5;
'''+expression+'''
    fragColor=TDOutputSwizzle(vec4(state.x,guides,0,1));
}
'''
    probe.op('mask_pixel').text=info['mask']
    probe.store(SESSION,info)
    result.update(minimum_radius_distance_cm=20,guide_fade_distance_cm=[45,15])
    return result


def gpu_check(probe):
    import numpy as np
    from td_builders.motion_design import WIDTH,DEPTH,CORNER
    records=[]
    floor_errors=[]
    for distance in (0,8,15,20,30,45,65,120):
        data=np.zeros((6,6,4),np.float32)
        data[0,0]=(250,250,0,1)
        data[0,1]=(250+distance,250,0,1)
        data[0,2]=(0,0,0,0)
        data[0,3]=(0,0,0,1)
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
        radius,guides=map(float,images['mask_tabletop'][0,0,:2])
        if distance<=20:
            routing.require(abs(radius-.5)<1e-6,'Schablonengröße nicht bereits bei 20 cm erreicht.')
        if distance>=65:
            routing.require(abs(radius-1)<1e-6,'Ferner Kreisradius verändert.')
        if distance>=45:
            routing.require(guides==0,'Ausrichtungsstriche erscheinen zu früh.')
        if distance<=15:
            routing.require(abs(guides-1)<1e-6,'Nahe Ausrichtungsstriche nicht vollständig sichtbar.')
        if distance==30:
            routing.require(abs(guides-.5)<1e-6,'Später Strichfade nicht mittig bei 30 cm.')
        records.append(dict(distance_cm=distance,navigation_scale=radius,guide_opacity=guides))
    return [dict(case='earlier_size_match_later_guides',samples=records,passed=True),
            dict(case='floor_precision',rgba8_pixel_equal=True,max_float_error=max(floor_errors))]


def install(resolve):
    return transaction.install(resolve,probe_path=PROBE,session=SESSION,backup=BACKUP,check=gpu_check)


def rollback(resolve):
    return transaction.rollback(resolve,backup=BACKUP)
