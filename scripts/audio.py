"""Sound for the edit: profile a recording, master the final mix, check the result.

  analyze  how loud / dynamic / noisy a recording is, and what each loudness target would cost
           (gain needed, how hard the loudest hits get limited, how loud the room hiss gets).
           Run it once on a new recording, before deciding anything about its sound.
  master   clean-up + music + SFX + loudness -> a finished audio file (AAC), plus a check report.
           finish.py calls this; run it alone to try sound changes in seconds.
  check    measure any finished file and flag problems.

Usage:
  python scripts/audio.py analyze projects/demo/renders/synced.mkv
  python scripts/audio.py master projects/demo/renders/edl-cut.mp4 --music library/music/x.mp3
  python scripts/audio.py check projects/demo/renders/demo-final.mp4

Levels come from style.json "audio": lufs (target for the main recording), pre (clean-up
filters), music_below_lu (music level under the recording), duck, sfx_db, max_gain_db.
"""

import argparse
import json
import math
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import style  # noqa: E402

SR = 48000
# -3 dBFS ceiling, limited at 4x oversampling so peaks between samples are caught too;
# with AAC 320k this keeps true peak under about -2.5 dBTP through YouTube's re-encode.
LIMITER = "aresample=192000,alimiter=limit=0.708:attack=1:release=50:level=false,aresample=48000"
CEILING_DB = -3.0
TP_MAX = -2.0          # warn above this true peak (dBTP)
ROOM_TONE_MAX = -45.0  # warn when the quietest moments are louder than this (dBFS RMS)


# --- measuring -------------------------------------------------------------------------------

def probe(path: Path, entries: str, stream: str | None = None) -> str:
    cmd = ["ffprobe", "-v", "error"]
    if stream:
        cmd += ["-select_streams", stream]
    cmd += ["-show_entries", entries, "-of", "default=nw=1:nk=1", str(path)]
    return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout.strip()


def has_audio(path: Path) -> bool:
    return bool(probe(path, "stream=codec_type", "a:0"))


def ebur(inputs: list[str], graph: str) -> dict:
    """Run `graph` (ending in an unlabelled audio pad) through ebur128; return I, LRA, TP."""
    log = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", *inputs, "-filter_complex",
         f"{graph},ebur128=peak=true:framelog=quiet[m]", "-map", "[m]", "-f", "null", "-"],
        check=True, capture_output=True, text=True).stderr
    summary = log[log.rindex("Summary:"):]

    def grab(key: str) -> float:
        val = summary.split(key)[1].split()[0]
        return -math.inf if val in ("-inf", "nan") else float(val)
    return {"I": grab("I:"), "LRA": grab("LRA:"), "TP": grab("Peak:")}


def loudness(path: Path, chain: str = "anull") -> float:
    return ebur(["-i", str(path)], f"[0:a]{chain}")["I"]


def pcm(path: Path, chain: str = "anull") -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vn", "-af", chain,
                          "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         check=True, capture_output=True).stdout
    return np.frombuffer(raw, np.float32)


def window_rms_db(x: np.ndarray, win: float = 0.4) -> np.ndarray:
    n = int(win * SR)
    w = x[: len(x) // n * n].reshape(-1, n)
    return 20 * np.log10(np.sqrt((w ** 2).mean(1)) + 1e-12)


def room_tone_db(x: np.ndarray) -> float:
    """Level of the quietest moments: 10th percentile of 0.4 s RMS, ignoring digital silence."""
    r = window_rms_db(x)
    r = r[r > -120]
    return float(np.percentile(r, 10)) if len(r) else -math.inf


def render_wav(src: Path, chain: str, out: Path) -> Path:
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-vn", "-af",
                    f"aresample={SR},{chain}", "-c:a", "pcm_f32le", str(out)], check=True)
    return out


def find_gain(wav: Path, target: float, max_gain: float) -> tuple[float, float]:
    """Gain that brings `wav` to `target` LUFS through the limiter (secant steps, capped)."""
    l0 = loudness(wav)
    g0, g1 = 0.0, min(target - l0, max_gain)
    l1 = loudness(wav, f"volume={g1:.2f}dB,{LIMITER}")
    for _ in range(4):
        if abs(target - l1) < 0.3 or (g1 >= max_gain and l1 < target):
            break
        slope = (l1 - l0) / (g1 - g0) if g1 != g0 else 1.0
        g0, l0 = g1, l1
        g1 = min(g1 + (target - l1) / max(slope, 0.2), max_gain)
        l1 = loudness(wav, f"volume={g1:.2f}dB,{LIMITER}")
    return g1, l1


