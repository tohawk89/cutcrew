"""House style: the defaults every script uses, learned from the user's feedback.

  style.json                     lasting preferences (all videos)
  projects/<name>/style.json     overrides for one video only (same keys, any subset)

Command-line flags override both. STYLE.md explains the *why* behind these numbers.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _merge(base: dict, over: dict) -> dict:
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _merge(base[k], v)
        else:
            base[k] = v
    return base


def project_dir(path: Path | None) -> Path | None:
    """The projects/<name> folder that `path` lives in, if any."""
    if path is None:
        return None
    projects = ROOT / "projects"
    for p in [path.resolve(), *path.resolve().parents]:
        if p.parent == projects:
            return p
    return None


def load(near: Path | None = None) -> dict:
    """House style, with the project's overrides applied when `near` is inside a project."""
    house = ROOT / "style.json"
    if not house.exists():  # fresh clone before setup.ps1: use the starter style
        house = ROOT / "defaults" / "style.json"
    style = json.loads(house.read_text(encoding="utf-8"))
    proj = project_dir(near)
    if proj and (proj / "style.json").exists():
        _merge(style, json.loads((proj / "style.json").read_text(encoding="utf-8")))
    return style


def ass_color(hex_rgb: str) -> str:
    """'#RRGGBB' -> ASS subtitle colour '&H00BBGGRR'."""
    h = hex_rgb.lstrip("#")
    return f"&H00{h[4:6]}{h[2:4]}{h[0:2]}".upper()


def caption_force_style(c: dict) -> str:
    return ",".join([
        f"FontName={c['font']}", f"FontSize={c['size']}", f"Bold={int(c['bold'])}",
        f"PrimaryColour={ass_color(c['color'])}", f"OutlineColour={ass_color(c['outline_color'])}",
        "BorderStyle=1", f"Outline={c['outline']}", "Shadow=0", f"MarginV={c['margin_v']}",
    ])
