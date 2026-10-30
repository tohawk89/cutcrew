"""Mix a pre-levelled live clip's sound into a finished video at a time, optionally fade the whole
mix out at the end, then a true-peak safety limiter (AAC overshoot headroom) and re-mux with the
picture copied.

Usage:
  python scripts/insert_live.py <finished.mp4> <live.wav> <at_sec> <out.mp4> [--fade-out SEC]

  --fade-out SEC  fade everything (recording + music + live) to silence over the last SEC seconds,
                  e.g. 4 = the end card's full purple screen (house).
Level the live clip first (loudnorm, ~3 LU above the main sound) and leave a freeze in the cut under it.
"""
import argparse
import subprocess

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("video")
ap.add_argument("live")
ap.add_argument("at", type=float)
ap.add_argument("out")
ap.add_argument("--fade-out", type=float, default=0)
args = ap.parse_args()

dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                            args.video], capture_output=True, text=True, check=True).stdout)
fade = f"afade=t=out:st={dur - args.fade_out:.3f}:d={args.fade_out:.3f}," if args.fade_out > 0 else ""
graph = (f"[1:a]aresample=48000,adelay={int(round(args.at * 1000))}:all=1[live];"
         f"[0:a][live]amix=inputs=2:duration=first:normalize=0,{fade}"
         "aresample=192000,alimiter=limit=0.6:attack=1:release=50:level=false,aresample=48000[a]")
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", args.video, "-i", args.live, "-filter_complex", graph,
                "-map", "0:v:0", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "320k",
                "-t", f"{dur:.3f}", "-movflags", "+faststart", args.out], check=True)
print("Done ->", args.out)
