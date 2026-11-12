"""Thai step captions for the usage animation (renders/usage/f_*.png -> renders/usage/usage-steps.mp4).
Each caption is a transparent 1920x1080 PNG made by headless Chrome (Kanit/Sarabun), faded in/out with ffmpeg.
Captions sit in a band at the top, so they never cover the legs or the pillows.

  python tools/usage_captions.py
"""
import os, subprocess, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "renders" / "usage"
CAP = OUT / "captions"; CAP.mkdir(parents=True, exist_ok=True)
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
FPS, N = 30, 640

# (start s, end s, number or "", line 1, line 2)
STEPS = [
    (0.0, 1.5, "", "ขั้นตอนการใช้งาน", "Hip B(lock) Ultra Smooth"),
    (1.5, 5.0, "1", "จัดผู้ป่วยนอนหงายราบ วางหมอนระหว่างขา", "ด้านแคบอยู่ฝั่งต้นขา ด้านกว้างอยู่ฝั่งปลายเท้า ให้ขาข้างที่ผ่าตัดกาง 30 องศา"),
    (5.0, 10.0, "2", "ประกบหมอนยกขาติดกับหมอนกางขา วางขาข้างผ่าตัดบนหมอนยกขา", "หนุนตั้งแต่ใต้ข้อพับเข่าจนถึงน่อง หัวเข่าและปลายเท้าตั้งตรง"),
    (10.0, 14.0, "3", "ล็อกแนวขาให้คงที่โดยใช้สายรัดขา รัดขาอีกข้างกับหมอน", "หลีกเลี่ยงการหมุนขาข้างที่ผ่าตัดเข้าด้านใน"),
    (14.0, 18.6, "4", "ตรวจสอบหลังการจัดท่า", "✓ กางออก 30 องศา   ✓ ข้อพับไม่ถูกกด ส้นเท้าลอย   ✓ สายรัดไม่แน่นเกินไป   ✓ เข่าและปลายเท้าตั้งตรง"),
    (18.6, N / FPS, "5", "เมื่อใช้เสร็จ ปลดสายรัด ตรวจสอบผิวหนัง", "ถอดปลอกหุ้ม เช็ดทำความสะอาดก่อนใช้กับผู้ป่วยรายต่อไป"),
]

HTML = """<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Kanit:wght@600;700&family=Sarabun:wght@500;600&display=swap" rel="stylesheet">
<style>*{{margin:0;padding:0;box-sizing:border-box}}html,body{{width:1920px;height:1080px;background:transparent;overflow:hidden}}
.band{{position:absolute;left:0;top:0;width:1920px;height:210px;background:linear-gradient(180deg,rgba(20,38,52,.88) 0%,rgba(20,38,52,.78) 62%,rgba(20,38,52,0) 100%)}}
.row{{position:absolute;left:72px;top:34px;right:72px;display:flex;gap:28px;align-items:center}}
.num{{width:96px;height:96px;flex:0 0 auto;border-radius:48px;background:linear-gradient(160deg,#6fb7c1,#3e8e9a);display:flex;align-items:center;justify-content:center;
 font:700 56px Kanit,Tahoma,sans-serif;color:#fff}}
.t1{{font:600 44px/1.25 Kanit,Tahoma,sans-serif;color:#fff}}
.t2{{font:600 32px/1.35 Sarabun,Tahoma,sans-serif;color:#bfe3e8;margin-top:4px}}
</style></head><body><div class="band"></div><div class="row">{num}<div><p class="t1">{a}</p><p class="t2">{b}</p></div></div></body></html>"""

def run(cmd):
    subprocess.run(cmd, check=True)

pngs = []
for i, (s, e, n, a, b) in enumerate(STEPS):
    html = CAP / f"cap{i}.html"
    num = f'<div class="num">{n}</div>' if n else ""
    html.write_text(HTML.format(num=num, a=a, b=b), encoding="utf-8")
    png = CAP / f"cap{i}.png"
    run([CHROME, "--headless", "--disable-gpu", "--hide-scrollbars", "--default-background-color=00000000",
         "--virtual-time-budget=4000", "--window-size=1920,1080", f"--screenshot={png}", html.as_uri()])
    pngs.append((s, e, png))

if os.environ.get("CAPS_ONLY"):
    raise SystemExit("captions only")

# ffmpeg: frames + each caption looped for its window, faded 0.3 s in/out, overlaid in turn
args = ["ffmpeg", "-y", "-v", "error", "-framerate", str(FPS), "-i", str(OUT / "f_%04d.png")]
for s, e, p in pngs:
    args += ["-loop", "1", "-framerate", str(FPS), "-t", f"{e - s:.3f}", "-i", str(p)]
fl, last = [], "[0:v]"
for i, (s, e, _) in enumerate(pngs):
    d = e - s; fi = 0.0 if s == 0 else 0.3
    fl.append(f"[{i + 1}:v]format=rgba,fade=t=in:st=0:d={fi or 0.01}:alpha=1,fade=t=out:st={max(d - 0.3, 0):.3f}:d=0.3:alpha=1,setpts=PTS+{s}/TB[c{i}]")
    fl.append(f"{last}[c{i}]overlay=eof_action=pass[v{i}]"); last = f"[v{i}]"
args += ["-filter_complex", ";".join(fl), "-map", last, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
         "-movflags", "+faststart", str(OUT / "usage-steps.mp4")]
run(args)
print("wrote", OUT / "usage-steps.mp4")
