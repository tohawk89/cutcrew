"""Film: turns a project's scenes (SVG strings) + timing.json into a HyperFrames composition.

    from kit.explainer.film import Film
    f = Film("projects/my-video")              # reads timing.json (made by timing.py)
    a, b = f.window("hook")                    # scene start/end in seconds (absolute)
    f.scene("hook", svg_string)                # one timed <section> per scene, in order
    f.pop("#logo", f.line("s4a") - 0.15)       # motion helpers take ABSOLUTE times
    f.write()                                  # -> animations/explainers/<name>/index.html (+ assets, meta)

Rules baked in (styles/explainer/STYLE.md): no slow camera pushes (there is no helper for one; only the
fast zoom_through between scenes), rotations spin around their own centre, text renders with
geometricPrecision so it never shimmers.
"""
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from kit.explainer.config import STYLE, OUT  # noqa: E402


class Film:
    def __init__(self, project_dir, name=None, bg="#F4F1EC"):
        self.P = Path(project_dir).resolve()
        self.name = name or self.P.name
        self.HF = OUT / self.name
        t = json.loads((self.P / "timing.json").read_text(encoding="utf-8"))
        self.windows = {k: tuple(v) for k, v in t["scenes"].items()}
        self.lines = t["lines"]
        self.total = t["total"]
        self.bg = bg
        self.js, self.sections, self.root_html, self.css, self.setup = [], [], [], [], []
        self._track = 1
        (self.HF / "assets" / "fonts").mkdir(parents=True, exist_ok=True)

    # ---- time ----
    def window(self, key):
        return self.windows[key]

    def line(self, line_id):
        """absolute start of a voice line"""
        return self.lines[line_id]["start"]

    def line_end(self, line_id):
        return self.lines[line_id]["end"]

    # ---- assets ----
    def asset(self, src, name=None):
        """Copy a file into the composition's assets/ (once) and return its relative path."""
        src = Path(src)
        if not src.is_absolute():
            src = self.P / src
        dst = self.HF / "assets" / (name or src.name)
        if not dst.exists() or dst.stat().st_size != src.stat().st_size:
            shutil.copy(src, dst)
        return f"assets/{dst.name}"

    # ---- structure ----
    def scene(self, key, art, white_in=False):
        """Add a scene (SVG string). white_in=True fades it in from white (after a zoom_through)."""
        a, b = self.windows[key]
        extra = f'<div class="white" id="{key}-white"></div>' if white_in else ""
        self.sections.append(f'<section id="sc-{key}" class="clip" data-start="{a}" data-duration="{round(b-a,3)}" '
                             f'data-track-index="{self._track}"><div class="cam" id="{key}-cam">{art}</div>{extra}</section>')
        self._track += 1
        if white_in:
            self.setup.append(f'gsap.set("#{key}-white", {{ opacity: 0 }});')
            self.js.append(f'tl.fromTo("#{key}-white",{{opacity:1}},{{opacity:0,duration:0.35,ease:"none"}},{a});')

    def add_root(self, html, css="", setup=""):
        self.root_html.append(html)
        if css:
            self.css.append(css)
        if setup:
            self.setup.append(setup)

    def tween(self, js):
        """Raw GSAP line using the timeline `tl`, e.g. 'tl.to("#x",{x:10,duration:1},12.3);'"""
        self.js.append(js)

    # ---- motion helpers (absolute seconds) ----
    def pop(self, sel, t, dur=0.45, frm=0.0, ease="back.out(1.7)", origin="50% 50%"):
        self.js.append(f'tl.from("{sel}",{{scale:{frm},opacity:0,transformOrigin:"{origin}",duration:{dur},ease:"{ease}"}},{round(t,3)});')

    def rise(self, sel, t, dy=60, dur=0.5):
        self.js.append(f'tl.from("{sel}",{{y:{dy},opacity:0,duration:{dur},ease:"power3.out"}},{round(t,3)});')

    def slide(self, sel, t, dx, dur=0.6):
        self.js.append(f'tl.from("{sel}",{{x:{dx},duration:{dur},ease:"power3.out"}},{round(t,3)});')

    def fadein(self, sel, t, dur=0.3):
        self.js.append(f'tl.from("{sel}",{{opacity:0,duration:{dur},ease:"none"}},{round(t,3)});')

    def draw_down(self, sel, t, dur=0.6):
        """Reveal top to bottom (cracks, drips, lines)."""
        self.js.append(f'tl.from("{sel}",{{scaleY:0,transformOrigin:"50% 0%",duration:{dur},ease:"power2.inOut"}},{round(t,3)});')

    def stagger_in(self, sel, t, each=0.12, dy=16):
        self.js.append(f'tl.from("{sel}",{{y:{dy},opacity:0,duration:0.35,stagger:{each},ease:"power3.out"}},{round(t,3)});')

    def pulse(self, sel, t, times=3, scale=1.06):
        self.js.append(f'tl.to("{sel}",{{scale:{scale},transformOrigin:"50% 50%",duration:0.45,yoyo:true,repeat:{times*2-1},ease:"sine.inOut"}},{round(t,3)});')

    def spin(self, sel, t, dur, deg, cx, cy):
        """Rotate around a point in SVG units (its own centre) — never the frame corner."""
        self.js.append(f'tl.to("{sel}",{{rotation:{deg},svgOrigin:"{cx} {cy}",duration:{dur},ease:"none"}},{round(t,3)});')

    def idle(self, pid, t0, t1, blinks=()):
        """Gentle bob between t0..t1 plus blinks at the given times (character made by Character.person)."""
        n = max(1, int((t1 - t0) / 1.6))
        self.js.append(f'tl.to("#{pid}-bob",{{y:-6,duration:0.8,ease:"sine.inOut",yoyo:true,repeat:{n*2-1}}},{round(t0,3)});')
        for bt in blinks:
            self.js.append(f'tl.to("#{pid}-eyes",{{scaleY:0.1,transformOrigin:"50% 50%",duration:0.07,yoyo:true,repeat:1}},{round(bt,3)});')

    def face_swap(self, pid, t, arm_deg=None):
        """Swap face1 -> face2 (person(..., swap_to=...)); optionally turn the front arm at the shoulder."""
        self.js.append(f'tl.to("#{pid}-face1",{{opacity:0,duration:0.06}},{round(t,3)});')
        self.js.append(f'tl.to("#{pid}-face2",{{opacity:1,duration:0.06}},{round(t,3)});')
        self.js.append(f'tl.from("#{pid}-face2",{{scale:0.85,transformOrigin:"50% 50%",duration:0.3,ease:"back.out(3)"}},{round(t,3)});')
        if arm_deg:
            self.js.append(f'tl.to("#{pid}-arm",{{rotation:{arm_deg},svgOrigin:"84 -470",duration:0.35,ease:"back.out(2)"}},{round(t+0.05,3)});')

    def zoom_through(self, key, t, origin="50% 50%", scale=2.2):
        """Fast zoom into a point + white flash at the end of a scene (the only allowed camera move).
        Give the next scene white_in=True."""
        self.js.append(f'tl.to("#{key}-cam",{{scale:{scale},transformOrigin:"{origin}",duration:0.6,ease:"power3.in"}},{round(t,3)});')
        self.sections[-1] = self.sections[-1].replace(
            "</section>", f'<div class="white" id="{key}-flash"></div></section>')
        self.setup.append(f'gsap.set("#{key}-flash", {{ opacity: 0 }});')
        self.js.append(f'tl.to("#{key}-flash",{{opacity:1,duration:0.35,ease:"none"}},{round(t+0.25,3)});')

    def step_list_states(self, prefix, times):
        """Light up step_list rows: times[i] = when step i becomes current (absolute)."""
        for i, t in enumerate(times):
            self.js.append(f'tl.to("#{prefix}-base{i}",{{opacity:0,duration:0.2}},{round(t,3)});')
            self.js.append(f'tl.to("#{prefix}-now{i}",{{opacity:1,duration:0.2}},{round(t,3)});')
            if i + 1 < len(times):
                self.js.append(f'tl.to("#{prefix}-done{i}",{{opacity:1,duration:0.2}},{round(times[i+1],3)});')
                self.js.append(f'tl.to("#{prefix}-now{i}",{{opacity:0,duration:0.2}},{round(times[i+1],3)});')

    def phone_in_out(self, start, end):
        rig = '["#rig-back","#phone-rig","#rig-front"]'
        self.js.append(f'tl.from({rig},{{y:1150,duration:0.55,ease:"power3.out"}},{start});')
        self.js.append(f'tl.to({rig},{{y:1150,duration:0.45,ease:"power3.in"}},{round(end-0.45,3)});')

    # ---- output ----
    def write(self, title=None):
        font = ROOT / STYLE["font"]["file"]
        shutil.copy(font, self.HF / "assets" / "fonts" / font.name)
        fam = STYLE["font"]["family"]
        fmt = STYLE["format"]
        html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width={fmt['width']}, height={fmt['height']}" />
