"""Scene 7 opener: placing the Hip B(lock) Ultra smooth set under the patient's legs (soft 3D look, no people).
Real sizes from doc 7.4: trapezoid wedge A 16 cm / B 28 cm / side C 48 cm / height 15 cm (total abduction ~14 deg),
U-shaped leg rail under the operated (left) leg, equal walls, groove floor rising towards the foot, ends before the heel,
5 cm velcro straps: 2 round the rail + left leg, 2 round the right leg + wedge. Order follows the doc: rail first, then wedge, then straps.

  blender -b -P blender/place.py -- --out renders/place [--stills 1,40,120]
Units: metres. Bed along Y (head +Y, feet -Y), up +Z. Patient's left = +X = right side of the frame (camera at the foot of the bed).
"""
import bpy, bmesh, math, sys, os
from mathutils import Vector, Euler

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
def arg(name, default=None):
    return argv[argv.index(name) + 1] if name in argv else default
OUT = os.path.abspath(arg("--out", "renders/place"))
STILLS = [int(s) for s in arg("--stills", "").split(",") if s]
FPS, N = 30, 120
CM = 0.01

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.fps = FPS; sc.frame_start = 1; sc.frame_end = N
sc.render.resolution_x, sc.render.resolution_y = 1920, 1080

# ---------- materials (soft matte) ----------
def mat(name, col, rough=0.75, sss=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough
    if sss and "Subsurface Weight" in b.inputs:
        b.inputs["Subsurface Weight"].default_value = sss; b.inputs["Subsurface Radius"].default_value = (0.05, 0.02, 0.01)
    return m
SKIN = mat("skin", (0.80, 0.55, 0.43), 0.5, 0.25)
FOAM = mat("foam", (0.22, 0.60, 0.40), 0.85)          # wedge (mint green)
RAILM = mat("rail", (0.16, 0.48, 0.44), 0.85)         # leg rail (a little bluer, to tell them apart)
STRAP = mat("strap", (0.03, 0.16, 0.62), 0.6)
VEL = mat("velcro", (0.62, 0.78, 0.70), 0.95)
MATT = mat("mattress", (0.13, 0.17, 0.23), 0.55)
FRAME = mat("frame", (0.55, 0.58, 0.62), 0.3)
BLANK = mat("blanket", (0.80, 0.83, 0.86), 0.9)
GOWN = mat("gown", (0.55, 0.72, 0.85), 0.85)
DRESS = mat("dressing", (0.98, 0.98, 0.98), 0.9)
FLOOR = mat("floor", (0.55, 0.62, 0.68), 0.7)

def link(ob): sc.collection.objects.link(ob); return ob
def finish(ob, m, smooth=True):
    ob.data.materials.clear(); ob.data.materials.append(m)
    if smooth:
        for p in ob.data.polygons: p.use_smooth = True
    return ob

def loft(name, secs, m, bevel=0.0, caps=True):
    """Closed cross-section loops (same vertex count) joined into a solid."""
    bm = bmesh.new(); rows = [[bm.verts.new(p) for p in s] for s in secs]; n = len(secs[0])
    for a, b in zip(rows, rows[1:]):
        for i in range(n): bm.faces.new((a[i], a[(i + 1) % n], b[(i + 1) % n], b[i]))
    if caps: bm.faces.new(list(reversed(rows[0]))); bm.faces.new(rows[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = link(bpy.data.objects.new(name, me))
    if bevel:
        bv = ob.modifiers.new("bevel", "BEVEL"); bv.width = bevel; bv.segments = 4; bv.limit_method = "ANGLE"
    return finish(ob, m)

def box(name, lo, hi, m, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=[(a + b) / 2 for a, b in zip(lo, hi)])
    o = bpy.context.active_object; o.name = name; o.scale = [b - a for a, b in zip(lo, hi)]
    bpy.ops.object.transform_apply(scale=True)
    if bevel: bv = o.modifiers.new("bevel", "BEVEL"); bv.width = bevel; bv.segments = 5
    return finish(o, m)

def empty(name, loc=(0, 0, 0), rot_z=0.0, parent=None):
    e = link(bpy.data.objects.new(name, None)); e.location = loc; e.rotation_euler = (0, 0, math.radians(rot_z))
    if parent: e.parent = parent
    return e

# ---------- wedge (world): flat on the mattress between the legs, narrow end towards the groin ----------
YN = -0.25                                   # narrow end (A) at mid-thigh
LEN = math.sqrt(48 ** 2 - 6 ** 2) * CM       # side C = 48 cm
HA, HB, HW = 8 * CM, 14 * CM, 15 * CM
def half(y): return HA + (HB - HA) * (YN - y) / LEN
trap = [(-HA, YN), (HA, YN), (HB, YN - LEN), (-HB, YN - LEN)]
wedge = loft("Wedge", [[Vector((x, y, z)) for x, y in trap] for z in (0.0, HW)], FOAM, 0.012)
wedge_par = empty("WedgeSlide"); wedge.parent = wedge_par
for side in (-1, 1):                         # 3 vertical velcro strips on each side
    for f in (0.2, 0.5, 0.8):
        y = YN - LEN * f; x = side * (half(y) + 0.001); w2 = 1.5 * CM
        sq = [(x, y + w2), (x + side * 0.003, y + w2), (x + side * 0.003, y - w2), (x, y - w2)]
        loft(f"Velcro{side}{f}", [[Vector((px, py, z)) for px, py in sq] for z in (0.02, HW - 0.02)], VEL).parent = wedge_par

# ---------- legs: straight axis parallel to the wedge sides (V of ~14 deg), built along local -Y ----------
SIDE = Vector((HB - HA, -LEN, 0)).normalized()          # left wedge side direction (towards the feet)
TH = math.degrees(math.asin(SIDE.x))                    # ~7.1 deg
RAIL_HALF = 0.096                                       # rail outer half width (constant, so its wall lies flat on the wedge)
def leg_origin(sign, offset):
    nrm = Vector((-SIDE.y, SIDE.x, 0)) * 1.0            # outward normal of the left side
    p = Vector((HA, YN, 0)) + nrm * offset              # a point on the leg axis (top view)
    s = (0 - p.y) / SIDE.y                              # walk the axis to hip level (y = 0)
    o = p + SIDE * s
    return Vector((sign * o.x, 0, 0))

# radius of the base limb along the leg (t = metres from hip level); muscles are added on top
PROF = [(-0.08, 0.086), (0.05, 0.078), (0.20, 0.066), (0.34, 0.052), (0.42, 0.047), (0.50, 0.043), (0.60, 0.040), (0.70, 0.031), (0.80, 0.023)]
def rad(t):
    for (a, ra), (b, rb) in zip(PROF, PROF[1:]):
        if t <= b: return ra + (rb - ra) * (t - a) / (b - a)
    return PROF[-1][1]
ANK = 0.82

K = 1 / 0.575
def leg_mesh(name, zof, lat):
    """An anatomical lower limb in leg-local coords: -Y towards the foot, +Z anterior (up, patient supine),
    lat = +1 / -1: the lateral side is +X / -X. zof(t): height of the leg axis above the mattress."""
    mb = bpy.data.metaballs.new(name); mb.resolution = 0.004; mb.render_resolution = 0.0035; mb.threshold = 0.6
    ob = link(bpy.data.objects.new(name + "MB", mb))
    P = lambda t, dz=0.0, dx=0.0: Vector((lat * dx, -t, zof(t) + dz))      # dx > 0 = lateral, dz > 0 = anterior
    def el(p, r, size=(1, 1, 1), along=None, stiff=2.0):
        e = mb.elements.new(); e.co = p; e.radius = r * K; e.stiffness = stiff
        if size != (1, 1, 1) or along is not None:
            e.type = "ELLIPSOID"; e.size_x, e.size_y, e.size_z = size
            if along is not None: e.rotation = Vector((0, 1, 0)).rotation_difference(along.normalized())   # local y = long axis
        return e
    def cap(p1, p2, r, stiff=2.0):
        e = mb.elements.new(); e.type = "CAPSULE"; d = p2 - p1; e.co = (p1 + p2) / 2; e.radius = r * K; e.stiffness = stiff
        e.size_x = d.length / 2; e.rotation = Vector((1, 0, 0)).rotation_difference(d.normalized()); return e
    # base limb (slightly flattened front-back where it lies on the bed: done by the muscle masses instead)
    ts = [i * 0.04 for i in range(-2, 21)] + [ANK]
    for a, b in zip(ts, ts[1:]): cap(P(a), P(b), (rad(a) + rad(b)) / 2)
    Y = Vector((0, -1, 0))
    # thigh: quadriceps (front), vastus medialis teardrop above the knee, hamstrings (back), adductors (inner, upper)
    el(P(0.16, 0.022), 0.060, (1.0, 2.7, 0.75), Y)
    el(P(0.30, 0.020, 0.012), 0.044, (0.9, 2.2, 0.75), Y)
    el(P(0.345, 0.012, -0.030), 0.032, (0.95, 1.5, 0.9), Y)
    el(P(0.20, -0.022), 0.058, (1.0, 2.6, 0.8), Y)
    el(P(0.06, 0.0, -0.040), 0.050, (0.8, 2.0, 0.9), Y)
    # knee: kneecap, patellar tendon, femoral condyles, tibial plateau
    el(P(0.415, 0.036), 0.024, (1.0, 1.15, 0.65))
    cap(P(0.435, 0.032), P(0.47, 0.028), 0.010)
    el(P(0.415, 0.004, -0.024), 0.030); el(P(0.415, 0.002, 0.026), 0.028)
    el(P(0.455, 0.010), 0.036, (1.25, 0.9, 0.85))
    # shin: tibia ridge in front (a little medial), calf muscles behind (medial head bigger and lower), Achilles
    cap(P(0.48, 0.026, -0.006), P(0.76, 0.016, -0.004), 0.012)
    el(P(0.545, -0.020, -0.017), 0.040, (0.95, 2.1, 1.0), Y)
    el(P(0.530, -0.018, 0.019), 0.034, (0.9, 1.8, 0.95), Y)
    el(P(0.60, -0.005, 0.024), 0.024, (0.8, 2.6, 0.8), Y)                # peroneal / lateral leg
    cap(P(0.66, -0.016), P(0.80, -0.020), 0.013)                          # Achilles tendon
    # ankle bones (medial higher, lateral lower and further back)
    el(P(0.800, 0.002, -0.022), 0.012); el(P(0.812, -0.006, 0.022), 0.011)
    # foot: supine, toes up, a little turned out; sole faces -Y (towards the foot of the bed)
    rot = math.radians(7) * lat                          # external rotation
    def F(s, w=0.0, h=0.0):
        """s = 0 heel .. 1 toe tips along the foot; w = sideways (+ lateral); h = towards the sole (+) / dorsum (-)."""
        base = Vector((0, -(ANK + 0.020 + 0.040 * s), zof(ANK) - 0.036 + 0.215 * s))
        L = Vector((0, -0.040, 0.215)).normalized(); Hn = Vector((0, -L.z, L.y))   # Hn points to the sole side (-Y-ish)
        v = Vector((lat * w, 0, 0)) + Hn * h
        p = base + v
        # turn the whole foot out round the leg axis through the ankle
        c = Vector((0, p.y, zof(ANK))); q = p - c
        q = Vector((q.x * math.cos(rot) + q.z * math.sin(rot), q.y, -q.x * math.sin(rot) + q.z * math.cos(rot)))
        return c + q
    Lf = Vector((0, -0.040, 0.215))
    el(F(0.02, 0.0, 0.006), 0.031, (1.0, 1.0, 1.05))                       # heel pad
    for s, wd, th in ((0.18, 0.028, 0.026), (0.34, 0.030, 0.022), (0.50, 0.034, 0.019), (0.66, 0.040, 0.017)):
        el(F(s, 0.004), th, (wd / th, 1.7, 1.0), Lf)                       # midfoot, widening to the ball of the foot
    el(F(0.42, -0.020, 0.012), 0.014, (1.0, 2.6, 1.0), Lf)                 # arch (medial, sole side) kept slim
    el(F(0.70, -0.022, 0.004), 0.019); el(F(0.68, 0.026, 0.004), 0.015)    # ball of the big toe / little toe
    # toes: big toe longest, the rest shorter towards the lateral side
    for w, s0, s1, r in ((-0.024, 0.74, 1.00, 0.0125), (-0.004, 0.75, 0.955, 0.0085), (0.012, 0.745, 0.925, 0.0080),
                         (0.026, 0.735, 0.885, 0.0074), (0.038, 0.72, 0.84, 0.0068)):
        cap(F(s0, w, 0.002), F(s1, w * 1.05, 0.002), r, 2.6)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    out = link(bpy.data.objects.new(name, me)); bpy.data.objects.remove(ob)
    sm = out.modifiers.new("smooth", "CORRECTIVE_SMOOTH"); sm.iterations = 4; sm.factor = 0.4
    return finish(out, SKIN)

# left (operated) leg: in the rail; groove floor 2 cm at the thigh -> 6 cm at the calf (slopes up), so the heel floats
RAIL_T0, RAIL_T1 = 0.20, 0.74
def floor_l(t): return 0.02 + 0.04 * max(0.0, min(1.0, (t - RAIL_T0) / (RAIL_T1 - RAIL_T0)))
def z_left(t): return floor_l(min(max(t, RAIL_T0), RAIL_T1)) + 0.006 + rad(min(max(t, RAIL_T0), RAIL_T1)) if t >= RAIL_T0 else floor_l(RAIL_T0) + 0.006 + rad(RAIL_T0) + (RAIL_T0 - t) * 0.02
# a straight leg: fit a line through the axis heights at the two rail ends
ZL0, ZL1 = floor_l(RAIL_T0) + 0.006 + rad(RAIL_T0), floor_l(RAIL_T1) + 0.006 + rad(RAIL_T1)
zl = lambda t: ZL0 + (ZL1 - ZL0) * (t - RAIL_T0) / (RAIL_T1 - RAIL_T0)
zr = lambda t: max(rad(t), 0.07) * 0.98 if t < 0.2 else 0.0705 + (0.040 - 0.0705) * (t - 0.2) / (ANK - 0.2)   # right leg lies on the mattress

FL = empty("LegFrameL", leg_origin(1, RAIL_HALF), TH)
LIFT_L = empty("LiftL", (0, 0, 0), 0, FL)
legL = leg_mesh("LegL", zl, 1); legL.parent = LIFT_L
FR = empty("LegFrameR", leg_origin(-1, rad(0.22) + 0.004), -TH)
legR = leg_mesh("LegR", zr, -1); legR.parent = FR

# dressing on the left hip (lateral, upper thigh, just below the blanket)
bpy.ops.mesh.primitive_plane_add(size=1)
dr = bpy.context.active_object; dr.name = "Dressing"; dr.scale = (0.07, 0.09, 1); dr.parent = LIFT_L
dr.location = (rad(0.04) * 0.9, -0.04, zl(0.04) + rad(0.04) * 0.45); dr.rotation_euler = (0, math.radians(62), 0)
finish(dr, DRESS, False)

# ---------- U rail (leg-local, under the left leg) ----------
def rail_section(t):
    ri = rad(t) + 0.006; ro = RAIL_HALF; fl = floor_l(t); cz = zl(t); top = cz      # walls up to the middle of the leg, equal height
    pts = [(-ro, top), (-ro, 0.0), (ro, 0.0), (ro, top), (ri, top)]
    pts += [(ri * math.cos(a), cz - ri * math.sin(a)) for a in [math.radians(d) for d in range(0, 181, 12)]]
    pts += [(-ri, top)]
    return [Vector((x, -t, z)) for x, z in pts]
RAIL_SLIDE = empty("RailSlide", (0, 0, 0), 0, FL)
rail = loft("Rail", [rail_section(RAIL_T0 + i * (RAIL_T1 - RAIL_T0) / 30) for i in range(31)], RAILM, 0.008)
rail.parent = RAIL_SLIDE

# ---------- straps (5 cm, built round their own centre so they can pop in) ----------
def strap_obj(name, loop2d, axis_pt, parent, thick=0.004):
    """loop2d: (x, z) points round a cross-section at leg-local depth axis_pt.y, extruded 5 cm along -Y."""
    c = Vector((0, axis_pt.y - 2.5 * CM, sum(z for _, z in loop2d) / len(loop2d)))
    secs = [[Vector((x, axis_pt.y - dy, z)) - c for x, z in loop2d] for dy in (0, 5 * CM)]
    s = loft(name, secs, STRAP, caps=False); s.parent = parent; s.location = c
    so = s.modifiers.new("solid", "SOLIDIFY"); so.thickness = thick; so.offset = 1
    return s
def left_loop(t):
    ri = rad(t) + 0.018; cz = zl(t); ro = RAIL_HALF + 0.003
    pts = [(ri * math.cos(a), cz + ri * math.sin(a)) for a in [math.radians(d) for d in range(0, 181, 12)]]   # over the leg
    return pts + [(-ro, cz), (-ro, 0.001), (ro, 0.001), (ro, cz)]
STRAPS = [strap_obj("StrapL1", left_loop(0.34), Vector((0, -0.34, 0)), FL), strap_obj("StrapL2", left_loop(0.60), Vector((0, -0.60, 0)), FL)]

def hull(pts):
    pts = sorted(set((round(x, 5), round(y, 5)) for x, y in pts))
    def cross(o, a, b): return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, hi = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(hi) >= 2 and cross(hi[-2], hi[-1], p) <= 0: hi.pop()
        hi.append(p)
    return lo[:-1] + hi[:-1]
def right_strap(name, t):
    # world cross-section at the right leg's depth t: round the right leg and the wedge
    o = FR.location; d = Vector((-SIDE.x, SIDE.y, 0)); c = o + d * t
    r = rad(t) + 0.016; z = zr(t)
    circ = [(c.x + r * math.cos(a), z + r * math.sin(a)) for a in [math.radians(k) for k in range(0, 360, 12)]]
    hw = half(c.y) + 0.004
    loop = hull(circ + [(-hw, 0.001), (hw, 0.001), (-hw, HW + 0.004), (hw, HW + 0.004)])
    cen = Vector((0, c.y - 2.5 * CM, sum(zz for _, zz in loop) / len(loop)))
    secs = [[Vector((x, c.y - dy, zz)) - cen for x, zz in loop] for dy in (0, 5 * CM)]
    s = loft(name, secs, STRAP, caps=False); s.location = cen
    so = s.modifiers.new("solid", "SOLIDIFY"); so.thickness = 0.004; so.offset = 1
    return s
STRAPS += [right_strap("StrapR1", 0.34), right_strap("StrapR2", 0.60)]

# ---------- bed, blanket, room ----------
box("Mattress", (-0.36, -1.05, -0.09), (0.36, 1.25, 0.0), MATT, 0.03)
box("TableBase", (-0.12, -0.6, -0.85), (0.12, 0.9, -0.09), FRAME)
for x in (-0.38, 0.38): box(f"Rail{x}", (x - 0.012, -0.9, -0.05), (x + 0.012, 1.1, -0.025), FRAME, 0.008)

# ---------- patient's body: frail elderly woman lying on her back, gown, arms at her sides, head on a pillow ----------
HAIR = mat("hair", (0.86, 0.86, 0.84), 0.8)
LID = mat("lid", (0.45, 0.28, 0.22), 0.7)
PILW = mat("pillow", (0.93, 0.95, 0.97), 0.9)
def mb_mesh(name, m, res, fill):
    mb = bpy.data.metaballs.new(name); mb.resolution = res; mb.render_resolution = res; mb.threshold = 0.6
    ob = link(bpy.data.objects.new(name + "MB", mb))
    def el(p, r, size=None, rot=None, stiff=2.0):
        e = mb.elements.new(); e.co = Vector(p); e.radius = r * K; e.stiffness = stiff
        if size: e.type = "ELLIPSOID"; e.size_x, e.size_y, e.size_z = size
        if rot: e.rotation = Euler([math.radians(a) for a in rot]).to_quaternion()
    def cap(p1, p2, r):
        p1, p2 = Vector(p1), Vector(p2); d = p2 - p1
        e = mb.elements.new(); e.type = "CAPSULE"; e.co = (p1 + p2) / 2; e.radius = r * K; e.stiffness = 2.0
        e.size_x = d.length / 2; e.rotation = Vector((1, 0, 0)).rotation_difference(d.normalized())
    fill(el, cap)
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    out = link(bpy.data.objects.new(name, me)); bpy.data.objects.remove(ob)
    sm = out.modifiers.new("smooth", "CORRECTIVE_SMOOTH"); sm.iterations = 4; sm.factor = 0.4
    return finish(out, m)

HEAD = Vector((0, 0.80, 0.160))                                         # head rests on the pillow (pillow top z 0.075)
def torso(el, cap):                                                     # in the gown: hips, belly, chest, shoulders, upper arms
    el((0, 0.06, 0.085), 0.16, (1.20, 0.80, 0.55))                      # hips / pelvis
    el((0, 0.28, 0.090), 0.14, (1.05, 1.25, 0.60))                      # belly
    el((0, 0.50, 0.095), 0.14, (1.15, 1.00, 0.55))                      # chest
    el((0, 0.635, 0.085), 0.060, (1.7, 0.75, 0.75))                     # gown neckline round the base of the neck
    el((-0.055, 0.46, 0.115), 0.034, (1.0, 0.9, 0.6)); el((0.055, 0.46, 0.115), 0.034, (1.0, 0.9, 0.6))
    for sx in (-1, 1):
        el((sx * 0.170, 0.600, 0.075), 0.048)                           # shoulder
        cap((sx * 0.200, 0.59, 0.060), (sx * 0.230, 0.40, 0.045), 0.034) # upper arm (short sleeve)
def skin_parts(el, cap):                                                # neck, head, face, forearms, hands
    cap((0, 0.62, 0.095), HEAD + Vector((0, -0.06, -0.035)), 0.038)     # neck
    el(HEAD, 0.088, (0.86, 1.08, 0.92))                                 # skull
    el(HEAD + Vector((0, -0.045, 0.030)), 0.050, (1.1, 0.9, 0.8))       # jaw / cheeks
    el(HEAD + Vector((0, -0.012, 0.084)), 0.009, (0.8, 1.6, 0.8))       # nose
    for sx in (-1, 1):
        el(HEAD + Vector((sx * 0.082, 0.0, -0.005)), 0.018, (0.6, 1.2, 0.9))   # ears
        cap((sx * 0.235, 0.40, 0.050), (sx * 0.245, 0.16, 0.040), 0.030)    # forearm
        el((sx * 0.245, 0.09, 0.035), 0.026, (0.75, 1.7, 0.6))             # hand, palm down
def hair(el, cap):                                                      # short white hair: crown and back of the head
    el(HEAD + Vector((0, 0.020, -0.012)), 0.092, (0.90, 1.05, 0.85))
    el(HEAD + Vector((0, 0.050, 0.030)), 0.070, (1.0, 0.9, 0.8))
body = mb_mesh("Torso", GOWN, 0.008, torso)
skin = mb_mesh("SkinUpper", SKIN, 0.005, skin_parts)
hr = mb_mesh("Hair", HAIR, 0.006, hair)
for sx in (-1, 1):                                                      # closed eyes: two little lid arcs
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.012, location=HEAD + Vector((sx * 0.030, 0.010, 0.073)))
    e = bpy.context.active_object; e.scale = (1.3, 0.35, 0.35); finish(e, LID)
box("Pillow", (-0.25, 0.68, 0.0), (0.25, 1.02, 0.075), PILW, 0.035)

# ---------- blanket draped over the body from the hips to the waist (rays from above, then relaxed like cloth) ----------
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
X0, X1, Y0B, Y1B, STEP = -0.40, 0.40, -0.13, 0.44, 0.01
nx, ny = int((X1 - X0) / STEP) + 1, int((Y1B - Y0B) / STEP) + 1
hit = [[-0.14] * nx for _ in range(ny)]
for j in range(ny):
    for i in range(nx):
        x, y = X0 + i * STEP, Y0B + j * STEP
        ok, loc, *_ = sc.ray_cast(dg, Vector((x, y, 1.0)), Vector((0, 0, -1)))
        if ok and loc.z > -0.05: hit[j][i] = loc.z + 0.010
h = [row[:] for row in hit]
for _ in range(60):                                                     # cloth tension: lift over gaps, sag a little
    n = [row[:] for row in h]
    for j in range(ny):
        for i in range(nx):
            nb = [h[jj][ii] for jj, ii in ((j - 1, i), (j + 1, i), (j, i - 1), (j, i + 1)) if 0 <= jj < ny and 0 <= ii < nx]
            n[j][i] = max(hit[j][i], 0.5 * h[j][i] + 0.5 * sum(nb) / len(nb) - 0.0006)
    h = n
bm = bmesh.new()
vs = [[bm.verts.new((X0 + i * STEP, Y0B + j * STEP, h[j][i])) for i in range(nx)] for j in range(ny)]
for j in range(ny - 1):
    for i in range(nx - 1): bm.faces.new((vs[j][i], vs[j][i + 1], vs[j + 1][i + 1], vs[j + 1][i]))
me = bpy.data.meshes.new("Blanket"); bm.to_mesh(me); bm.free()
bl = finish(link(bpy.data.objects.new("Blanket", me)), BLANK)
so = bl.modifiers.new("solid", "SOLIDIFY"); so.thickness = 0.008; so.offset = 1
bl.modifiers.new("sub", "SUBSURF").levels = 1
bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, -0.85)); finish(bpy.context.active_object, FLOOR, False)

