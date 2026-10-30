"""Transcribe a video/audio file with NVIDIA Parakeet (runs locally, free).

Writes three files next to each other in --out:
  <name>.json  word-level timings (what the editor scripts read)
  <name>.txt   readable transcript with timestamps (what Claude reads)
  <name>.srt   caption file

Usage:
  python scripts/transcribe.py projects/demo/raw/take1.mp4
  python scripts/transcribe.py take1.mp4 --out projects/demo/transcripts
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import style  # noqa: E402

MODEL = "nemo-parakeet-tdt-0.6b-v3"  # 25 European languages, auto-detected
FILLERS = {"um", "uh", "erm", "er", "ah", "uhm", "hmm", "mm", "mhm"}


def extract_audio(src: Path, wav: Path) -> None:
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(src),
         "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(wav)],
        check=True,
    )


def probe_duration(src: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(src)],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    return float(out)


def bare(word: str) -> str:
    return "".join(c for c in word.lower() if c.isalnum() or c == "'")


def tokens_to_words(seg) -> list[dict]:
    """Merge Parakeet sub-word tokens into words with absolute start/end times."""
    words: list[dict] = []
    for tok, ts in zip(seg.tokens, seg.timestamps):
        t = seg.start + ts
        if not words or tok.startswith(" "):
            if tok.strip() and not bare(tok) and words:
                words[-1]["text"] += tok.strip()  # stray punctuation
                words[-1]["_last"] = t
                continue
            words.append({"text": tok.strip(), "start": t, "_last": t})
        else:
            words[-1]["text"] += tok
            words[-1]["_last"] = t
    for i, w in enumerate(words):
        nxt = words[i + 1]["start"] if i + 1 < len(words) else seg.end
        w["end"] = round(min(nxt, w.pop("_last") + 0.3, seg.end), 3)
        w["start"] = round(w["start"], 3)
        w["filler"] = bare(w["text"]) in FILLERS
    return [w for w in words if w["text"]]


def fmt_ts(t: float, srt: bool = False) -> str:
    h, rem = divmod(max(t, 0), 3600)
    m, s = divmod(rem, 60)
    if srt:
        return f"{int(h):02}:{int(m):02}:{int(s):02},{int(round((s % 1) * 1000)) % 1000:03}"
    return f"{int(h * 60 + m):02}:{s:04.1f}"


def caption_lines(words: list[dict], max_words=7, max_chars=42, uppercase=False, max_gap=0.5) -> list[dict]:
    lines, cur = [], []
    for w in words:
        if w["filler"]:
            continue
        if cur and (
            len(cur) >= max_words
            or len(" ".join(x["text"] for x in cur + [w])) > max_chars
            or w["start"] - cur[-1]["end"] > max_gap
            or cur[-1]["text"][-1:] in ".?!"
        ):
            lines.append(cur)
            cur = []
        cur.append(w)
    if cur:
        lines.append(cur)
    lines = [{"start": l[0]["start"], "end": l[-1]["end"],
              "text": " ".join(x["text"] for x in l)} for l in lines]
    if uppercase:
        for l in lines:
            l["text"] = l["text"].upper()
    return lines


def write_srt(path: Path, words: list[dict]) -> None:
    c = style.load(path)["captions"]
    lines = caption_lines(words, c["max_words"], c["max_chars"], c["uppercase"])
    with open(path, "w", encoding="utf-8") as f:
        for i, c in enumerate(lines, 1):
            f.write(f"{i}\n{fmt_ts(c['start'], True)} --> {fmt_ts(c['end'], True)}\n{c['text']}\n\n")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", type=Path)
    ap.add_argument("--out", type=Path, help="output folder (default: ../transcripts next to raw/, else beside input)")
    args = ap.parse_args()

    src = args.input.resolve()
    out_dir = args.out or (src.parent.parent / "transcripts" if src.parent.name == "raw" else src.parent)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = out_dir / src.stem

    os.environ.setdefault("ORT_LOGGING_LEVEL", "3")
    import onnx_asr  # imported late so --help is instant

    print(f"Loading Parakeet ({MODEL})...", file=sys.stderr)
    model = onnx_asr.load_model(MODEL).with_vad(onnx_asr.load_vad("silero")).with_timestamps()

    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / "audio.wav"
        extract_audio(src, wav)
        print("Transcribing...", file=sys.stderr)
        segments = []
        for seg in model.recognize(str(wav)):
            segments.append({"start": round(seg.start, 3), "end": round(seg.end, 3),
                             "text": seg.text.strip(), "words": tokens_to_words(seg)})

    words = [w for s in segments for w in s["words"]]
    data = {"source": os.path.relpath(src, out_dir), "duration": probe_duration(src),
            "model": MODEL, "segments": segments}
    stem.with_suffix(".json").write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
    stem.with_suffix(".txt").write_text(
        "\n".join(f"[{fmt_ts(s['start'])} - {fmt_ts(s['end'])}] {s['text']}" for s in segments) + "\n",
        encoding="utf-8")
    write_srt(stem.with_suffix(".srt"), words)

    fillers = sum(w["filler"] for w in words)
    print(f"Done: {len(segments)} segments, {len(words)} words ({fillers} fillers) -> {stem}.json/.txt/.srt")


if __name__ == "__main__":
    main()
