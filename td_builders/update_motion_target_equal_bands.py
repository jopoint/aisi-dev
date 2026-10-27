"""Equal 2.5 cm frame/divider bands, matched to the existing alignment bars."""
from td_builders import update_motion_target_frame_strip as frame
from td_builders import update_motion_feedback_brightness as transaction
from td_builders import update_motion_alignment_guides as alignment
from td_builders import update_motion_target_divisions as divisions
from td_builders import update_motion_redisplay as redisplay
from td_builders import build_motion_output_routing as routing

PROBE='/project1/comp_aisi_motion_target_equal_bands_check'
SESSION='motion_target_equal_bands_probe'
BACKUP='motion_target_equal_bands_backup'
WIDTH_CM=2.5
HELPER='''float targetDividers(vec2 local, vec2 halfSize, float corner) {
    // White frame: 0..2.5 cm inward. Transparent divider: 2.5..5 cm inward.
    float distance=roundedRect(local,halfSize,corner);
    return max(0.0,coverage(distance+2.5)-coverage(distance+5.0));
}
'''
FLOOR='''            float floorDistance=roundedRect(rotate2(p-target.xy,-target.z),halfSize,shape.z);
            float floorFrame=max(0.0,coverage(floorDistance-2.5)-targetMask);
            float floorCenter=coverage(floorDistance+2.5);
            vec4 f=white(max(floorFrame,floorCenter));'''


def patch_shader(text):
    routing.require(text.count('    return coverage(d-1.25);')==1 and text.count('float alignmentBars(')==1,
                    'Breite der Ausrichtungshilfen lokal abweichend; nichts überschrieben.')
    if text.count(HELPER)==1 and text.count(FLOOR)==1:
        return text
    normalized=frame.patch_shader(text)
    return redisplay._patch(normalized,((frame.HELPER,HELPER),(frame.FLOOR,FLOOR)))


def prepare(resolve):
    result=transaction.prepare(resolve,probe_path=PROBE,session=SESSION,backup=BACKUP,patcher=patch_shader)
    probe=resolve(PROBE)
    info=dict(probe.fetch(SESSION))
    info['mask']=info['new'].split('void main() {')[0]+'''void main() {
    vec2 p=vec2(vUV.x,1.0-vUV.y)*500.0;
    vec4 target=datum(1,0),shape=datum(4,0);
    vec2 local=rotate2(p-target.xy,-target.z);
    float distance=roundedRect(local,shape.xy*.5,shape.z);
    float original=coverage(distance);
    float floorFrame=max(0.0,coverage(distance-2.5)-original);
    float floorCenter=coverage(distance+2.5);
    float tableFill=original*(1.0-targetDividers(local,shape.xy*.5,shape.z)*original);
    fragColor=TDOutputSwizzle(vec4(original,max(floorFrame,floorCenter),tableFill,1));
}
'''
    probe.op('mask_pixel').text=info['mask']
    probe.store(SESSION,info)
    result.update(frame_strip_width_cm=WIDTH_CM,divider_width_cm=WIDTH_CM,
                  alignment_bar_width_cm=WIDTH_CM,white_center=True,
                  floor_frame='0..2.5 cm outside',floor_divider='0..2.5 cm inside',
                  tabletop_frame='0..2.5 cm inside',tabletop_divider='2.5..5 cm inside',masks_changed=False)
    return result


def gpu_check(probe):
    import numpy as np
    from td_builders.motion_design import WIDTH,DEPTH,CORNER
    checks=[]
    def render(rotation,coincident=False,phase=0,age=0,visibility=1):
        data=np.zeros((6,6,4),np.float32)
        data[0,0]=(250,250,rotation,1) if coincident else (100,100,0,1)
        data[0,1]=(250,250,rotation,1) if coincident else (300,300,rotation,1)
        data[0,2]=(0,0,.5,phase)
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
        mask=images['mask_tabletop']
        original,floor_fill,table_fill=(mask[:,:,i] for i in range(3))
        region=floor_fill>1e-6
        proof=divisions.check_pattern(images['new_floor'][region,3],floor_fill[region])
        routing.require(float(table_fill.sum())>.85*float(original.sum()),'Weiße Innenfläche fehlt.')
        checks.append(dict(case='equal_white_and_transparent_bands',rotation_deg=rotation,width_cm=WIDTH_CM,**proof))
        same=render(rotation,coincident=True)
        exterior=(same['mask_tabletop'][:,:,0]<=0)&(same['mask_tabletop'][:,:,1]>.99)
        routing.require(int(exterior.sum())>100 and float(same['new_floor'][exterior,3].min())>.99,
                        'Außenrahmen bei deckungsgleichem Source/Ziel maskiert.')
        checks.append(dict(case='exterior_frame_survives_source_mask',rotation_deg=rotation,passed=True))
    images=render(0)
    rows=np.flatnonzero(images['mask_tabletop'][:,600,0]>.99)
    row=int(round((int(rows[0])+int(rows[-1]))/2))
    def floor_at(x): return float(images['new_floor'][row,int(x/500*images['new_floor'].shape[1]),3])
    routing.require(floor_at(376)>.99 and floor_at(379)<.01
                    and floor_at(381)>.99 and floor_at(384)<1e-6,
                    'Bodenstreifen und Trennung nicht je 2,5 cm.')
    same=render(0,coincident=True)
    table=same['new_tabletop']
    def table_at(x): return float(table[table.shape[0]//2,int(x/500*table.shape[1]),3])
    routing.require(table_at(324)>.99 and table_at(326)<.01 and table_at(328)>.99,
                    'Tabletop-Rahmen und Trennung nicht je 2,5 cm.')
    checks.append(dict(case='same_nominal_width_as_alignment_bars',passed=True))
    for age in (0,.09,.18,1):
        images=render(33,coincident=True,phase=1,age=age)
        alignment.check_floor(images['old_tabletop'],images['new_tabletop'])
    full=render(33,coincident=True)
    half=render(33,coincident=True,visibility=.5)
    for surface in ('floor','tabletop'):
        routing.require(float(np.max(np.abs(full['new_'+surface]*.5-half['new_'+surface])))<=1e-6,
                        'Wiedereinblendung verändert.')
    checks.append(dict(case='tabletop_success_and_redisplay_preserved',passed=True))
    return checks


def install(resolve):
    return transaction.install(resolve,probe_path=PROBE,session=SESSION,backup=BACKUP,check=gpu_check)


def rollback(resolve):
    return transaction.rollback(resolve,backup=BACKUP)