# ---------- animation: rail slides in under the lifted leg, leg goes down, wedge slides in, straps close ----------
def k(ob, f, loc=None, rot=None, scale=None):
    if loc is not None: ob.location = loc; ob.keyframe_insert("location", frame=f)
    if rot is not None: ob.rotation_euler = [math.radians(a) for a in rot]; ob.keyframe_insert("rotation_euler", frame=f)
    if scale is not None: ob.scale = scale; ob.keyframe_insert("scale", frame=f)
k(LIFT_L, 1, rot=(-6, 0, 0)); k(LIFT_L, 20, rot=(-6, 0, 0)); k(LIFT_L, 30, rot=(0, 0, 0))   # held up a little, then laid in the groove
k(RAIL_SLIDE, 1, loc=(0.42, 0, 0)); k(RAIL_SLIDE, 20, loc=(0, 0, 0))
k(wedge_par, 1, loc=(0, -0.75, 0)); k(wedge_par, 24, loc=(0, -0.75, 0)); k(wedge_par, 44, loc=(0, 0, 0))
for i, s in enumerate(STRAPS):
    f0 = 50 + i * 9; full = tuple(s.scale)
    k(s, 1, scale=(0, 0, 0)); k(s, f0, scale=(0, 0, 0)); k(s, f0 + 5, scale=(1.08, 1.08, 1.08)); k(s, f0 + 8, scale=(1, 1, 1))
