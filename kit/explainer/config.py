"""Explainer settings: your styles/explainer/style.json, else the shipped defaults/explainer/style.json."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_mine = ROOT / "styles" / "explainer" / "style.json"
STYLE = json.loads((_mine if _mine.exists() else ROOT / "defaults" / "explainer" / "style.json").read_text(encoding="utf-8"))
# Python that has kokoro-onnx installed (hyperframes tts runs Kokoro through it); empty = this Python.
TTS_PYTHON = STYLE["voice"].get("tts_python") or sys.executable
if not Path(TTS_PYTHON).exists():
    TTS_PYTHON = sys.executable
OUT = ROOT / "animations" / "explainers"   # one HyperFrames project per film: OUT/<project-name>/
