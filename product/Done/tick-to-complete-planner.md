# PRD: Tick to Complete Tasks from Planner (#6)

## 1. Problem Statement

Completing a task currently requires either navigating away from the planner to create a full visit log, or using the `task_complete_view` which redirects to the daily agenda. There is no way to mark a task as done with a single click while staying on the planner. Sarah wants a quick tick that completes the task and creates a minimal record without leaving the planner view.

## 2. Strategic Goal

Add an in-place completion tick on planner task cards so field managers can rapidly mark tasks as done while reviewing the weekly/monthly plan, improving planner stickiness and reducing context-switching.

## 3. Proposed Scope

- **Weekly Planner:** Add a clickable tick icon to incomplete task cards that fires an AJAX completion
- **Monthly Planner:** Same tick on task badges
- **Backend:** Modify existing `task_complete_view` to support AJAX (JSON response) alongside existing redirect behavior
- **VisitLog:** Auto-create a minimal VisitLog on tick (date=today, section=task.section, notes="Task completed: {instructions}")

### Explicitly Out of Scope
- Changing the daily agenda or section detail views
- Adding "un-tick" (un-complete) functionality — completion is one-way for now
- Modifying the existing log-and-complete flow (full visit log form)
- Adding task completion from the Kanban to-do board

## 4. Design Decisions

| Decision | Rationale |
|----------|-----------|
| Create minimal VisitLog on tick | Ensures every completion has a record; matches existing `task_complete_view` behavior |
| AJAX via `X-Requested-With` header | Backward-compatible — existing redirect flow for non-AJAX callers still works |
| Optimistic UI update | Immediate visual feedback; revert on network failure |
| One-way (complete only) | Matches current behavior; prevents accidental un-completes |
| Keep edit link accessible | Hover or long-press reveals edit option as fallback |

## 5. Technical Constraints

- **Backend:** Modify `task_complete_view` — existing function at `core/views.py:846`. Add AJAX detection and JSON response branch. Create VisitLog BEFORE marking complete (atomicity via ordering).
- **Frontend:** Vanilla JavaScript `fetch()` call. No new dependencies. Optimistic DOM update (add opacity class, swap icon). Revert on error.
- **Existing data:** Task model unchanged. VisitLog model unchanged.

---

# User Stories

## Story 1: Tick Complete on Weekly Planner

**Value Proposition:** As a Manager reviewing the weekly planner, I want to tick a task as complete with one click so I can rapidly mark off done work without leaving the planner.

**Technical Implementation Path:**
- Target File: `core/views.py` — `task_complete_view()`
  - Add: detect `X-Requested-With: XMLHttpRequest` header
  - On AJAX: create VisitLog, mark `is_completed=True`, return `JsonResponse({'success': True})`
  - On non-AJAX: existing redirect to daily agenda (unchanged)
- Target File: `core/templates/core/weekly_planner.html`
  - Replace edit icon on incomplete task cards with clickable tick icon
  - Add JS: `fetch()` on tick click, optimistic update, revert on failure
  - Keep edit link on hover/long-press or as separate small icon

**Acceptance Criteria (AC):**
- [ ] Clicking the tick on an incomplete task card marks it complete in-place
- [ ] Task card immediately greys out (opacity 60%) and icon changes to check
- [ ] A minimal VisitLog is created with date=today and auto-generated notes
- [ ] Page does NOT navigate away — user stays on planner
- [ ] Completed tasks show the check icon and cannot be ticked again
- [ ] Network failure gracefully reverts the UI and shows feedback

**The Test Plan (MANDATORY):**
- **Unit Test:** `test_task_complete_ajax`: POST to `/tasks/<id>/complete/` with `X-Requested-With` header. Verify: returns JSON `{success: true}`, task.is_completed=True, VisitLog created with correct fields.
- **Edge Case:** Ticking an already-completed task returns `{success: false, error: 'already_completed'}`.
- **Edge Case:** VisitLog creation fails (e.g., DB error) → task remains incomplete, error returned.

---

## Story 2: Tick Complete on Monthly Planner

**Value Proposition:** As a Manager viewing the monthly calendar, I want the same quick-tick functionality on monthly planner task badges.

**Technical Implementation Path:**
- Target File: `core/templates/core/monthly_planner.html`
  - Same tick icon + fetch() handler as weekly planner
  - Monthly task badges are more compact — tick icon must fit at 10px text size

**Acceptance Criteria (AC):**
- [ ] Monthly planner task badges show tickable icon for incomplete tasks
- [ ] Tick behavior identical to weekly planner (AJAX, optimistic update, VisitLog created)
- [ ] Compact sizing works on the dense monthly grid

**The Test Plan (MANDATORY):**
- **Playwright E2E (future):** Navigate to monthly planner, tick a task, verify card greys out and page stays on monthly view.

---

## 6. Task Card UI Before/After

```
BEFORE (incomplete):
┌──────────────────────────────────────┐
│ [Oakdale]          [edit icon →]     │
│ Weeding - Remove invasives            │
└──────────────────────────────────────┘

AFTER (incomplete — with tick):
┌──────────────────────────────────────┐
│ [Oakdale]    [☐ tick] [edit icon→]   │
│ Weeding - Remove invasives            │
└──────────────────────────────────────┘

AFTER (completed):
┌──────────────────────────────────────┐  ← 60% opacity
│ [Oakdale]    [✓ check]               │
│ Weeding - Remove invasives            │
└──────────────────────────────────────┘
```

## 7. File Map

| File | Change | Risk |
|------|--------|------|
| `core/views.py` | Modify `task_complete_view()` — AJAX branch + atomic ordering | Low — additive branch, existing path unchanged |
| `core/templates/core/weekly_planner.html` | Tick icon + fetch() handler on team/manager/chairperson task cards | Low — replaces edit icon on incomplete tasks |
| `core/templates/core/monthly_planner.html` | Same tick icon + handler on task badges | Low — additive |
| `core/tests/test_views.py` | Add AJAX completion tests | None |

## 8. Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Double-tick (rapid clicks create duplicate VisitLogs) | Medium | Disable tick icon after first click (optimistic). Backend: check `is_completed` before creating VisitLog. |
| Optimistic update flash on slow network | Low | 300ms debounce before showing error revert. |
| Monthly planner density — tick too small to tap | Low | Ensure minimum 24×24px touch target on the tick area. |

## 9. Pre-Flight Checklist

- [x] Design approach confirmed (minimal VisitLog, AJAX, optimistic update)
- [x] Reuses existing `task_complete_view` — no new URL needed
- [x] One-way completion only — scope locked
- [x] Both planners covered
- [ ] Backend AJAX branch implemented
- [ ] Frontend tick + fetch() implemented on both planners
- [ ] Unit tests for AJAX endpoint
- [ ] Manual test: tick task, verify VisitLog created, verify planner stays in place

---

*Design written 2026-08-11 — Tick to Complete from Planner.*
