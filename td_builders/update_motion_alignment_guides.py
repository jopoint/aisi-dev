"""Tabletop alignment experiment; isolated GPU proof, no engine or geometry edits."""
from td_builders import update_motion_feedback_brightness as transaction
from td_builders import build_motion_output_routing as routing

PROBE = '/project1/comp_aisi_motion_alignment_check'
SESSION = 'motion_alignment_probe'
BACKUP = 'motion_alignment_backup'
OLD = '''            bool success=state.w>.5;
            layer=white(success?0.0:targetMask);
            float navRadius=29.0*state.x;
            float centerDistance=length(p-source.xy);
            if(success) {
                layer=vec4(0.0,236.0/255.0,101.0/255.0,1.0);
            } else {
                float ga=feedbackHalo(p-source.xy,angle,state.z,t,distance)
                    *smoothstep(0.0,1.0,state.y)*targetMask;
                layer=over(vec4(vec3(0.0,1.0,110.0/255.0)*ga,ga),layer);
                float ring=softRing(pulse.x,centerDistance)*pulse.y;
                float nav=state.x>0.0?coverage(centerDistance-navRadius):0.0;
                layer*=1.0-navigationShadow(p-source.xy,navRadius,state.x,nav);
                layer=over(white(ring*(1.0-nav)),layer);
                float hole=0.0;
                if(distance>=3.0 && state.x>0.0)
                    hole=arrow(rotate2(p-source.xy,-angle)/state.x-vec2(5,0));
                layer=over(white(nav*(1.0-hole)*(1.0-ring)),layer);
            }
'''
NEW = '''            bool success=state.w>.5;
            // Display-only scale: no state-engine or arrival-threshold changes.
            state.x=success ? .5*(1.0-smoothstep(0.0,.18,pulse.z))
                            : .5+.5*clamp(state.x,0.0,1.0);
            float guides=(1.0-smoothstep(25.0,65.0,distance))
                *(success?1.0-smoothstep(0.0,.18,pulse.z):1.0);
            vec2 targetLocal=rotate2(p-target.xy,-target.z);
            float templateRing=coverage(abs(length(targetLocal)-13.0)-1.5)*targetMask;
            float targetBars=alignmentBars(targetLocal,14.5)*guides*targetMask;
            layer=white(success?0.0:targetMask);
            float navRadius=29.0*state.x;
            float centerDistance=length(p-source.xy);
            if(success) {
                layer=vec4(0.0,236.0/255.0,101.0/255.0,1.0);
            } else {
                float ga=feedbackHalo(p-source.xy,angle,state.z,t,distance)
                    *smoothstep(0.0,1.0,state.y)*targetMask;
                layer=over(vec4(vec3(0.0,1.0,110.0/255.0)*ga,ga),layer);
                // Knock out target template before drawing the source navigation circle.
                layer*=1.0-max(templateRing,targetBars);
                float ring=softRing(pulse.x,centerDistance)*pulse.y;
                float nav=state.x>0.0?coverage(centerDistance-navRadius):0.0;
                layer*=1.0-navigationShadow(p-source.xy,navRadius,state.x,nav);
                layer=over(white(ring*(1.0-nav)),layer);
                float hole=0.0;
                if(distance>=3.0 && state.x>0.0)
                    hole=arrow(rotate2(p-source.xy,-angle)/state.x-vec2(5,0));
                layer=over(white(nav*(1.0-hole)*(1.0-ring)),layer);
            }
            // Source bars are white off-target and transparent on the white target.
            float sourceBars=alignmentBars(rotate2(p-source.xy,-source.z),navRadius)*guides;
            if(success) layer*=1.0-targetBars;
            layer*=1.0-sourceBars*targetMask;
            layer=over(white(sourceBars*(1.0-targetMask)),layer);
'''
HELPER = '''float alignmentBars(vec2 local, float radius) {
    float offset=radius+10.0;
    float d=min(segment(local,vec2(offset-5.0,0),vec2(offset+5.0,0)),
                segment(local,vec2(-offset-5.0,0),vec2(-offset+5.0,0)));
    return coverage(d-1.25);
}
'''
ANCHOR = '''            layer*=sourceMask*released*remain;'''
AFTER = '''            layer*=sourceMask*released*remain;
            // The success circle contracts as a disk, independently of the green dissolve.
            if(success && state.x>0.0)
                layer=over(white(coverage(centerDistance-navRadius)*sourceMask*released),layer);'''


def patch_shader(text):
    if NEW in text and HELPER in text and AFTER in text and OLD not in text:
        return text
    routing.require(text.count(OLD) == 1 and text.count(ANCHOR) == 1
                    and text.count('float targetEdge(') == 1 and 'alignmentBars(' not in text,
                    'Navigationscode lokal abweichend; nichts überschrieben.')
    return text.replace(OLD, NEW, 1).replace(ANCHOR, AFTER, 1).replace(
        'float targetEdge(', HELPER+'float targetEdge(', 1)


def prepare(resolve):
    result = transaction.prepare(resolve, probe_path=PROBE, session=SESSION,
                                 backup=BACKUP, patcher=patch_shader)
    result.update(minimum_navigation_scale=.5, template_radius_cm=14.5,
                  guide_fade_distance_cm=[65,25], success_contraction_seconds=.18)
    return result


