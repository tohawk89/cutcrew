"""Final mix and export: overlays and captions on the picture; music, SFX and loudness on the sound.

Usage:
  python scripts/finish.py projects/demo/renders/edl-cut.mp4 \
      --music library/music/chill.mp3 \
      --overlay projects/demo/assets/intro-title.mp4@0 \
      --overlay projects/demo/assets/stat-callout.webm@42.5 \
      --sfx library/sfx/whoosh.wav@42.3 \
      --captions projects/demo/renders/edl-cut.srt

Overlays: an MP4 covers the full frame (cutaway); a WebM/MOV with transparency
is layered on top of the footage. They are scaled to the video's size.

Picture and sound are made separately, then joined without re-encoding:
  picture  overlays + captions, encoded once and cached in renders/.cache/. Re-running with the
           same picture inputs reuses it, so a sound-only change (music, levels) takes seconds.
           With no overlays or captions the cut's own picture is copied as-is.
  sound    audio.py master: clean-up, music bed, SFX, loudness; then audio.py check reports
           loudness, true peak, room tone and music level (exit code 1 if anything is off).
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import audio  # noqa: E402
import style  # noqa: E402
from audio import probe, timed  # noqa: E402


def stamp(path: Path) -> list:
    st = path.stat()
    return [str(path), st.st_size, int(st.st_mtime)]


def picture(video: Path, overlays, captions: Path | None, house: dict, preset: str, cache: Path) -> Path:
    """The finished picture (video stream only); cached by its inputs."""
    if not overlays and not captions:
        return video
    key = {"video": stamp(video), "overlays": [stamp(p) + [at] for p, at in overlays],
           "captions": stamp(captions) if captions else None,
           "caption_style": house["captions"] if captions else None,
           "preset": preset, "crf": house["export"]["crf"]}
    out, keyfile = cache / f"{video.stem}.picture.mp4", cache / f"{video.stem}.picture.json"
    if out.exists() and keyfile.exists() and json.loads(keyfile.read_text()) == key:
        print("Picture unchanged: reusing the cached render.", file=sys.stderr)
        return out

    w, h = probe(video, "stream=width,height", "v:0").split()
    inputs, graph, v = ["-i", str(video)], [], "[0:v]"
    for i, (path, at) in enumerate(overlays):
        # ffmpeg's native VP9 decoder drops the alpha channel; libvpx keeps it.
        dec = ["-c:v", "libvpx-vp9"] if path.suffix.lower() == ".webm" else []
        inputs += [*dec, "-i", str(path)]
        odur = float(probe(path, "format=duration"))
        graph.append(f"[{i + 1}:v]scale={w}:{h}:force_original_aspect_ratio=decrease,"
                     f"pad={w}:{h}:-1:-1:color=0x00000000,format=yuva420p,"
                     f"setpts=PTS-STARTPTS+{at}/TB[ov{i}]")
        graph.append(f"{v}[ov{i}]overlay=eof_action=pass:enable='between(t,{at},{at + odur})'[vo{i}]")
        v = f"[vo{i}]"
    if captions:
        # Filter options are colon-separated, so the drive colon in C:/... must be escaped.
        srt = captions.resolve().as_posix().replace(":", r"\:").replace("'", r"\'")
        graph.append(f"{v}subtitles=f='{srt}':force_style='{style.caption_force_style(house['captions'])}'[vsub]")
        v = "[vsub]"
    graph.append(f"{v}format=yuv420p[vout]")

    cache.mkdir(parents=True, exist_ok=True)
    dur = float(probe(video, "format=duration"))
    print(f"Rendering picture ({dur:.1f}s, preset {preset})...", file=sys.stderr)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-stats", *inputs,
                    "-filter_complex", ";".join(graph), "-map", "[vout]", "-an", "-t", f"{dur:.3f}",
                    "-c:v", "libx264", "-preset", preset, "-crf", str(house["export"]["crf"]), str(out)],
                   check=True)
    keyfile.write_text(json.dumps(key))
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video", type=Path)
    ap.add_argument("--music", type=Path, help="background music (loops with a crossfade if short)")
    # Unset options fall back to style.json ("audio" / "export" / "captions").
    ap.add_argument("--music-db", type=float, help="fixed music level (ignored when music_below_lu is set)")
    ap.add_argument("--duck", action=argparse.BooleanOptionalAction, help="lower music under the main sound")
    ap.add_argument("--overlay", type=timed, action="append", default=[], metavar="FILE@SEC")
    ap.add_argument("--sfx", type=timed, action="append", default=[], metavar="FILE@SEC")
    ap.add_argument("--sfx-db", type=float)
    ap.add_argument("--captions", type=Path, help=".srt to burn into the picture")
    ap.add_argument("--lufs", type=float, help="target loudness of the main sound")
    ap.add_argument("--out", type=Path, help="default: <video>-final.mp4")
    ap.add_argument("--preset", help="x264 preset for the picture (ultrafast for quick drafts)")
    args = ap.parse_args()

    video = args.video.resolve()
    house = style.load(video)
    out = (args.out or video.with_name(video.stem + "-final.mp4")).resolve()
    cache = out.parent / ".cache"
    dur = float(probe(video, "format=duration"))

    pic = picture(video, args.overlay, args.captions, house, args.preset or house["export"]["preset"], cache)

    print("Mastering sound...", file=sys.stderr)
    snd = cache / f"{out.stem}.sound.m4a"
    cache.mkdir(parents=True, exist_ok=True)
    info = audio.master(video, snd, args.music and args.music.resolve(), args.sfx, args.lufs,
                        args.music_db, args.duck, args.sfx_db)

    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(pic), "-i", str(snd),
                    "-map", "0:v:0", "-map", "1:a:0", "-c", "copy", "-t", f"{dur:.3f}",
                    "-movflags", "+faststart", str(out)], check=True)
    out.with_suffix(".sound.json").write_text(json.dumps(info, indent=1))
    print(f"Done -> {out}")
    problems = audio.check(out, info, dur)
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
