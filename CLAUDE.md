# CutCrew — Claude Code is the editor

This folder is a video editing system driven by Claude Code. The user records, drops the
files in, and asks for an edit in plain language. You run the pipeline below.

| Role | Tool | Where |
|---|---|---|
| Editor | Claude Code (you) | this folder |
| Transcriber | NVIDIA Parakeet TDT 0.6B v3 (local, CPU) | `scripts/transcribe.py` |
| Animator | HyperFrames (HTML → video) | `animations/` + `/hyperframes` skills |
| Researcher | Chrome (Claude in Chrome / built-in browser) | references, fact sources, free music search |
| Fact grabber | Playwright + your Edge | `scripts/grab.py` → `animations/compositions/fact-card.html` |
| Screen recorder | OBS Studio | records into `projects/<name>/raw/` |
| Sound designer | YouTube Audio Library, Pixabay, Freesound | `library/music`, `library/sfx` |
| Finisher | FFmpeg | `scripts/cut.py`, `scripts/finish.py` |

## Commands (Windows, run from this folder)

```powershell
.venv\Scripts\python.exe scripts\sync.py projects\<name>\raw\<video>.mp4 projects\<name>\raw\<audio>.wav   # -> renders\synced.mkv
.venv\Scripts\python.exe scripts\transcribe.py projects\<name>\raw\<file>.mp4
.venv\Scripts\python.exe scripts\cut.py suggest projects\<name>\transcripts\<file>.json
.venv\Scripts\python.exe scripts\audio.py analyze projects\<name>\renders\synced.mkv   # sound profile + loudness options
.venv\Scripts\python.exe scripts\cut.py render projects\<name>\edl.json --draft   # fast 1080p draft (proxy made once)
.venv\Scripts\python.exe scripts\cut.py render projects\<name>\edl.json           # final quality (full resolution)
.venv\Scripts\python.exe scripts\finish.py projects\<name>\renders\edl-cut.mp4 --music ... --overlay FILE@SEC --sfx FILE@SEC --captions ...srt
.venv\Scripts\python.exe scripts\audio.py master projects\<name>\renders\edl-cut.mp4 --music ...   # try sound changes alone, in seconds
.venv\Scripts\python.exe scripts\audio.py check <file>                                          # sound report
.venv\Scripts\python.exe scripts\grab.py URL --find "exact sentence" --out projects\<name>\assets\facts\fact-1.png   # source screenshot for a fact card
```

**`/setup`** is first-time onboarding: checks the tools and interviews the user into `STYLE.md`.
If `STYLE.md` or `style.json` is missing at the root, suggest `/setup` before editing.

**`/edit <project> [wishes]`** starts an edit: asks the setup questions once (captions, fact
screenshots, music, graphics, platform), saves them to the project's `notes.md`, then runs the workflow below.

Every script has `--help`. If `.venv` is missing or broken (e.g. the folder was moved), run `setup.ps1`.

## Project layout

```
STYLE.md, style.json, FEEDBACK.md   the user's taste (see "Learning from feedback")
projects/<name>/
  style.json, notes.md   optional: overrides and notes for this video only
  raw/            original recordings — NEVER modify or delete these
  transcripts/    <file>.json (word timings), .txt (read this), .srt
  assets/         rendered animations, B-roll, project-specific audio
  edl.json        the edit: which source ranges to keep, in order
  renders/        edl-cut.mp4 (+ .srt/.json re-timed to the cut), *-final.mp4
library/music, library/sfx   shared free audio; every file logged in library/CREDITS.md
animations/                   HyperFrames project (one composition per graphic)
```

## Learning from feedback — do this on every video

The user wants every edit to get closer to their taste. Their preferences live in three files:

| File | Holds | Who reads it |
|---|---|---|
| `STYLE.md` | taste in words: pacing, look, tone, music mood, "never do" list | you, before every edit |
| `style.json` | the numbers: cut gap/pad, caption look, music/SFX levels, loudness, export quality | the scripts, automatically |
| `FEEDBACK.md` | log of every piece of feedback and what changed | you, to spot patterns |

A project can override house style for one video with `projects/<name>/style.json` (any subset of
the same keys) and keep one-off notes in `projects/<name>/notes.md`.

**Before editing:** read `STYLE.md`, `style.json`, the last ~10 rows of `FEEDBACK.md`, and the
project's `notes.md`/`style.json` if present. Follow them, including for HyperFrames graphics
(pass the "Animations & graphics" section as the design brief).

**Whenever the user reacts to a draft or the final video** (any comment counts: "music too loud",
"cuts feel rushed", "love the title card", "captions in yellow"):
1. Apply it to the current video.
2. Decide scope. A clear taste statement ("I hate…", "always…", "too loud" with no video-specific
   reason) → **house**. Tied to this video's content → **video**. Unsure → ask one short question:
   "Always, or just this video?"
3. Save it:
   - house → change `style.json` if it's a number/setting, and update the matching `STYLE.md`
     section in words (bump "Last updated"). Praise counts too: record what worked so you repeat it.
   - video → `projects/<name>/style.json` or `notes.md`.
4. Add a row at the top of the `FEEDBACK.md` table (date, project, their words, what changed, scope).
5. Tell the user in one line what you saved, e.g. "Saved to house style: pauses now cut at 0.4 s."

