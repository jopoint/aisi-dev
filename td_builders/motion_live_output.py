"""Promote the owned chair gate to live content, retaining the original mask.

Prepare while OFF; activate in a later TD frame after a fresh source check.
Only one owned switch expression changes. Original test registration remains
intact; rollback restores that expression and disables both production flags.
Never saves the project or resets the Motion engine.
"""
import copy

from td_builders import motion_output_simulation_test as test
from td_builders import check_motion_live_masks as masks

SESSION='motion_live_output_session'


def validate(resolve,comp,unused=None):
    routing=test.routing
    info=comp.fetch(SESSION,None)
    routing.require(isinstance(info,dict),'Live-Ausgabe nicht vorbereitet.')
    routing.require(not comp.par.Simulationtest.eval(),'Simulationsmaske muss deaktiviert bleiben.')
    routing.assert_snapshot(resolve,info['expected_protected'])
    routing.require(test.own_snapshot(resolve,comp)==info['expected_owned'],
                    'Live-Routing lokal verändert; nichts überschrieben.')
    routing.require(comp.fetch(test.SESSION,None)==info['original_test'],
                    'Ursprüngliche Testregistrierung wurde verändert; nichts überschrieben.')


def prepare(resolve):
    routing=test.routing
    comp=resolve(routing.PATH)
    routing.require(comp is not None and comp.fetch(SESSION,None) is None,
                    'Routing fehlt oder Live-Ausgabe bereits vorbereitet.')
    routing.require(not comp.par.Simulationtest.eval() and not comp.par.Enablemotion.eval()
                    and not comp.par.Sourceapproved.eval(),'Vorbereitung verlangt alle drei Freigaben aus.')
    previous=comp.fetch(test.SESSION,None)
    routing.require(isinstance(previous,dict) and 'original_chair_input' in previous,
                    'Registrierter Chair-Test fehlt.')
    test.validate(resolve,comp,previous)
    switch=comp.op('simulation_chairs_switch')
    routing.require(switch is not None and switch.par.index.expr==test.simulation_gate(),
                    'Chair-Schalter weicht ab; nichts überschrieben.')
    proof=masks.check(resolve)
    if not proof['passed']:
        return dict(proof,live_prepared=False)
    # Prime only the isolated chair reader; the next TD frame confirms it.
    routing.digest(resolve('/project1/comp_aisi_motion_layout_chairs/out_chairs'))
    before={p:routing.digest(resolve(p)) for p in routing.SURFACES}
    original=switch.par.index.expr
    try:
        switch.par.index.expr=test.content_gate()
        for path,pixels in before.items():
            routing.require(routing.digest(resolve(path))==pixels,'Live-Vorbereitung ändert Bypass: '+path)
        info={'original_expression':original,'original_test':copy.deepcopy(previous),
              'expected_protected':copy.deepcopy(previous['expected_protected']),
              'expected_owned':test.own_snapshot(resolve,comp),
              'mask_proof':proof,'phase':'prepared'}
        clock=routing.symbol('absTime')
        info['prepared_td_frame']=float(clock.frame) if clock is not None else None
        comp.store(SESSION,info)
        validate(resolve,comp)
        return {'passed':True,'live_prepared':True,'source_approved':False,'enabled':False,
                'bypass_pixel_checks':len(before),'original_mask_selected':True,
                'prepared_td_frame':info['prepared_td_frame'],'saved':False,
                'next':'activate in a later TD frame; real table must stay still for the pose check'}
    except Exception:
        switch.par.index.expr=original
        comp.unstore(SESSION)
        raise


def indices(comp):
    return {s:int(comp.op(s+'_switch').par.index.eval())
            for s in ('floor','tabletop','simulation_mask','simulation_chairs')}


