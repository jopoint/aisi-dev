"""Earlier halo size from proximity; preserve contact, success and target clipping."""
from td_builders import build_motion_output_routing as routing
from td_builders import update_motion_feedback_brightness as transaction
from td_builders import update_motion_alignment_guides as alignment
from td_builders.update_motion_feedback_response import NEW_RADIUS as OLD_RADIUS

PROBE = '/project1/comp_aisi_motion_feedback_proximity_check'
SESSION = 'motion_feedback_proximity_probe'
BACKUP = 'motion_feedback_proximity_backup'
NEW_RADIUS = '''    float growth=max(smoothstep(0.0,1.0,clamp(h*1.2,0.0,1.0)),
                     1.0-smoothstep(20.0,80.0,distance));
    float radius=mix(35.0,81.4,growth);'''


def patch_shader(text):
    routing.require(text.count(OLD_RADIUS) == 1 and 'float growth=max(' not in text,
                    'Feedbackradius lokal abweichend oder bereits angepasst; nichts überschrieben.')
    return text.replace(OLD_RADIUS, NEW_RADIUS, 1)


def prepare(resolve):
    result = transaction.prepare(resolve, probe_path=PROBE, session=SESSION,
                                 backup=BACKUP, patcher=patch_shader)
    probe = resolve(PROBE)
    info = dict(probe.fetch(SESSION))
    start = info['old'].index('float feedbackHalo(')
    end = info['old'].index('float navigationShadow(', start)
    previous = info['old'][start:end].replace('float feedbackHalo(', 'float previousFeedbackHalo(', 1)
    info['mask'] = info['new'].split('void main() {')[0] + previous + '''void main() {
    vec2 p=vec2(vUV.x,1.0-vUV.y)*500.0;
    float h=datum(2,0).z;
    float distance=length(datum(1,0).xy-datum(0,0).xy);
    float current=feedbackHalo(p-250.0,0.0,h,4.0,distance);
    float previous=previousFeedbackHalo(p-250.0,0.0,h,4.0,distance);
    float growth=max(smoothstep(0.0,1.0,clamp(h*1.2,0.0,1.0)),
                     1.0-smoothstep(20.0,80.0,distance));
    float target=coverage(roundedRect(p-datum(1,0).xy,datum(4,0).xy*.5,datum(4,0).z));
    fragColor=TDOutputSwizzle(vec4(current,previous,mix(35.0,81.4,growth)/100.0,target));
}
'''
    probe.op('mask_pixel').text = info['mask']
    probe.store(SESSION, info)
    result.update(growth_distance_cm=[80, 20], maximum_radius_cm=81.4,
                  success_thresholds_changed=False)
    return result


def gpu_check(probe):
    import numpy as np
    from td_builders.motion_design import WIDTH, DEPTH, CORNER
    checks, errors = [], []

    def render(distance, h=0, phase=0):
        data = np.zeros((6, 6, 4), np.float32)
        data[0, 0] = (250, 250, 0, 1)
        data[0, 1] = (250+distance, 250, 0, 1)
        data[0, 2] = (0, 1, h, phase)
        data[0, 3] = (0, 0, .5, 0 if phase else 1)
        data[0, 4] = (WIDTH, DEPTH, CORNER, 0)
        data[5, 0] = (4, 4, 1, 1)
        probe.store('data', data)
        probe.op('state').cook(force=True)
        images = {}
        for name in ('old_floor', 'new_floor', 'old_tabletop', 'new_tabletop', 'mask_tabletop'):
            node = probe.op(name)
            routing.digest(node)
            images[name] = node.numpyArray(delayed=False).copy()
            routing.require(np.isfinite(images[name]).all(), 'Nichtendliche GPU-Ausgabe.')
        errors.append(alignment.check_floor(images['old_floor'], images['new_floor'])['max_float_error'])
        return images

    for distance in (120, 80, 65, 40, 20, 8, 0):
        images = render(distance)
        mask = images['mask_tabletop']
        u = max(0, min(1, (distance-20)/60))
        growth = 1 - u*u*(3-2*u)
        radius = 35 + 46.4*growth
        routing.require(float(np.max(np.abs(mask[:, :, 2]-radius/100))) < 1e-6,
                        'Distanzabhängiger Feedbackradius abweichend.')
        if distance >= 80:
            routing.require(np.array_equal(mask[:, :, 0], mask[:, :, 1]), 'Fernbereich verändert.')
        else:
            routing.require(float((mask[:, :, 0]-mask[:, :, 1]).min()) >= -1e-6
                            and int((mask[:, :, 0] > mask[:, :, 1]+.01).sum()) > 0,
                            'Feedback vor Erfolg nicht größer.')
        outside = mask[:, :, 3] == 0
        routing.require(np.array_equal(images['old_tabletop'][outside], images['new_tabletop'][outside]),
                        'Tabletop außerhalb des Ziel-Footprints verändert.')
        checks.append(dict(case='earlier_radius_even_with_low_progress', distance_cm=distance,
                           radius_cm=radius, passed=True))
    for phase in (1, 2):
        images = render(0, h=1, phase=phase)
        routing.require(np.array_equal(images['old_tabletop'], images['new_tabletop']),
                        'Erfolgsdarstellung verändert.')
    checks.append(dict(case='success_unchanged', passed=True))
    checks.append(dict(case='floor_precision', rgba8_pixel_equal=True, max_float_error=max(errors)))
    return checks


def install(resolve):
    return transaction.install(resolve, probe_path=PROBE, session=SESSION, backup=BACKUP, check=gpu_check)


def rollback(resolve):
    return transaction.rollback(resolve, backup=BACKUP)