**After delivering a video**, ask once for feedback (e.g. "Anything you'd change — pacing, captions,
music, graphics?"), so preferences keep accumulating.

**When the user confirms the final video** ("it's good, no changes"), ask once whether to delete the
project's leftover files. List them with sizes first: `renders/synced.mkv`, `synced-proxy.mkv`,
`edl-cut-draft.mp4`, `edl-cut.mp4`, `renders/.cache/`, A/B clips in `assets/`. Delete only on a yes.
Always keep the final video(s), `raw/`, cards in `assets/`, `edl.json`, transcripts and notes; all
the leftovers can be rebuilt from `raw/` in a few minutes if a change is needed later.

If the same kind of feedback shows up twice in `FEEDBACK.md`, the house style isn't strict enough —
tighten it and say so. Never silently undo a saved preference; if a new request contradicts one,
point it out and ask which wins.

## Workflow

0. **Read the style** — `STYLE.md`, `style.json`, recent `FEEDBACK.md` (see above).
1. **Set up** — create `projects/<kebab-name>/{raw,transcripts,assets,renders}` if new. Ask the user
   to put recordings in `raw/` (OBS can record straight there). If they're in another folder on the same drive
   (e.g. the camera import folder STYLE.md names), hard-link them in yourself, named `camera.mp4` / `audio.m4a`:
   `New-Item -ItemType HardLink -Path projects\<name>\raw\camera.mp4 -Target "<original>"` (never
   `-Force`). A hard link takes no extra space, and the user can then delete the original safely.
1b. **Sync separate audio** — if the voice was recorded on another device (clap at the start),
   run `sync.py` first and use `renders/synced.mkv` as the source for everything below.
   Check its printed confidence; cut the clap out in the EDL.
1c. **Profile the sound** — `audio.py analyze` (about 10 s). It shows loudness, dynamics, room tone
   and what each loudness target costs. Decide the sound strategy from it *before* any render;
   if the house target looks wrong for this recording, say so and ask.
2. **Transcribe** each raw file. Read the `.txt`, not the `.json`, to understand content.
3. **Rough cut** — run `cut.py suggest` (cuts pauses and um/uh per `style.json`), then edit `edl.json` by hand:
   - Retakes: when a sentence is said more than once, keep the **last** clean take, drop the others.
   - Remove false starts, "let me do that again", tangents the user asked to cut.
   - Keep `note` fields accurate; they're how the user reviews the edit.
   - Any range can take `"speed": X` (0.5–4, sound pitch kept) or `"hold": SEC` (freeze its last
     frame), e.g. for the footage under a caption + source overlay or a long hero shot.
   - Before rendering, give the user a short summary: what was cut, old → new runtime.
4. **Render a draft** with `--draft` (1080p from a proxy, fast). Renders also write
   `renders/<edl>-cut.json/.srt`: word timings on the **new** timeline — use these for every later
   timing decision. Draft and final share the same timeline, so overlay times carry over.
5. **Animations** — work inside `animations/`. Always invoke the `/hyperframes` skill first; it routes
   to the right workflow (titles, lower-thirds, callouts → `/motion-graphics`; talking-head overlays
   → `/talking-head-recut`; captions → `/embedded-captions`). Match the video's resolution
   (`ffprobe` it). Render each graphic to `projects/<name>/assets/<graphic>.mp4` (full-frame cutaway)
   or a transparent `.webm` (on top of footage), timed from the cut transcript.
5b. **Fact screenshots** — when a caption or spoken line states a checkable fact and the user wants
   sources shown (intake answer in `notes.md`): ask per fact, research it in the browser, confirm the URL
   and the exact sentence with the user, capture with `grab.py`, render `fact-talk.html` (caption
   first, then the source joins it, both leave together) with the variables it prints. Under it,
   prefer moving footage that would have been cut, sped up to fit (`"speed"` in the EDL); else
   stretch or freeze (`"hold"`). Steps in `.claude/commands/edit.md` § 3. If the sources contradict
   the caption, tell the user first.
6. **Sound** — music and SFX come only from free sources the user approved:
   YouTube Audio Library, Pixabay Music/Sound Effects, Freesound (CC0 or CC-BY only).
   Log each file in `library/CREDITS.md` (title, author, URL, licence, attribution text).
   If a licence needs attribution, remind the user to put it in the video description.
   Downloading files needs the user's OK each time.
7. **Finish** with `finish.py`. Levels, ducking, loudness and caption look come from `style.json`;
   pass `--captions` only if `captions.burn_in` is true. The picture (overlays/captions) is
   rendered once and cached; the sound is made separately and joined without re-encoding, so a
   sound-only change re-runs in seconds. **Fix sound problems with `audio.py master` on the cut
   (or a 30–60 s excerpt), never by re-exporting video.** Isolate a suspected cause with an A/B
   on a short excerpt before changing anything.
8. **Verify before saying it's done**:
   - Extract frames at each overlay time and look at them:
     `ffmpeg -ss <sec> -i <final.mp4> -frames:v 1 -vf scale=960:-1 check.png`
   - Read the sound check `finish.py` prints (or `audio.py check <final>`): main sound on target,
     true peak ≤ -2 dBTP, room tone ≤ -45 dBFS, music at the house distance under the main sound,
     sound/picture lengths equal. Any `!!` line must be fixed before delivering.
   - Optionally re-transcribe the final cut to confirm no retakes/fillers slipped through.

## Rules

- Never change or delete anything in `raw/`; the only thing allowed is adding recordings (create the
  folder, hard-link a new file in). All output goes to `renders/` or `assets/`.
- Never run `hyperframes publish` / `npm run publish` (uploads to the web) unless the user asks.
- One source file per EDL. To combine several cuts, render each, then join with FFmpeg's concat
  demuxer (same codec/resolution/fps) or re-encode with the concat filter.
- Screen recordings that need zoom-ins: use FFmpeg `crop`+`scale` on a range, or a HyperFrames
  composition that embeds the clip — don't re-record.
- Parakeet v3 covers English and 24 other European languages. For other languages (e.g. Malay,
  Arabic, Chinese), tell the user and offer to add faster-whisper as an alternative transcriber.