# --- analyze ---------------------------------------------------------------------------------

def analyze(path: Path, targets=(-14, -18, -21, -24)) -> dict:
    house = style.load(path)["audio"]
    pre = house.get("pre") or "anull"
    max_gain = float(house.get("max_gain_db", 30))
    raw = ebur(["-i", str(path)], "[0:a]anull")
    with tempfile.TemporaryDirectory() as tmp:
        wav = render_wav(path, pre, Path(tmp) / "clean.wav")
        clean = ebur(["-i", str(wav)], "[0:a]anull")
        x = pcm(wav)
        room = room_tone_db(x)
        peak = float(20 * np.log10(np.abs(x).max() + 1e-12))
        # Peaks per 10 ms: the top 0.5% are the "loud hits" (snaps, thuds) the limiter will meet.
        k = SR // 100
        wp = 20 * np.log10(np.abs(x[: len(x) // k * k]).reshape(-1, k).max(1) + 1e-12)
        hits = float(np.percentile(wp, 99.5))
        with ThreadPoolExecutor(len(targets)) as pool:
            gains = list(pool.map(lambda t: find_gain(wav, t, max_gain), targets))
    rows = []
    for t, (g, reached) in zip(targets, gains):
        rows.append({"target": t, "gain": round(g, 1), "reached": round(reached, 1),
                     "hits_limited_db": round(max(0.0, hits + g - CEILING_DB), 1),
                     "worst_hit_limited_db": round(max(0.0, peak + g - CEILING_DB), 1),
                     "time_limited_pct": round(float(np.mean(wp + g > CEILING_DB)) * 100, 2),
                     "room_tone_db": round(room + g, 1)})
    return {"file": str(path), "raw": raw, "clean": clean, "peak_db": round(peak, 1),
            "plr": round(clean["TP"] - clean["I"], 1), "room_tone_db": round(room, 1),
            "targets": rows, "house_lufs": house.get("lufs")}


def print_analysis(a: dict) -> None:
    c = a["clean"]
    print(f"{Path(a['file']).name}")
    print(f"  loudness {c['I']:.1f} LUFS, range {c['LRA']:.1f} LU, true peak {c['TP']:.1f} dBTP "
          f"(after clean-up; raw {a['raw']['I']:.1f} LUFS)")
    print(f"  loudest hits are {a['plr']:.0f} dB above the average "
          f"({'very dynamic: ASMR-like' if a['plr'] > 18 else 'normal'}); "
          f"room tone {a['room_tone_db']:.0f} dBFS")
    print("  target   gain     reached   loud hits limited   time limited   room tone after")
    for r in a["targets"]:
        warn = []
        if r["reached"] < r["target"] - 1:
            warn.append("not reachable: gain capped")
        if r["room_tone_db"] > ROOM_TONE_MAX:
            warn.append("hiss audible")
        if r["hits_limited_db"] > 10:
            warn.append("hits squashed")
        mark = "  <- house" if r["target"] == a["house_lufs"] else ""
        print(f"  {r['target']:>4}   {r['gain']:+5.1f} dB  {r['reached']:6.1f}    "
              f"{r['hits_limited_db']:5.1f} dB (worst {r['worst_hit_limited_db']:.0f})"
              f"   {r['time_limited_pct']:5.2f} %     {r['room_tone_db']:6.1f} dBFS"
              f"{mark}{'  (' + ', '.join(warn) + ')' if warn else ''}")


# --- master ----------------------------------------------------------------------------------

def master(video: Path, out: Path, music: Path | None = None, sfx=(), lufs=None,
           music_db=None, duck=None, sfx_db=None, quiet=False) -> dict:
    """Finished audio for `video` (its own sound + music + SFX), loudness-matched, as AAC."""
    house = style.load(video)["audio"]
    lufs = house["lufs"] if lufs is None else lufs
    duck = house.get("duck", True) if duck is None else duck
    sfx_db = house.get("sfx_db", -6) if sfx_db is None else sfx_db
    pre = house.get("pre") or "anull"
    max_gain = float(house.get("max_gain_db", 30))
    dur = float(probe(video, "format=duration"))
    log = (lambda *a: None) if quiet else (lambda m: print(m, file=sys.stderr))
    info = {"target_lufs": lufs}

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        inputs, graph, mix, n = [], [], [], 0
        main_wav = None
        if has_audio(video):
            # Clean-up runs on the recording only, before anything is mixed in: a denoiser on
            # the mix would treat steady music as noise and eat quiet details.
            main_wav = render_wav(video, pre, tmp / "main.wav")
            # Gain from the main recording alone: music filling the quiet gaps would pull the
            # gated loudness down and push the item sounds (and the limiter) much harder.
            gain, reached = find_gain(main_wav, lufs, max_gain)
            info.update(gain_db=round(gain, 1), main_lufs=round(reached, 1),
                        room_tone_db=round(room_tone_db(pcm(main_wav)) + gain, 1))
            inputs += ["-i", str(main_wav)]
            n += 1
            use_duck = bool(music) and duck
            graph.append("[0:a]asplit=2[main][sc]" if use_duck else "[0:a]anull[main]")
            mix.append("[main]")
        if music:
            level = music_db if music_db is not None else house.get("music_db", -18)
            below = house.get("music_below_lu")
            music_i = loudness(music)
            if below is not None and main_wav is not None:
                # Quiet sources (ASMR) make a fixed dB level meaningless: place the music a set
                # number of LU under the main sound as it ends up (after gain and limiter).
                level = (reached - below) - gain - music_i
            info["music_level_db"] = round(level, 1)
            # Loop by crossfading copies of the track, so the restart is never heard.
            mdur, xf = float(probe(music, "format=duration")), 4.0
            copies = max(1, math.ceil((dur - xf) / max(mdur - xf, 1)))
            chain = f"[{n}:a]aresample={SR}[m0]"
            for c in range(1, copies):
                chain += f";[{n + c}:a]aresample={SR}[mi{c}];[m{c - 1}][mi{c}]acrossfade=d={xf}[m{c}]"
            inputs += [x for _ in range(copies) for x in ("-i", str(music))]
            graph.append(chain)
            graph.append(f"[m{copies - 1}]atrim=0:{dur},volume={level:.2f}dB,"
                         f"afade=t=in:d=1.5,afade=t=out:st={max(dur - 3, 0)}:d=3[music]")
            if main_wav is not None and duck:
                graph.append("[music][sc]sidechaincompress=threshold=0.03:ratio=6:attack=30:release=600[musicd]")
                mix.append("[musicd]")
            else:
                mix.append("[music]")
            n += copies
        for i, (path, at) in enumerate(sfx):
            inputs += ["-i", str(path)]
            graph.append(f"[{n}:a]aresample={SR},volume={sfx_db}dB,adelay={int(at * 1000)}:all=1[sfx{i}]")
            mix.append(f"[sfx{i}]")
            n += 1
        if not mix:
            raise SystemExit("Nothing to master: the video has no sound and no music/SFX given.")

        if main_wav is None:  # music / SFX only: normalise the mix itself
            premix = tmp / "premix.wav"
            subprocess.run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex",
                            ";".join(graph + [f"{''.join(mix)}amix=inputs={len(mix)}:duration=longest:normalize=0[p]"]),
                            "-map", "[p]", "-t", f"{dur:.3f}", "-c:a", "pcm_f32le", str(premix)], check=True)
            gain, reached = find_gain(premix, lufs, max_gain)
            info.update(gain_db=round(gain, 1), main_lufs=round(reached, 1))
        log(f"  gain {gain:+.1f} dB -> main sound {reached:.1f} LUFS (target {lufs})"
            + (f", music {info['music_level_db']:+.1f} dB" if music else ""))
        if reached < lufs - 1:
            log(f"  NOTE: target needs more than +{max_gain:.0f} dB; capped to protect quiet parts")

        graph.append(f"{''.join(mix)}amix=inputs={len(mix)}:duration=first:normalize=0,"
                     f"volume={gain:.2f}dB,{LIMITER},apad[aout]")
        out.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", ";".join(graph),
                        "-map", "[aout]", "-t", f"{dur:.3f}", "-c:a", "aac", "-b:a", "320k", str(out)],
                       check=True)

        if music and main_wav is not None:
            # The music bed's own loudness in the mix (before ducking, which only lowers it).
            info["music_under_lu"] = round(reached - (music_i + info["music_level_db"] + gain), 1)
    return info


