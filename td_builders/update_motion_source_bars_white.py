"""White moving source bars; retain transparent target template and target bars."""
from td_builders import build_motion_output_routing as routing
from td_builders import update_motion_feedback_brightness as transaction
from td_builders import update_motion_alignment_guides as alignment
from td_builders import update_motion_feedback_size_cutouts as cutouts

PROBE = '/project1/comp_aisi_motion_source_bars_white_check'
SESSION = 'motion_source_bars_white_probe'
BACKUP = 'motion_source_bars_white_backup'
OLD_COMMENT = '// Source alignment bars cut out alpha, including the target overlap.'
NEW_COMMENT = '// Moving source bars are white; target guides remain alpha cutouts.'


def patch_shader(text):
    routing.require(text.count(cutouts.NEW_SOURCE) == 1 and text.count(cutouts.NEW_GUIDES) == 1
                    and cutouts.OLD_SOURCE not in text,
                    'Source-/Zielhilfen lokal abweichend oder Source-Striche bereits weiß.')
    return text.replace(cutouts.NEW_SOURCE, cutouts.OLD_SOURCE, 1).replace(OLD_COMMENT, NEW_COMMENT, 1)


def prepare(resolve):
    result = transaction.prepare(resolve, probe_path=PROBE, session=SESSION,
                                 backup=BACKUP, patcher=patch_shader)
    probe = resolve(PROBE)
    info = dict(probe.fetch(SESSION))
    info['mask'] = info['new'].split('void main() {')[0]+'''void main() {
    vec2 p=vec2(vUV.x,1.0-vUV.y)*500.0;
    vec4 source=datum(0,0),target=datum(1,0),shape=datum(4,0);
    float distance=length(target.xy-source.xy);
    float guides=1.0-smoothstep(15.0,45.0,distance);
    float navRadius=29.0*(.5+.5*smoothstep(20.0,65.0,distance));
    vec2 local=rotate2(p-target.xy,-target.z);
    float targetMask=coverage(roundedRect(local,shape.xy*.5,shape.z));
    float targetGuides=max(coverage(abs(length(local)-13.0)-1.5),alignmentBars(local,14.5))*targetMask*guides;
    float sourceBars=alignmentBars(rotate2(p-source.xy,-source.z),navRadius)*guides;
    float sourceMask=coverage(roundedRect(rotate2(p-source.xy,-source.z),shape.xy*.5,shape.z));
    fragColor=TDOutputSwizzle(vec4(targetGuides,sourceBars,
                                  coverage(length(p-source.xy)-navRadius),sourceMask));
}
'''
    probe.op('mask_pixel').text = info['mask']
    probe.store(SESSION, info)
    result.update(source_bars='white', target_circle_and_bars='transparent alpha cutouts')
    return result


def gpu_check(probe):
    import numpy as np
    from td_builders.motion_design import WIDTH, DEPTH, CORNER
    checks = []
    for rotation, phase in ((0,0), (33,0), (90,0), (33,2)):
        data = np.zeros((6,6,4), np.float32)
        data[0,0] = (250,250,rotation,1)
        data[0,1] = (262,250,rotation,1)
        data[0,2] = (0,1,.5,phase)
        data[0,3] = (0,0,10 if phase else 0,0 if phase else 1)
        data[0,4] = (WIDTH,DEPTH,CORNER,0)
        data[0,5] = (1,1,1 if phase else 0,1)
        data[5,0] = (20,10,1,1)
        data[5,1] = (10,1,1,0)
        probe.store('data', data)
        probe.op('state').cook(force=True)
        images = {}
        for name in ('old_floor','new_floor','old_tabletop','new_tabletop','mask_tabletop'):
            node = probe.op(name)
            routing.digest(node)
            images[name] = node.numpyArray(delayed=False).copy()
            routing.require(np.isfinite(images[name]).all(), 'Nichtendliche GPU-Ausgabe.')
        alignment.check_floor(images['old_floor'], images['new_floor'])
        old, new, mask = images['old_tabletop'], images['new_tabletop'], images['mask_tabletop']
        if phase:
            alignment.check_floor(old, new)
        else:
            source = (mask[:,:,1] == 1) & (mask[:,:,3] == 1)
            routing.require(int(source.sum()) > 5 and float(np.max(np.abs(new[source]-1))) < 1e-6,
                            'Source-Striche nicht vollständig weiß.')
            eligible = (mask[:,:,1] == 0) & (mask[:,:,2] == 0)
            cutouts.check_cutout(new, mask[:,:,0], eligible)
            alignment.check_floor(old[mask[:,:,1] == 0], new[mask[:,:,1] == 0])
        checks.append(dict(rotation_deg=rotation, phase=phase, floor_unchanged=True,
                           source_white_target_transparent=not bool(phase), success_unchanged=bool(phase)))
    return checks


def install(resolve):
    return transaction.install(resolve, probe_path=PROBE, session=SESSION, backup=BACKUP, check=gpu_check)


def rollback(resolve):
    return transaction.rollback(resolve, backup=BACKUP)
