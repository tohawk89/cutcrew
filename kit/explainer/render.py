"""Render an explainer: HyperFrames picture -> + voice -> finish.py (music bed, loudness, sound check).

  python kit/explainer/render.py projects/<name>            # draft  -> renders/<name>-draft.mp4
  python kit/explainer/render.py projects/<name> --final    # delivery quality -> renders/<name>-final.mp4
  python kit/explainer/render.py projects/<name> --span 31.5-33   # quick test clip of a span (picture only)

Music comes from vo.json "music" (a path), padded with silence to the film length so it never loops.
Run after: kit/explainer/film build (python projects/<name>/film.py) and timing.py.
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from kit.explainer.config import STYLE, OUT  # noqa: E402
NPX = "npx.cmd" if os.name == "nt" else "npx"
PY = str(ROOT / ".venv" / "Scripts" / "python.exe") if os.name == "nt" else sys.executable


def run(args, **kw):
    print("$", " ".join(str(a) for a in args)[:160])
    subprocess.run(args, check=True, **kw)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    ap.add_argument("--final", action="store_true")
    ap.add_argument("--span", help="start-end seconds, picture-only test render")
    a = ap.parse_args()
    P = Path(a.project).resolve()
    name = P.name
    HF = OUT / name
    t = json.loads((P / "timing.json").read_text(encoding="utf-8"))
    vo = json.loads((P / "vo.json").read_text(encoding="utf-8"))
    R = P / "renders"
    R.mkdir(exist_ok=True)
    hf = [NPX, "--yes", STYLE["hyperframes"], "render", ".", "--video-frame-format", "png", "--quiet"]
    if a.span:
        s0, s1 = a.span.split("-")
        out = R / f"test-{s0}-{s1}.mp4"
        run(hf + ["-q", "draft", "--start", s0, "--end", s1, "-o", str(out)], cwd=HF)
        print("test clip:", out)
        return
    pic = R / "animation.mp4"
    run(hf + ["-q", "delivery" if a.final else "draft", "-o", str(pic)], cwd=HF)
    cut = R / f"{name}-cut.mp4"
    run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", str(pic), "-i", str(R / "voice.wav"), "-map", "0:v", "-map", "1:a",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-shortest", str(cut)])
    out = R / f"{name}-{'final' if a.final else 'draft'}.mp4"
    cmd = [PY, str(ROOT / "scripts" / "finish.py"), str(cut), "--out", str(out)]
    if vo.get("music"):
        music = Path(vo["music"])
        music = music if music.is_absolute() else ROOT / music
        padded = P / "assets" / "music-padded.wav"
        run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", str(music), "-af", f"apad=whole_dur={t['total']}",
             "-t", str(t["total"]), "-ar", "44100", str(padded)])
        cmd += ["--music", str(padded)]
    if not a.final:
        cmd += ["--preset", "ultrafast"]
    print("$", " ".join(cmd)[:160])
    rc = subprocess.run(cmd).returncode
    if not out.exists():
        sys.exit(f"finish.py failed (exit {rc})")
    if rc:
        print("NOTE: the sound check flagged something (!! above). With a TTS voice + music bed the 'room tone' line\n"
              "      is the music in the pauses and needs no fix; any other !! line must be fixed before delivery.")
    print("done:", out)


if __name__ == "__main__":
    main()