<title>{title or self.name}</title>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>
@font-face {{ font-family: "{fam}"; src: url("assets/fonts/{font.name}") format("truetype"); font-weight: 300 900; }}
body {{ margin: 0; background: {self.bg}; }}
#root {{ position: relative; width: 100%; height: 100%; overflow: hidden; background: {self.bg}; }}
.clip {{ position: absolute; inset: 0; overflow: hidden; }}
.cam {{ position: absolute; inset: 0; }}
.art {{ position: absolute; left: 0; top: 0; width: {fmt['width']}px; height: {fmt['height']}px; display: block;
        text-rendering: geometricPrecision; shape-rendering: geometricPrecision; }}
.art text, .t {{ font-family: "{fam}", "Segoe UI", sans-serif; text-rendering: geometricPrecision; }}
.white {{ position: absolute; inset: 0; background: #FFFFFF; opacity: 0; pointer-events: none; }}
{chr(10).join(self.css)}
</style>
</head>
<body>
<div id="root" data-composition-id="{self.name}" data-start="0" data-width="{fmt['width']}" data-height="{fmt['height']}" data-duration="{self.total}" data-fps="{fmt['fps']}">
{''.join(self.sections)}
{''.join(self.root_html)}
</div>
<script>
const tl = gsap.timeline({{ paused: true }});
{chr(10).join(self.setup)}
{chr(10).join(self.js)}
window.__timelines["{self.name}"] = tl;
</script>
</body>
</html>
"""
        (self.HF / "index.html").write_text(html, encoding="utf-8")
        (self.HF / "meta.json").write_text(json.dumps({"id": self.name, "name": title or self.name}) + "\n", encoding="utf-8")
        shutil.copy(ROOT / "animations" / "hyperframes.json", self.HF / "hyperframes.json")
        print(f"written {self.HF / 'index.html'}  ({len(self.sections)} scenes, {len(self.js)} tweens, {self.total}s)")
        return self.HF
