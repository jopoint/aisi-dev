"""Distance-only halo radius and transparent tabletop alignment guides."""
from td_builders import build_motion_output_routing as routing
from td_builders import update_motion_feedback_brightness as transaction
from td_builders import update_motion_alignment_guides as alignment
from td_builders import update_motion_feedback_proximity as proximity

PROBE = '/project1/comp_aisi_motion_feedback_size_cutouts_check'
SESSION = 'motion_feedback_size_cutouts_probe'
BACKUP = 'motion_feedback_size_cutouts_backup'
RADIUS = '''    float radius=35.0+(65.12-35.0)*(1.0-smoothstep(20.0,80.0,distance))
                     +(81.4-65.12)*(1.0-smoothstep(8.0,20.0,distance));'''
OLD_GUIDES = '''                layer*=1.0-targetGuides*targetFill;
                layer=over(white(targetGuides*(1.0-targetFill)),layer);'''
NEW_GUIDES = '                layer*=1.0-targetGuides;'
OLD_SOURCE = '            layer=over(white(sourceBars),layer);'
NEW_SOURCE = '            layer*=1.0-sourceBars;'


def patch_shader(text):
    candidates = (proximity.OLD_RADIUS, proximity.NEW_RADIUS)
    found = [code for code in candidates if text.count(code) == 1]
    routing.require(len(found) == 1 and RADIUS not in text
                    and text.count(OLD_GUIDES) == 1 and text.count(OLD_SOURCE) == 1,
                    'Radius-/Hilfencode lokal abweichend oder bereits angepasst; nichts überschrieben.')
    return (text.replace(found[0], RADIUS, 1).replace(OLD_GUIDES, NEW_GUIDES, 1)
            .replace(OLD_SOURCE, NEW_SOURCE, 1)
            .replace('// Target guides cut out on white, and remain white where a dividing line crosses.',
                     '// Target guides remain transparent through fill and feedback.')
            .replace('// Source bars stay white on both the physical source and the target overlap.',
                     '// Source alignment bars cut out alpha, including the target overlap.'))


def radius_cm(distance):
    def smooth_between(a, b):
        u = max(0, min(1, (distance-a)/(b-a)))
        return u*u*(3-2*u)
    return 35 + (65.12-35)*(1-smooth_between(20, 80)) + (81.4-65.12)*(1-smooth_between(8, 20))


def check_cutout(image, coverage, eligible=None):
    """Zero RGBA in the full core; preserve the coverage-complement at AA edges."""
    import numpy as np
    eligible = np.ones(coverage.shape, dtype=bool) if eligible is None else eligible
    core = (coverage == 1.0) & eligible
    routing.require(int(core.sum()) > 5, 'Zu wenige vollständig gedeckte Hilfen-Prüfpixel.')
    maximum = float(np.abs(image[core]).max())
    routing.require(maximum < 1e-6, 'Ausrichtungshilfe im Kern nicht transparent.')
    edge = (coverage > 0.0) & (coverage < 1.0) & eligible
    excess = (float(np.max(np.abs(image[edge])-(1.0-coverage[edge, None])))
              if bool(edge.any()) else 0.0)
    # Different shader contexts may evaluate rotated SDF edges at slightly
    # different Float32 precision; only the AA boundary gets this tolerance.
    routing.require(excess <= 1e-4, 'Alpha-Kante überschreitet das Komplement der Hilfenmaske.')
    return dict(core_pixels=int(core.sum()), core_max_rgba=maximum,
                edge_pixels=int(edge.sum()), edge_max_excess=excess)


def prepare(resolve):
    result = transaction.prepare(resolve, probe_path=PROBE, session=SESSION,
                                 backup=BACKUP, patcher=patch_shader)
    probe = resolve(PROBE)
    info = dict(probe.fetch(SESSION))
    info['mask'] = info['new'].split('void main() {')[0]+'''void main() {
    vec2 p=vec2(vUV.x,1.0-vUV.y)*500.0;
    vec4 source=datum(0,0),target=datum(1,0);
    float distance=length(target.xy-source.xy);
    float guides=1.0-smoothstep(15.0,45.0,distance);
    float navRadius=29.0*(.5+.5*smoothstep(20.0,65.0,distance));
    vec2 local=rotate2(p-target.xy,-target.z);
    float targetMask=coverage(roundedRect(local,datum(4,0).xy*.5,datum(4,0).z));
    float targetGuides=max(coverage(abs(length(local)-13.0)-1.5),alignmentBars(local,14.5))*targetMask*guides;
    float sourceBars=alignmentBars(rotate2(p-source.xy,-source.z),navRadius)*guides;
''' + RADIUS + '''
    fragColor=TDOutputSwizzle(vec4(targetGuides,sourceBars,radius/100.0,
                                  coverage(length(p-source.xy)-navRadius)));
}
'''
    probe.op('mask_pixel').text = info['mask']
    probe.store(SESSION, info)
    result.update(radius_at_20cm=65.12, fraction_of_maximum_radius=.8,
                  maximum_radius_cm=81.4, maximum_at_distance_cm=8,
                  alignment_guides='transparent alpha cutouts', success_thresholds_changed=False)
    return result


def gpu_check(probe):
    import numpy as np
    from td_builders.motion_design import WIDTH, DEPTH, CORNER
    checks, floor_errors = [], []

    def render(distance, h=0, rotation=0, phase=0):
        data = np.zeros((6, 6, 4), np.float32)
        data[0, 0] = (250, 250, rotation, 1)
        data[0, 1] = (250+distance, 250, rotation, 1)
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
        floor_errors.append(alignment.check_floor(images['old_floor'], images['new_floor'])['max_float_error'])
        return images

    for distance in (120, 80, 40, 20, 12, 8, 0):
        for h in (0, .5, 1):
            images = render(distance, h)
            actual = images['mask_tabletop'][:, :, 2]
            routing.require(float(np.max(np.abs(actual-radius_cm(distance)/100))) < 1e-6,
                            'Radius folgt nicht ausschließlich der Distanz.')
        checks.append(dict(case='distance_only_radius', distance_cm=distance,
                           radius_cm=radius_cm(distance), passed=True))
    for rotation in (0, 33, 90):
        images = render(12, rotation=rotation)
        mask, output = images['mask_tabletop'], images['new_tabletop']
        # Target helpers can be covered by the moving navigation disk; source bars cannot.
        source = check_cutout(output, mask[:, :, 1])
        target = check_cutout(output, mask[:, :, 0], mask[:, :, 3] == 0)
        checks.append(dict(case='transparent_source_and_target_guides', rotation_deg=rotation,
                           source=source, target=target, passed=True))
    for phase in (1, 2):
        images = render(0, phase=phase)
        routing.require(np.array_equal(images['old_tabletop'], images['new_tabletop']),
                        'Erfolgsdarstellung verändert.')
    checks.append(dict(case='success_unchanged', passed=True))
    checks.append(dict(case='floor_precision', rgba8_pixel_equal=True, max_float_error=max(floor_errors)))
    return checks


def install(resolve):
    return transaction.install(resolve, probe_path=PROBE, session=SESSION, backup=BACKUP, check=gpu_check)


def rollback(resolve):
    return transaction.rollback(resolve, backup=BACKUP)
