# CutCrew: instructions for other coding agents (Antigravity, Codex, Gemini CLI, …)

CutCrew was built for Claude Code, and **`CLAUDE.md` is the source of truth**. Read all of it
before doing anything. It has the pipeline, the rules and the project layout. This file only
explains what to change when you are *not* Claude Code.

## Map Claude Code terms to yours

| `CLAUDE.md` / commands say | Do this instead |
|---|---|
| `/edit`, `/explainer`, `/setup` | Open `.claude/commands/<name>.md` and follow it step by step. (Antigravity: the `.agents/workflows/` files do this for you.) |
| `$ARGUMENTS` | The words the user wrote after the command. |
| "AskUserQuestion" | Ask the questions in chat, all in one message, house default first, and **wait** for the answer. |
| `/hyperframes`, `/motion-graphics`, `/hyperframes-core`, … (skills) | Read the skill's `SKILL.md` before writing any animation: `%USERPROFILE%\.claude\skills\<name>\SKILL.md` (installed by `setup.ps1`). Follow its references too. If it's missing, run `npx skills add heygen-com/hyperframes`. |
| "Claude in Chrome" / built-in browser | Your own browser tool. |
| memory files | Not available. The project's memory is `STYLE.md`, `style.json`, `FEEDBACK.md` and each project's `notes.md`. |

## Rules that matter most (repeated from CLAUDE.md so they are never skipped)

- **Explainers / story clips** use `styles/explainer/STYLE.md` + `style.json` and the kit in
  `kit/explainer/`, never the root `STYLE.md`. Copy the structure of the worked example
  `projects/squared-explainer/` (if present) instead of inventing your own. Render nothing until
  the user says "go". Script and stills come first.
- Read `STYLE.md`, `style.json` and the last ~10 rows of `FEEDBACK.md` before every edit.
- Never modify or delete original recordings (each project's recordings folder, see CLAUDE.md "Rules").
- Python is `.venv\Scripts\python.exe`, run from the repo root. Every script has `--help`.
- Never run `hyperframes publish` / `npm run publish` unless the user asks.
- Downloading music/SFX needs the user's OK each time. Log every file in `library/CREDITS.md`.
- Verify before saying it's done (CLAUDE.md "Workflow" step 8).
