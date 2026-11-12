"""Build the online slide deck (GitHub Pages) from the Claude Slides project files.

Input : SRC/project/deck.json, SRC/project/slides/<id>.html, SRC/<blob-id>.<ext> (assets read from the artifact)
Output: docs/index.html (all slides + viewer) and docs/media/<blob-id>.<ext>

  python slides-web/build.py <SRC folder>
"""
import json, os, re, shutil, sys, glob, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = sys.argv[1]
OUT = os.path.join(ROOT, "docs")
MEDIA = os.path.join(OUT, "media")
os.makedirs(MEDIA, exist_ok=True)
HERE = os.path.dirname(os.path.abspath(__file__))

deck = json.load(open(os.path.join(SRC, "project", "deck.json"), encoding="utf-8"))

# lucide icons (ISC licence), 24x24 stroke icons
ICONS = {
    "CheckCircle": '<circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/>',
    "Home": '<path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>',
    "Lightbulb": '<path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .2 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5"/><path d="M9 18h6"/><path d="M10 22h4"/>',
    "Search": '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
    "Users": '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
    "Check": '<path d="M20 6 9 17l-5-5"/>',
    "Star": '<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>',
    "Warning": '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
}

blobs = {}
for f in glob.glob(os.path.join(SRC, "*.*")):
    name = os.path.basename(f)
    m = re.match(r"^([0-9a-f]{32})\.(\w+)$", name)
    if m:
        blobs[m.group(1)] = name


def blob(m):
    bid = m.group(1)
    if bid not in blobs:
        raise SystemExit(f"missing asset {bid}")
    dst = os.path.join(MEDIA, blobs[bid])
    if not os.path.exists(dst):
        shutil.copy2(os.path.join(SRC, blobs[bid]), dst)
    return "media/" + blobs[bid]


def icon(m):
    attrs = m.group(1)
    name = re.search(r'name="([^"]+)"', attrs).group(1)
    style = re.search(r'style="([^"]*)"', attrs)
    style = style.group(1) if style else ""
    if name not in ICONS:
        print("warning: icon", name, "drawn as a dot")
    svg = ICONS.get(name, '<circle cx="12" cy="12" r="4"/>')
    return (f'<span class="x-icon" style="{style}"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{svg}</svg></span>')


def shape(m):
    attrs = m.group(1)
    kind = re.search(r'kind="([^"]+)"', attrs).group(1)
    style = re.search(r'style="([^"]*)"', attrs)
    return f'<span class="x-shape k-{kind}" style="{style.group(1) if style else ""}"></span>'


def crop(m):
    zoom, x, y = m.group(1).split()
    return f'style="object-position:{x} {y}; '


slides = []
for sid in deck["order"]:
    s = open(os.path.join(SRC, "project", "slides", sid + ".html"), encoding="utf-8").read()
    s = re.sub(r"<aside[\s\S]*?</aside>", "", s)  # speaker notes stay private
    s = re.sub(r"/_blob/([0-9a-f]{32})", blob, s)
    s = re.sub(r"<x-icon([^>]*)>\s*</x-icon>", icon, s)
    s = re.sub(r"<x-shape([^>]*)>\s*</x-shape>", shape, s)
    s = re.sub(r'data-crop="([^"]+)"\s+([^>]*?)style="', lambda m: m.group(2) + crop(m), s)
    s = s.replace("<section ", '<section class="slide" ', 1)
    slides.append(s.strip())

title = deck.get("title", "Slides")
tpl = open(os.path.join(HERE, "viewer.html"), encoding="utf-8").read()
fonts = "".join(f'<link rel="stylesheet" href="{html.escape(f["href"])}">' for f in deck.get("faces", {}).values())
page = tpl.replace("@TITLE", html.escape(title)).replace("@FONTS", fonts).replace("@SLIDES", "\n".join(slides))
open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(page)
open(os.path.join(OUT, ".nojekyll"), "w").close()
used = set(re.findall(r"media/([0-9a-f]{32}\.\w+)", page))
for f in os.listdir(MEDIA):
    if f not in used:
        os.remove(os.path.join(MEDIA, f))
print(len(slides), "slides,", len(used), "media files ->", os.path.join(OUT, "index.html"))
