"""Fehlende AISI-Sources und zugehörige Pfeile ausblenden; manuelle Reparatur."""

ROOT = '/project1/comp_layout_proposal'
BACKUP_KEY = 'aisi_source_presence_before_repair'
MARKER = '# aisi_source_presence_v1\n'
ROLES = ('table_source_geo', 'table_motion_line_floor_geo', 'table_motion_line_tabletop_geo')


def gated_expression(base):
    if base.startswith(MARKER):
        return base
    return MARKER + '''float(bool((
%s
)) and (lambda raw, index: raw is None or raw['table/%%d/source_available' %% index] is None or raw['table/%%d/source_available' %% index].eval() == 1)(op('/project1/comp_io/null_osc_raw'), int(parent().name[4:]) - 1 if parent().name.startswith('item') and parent().name[4:].isdigit() else -1))''' % base


def _restore(resolve, backup):
    if any(resolve(path) is None for path, value, expression, mode in backup):
        raise ValueError('Rückfallziel fehlt')
    for path, value, expression, mode in backup:
        par = resolve(path).par.render
        par.val = value
        par.expr = expression or ''
        par.mode = mode


def restore_aisi_source_presence(resolve):
    root = resolve(ROOT)
    backup = root.fetch(BACKUP_KEY, None) if root is not None else None
    if backup is None:
        raise ValueError('Keine Rückfallkopie vorhanden')
    _restore(resolve, backup)
    return {'restored': True, 'saved': False}


def repair_aisi_source_presence(resolve):
    root = resolve(ROOT)
    if root is None:
        raise ValueError('AISI-COMP fehlt')
    items = [root.op('table_template')] + [c for c in root.children
             if c.name.startswith('item') and c.name[4:].isdigit()]
    if items[0] is None or len(items) < 2:
        raise ValueError('Template oder Instanzen fehlen')
    nodes, expressions = [], []
    for item in items:
        for role in ROLES:
            node = item.op(role)
            if node is None:
                raise ValueError('Source-/Pfeilgeometrie fehlt: ' + item.path)
            par = node.par.render
            mode = str(par.mode).lower()
            if 'constant' in mode:
                base = repr(bool(par.eval()))
            elif 'expression' in mode and par.expr:
                base = par.expr
            else:
                raise ValueError('Unbekannte Render-Bindung: ' + node.path)
            expression = gated_expression(base)
            compile(expression, node.path, 'eval')
            nodes.append(node); expressions.append(expression)
    before = [(node.path, node.par.render.val, node.par.render.expr, node.par.render.mode) for node in nodes]
    if root.fetch(BACKUP_KEY, None) is None:
        root.store(BACKUP_KEY, before)
    try:
        for node, expression in zip(nodes, expressions):
            node.par.render.expr = expression
    except Exception:
        _restore(resolve, before)
        raise
    return {'gated_geometries': len(nodes), 'target_changes': False,
            'forced_cook': False, 'saved': False}


try:
    _resolve = op
except NameError:
    if __name__ == '__main__':
        raise RuntimeError('Im TouchDesigner-Python-Textport ausführen')
else:
    print(repair_aisi_source_presence(_resolve))
    print('Nur Source-/Pfeilsichtbarkeit an Live-Verfügbarkeit gebunden. Keine Speicherung.')
    print('Rücknahme: restore_aisi_source_presence(op)')
