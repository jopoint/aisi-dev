"""Tie existing chair rendering to the verified visual reveal, without moving chairs."""
import copy
import hashlib

from td_builders import build_motion_output_routing as routing
from td_builders import motion_live_output as live

CHAIRS = '/project1/comp_aisi_motion_layout_chairs'
PROBE = '/project1/comp_aisi_motion_chair_reveal_check'
SESSION = 'motion_chair_reveal_probe'
BACKUP = 'motion_chair_reveal_backup'
OLD = '    vec4 clock=datum(0,5);'
NEW = OLD + '''
    vec4 visualReveal=datum(1,5);
    if(visualReveal.z>.5) {
        if(visualReveal.y<.5) {
            fragColor=TDOutputSwizzle(vec4(0));
            return;
        }
        clock.y=visualReveal.x;
    }'''


def patch_shader(text):
    if text.count(NEW) == 1:
        return text
    routing.require(text.count(OLD) == 1 and 'visualReveal' not in text,
                    'Chair-Shader lokal abweichend; nichts überschrieben.')
    return text.replace(OLD,NEW,1)


def validate(resolve):
    live.validate(resolve,resolve(routing.PATH))
    comp = resolve(CHAIRS)
    routing.require(comp is not None and comp.op('chair_pixel') is not None,'Chair-Komponente fehlt.')
    owned = comp.fetch('chair_owned',None)
    routing.require(isinstance(owned,dict),'Chair-Schutzsnapshot fehlt.')
    routing.assert_snapshot(resolve,owned)
    motion = resolve(routing.MOTION[:-1])
    routing.require('motion_visual_reveal' in motion.op('motion_runtime').text and
                    'clock.y=visualReveal.x;' in motion.op('motion_pixel').text,
                    'Verifizierte visuelle Reveal-Uhr fehlt.')
    return comp


def prepare(resolve):
    import numpy as np
    comp = validate(resolve)
    routing.require(resolve(PROBE) is None and comp.fetch(BACKUP,None) is None,'Chair-Reveal-Probe/Sicherung existiert bereits.')
    old = comp.op('chair_pixel').text
    new = patch_shader(old)
    routing.require(old != new,'Chair-Reveal bereits installiert.')
    kinds = {name:routing.symbol(name) for name in ('containerCOMP','scriptTOP','textDAT','glslTOP')}
    routing.require(all(kinds.values()),'Benötigter TD-Operatortyp fehlt.')
    probe = resolve('/project1').create(kinds['containerCOMP'],PROBE.rsplit('/',1)[1])
    try:
        probe.store(SESSION,dict(old=old,new=new,owned=copy.deepcopy(comp.fetch('chair_owned'))))
        probe.store('motion_state',np.zeros((6,6,4),np.float32))
        probe.store('chair_state',np.zeros((1,15,4),np.float32))
        callbacks = probe.create(kinds['textDAT'],'state_callbacks')
        callbacks.text = "def onCook(scriptOp):\n    scriptOp.copyNumpyArray(scriptOp.parent().fetch(scriptOp.name))\n"
        for name in ('motion_state','chair_state'):
            state = probe.create(kinds['scriptTOP'],name)
            state.par.callbacks = callbacks.path
            fmt = getattr(state.par,'format',None)
            if fmt is None: fmt = getattr(state.par,'pixelformat',None)
            routing.require(fmt is not None,'Float-State-Format fehlt.')
            fmt.val = 'rgba32float'
        for version,text in (('old',old),('new',new)):
            pixel = probe.create(kinds['textDAT'],version+'_pixel')
            pixel.text = text
            render = probe.create(kinds['glslTOP'],version+'_render')
            render.inputConnectors[0].connect(probe.op('motion_state'))
            render.inputConnectors[1].connect(probe.op('chair_state'))
            render.par.pixeldat = pixel.path
            render.par.outputresolution = 'custom'
            render.par.resolutionw = render.par.resolutionh = 1000
        validate(resolve)
        return dict(prepared=True,probe=PROBE,production_shader_changed=False,
                    chairs_moved=False,saved=False,next='install in a separate Textport entry; GPU proof first')
    except Exception:
        probe.destroy()
        raise


