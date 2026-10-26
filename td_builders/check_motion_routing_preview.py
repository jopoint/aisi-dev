"""TD checks on the isolated routing preview; restores its local enable flag."""
import builtins
import hashlib
import json
import sys


def check(resolve):
    comp = resolve('/project1/comp_aisi_motion_routing_preview')
    if comp is None or not comp.fetch('motion_routing_preview_only', False):
        raise RuntimeError('Isolierte Routing-Vorschau fehlt; nichts geändert.')
    result = {'passed': False, 'checks': [], 'saved': False,
              'production_outputs_changed': False, 'physical_validation': 'not performed'}
    flag = comp.par.Enablemotion
    if str(flag.mode) != 'ParMode.CONSTANT':
        raise RuntimeError('Vorschau-Schalter ist nicht konstant; nichts geändert.')
    previous = flag.val

    def require(ok, message):
        if not ok:
            raise RuntimeError(message)
        result['checks'].append(message)

    def digest(node):
        node.cook(force=True)
        if node.errors():
            raise RuntimeError(node.path+': '+str(node.errors()))
        array = node.numpyArray(delayed=False)
        return (tuple(array.shape), hashlib.sha256(array.tobytes()).hexdigest())

    try:
        flag.val = False
        for surface in ('floor', 'tabletop'):
            legacy, out = comp.op(surface+'_legacy'), comp.op('out_'+surface)
            require(digest(legacy) == digest(out),
                    surface+': deaktivierter Prüfzweig entspricht dem bisherigen Bild')
        mask = comp.op('tabletop_masked')
        require([n.name for n in mask.inputs] == ['tabletop_motion','mask_existing']
                and mask.par.operand.eval() == 'multiply',
                'Tabletop-Prüfzweig verwendet die bestehende Maske nach dem Motion-Content')
        for local, original in (('tabletop_masked','mask_tabletop'),
                                ('floor_with_chairs','composite_floor_with_synth_chairs')):
            copied = comp.op(local)
            source = resolve('/project1/comp_layout_proposal/'+original)
            require(all(getattr(copied.par,p).eval() == getattr(source.par,p).eval()
                        for p in ('resolutionw','resolutionh')),
                    local+': Auflösungsparameter entsprechen dem Original')
        flag.val = True
        raw = resolve('/project1/comp_io/null_osc_raw')
        mode = raw['study/mode'] if raw is not None else None
        expected = int(mode is not None and mode.eval() == 2)
        require(all(comp.op(s+'_switch').par.index.eval() == expected
                    for s in ('floor','tabletop')),
                'Lokale Umschaltung folgt dem aktuellen Study-/Tracking-/AISI-Modus')
        for surface in ('floor', 'tabletop'):
            digest(comp.op('out_'+surface))
        require(comp.op('floor_optional_chairs').par.index.eval()
                == resolve('/project1/comp_layout_proposal/switch_enable_synth_chairs_regular').par.index.eval(),
                'Chair-Auswahl folgt dem bestehenden Schalter')
        result['passed'] = True
        result['visual_mask_alignment'] = 'pending; independent simulation uses separate poses'
    except Exception as error:
        result['failure'] = str(error)
    finally:
        flag.val = previous
        result['local_enable_restored'] = bool(flag.eval()) == bool(previous)
    return result


def symbol(name):
    return (globals().get(name) or getattr(builtins, name, None)
            or getattr(sys.modules.get('__main__'), name, None))


if callable(symbol('op')):
    print(json.dumps(check(symbol('op')),ensure_ascii=False,indent=2))
