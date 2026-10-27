"""Add one owned Execute DAT component; never save, replace or rewire the graph."""
import hashlib
from pathlib import Path

from td_builders import motion_live_output as live

PATH = '/project1/comp_aisi_motion_auto_approval'
MARK = 'motion_auto_approval_owned'


def callback_text(repo):
    return '''import sys
for folder in %r:
    if folder not in sys.path:
        sys.path.insert(0, folder)

def safe_off():
    c = op(%r)
    if c is not None:
        c.par.Enablemotion = False
        c.par.Sourceapproved = False

def onStart():
    safe_off()
    me.parent().store('approval_runtime', None)

def onFrameStart(frame):
    try:
        from td_builders import motion_auto_approval
        motion_auto_approval.tick(op, me.parent(), absTime.frame)
    except Exception as error:
        safe_off()
        me.parent().store('approval_status', dict(approved=False, message=str(error)))
''' % ((str(repo), str(repo/'src')), live.test.routing.PATH)


def prepare(resolve, symbols):
    routing = live.test.routing
    routing.require(resolve(PATH) is None, 'Auto-Freigabe existiert bereits; nichts überschrieben.')
    comp = resolve(routing.PATH)
    routing.require(comp is not None, 'Motion-Routing fehlt.')
    live.validate(resolve, comp)
    repo = Path(__file__).resolve().parents[1]
    source = callback_text(repo)
    compile(source, PATH+'/callbacks', 'exec')
    owner = resolve('/project1').create(symbols['containerCOMP'], PATH.rsplit('/', 1)[1])
    try:
        owner.appendCustomPage('Motion').appendToggle('Enabled')[0].val = False
        node = owner.create(symbols['executeDAT'], 'callbacks')
        node.par.active = False
        node.text = source
        for name in ('start', 'framestart'):
            routing.require(getattr(node.par, name, None) is not None, 'Execute-DAT-Parameter fehlt: '+name)
            getattr(node.par, name).val = True
        owner.store(MARK, hashlib.sha256(source.encode('utf-8')).hexdigest())
        owner.storeStartupValue('approval_runtime', None)
        return dict(prepared=True, component=PATH, armed=False, production_outputs_changed=False,
                    calibration_changed=False, saved=False, next='install in a separate Textport entry')
    except Exception:
        owner.destroy()
        raise


def owned(resolve):
    owner = resolve(PATH)
    live.test.routing.require(owner is not None, 'Eigener Auto-Freigabe-Baustein fehlt.')
    node = owner.op('callbacks')
    live.test.routing.require(len(owner.children) == 1 and node is not None,
                             'Eigener Baustein enthält zusätzliche lokale Knoten; nichts überschrieben.')
    live.test.routing.require(node is not None and owner.fetch(MARK, None) ==
                             hashlib.sha256(node.text.encode('utf-8')).hexdigest(),
                             'Eigener Callback wurde verändert; nichts überschrieben.')
    return owner, node


def install(resolve):
    from td_builders import motion_auto_approval as runtime
    owner, node = owned(resolve)
    comp = resolve(live.test.routing.PATH)
    live.validate(resolve, comp)
    runtime.reset(resolve, owner)
    owner.par.Enabled = True
    node.par.active = True
    return dict(installed=True, automatic_approval_armed=True, source_approved=False,
                saved=False, next='wait for separate TD frames, then read status; save manually after validation')


def status(resolve):
    owner, node = owned(resolve)
    return dict(component=PATH, enabled=bool(owner.par.Enabled.eval()),
                callback_active=bool(node.par.active.eval()),
                status=owner.fetch('approval_status', None), saved=False)


def rollback(resolve):
    from td_builders import motion_auto_approval as runtime
    owner, node = owned(resolve)
    node.par.active = False
    runtime.disable(resolve)
    owner.destroy()
    return dict(removed=True, source_approved=False, calibration_changed=False, saved=False)
