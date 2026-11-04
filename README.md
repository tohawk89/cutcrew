# CutCrew

**Talk to your video editor. It's Claude Code.**

Record, drop the files in, and say what you want in plain words. Claude cuts it, adds the cards and
music, checks every frame and the sound, and hands you the final. Everything except Claude runs free
on your own PC.

> *"Cut the pauses and retakes, add a title card, soft piano under it, export for YouTube."*

## Install (Windows 10/11)

Open PowerShell where you want the folder and paste:

```powershell
irm https://raw.githubusercontent.com/tohawk89/cutcrew/main/install.ps1 | iex
```

It installs whatever is missing (FFmpeg, Node.js, Python, the speech model) and is safe to run
again. You also need Claude Code: the [desktop app](https://claude.ai/download) (Code tab) or the CLI.
Installing by hand, OBS settings and the free sound library are covered in [SETUP.md](SETUP.md).

## Make your first video

1. Open the `cutcrew` folder in Claude Code.
2. Type **`/setup`** and answer a few questions about your channel. Claude writes your `STYLE.md`.
3. Put your recording in `projects/my-first-video/raw/`, or just tell Claude where it is.
4. Type **`/edit my-first-video`**, answer the intake questions, then direct it:

   > Show me what you'd cut before rendering.
   >
   > Music is too loud, and the cuts feel rushed.
   >
   > Looks good, render the final.

You always see a draft first. Nothing is final until you say so.

## It learns your taste

Every comment you make ("music too loud", "love that title card") fixes this video **and** is saved
for the next one. When it's unclear whether you mean "always" or "just this video", Claude asks.

| File | Holds |
|---|---|
| `STYLE.md` | your taste in words: pacing, look, music, "never do" list |
| `style.json` | the numbers the scripts use: cut gaps, music level, loudness |
| `FEEDBACK.md` | everything you said and what changed |

## Token use per stage

What one edit costs in Claude tokens, from start to the approved final, draft rounds included:

| Stage | What Claude does | Tokens | New tokens | Share |
|---|---|---:|---:|---:|
| Intake & planning | reads your style, asks the setup questions, plans the edit | 1.5 M | 123 k | 5 % |
| Sync | lines up the separate audio with the camera (clap) | 595 k | 8 k | 2 % |
| Transcribe | runs Parakeet and reads the transcript | 233 k | 4 k | 1 % |
| Sound profile | measures loudness and room tone | 798 k | 7 k | 2 % |
| Rough cut | writes the EDL: retakes, pauses, pacing | 757 k | 8 k | 2 % |
| Draft render | renders the 1080p draft | 2.9 M | 52 k | 9 % |
| Animations | builds and renders title, caption and end cards | 2.9 M | 54 k | 9 % |
| Research & fact cards | looks up facts and music in the browser, grabs sources | 3.3 M | 36 k | 10 % |
| Music & sound | picks and logs music, masters the sound | 1.1 M | 30 k | 3 % |
| Finish | joins cards, music and sound into the final | 5.0 M | 32 k | 15 % |
| Verify | looks at frames and reads sound checks before delivering | 12.0 M | 334 k | 36 % |
| Feedback & style | saves your comments to STYLE.md / FEEDBACK.md | 2.1 M | 157 k | 6 % |
| **Whole video** | | **33.2 M** | **846 k** | |

- Average of 6 real edits (silent ASMR unboxings, 3–13 min finals, October 2026). The simplest took
  16 M, and a concert video with many cards took 71 M. A talking video will differ.
- **Tokens** counts everything Claude read. About 97 % of it is cache: Claude re-reading the
  conversation so far, which costs much less of your plan. **New tokens** is the fresh part.
- Verify is the biggest because Claude looks at frames from the video before telling you it's done.
- See your own numbers: `.venv\Scripts\python.exe scripts\tokens.py --project <name>`

## Good to know

- **Windows only** for now. The Python scripts themselves are portable.
- **Languages:** the speech model covers English and 24 European languages. For Malay, Chinese,
  Arabic and others, ask Claude to add faster-whisper.
- **Your recordings are never touched.** Everything Claude makes goes to `renders/` and `assets/`.
- Claude **asks before** every music download and never publishes anything unless you ask.

<details>
<summary><b>Under the hood</b>: the crew, the pipeline, the files</summary>

### The crew

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

### The pipeline

```
recording ─► transcribe.py ─► cut.py suggest ─► edl.json ─(Claude: retakes, pacing)─► cut.py render
                                                                                          │
HyperFrames cards (title, captions, fact cards, end card) ─┐                              ▼
music + SFX from library/ ─────────────────────────────────┴────────────► finish.py ─► final.mp4
                                                         (ducking, captions, loudness, sound check)
```

### What's in the repo

```
CLAUDE.md                 the editor's instructions (workflow, rules)
.claude/commands/         /setup and /edit
.claude/skills/studio-crew  optional pane: a pixel-art crew acting out each step; also guards raw/
scripts/                  transcribe, sync, cut, audio, finish, grab, tokens (each has --help)
animations/compositions/  reusable HyperFrames cards: title, end, inner-talk, fact, fact-talk, ticket-talk
defaults/                 starter STYLE.md, style.json, FEEDBACK.md, CREDITS.md
setup.ps1, install.ps1    installer
SETUP.md                  detailed guide: manual install, OBS settings, building a free sound library
```

Never in the repo (see `.gitignore`): your projects and recordings, your style and feedback files
(fresh copies come from `defaults/` on first setup), downloaded music/SFX (their licences don't allow
re-sharing), the Windows fonts, and fact-card screenshots. Video-only tweaks live in
`projects/<name>/style.json` and `notes.md`.

### Commands

You rarely type these: Claude runs them. Full list in `CLAUDE.md`.

```powershell
.venv\Scripts\python.exe scripts\transcribe.py projects\<name>\raw\<file>.mp4
.venv\Scripts\python.exe scripts\cut.py suggest projects\<name>\transcripts\<file>.json
.venv\Scripts\python.exe scripts\cut.py render projects\<name>\edl.json --draft
.venv\Scripts\python.exe scripts\finish.py projects\<name>\renders\edl-cut.mp4 --music ...
.venv\Scripts\python.exe scripts\audio.py check <file>
.venv\Scripts\python.exe scripts\tokens.py --per-video
```

</details>

## Credits

Built on [Claude Code](https://claude.com/claude-code),
[HyperFrames](https://github.com/heygen-com/hyperframes) (Apache-2.0),
[NVIDIA Parakeet TDT 0.6B v3](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3) (CC-BY-4.0) via
[onnx-asr](https://github.com/istupakov/onnx-asr), [FFmpeg](https://ffmpeg.org) and
[Playwright](https://playwright.dev).

## License

[MIT](LICENSE). Third-party tools, models, fonts and music keep their own licences.