def activate(resolve):
    routing=test.routing
    comp=resolve(routing.PATH)
    routing.require(comp is not None,'Motion-Routing fehlt.')
    validate(resolve,comp)
    info=comp.fetch(SESSION)
    routing.require(info['phase']=='prepared','Live-Ausgabe nicht in Vorbereitungsphase.')
    routing.require(not comp.par.Enablemotion.eval() and not comp.par.Sourceapproved.eval(),
                    'Live-Flags vor Aktivierung verändert.')
    clock=routing.symbol('absTime')
    if clock is not None and float(clock.frame)==info['prepared_td_frame']:
        return {'passed':False,'status':'Auf späteren TD-Frame warten.','saved':False}
    fresh=masks.current_sources(resolve)  # No GPU digests before enabling.
    if not fresh['passed']:
        return fresh
    old=info['mask_proof']['live_stream']
    current=fresh['live_stream']
    routing.require(current['signature'][0]==old['signature'][0]
                    and current['signature']!=old['signature']
                    and current['layout']==old['layout'] and current['ids']==old['ids'],
                    'Quelle oder Vorschlag seit Pixelprüfung verändert; neu vorbereiten nach Rücknahme.')
    try:
        comp.par.Sourceapproved=True
        comp.par.Enablemotion=True
        selected=indices(comp)
        routing.require(selected['floor']==selected['tabletop']==selected['simulation_chairs']
                        and selected['simulation_mask']==0,'Live-Content/Chairs oder Originalmaske falsch gewählt.')
        info['phase']='active'
        comp.store(SESSION,info)
        return {'passed':True,'source_approved':True,'indices':selected,
                'active_in_current_mode':selected['floor']==1,'live_stream':current,
                'original_mask_selected':True,'saved':False,
                'physical_validation':'not performed','next':'run separate verify after TD resumes'}
    except Exception:
        comp.par.Enablemotion=False
        comp.par.Sourceapproved=False
        raise


def verify(resolve):
    routing=test.routing
    comp=resolve(routing.PATH)
    routing.require(comp is not None,'Motion-Routing fehlt.')
    try:
        validate(resolve,comp)
        proof=masks.check(resolve,validator=validate,allow_live=True)
        routing.require(proof['passed'],'Aktueller Live-Maskenabgleich nicht bestanden.')
        selected=indices(comp)
        routing.require(selected['floor']==selected['tabletop']==selected['simulation_chairs']
                        and selected['simulation_mask']==0,'Gemeinsames Live-Gatter/Originalmaske verletzt.')
        for path in routing.SURFACES:
            routing.digest(resolve(path))
        routing.require(routing.digest(resolve(routing.LAYOUT+'null_table_mask'))==
                        routing.digest(resolve(routing.LAYOUT+'reorder_table_mask')),
                        'Produktiver Maskeneingang entspricht nicht Originalmaske.')
        chair_comp=resolve('/project1/comp_aisi_motion_layout_chairs')
        routing.digest(chair_comp.op('out_chairs'))
        # GPU readback can exceed the stream timeout within one TD frame.
        # Reacquire the camera after all readbacks, then cook the chair state
        # explicitly: an out TOP cook need not recook its cached Script TOP.
        pixel_live=proof['live_stream']
        # Do not compare newly received poses to same-frame cached geometry.
        # Pose/raster proof remains attached to pixel_live, sampled before GPU work.
        current=masks.current_stream(resolve)
        routing.require(current['passed'],'Kameraquelle nach GPU-Prüfung nicht frisch.')
        live=current['live_stream']
        routing.require(live['layout']==pixel_live['layout'] and live['ids']==pixel_live['ids'],
                        'Quelle oder Vorschlag während GPU-Prüfung verändert.')
        state=chair_comp.op('chair_state')
        routing.require(state is not None,'Chair-State fehlt.')
        state.cook(force=True)
        routing.require(not state.errors(),'Chair-State fehlerhaft: '+str(state.errors()))
        chair_status=chair_comp.fetch('chair_live_status',{}) or {}
        routing.require(chair_status.get('fresh') and chair_status.get('layout')==live['layout']
                        and chair_status.get('signature')==live['signature'],
                        'Chair-Stream nicht frisch oder nicht an denselben Vorschlag gebunden.')
        raw=resolve(routing.RAW)
        expected=int(raw['aisi_motion/chairs/count'].eval()) if raw['aisi_motion/chairs/visible'].eval() else 0
        routing.require(chair_status.get('visible_chairs')==expected,'Sichtbare Chair-Menge weicht vom Vorschlag ab.')
        proof.update({'mask_pixel_signature':pixel_live['signature'],
                      'live_stream':live,
                      'indices':selected,'original_mask_selected':True,
                      'chair_stream':chair_status,
                      'active_in_current_mode':selected['floor']==1})
        return proof
    except Exception:
        # Disable content without changing any local wiring on failed proof.
        comp.par.Enablemotion=False
        comp.par.Sourceapproved=False
        raise


def rollback(resolve):
    routing=test.routing
    comp=resolve(routing.PATH)
    routing.require(comp is not None,'Motion-Routing fehlt.')
    validate(resolve,comp)
    info=comp.fetch(SESSION)
    comp.par.Enablemotion=False
    comp.par.Sourceapproved=False
    comp.op('simulation_chairs_switch').par.index.expr=info['original_expression']
    test.validate(resolve,comp,comp.fetch(test.SESSION))
    comp.unstore(SESSION)
    return {'passed':True,'live_extension_removed':True,'source_approved':False,
            'indices':indices(comp),'original_test_registration_preserved':True,'saved':False}
