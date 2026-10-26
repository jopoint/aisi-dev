"""Read existing mask geometry and pose bindings; no writes or forced cooks."""
import builtins
import json
import sys

BASE = '/project1/comp_layout_proposal/'


def value(v):
    if hasattr(v, 'path'):
        return v.path
    if isinstance(v, (list, tuple)):
        return [value(item) for item in v]
    if isinstance(v, (str, int, float, bool)) or v is None:
        return v
    return str(v)


def parameters(node, names):
    return {p.name:{'value':value(p.eval()), 'expression':p.expr,
                    'mode':str(p.mode), 'binding':p.bindExpr}
            for p in node.pars() if p.name in names}


def inspect(resolve):
    report={'read_only':True, 'items':[], 'missing':[], 'rendered_masks':[]}
    for name in ('tables_active','table_types'):
        node=resolve(BASE+name)
        if node is not None and node.isDAT:
            report[name]=[[cell.val for cell in node.row(i)][:16]
                          for i in range(min(node.numRows,8))]
    for name in ('render_table_mask','cam1'):
        node=resolve(BASE+name)
        if node is None:
            report['missing'].append(BASE+name)
            continue
        report[name]=parameters(node,('geometry','camera','projection','orthowidth',
            'tx','ty','tz','rx','ry','rz','resolutionw','resolutionh'))
        if name == 'render_table_mask':
            geos=node.par.geometry.eval()
            if isinstance(geos,(list,tuple)):
                seen=set()
                for geo in geos:
                    if not hasattr(geo,'path') or geo.path in seen:
                        continue
                    seen.add(geo.path)
                    report['rendered_masks'].append({'path':geo.path,
                        'render':bool(geo.render),
                        'inputs':[source.path for source in geo.inputs],
                        'parameters':parameters(geo,('tx','ty','tz','rx','ry','rz','sx','sy','sz'))})
    raw=resolve('/project1/comp_io/null_osc_raw')
    report['live_occupancy']={}
    if raw is not None:
        names=['vision/table/count','table/count','study/mode']
        names += ['vision/table/%d/%s' % (i,key) for i in range(5)
                  for key in ('available','x','y','rot')]
        for name in names:
            channel=raw[name]
            if channel is not None:
                report['live_occupancy'][name]=channel.eval()
    for i in range(1,6):
        item=resolve(BASE+'item%d' % i)
        if item is None:
            continue
        entry={'path':item.path, 'parameters':parameters(item,(
            'X','Y','Rot','Targetx','Targety','Targetrot','Tabletype',
            'Tableid','Tableindex','Index','Width','Height'))}
        # One instance establishes shape axes as well as source/mask transforms.
        if i == 1:
            entry['geometry']=[]
            for role in ('table_source_geo','table_target_floor_geo','table_mask_geo'):
                geo=item.op(role)
                if geo is None:
                    report['missing'].append(item.path+'/'+role)
                    continue
                description={'path':geo.path,'parameters':parameters(geo,(
                    'tx','ty','tz','rx','ry','rz','sx','sy','sz','Tabletype')),
                    'render_sops':[]}
                for sop in geo.children:
                    if not getattr(sop,'isSOP',False) or not getattr(sop,'render',False):
                        continue
                    shape={'path':sop.path,'type':str(sop.type),
                           'parameters':parameters(sop,('sizex','sizey','sizez',
                                                       'tx','ty','rz','callbacks'))}
                    try:
                        points=[(float(p.P[0]),float(p.P[1]),float(p.P[2]))
                                for p in sop.points]
                        shape['point_count']=len(points)
                        shape['bounds']=([[min(p[axis] for p in points),
                                           max(p[axis] for p in points)]
                                          for axis in range(3)] if points else None)
                    except Exception as error:
                        shape['bounds_unavailable']=str(error)
                    description['render_sops'].append(shape)
                entry['geometry'].append(description)
        report['items'].append(entry)
    return report


def symbol(name):
    return (globals().get(name) or getattr(builtins,name,None)
            or getattr(sys.modules.get('__main__'),name,None))


if callable(symbol('op')):
    print(json.dumps(inspect(symbol('op')),ensure_ascii=False,indent=2))
