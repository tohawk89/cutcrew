# CutCrew — detailed setup guide

The 7-role stack, with every paid tool swapped for a free one (except Claude Code):

| # | Role | Original | This setup | Cost |
|---|---|---|---|---|
| 01 | Editor | Claude Code | Claude Code | your plan |
| 02 | Transcriber | Parakeet | **Parakeet TDT 0.6B v3**, running locally | free |
| 03 | Animator | HyperFrames | **HyperFrames** (open source, Apache-2.0) | free |
| 04 | Researcher | Google Chrome | **Chrome** + Claude in Chrome / Claude's built-in browser | free |
| 05 | Screen editor | Tella *(paid)* | **OBS Studio** to record; cuts/zooms done by Claude + FFmpeg | free |
| 06 | Sound designer | Epidemic Sound *(paid)* | **YouTube Audio Library**, **Pixabay**, **Freesound** | free |
| 07 | Finisher | FFmpeg | **FFmpeg** | free |

---

## Step 1 — Install everything (one command)

The one-line installer in the README clones CutCrew and runs `setup.ps1` for you. To do it by hand
instead, open PowerShell where you want the folder and run:

```powershell
git clone https://github.com/tohawk89/cutcrew.git
cd cutcrew
powershell -ExecutionPolicy Bypass -File setup.ps1
```

Add `-WithObs` to also install OBS Studio.

It installs anything missing (FFmpeg, Node.js 22+, Python), creates `.venv`, downloads the
Parakeet model (~2.4 GB, once), and checks HyperFrames. Run it again any time something breaks
or after moving the folder.

It also installs the HyperFrames skills for Claude Code into your user skills folder
(`~/.claude/skills/hyperframes*`), so every Claude Code session can use `/hyperframes`.

## Step 2 — Set up OBS for recording (replaces Tella's recorder)

In OBS → **Settings**:

1. **Output → Recording**
   - Recording Path: `<cutcrew folder>\projects\<project-name>\raw`
   - Recording Format: **Hybrid MP4** (crash-safe; or MKV, then File → Remux Recordings)
   - Video Encoder: **NVIDIA NVENC H.264** (or AMD AMF / Intel QSV; x264 if you have no GPU encoder)
   - Rate control: CQP, CQ level **18**
2. **Video** — Base and Output resolution **1920×1080**, FPS **30** (or 60 for fast screen action).
3. **Audio** — Sample rate **48 kHz**.
4. Scenes: add **Display Capture** (screen) and optionally **Video Capture Device** (webcam) as a
   small corner box, plus your mic under **Audio Input Capture**. Add the mic filters
   **Noise Suppression (RNNoise)** → **Compressor** → **Limiter (-1 dB)** for clean voice.

Tip: when you fluff a line, pause, then **say the whole sentence again**. Claude keeps the last take.

## Step 3 — Build your free sound library (replaces Epidemic Sound)

| Source | Use for | Licence notes |
|---|---|---|
| [YouTube Audio Library](https://studio.youtube.com) → Audio library | music | free; some tracks need attribution (shown per track) |
| [Pixabay Music](https://pixabay.com/music/) / [Sound Effects](https://pixabay.com/sound-effects/) | music + SFX | Pixabay Content License, no attribution needed |
| [Freesound](https://freesound.org) | SFX (whooshes, clicks, pops) | filter to **CC0** to skip attribution; CC-BY needs credit |

Save files into `library/music` and `library/sfx`, and add a row to `library/CREDITS.md`.
(Or ask Claude to search for you in Chrome — it'll ask before downloading anything.)

## Step 4 — Your first edit

1. Record a video with OBS into `projects/my-first-video/raw/`.
2. Open this folder in Claude Code (Desktop app → pick folder, or `claude` in a terminal here).
3. Say something like:

   > New video project: my-first-video. Transcribe the recording, cut the pauses, ums and
   > retakes, then show me what you'd cut before rendering.

4. Then keep directing it:

   > Add an animated title card for the first 3 seconds that says "5 tips for…".
   > Add a lower-third with my name at 0:05. Pop a stat callout when I say "40 percent".
   > Add calm lo-fi music from the library, a whoosh on each callout, and burned-in captions.
   > Export the final video.

What happens under the hood:

```
OBS recording ──► transcribe.py (Parakeet) ──► transcript .txt/.json/.srt
                         │
                         ▼
               cut.py suggest ──► edl.json ──(Claude edits: retakes, order)──► cut.py render
                                                                                   │
HyperFrames animations (assets/*.mp4/.webm) ─────┐                                 ▼
library music + SFX ─────────────────────────────┴──────────────► finish.py ──► renders/*-final.mp4
                                          (ducking, captions, loudness from style.json)
```

## Step 5 — Give feedback; it's remembered

Just react to drafts in plain words: "cuts feel rushed", "music too loud", "captions yellow and
all caps", "I love that title animation". Claude fixes the current video **and** saves it:

- `STYLE.md` — your taste in words (pacing, captions, graphics, music, never-do list).
- `style.json` — the settings the scripts use, so changes apply automatically next time.
- `FEEDBACK.md` — a log of everything you said and what changed.

If it's unclear whether you mean "always" or "just this video", Claude asks. Video-only tweaks go in
`projects/<name>/style.json` or `notes.md`. You can also edit `STYLE.md` yourself any time.

## Notes & limits

- **Languages:** Parakeet v3 handles English + 24 European languages. For Malay, Chinese, Arabic etc.,
  ask Claude to add faster-whisper as the transcriber.
- **Speed:** Parakeet runs on the CPU (~1 s per 10 s of audio on a 6-core desktop CPU). GPU use would need
  ~1 GB of extra CUDA 13 libraries, which isn't worth it at that speed.
- **Tella-style auto-zoom/cursor polish** isn't automatic in OBS. Ask Claude to zoom into a region
  for a time range (FFmpeg crop) or build a HyperFrames zoom composition. If you want a GUI for this,
  [Cap](https://cap.so) is an open-source alternative worth trying.
- HyperFrames can **publish** projects to a public link; Claude is told never to do that unless you ask.
