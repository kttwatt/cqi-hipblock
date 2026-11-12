"""Usage steps animation for the slide "ขั้นตอนการใช้งาน" (5 steps), reusing the patient + Hip B(lock) scene from place.py.
  1 supine, wedge between the legs (narrow end at the thigh, wide end at the foot), operated (left) leg abducted
  2 leg rail placed against the wedge, operated leg laid on the rail (popliteal to calf supported, knee/toes up, heel floats)
  3 straps: 2 round the rail + operated leg, 2 round the other leg + wedge
  4 check (camera goes round: abduction, heel floating, straps, knee/toes up)
  5 done: straps released
Thai step captions are added afterwards by tools/usage_captions.py (fonts render better in the browser).

  blender -b -P blender/usage.py -- --out renders/usage [--stills 1,120,260,400,500,600]
"""
import os, math
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "place.py"), encoding="utf-8").read()
scene_part = src[:src.index("# ---------- animation")]
tail_part = src[src.index("sun_d = bpy.data.lights"):].replace("taa_render_samples = 48", "taa_render_samples = 32")
exec(scene_part, globals())

N = 640
sc.frame_end = N

def k(ob, f, loc=None, rot=None, scale=None):
    if loc is not None: ob.location = loc; ob.keyframe_insert("location", frame=f)
    if rot is not None: ob.rotation_euler = [math.radians(a) for a in rot]; ob.keyframe_insert("rotation_euler", frame=f)
    if scale is not None: ob.scale = scale; ob.keyframe_insert("scale", frame=f)

TH_L = math.degrees(FL.rotation_euler.z); TH_R = math.degrees(FR.rotation_euler.z)
IN = 5.0                                   # legs start this much closer together (no pillow yet)
LIE = dict(loc=(0, 0, -0.024), rot=(6.5, 0, 0))   # left leg resting on the mattress (no rail under it)
UP = dict(loc=(0, 0, 0.03), rot=(-6, 0, 0))       # left leg held up while the rail goes in
REST = dict(loc=(0, 0, 0), rot=(0, 0, 0))         # left leg lying in the rail groove

# ---- step 1 (f 45-150): legs part, wedge slides in from the foot end ----
k(FL, 1, rot=(0, 0, TH_L - IN)); k(FL, 50, rot=(0, 0, TH_L - IN)); k(FL, 85, rot=(0, 0, TH_L))
k(FR, 1, rot=(0, 0, TH_R + IN)); k(FR, 50, rot=(0, 0, TH_R + IN)); k(FR, 85, rot=(0, 0, TH_R))
k(wedge_par, 1, loc=(0, -0.80, 0)); k(wedge_par, 70, loc=(0, -0.80, 0)); k(wedge_par, 120, loc=(0, 0, 0))

# ---- step 2 (f 150-300): leg lifted, rail slides in against the wedge, leg laid in the groove ----
k(LIFT_L, 1, **LIE); k(LIFT_L, 165, **LIE); k(LIFT_L, 195, **UP); k(LIFT_L, 235, **UP); k(LIFT_L, 265, **REST)
k(RAIL_SLIDE, 1, loc=(0.50, 0, 0), scale=(0, 0, 0)); k(RAIL_SLIDE, 178, scale=(0, 0, 0)); k(RAIL_SLIDE, 186, scale=(1, 1, 1))
k(RAIL_SLIDE, 190, loc=(0.50, 0, 0)); k(RAIL_SLIDE, 232, loc=(0, 0, 0))

# ---- step 3 (f 300-420): straps close one by one; step 5 (f 560-610): straps released ----
for i, s in enumerate(STRAPS):
    f0 = 312 + i * 22
    k(s, 1, scale=(0, 0, 0)); k(s, f0, scale=(0, 0, 0)); k(s, f0 + 7, scale=(1.08, 1.08, 1.08)); k(s, f0 + 11, scale=(1, 1, 1))
    f1 = 562 + (3 - i) * 10
    k(s, f1, scale=(1, 1, 1)); k(s, f1 + 4, scale=(1.08, 1.08, 1.08)); k(s, f1 + 10, scale=(0, 0, 0))

for ob in bpy.data.objects:
    ad = ob.animation_data
    if ad and ad.action:
        try:
            for fc in ad.action.fcurves:
                for kp in fc.keyframe_points: kp.interpolation = "BEZIER"; kp.easing = "AUTO"
        except AttributeError:
            pass

# ---- camera ----
cam_d = bpy.data.cameras.new("Cam"); cam_d.lens = 38
cam = link(bpy.data.objects.new("Cam", cam_d)); sc.camera = cam
tgt = empty("Target"); cam.constraints.new("TRACK_TO").target = tgt
def camkey(f, c, t):
    cam.location = c; cam.keyframe_insert("location", frame=f); tgt.location = t; tgt.keyframe_insert("location", frame=f)
TOP = ((0.094, -1.89, 1.57), (-0.04, -0.40, 0.0))        # from the foot of the bed, looking down the legs
SIDE_L = ((1.60, -1.10, 0.66), (0.08, -0.38, 0.06))      # low, from the patient's left: rail, knee, floating heel
camkey(1, (0.16, -2.05, 2.15), (0.0, 0.18, 0.0))          # wide: the whole patient
camkey(45, *TOP); camkey(160, *TOP)
camkey(200, *SIDE_L); camkey(285, *SIDE_L)
camkey(315, *TOP); camkey(425, *TOP)
camkey(470, (1.05, -1.75, 0.95), (0.06, -0.42, 0.05))     # round to the side ...
camkey(510, *SIDE_L); camkey(535, *SIDE_L)
camkey(560, *TOP); camkey(N, (0.12, -2.00, 1.95), (0.0, 0.0, 0.0))
for fc in (cam.animation_data.action.fcurves if hasattr(cam.animation_data.action, "fcurves") else []):
    for kp in fc.keyframe_points: kp.interpolation = "BEZIER"

exec(tail_part, globals())
