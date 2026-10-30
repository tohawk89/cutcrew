---
description: Start a video edit: ask the setup questions once, then run the whole pipeline
argument-hint: <project-name> [what you want, e.g. "captions, music"]
---

The user wants to edit a video. Arguments: `$ARGUMENTS`
(first word = project name under `projects/`; the rest = what they asked for, in their words).

Follow the Workflow in `CLAUDE.md` from step 0 to the end. This command adds an **intake** at the
start so nothing is forgotten, and a **fact check** for captions.

## 1. Intake (before any render)

1. Read the house style (`STYLE.md`, `style.json`, last ~10 rows of `FEEDBACK.md`) and the
   project's `notes.md` / `style.json` if they exist. Set the project up if it's new and list
   what's in `raw/`. If it's empty, ask where the recordings are; when they're in a folder on the same drive
   (e.g. the camera import folder STYLE.md names), hard-link them into `raw/` yourself (CLAUDE.md step 1).
2. Ask the setup questions **in one go** with AskUserQuestion. Skip any question the arguments
   or the house style already answer, and put the house default first as "(house style)":
   - **Captions:** none / inner-talk thoughts at key moments / full transcript captions.
     If captions: when (whole video or which parts) and where (top / bottom / other).
   - **Fact screenshots:** when a caption states a fact (a number, date, spec, record,
     "the first…"), should I find the source online and show it in the video?
     (yes, ask me each time / yes, do it automatically / no)
   - **Music:** house style (soft piano/ambient, low) / none / something else. Before asking, look at
     the item and the `library/CREDITS.md` "Mood / used in" column: say which library track fits this
     video and why, or, if none fits well, suggest one new track as an option (STYLE.md → Music).
   - **Graphics:** title card + end card (house style) / anything extra.
   - **Platform & length:** YouTube long-form / Shorts-Reels (vertical) / no limit.
3. Save the answers to `projects/<name>/notes.md` under "Intake". An answer that clearly applies
   to every video ("always…") goes to the house style, as CLAUDE.md describes.

## 2. Run the pipeline

Sync → sound profile → transcribe → rough cut (summary + old → new runtime) → draft render →
**user reviews the draft** → captions → fact screenshots (below) → title/end cards → music →
finish → verify → deliver → ask for feedback → **once the user confirms the final video**, list the
leftover files with sizes and ask whether to delete them (CLAUDE.md, "When the user confirms the
final video").

## 3. Fact screenshots (when the user said yes)

For each caption, inner-talk thought, or spoken line that states a checkable fact:

1. **Ask first** (unless the intake said "automatically"): quote the line with its time in the cut
   and ask "Want a source screenshot for this?"
2. **Research** in the built-in browser: search, open the best sources, and check that the page
   really says the fact. Prefer the maker's official page or spec sheet, then reputable news, then
   Wikipedia. If the sources disagree with the caption, tell the user before going further
   (they may want to fix the caption, not show a wrong fact).
3. **Confirm**: show the user the URL and the exact sentence you'll highlight. Wait for OK.
4. **Capture**:
   `.venv\Scripts\python.exe scripts\grab.py <url> --find "<exact sentence>" --out projects\<name>\assets\facts\fact-<n>.png`
   Look at the saved PNG. If a banner or pop-up still covers the content, retry
   (`--wait 5`, or `--keep-floating` if hiding sticky bars hid the content itself).
5. **Animate caption + source together** with `animations/compositions/fact-talk.html` (one overlay
   per fact; it replaces the separate inner-talk + fact-card pair for that caption). The caption comes
   in alone and is read first, then the source window joins it (the bubble's trail dots point at it),
   pushes in, the marker sweeps the sentence, and both leave together. Variables: `text` (the approved
   caption), `layout`, the ones `grab.py` printed, `"hold": 4`. Render 4K transparent to
   `projects/<name>/assets/fact-talk-<n>.webm`; `ffprobe` its length (≈ 10 s for a 10-word caption).
   Pick `layout` from a frame of the footage it will sit on:
   - `below` (default): caption at the top, source under it. Hands and item low or centre.
   - `above`: source on top, caption at the bottom. The action is near the top edge.
   - `side`: caption left, source right. The item sits left/centre and should stay in view.
   `fact-card.html` (source alone) is only for a fact with no caption.
6. **Choose the footage under it**, in this order of preference, and say which one in the EDL `note`:
   1. **Moving footage that would have been cut** (the user's favourite): turning the box, waiting,
      re-tries, fiddling with packaging. Instead of cutting it, keep it as its own range under the
      overlay. If it's longer than the overlay, set `"speed"` = range length ÷ overlay length (up to
      `4`, a timelapse feel; trim first if it would need more). The scrim dims it into a background.
   2. **Stretch**: the right moment but a little short → `"speed"` 0.75–0.9 (below 0.75 it stutters).
   3. **Stop**: nothing suitable moves, or the action must not be missed → `"hold"` on the range that
      ends where the overlay starts; it freezes that last frame (pick one without motion blur). The
      item sound goes silent during the freeze, so check the draft with music.
   Never over the reveal or a satisfying sound, and never loop the same footage. Listen to sped-up
   ranges in the draft: the sound is time-stretched (pitch kept); if 3–4× sounds busy, use less speed.
   Then place it with `finish.py --overlay` at the caption's time and check frames at ~1.5 s
   (caption alone), at the join, during the highlight, and just after it leaves.
7. Log each source in `projects/<name>/notes.md` (fact, URL, date captured) so the user can add
   it to the video description.
