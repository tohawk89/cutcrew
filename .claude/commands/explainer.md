---
description: Make an animated explainer / montage (flat cartoon scenes, narrator, music, real app clip, CTA, credits)
argument-hint: <project-name> [product URL or what it's about]
---

The user wants an **animated explainer** (not an unboxing edit). Arguments: `$ARGUMENTS`
(first word = project name under `projects/`; the rest = the product / brief in their words).

Style: `styles/explainer/STYLE.md` + `style.json` (NOT the root unboxing STYLE.md; if missing, copy them from `defaults/explainer/`). Kit: `kit/explainer/`.
Worked example to copy from: `projects/squared-explainer/` (notes.md, vo.json, build_hf.py, phone-shots.md).
Commands below are run from the repo root with `.venv\Scripts\python.exe`.

**Golden rule: render nothing until the user says go.** Everything before "go" is discussion, text and stills.

## 1. Intake (ask once)
1. Read `styles/explainer/STYLE.md`, `style.json`, the last ~10 rows of `FEEDBACK.md` (scope `explainer`/`video`),
   and the project's `notes.md` if it exists. New project: `kit/explainer/new.py <name>`.
2. Research the product (open its site in the browser; read the page). Ask in one go (AskUserQuestion),
   house default first: format (16:9 / 9:16), length, language, voice (Kokoro af_heart), music (light
   corporate, 15 LU under voice), CTA wording, real product clips (have them / record plain ones), logo file.
3. Save the answers in `notes.md` → Intake. Note brand colours sampled from the logo.

## 2. Script & storyboard (text only)
- Story shape from STYLE.md (hook → problem → brand → how it works with a benefit per step → real clip → CTA → credits).
- Write the table in `notes.md` and the lines in `vo.json` (one sentence per line, `scene` keys).
- Any factual claim: find a source, show the URL + exact wording, prefer a line without unverified numbers.
- Get approval. Log each approval in notes.md → Approvals.

## 3. Look (stills only)
- Edit `projects/<name>/film.py` (from the template): brand colours, `Character(...)`, scenes with `kit.explainer.parts`.
- `film.py --stills` → `assets/stills/` (one frame per scene). Show them; iterate on feedback
  (character, hands, hair, layout). Record taste notes as in CLAUDE.md "Learning from feedback"
  (scope `explainer` → `styles/explainer/`).
- Real clips: if needed, give the user the plain-shot list (template: `projects/squared-explainer/phone-shots.md`);
  hard-link arrivals into `raw/`, check specs/frames, then use `parts.phone_rig()`.

## 4. Voice & music
- `kit/explainer/voice.py <proj> --samples "<one line>"` → let the user pick a voice.
- Music: search Pixabay / YouTube Audio Library; skip Content ID registered tracks; offer 2–3 with links;
  download only the chosen one (ask first), log it in `library/CREDITS.md`, set `"music"` in vo.json.

## 5. Build (after "go")
1. `kit/explainer/voice.py <proj>` (all lines; `--only id` after a wording change).
2. `kit/explainer/timing.py <proj>` → timing.json + renders/voice.wav. Set `pad_to`/credits so the film ≥ music.
3. `python projects/<name>/film.py` → `animations/explainers/<name>/`; then in that folder `npx hyperframes@0.9.26 check`
   (fix every error; contrast warnings on text that is mid-animation are OK).
4. `kit/explainer/render.py <proj>` → `renders/<name>-draft.mp4`. Test a span with `--span 31.5-33`.

## 6. Verify before showing anything
- Frames at every scene change and each beat (ffmpeg -ss … -frames:v 1).
- **Text must be still**: compare frames 2 apart on a text crop (`psnr` = inf or ≥ 60 dB). No slow camera pushes.
- Sound check: voice −21 LUFS, peak ≤ −2 dBTP, music 15 LU under, lengths equal. The "room tone" line is
  the music bed under a TTS voice (expected); any other `!!` must be fixed.

## 7. Notes → final → cleanup
- Apply each note, re-render the draft, log it in FEEDBACK.md (scope explainer/video).
- On "render final": `render.py <proj> --final` → `renders/<name>-final.mp4`, verify again, deliver, ask for feedback.
- On "it's good, no changes": list leftovers with sizes (drafts, animation.mp4, *-cut.mp4, .cache, voice-samples)
  and delete only on a yes. Keep the final, raw/, voice lines, vo.json, timing.json, film.py, notes, stills.