# --- check -----------------------------------------------------------------------------------

def check(path: Path, info: dict | None = None, video_duration: float | None = None) -> list[str]:
    """Measure a finished file; print a short report and return the list of problems."""
    house = style.load(path)["audio"]
    m = ebur(["-i", str(path)], "[0:a]anull")
    room = room_tone_db(pcm(path))
    problems, lines = [], []

    def row(ok: bool, text: str) -> None:
        lines.append(f"  {'ok' if ok else '!!'}  {text}")
        if not ok:
            problems.append(text)

    if info and "main_lufs" in info:
        row(abs(info["main_lufs"] - info["target_lufs"]) <= 0.5,
            f"main sound {info['main_lufs']:.1f} LUFS (target {info['target_lufs']})")
        lines.append(f"      whole mix {m['I']:.1f} LUFS"
                     + (" (lower than the main sound: music fills the quiet gaps, expected)"
                        if info.get("music_level_db") is not None and m["I"] < info["main_lufs"] - 0.5 else ""))
    else:
        # Without the master's notes the mix can't be split into recording and music.
        lines.append(f"  --  loudness {m['I']:.1f} LUFS (house {house['lufs']} for the main sound; "
                     "a music bed reads lower)")
    row(m["TP"] <= TP_MAX, f"true peak {m['TP']:.1f} dBTP (max {TP_MAX})")
    if info and "room_tone_db" in info:  # the recording alone: music would read as "hiss"
        row(info["room_tone_db"] <= ROOM_TONE_MAX,
            f"room tone {info['room_tone_db']:.0f} dBFS in the quietest moments (max {ROOM_TONE_MAX:.0f})")
    else:
        lines.append(f"  --  quietest moments {room:.0f} dBFS (includes any music)")
    if info and "music_under_lu" in info:
        want = house.get("music_below_lu", 0)
        row(info["music_under_lu"] >= want - 1.5,
            f"music {info['music_under_lu']:.1f} LU under the main sound (house {want})")
    if video_duration is not None:
        adur = float(probe(path, "stream=duration", "a:0") or probe(path, "format=duration"))
        row(abs(adur - video_duration) < 0.1, f"sound {adur:.2f}s vs picture {video_duration:.2f}s")
    print(f"Sound check: {path.name}")
    print("\n".join(lines))
    return problems


