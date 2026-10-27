"""Temporary manual comparison of target surface with/without its divider."""
import hashlib

from td_builders import update_motion_navigation_shadow as shadow
from td_builders import build_motion_output_routing as routing

SESSION='motion_divider_visibility_preview'
VISIBLE='            float targetLines=targetDividers(rotate2(p-target.xy,-target.z),halfSize,shape.z)*targetMask;'
HIDDEN='            float targetLines=0.0; // Temporary divider comparison; restore via comparison helper.'
DEFAULT='            float targetLines=0.0; // Accepted default: solid target surface without divider.'
DEFAULT_BACKUP='motion_solid_target_default_backup'


def _hash(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def _apply(resolve,comp,text):
    pixel=comp.op('motion_pixel')
    before=pixel.text
    engine,reader=comp.fetch('motion_engine',None),comp.fetch('motion_osc_reader',None)
    revision=getattr(engine,'revision',None)
    try:
        pixel.text=text
        for name in ('render_floor','render_tabletop','render_preview'):
            routing.digest(comp.op(name))
        shadow._validate(resolve)
        routing.require(comp.fetch('motion_engine',None) is engine
                        and comp.fetch('motion_osc_reader',None) is reader
                        and getattr(engine,'revision',None)==revision,
                        'Engine/Reader/Revision während Vergleich verändert.')
    except Exception:
        pixel.text=before
        raise


def hide(resolve):
    comp=shadow._validate(resolve)
    pixel=comp.op('motion_pixel')
    existing=comp.fetch(SESSION,None)
    if existing is not None:
        routing.require(isinstance(existing,dict) and _hash(pixel.text)==existing.get('hidden_sha256'),
                        'Vorhandener Vergleich lokal verändert; nichts überschrieben.')
        return dict(passed=True,divider_visible=False,already_hidden=True,saved=False)
    old=pixel.text
    routing.require(old.count(VISIBLE)==1 and HIDDEN not in old,
                    'Lokale Trennlinien-Komposition unbekannt; nichts überschrieben.')
    new=old.replace(VISIBLE,HIDDEN,1)
    _apply(resolve,comp,new)
    comp.store(SESSION,dict(old=old,old_sha256=_hash(old),hidden_sha256=_hash(new)))
    return dict(passed=True,divider_visible=False,temporary=True,saved=False,
                engine_reset=False,targets_changed=False,masks_changed=False)


def show(resolve):
    comp=shadow._validate(resolve)
    info=comp.fetch(SESSION,None)
    routing.require(isinstance(info,dict),'Keine eigene Vergleichssicherung vorhanden.')
    routing.require(_hash(comp.op('motion_pixel').text)==info.get('hidden_sha256')
                    and _hash(info['old'])==info.get('old_sha256'),
                    'Shader/Sicherung nach Ausblenden verändert; nichts überschrieben.')
    _apply(resolve,comp,info['old'])
    comp.unstore(SESSION)
    return dict(passed=True,divider_visible=True,restored=True,saved=False,
                engine_reset=False,targets_changed=False,masks_changed=False)


def adopt_as_default(resolve):
    comp=shadow._validate(resolve)
    pixel=comp.op('motion_pixel')
    existing=comp.fetch(DEFAULT_BACKUP,None)
    if existing is not None:
        routing.require(isinstance(existing,dict) and _hash(pixel.text)==existing.get('default_sha256'),
                        'Standardshader nach Übernahme verändert; nichts überschrieben.')
        return dict(passed=True,divider_visible=False,standard=True,already_adopted=True,saved=False)
    preview=comp.fetch(SESSION,None)
    if preview is not None:
        routing.require(isinstance(preview,dict) and _hash(pixel.text)==preview.get('hidden_sha256')
                        and _hash(preview['old'])==preview.get('old_sha256')
                        and pixel.text.count(HIDDEN)==1,
                        'Vergleich/Sicherung lokal verändert; nichts überschrieben.')
        old_visible=preview['old']
        new=pixel.text.replace(HIDDEN,DEFAULT,1)
    else:
        routing.require(pixel.text.count(VISIBLE)==1 and HIDDEN not in pixel.text and DEFAULT not in pixel.text,
                        'Keine bekannte Trennlinienfassung für Standardübernahme.')
        old_visible=pixel.text
        new=pixel.text.replace(VISIBLE,DEFAULT,1)
    _apply(resolve,comp,new)
    comp.store(DEFAULT_BACKUP,dict(old_visible=old_visible,old_sha256=_hash(old_visible),
                                  default_sha256=_hash(new)))
    if preview is not None: comp.unstore(SESSION)
    return dict(passed=True,divider_visible=False,standard=True,temporary_comparison_closed=True,
                saved=False,engine_reset=False,targets_changed=False,masks_changed=False)


def restore_previous_divider(resolve):
    comp=shadow._validate(resolve)
    info=comp.fetch(DEFAULT_BACKUP,None)
    routing.require(isinstance(info,dict) and _hash(comp.op('motion_pixel').text)==info.get('default_sha256')
                    and _hash(info['old_visible'])==info.get('old_sha256'),
                    'Standard/Sicherung lokal verändert oder nicht vorhanden; nichts überschrieben.')
    _apply(resolve,comp,info['old_visible'])
    comp.unstore(DEFAULT_BACKUP)
    return dict(passed=True,divider_visible=True,restored=True,saved=False)
