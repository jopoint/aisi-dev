# build_aisi_td.py
# AISI TouchDesigner Builder
# Schritt 4: Source/Target Marker + Bewegungslinien für 4 Tische

ROOT_PATH = '/project1'
OSC_PORT = 9000

ROI_CENTER_CM = 250
TD_SCALE = 0.0052


def destroy_if_exists(path):
    existing = op(path)
    if existing is not None:
        existing.destroy()


def clear_children(parent):
    for child in parent.children:
        child.destroy()


def set_expr(par, expr):
    par.expr = expr
    par.mode = ParMode.EXPRESSION


def set_rgb_pars(op_obj, r, g, b):
    if hasattr(op_obj.par, 'colorr'):
        op_obj.par.colorr = r
    if hasattr(op_obj.par, 'colorg'):
        op_obj.par.colorg = g
    if hasattr(op_obj.par, 'colorb'):
        op_obj.par.colorb = b
    if hasattr(op_obj.par, 'diffr'):
        op_obj.par.diffr = r
    if hasattr(op_obj.par, 'diffg'):
        op_obj.par.diffg = g
    if hasattr(op_obj.par, 'diffb'):
        op_obj.par.diffb = b


def create_color_mat(parent, name, r, g, b):
    mat = parent.create(phongMAT, name)
    mat.nodeX = -200 - (len(parent.children) * 80)
    mat.nodeY = -300
    set_rgb_pars(mat, r, g, b)
    print(f"  [MAT] {name}: RGB({r}, {g}, {b}) @ {mat.path}")
    return mat


def chop_expr(channel_name):
    return "op('/project1/comp_io/null_osc_raw')['%s'].eval()" % channel_name


def cm_to_td_x_expr(channel_name):
    return "(%s - %s) * %s" % (
        chop_expr(channel_name),
        ROI_CENTER_CM,
        TD_SCALE
    )


def cm_to_td_y_expr(channel_name):
    return "-(%s - %s) * %s" % (
        chop_expr(channel_name),
        ROI_CENTER_CM,
        TD_SCALE
    )


def safe_chop_expr(channel_name, fallback=0):
    return "(lambda o: o[%r].eval() if o is not None and o[%r] is not None else %s)(op('/project1/comp_io/null_osc_raw'))" % (
        channel_name,
        channel_name,
        fallback,
    )


def safe_cm_to_td_x_expr(channel_name, fallback=0):
    return "(lambda o: ((o[%r].eval() - %s) * %s) if o is not None and o[%r] is not None else %s)(op('/project1/comp_io/null_osc_raw'))" % (
        channel_name,
        ROI_CENTER_CM,
        TD_SCALE,
        channel_name,
        fallback,
    )


def safe_cm_to_td_y_expr(channel_name, fallback=0):
    return "(lambda o: (-(o[%r].eval() - %s) * %s) if o is not None and o[%r] is not None else %s)(op('/project1/comp_io/null_osc_raw'))" % (
        channel_name,
        ROI_CENTER_CM,
        TD_SCALE,
        channel_name,
        fallback,
    )


def safe_op_par_expr(op_path, par_name, fallback=0):
    return "(lambda o: o.par.%s.eval() if o is not None else %s)(op(%r))" % (
        par_name,
        fallback,
        op_path,
    )


