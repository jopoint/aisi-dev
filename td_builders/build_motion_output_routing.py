"""Reversible production content insertion, before original masks/calibration.

Default OFF. Sourceapproved also stays OFF until the actual source/mask
alignment has been verified. Never saves a .toe or changes projector nodes.
"""
import builtins
import copy
import hashlib
import json
import sys

REPO='C:/dev/Promotion_Prototypen/AISI'
NAME='comp_aisi_motion_output_routing'
PATH='/project1/'+NAME
LAYOUT='/project1/comp_layout_proposal/'
OUTPUT='/project1/comp_output/'
MOTION='/project1/comp_aisi_motion_v1_5/'
BRIDGE='select_aisi_motion_tabletop_content'
BASE_FLOOR=OUTPUT+'select_floor'
RAW='/project1/comp_io/null_osc_raw'
FLAG='motion_production_routing'
SURFACES=(OUTPUT+'switch_floor',OUTPUT+'switch_tabletop',OUTPUT+'switch_table_mask')
GATE=("(int(op(%r).par.Enablemotion.eval() and op(%r).par.Sourceapproved.eval() "
      "and (lambda n: n is not None and n['study/mode'] is not None "
      "and n['study/mode'].eval()==2)(op(%r)) "
      "and (lambda n: n is not None and n['state'] is not None "
      "and n['state'].eval()==0)(op(%r)) "
      "and (lambda n: n is not None and n['state'] is not None "
      "and n['state'].eval()==0)(op(%r))), absTime.frame)[0]"
      % (PATH,PATH,RAW,LAYOUT+'panel_mode',OUTPUT+'panel_mode'))


def require(ok,message):
    if not ok:
        raise RuntimeError(message)


def ref(parameter):
    value=parameter.eval()
    return value.path if hasattr(value,'path') else str(value)


def signature(node):
    pars={}
    for p in node.pars():
        mode=str(p.mode)
        pars[p.name]=[mode,str(p.val) if mode=='ParMode.CONSTANT' else None,
                      p.expr or '',p.bindExpr or '']
    result={'type':str(node.type),'inputs':[n.path for n in node.inputs],'parameters':pars}
    if str(node.type)=='text' and node.isDAT:
        result['text_sha256']=hashlib.sha256(node.text.encode('utf-8')).hexdigest()
    return result


def snapshot(resolve):
    result={}
    def visit(node):
        result[node.path]=signature(node)
        if node.isCOMP:
            for child in node.children:
                visit(child)
    for path in (LAYOUT[:-1],OUTPUT[:-1],'/project1/comp_study_visualization'):
        node=resolve(path)
        require(node is not None,'Geschützter Teilgraph fehlt: '+path)
        visit(node)
    return result


def absent_empty_table_instances(resolve,expected,missing):
    """Recognize only absent item1..5 trees in a proven empty replicator.

    Keep saved snapshots intact. Present instances are always compared strictly.
    Template, data callback and replicator recipe must match the saved snapshot.
    """
    if not missing:
        return set()
    for path in missing:
        if not path.startswith(LAYOUT):
            return set()
        name=path[len(LAYOUT):].split('/',1)[0]
        if name not in ('item1','item2','item3','item4','item5'):
            return set()
        root=LAYOUT+name
        if root not in expected or resolve(root) is not None:
            return set()
    recipe=('table_template','replicate_tables','tables_active',
            'tables_active_callbacks','replicator_callbacks')
    for name in recipe:
        path=LAYOUT+name
        node=resolve(path)
        if node is None or path not in expected or signature(node)!=expected[path]:
            return set()
    raw=resolve(RAW)
    count=raw['table/count'] if raw is not None else None
    if count is None or count.eval()!=0:
        return set()
    table=resolve(LAYOUT+'tables_active')
    header=('id','type','x','y','rot','target_x','target_y','target_rot')
    if table.numRows!=1 or table.numCols!=len(header):
        return set()
    if tuple(table[0,col].val for col in range(table.numCols))!=header:
        return set()
    replicator=resolve(LAYOUT+'replicate_tables')
    if (str(replicator.type)!='replicator'
            or ref(replicator.par.template)!=LAYOUT+'tables_active'
            or ref(replicator.par.master)!=LAYOUT+'table_template'
            or ref(replicator.par.callbacks)!=LAYOUT+'replicator_callbacks'
            or replicator.par.namefromtable.eval()!='rowindex'):
        return set()
    layout=resolve(LAYOUT[:-1])
    if any(n.name.startswith('item') and n.name[4:].isdigit() for n in layout.children):
        return set()
    return set(missing)


