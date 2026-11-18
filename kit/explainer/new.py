"""Start a new explainer project from the kit.

  python kit/explainer/new.py <kebab-name>

Creates projects/<name>/ with raw/, assets/, renders/, a vo.json script skeleton, a film.py (scene code,
from template_film.py) and notes.md (intake + gates). Then: edit vo.json -> voice.py -> timing.py ->
film.py --stills -> (user says go) -> render.py.
"""
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KIT = Path(__file__).resolve().parent

VO = {
    "voice": "af_heart", "speed": 0.95,
    "music": None,
    "scenes": [{"key": "hook", "lead": 0.6, "tail": 0.5}, {"key": "how", "lead": 0.3},
               {"key": "cta", "lead": 0.3, "tail": 1.0}, {"key": "credits", "fixed": 5.0}],
    "lines": [
        {"id": "h1", "scene": "hook", "text": "Got the keys to your new home?"},
        {"id": "h2", "scene": "hook", "text": "It could be perfect... or not."},
        {"id": "w1", "scene": "how", "text": "Add your house in a minute."},
        {"id": "w2", "scene": "how", "text": "Check it room by room, with a ready-made checklist."},
        {"id": "w3", "scene": "how", "text": "Snap a photo of every defect."},
        {"id": "w4", "scene": "how", "text": "Then get a report you can send straight to your developer."},
        {"id": "c1", "scene": "cta", "text": "Register now at example dot com."},
    ],
}

NOTES = """# {name}

Animated explainer. Style: `styles/explainer/STYLE.md` (+ style.json). Kit: `kit/explainer/`.

## Status
**DISCUSSION / SCRIPT STAGE. Render nothing until the user says go.**

## Intake
- Product / URL:
- Format (16:9 / 9:16), length:
- Language, voice (Kokoro af_heart is house):
- Music (light corporate, not Content ID registered, 15 LU under voice):
- Real product clips (plain 9:16, no zoom/cards/cursor, one file per shot):
- CTA:
- Credits (house rows in style.json + music):
- Brand colours (sample from the logo):

## Script & storyboard
| # | Scene | Voiceover | On screen / motion | ~Sec |
|---|---|---|---|---|

## Approvals
| Date | Gate | What the user said |
|---|---|---|
"""


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    name = sys.argv[1]
    P = ROOT / "projects" / name
    if (P / "film.py").exists():
        sys.exit(f"{P} already has a film.py; not overwriting.")
    for d in ("raw", "assets", "renders"):
        (P / d).mkdir(parents=True, exist_ok=True)
    if not (P / "vo.json").exists():
        (P / "vo.json").write_text(json.dumps(VO, indent=1), encoding="utf-8")
    shutil.copy(KIT / "template_film.py", P / "film.py")
    if not (P / "notes.md").exists():
        (P / "notes.md").write_text(NOTES.format(name=name), encoding="utf-8")
    print(f"created {P}: vo.json, film.py, notes.md, raw/, assets/, renders/")


if __name__ == "__main__":
    main()
