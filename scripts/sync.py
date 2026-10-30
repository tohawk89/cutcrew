"""Sync a separately recorded audio file to a video (clap sync), and mux them into one file.

The camera's own (scratch) audio is only used to find the alignment; the output keeps the
camera's picture untouched (stream copy) and replaces its sound with the external audio.

How it lines up: both soundtracks are reduced to an onset envelope (sharp sounds like a clap
stand out) and cross-correlated over the first --window seconds. It then measures again near
the end of the video; if the two devices' clocks drifted apart, the audio is stretched to match.

Usage:
  python scripts/sync.py projects/demo/raw/cam.mp4 projects/demo/raw/mic.wav
  # -> projects/demo/renders/synced.mkv  (use this as the source for transcribe/cut)

  --offset SEC  skip detection: audio time = video time + SEC
"""

import argparse
import subprocess
import sys
from pathlib import Path

import numpy as np

SR = 8000  # analysis sample rate; 0.125 ms resolution is plenty


def duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(path)],
        check=True, capture_output=True, text=True).stdout
    return float(out.strip())


def has_audio(path: Path) -> bool:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index",
         "-of", "csv=p=0", str(path)], capture_output=True, text=True).stdout
    return bool(out.strip())


def decode(path: Path, start: float, length: float) -> np.ndarray:
    """Mono float32 PCM at SR, from `start` for `length` seconds (shorter at file end)."""
    # No -ss at 0: an input seek to 0 skips AAC priming compensation (~21 ms early).
    seek = ["-ss", f"{start:.3f}"] if start > 0 else []
    pcm = subprocess.run(
        ["ffmpeg", "-v", "error", *seek, "-t", f"{length:.3f}",
         "-i", str(path), "-vn", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
        check=True, capture_output=True).stdout
    x = np.frombuffer(pcm, dtype=np.float32)
    if start < 0:  # window begins before the file: pad so indices still map to time
        x = np.concatenate([np.zeros(int(-start * SR), np.float32), x])
    return x


def envelope(x: np.ndarray) -> np.ndarray:
    """Onset envelope: rectified high-passed signal, smoothed, rising edges only."""
    hp = np.diff(x, prepend=0.0)
    env = np.abs(hp)
    k = int(0.005 * SR)
    env = np.convolve(env, np.ones(k) / k, mode="same")
    onset = np.maximum(np.diff(env, prepend=0.0), 0.0)
    return (onset - onset.mean()) / (onset.std() + 1e-9)


def best_lag(a: np.ndarray, b: np.ndarray) -> tuple[float, float]:
    """Seconds to shift `b` so it lines up with `a` (b_time = a_time + lag), and a confidence."""
    n = 1 << int(np.ceil(np.log2(len(a) + len(b))))
    corr = np.fft.irfft(np.fft.rfft(b, n) * np.conj(np.fft.rfft(a, n)), n)
    i = int(np.argmax(corr))
    lag = i if i < n // 2 else i - n
    peak = corr[i]
    # confidence: peak vs the next best peak at least 50 ms away
    guard = int(0.05 * SR)
    masked = corr.copy()
    lo, hi = i - guard, i + guard
    masked[max(lo, 0):max(hi, 0)] = -np.inf
    if lo < 0:
        masked[n + lo:] = -np.inf
    if hi > n:
        masked[:hi - n] = -np.inf
    second = masked.max()
    return lag / SR, float(peak / (abs(second) + 1e-9))


def loudest_clap(x: np.ndarray) -> float:
    return float(np.argmax(envelope(x))) / SR


def measure(video: Path, audio: Path, v_start: float, length: float,
            guess: float | None, search: float) -> tuple[float, float]:
    """Offset (audio_time - video_time) using the video window [v_start, v_start+length]."""
    a = decode(video, v_start, length)
    if guess is None:
        b_start, b_len = 0.0, length + search
        b = decode(audio, 0.0, b_len)
        a_t0 = v_start
    else:
        b_start = v_start + guess - search
        b = decode(audio, b_start, length + 2 * search)
        a_t0 = v_start
    lag, conf = best_lag(envelope(a), envelope(b))
    return b_start + lag - a_t0, conf


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("video")
    p.add_argument("audio")
    p.add_argument("--out", help="default: <project>/renders/synced.mkv")
    p.add_argument("--offset", type=float, help="manual offset: audio time = video time + SEC")
    p.add_argument("--window", type=float, default=60.0, help="seconds analysed at the start (default 60)")
    p.add_argument("--no-drift", action="store_true", help="don't correct clock drift")
    args = p.parse_args()

    video, audio = Path(args.video), Path(args.audio)
    if args.out:
        out = Path(args.out)
    else:
        base = video.resolve().parent
        out = (base.parent / "renders" if base.name == "raw" else base) / "synced.mkv"
    out.parent.mkdir(parents=True, exist_ok=True)

    vdur, adur = duration(video), duration(audio)
    print(f"video {vdur:.2f}s, audio {adur:.2f}s")

    if args.offset is not None:
        off, ratio = args.offset, 1.0
        print(f"manual offset {off:+.4f}s")
    else:
        if not has_audio(video):
            sys.exit("The video has no sound track to sync against. Pass --offset SEC instead.")
        # The audio recorder may have started well before the camera: search the whole head.
        search = min(adur, max(args.window, adur - vdur + 10) + 30)
        off, conf = measure(video, audio, 0.0, min(args.window, vdur), None, search)
        clap_v = loudest_clap(decode(video, 0.0, min(args.window, vdur)))
        print(f"start offset {off:+.4f}s (confidence {conf:.1f}; loudest transient in video at {clap_v:.2f}s)")
        if conf < 1.3:
            print("WARNING: weak match. Check the result, or pass --offset by hand.")
        ratio = 1.0
        if not args.no_drift and vdur > 120:
            # Measure in short windows along the video and fit audio_t = off0 + ratio * video_t.
            win = 15.0
            pts = []
            for t0 in np.arange(0.0, vdur - win, 30.0):
                o, c = measure(video, audio, float(t0), win, off, 1.0)
                if c >= 1.5:
                    pts.append((t0 + win / 2, o))
            if len(pts) >= 3:
                t, o = np.array(pts).T
                slope, icpt = np.polyfit(t, o, 1)
                resid = np.abs(o - (icpt + slope * t))
                keep = resid < max(0.01, 3 * np.median(resid))  # drop outlier windows
                if keep.sum() >= 3:
                    slope, icpt = np.polyfit(t[keep], o[keep], 1)
                drift = slope * vdur
                print(f"drift over the video {drift * 1000:+.1f} ms ({int(keep.sum())}/{len(pts)} windows)")
                if abs(drift) > 0.015:
                    ratio, off = 1.0 + slope, float(icpt)
                    print(f"correcting drift: audio tempo x{ratio:.6f}, offset at 0s {off:+.4f}s")

    # Build the audio chain: skip/pad so audio t=0 lines up with video t=0, fix tempo, fit length.
    chain = []
    if off >= 0:
        chain.append(f"atrim=start={off:.4f},asetpts=PTS-STARTPTS")
    else:
        ms = int(round(-off * 1000))
        chain.append(f"adelay={ms}:all=1")
    if ratio != 1.0:
        chain.append(f"atempo={ratio:.6f}")
    chain.append(f"apad,atrim=end={vdur:.4f}")

    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-stats", "-i", str(video), "-i", str(audio),
           "-filter_complex", f"[1:a]{','.join(chain)}[a]",
           "-map", "0:v:0", "-map", "[a]", "-c:v", "copy", "-c:a", "flac", "-ar", "48000",
           str(out)]
    subprocess.run(cmd, check=True)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
