"""Four-centimetre white frame strip, filled center and fine dividing line."""
from td_builders import update_motion_target_surface_lines as surfaces
from td_builders import update_motion_target_single_line as single_line
from td_builders import update_motion_target_divisions as divisions
from td_builders import update_motion_target_outline as outline
from td_builders import update_motion_feedback_brightness as transaction
from td_builders import update_motion_alignment_guides as alignment
from td_builders import update_motion_redisplay as redisplay
from td_builders import build_motion_output_routing as routing

PROBE='/project1/comp_aisi_motion_target_frame_strip_check'
SESSION='motion_target_frame_strip_probe'
BACKUP='motion_target_frame_strip_backup'
HELPER='''float targetDividers(vec2 local, vec2 halfSize, float corner) {
    // A constant-distance inner divider leaves a 4 cm strip with rounded corners.
    float distance=roundedRect(local,halfSize,corner);
    return coverage(abs(distance+4.0)-.3);
}
'''
FLOOR='''            float floorDistance=roundedRect(rotate2(p-target.xy,-target.z),halfSize,shape.z);
            float floorDivider=coverage(abs(floorDistance)-.3);
            vec4 f=white(coverage(floorDistance-4.0)*(1.0-floorDivider));'''


def patch_shader(text):
    if text.count(HELPER)==1 and text.count(FLOOR)==1:
        return text
    # The earlier outline may still be active if later experiments were only prepared.
    if text.count(outline.HELPER)==1:
        text=divisions.patch_shader(text)
    helpers=[h for h in (surfaces.NEW_HELPER,single_line.NEW,divisions.HELPER) if text.count(h)==1]
    floors=[f for f in (surfaces.FLOOR_NEW,surfaces.FLOOR_OLD) if text.count(f)==1]
    routing.require(len(helpers)==1 and len(floors)==1 and HELPER not in text and FLOOR not in text,
                    'Rahmen-/Linienvorgänger lokal unbekannt; nichts überschrieben.')
    return redisplay._patch(text,((helpers[0],HELPER),(floors[0],FLOOR)))


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
    float floorFill=coverage(distance-4.0)*(1.0-coverage(abs(distance)-.3));
    float tableFill=original*(1.0-targetDividers(local,shape.xy*.5,shape.z)*original);
    fragColor=TDOutputSwizzle(vec4(original,floorFill,tableFill,1));
}
'''
    probe.op('mask_pixel').text=info['mask']
    probe.store(SESSION,info)
    result.update(frame_strip_width_cm=4,divider_line_width_cm=.6,white_center=True,
                  floor_frame='outside original footprint',tabletop_frame='inside original footprint',
                  masks_changed=False,success_animation_changed=False)
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
        mask=images['mask_tabletop']
        original,floor_fill,table_fill=(mask[:,:,i] for i in range(3))
        region=floor_fill>1e-6
        proof=divisions.check_pattern(images['new_floor'][region,3],floor_fill[region])
        routing.require(float(table_fill.sum())>.9*float(original.sum()),'Weiße Tabletop-Innenfläche fehlt.')
        exterior=(original<=0)&(floor_fill>.99)
        routing.require(int(exterior.sum())>100,'Weißer 4-cm-Bodenrahmen außerhalb fehlt.')
        protected=(original<=0)&(floor_fill<=0)
        # Earlier thin exterior lines are allowed only in the new frame's band.
        alignment.check_floor(images['old_floor'][protected],images['new_floor'][protected])
        checks.append(dict(case='filled_center_four_cm_frame',rotation_deg=rotation,**proof))
        same=render(rotation,coincident=True)
        diagnostic=same['mask_tabletop']
        exterior=(diagnostic[:,:,0]<=0)&(diagnostic[:,:,1]>.99)
        proof=divisions.check_pattern(same['new_floor'][exterior,3],diagnostic[:,:,1][exterior])
        routing.require(int(exterior.sum())>100 and float(same['new_floor'][exterior,3].min())>.99,
                        'Äußerer weißer Rahmen bei deckungsgleichem Source/Ziel maskiert.')
        checks.append(dict(case='coincident_source_preserves_white_exterior_strip',rotation_deg=rotation,**proof))
    images=render(0)
    rows=np.flatnonzero(images['mask_tabletop'][:,600,0]>.99)
    row=int(round((int(rows[0])+int(rows[-1]))/2))
    def at(name,x): return float(images[name][row,int(x/500*images[name].shape[1]),3])
    routing.require(at('new_floor',350)>.99 and at('new_floor',380)<.5
                    and at('new_floor',382)>.99 and at('new_floor',386)<1e-6,
                    'Bodenrahmen oder Trennlinie liegt nicht bei ursprünglichem Außenrand/4 cm außen.')
    same=render(0,coincident=True)
    table=same['new_tabletop']
    def table_at(x): return float(table[table.shape[0]//2,int(x/500*table.shape[1]),3])
    routing.require(table_at(326)<.5 and table_at(328)>.99 and table_at(320)>.99,
                    'Tabletop-Rahmenstreifen nicht 4 cm innen oder Innenfläche nicht weiß.')
    checks.append(dict(case='four_cm_strip_locations_and_fine_divider',passed=True))
    for age in (0,.09,.18,1):
        images=render(33,coincident=True,phase=1,age=age)
        alignment.check_floor(images['old_tabletop'],images['new_tabletop'])
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
