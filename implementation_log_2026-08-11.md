# Implementation Log — 2026-08-11

> **Sprint:** Foundation Stabilization (Phase 0)
> **Source Plan:** `product/context/prinicples/consolidated-sprint-plan.html`
> **PM Brief:** `product/context/prinicples/pm-brief.md`

---

## Completed (P0 Docs — ~1.5h)

### 0.1 — Register River in Composing-Context Skill ✅
**File:** `C:\Users\Kobus Meiring\.agents\skills\composing-context\SKILL.md`

Added a §River routing table matching the Harvester/Homtini pattern with task signals, modes, sub-skills, and first docs. Added River-specific rules (summarise.py regeneration, ADR directory, backlog as single source of truth).

### 0.2 — Refresh project_overview.md ✅
**File:** `product/context/project_overview.md`

- Updated date from 2026-02-19 → 2026-08-11
- Updated Current State Summary to reflect active production use
- Added completed features: Chairperson role, Multi-day tasks, Excel Export, Rolling To-Do, Mobile responsive, Redirect context fix
- Updated Remaining Backlog to match `progress_log.json` next_three_steps + Sarah's production feedback
- Replaced stale Next Steps with current sprint status

### 0.3 — Clean up backlog.md + Consolidate backlog_v1.md ✅
**File:** `product/backlog.md`

Full rewrite. Removed items that were already done but still listed as pending (Monthly Calendar, Stage Tracking, Dashboard, Template Management). Consolidated Jess's production feedback (`backlog_v1.md`) and Sarah's latest request list (#2–6) into a single authoritative backlog. Added a Completed archive table. 12 items prioritized across Current Sprint / Next Sprint / Production Feedback / Original Backlog.

### 0.4 — Add §VI Performance Patterns to build_principles.md ✅
**File:** `product/context/build_principles.md`

Added 6 new principles derived from Abseil cross-pollination analysis:
1. Bulk Over Loop — never `.save()` in a loop
2. Use `.only()` / `.defer()` for list contexts
3. Prefer `.values()` / `.values_list()` for read-only rendering
4. Guard log calls in loops with `isEnabledFor()`
5. Precompute once, pass via context
6. Always `.select_related()` in list views

Also strengthened §II "Silent Errors" to include the logging guard.

### 0.7 — Regenerate CURRENT_STATE.md ✅
**File:** `product/context/CURRENT_STATE.md`

Ran `python summarise.py` — regenerated successfully.

---

## Code Audit Findings (Not Yet Implemented)

### 0.5 — Fix `create_task_series()` bulk_create
**Status: ALREADY DONE** — Discovered during code audit. `core/services/task_services.py` already uses `Task.objects.bulk_create()` (commit `abee562`). No `.save()` in loop remaining. Risk register concern about `bulk_create()` skipping `Task.save()` → `full_clean()` is moot because `date` is always set in the loop.

### 0.6 — @transaction.atomic on multi-write paths
**Status: NOT DONE.** `VisitLogCreateView.form_valid` writes 4 things sequentially without a transaction:
1. VisitLog save
2. Metric formset save
3. Photo formset save
4. Task.is_completed save

**Risk:** Partial writes possible if late steps fail. No existing test coverage for VisitLog views.

### Kanban Bug — "click move to done, snaps back to to do"
**Status: NOT YET FIXED.** Analysis:
- Kanban uses SortableJS drag-and-drop (no "click to complete" button exists)
- Backend `move_todo_task` logic appears correct on inspection
- Frontend `fetch` has no `.catch()` for network failures — if POST fails, DOM stays visually moved but backend doesn't persist
- Possible CSRF token staleness
- Existing tests: 4 in `test_todo_kanban.py` (service logic, API, view grouping, exclusions) but no test for drag-to-done flow

### sync_from_prod.py
**Status: NOT YET STARTED.** Greenfield management command.

---

## Backlog Consolidation Summary

The following items were added to `product/backlog.md`:

| # | Source | Description |
|---|--------|-------------|
| 1 | progress_log | Playwright E2E Testing |
| 2 | progress_log | Enhanced Weeding Data Capture |
| 3 | progress_log | Stage Tracking Visualization |
| 4 | Jess (v1) | Quick Log from Planner |
| 5 | Sarah #2 | Impact Overview — Participant Count |
| 6 | Sarah #3 | Planner — Tick to Complete + Log |
| 7 | Sarah #4 | Typeable Litter Bag Count on Dashboard |
| 8 | Sarah #5 | Planner Activity → Section/Lifecycle Indicators |
| 9 | Sarah #6 | Export Planner to Excel |
| 10 | Original | Edit Log Entry from Completed Task |
| 11 | Original | Sections with Recent Activity on Dashboard |
| 12 | Original | Detailed Planting Metrics on Dashboard |

---

## Next Up (P0 Code Tasks)

1. ~~**sync_from_prod.py management command**~~ ✅ Done (see below)
2. **Kanban bug fix** (production issue, ~45m) — PRD at `product/Ready/kanban-snap-back-bug.md`
3. **0.6 @transaction.atomic on VisitLog views** (20m + writing tests)

---

## sync_from_prod.py ✅

**File:** `core/management/commands/sync_from_prod.py` (adapted from Harvester version)

Management command that syncs the local SQLite database and media files from the production server. Key design decisions:

- **dumpdata/loaddata** instead of pg_dump/psql — because local is SQLite, production is PostgreSQL
- **--natural-foreign --natural-primary** — handles FK references correctly across DB engines
- **Excludes** contenttypes, auth.Permission, sessions, admin.LogEntry — these are auto-generated and can cause conflicts
- **Flush before load** — clears local DB first to avoid integrity errors
- **Rsync → SCP fallback** for media — rsync is faster (delta transfers), SCP as backup

Usage:
```bash
# Full sync (DB + media)
python manage.py sync_from_prod

# DB only (to reproduce the Kanban bug locally)
python manage.py sync_from_prod --db-only

# Dry run — download dump but don't load
python manage.py sync_from_prod --no-load --keep-dump

# Custom server
python manage.py sync_from_prod --host myserver.com --user deploy
```