def assert_snapshot(resolve,expected):
    differences=[]
    missing=[]
    for path,value in expected.items():
        node=resolve(path)
        if node is None:
            missing.append(path)
        elif signature(node)!=value:
            differences.append(path)
    accepted=absent_empty_table_instances(resolve,expected,missing)
    differences.extend(path for path in missing if path not in accepted)
    require(not differences,'Unerwartete Parameter-/Verbindungsänderung: '+str(differences))


def owned_snapshot(comp,bridge):
    result={}
    for node in [comp]+list(comp.children)+[bridge]:
        result[node.path]=signature(node)
    # These two control values are intentionally user-changeable. Their
    # modes/expressions/bindings and all other local edits remain protected.
    for name in ('Enablemotion','Sourceapproved'):
        result[comp.path]['parameters'][name][1]=None
    return result


def assert_owned(resolve,comp):
    bridge=resolve(LAYOUT+BRIDGE)
    expected=comp.fetch('motion_output_owned',None)
    require(bridge is not None and isinstance(expected,dict)
            and owned_snapshot(comp,bridge)==expected,
            'Eigene Routing-Knoten wurden lokal verändert; nichts überschrieben.')


def digest(node):
    node.cook(force=True)
    require(not node.errors(),node.path+': '+str(node.errors()))
    a=node.numpyArray(delayed=False)
    return [list(a.shape),hashlib.sha256(a.tobytes()).hexdigest()]


def preflight(resolve):
    root,layout=resolve('/project1'),resolve(LAYOUT[:-1])
    require(root is not None and layout is not None,'project1/Layout fehlt; nichts geändert.')
    require(resolve(PATH) is None and layout.op(BRIDGE) is None,
            'Eigene Routing-Knoten existieren bereits; nichts überschrieben.')
    paths={
        'floor_select':LAYOUT+'select_floor_for_synth_chairs','floor_base':BASE_FLOOR,
        'chairs':LAYOUT+'composite_floor_with_synth_chairs',
        'chair_switch':LAYOUT+'switch_enable_synth_chairs_regular',
        'tabletop':LAYOUT+'null_tabletop','tabletop_base':LAYOUT+'render_tabletop',
        'mask':LAYOUT+'mask_tabletop','mask_source':LAYOUT+'null_table_mask',
        'floor_motion':MOTION+'out_floor','tabletop_motion':MOTION+'out_tabletop'}
    nodes={k:resolve(v) for k,v in paths.items()}
    require(all(n is not None for n in nodes.values()),'Erwartete Einfügeknoten fehlen; nichts geändert.')
    floor=nodes['floor_select']
    require(str(floor.type)=='select' and str(floor.par.top.mode)=='ParMode.CONSTANT'
            and ref(floor.par.top)==BASE_FLOOR,'Floor-Basis weicht ab; nichts geändert.')
    require([n.path for n in nodes['chairs'].inputs]==[floor.path,LAYOUT+'select_synth_chairs_regular']
            and [n.path for n in nodes['chair_switch'].inputs]==[floor.path,nodes['chairs'].path],
            'Chair-Komposition weicht ab; nichts geändert.')
    require(str(nodes['tabletop'].type)=='null'
            and list(nodes['tabletop'].inputs)==[nodes['tabletop_base']],
            'Unmaskierter Tabletop-Pfad weicht ab; nichts geändert.')
    require(list(nodes['mask'].inputs)==[nodes['tabletop'],nodes['mask_source']]
            and nodes['mask'].par.operand.eval()=='multiply',
            'Tabletop-Maskenreihenfolge weicht ab; nichts geändert.')
    for name,source in (('select_central_floor',LAYOUT+'null_floor_with_optional_synth_chairs'),
                        ('select_tabletop',LAYOUT+'null_tabletop_masked'),
                        ('select_table_mask',LAYOUT+'null_table_mask')):
        node=resolve(OUTPUT+name)
        require(node is not None and str(node.par.top.mode)=='ParMode.CONSTANT'
                and ref(node.par.top)==source,'Ausgabe-Select weicht ab: '+name)
    for path in SURFACES+(LAYOUT+'panel_mode',OUTPUT+'panel_mode',RAW):
        require(resolve(path) is not None,'Erforderlicher Modus-/Ausgabeknoten fehlt: '+path)
    return root,layout,nodes


