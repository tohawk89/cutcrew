# My video style

Claude reads this before every edit and updates it whenever I give feedback that should apply
to future videos. Numbers the scripts use live in `style.json`; this file holds the *why* and
everything that can't be a number (taste, look, tone).

This is the starter style. Run `/setup` in Claude Code and it will interview you and rewrite it,
or just start editing: every comment you make on a draft gets saved here.

_Last updated: (not yet — starter style)_

## Channel & format
- Channel: **(your channel name)**.
- Format: (e.g. talking head, screen tutorial, unboxing, vlog). Who's on camera, how it's filmed.
- Language: (Parakeet covers English + 24 European languages; for others ask for faster-whisper).

## Pacing & cutting
- If I talk: cut pauses longer than 0.6 s, keep 0.12 s around speech, remove um/uh, keep the
  last clean take of a repeated line. (`style.json` → cut)
- Focus on the point, not the process: jump-cut past setup, waiting and mistakes.

## Captions
- No burned-in transcript captions by default (`style.json` → captions.burn_in = false).
- On-screen text: short (about 10 words, 1–2 lines), never covering the main action.
- Fact cards: when a caption states a checkable fact, ask whether to show the source.

## Animations & graphics
- Clean, flat, friendly. Brand colour purple/indigo, approx `#5A46D6`, with white.
- **Title card**: the video's title at the start. **End card**: thanks the viewer for watching.
- Templates live in `animations/compositions/` and are reused on every video.

## Music & sound
- Quiet music when it fits: soft, low under the voice, never covering it. Pick by fit per video;
  reuse a library track when it suits.
- Final loudness **-14 LUFS** (YouTube), true peak under -2 dBTP. (`style.json` → audio)

## Intro & outro
- Intro: get to the point in the first seconds, title card on top.
- Outro: an end card that thanks the viewer; a proper fade, never a sudden stop.

## Never do
- (things you never want, e.g. "never ask viewers to like and subscribe")
