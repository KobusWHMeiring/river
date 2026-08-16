# Backlog Loop — Design Note

**Date:** 2026-08-14
**Scope:** River repo only. Other repos are unaffected (extension is project-local, skills are marker-gated).

## Problem

The backlog (`product/ready|refinement|Done|designs` + generated `product/backlog.md`) drifts from reality because the "close the loop" step is not reliably run at the end of a coding session. A read of the backlog therefore reports stale data. The user also does not always commit, so `git log` cannot be the sole evidence of "what happened this session."

## Solution

Three coordinated pieces + one checkpoint file.

### 1. `reading-the-backlog` skill (new)
Reports current state + what's "up next". **Never trusts `backlog.md` alone** — re-verifies against git/code and flags drift. Authoritative "up next" = `product/ready/`. `progress_log.json`'s `next_three_steps` is shown as advisory only, with drift flags.

### 2. `maintaining-the-backlog` skill (enhanced)
Gains a session-end "close the loop" path:
- Summarise what changed using `git status` + working-tree state (works without commits).
- Move PRDs (ready→Done etc.), regenerate `backlog.md` + `CURRENT_STATE.md`.
- Refresh `progress_log.json` (advisory).
- Append to `learnings.md` **only** when the insight is genuinely new (grep-first dedup).
- Write the checkpoint file (below).

### 3. `.pi/extensions/backlog-checkpoint.ts` (new, project-local)
Hooks pi's `session_before_switch` (reason `"new"`), i.e. right before `/new`:
- **Always** runs the mechanical refresh: `python product/backlog.py` + `python summarise.py`.
- **Blocks `/new`** (default = cancel) when the checkpoint is **older than the latest source-file change** — a commit-independent signal so it works with uncommitted work.
- Cancel → stay in session, run close-the-loop, then `/new` again. Confirm → proceed anyway.

### 4. Checkpoint file: `product/context/SESSION_CHECKPOINT.json`
Written by the close-the-loop skill, read by the extension. Holds timestamp, summary, moved files, resulting "up next", and whether learnings were appended.

## Freshness signal (commit-independent)

Stale ⇔ `mtime(SESSION_CHECKPOINT.json)` < `max mtime` of all repo files, excluding:

- `.git/`, `.pi/`, `node_modules/`, `.venv/`, `venv/`, `__pycache__/`, `*.pyc`
- `static/`, `media/`, `db.sqlite3`, `test_db.sqlite3`, `.env`
- derived outputs: `product/backlog.md`, `product/context/CURRENT_STATE.md`, `product/context/SESSION_CHECKPOINT.json`

Any source/PRD/learnings change after the last checkpoint therefore triggers the guardrail, committed or not.

## Decisions

- Enhance `maintaining-the-backlog` (no separate "closing-the-loop" skill).
- `product/ready/` is the authoritative "up next"; `progress_log.json` is advisory.
- Guardrail prompt defaults to **cancel** (must consciously choose to skip).
- Scoped to River via: project-local `.pi/extensions/` + skill marker gate on `product/backlog.py` + `summarise.py`.