def make_marker_geo(parent, name, x_channel, y_channel, rot_channel, material_path=None):
    geo = parent.create(geometryCOMP, name)
    clear_children(geo)

    table_width_td = 123 * TD_SCALE
    table_depth_td = 57 * TD_SCALE
    outline_thickness_td = 0.015
    orientation_mark_length_td = table_depth_td * 0.4

    top_rect = geo.create(rectangleSOP, 'top_edge')
    top_rect.nodeX = -200
    top_rect.nodeY = -100

    bottom_rect = geo.create(rectangleSOP, 'bottom_edge')
    bottom_rect.nodeX = -200
    bottom_rect.nodeY = 0

    left_rect = geo.create(rectangleSOP, 'left_edge')
    left_rect.nodeX = -200
    left_rect.nodeY = 100

    right_rect = geo.create(rectangleSOP, 'right_edge')
    right_rect.nodeX = -200
    right_rect.nodeY = 200

    orientation_rect = geo.create(rectangleSOP, 'orientation_mark')
    orientation_rect.nodeX = -200
    orientation_rect.nodeY = 300

    merge = geo.create(mergeSOP, 'merge1')
    merge.nodeX = 50
    merge.nodeY = 100

    edge_specs = [
        (top_rect, table_width_td, outline_thickness_td, 0, table_depth_td / 2),
        (bottom_rect, table_width_td, outline_thickness_td, 0, -table_depth_td / 2),
        (left_rect, outline_thickness_td, table_depth_td, -table_width_td / 2, 0),
        (right_rect, outline_thickness_td, table_depth_td, table_width_td / 2, 0),
    ]

    for rect, size_x, size_y, pos_x, pos_y in edge_specs:
        if hasattr(rect.par, 'sizex'):
            rect.par.sizex = size_x
        if hasattr(rect.par, 'sizey'):
            rect.par.sizey = size_y
        if hasattr(rect.par, 'tx'):
            rect.par.tx = pos_x
        if hasattr(rect.par, 'ty'):
            rect.par.ty = pos_y

        rect.display = False
        rect.render = False

    if hasattr(orientation_rect.par, 'sizex'):
        orientation_rect.par.sizex = outline_thickness_td
    if hasattr(orientation_rect.par, 'sizey'):
        orientation_rect.par.sizey = orientation_mark_length_td
    if hasattr(orientation_rect.par, 'tx'):
        orientation_rect.par.tx = 0
    if hasattr(orientation_rect.par, 'ty'):
        orientation_rect.par.ty = table_depth_td * 0.12

    orientation_rect.display = False
    orientation_rect.render = False

    merge.inputConnectors[0].connect(top_rect)
    merge.inputConnectors[1].connect(bottom_rect)
    merge.inputConnectors[2].connect(left_rect)
    merge.inputConnectors[3].connect(right_rect)
    merge.inputConnectors[4].connect(orientation_rect)

    merge.display = True
    merge.render = True

    geo.display = True
    geo.render = True

    set_expr(geo.par.tx, cm_to_td_x_expr(x_channel))
    set_expr(geo.par.ty, cm_to_td_y_expr(y_channel))
    geo.par.tz = 0
    set_expr(geo.par.rz, chop_expr(rot_channel))

    if material_path is not None:
        if hasattr(geo.par, 'material'):
            geo.par.material = material_path
            print(f"  [GEO] {name} -> {material_path}")
        else:
            print(f"  [WARN] {name}: geo.par.material existiert nicht!")

    return geo


def make_circle_geo(parent, name, x_channel, y_channel, radius_channel, material_path=None, tz=0.02):
    geo = parent.create(geometryCOMP, name)
    clear_children(geo)

    circle = geo.create(circleSOP, 'circle1')
    circle.nodeX = -120
    circle.nodeY = 0

    radius_expr = "(lambda o: max(o[%r].eval(), 0) * %s if o is not None and o[%r] is not None else 0)(op('/project1/comp_io/null_osc_raw'))" % (
        radius_channel,
        TD_SCALE,
        radius_channel,
    )

    if hasattr(circle.par, 'type'):
        try:
            circle.par.type = 'poly'
        except Exception:
            pass

    if hasattr(circle.par, "arc"):
        try:
            # Circle SOP Arc Type:
            # 0 = Closed Arc
            # 1 = Open Arc
            # 2 = Sliced Arc
            circle.par.arc.menuIndex = 1
        except Exception as e:
            print(f"Warning: could not set Circle SOP Arc Type to Open Arc: {e}")

    if hasattr(circle.par, 'divs'):
        circle.par.divs = 48

    if hasattr(circle.par, 'radius'):
        set_expr(circle.par.radius, radius_expr)

    if hasattr(circle.par, 'radx'):
        set_expr(circle.par.radx, radius_expr)

    if hasattr(circle.par, 'rady'):
        set_expr(circle.par.rady, radius_expr)

    circle.display = True
    circle.render = True

    geo.display = True
    geo.render = True

    set_expr(geo.par.tx, safe_cm_to_td_x_expr(x_channel, 0))
    set_expr(geo.par.ty, safe_cm_to_td_y_expr(y_channel, 0))
    geo.par.tz = tz

    if material_path is not None:
        if hasattr(geo.par, 'material'):
            geo.par.material = material_path
            print(f"  [GEO] {name} -> {material_path}")
        else:
            print(f"  [WARN] {name}: geo.par.material existiert nicht!")

    return geo


