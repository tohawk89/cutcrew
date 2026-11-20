---
description: Start a video edit: ask the setup questions once, then run the whole pipeline
---

1. Read `AGENTS.md` and `CLAUDE.md` in the repo root if you haven't this session.
2. Open `.claude/commands/edit.md` and follow it exactly, step by step. It is the real recipe.
   This file only points to it, so Claude Code and Antigravity share one source of truth.
3. Where it says `$ARGUMENTS`, use the words the user typed after `/edit`. Where it says
   AskUserQuestion, ask in chat in one message and wait. Where it names a HyperFrames skill
   (`/hyperframes` etc.), read that skill's SKILL.md first (see AGENTS.md).
