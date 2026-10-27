"""Fade the target-center template circle with the existing alignment guides."""
from td_builders import update_motion_feedback_brightness as transaction
from td_builders import update_motion_alignment_guides as alignment
from td_builders import compare_motion_target_divider as comparison
from td_builders import update_motion_redisplay as redisplay
from td_builders import build_motion_output_routing as routing

PROBE='/project1/comp_aisi_motion_target_template_fade_check'
SESSION='motion_target_template_fade_probe'
BACKUP='motion_target_template_fade_backup'
OLD='            float templateRing=coverage(abs(length(targetLocal)-13.0)-1.5)*targetMask;'
NEW='            float templateRing=coverage(abs(length(targetLocal)-13.0)-1.5)*targetMask*guides;'


def patch_shader(text):
    return redisplay._patch(text,((OLD,NEW),))


def prepare(resolve):
    comp=transaction.shadow._validate(resolve)
    routing.require(comp.fetch(comparison.SESSION,None) is None,
                    'Temporärer Vergleich noch offen; zuerst divider_compare.adopt_as_default(op) ausführen.')
    result=transaction.prepare(resolve,probe_path=PROBE,session=SESSION,backup=BACKUP,patcher=patch_shader)
    result.update(target_circle_uses_existing_guide_fade=True,fade_distance_cm=[45,15],
                  source_navigation_changed=False,white_surface_unchanged=True)
    return result


def gpu_check(probe):
    import numpy as np
    from td_builders.motion_design import WIDTH,DEPTH,CORNER
    checks=[]
    floor_errors=[]
    def render(distance,rotation=0,phase=0,age=0,visibility=1):
        data=np.zeros((6,6,4),np.float32)
        data[0,0]=(250,250,0,1)
        data[0,1]=(250+distance,250,rotation,1)
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
    for distance,expected in ((15,0),(30,.5),(45,1),(60,1)):
        images=render(distance)
        image=images['new_tabletop']
        # Ring point perpendicular to travel, outside the source navigation disk/bars.
        pixel=image[image.shape[0]//2+int(13/500*image.shape[0]),int((250+distance)/500*image.shape[1])]
        routing.require(abs(float(pixel[3])-expected)<=1e-5,
                        'Zielkreis folgt nicht dem Nähe-Fade der Ausrichtungshilfen.')
        checks.append(dict(case='target_circle_follows_guide_fade',distance_cm=distance,
                           expected_background_alpha=expected,actual_background_alpha=float(pixel[3])))
    for rotation in (0,33,90):
        images=render(15,rotation=rotation)
        alignment.check_floor(images['old_tabletop'],images['new_tabletop'])
    checks.append(dict(case='near_circle_unchanged_three_rotations',passed=True))
    for age in (0,.09,.18,1):
        success=render(0,phase=1,age=age)
        alignment.check_floor(success['old_tabletop'],success['new_tabletop'])
    full=render(30)
    half=render(30,visibility=.5)
    for surface in ('floor','tabletop'):
        routing.require(float(np.max(np.abs(full['new_'+surface]*.5-half['new_'+surface])))<=1e-6,
                        'Wiedereinblendung verändert.')
    checks.append(dict(case='success_and_redisplay_preserved',passed=True))
    checks.append(dict(case='floor_precision',rgba8_pixel_equal=True,max_float_error=max(floor_errors)))
    return checks


def install(resolve):
    return transaction.install(resolve,probe_path=PROBE,session=SESSION,backup=BACKUP,check=gpu_check)


def rollback(resolve):
    return transaction.rollback(resolve,backup=BACKUP)
