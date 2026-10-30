# CutCrew

**Talk to your video editor. It's Claude Code.**

CutCrew turns [Claude Code](https://claude.com/claude-code) into a video editor that learns your
taste. You record, drop the files in, and say what you want in plain words: *"cut the pauses and
retakes, add a title card, soft piano under it, export for YouTube."* Claude runs a free, local
pipeline: transcription, rough cut, animated graphics, music, loudness, and checks every frame
before saying it's done.

Every comment you make on a draft ("music too loud", "cuts feel rushed", "love that title card")
is saved to your house style, so each video comes out closer to how you like it.

## The crew

| Role | Tool | Cost |
|---|---|---|
| Editor | Claude Code | your Claude plan |
| Transcriber | NVIDIA Parakeet TDT 0.6B v3, runs locally on the CPU | free |
| Animator | [HyperFrames](https://github.com/heygen-com/hyperframes) (HTML → video) | free |
| Researcher | Claude's built-in browser or Claude in Chrome | free |
| Fact grabber | Playwright + your Edge/Chrome (source screenshots for fact cards) | free |
| Recorder | OBS Studio (optional) | free |
| Sound | YouTube Audio Library, Pixabay, Freesound | free |
| Finisher | FFmpeg | free |

```
recording ─► transcribe.py ─► cut.py suggest ─► edl.json ─(Claude: retakes, pacing)─► cut.py render
                                                                                          │
HyperFrames cards (title, captions, fact cards, end card) ─┐                              ▼
music + SFX from library/ ─────────────────────────────────┴────────────► finish.py ─► final.mp4
                                                         (ducking, captions, loudness, sound check)
```

## Install (Windows 10/11)

Open PowerShell where you want the folder and paste:

```powershell
irm https://raw.githubusercontent.com/tohawk89/cutcrew/main/install.ps1 | iex
```

That clones CutCrew and runs `setup.ps1`, which installs anything missing with winget (Git,
FFmpeg, Node.js 22+, Python), builds the Python environment, downloads the Parakeet model
(~2.4 GB, once), copies the card fonts from Windows, and installs the HyperFrames skills for
Claude Code. It's safe to run again any time. Add `-WithObs` to also install OBS Studio.

Prefer to do it by hand:

```powershell
git clone https://github.com/tohawk89/cutcrew.git
cd cutcrew
powershell -ExecutionPolicy Bypass -File setup.ps1
```

You also need Claude Code: the [desktop app](https://claude.ai/download) (Code tab) or the CLI.

## First run

1. Open the `cutcrew` folder in Claude Code.
2. Type **`/setup`**. Claude checks the tools, then asks about your channel (format, language,
   platform, captions, brand colour, things you never want) and writes your starting `STYLE.md`.
3. Put a recording in `projects/my-first-video/raw/` (or tell Claude where it is; on the same
   drive it hard-links it in, no copy).
4. Type **`/edit my-first-video`** and answer the intake questions once. Then just direct it:

   > Cut the pauses and retakes, show me what you'd cut before rendering.
   > Add a title card that says "5 tips for…". Soft piano under it, low.
   > Looks good, render the final.

Claude shows you a draft first, applies your comments, and asks for feedback after delivery.

## It learns your taste

| File | Holds |
|---|---|
| `STYLE.md` | your taste in words: pacing, look, tone, music mood, "never do" list |
| `style.json` | the numbers the scripts read: cut gaps, caption look, music level, loudness, export quality |
| `FEEDBACK.md` | a log of everything you said and what changed |
| `projects/<name>/style.json`, `notes.md` | overrides and notes for one video only |

When it's unclear whether a comment means "always" or "just this video", Claude asks. These files
are yours: they're git-ignored, and fresh copies come from `defaults/` on first setup.

## What's in the repo

```
CLAUDE.md                 the editor's instructions (workflow, rules)
.claude/commands/         /setup and /edit
.claude/skills/studio-crew  optional pane: a pixel-art crew acting out each step; also guards raw/
scripts/                  transcribe, sync, cut, audio, finish, grab (each has --help)
animations/compositions/  reusable HyperFrames cards: title, end, inner-talk, fact, fact-talk, ticket-talk
defaults/                 starter STYLE.md, style.json, FEEDBACK.md, CREDITS.md
setup.ps1, install.ps1    installer
SETUP.md                  detailed guide: OBS settings, building a free sound library
```

Never in the repo (see `.gitignore`): your projects and recordings, your style and feedback files,
downloaded music/SFX (their licences don't allow re-sharing the files), the Windows fonts, and
fact-card screenshots.

## Commands

```powershell
.venv\Scripts\python.exe scripts\transcribe.py projects\<name>\raw\<file>.mp4
.venv\Scripts\python.exe scripts\cut.py suggest projects\<name>\transcripts\<file>.json
.venv\Scripts\python.exe scripts\cut.py render projects\<name>\edl.json --draft
.venv\Scripts\python.exe scripts\finish.py projects\<name>\renders\edl-cut.mp4 --music ...
.venv\Scripts\python.exe scripts\audio.py check <file>
```

You rarely type these: Claude runs them. Full list in `CLAUDE.md`.

## Notes and limits

- **Windows only** for now (PowerShell setup, winget). The Python scripts themselves are portable.
- **Languages:** Parakeet v3 covers English and 24 European languages. For others (Malay, Chinese,
  Arabic, …) ask Claude to add faster-whisper.
- **Your raw recordings are never touched.** Claude only adds files to `raw/`; everything it makes
  goes to `renders/` and `assets/`.
- Claude asks before every music download and logs each track's licence in `library/CREDITS.md`.
- HyperFrames can publish to a public link; Claude never does that unless you ask.

## Credits

Built on [Claude Code](https://claude.com/claude-code),
[HyperFrames](https://github.com/heygen-com/hyperframes) (Apache-2.0),
[NVIDIA Parakeet TDT 0.6B v3](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3) (CC-BY-4.0) via
[onnx-asr](https://github.com/istupakov/onnx-asr), [FFmpeg](https://ffmpeg.org) and
[Playwright](https://playwright.dev).

## License

[MIT](LICENSE). Third-party tools, models, fonts and music keep their own licences.
