"""Thin target lines: outside on floor, inside on tabletop; masks unchanged."""
from td_builders import update_motion_target_single_line as single_line
from td_builders import update_motion_target_divisions as divisions
from td_builders import update_motion_feedback_brightness as transaction
from td_builders import update_motion_alignment_guides as alignment
from td_builders import update_motion_redisplay as redisplay
from td_builders import build_motion_output_routing as routing

PROBE='/project1/comp_aisi_motion_target_surface_lines_check'
SESSION='motion_target_surface_lines_probe'
BACKUP='motion_target_surface_lines_backup'
NEW_HELPER=single_line.NEW.replace('<=.3','<=.15').replace(')-.3',')-.15').replace('distance)-.3','distance)-.15')
FLOOR_OLD='            vec4 f=white(targetFill);'
FLOOR_NEW='''            float floorLine=coverage(abs(roundedRect(rotate2(p-target.xy,-target.z),halfSize,shape.z)-1.0)-.15);
            vec4 f=white(max(targetMask,floorLine));'''


def patch_shader(text):
    if text.count(NEW_HELPER)==1 and text.count(FLOOR_NEW)==1 and FLOOR_OLD not in text:
        return text
    known=[helper for helper in (single_line.NEW,divisions.HELPER) if text.count(helper)==1]
    routing.require(len(known)==1,'Lokale Linienfunktion unbekannt; nichts überschrieben.')
    return redisplay._patch(text,((known[0],NEW_HELPER),(FLOOR_OLD,FLOOR_NEW)))


def prepare(resolve):
    result=transaction.prepare(resolve,probe_path=PROBE,session=SESSION,backup=BACKUP,patcher=patch_shader)
    probe=resolve(PROBE)
    info=dict(probe.fetch(SESSION))
    info['mask']=info['new'].split('void main() {')[0]+'''void main() {
    vec2 p=vec2(vUV.x,1.0-vUV.y)*500.0;
    vec4 target=datum(1,0),shape=datum(4,0);
    vec2 local=rotate2(p-target.xy,-target.z);
    float distance=roundedRect(local,shape.xy*.5,shape.z);
    float outer=coverage(distance);
    float floorLine=coverage(abs(distance-1.0)-.15);
    float tabletopLine=targetDividers(local,shape.xy*.5,shape.z)*outer;
    fragColor=TDOutputSwizzle(vec4(outer,floorLine,tabletopLine,1));
}
'''
    probe.op('mask_pixel').text=info['mask']
    probe.store(SESSION,info)
    result.update(line_width_cm=.3,floor_line_offset_cm=1,tabletop_line_inset_cm=10,
                  masks_changed=False,white_fill_preserved=True,success_animation_changed=False)
    return result


def gpu_check(probe):
    import numpy as np
    from td_builders.motion_design import WIDTH,DEPTH,CORNER
    checks=[]
    def render(rotation,coincident=False,feedback=False,phase=0,age=0,visibility=1):
        data=np.zeros((6,6,4),np.float32)
        data[0,0]=(250,250,rotation,1) if coincident else (100,100,0,1)
        data[0,1]=(250,250,rotation,1) if coincident else (300,300,rotation,1)
        data[0,2]=(0,int(feedback),.5,phase)
        data[0,3]=(0,0,age,1)
        data[0,4]=(WIDTH,DEPTH,CORNER,0)
        data[0,5]=(visibility,1,0,0)
        data[5,0]=(4,4,1,1)
        probe.store('data',data)
        probe.op('state').cook(force=True)
        images={}
        for name in ('old_floor','new_floor','old_tabletop','new_tabletop','mask_tabletop'):
            node=probe.op(name)
            routing.digest(node)
            images[name]=node.numpyArray(delayed=False).copy()
            routing.require(np.isfinite(images[name]).all(),'Nichtendliche GPU-Ausgabe.')
        return images
    for rotation in (0,33,90):
        images=render(rotation)
        outer,floor_line,table_line=(images['mask_tabletop'][:,:,i] for i in range(3))
        floor_pixels=floor_line>1e-6
        routing.require(int(floor_pixels.sum())>100 and float(outer[floor_pixels].max())==0,
                        'Bodenlinie liegt nicht vollständig außerhalb der ursprünglichen Fläche.')
        routing.require(float(table_line[outer<=0].max())==0,'Tabletop-Linie liegt außerhalb Zielfläche.')
        proof=divisions.check_pattern(images['new_floor'][floor_pixels,3],floor_line[floor_pixels])
        inside=outer>=.999999
        routing.require(float(images['new_floor'][inside,3].min())>.999,
                        'Im Boden-Ziel verbleibt eine innere Trennlinie.')
        protected=(outer<=0)&(floor_line<=0)
        alignment.check_floor(images['old_floor'][protected],images['new_floor'][protected])
        alignment.check_floor(images['old_tabletop'][outer<=0],images['new_tabletop'][outer<=0])
        checks.append(dict(case='floor_outside_tabletop_inside',rotation_deg=rotation,
                           line_width_cm=.3,**proof))
        # Keep guidance phase explicitly: isolate geometric masking from success fade.
        coincident_images=render(rotation,coincident=True)
        diagnostic=coincident_images['mask_tabletop']
        band=diagnostic[:,:,1]>1e-6
        proof=divisions.check_pattern(coincident_images['new_floor'][band,3],diagnostic[:,:,1][band])
        routing.require(float(coincident_images['new_floor'][band,3].max())>.1,
                        'Boden-Außenlinie bei deckungsgleichem Source/Ziel vollständig maskiert.')
        checks.append(dict(case='coincident_source_mask_preserves_exterior_line',rotation_deg=rotation,**proof))
    images=render(0,coincident=True)
    def pixel(image,x): return image[image.shape[0]//2,int(x/500*image.shape[1])]
    old_alpha=float(pixel(images['old_tabletop'],320)[3])
    new_alpha=float(pixel(images['new_tabletop'],320)[3])
    routing.require(old_alpha<new_alpha<.9,'Tabletop-Linie fehlt oder ist nicht dünner.')
    checks.append(dict(case='tabletop_line_halved',old_line_sample_alpha=old_alpha,new_line_sample_alpha=new_alpha))
    for age in (0,.09,.18,1):
        success=render(33,coincident=True,phase=1,age=age)
        alignment.check_floor(success['old_tabletop'],success['new_tabletop'])
    full=render(33,coincident=True,feedback=True)
    half=render(33,coincident=True,feedback=True,visibility=.5)
    for surface in ('floor','tabletop'):
        routing.require(float(np.max(np.abs(full['new_'+surface]*.5-half['new_'+surface])))<=1e-6,
                        'Weiche Wiedereinblendung verändert.')
    checks.append(dict(case='tabletop_success_and_redisplay_preserved',passed=True))
    return checks


def install(resolve):
    return transaction.install(resolve,probe_path=PROBE,session=SESSION,backup=BACKUP,check=gpu_check)


def rollback(resolve):
    return transaction.rollback(resolve,backup=BACKUP)