# --- CLI -------------------------------------------------------------------------------------

def timed(spec: str) -> tuple[Path, float]:
    path, _, at = spec.rpartition("@")
    if not path:
        raise argparse.ArgumentTypeError(f"expected FILE@SECONDS, got {spec!r}")
    return Path(path).resolve(), float(at)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("analyze", help="profile a recording and cost out loudness targets")
    a.add_argument("file", type=Path)
    a.add_argument("--json", action="store_true")
    m = sub.add_parser("master", help="make the finished sound for a cut")
    m.add_argument("video", type=Path)
    m.add_argument("--music", type=Path)
    m.add_argument("--sfx", type=timed, action="append", default=[], metavar="FILE@SEC")
    m.add_argument("--lufs", type=float)
    m.add_argument("--music-db", type=float, help="fixed music level (ignored when music_below_lu is set)")
    m.add_argument("--duck", action=argparse.BooleanOptionalAction)
    m.add_argument("--sfx-db", type=float)
    m.add_argument("--out", type=Path, help="default: <video>-audio.m4a")
    c = sub.add_parser("check", help="measure a finished file and flag problems")
    c.add_argument("file", type=Path)
    args = ap.parse_args()

    if args.cmd == "analyze":
        res = analyze(args.file.resolve())
        print(json.dumps(res, indent=1) if args.json else "", end="")
        if not args.json:
            print_analysis(res)
    elif args.cmd == "master":
        video = args.video.resolve()
        out = (args.out or video.with_name(video.stem + "-audio.m4a")).resolve()
        info = master(video, out, args.music and args.music.resolve(), args.sfx, args.lufs,
                      args.music_db, args.duck, args.sfx_db)
        out.with_suffix(".sound.json").write_text(json.dumps(info, indent=1))
        print(f"Done -> {out}")
        sys.exit(1 if check(out, info, float(probe(video, "format=duration"))) else 0)
    else:
        f = args.file.resolve()
        side = f.with_suffix(".sound.json")  # written by finish.py / master
        info = json.loads(side.read_text()) if side.exists() else None
        vdur = float(probe(f, "format=duration")) if info else None
        sys.exit(1 if check(f, info, vdur) else 0)


if __name__ == "__main__":
    main()
