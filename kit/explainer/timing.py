"""Voice-driven timing: places every voice line, sizes every scene around its lines, writes
timing.json and renders/voice.wav.

  python kit/explainer/timing.py projects/<name>

vo.json:
  "scenes": [                       # in order; any key can be omitted (defaults in styles/explainer/style.json)
    {"key": "hook",  "lead": 0.6, "tail": 0.5, "min": 4.0},
    {"key": "brand", "hold": 1.0},  # extra seconds after the last line (e.g. let a logo breathe)
    {"key": "credits", "fixed": 5.0}  # silent scene of fixed length
  ],
  "lines": [{"id": "s1a", "scene": "hook", "text": "..."}],
  "pad_to": 57.0                    # optional: stretch the last scene so the film is at least this long
Scenes not listed in "scenes" are taken from the lines, in order.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from kit.explainer.config import STYLE  # noqa: E402
DEF = STYLE["timing"]


def dur(f):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)],
                                capture_output=True, text=True).stdout)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project")
    P = Path(ap.parse_args().project)
    vo = json.loads((P / "vo.json").read_text(encoding="utf-8"))
    order = [s for s in vo.get("scenes", [])]
    keys = [s["key"] for s in order]
    for line in vo["lines"]:
        if str(line["scene"]) not in keys:
            order.append({"key": str(line["scene"])})
            keys.append(str(line["scene"]))
    by_scene = {k: [l for l in vo["lines"] if str(l["scene"]) == k] for k in keys}

    t, windows, lines = 0.0, {}, {}
    for sc in order:
        k = sc["key"]
        start = t
        if "fixed" in sc:
            t = start + sc["fixed"]
        else:
            cur = start + sc.get("lead", DEF["lead"])
            for line in by_scene[k]:
                d = dur(P / "assets" / "voice" / f"{line['id']}.wav")
                lines[line["id"]] = {"start": round(cur, 2), "end": round(cur + d, 2)}
                cur += d + sc.get("gap", DEF["gap"])
            end = cur - sc.get("gap", DEF["gap"]) + sc.get("tail", DEF["tail"]) + sc.get("hold", 0)
            t = max(end, start + sc.get("min", 0))
        windows[k] = [round(start, 2), round(t, 2)]
    if vo.get("pad_to") and t < vo["pad_to"]:
        windows[keys[-1]][1] = round(vo["pad_to"], 2)
        t = vo["pad_to"]
    total = round(t, 2)
    (P / "timing.json").write_text(json.dumps({"total": total, "scenes": windows, "lines": lines}, indent=1), encoding="utf-8")

    # voice track on the timeline
    (P / "renders").mkdir(exist_ok=True)
    ids = list(lines)
    args = ["ffmpeg", "-nostdin", "-v", "error", "-y"]
    for i in ids:
        args += ["-i", str(P / "assets" / "voice" / f"{i}.wav")]
    f = ";".join(f"[{n}]adelay={int(lines[i]['start']*1000)}:all=1[a{n}]" for n, i in enumerate(ids))
    f += ";" + "".join(f"[a{n}]" for n in range(len(ids))) + f"amix=inputs={len(ids)}:normalize=0,apad=whole_dur={total}[out]"
    args += ["-filter_complex", f, "-map", "[out]", "-ar", "48000", "-ac", "1", "-t", str(total), str(P / "renders" / "voice.wav")]
    subprocess.run(args, check=True)

    for k, (a, b) in windows.items():
        print(f"scene {k:12} {a:6.2f} -> {b:6.2f}  ({b-a:4.1f}s)")
        for i in [l["id"] for l in by_scene.get(k, [])]:
            print(f"   {i:6} {lines[i]['start']:6.2f} -> {lines[i]['end']:6.2f}")
    print(f"total {total}s -> timing.json, renders/voice.wav")


if __name__ == "__main__":
    main()
