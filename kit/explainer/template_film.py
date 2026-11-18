"""Film for this project (made from kit/explainer/template_film.py — edit freely).

Build:   .venv\\Scripts\\python.exe projects/<name>/film.py   (-> animations/explainers/<name>/)
Stills:  .venv\\Scripts\\python.exe projects/<name>/film.py --stills     (one PNG per scene, mid-scene, for approval)
Each scene function returns SVG and registers its motion on the film with absolute times from f.line()/f.window().
"""
import sys
from pathlib import Path

P = Path(__file__).resolve().parent
sys.path.insert(0, str(P.parents[1]))
from kit.explainer.film import Film, STYLE          # noqa: E402
from kit.explainer.character import Character       # noqa: E402
from kit.explainer import parts as kp                # noqa: E402

C = STYLE["colors"]
BRAND, BRAND_SH, BRAND_DARK, BRAND_TEXT = "#3FC1AE", "#30A492", "#2F2A5B", "#23897A"   # <- sample from the client's logo
ch = Character(shirt=BRAND, shirt_shadow=BRAND_SH, pants=BRAND_DARK)
f = Film(P)
LOGO_RATIO = 216 / 1369                                # <- logo height / width
logo_href = f.asset("assets/logo.png") if (P / "assets" / "logo.png").exists() else None


def logo(x, y, w, white=False):
    return kp.logo(logo_href, x, y, w, LOGO_RATIO, white) if logo_href else kp.text(x, y + 30, "LOGO", 90, color="#FFFFFF" if white else BRAND_DARK)


def hook():
    a, b = f.window("hook")
    orno = f.line("h2") + 1.0                           # the beat where the mood turns
    art = kp.svg(
        '<path d="M0,880 Q480,850 960,872 T1920,862 L1920,1080 L0,1080 Z" fill="#BFE0CD"/>'
        f'<g transform="translate(1250,882) scale(1.9)">{kp.g("hk-house", kp.house(door=BRAND, door_sh=BRAND_SH))}</g>'
        + kp.g("hk-crack", kp.crack(1420, 470, 190, 7))
        + ch.person("hk-man", "keys", 470, 960, 0.95, swap_to="afraid")
        + kp.g("hk-title", kp.text(960, 110, "A good one... or not?", 64)), "#DCEFEA")
    f.scene("hook", art)
    f.pop("#hk-house", a + 0.05, 0.7, 0.85, "back.out(1.4)", "50% 100%")
    f.slide("#hk-man", a + 0.15, -520, 0.8)
    f.idle("hk-man", a + 1.0, b, (a + 1.6,))
    f.rise("#hk-title", f.line("h2") - 0.1, 30, 0.45)
    f.draw_down("#hk-crack", orno, 0.5)
    f.face_swap("hk-man", orno, arm_deg=22)


def how():
    a, b = f.window("how")
    cards, ids = kp.step_cards([("Add your house", ["Set up in a minute."], "house"),
                                ("Check room by room", ["A checklist shows you", "what to look for."], "checklist"),
                                ("Snap a photo", ["Photo proof for", "every defect."], "camera"),
                                ("Get your report", ["Ready to send to", "your developer."], "report")], num_bg=BRAND_TEXT)
    f.scene("how", kp.svg(kp.g("hw-title", kp.text(960, 130, "How it works", 60)) + cards, C["cream"]))
    f.rise("#hw-title", a, 30, 0.4)
    for i, line in enumerate(("w1", "w2", "w3", "w4")):
        f.rise(f"#{ids[i]}", f.line(line) - 0.15, 120, 0.55)


def cta():
    a, b = f.window("cta")
    art = kp.svg('<path d="M0,980 L1920,980 L1920,1080 L0,1080 Z" fill="#E8E0D2"/>'
                 + ch.person("ct-man", "point", 380, 985, 1.0)
                 + kp.g("ct-logo", logo(1360, 270, 760))
                 + kp.g("ct-reg", kp.text(1360, 520, "Register now", 96))
                 + kp.g("ct-btn", f'<rect x="1040" y="590" width="640" height="130" rx="65" fill="{BRAND_TEXT}"/>'
                        + kp.text(1360, 676, "example.com", 64, color="#FFFFFF")), C["cream"])
    f.scene("cta", art)
    f.slide("#ct-man", a + 0.1, -600, 0.7)
    f.idle("ct-man", a + 0.8, b, (a + 2.0,))
    f.pop("#ct-logo", a + 0.2, 0.55, 0.7, "back.out(1.5)")
    f.rise("#ct-reg", f.line("c1") - 0.15, 40, 0.5)
    f.pop("#ct-btn", f.line("c1") + 0.4, 0.5, 0.5)
    f.pulse("#ct-btn", f.line("c1") + 1.0, 2)


def credits():
    a, b = f.window("credits")
    rows = [tuple(r) for r in STYLE["credits"]] + [("Music", "“Track” by Artist", "Pixabay")]
    f.scene("credits", kp.svg(kp.credits(rows, logo(960, 270, 560, white=True), "example.com"), BRAND_DARK))
    f.pop("#cr-logo", a + 0.1, 0.5, 0.8, "power3.out")
    f.rise("#cr-url", a + 0.3, 20, 0.4)
    f.stagger_in(".s-cr-row", a + 0.35)


for scene in (hook, how, cta, credits):
    scene()
HF = f.write()

if "--stills" in sys.argv:
    import subprocess
    mids = ",".join(str(round((x + y) / 2 + (y - x) * 0.3, 2)) for x, y in f.windows.values())
    subprocess.run(["npx.cmd" if sys.platform == "win32" else "npx", "--yes", STYLE["hyperframes"], "snapshot",
                    "--at", mids, "--no-end", "-o", str(P / "assets" / "stills")], cwd=HF)