def check_floor(old, new):
    import numpy as np
    routing.require(old.shape == new.shape and np.isfinite(old).all() and np.isfinite(new).all(),
                    'Ungültige Boden-Prüfbilder.')
    error = float(np.max(np.abs(old-new)))
    same_rgba8 = np.array_equal(np.rint(np.clip(old,0,1)*255).astype(np.uint8),
                               np.rint(np.clip(new,0,1)*255).astype(np.uint8))
    routing.require(error <= np.finfo(np.float32).eps and same_rgba8,
                    'Bodenausgabe verändert: Floatfehler=%r, RGBA8 gleich=%r' % (error,same_rgba8))
    return {'max_float_error': error, 'rgba8_pixel_equal': same_rgba8}


def gpu_check(probe):
    import numpy as np
    from td_builders.motion_design import WIDTH, DEPTH, CORNER
    checks = []
    floor_checks = []
    def render(target_x, rotation, nav, phase, age):
        data = np.zeros((6,6,4), np.float32)
        data[0,0] = (250,250,0,1)
        data[0,1] = (target_x,250,rotation,1)
        data[0,2] = (nav,0,0,phase)
        data[0,3] = (0,0,age,1)
        data[0,4] = (WIDTH,DEPTH,CORNER,0)
        data[5,0] = (4,4,1,1)
        probe.store('data',data)
        probe.op('state').cook(force=True)
        images = {}
        for name in ('old_floor','new_floor','old_tabletop','new_tabletop'):
            node = probe.op(name)
            routing.digest(node)
            images[name] = node.numpyArray(delayed=False).copy()
        floor_checks.append(check_floor(images['old_floor'],images['new_floor']))
        for image in images.values():
            routing.require(np.isfinite(image).all(), 'Nichtendliche GPU-Ausgabe.')
        return images['old_tabletop'], images['new_tabletop']
    def alpha(image,x,y=250):
        # All point probes use the central row, avoiding image-origin ambiguity.
        return float(image[int(image.shape[0]/2),int(x/500*image.shape[1]),3])
    # No target under the source: directly measure the white disk and its radius.
    old,new = render(370,0,0,0,0)
    routing.require(alpha(new,260)>.99 and alpha(new,267)<.01,
                    'Navigationskreis bleibt nicht bei halbem Radius.')
    checks.append(dict(case='minimum_navigation_radius',radius_cm=14.5,passed=True))
    _,far = render(370,0,1,0,0)
    routing.require(alpha(far,275)>.99 and alpha(far,282)<.01, 'Ferner Navigationsradius verändert.')
    checks.append(dict(case='full_navigation_radius',radius_cm=29,passed=True))
    # Target circle is a transparent ring centered exactly on the target.
    old,new = render(310,0,0,0,0)
    routing.require(alpha(old,323)>.99 and alpha(new,323)<.01
                    and alpha(new,310)>.99, 'Zielschablone nicht als mittiger Ring ausgespart.')
    checks.append(dict(case='centered_target_template',passed=True))
    # Bars white off-target and dark on-target; near-only, not in the far case.
    _,near = render(270,0,0,0,0)
    routing.require(alpha(near,225)<.01 and alpha(near,295)<.01,
                    'Striche auf weißem Ziel nicht ausgespart.')
    # Near rotated target: full guide opacity, source bar remains off the target.
    _,off_target = render(270,90,0,0,0)
    routing.require(alpha(off_target,225)>.99, 'Source-Strich außerhalb Ziel nicht weiß.')
    routing.require(alpha(far,215)<.01,
                    'Distanzabhängige Ausrichtungshilfen fehlerhaft.')
    checks.append(dict(case='near_guides_white_or_transparent',passed=True))
    for rotation in (0,33,90):
        old,new = render(280,rotation,0,0,0)
        routing.require(not np.array_equal(old,new), 'Neue Hilfen nicht sichtbar.')
        checks.append(dict(case='rotated_guidance',rotation_deg=rotation,floor_rgba8_pixel_equal=True))
    _,start = render(250,0,0,1,0)
    _,middle = render(250,0,0,1,.09)
    _,end = render(250,0,0,1,.18)
    # White disk contracts over unchanged green success field.
    def white_at(image,x):
        return float(image[image.shape[0]//2,int(x/500*image.shape[1]),0])
    routing.require(white_at(start,260)>.99 and white_at(middle,260)<.01
                    and white_at(middle,254)>.99 and white_at(end,250)<.01,
                    'Erfolgskreis zieht sich nicht nach innen zusammen.')
    _,completed = render(250,0,0,2,1)
    routing.require(float(np.max(np.abs(completed)))<=1e-6, 'Nach Erfolg verbleibt Grafik.')
    checks.append(dict(case='success_contracts_then_disappears',passed=True))
    checks.append(dict(case='floor_float_precision',rgba8_pixel_equal=True,
                       max_float_error=max(item['max_float_error'] for item in floor_checks)))
    return checks


def install(resolve):
    return transaction.install(resolve, probe_path=PROBE, session=SESSION,
                               backup=BACKUP, check=gpu_check)


def rollback(resolve):
    return transaction.rollback(resolve, backup=BACKUP)
