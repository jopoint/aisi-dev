"""Keep only the outer target division and reduce its width to 0.6 cm."""
from td_builders import update_motion_target_divisions as divisions
from td_builders import update_motion_feedback_brightness as transaction
from td_builders import update_motion_alignment_guides as alignment
from td_builders import update_motion_redisplay as redisplay
from td_builders import build_motion_output_routing as routing

PROBE='/project1/comp_aisi_motion_target_single_line_check'
SESSION='motion_target_single_line_probe'
BACKUP='motion_target_single_line_backup'
OLD=divisions.HELPER
NEW='''float targetDividers(vec2 local, vec2 halfSize, float corner) {
    vec2 ringHalf=halfSize-vec2(10.0);
    if(min(ringHalf.x,ringHalf.y)<=.3) return 0.0;
    float radius=max(0.0,min(corner,min(ringHalf.x,ringHalf.y)-.3));
    float distance=roundedRect(local,ringHalf,radius);
    return coverage(abs(distance)-.3);
}
'''


def patch_shader(text):
    return redisplay._patch(text,((OLD,NEW),))


def prepare(resolve):
    result=transaction.prepare(resolve,probe_path=PROBE,session=SESSION,backup=BACKUP,patcher=patch_shader)
    probe=resolve(PROBE)
    info=dict(probe.fetch(SESSION))
    info['mask']=info['new'].split('void main() {')[0]+'''void main() {
    vec2 p=vec2(vUV.x,1.0-vUV.y)*500.0;
    vec4 target=datum(1,0),shape=datum(4,0);
    vec2 local=rotate2(p-target.xy,-target.z);
    float outer=coverage(roundedRect(local,shape.xy*.5,shape.z));
    float lines=targetDividers(local,shape.xy*.5,shape.z)*outer;
    fragColor=TDOutputSwizzle(vec4(outer,lines,outer*(1.0-lines),1));
}
'''
    probe.op('mask_pixel').text=info['mask']
    probe.store(SESSION,info)
    result.update(division_insets_cm=[10],line_width_cm=.6,white_fill_preserved=True,
                  outer_footprint_changed=False,surfaces=['floor','tabletop'])
    return result


def gpu_check(probe):
    import numpy as np
    from td_builders.motion_design import WIDTH,DEPTH,CORNER
    checks=[]
    def render(rotation=0,overlap=False,feedback=False,phase=0,age=0,visibility=1):
        data=np.zeros((6,6,4),np.float32)
        data[0,0]=(250,250,0,1) if overlap else (100,100,0,1)
        data[0,1]=(275,250,rotation,1) if overlap else (300,300,rotation,1)
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
        outer,lines,fill=(images['mask_tabletop'][:,:,i] for i in range(3))
        inside=outer>=.999999
        outside=outer<=0
        routing.require(float(fill.sum())>.95*float(outer.sum()) and float(lines.sum())>100,
                        'Einzelne dünne Linie oder weiße Füllung fehlt.')
        proof=divisions.check_pattern(images['new_floor'][inside,3],fill[inside])
        for surface in ('floor','tabletop'):
            alignment.check_floor(images['old_'+surface][outside],images['new_'+surface][outside])
        checks.append(dict(case='single_rounded_line',rotation_deg=rotation,
                           outer_footprint_preserved=True,white_fraction=float(fill.sum()/outer.sum()),**proof))
    images=render()
    rows=np.flatnonzero(images['mask_tabletop'][:,600,0]>.99)
    row=int(round((int(rows[0])+int(rows[-1]))/2))
    def alpha(name,x): return float(images[name][row,int(x/500*images[name].shape[1]),3])
    for x in (350,360):
        routing.require(alpha('old_floor',x)<.2 and alpha('new_floor',x)>.99,
                        'Eine innere Linie wurde nicht entfernt.')
    routing.require(alpha('old_floor',370)<alpha('new_floor',370)<.65,
                    'Äußerste Linie fehlt oder ist nicht dünner.')
    checks.append(dict(case='two_inner_lines_removed_outer_line_thinner',passed=True))
    for age in (0,.09,.18,1):
        success=render(33,overlap=True,phase=1,age=age)
        alignment.check_floor(success['old_tabletop'],success['new_tabletop'])
    full=render(33,overlap=True,feedback=True)
    half=render(33,overlap=True,feedback=True,visibility=.5)
    green=full['new_tabletop'][:,:,1]-np.maximum(full['new_tabletop'][:,:,0],full['new_tabletop'][:,:,2])
    routing.require(float(green.max())>.1,'Feedback verschwunden.')
    for surface in ('floor','tabletop'):
        routing.require(float(np.max(np.abs(full['new_'+surface]*.5-half['new_'+surface])))<=1e-6,
                        'Wiedereinblendung verändert.')
    checks.append(dict(case='feedback_success_redisplay_preserved',passed=True))
    return checks


def install(resolve):
    return transaction.install(resolve,probe_path=PROBE,session=SESSION,backup=BACKUP,check=gpu_check)


def rollback(resolve):
    return transaction.rollback(resolve,backup=BACKUP)