def make_motion_line_geo(parent, name, source_x, source_y, target_x, target_y, material_path=None):
    geo = parent.create(geometryCOMP, name)
    clear_children(geo)

    shaft_thickness_td = 0.012
    head_length_td = 0.075
    head_angle_deg = 35
    head_projection_td = head_length_td * 0.8191520442889918
    head_offset_y_td = head_length_td * 0.573576436351046 / 2

    shaft_rect = geo.create(rectangleSOP, 'shaft_rect')
    shaft_rect.nodeX = -500
    shaft_rect.nodeY = -160

    shaft_xform = geo.create(transformSOP, 'shaft_xform')
    shaft_xform.nodeX = -320
    shaft_xform.nodeY = -160
    shaft_xform.inputConnectors[0].connect(shaft_rect)

    head_upper_rect = geo.create(rectangleSOP, 'head_upper_rect')
    head_upper_rect.nodeX = -500
    head_upper_rect.nodeY = -20

    head_upper_xform = geo.create(transformSOP, 'head_upper_xform')
    head_upper_xform.nodeX = -320
    head_upper_xform.nodeY = -20
    head_upper_xform.inputConnectors[0].connect(head_upper_rect)

    head_lower_rect = geo.create(rectangleSOP, 'head_lower_rect')
    head_lower_rect.nodeX = -500
    head_lower_rect.nodeY = 120

    head_lower_xform = geo.create(transformSOP, 'head_lower_xform')
    head_lower_xform.nodeX = -320
    head_lower_xform.nodeY = 120
    head_lower_xform.inputConnectors[0].connect(head_lower_rect)

    merge = geo.create(mergeSOP, 'merge1')
    merge.nodeX = -80
    merge.nodeY = 0

    table_prefix = name.replace('_motion_line_geo', '')
    source_geo_path = parent.path + '/' + table_prefix + '_source_geo'
    target_geo_path = parent.path + '/' + table_prefix + '_target_geo'

    sx = safe_op_par_expr(source_geo_path, 'tx', 0)
    sy = safe_op_par_expr(source_geo_path, 'ty', 0)
    tx = safe_op_par_expr(target_geo_path, 'tx', 0)
    ty = safe_op_par_expr(target_geo_path, 'ty', 0)

    dx = "((%s) - (%s))" % (tx, sx)
    dy = "((%s) - (%s))" % (ty, sy)

    dist = "((%s)*(%s) + (%s)*(%s)) ** 0.5" % (dx, dx, dy, dy)
    shaft_length = "max(%s, 0.001)" % dist
    head_center_x = "(%s) - (%s / 2)" % (dist, head_projection_td)
    angle = "__import__('math').degrees(__import__('math').atan2((%s), (%s)))" % (dy, dx)

    if hasattr(shaft_rect.par, 'sizex'):
        set_expr(shaft_rect.par.sizex, shaft_length)
    if hasattr(shaft_rect.par, 'sizey'):
        shaft_rect.par.sizey = shaft_thickness_td
    if hasattr(shaft_xform.par, 'tx'):
        set_expr(shaft_xform.par.tx, "(%s) / 2" % shaft_length)
    if hasattr(shaft_xform.par, 'ty'):
        shaft_xform.par.ty = 0

    if hasattr(head_upper_rect.par, 'sizex'):
        head_upper_rect.par.sizex = head_length_td
    if hasattr(head_upper_rect.par, 'sizey'):
        head_upper_rect.par.sizey = shaft_thickness_td
    if hasattr(head_upper_xform.par, 'tx'):
        set_expr(head_upper_xform.par.tx, head_center_x)
    if hasattr(head_upper_xform.par, 'ty'):
        head_upper_xform.par.ty = -head_offset_y_td
    if hasattr(head_upper_xform.par, 'rz'):
        head_upper_xform.par.rz = head_angle_deg

    if hasattr(head_lower_rect.par, 'sizex'):
        head_lower_rect.par.sizex = head_length_td
    if hasattr(head_lower_rect.par, 'sizey'):
        head_lower_rect.par.sizey = shaft_thickness_td
    if hasattr(head_lower_xform.par, 'tx'):
        set_expr(head_lower_xform.par.tx, head_center_x)
    if hasattr(head_lower_xform.par, 'ty'):
        head_lower_xform.par.ty = head_offset_y_td
    if hasattr(head_lower_xform.par, 'rz'):
        head_lower_xform.par.rz = -head_angle_deg

    shaft_rect.display = False
    shaft_rect.render = False
    shaft_xform.display = False
    shaft_xform.render = False
    head_upper_rect.display = False
    head_upper_rect.render = False
    head_upper_xform.display = False
    head_upper_xform.render = False
    head_lower_rect.display = False
    head_lower_rect.render = False
    head_lower_xform.display = False
    head_lower_xform.render = False

    merge.inputConnectors[0].connect(shaft_xform)
    merge.inputConnectors[1].connect(head_upper_xform)
    merge.inputConnectors[2].connect(head_lower_xform)
    merge.display = True
    merge.render = True

    set_expr(geo.par.tx, sx)
    set_expr(geo.par.ty, sy)
    geo.par.tz = 0.03
    geo.par.sx = 1
    geo.par.sy = 1
    geo.par.sz = 1
    set_expr(geo.par.rz, angle)

    geo.display = True
    geo.render = True

    if material_path is not None:
        if hasattr(geo.par, 'material'):
            geo.par.material = material_path
            print(f"  [GEO] {name} -> {material_path}")
        else:
            print(f"  [WARN] {name}: geo.par.material existiert nicht!")

    return geo


