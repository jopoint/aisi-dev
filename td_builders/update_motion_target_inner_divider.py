"""One thin inner target divider on both surfaces; no exterior floor frame."""
from td_builders import update_motion_target_equal_bands as bands
from td_builders import update_motion_feedback_brightness as transaction
from td_builders import update_motion_alignment_guides as alignment
from td_builders import update_motion_target_divisions as divisions
from td_builders import update_motion_redisplay as redisplay
from td_builders import build_motion_output_routing as routing

PROBE='/project1/comp_aisi_motion_target_inner_divider_check'
SESSION='motion_target_inner_divider_probe'
BACKUP='motion_target_inner_divider_backup'
HELPER='''float targetDividers(vec2 local, vec2 halfSize, float corner) {
    // White rim: 2.5 cm. Divider: 0.4 cm, entirely inside the original target.
    float distance=roundedRect(local,halfSize,corner);
    return coverage(abs(distance+2.7)-.2);
}
'''
FLOOR='            vec4 f=white(targetFill);'


def patch_shader(text):
    return redisplay._patch(text,((bands.HELPER,HELPER),(bands.FLOOR,FLOOR)))


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
    float line=targetDividers(local,shape.xy*.5,shape.z)*original;
    float fill=original*(1.0-line);
    float previousExterior=max(0.0,coverage(distance-2.5)-original);
    fragColor=TDOutputSwizzle(vec4(original,line,fill,previousExterior));
}
'''
    probe.op('mask_pixel').text=info['mask']
    probe.store(SESSION,info)
    result.update(divider_width_cm=.4,white_rim_width_cm=2.5,divider_center_inset_cm=2.7,
                  surfaces=['floor','tabletop'],exterior_floor_frame=False,masks_changed=False,
                  white_center=True,alignment_bar_width_cm=2.5)
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
        original,line,fill,previous_exterior=(images['mask_tabletop'][:,:,i] for i in range(4))
        inside=original>=.999999
        proof=divisions.check_pattern(images['new_floor'][inside,3],fill[inside])
        routing.require(float(fill.sum())>.95*float(original.sum()) and int((line>.1).sum())>100,
                        'Dünne innere Linie oder weiße Füllung fehlt.')
        exterior=(original<=0)&(previous_exterior>.99)
        routing.require(int(exterior.sum())>100 and float(images['new_floor'][exterior,3].max())<1e-6,
                        'Zusätzlicher Boden-Außenrahmen noch vorhanden.')
        routing.require(float(line[original<=0].max())==0,'Neue Trennlinie liegt außerhalb Zielfläche.')
        protected=(original<=0)&(previous_exterior<=0)
        alignment.check_floor(images['old_floor'][protected],images['new_floor'][protected])
        alignment.check_floor(images['old_tabletop'][original<=0],images['new_tabletop'][original<=0])
        checks.append(dict(case='thin_inner_divider_no_exterior_frame',rotation_deg=rotation,
                           divider_width_cm=.4,**proof))
        same=render(rotation,coincident=True)
        band=(same['mask_tabletop'][:,:,0]<=0)&(same['mask_tabletop'][:,:,3]>.99)
        routing.require(float(same['new_floor'][band,3].max())<1e-6,
                        'Bei deckungsgleichen Posen verbleibt ein zusätzlicher Außenrahmen.')
    same=render(0,coincident=True)
    table=same['new_tabletop']
    def table_at(x): return float(table[table.shape[0]//2,int(x/500*table.shape[1]),3])
    routing.require(table_at(324)>.99 and table_at(327)<.5 and table_at(329)>.99,
                    'Tabletop-Linie oder weiße Bereiche liegen nicht richtig.')
    checks.append(dict(case='tabletop_inner_line_and_white_center',passed=True))
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