def gpu_check(probe):
    import numpy as np
    from td_builders.motion_design import WIDTH,DEPTH,CORNER
    from td_builders.update_motion_alignment_guides import check_floor
    chairs = np.zeros((1,15,4),np.float32)
    for i,(x,y) in enumerate(((80,250),(180,250),(250,100),(250,250),(350,350),(420,250))):
        chairs[0,i] = (x,y,25,1)
    probe.store('chair_state',chairs)
    probe.op('chair_state').cook(force=True)
    def image(version,age,visual_age,ready,managed):
        state = np.zeros((6,6,4),np.float32)
        state[0,0] = (100,100,33,1)
        state[0,4] = (WIDTH,DEPTH,CORNER,0)
        state[5,0] = (10,age,1,1)
        state[5,1] = (visual_age,int(ready),int(managed),0)
        probe.store('motion_state',state)
        probe.op('motion_state').cook(force=True)
        render = probe.op(version+'_render')
        routing.digest(render)
        return render.numpyArray(delayed=False).copy()
    checks = []
    for age in (0,.5,1.5,2.9,3.1):
        hidden = image('new',4,age,False,True)
        routing.require(np.isfinite(hidden).all() and np.count_nonzero(hidden) == 0,'Chairs vor Reveal sichtbar.')
        reference = image('old',age,0,False,False)
        visible = image('new',4,age,True,True)
        precision = check_floor(reference,visible)
        if age > 0:
            routing.require(np.max(reference)>.1,'Leerer Chair-Referenzfall.')
        legacy = image('new',4,age,False,False)
        check_floor(image('old',4,0,False,False),legacy)
        checks.append(dict(visual_age_seconds=age,hidden_until_approved=True,
                           synchronized_reveal_rgba8_equal=True,legacy_unchanged=True,**precision))
    return checks


def install(resolve):
    comp = validate(resolve)
    probe = resolve(PROBE)
    routing.require(probe is not None,'Zuerst prepare aufrufen.')
    info = probe.fetch(SESSION,None)
    routing.require(isinstance(info,dict),'Eigene Prüfregistrierung fehlt.')
    pixel = comp.op('chair_pixel')
    routing.require(pixel.text == info['old'] and comp.fetch('chair_owned') == info['owned'],
                    'Chair-Shader/Sicherung seit Vorbereitung verändert.')
    for version in ('old','new'):
        routing.require(probe.op(version+'_pixel').text == info[version],'Prüfshader lokal verändert.')
    checks = gpu_check(probe)
    motion = resolve(routing.MOTION[:-1])
    engine, reader = motion.fetch('motion_engine'),comp.fetch('chair_reader',None)
    revision, started = engine.revision,engine.started
    expected = copy.deepcopy(info['owned'])
    routing.require('text_sha256' in expected[pixel.path],'Chair-DAT-Texthash fehlt.')
    expected[pixel.path]['text_sha256'] = hashlib.sha256(info['new'].encode()).hexdigest()
    try:
        pixel.text = info['new']
        routing.digest(comp.op('out_chairs'))
        routing.assert_snapshot(resolve,expected)
        comp.store('chair_owned',expected)
        validate(resolve)
        routing.require(motion.fetch('motion_engine') is engine and comp.fetch('chair_reader',None) is reader
                        and engine.revision == revision and engine.started == started,'Engine/Reader/Revision verändert.')
    except Exception:
        pixel.text = info['old']
        comp.store('chair_owned',info['owned'])
        raise
    comp.store(BACKUP,dict(old=info['old'],owned=info['owned'],expected=expected))
    probe.destroy()
    return dict(passed=True,gpu_checks=checks,chairs_moved=False,engine_reset=False,
                revision_changed=False,masks_changed=False,saved=False,
                next='activate proposal in UI; chairs must appear only as the shared wave reaches them')


def rollback(resolve):
    comp = validate(resolve)
    info = comp.fetch(BACKUP,None)
    routing.require(isinstance(info,dict) and comp.fetch('chair_owned') == info['expected'],'Eigene Chair-Reveal-Sicherung fehlt oder verändert.')
    comp.op('chair_pixel').text = info['old']
    comp.store('chair_owned',info['owned'])
    comp.unstore(BACKUP)
    validate(resolve)
    return dict(restored=True,chairs_moved=False,revision_changed=False,saved=False)