def expected_installed(before,comp_path=PATH):
    expected=copy.deepcopy(before)
    expected[LAYOUT+'select_floor_for_synth_chairs']['parameters']['top'][1]=comp_path+'/out_floor'
    expected[LAYOUT+'null_tabletop']['inputs']=[LAYOUT+BRIDGE]
    return expected


def build(resolve,symbols):
    root,layout,nodes=preflight(resolve)
    before=snapshot(resolve)
    images={path:digest(resolve(path)) for path in SURFACES}
    old_floor=nodes['floor_select'].par.top.val
    comp=bridge=None
    floor_touched=table_touched=False
    try:
        comp=root.create(symbols['containerCOMP'],NAME)
        require(comp.path==PATH,'TD hat den Komponentennamen unerwartet geändert.')
        page=comp.appendCustomPage('Motion Output')
        page.appendToggle('Enablemotion',label='Neuen AISI-Content verwenden')[0].val=False
        page.appendToggle('Sourceapproved',label='Quelle und bestehende Maske abgeglichen')[0].val=False
        comp.par.display=False
        comp.nodeX,comp.nodeY=1800,-1100
        for surface in ('floor','tabletop'):
            legacy=comp.create(symbols['selectTOP'],surface+'_legacy')
            legacy.par.top=nodes[surface+'_base'].path
            motion=comp.create(symbols['selectTOP'],surface+'_motion')
            motion.par.top=nodes[surface+'_motion'].path
            # Preserve the original resolution before any mask/warp/grid.
            motion.par.outputresolution='custom'
            motion.par.resolutionw.expr='op(%r).width' % legacy.path
            motion.par.resolutionh.expr='op(%r).height' % legacy.path
            switch=comp.create(symbols['switchTOP'],surface+'_switch')
            switch.inputConnectors[0].connect(legacy)
            switch.inputConnectors[1].connect(motion)
            switch.par.index.expr=GATE
            out=comp.create(symbols['outTOP'],'out_'+surface)
            out.inputConnectors[0].connect(switch)
            digest(motion)  # Check the new branch without selecting it in production.
            require(digest(legacy)==digest(out),'Eigener Bypass ist nicht pixelgleich: '+surface)
        bridge=layout.create(symbols['selectTOP'],BRIDGE)
        bridge.par.top=PATH+'/out_tabletop'
        # These are the ONLY changes to existing nodes. Original mask inputs,
        # chair graph, output selectors, calibration, warps and blends stay put.
        floor_touched=True
        nodes['floor_select'].par.top=PATH+'/out_floor'
        table_touched=True
        nodes['tabletop'].inputConnectors[0].connect(bridge)
        assert_snapshot(resolve,expected_installed(before))
        for path,original in images.items():
            require(digest(resolve(path))==original,'Ausgabebild bei deaktiviertem Motion verändert: '+path)
        comp.store(FLAG,True)
        comp.store('motion_output_before',before)
        comp.store('motion_output_floor_reference',old_floor)
        comp.store('motion_output_owned',owned_snapshot(comp,bridge))
        return {'component':PATH,'installed':True,'enabled':False,'source_approved':False,
                'existing_nodes_changed':[nodes['floor_select'].path,nodes['tabletop'].path],
                'original_mask_operator_preserved':True,'chair_composition_preserved':True,
                'protected_graph_verified':True,'bypass_pixel_checks':len(images),
                'calibration_changed':False,'projector_transforms_changed':False,
                'saved':False,'physical_validation':'not performed',
                'status':'production insertion installed; legacy content remains selected'}
    except Exception as error:
        rollback_errors=[]
        for changed,restore in (
                (table_touched,lambda:nodes['tabletop'].inputConnectors[0].connect(nodes['tabletop_base'])),
                (floor_touched,lambda:setattr(nodes['floor_select'].par.top,'val',old_floor))):
            if changed:
                try:
                    restore()
                except Exception as rollback:
                    rollback_errors.append(str(rollback))
        if rollback_errors:
            raise RuntimeError(str(error)+'; Rückbau unvollständig, neue Knoten erhalten: '
                               +str(rollback_errors)) from error
        if bridge is not None:
            bridge.destroy()
        if comp is not None:
            comp.destroy()
        assert_snapshot(resolve,before)
        raise


