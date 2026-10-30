"""Cut a recording down using an edit decision list (EDL).

An EDL is a small JSON file listing the parts of the source to KEEP, in order:

  {
    "source": "../raw/take1.mp4",          # relative to the EDL file
    "keep": [
      {"start": 0.00, "end": 12.40, "note": "intro"},
      {"start": 15.10, "end": 48.75, "note": "main point"}
    ]
  }

Ranges may be reordered or repeated; they play in the order listed.
Any range may also set (for the footage behind a caption + source card, or a long hero shot):
  "speed": X    play it X times faster (0.5-4; 2 = half as long). Sound is time-stretched
                with its pitch kept. Below ~0.75 the picture starts to stutter.
  "hold": SEC   freeze its last frame for SEC seconds after it plays; the sound pads with silence.

Usage:
  # 1. Draft an EDL from a transcript: drops silences and filler words (um, uh...)
  python scripts/cut.py suggest projects/demo/transcripts/take1.json

  # 2. (Claude or you edit edl.json: remove retakes, reorder, trim)

  # 3. Render it. Also writes captions re-timed to the cut (<out>.srt / .json)
  python scripts/cut.py render projects/demo/edl.json --draft   # fast 1080p draft
  python scripts/cut.py render projects/demo/edl.json           # final quality
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import style  # noqa: E402
from transcribe import write_srt  # noqa: E402


def ffprobe(path: Path, entries: str, stream: str = "v:0") -> str:
    return subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", stream, "-show_entries", entries,
         "-of", "default=nw=1:nk=1", str(path)],
        check=True, capture_output=True, text=True,
    ).stdout.strip()


def suggest(args) -> None:
    tr_path = args.transcript.resolve()
    tr = json.loads(tr_path.read_text(encoding="utf-8"))
    for key, value in style.load(tr_path)["cut"].items():
        if getattr(args, key) is None:
            setattr(args, key, value)
    all_words = [w for s in tr["segments"] for w in s["words"]]
    words = [w for w in all_words if args.keep_fillers or not w["filler"]]
    if not words:
        sys.exit("Transcript has no words.")

    # Each range is [start, end, lo, hi]; lo/hi stop the padding from reaching into a cut filler.
    ranges, cur, lo = [], None, 0.0
    for w in all_words:
        if w["filler"] and not args.keep_fillers:
            if cur:
                cur[3] = w["start"]
                ranges.append(cur)
                cur = None
            lo = w["end"]
            continue
        if cur and w["start"] - cur[1] > args.max_gap:
            ranges.append(cur)
            cur = None
        if cur is None:
            cur, lo = [w["start"], w["end"], lo, tr["duration"]], 0.0
        cur[1] = max(cur[1], w["end"])
    if cur:
        ranges.append(cur)

    keep = []
    for a, b, lo, hi in ranges:
        a, b = max(lo, a - args.pad), min(hi, b + args.pad)
        if keep and a <= keep[-1]["end"]:
            keep[-1]["end"] = round(b, 3)
        else:
            keep.append({"start": round(a, 3), "end": round(b, 3)})
    for k in keep:
        k["note"] = " ".join(w["text"] for w in words if k["start"] <= w["start"] < k["end"])[:80]

    out = (args.out or tr_path.parent.parent / "edl.json").resolve()
    source = (tr_path.parent / tr["source"]).resolve()
    out.write_text(json.dumps({"source": Path(_rel(source, out.parent)).as_posix(),
                               "transcript": Path(_rel(tr_path, out.parent)).as_posix(),
                               "keep": keep}, indent=1, ensure_ascii=False), encoding="utf-8")
    kept = sum(k["end"] - k["start"] for k in keep)
    print(f"EDL: {len(keep)} ranges, {kept:.1f}s of {tr['duration']:.1f}s kept "
          f"({tr['duration'] - kept:.1f}s removed) -> {out}")


def _rel(p: Path, base: Path) -> str:
    try:
        return os.path.relpath(p, base)
    except ValueError:  # different drives (e.g. C: vs E:) have no relative path
        return str(p)


def _tempo_chain(x: float) -> list:
    """atempo factors (each 0.5-2, the range every ffmpeg build accepts) multiplying to x."""
    out = []
    while x > 2:
        out.append(2.0)
        x /= 2
    while x < 0.5:
        out.append(0.5)
        x /= 0.5
    return out + [x]


def proxy(src: Path, folder: Path) -> Path:
    """1080p copy of `src` for fast drafts, made once (kept in renders/, never in raw/).
    Timestamps pass through untouched, so EDL times and sync are identical to the source."""
    out = folder / f"{src.stem}-proxy.mkv"
    if out.exists() and out.stat().st_mtime >= src.stat().st_mtime:
        return out
    folder.mkdir(parents=True, exist_ok=True)
    print(f"Making a 1080p draft proxy of {src.name} (once)...", file=sys.stderr)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-stats", "-i", str(src),
                    "-map", "0:v:0", "-map", "0:a?", "-vf", "scale=-2:'min(1080,ih)'",
                    "-fps_mode", "passthrough", "-c:v", "libx264", "-preset", "veryfast",
                    "-crf", "20", "-g", "30", "-c:a", "copy", str(out)], check=True)
    return out


def render(args) -> None:
    edl_path = args.edl.resolve()
    edl = json.loads(edl_path.read_text(encoding="utf-8"))
    src = (edl_path.parent / edl["source"]).resolve()
    suffix = "-cut-draft.mp4" if args.draft else "-cut.mp4"
    out = (args.out or edl_path.parent / "renders" / f"{edl_path.stem}{suffix}").resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    export = style.load(edl_path)["export"]

    fps = Fraction(ffprobe(src, "stream=r_frame_rate"))
    has_audio = bool(ffprobe(src, "stream=codec_type", "a:0"))
    if args.draft:
        src = proxy(src, edl_path.parent / "renders")
        args.preset = args.preset or "ultrafast"

    # Snap every cut to the frame grid so audio and video stay in sync over many cuts.
    snap = lambda t: round(Fraction(t).limit_denominator(100000) * fps) / fps  # noqa: E731
    keep = [k for k in edl["keep"] if snap(k["end"]) > snap(k["start"])]
    ranges = [(snap(k["start"]), snap(k["end"])) for k in keep]
    speeds = [float(k.get("speed", 1)) for k in keep]
    holds = [float(k.get("hold", 0)) for k in keep]
    if any(not 0.5 <= x <= 4 for x in speeds):
        sys.exit('"speed" must be between 0.5 and 4')
    half = 1 / (2 * fps)
    # Phone/action cams record variable frame rate (dropping frames in low light). Resample to
    # constant fps from the real timestamps first, or the picture drifts away from the sound.
    cfr = f"fps={fps}"

    in_order = all(ranges[i][1] <= ranges[i + 1][0] for i in range(len(ranges) - 1))
    # Speed changes and freezes before the last range need the per-range path below.
    plain = all(x == 1 for x in speeds) and not any(holds[:-1])
    if in_order and plain:
        # One pass with select: fast and light on memory.
        expr = "+".join(f"between(t,{float(a - half):.4f},{float(b - half):.4f})" for a, b in ranges)
        graph = f"[0:v]setpts=PTS-STARTPTS,{cfr},select='{expr}',setpts=N/FRAME_RATE/TB[v]"
        if has_audio:
            # Audio per range with 10 ms fades, so jump cuts never click.
            n = len(ranges)
            parts = [f"[0:a]asetpts=PTS-STARTPTS,aresample=48000,asplit={n}" + "".join(f"[sa{i}]" for i in range(n))]
            for i, (a, b) in enumerate(ranges):
                d = float(b - a)
                parts.append(f"[sa{i}]atrim={float(a):.4f}:{float(b):.4f},asetpts=PTS-STARTPTS,"
                             f"afade=t=in:d=0.01,afade=t=out:st={max(d - 0.01, 0):.4f}:d=0.01[a{i}]")
            parts.append("".join(f"[a{i}]" for i in range(n)) + f"concat=n={n}:v=0:a=1[a]")
            graph += ";" + ";".join(parts)
    else:
        # Reordered/repeated ranges, speed changes or freezes: trim each piece, shape it, concat.
        n = len(ranges)
        parts = [f"[0:v]setpts=PTS-STARTPTS,{cfr},split={n}" + "".join(f"[sv{i}]" for i in range(n))]
        if has_audio:
            parts.append(f"[0:a]asetpts=PTS-STARTPTS,aresample=48000,asplit={n}" + "".join(f"[sa{i}]" for i in range(n)))
        for i, ((a, b), x, h) in enumerate(zip(ranges, speeds, holds)):
            v = f"[sv{i}]trim={float(a):.4f}:{float(b):.4f},setpts=PTS-STARTPTS"
            if x != 1:
                v += f",setpts=PTS/{x},{cfr}"
            if h > 0:
                v += f",tpad=stop_mode=clone:stop_duration={h:.3f}"
            parts.append(v + f"[v{i}]")
            if has_audio:
                d = float(b - a) / x
                af = f"[sa{i}]atrim={float(a):.4f}:{float(b):.4f},asetpts=PTS-STARTPTS"
                if x != 1:
                    af += "," + ",".join(f"atempo={f:.6f}" for f in _tempo_chain(x))
                af += f",afade=t=in:d=0.01,afade=t=out:st={max(d - 0.01, 0):.4f}:d=0.01"
                if h > 0:
                    af += f",apad=pad_dur={h:.3f}"
                parts.append(af + f"[a{i}]")
        pads = "".join(f"[v{i}]" + (f"[a{i}]" if has_audio else "") for i in range(n))
        parts.append(f"{pads}concat=n={n}:v=1:a={int(has_audio)}[v]" + ("[a]" if has_audio else ""))
        graph = ";".join(parts)

    # On the plain path, "hold" on the last range freezes its final frame (a long hero shot when
    # the footage runs short). Invisible on a locked-off still; the audio pads with silence.
    hold = holds[-1] if in_order and plain else 0
    vout, aout = "[v]", "[a]"
    if hold > 0:
        graph += f";[v]tpad=stop_mode=clone:stop_duration={hold:.3f}[vh]"
        vout = "[vh]"
        if has_audio:
            graph += f";[a]apad=pad_dur={hold:.3f}[ah]"
            aout = "[ah]"

    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(graph)
        graph_file = f.name
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-stats", "-i", str(src),
           "-/filter_complex", graph_file, "-map", vout]
    if has_audio:
        cmd += ["-map", aout, "-c:a", "aac", "-b:a", "192k"]
    cmd += ["-c:v", "libx264", "-preset", args.preset or export["preset"], "-crf", str(export["crf"]),
            "-pix_fmt", "yuv420p",
            "-r", str(fps), "-movflags", "+faststart", str(out)]
    print(f"Rendering {len(ranges)} ranges from {src.name}...", file=sys.stderr)
    subprocess.run(cmd, check=True)
    Path(graph_file).unlink(missing_ok=True)

    # Re-time the transcript to the new cut so captions line up.
    if edl.get("transcript"):
        tr_path = (edl_path.parent / edl["transcript"]).resolve()
        tr = json.loads(tr_path.read_text(encoding="utf-8"))
        words, offset = [], 0.0
        all_words = [w for s in tr["segments"] for w in s["words"]]
        for (a, b), x, h in zip(ranges, speeds, holds):
            a, b = float(a), float(b)
            for w in all_words:
                if a <= (w["start"] + w["end"]) / 2 < b and not w["filler"]:
                    words.append({**w, "start": round((max(w["start"], a) - a) / x + offset, 3),
                                  "end": round((min(w["end"], b) - a) / x + offset, 3)})
            offset += (b - a) / x + h
        out.with_suffix(".json").write_text(json.dumps(
            {"source": out.name, "duration": round(offset, 3), "model": tr.get("model"),
             "segments": [{"start": 0, "end": round(offset, 3),
                           "text": " ".join(w["text"] for w in words), "words": words}]},
            indent=1, ensure_ascii=False), encoding="utf-8")
        write_srt(out.with_suffix(".srt"), words)
    print(f"Done -> {out}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("suggest", help="draft an EDL from a transcript")
    s.add_argument("transcript", type=Path)
    s.add_argument("--out", type=Path, help="default: <project>/edl.json")
    # Defaults for these come from style.json ("cut" section).
    s.add_argument("--max-gap", type=float, help="pauses longer than this (s) are cut")
    s.add_argument("--pad", type=float, help="breathing room kept around speech (s)")
    s.add_argument("--keep-fillers", action=argparse.BooleanOptionalAction, help="keep um/uh")
    s.set_defaults(func=suggest)

    r = sub.add_parser("render", help="render an EDL to MP4")
    r.add_argument("edl", type=Path)
    r.add_argument("--out", type=Path, help="default: <project>/renders/<edl>-cut.mp4")
    r.add_argument("--preset", help="x264 preset (ultrafast for quick drafts; default from style.json)")
    r.add_argument("--draft", action="store_true",
                   help="fast 1080p draft from a proxy (made once) -> <edl>-cut-draft.mp4")
    r.set_defaults(func=render)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