def make_calibration_rect_geo(parent, name, width, height, tx, ty, material_path=None, tz=0):
    geo = parent.create(geometryCOMP, name)
    clear_children(geo)

    rect = geo.create(rectangleSOP, 'rect1')
    rect.nodeX = 0
    rect.nodeY = 0
    rect.display = True
    rect.render = True

    if hasattr(rect.par, 'sizex'):
        rect.par.sizex = width
    if hasattr(rect.par, 'sizey'):
        rect.par.sizey = height

    geo.display = True
    geo.render = True
    geo.par.tx = tx
    geo.par.ty = ty
    geo.par.tz = tz

    if material_path is not None:
        if hasattr(geo.par, 'material'):
            geo.par.material = material_path
            print(f"  [CAL] {name} -> {material_path}")
        else:
            print(f"  [WARN] {name}: geo.par.material existiert nicht!")

    return geo


def build():
    root = op(ROOT_PATH)

    destroy_if_exists(ROOT_PATH + '/comp_io')
    destroy_if_exists(ROOT_PATH + '/comp_render')
    destroy_if_exists(ROOT_PATH + '/comp_layout_proposal')
    destroy_if_exists(ROOT_PATH + '/comp_calibration')
    destroy_if_exists(ROOT_PATH + '/comp_tabletop_calibration')
    destroy_if_exists(ROOT_PATH + '/comp_output')

    # =========================
    # comp_io
    # =========================

    comp_io = root.create(containerCOMP, 'comp_io')
    comp_io.nodeX = -500
    comp_io.nodeY = 100
    comp_io.par.w = 500
    comp_io.par.h = 300

    oscin1 = comp_io.create(oscinCHOP, 'oscin1')
    oscin1.nodeX = 0
    oscin1.nodeY = 100
    oscin1.par.port = OSC_PORT
    oscin1.par.active = True

    null_osc_raw = comp_io.create(nullCHOP, 'null_osc_raw')
    null_osc_raw.nodeX = 220
    null_osc_raw.nodeY = 100
    null_osc_raw.inputConnectors[0].connect(oscin1)
    null_osc_raw.viewer = True
    null_osc_raw.display = True

    # =========================
    # comp_layout_proposal
    # =========================

    comp_layout_proposal = root.create(containerCOMP, 'comp_layout_proposal')
    comp_layout_proposal.nodeX = 150
    comp_layout_proposal.nodeY = 100
    comp_layout_proposal.par.w = 800
    comp_layout_proposal.par.h = 500

    # =========================
    # Materialien
    # =========================
    print("[BUILD] Erzeuge Materialien...")
    mat_source_green = create_color_mat(comp_layout_proposal, 'mat_source_green', 0, 1, 0)
    mat_target_blue = create_color_mat(comp_layout_proposal, 'mat_target_blue', 0, 0, 1)
    mat_motion_white = create_color_mat(comp_layout_proposal, 'mat_motion_white', 1, 1, 1)
    mat_person = create_color_mat(comp_layout_proposal, 'mat_person', 1, 1, 0)
    mat_chair = create_color_mat(comp_layout_proposal, 'mat_chair', 0, 1, 0)

    render_geos = []
    person_chair_geos = []
    motion_geos = []

    for i in range(4):
        line_geo = make_motion_line_geo(
            comp_layout_proposal,
            f'table{i}_motion_line_geo',
            f'table/{i}/source_x',
            f'table/{i}/source_y',
            f'table/{i}/target_x',
            f'table/{i}/target_y',
            mat_motion_white.path
        )
        line_geo.nodeX = -600
        line_geo.nodeY = 180 - i * 120
        motion_geos.append(line_geo)

        source_geo = make_marker_geo(
            comp_layout_proposal,
            f'table{i}_source_geo',
            f'table/{i}/source_x',
            f'table/{i}/source_y',
            f'table/{i}/source_rot',
            mat_source_green.path
        )
        source_geo.nodeX = -300
        source_geo.nodeY = 180 - i * 120
        render_geos.append(source_geo)

        target_geo = make_marker_geo(
            comp_layout_proposal,
            f'table{i}_target_geo',
            f'table/{i}/target_x',
            f'table/{i}/target_y',
            f'table/{i}/target_rot',
            mat_target_blue.path
        )
        target_geo.nodeX = 0
        target_geo.nodeY = 180 - i * 120
        render_geos.append(target_geo)

        person_geo = make_circle_geo(
            comp_layout_proposal,
            f'person{i}_geo',
            f'person/{i}/x',
            f'person/{i}/y',
            f'person/{i}/radius',
            mat_person.path,
            tz=0.02
        )
        person_geo.nodeX = 220
        person_geo.nodeY = 180 - i * 120
        person_chair_geos.append(person_geo)

        chair_geo = make_circle_geo(
            comp_layout_proposal,
            f'chair{i}_geo',
            f'chair/{i}/x',
            f'chair/{i}/y',
            f'chair/{i}/radius',
            mat_chair.path,
            tz=0.02
        )
        chair_geo.nodeX = 420
        chair_geo.nodeY = 180 - i * 120
        person_chair_geos.append(chair_geo)

    render_geos.extend(person_chair_geos)
    render_geos.extend(motion_geos)

    # =========================
    # Kamera, Licht, Render
    # =========================

    cam = comp_layout_proposal.create(cameraCOMP, 'cam1')
    cam.nodeX = -250
    cam.nodeY = -420
    cam.par.tx = 0
    cam.par.ty = 0
    cam.par.tz = 5

    if hasattr(cam.par, 'projection'):
        cam.par.projection = 'orthographic'
    if hasattr(cam.par, 'orthowidth'):
        cam.par.orthowidth = 3

    light = comp_layout_proposal.create(lightCOMP, 'light1')
    light.nodeX = 0
    light.nodeY = -420
    light.par.tx = 0
    light.par.ty = 0
    light.par.tz = 3

    render = comp_layout_proposal.create(renderTOP, 'render1')
    render.nodeX = 300
    render.nodeY = 100
    render.par.camera = cam.path
    render.par.lights = light.path
    render.par.geometry = ' '.join([geo.path for geo in render_geos])
    render.par.resolutionw = 1000
    render.par.resolutionh = 1000

    null_render = comp_layout_proposal.create(nullTOP, 'null_render')
    null_render.nodeX = 530
    null_render.nodeY = 100
    null_render.inputConnectors[0].connect(render)
    null_render.viewer = True
    null_render.display = True

    # =========================
    # comp_calibration
    # =========================

    comp_calibration = root.create(containerCOMP, 'comp_calibration')
    comp_calibration.nodeX = 150
    comp_calibration.nodeY = 650
    comp_calibration.par.w = 800
    comp_calibration.par.h = 500

    print('[BUILD] Erzeuge Calibration Layer...')
    mat_calibration_grid = create_color_mat(comp_calibration, 'mat_calibration_grid', 0.75, 0.75, 0.75)
    mat_calibration_corner = create_color_mat(comp_calibration, 'mat_calibration_corner', 1, 1, 1)

    calibration_geos = []
    roi_half_td = 250 * TD_SCALE
    roi_size_td = roi_half_td * 2
    grid_spacing_td = 50 * TD_SCALE
    grid_thickness_td = 0.006
    corner_size_td = 0.04

    for i in range(11):
        pos = -roi_half_td + i * grid_spacing_td

        vertical_geo = make_calibration_rect_geo(
            comp_calibration,
            f'grid_v_{i}',
            grid_thickness_td,
            roi_size_td,
            pos,
            0,
            mat_calibration_grid.path,
            tz=0
        )
        vertical_geo.nodeX = -650
        vertical_geo.nodeY = 200 - i * 45
        calibration_geos.append(vertical_geo)

        horizontal_geo = make_calibration_rect_geo(
            comp_calibration,
            f'grid_h_{i}',
            roi_size_td,
            grid_thickness_td,
            0,
            pos,
            mat_calibration_grid.path,
            tz=0
        )
        horizontal_geo.nodeX = -420
        horizontal_geo.nodeY = 200 - i * 45
        calibration_geos.append(horizontal_geo)

    corner_positions = [
        ('corner_tl', -roi_half_td, roi_half_td),
        ('corner_tr', roi_half_td, roi_half_td),
        ('corner_bl', -roi_half_td, -roi_half_td),
        ('corner_br', roi_half_td, -roi_half_td),
    ]

    for idx, (name, pos_x, pos_y) in enumerate(corner_positions):
        corner_geo = make_calibration_rect_geo(
            comp_calibration,
            name,
            corner_size_td,
            corner_size_td,
            pos_x,
            pos_y,
            mat_calibration_corner.path,
            tz=0.01
        )
        corner_geo.nodeX = -180
        corner_geo.nodeY = 200 - idx * 60
        calibration_geos.append(corner_geo)

    calibration_cam = comp_calibration.create(cameraCOMP, 'cam1')
    calibration_cam.nodeX = -250
    calibration_cam.nodeY = -420
    calibration_cam.par.tx = 0
    calibration_cam.par.ty = 0
    calibration_cam.par.tz = 5

    if hasattr(calibration_cam.par, 'projection'):
        calibration_cam.par.projection = 'orthographic'
    if hasattr(calibration_cam.par, 'orthowidth'):
        calibration_cam.par.orthowidth = 3

    calibration_light = comp_calibration.create(lightCOMP, 'light1')
    calibration_light.nodeX = 0
    calibration_light.nodeY = -420
    calibration_light.par.tx = 0
    calibration_light.par.ty = 0
    calibration_light.par.tz = 3

    calibration_render = comp_calibration.create(renderTOP, 'render1')
    calibration_render.nodeX = 300
    calibration_render.nodeY = 100
    calibration_render.par.camera = calibration_cam.path
    calibration_render.par.lights = calibration_light.path
    calibration_render.par.geometry = ' '.join([geo.path for geo in calibration_geos])
    calibration_render.par.resolutionw = 1000
    calibration_render.par.resolutionh = 1000

    calibration_null_render = comp_calibration.create(nullTOP, 'null_render')
    calibration_null_render.nodeX = 530
    calibration_null_render.nodeY = 100
    calibration_null_render.inputConnectors[0].connect(calibration_render)
    calibration_null_render.viewer = True
    calibration_null_render.display = True

    # =========================
    # comp_tabletop_calibration
    # =========================

    comp_tabletop_calibration = root.create(containerCOMP, 'comp_tabletop_calibration')
    comp_tabletop_calibration.nodeX = 150
    comp_tabletop_calibration.nodeY = 1200
    comp_tabletop_calibration.par.w = 800
    comp_tabletop_calibration.par.h = 500

    print('[BUILD] Erzeuge Tabletop Calibration Layer...')
    mat_tabletop_pattern = create_color_mat(comp_tabletop_calibration, 'mat_tabletop_pattern', 1, 1, 1)

    tabletop_geos = []
    table_real_width_td = 133 * TD_SCALE
    table_real_depth_td = 67 * TD_SCALE
    tabletop_outline_thickness_td = 0.012
    tabletop_centerline_thickness_td = 0.008
    tabletop_corner_size_td = 0.035

    tabletop_specs = [
        ('tabletop_top_edge', table_real_width_td, tabletop_outline_thickness_td, 0, table_real_depth_td / 2, 0),
        ('tabletop_bottom_edge', table_real_width_td, tabletop_outline_thickness_td, 0, -table_real_depth_td / 2, 0),
        ('tabletop_left_edge', tabletop_outline_thickness_td, table_real_depth_td, -table_real_width_td / 2, 0, 0),
        ('tabletop_right_edge', tabletop_outline_thickness_td, table_real_depth_td, table_real_width_td / 2, 0, 0),
        ('tabletop_center_horizontal', table_real_width_td, tabletop_centerline_thickness_td, 0, 0, 0.01),
        ('tabletop_center_vertical', tabletop_centerline_thickness_td, table_real_depth_td, 0, 0, 0.01),
    ]

    for idx, (name, width, height, pos_x, pos_y, pos_z) in enumerate(tabletop_specs):
        tabletop_geo = make_calibration_rect_geo(
            comp_tabletop_calibration,
            name,
            width,
            height,
            pos_x,
            pos_y,
            mat_tabletop_pattern.path,
            tz=pos_z
        )
        tabletop_geo.nodeX = -650
        tabletop_geo.nodeY = 220 - idx * 55
        tabletop_geos.append(tabletop_geo)

    tabletop_corner_positions = [
        ('tabletop_corner_tl', -table_real_width_td / 2, table_real_depth_td / 2),
        ('tabletop_corner_tr', table_real_width_td / 2, table_real_depth_td / 2),
        ('tabletop_corner_bl', -table_real_width_td / 2, -table_real_depth_td / 2),
        ('tabletop_corner_br', table_real_width_td / 2, -table_real_depth_td / 2),
    ]

    for idx, (name, pos_x, pos_y) in enumerate(tabletop_corner_positions):
        tabletop_corner_geo = make_calibration_rect_geo(
            comp_tabletop_calibration,
            name,
            tabletop_corner_size_td,
            tabletop_corner_size_td,
            pos_x,
            pos_y,
            mat_tabletop_pattern.path,
            tz=0.02
        )
        tabletop_corner_geo.nodeX = -300
        tabletop_corner_geo.nodeY = 220 - idx * 60
        tabletop_geos.append(tabletop_corner_geo)

    tabletop_cam = comp_tabletop_calibration.create(cameraCOMP, 'cam1')
    tabletop_cam.nodeX = -250
    tabletop_cam.nodeY = -420
    tabletop_cam.par.tx = 0
    tabletop_cam.par.ty = 0
    tabletop_cam.par.tz = 5

    if hasattr(tabletop_cam.par, 'projection'):
        tabletop_cam.par.projection = 'orthographic'
    if hasattr(tabletop_cam.par, 'orthowidth'):
        tabletop_cam.par.orthowidth = 1.2

    tabletop_light = comp_tabletop_calibration.create(lightCOMP, 'light1')
    tabletop_light.nodeX = 0
    tabletop_light.nodeY = -420
    tabletop_light.par.tx = 0
    tabletop_light.par.ty = 0
    tabletop_light.par.tz = 3

    tabletop_render = comp_tabletop_calibration.create(renderTOP, 'render1')
    tabletop_render.nodeX = 300
    tabletop_render.nodeY = 100
    tabletop_render.par.camera = tabletop_cam.path
    tabletop_render.par.lights = tabletop_light.path
    tabletop_render.par.geometry = ' '.join([geo.path for geo in tabletop_geos])
    tabletop_render.par.resolutionw = 1000
    tabletop_render.par.resolutionh = 1000

    tabletop_null_render = comp_tabletop_calibration.create(nullTOP, 'null_render')
    tabletop_null_render.nodeX = 530
    tabletop_null_render.nodeY = 100
    tabletop_null_render.inputConnectors[0].connect(tabletop_render)
    tabletop_null_render.viewer = True
    tabletop_null_render.display = True

    # =========================
    # comp_output
    # =========================

    comp_output = root.create(containerCOMP, 'comp_output')
    comp_output.nodeX = 1050
    comp_output.nodeY = 100
    comp_output.par.w = 300
    comp_output.par.h = 200

    output_page = comp_output.appendCustomPage('Output')
    output_mode_par = output_page.appendInt('Outputmode', label='Output Mode')
    if isinstance(output_mode_par, (list, tuple)):
        output_mode_par = output_mode_par[0] if output_mode_par else None

    if output_mode_par is not None:
        if hasattr(output_mode_par, 'default'):
            output_mode_par.default = 0
        if hasattr(output_mode_par, 'min'):
            output_mode_par.min = 0
        if hasattr(output_mode_par, 'max'):
            output_mode_par.max = 2
        if hasattr(output_mode_par, 'normMin'):
            output_mode_par.normMin = 0
        if hasattr(output_mode_par, 'normMax'):
            output_mode_par.normMax = 2
        if hasattr(output_mode_par, 'clampMin'):
            output_mode_par.clampMin = True
        if hasattr(output_mode_par, 'clampMax'):
            output_mode_par.clampMax = True

    if hasattr(comp_output.par, 'Outputmode'):
        comp_output.par.Outputmode = 0

    select_layout_render = comp_output.create(selectTOP, 'select_layout_render')
    select_layout_render.nodeX = 0
    select_layout_render.nodeY = 0
    select_layout_render.par.top = '/project1/comp_layout_proposal/null_render'
    select_layout_render.viewer = True
    select_layout_render.display = True

    select_calibration_render = comp_output.create(selectTOP, 'select_calibration_render')
    select_calibration_render.nodeX = 0
    select_calibration_render.nodeY = 120
    select_calibration_render.par.top = '/project1/comp_calibration/null_render'

    select_tabletop_calibration_render = comp_output.create(selectTOP, 'select_tabletop_calibration_render')
    select_tabletop_calibration_render.nodeX = 0
    select_tabletop_calibration_render.nodeY = 240
    select_tabletop_calibration_render.par.top = '/project1/comp_tabletop_calibration/null_render'

    switch_output = comp_output.create(switchTOP, 'switch_output')
    switch_output.nodeX = 220
    switch_output.nodeY = 60
    switch_output.inputConnectors[0].connect(select_layout_render)
    switch_output.inputConnectors[1].connect(select_calibration_render)
    switch_output.inputConnectors[2].connect(select_tabletop_calibration_render)
    set_expr(switch_output.par.index, "op('/project1/comp_output').par.Outputmode.eval()")

    null_output = comp_output.create(nullTOP, 'null_output')
    null_output.nodeX = 440
    null_output.nodeY = 60
    null_output.inputConnectors[0].connect(switch_output)
    null_output.viewer = True
    null_output.display = True

    print('[BUILD] Fertig!')
    print(f'  Materialien: {mat_source_green.path}, {mat_target_blue.path}, {mat_motion_white.path}')
    print('  Zuweisungen: Source -> mat_source_green, Target -> mat_target_blue, Motion -> mat_motion_white')
    print('  Geometrien: 4 Source + 4 Target + 4 Motion')
    print('AISI TD Builder Schritt 8 fix: comp_output connected via Select TOP.')
    print('AISI TD Builder Schritt 10 fertig: table outlines.')
    print('AISI TD Builder Schritt 11 fertig: table orientation marks.')
    print('AISI TD Builder Schritt 11 fix: orientation marks rotated 90 degrees.')
    print('AISI TD Builder Schritt 12 fertig: calibration layer added.')
    print('AISI TD Builder Schritt 13 fertig: output mode switch.')
    print('AISI TD Builder Schritt 15 fertig: motion arrows with V heads above table outlines.')
    print('AISI TD Builder Schritt 16 fertig: standalone tabletop calibration container added.')


# Nicht automatisch aufrufen - TD ruft build() auf
# build()