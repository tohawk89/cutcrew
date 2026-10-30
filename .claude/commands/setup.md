---
description: First-time setup: check the tools, then learn the user's channel and style before the first edit
---

The user just installed CutCrew (or wants to redo onboarding). Get them from "cloned" to "ready to
edit" in one sitting. Be brief; this is a checklist, not a lecture.

## 1. Check the machine

Run these and report one line each (ok / missing):
- `.venv\Scripts\python.exe -c "import onnx_asr, playwright"` (transcriber + fact grabber)
- `ffmpeg -version`, `node --version` (needs 22+)
- `STYLE.md`, `style.json`, `FEEDBACK.md`, `library\CREDITS.md` exist at the root
- `animations\assets\fonts\SegUIVar.ttf` and `bahnschrift.ttf` exist
- HyperFrames skills are available to you (`/hyperframes` is in your skill list)

If anything is missing, ask before running `powershell -ExecutionPolicy Bypass -File setup.ps1`
(it installs with winget and downloads the ~2.4 GB Parakeet model, so it takes a while). Run it in
the background and carry on with step 2 meanwhile. If HyperFrames skills were just installed, tell
the user to start a new Claude Code session after setup so they load.

## 2. Learn the channel (one AskUserQuestion round, then a free-text follow-up if needed)

Ask in one go:
- **Format:** talking head / screen tutorial / unboxing-ASMR (no talking) / vlog / other
- **Language** of the voice (Parakeet: English + 24 European languages; otherwise offer faster-whisper)
- **Platform:** YouTube long-form (-14 LUFS) / Shorts-Reels vertical / quiet ASMR (-21 LUFS)
- **Captions:** none / key-moment thoughts / full transcript burned in

Then ask in plain text for: channel name, brand colour (hex or "pick for me"), and anything they
never want ("never ask to subscribe", "no music", …).

## 3. Save it

- Rewrite `STYLE.md` from the answers (keep its section headings; set "Last updated" to today).
- Set the matching numbers in `style.json` (`audio.lufs`, `captions.burn_in`, `cut.keep_fillers`).
- Put the channel name into the `channel` variable default of
  `animations/compositions/end-card.html`, and the brand colour into the card templates if they
  gave one (ask before restyling all cards).
- Add the first row to `FEEDBACK.md`: today, "(setup)", their answers in short, "starter style", house.

## 4. Optional extras (mention, don't push)

- **OBS Studio** for recording: `setup.ps1 -WithObs`. Point its Recording Path at
  `projects\<name>\raw` (Settings → Output), Hybrid MP4, 48 kHz audio.
- **Claude in Chrome** or the built-in browser, for fact sources and free music search.
- Free music: YouTube Audio Library, Pixabay, Freesound (CC0/CC-BY). Claude asks before every download.

## 5. Hand off

End with one line: "Ready. Drop a recording in `projects/<name>/raw/` and type `/edit <name>`."
