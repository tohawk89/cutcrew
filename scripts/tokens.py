"""How many Claude tokens each pipeline stage used, read from your Claude Code session logs.

Claude Code keeps every session of this folder in ~/.claude/projects/<folder>/*.jsonl, with the
token usage of each reply. This script gives each reply to the stage of the tool call it made
(a reply with no matching call stays in the stage before it) and to the project it was working on
(only projects still in projects/):

  Sync, Transcribe, Sound profile, Rough cut, Draft render, Animations, Research & fact cards,
  Music & sound, Finish, Verify, Feedback & style, Intake & planning, and Building the pipeline
  (changes to scripts/, CLAUDE.md, .claude/: not part of a normal edit).

Usage:
  .venv\\Scripts\\python.exe scripts\\tokens.py                         # every session, by stage
  .venv\\Scripts\\python.exe scripts\\tokens.py --project <name>        # one video
  .venv\\Scripts\\python.exe scripts\\tokens.py --per-video --markdown  # average per video (README table)

"Total" counts every token Claude read or wrote. Most of it is cache reads (Claude re-reading the
conversation so far), which cost far less of a plan than "new" tokens (fresh input + cache writes + output).
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# (stage, what Claude does there), in pipeline order.
STAGES = [
    ("Intake & planning", "reads your style, asks the setup questions, plans the edit"),
    ("Sync", "lines up the separate audio with the camera (clap)"),
    ("Transcribe", "runs Parakeet and reads the transcript"),
    ("Sound profile", "measures loudness and room tone"),
    ("Rough cut", "writes the EDL: retakes, pauses, pacing"),
    ("Draft render", "renders the 1080p draft"),
    ("Animations", "builds and renders title, caption and end cards"),
    ("Research & fact cards", "looks up facts and music in the browser, grabs sources"),
    ("Music & sound", "picks and logs music, masters the sound"),
    ("Finish", "joins cards, music and sound into the final"),
    ("Verify", "looks at frames and reads sound checks before delivering"),
    ("Feedback & style", "saves your comments to STYLE.md / FEEDBACK.md"),
    ("Building the pipeline", "changes to the scripts and instructions themselves"),
]
PIPELINE = "Building the pipeline"

# First match wins. Commands from Bash/PowerShell.
COMMAND_RULES = [
    ("sync.py", "Sync"),
    ("transcribe.py", "Transcribe"),
    ("audio.py analyze", "Sound profile"),
    ("cut.py suggest", "Rough cut"),
    ("cut.py render", "Draft render"),
    ("grab.py", "Research & fact cards"),
    ("insert_live", "Finish"),
    ("finish.py", "Finish"),
    ("audio.py master", "Music & sound"),
    ("audio.py check", "Verify"),
    ("-frames:v", "Verify"),
    ("hyperframes", "Animations"),
    ("npx", "Animations"),
]

PROJECT_RE = re.compile(r"projects/([a-z0-9][a-z0-9._-]*)")


def stage_of(name, text):
    """Stage for one tool call, or None. text is the lower-cased input with / separators."""
    if name in ("Bash", "PowerShell"):
        return next((st for key, st in COMMAND_RULES if key in text), None)
    if "browser" in name.lower() or "chrome" in name.lower():
        return "Research & fact cards"
    if name == "Skill":
        return "Animations" if any(k in text for k in ("hyperframes", "motion", "media-use")) else None
    if name in ("Edit", "Write", "Read"):
        if "feedback.md" in text or "style.md" in text or ("style.json" in text and "projects/" not in text):
            return "Feedback & style"
        if "edl.json" in text or "/transcripts/" in text:
            return "Rough cut"
        if "animations/" in text:
            return "Animations"
        if "credits.md" in text or "library/" in text:
            return "Music & sound"
        if ".png" in text or ".jpg" in text:
            return "Verify"
        if "notes.md" in text:
            return "Intake & planning"
        if any(k in text for k in ("scripts/", "claude.md", ".claude/", "setup.ps1", "readme")):
            return PIPELINE
    return None


def log_dir():
    # Claude Code names the folder after the path with every non-alphanumeric character as "-".
    slug = re.sub(r"[^A-Za-z0-9]", "-", str(ROOT))
    return Path.home() / ".claude" / "projects" / slug


def read_session(path):
    """Replies in order as (usage, [(tool name, text)]). One reply spans several lines; usage once per id."""
    replies = {}
    for line in path.open(encoding="utf-8", errors="replace"):
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if rec.get("type") != "assistant":
            continue
        msg = rec.get("message") or {}
        mid = msg.get("id")
        if not mid:
            continue
        reply = replies.setdefault(mid, {"usage": {}, "tools": []})
        reply["usage"] = msg.get("usage") or reply["usage"]
        for block in msg.get("content") or []:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                text = json.dumps(block.get("input", {})).lower().replace("\\\\", "/")
                reply["tools"].append((block["name"], text))
    return list(replies.values())


def collect(files):
    """{project: {stage: [total, new, output]}}"""
    data = defaultdict(lambda: defaultdict(lambda: [0, 0, 0]))
    # Only real projects: skips test names and paths like ~/.claude/projects/<folder>/memory.
    known = {p.name for p in (ROOT / "projects").iterdir() if p.is_dir()} if (ROOT / "projects").is_dir() else set()
    for path in files:
        stage, project = "Intake & planning", "(no project)"
        for reply in read_session(path):
            for name, text in reply["tools"]:
                st = stage_of(name, text)
                if st:
                    stage = st
                    break
            mentions = [m for _, text in reply["tools"] for m in PROJECT_RE.findall(text) if m in known]
            if mentions:
                project = max(set(mentions), key=mentions.count)
            u = reply["usage"]
            new = u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0) + u.get("output_tokens", 0)
            row = data[project][stage]
            row[0] += new + u.get("cache_read_input_tokens", 0)
            row[1] += new
            row[2] += u.get("output_tokens", 0)
    return data


def fmt(n):
    return f"{n / 1e6:.1f} M" if n >= 1e6 else f"{n / 1e3:.0f} k"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", help="only this projects/<name>")
    ap.add_argument("--per-video", action="store_true",
                    help="average per edited project (pipeline building and project-less talk left out)")
    ap.add_argument("--markdown", action="store_true", help="print a Markdown table (for the README)")
    ap.add_argument("--logs", type=Path, help="session log folder (default: this folder's Claude Code logs)")
    args = ap.parse_args()

    folder = args.logs or log_dir()
    files = sorted(folder.rglob("*.jsonl"))
    if not files:
        sys.exit(f"No session logs in {folder}")
    data = collect(files)

    if args.project:
        if args.project not in data:
            sys.exit(f"No tokens found for project {args.project!r}. Known: {', '.join(sorted(data))}")
        projects, divide = [args.project], 1
    elif args.per_video:
        projects = [p for p in data if p != "(no project)"]
        divide = len(projects)
    else:
        projects, divide = list(data), 1

    totals = {st: [0, 0, 0] for st, _ in STAGES}
    for p in projects:
        for st, row in data[p].items():
            if args.per_video and st == PIPELINE:
                continue
            for i in range(3):
                totals[st][i] += row[i] / divide
    grand = sum(r[0] for r in totals.values()) or 1
    rows = [(st, desc, totals[st]) for st, desc in STAGES if totals[st][0]]

    scope = (f"project {args.project}" if args.project
             else f"average of {divide} videos" if args.per_video else f"all {len(files)} sessions")
    if args.markdown:
        print("| Stage | What Claude does | Tokens | New tokens | Share |")
        print("|---|---|---:|---:|---:|")
        for st, desc, (t, n, _) in rows:
            print(f"| {st} | {desc} | {fmt(t)} | {fmt(n)} | {100 * t / grand:.0f} % |")
        print(f"| **Whole video** | | **{fmt(grand)}** | **{fmt(sum(r[1] for _, _, r in rows))}** | |")
        return

    print(f"Tokens by stage ({scope}, from {folder})\n")
    print(f"{'Stage':24} {'Total':>9} {'New':>9} {'Output':>9} {'Share':>6}")
    for st, _, (t, n, o) in rows:
        print(f"{st:24} {fmt(t):>9} {fmt(n):>9} {fmt(o):>9} {100 * t / grand:5.0f}%")
    print(f"{'All':24} {fmt(grand):>9} {fmt(sum(r[1] for _, _, r in rows)):>9} "
          f"{fmt(sum(r[2] for _, _, r in rows)):>9}")
    if not args.project:
        print("\nProjects: " + ", ".join(f"{p} {fmt(sum(r[0] for r in data[p].values()))}" for p in sorted(data)))


if __name__ == "__main__":
    main()
