"""Voice for an explainer: one Kokoro file per sentence (so every pop can land on its word).

  python kit/explainer/voice.py projects/<name>                 # all lines in vo.json -> assets/voice/<id>.wav
  python kit/explainer/voice.py projects/<name> --only s1a,s3b  # re-make some lines (after a wording change)
  python kit/explainer/voice.py projects/<name> --samples "One line to compare." --voices af_heart,am_michael,bf_emma
                                                                # -> assets/voice-samples/<voice>.wav

vo.json: {"voice": "af_heart", "speed": 0.95, "lines": [{"id": "s1a", "scene": "hook", "text": "..."}, ...]}
Kokoro runs through `hyperframes tts` with the Python named in style.json voice.tts_python (empty = this Python).
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from kit.explainer.config import STYLE, TTS_PYTHON  # noqa: E402
CFG = STYLE["voice"]


def tts(text, out, voice, speed):
    with tempfile.TemporaryDirectory() as tmp:
        txt, wav = Path(tmp) / "line.txt", Path(tmp) / "line.wav"
        txt.write_text(text, encoding="utf-8")
        env = {**os.environ, "HYPERFRAMES_PYTHON": TTS_PYTHON}
        npx = "npx.cmd" if os.name == "nt" else "npx"
        r = subprocess.run([npx, "--yes", CFG["hyperframes_tts"], "tts", str(txt), "-o", str(wav), "-v", voice, "-s", str(speed)],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, stdin=subprocess.DEVNULL)
        if r.returncode or not wav.exists():
            sys.exit(f"tts failed for {out.name}: {(r.stderr or r.stdout)[-400:]}")
        out.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", str(wav), "-ac", "1", "-ar", "48000",
                        "-c:a", "pcm_s16le", str(out)], check=True)


def dur(f):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)],
                                capture_output=True, text=True).stdout)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("--only", help="comma-separated line ids to (re)make")
    ap.add_argument("--force", action="store_true", help="re-make every line")
    ap.add_argument("--samples", help="make this one line in several voices instead")
    ap.add_argument("--voices", default="af_heart,am_michael,bf_emma")
    a = ap.parse_args()
    P = Path(a.project)
    vo = json.loads((P / "vo.json").read_text(encoding="utf-8")) if (P / "vo.json").exists() else {}
    voice, speed = vo.get("voice", CFG["voice"]), vo.get("speed", CFG["speed"])
    if a.samples:
        for v in a.voices.split(","):
            out = P / "assets" / "voice-samples" / f"{v}.wav"
            tts(a.samples, out, v, speed)
            print(f"{v:12} {dur(out):5.2f}s  {out}")
        return
    only = set(a.only.split(",")) if a.only else None
    for line in vo["lines"]:
        out = P / "assets" / "voice" / f"{line['id']}.wav"
        if only is not None and line["id"] not in only:
            continue
        if out.exists() and not a.force and only is None:
            continue
        tts(line["text"], out, voice, speed)
        print(f"{line['id']:6} {dur(out):5.2f}s  {line['text']}")


if __name__ == "__main__":
    main()