def check(resolve):
    comp=resolve(PATH)
    require(comp is not None and comp.fetch(FLAG,False),'Produktive Motion-Einbindung fehlt.')
    before=comp.fetch('motion_output_before',None)
    require(isinstance(before,dict),'Rückbau-Snapshot fehlt.')
    assert_owned(resolve,comp)
    require(not comp.par.Enablemotion.eval() and not comp.par.Sourceapproved.eval(),
            'Diese Bypass-Prüfung verlangt deaktiviertes Motion und nicht freigegebene Quelle.')
    assert_snapshot(resolve,expected_installed(before))
    checks=['Nur die beiden vorgesehenen Content-Einfügepunkte geändert',
            'Bestehende Masken-, Chair- und Projektorknoten strukturell unverändert']
    for surface,path in (('floor',LAYOUT+'select_floor_for_synth_chairs'),
                          ('tabletop',LAYOUT+'null_tabletop')):
        require(comp.op(surface+'_switch').par.index.eval()==0,'Bypass-Index ist nicht null.')
        require(digest(resolve(path))==digest(comp.op(surface+'_legacy')),
                'Content-Bypass nicht pixelgleich: '+surface)
        motion=comp.op(surface+'_motion'); legacy=comp.op(surface+'_legacy')
        digest(motion)
        require((motion.width,motion.height)==(legacy.width,legacy.height),
                'Motion-Auflösung weicht ab: '+surface)
        checks.extend([surface+': Content-Bypass pixelgleich',surface+': Motion-Auflösung entspricht Original'])
    for path in SURFACES:
        digest(resolve(path))
    checks.append('Floor-/Tabletop-/Masken-Ausgabeschalter fehlerfrei')
    return {'passed':True,'checks':checks,'enabled':False,'source_approved':False,
            'saved':False,'physical_validation':'not performed','active_motion_output_tested':False}


def uninstall(resolve):
    comp=resolve(PATH)
    require(comp is not None and comp.fetch(FLAG,False),'Eigene Einbindung fehlt.')
    before=comp.fetch('motion_output_before',None)
    require(isinstance(before,dict),'Rückbau-Snapshot fehlt.')
    assert_owned(resolve,comp)
    assert_snapshot(resolve,expected_installed(before))
    bridge=resolve(LAYOUT+BRIDGE)
    require(bridge is not None,'Eigene Tabletop-Brücke fehlt.')
    comp.par.Enablemotion=False
    comp.par.Sourceapproved=False
    floor,table=resolve(LAYOUT+'select_floor_for_synth_chairs'),resolve(LAYOUT+'null_tabletop')
    old=comp.fetch('motion_output_floor_reference')
    try:
        floor.par.top=old
        table.inputConnectors[0].connect(resolve(LAYOUT+'render_tabletop'))
        assert_snapshot(resolve,before)
    except Exception:
        floor.par.top=PATH+'/out_floor'
        table.inputConnectors[0].connect(bridge)
        raise
    bridge.destroy()
    comp.destroy()
    return {'removed':True,'original_graph_restored':True,'saved':False}


def symbol(name):
    return (globals().get(name) or getattr(builtins,name,None)
            or getattr(sys.modules.get('__main__'),name,None))


if globals().get('__spec__') is None and callable(symbol('op')):
    kinds=('containerCOMP','selectTOP','switchTOP','outTOP')
    print(json.dumps(build(symbol('op'),{k:symbol(k) for k in kinds}),ensure_ascii=False,indent=2))