for ob in bpy.data.objects:
    if ob.animation_data and ob.animation_data.action:
        try:
            for fc in ob.animation_data.action.fcurves:
                for kp in fc.keyframe_points: kp.interpolation = "BEZIER"; kp.easing = "AUTO"
        except AttributeError:
            pass

# ---------- camera + light ----------
cam_d = bpy.data.cameras.new("Cam"); cam_d.lens = 38
cam = link(bpy.data.objects.new("Cam", cam_d)); sc.camera = cam
tgt = empty("Target"); cam.constraints.new("TRACK_TO").target = tgt
def camkey(f, c, t):
    cam.location = c; cam.keyframe_insert("location", frame=f); tgt.location = t; tgt.keyframe_insert("location", frame=f)
camkey(1, (0.16, -2.05, 2.15), (0.0, 0.18, 0.0))                       # wide: the whole patient
camkey(42, (0.094, -1.89, 1.57), (-0.04, -0.40, 0.0))                   # then in to the legs
camkey(N, (0.08, -1.80, 1.50), (-0.04, -0.40, 0.01))

sun_d = bpy.data.lights.new("Sun", "SUN"); sun_d.energy = 0.9; sun_d.angle = math.radians(12)
sun = link(bpy.data.objects.new("Sun", sun_d)); sun.rotation_euler = (math.radians(35), math.radians(-18), math.radians(25))
area_d = bpy.data.lights.new("Area", "AREA"); area_d.energy = 90; area_d.size = 2.5
area = link(bpy.data.objects.new("Area", area_d)); area.location = (0, -0.3, 2.2)
world = bpy.data.worlds.new("W"); sc.world = world; world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.62, 0.70, 0.78, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.30

for eng in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
    try: sc.render.engine = eng; break
    except TypeError: pass
try: sc.eevee.taa_render_samples = 48
except Exception: pass
try: sc.eevee.use_shadows = True
except Exception: pass
for vt in ("Standard",):
    try: sc.view_settings.view_transform = vt; break
    except TypeError: pass

sc.render.image_settings.file_format = "PNG"
os.makedirs(OUT, exist_ok=True)
if STILLS:
    for f in STILLS:
        sc.frame_set(f); sc.render.filepath = os.path.join(OUT, f"still_{f:03d}.png"); bpy.ops.render.render(write_still=True)
else:
    sc.render.filepath = os.path.join(OUT, "f_"); bpy.ops.render.render(animation=True)
