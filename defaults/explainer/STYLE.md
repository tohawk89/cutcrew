# Explainer style (animated montage / product explainer)

_Starter version. It learns your taste as you give feedback (see FEEDBACK.md, scope `explainer`)._

This is the house style for **animated explainers and montages**: flat-vector cartoon scenes, a narrator,
music, an optional real app clip inside a cartoon phone, a call to action and credits.
It is **not** the unboxing style (green mat, title card, purple end card): that lives in the root
`STYLE.md`. Nothing here changes unboxing edits, and nothing in the root STYLE.md applies here unless
repeated below.

Kit: `kit/explainer/` (start a project with `/explainer <name>`).
Numbers: `styles/explainer/style.json`.

## Story
- 45–75 s. Hook (a relatable situation) → the problem/risk → the brand → how it works, **each step with
  what the viewer gets from it** (not generic "benefits") → a real product clip → one call to action → credits.
- Benefits are written from how the product works ("Photo proof for every defect"), never vague marketing.
- One short voice line per beat; each card/pop lands on its word.
- Any factual claim (laws, numbers) is checked against a source and shown to the user before it is voiced.
  Prefer a line with no numbers when the numbers are not from an official source.

## Look
- Flat vector, **no outlines**, 2 tones per object (base + one hard-edged shadow), no gradients.
- Colours come from the **client's logo** (sample them), plus: a warm wall family (terracotta/sand/cream)
  so a cool character pops, and **orange only for "problems"** (crack circle, "?").
- White text never sits on the light brand colour: use a darker shade behind white text (contrast ≥ 4:1).
- Type: rounded bold sans (Segoe UI Variable locally; Poppins/Nunito if installed). Reading text ≥ 28 px.

## Character (starter design; change it with the user)
- Taller-than-wide head with a jaw and forward chin; neat side-part hair that wraps behind the ear;
  big ear drawn over the hair; dot eyes set wide; big open D-mouth with a teeth band; no nose, no blush.
- Broad rounded (raglan) shoulders; arms grow out of the shoulder curve, tapered, with an elbow joint;
  the far arm is one shade darker. Hands have a thumb; fingers wrap held props.
- Shirt in the client's main brand colour, trousers in their dark colour.
- Poses: keys (happy), point, confused (hand on head + "?"), phone. Faces: happy, worried, afraid, down.
- **Holding a phone up close:** big round fist behind the phone's bottom-right corner, only the thumb in
  front resting on the edge, straight sleeve out to the bottom right.

## Motion
- Simple: pop-ins (back.out), slide-ins, rise-ins, a crack that draws itself, blinks, a gentle bob,
  a face swap on the beat (e.g. smile → afraid on "…or not").
- **Never a slow camera push/zoom on a scene that has text.** Even 3–5 % makes text shimmer/wobble at 30 fps
  . Keep scenes still and move the elements. A **fast** zoom-through between
  scenes (≤ 0.6 s, e.g. into a crack, then a white flash) is fine.
- Anything that rotates spins around its own centre (`svgOrigin`), never the frame corner.
- Text stays on screen at least 0.5 s + 0.3 s per word; credits ≥ 5 s.

## Real product clips
- Ask for **plain** 9:16 clips: no zoom, no cards, no cursor, ~1 s still before and ~1.5 s after each action,
  one file per shot.
- Mute them; the narrator carries the scene. Speed each clip to fit its line (1.5–3×).
- A step list beside the phone highlights the current step in time with the voice.

## Sound
- Voice: Kokoro `af_heart`, speed 0.95, generated **one sentence per file** so timing can be placed.
  Main sound −21 LUFS, true peak ≤ −2 dBTP.
- Music: simple, professional, light corporate; **not Content ID registered**; 15 LU under the voice.
  Prefer a track whose length matches the film (it ends on its own); pad with silence, never loop.
- The sound check's "room tone" warning is the music bed in the pauses (TTS has no noise floor); it needs no fix.

## Credits (approved layout)
Logo + URL on top, a thin line, then two columns (small grey caps labels, white values, teal links):
CREATED BY <your name> · MADE WITH CutCrew (github.com/tohawk89/cutcrew) · VOICE Kokoro TTS · ANIMATION FlatStory (when its clips are used) · MUSIC "title" by artist · source.
On screen ≥ 5 s; rows appear one by one.

## Process (the user's gates)
Script/storyboard in `notes.md` → style frame stills → all scene stills → voice samples → music picks
→ "go" → draft → notes → final. **Render nothing until the user says go.**
