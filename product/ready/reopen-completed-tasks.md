# PRD: Re-open Completed Tasks + Participant Count on Completion

**Status:** Implemented — committed + unit-tested; UAT 8/9 passed. Outstanding: success toast on complete/re-open (UAT item 4).
**Source:** Sarah Schumann (Director), 2026-08-12

## 1. Problem Statement

Two related complaints about task completion:

1. **Completion is one-way.** Once a task is ticked complete there is no way to "un-complete" / re-open it. If the tick was accidental, or the work was recorded under the wrong task, the user is stuck.
2. **Participant count doesn't update after ticking complete.** When Sarah ticks a task complete and then edits it, the participant count doesn't change. The number of people who actually did the work is never captured at completion time, and editing the *task* doesn't touch it.

## 2. Strategic Goal

Make task completion reversible and ensure participant numbers are captured/editable at the moment of completion, so the Participation metric on the dashboard reflects reality.

## 3. What We Know (Current Behaviour)

- **`participant_count` lives on `VisitLog`, not `Task`** (`core/models.py`, `VisitLog.participant_count`, `PositiveIntegerField(default=0)`).
- **`task_complete_view`** (`core/views.py`, `task_complete_view(request, pk)`) creates a minimal `VisitLog` with no participant value (defaults to `0`) and sets `task.is_completed = True`. It returns `{'success': False, 'error': 'already_completed'}` if the task is already done.
- **Tick-to-complete** (weekly + monthly planners, shipped via `product/Done/tick-to-complete-planner.md`) calls the same `task_complete_view` via AJAX — so the auto-created log has `participant_count = 0` and there is no participant input in that flow.
- **`TaskForm` has no participant field** (`core/forms.py`). Editing a task can never change participants.
- **`VisitLogForm` does have a typeable `participant_count` field** (`core/forms.py` + `visit_log_form.html` line ~191), and the daily agenda routes "Edit" on a completed task to `visit_log_edit` (`daily_agenda.html` line ~112). So on the daily agenda, editing the *log* works — but the *planner* tick flow and *task* edit flow do not.
- There is no `un-complete` endpoint or UI anywhere.

### Root cause summary
- "Participant count doesn't update" = participant data is on the VisitLog, but completion (tick) and task-edit don't surface it.
- "Can't re-open" = `is_completed` is only ever set to `True`; there is no path back to `False`.

## 4. Proposed Scope

- **Re-open / un-complete:** Add a way to set `task.is_completed = False` from the planner and daily agenda.
- **Participant capture at completion:** Surface a participant-count input (or quick prompt) at the moment of ticking complete, and/or route the user to the visit-log edit immediately after ticking so participants can be recorded.
- **Participant editing consistency:** Ensure editing a completed task exposes the VisitLog participant count (align the planner edit path with the daily-agenda "Edit Log" routing).

### Explicitly Out of Scope (initial)
- Changing the dashboard Participation aggregation itself (it already sums `VisitLog.participant_count`).
- Full visit-log form redesign.
- Kanban (rolling to-do) completion — rolling tasks are separate.

## 5. Open Questions / Decisions Needed

1. **What happens to the auto-created VisitLog on re-open?**
   - If it is empty (no participants, no metrics, no photos) → delete it automatically?
   - If it has recorded data → keep it but warn the user, or block re-open?
2. **Re-open scope:** Should re-open be allowed for *all* completed tasks, or only those completed via the quick tick (minimal log)?
3. **Participant capture UX at tick time:** inline number input on the card, a small modal, or auto-redirect to the log edit form?
4. **Should "re-open" and "participant-on-complete" ship together or as two slices?** (Recommend: two slices, one PRD.)

## 6. Success Criteria (high-level)

- A completed task can be re-opened (returned to incomplete) with a clear, safe behaviour for its auto-created VisitLog.
- Participants are captured at completion time and reflected in the dashboard Participation total.
- Editing a completed task reliably updates participant count (planner path matches daily-agenda path).

## 7. Likely Touch Points

| Area | File | Note |
|------|------|------|
| Complete view | `core/views.py` — `task_complete_view` | Add un-complete + participant handling |
| URL | `core/urls.py` | Possibly add un-complete endpoint |
| Task form | `core/forms.py` — `TaskForm` | Decide whether participant lives here or stays on VisitLog |
| Planner templates | `weekly_planner.html`, `monthly_planner.html` | Tick flow + re-open affordance |
| Daily agenda | `daily_agenda.html` | Re-open affordance |
| Tests | `core/tests/test_task_complete.py` | Extend for un-complete + participant |

## 8. Pre-Flight Checklist

- [x] Re-open behaviour for auto-created VisitLog decided (keep + audit trail)
- [x] Participant-capture UX at tick time decided (tick prompt + routing fix)
- [x] One-work-record-per-task rule decided (reuse VisitLog; Approach 1 redirect)
- [x] Audit history visibility decided (list on VisitLog edit form)
- [x] Confirm dashboard Participation metric already correct (no change needed)
- [x] Tests written and passing
- [ ] Split into implementation slices agreed

---

# 2026-08-14 Re-open + Participant Count — Design

## Locked Decisions

| # | Decision | Choice |
|---|----------|--------|
| 1 | Re-open semantics | Flip `is_completed` back to `False`; keep the VisitLog; record an audit event |
| 2 | Audit trail | New `TaskCompletionHistory` model (mirrors `SectionStageHistory`) |
| 3 | One work record per task | Reuse/update the existing VisitLog on re-completion — never duplicate |
| 4 | Participant capture | Both: inline tick prompt + planner edit-routing fix |
| 5 | Full-log-form duplicate (edge case) | Approach 1 — `VisitLogCreateView.get()` redirects to `visit_log_edit` when the task already has a log |
| 6 | History UI | One-line-per-event list on the VisitLog edit form when linked to a task |

## Data Model (new)

```python
class TaskCompletionHistory(models.Model):
    ACTION_CHOICES = [('completed', 'Completed'), ('reopened', 'Reopened')]
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='completion_history')
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    changed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-changed_at']

    def __str__(self):
        return f"{self.task} — {self.get_action_display()} at {self.changed_at}"
```

`User` is already imported in `core/models.py` (`django.contrib.auth.models`).

## Completion Flow — modify `task_complete_view`

- Accept an optional `participant_count` in the POST body.
- **Reuse, don't duplicate:** `existing = task.visitlog_set.first()`. If present, update its `participant_count` (leave date/notes/section as-is); otherwise create a new `VisitLog` with `participant_count` (default 0).
- `task.is_completed = True`; `task.save()`.
- `TaskCompletionHistory.objects.create(task=task, action='completed', user=request.user)`.
- Return JSON (unchanged shape: `{'success': True}` / `{'success': False, 'error': ...}`).

## Re-open Flow — new `task_reopen_view`

- `POST /tasks/<pk>/reopen/`.
- `task.is_completed = False`; `task.save()`.
- **Do not touch the VisitLog** (it stays as the work record).
- `TaskCompletionHistory.objects.create(task=task, action='reopened', user=request.user)`.
- Return `JsonResponse({'success': True})` for AJAX; redirect to daily agenda otherwise.

## Participant Capture — "both"

- **Tick prompt (A):** on incomplete task cards (weekly/monthly planners), clicking the tick reveals a compact inline number input (participants, default blank/0) with confirm/cancel. Confirm POSTs `participant_count` to `task_complete`.
- **Routing fix (B):** in `weekly_planner.html` and `monthly_planner.html`, the edit link for a completed task points to `visit_log_edit` (fall back to `task_edit` if no VisitLog) — matching `daily_agenda.html`'s existing behaviour.

## Edge Case — Approach 1 (one work record per task)

- In `VisitLogCreateView.get()`: if `?task=<id>` and that task already has a `VisitLog`, redirect to `visit_log_edit` for that log, preserving `next`.
- Prevents the re-open → re-complete-via-full-form sequence from creating a second log.
- No existing data affected (verified: 0 tasks with >1 log in the dev DB, 2026-08-14).
- General logs (no task / `task=None`) are unaffected.

## History List (visible)

- On `visit_log_form.html`, when the log is linked to a task, render `task.completion_history` as a one-line-per-event list: action label, `user` (if present), `changed_at`.

## File Map

| File | Change |
|------|--------|
| `core/models.py` | Add `TaskCompletionHistory` |
| `core/migrations/` | New migration |
| `core/views.py` | Modify `task_complete_view`; add `task_reopen_view`; add redirect in `VisitLogCreateView.get()` |
| `core/urls.py` | Add `tasks/<pk>/reopen/` |
| `weekly_planner.html`, `monthly_planner.html` | Tick prompt + un-tick affordance + edit routing |
| `daily_agenda.html` | Un-tick (re-open) affordance |
| `visit_log_form.html` | History list |
| `core/tests/test_task_complete.py` (+ new) | Tests below |

## Test Plan (MANDATORY)

- Unit: reopen flips `is_completed=False` and creates a `reopened` audit event; the VisitLog is preserved.
- Unit: tick with `participant_count` writes to the VisitLog; tick with no participants → 0.
- Unit: re-completion reuses the existing VisitLog (no second log created).
- Unit: `VisitLogCreateView` GET with `?task=<already-logged task>` redirects to `visit_log_edit`.
- Unit: completed-task edit link resolves to `visit_log_edit` (routing).
- Edge: re-open a task completed via the full log form (rich log) → log preserved, audit recorded.
- Edge: double-tick → `already_completed` (existing behaviour).

## Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Optimistic UI complexity with the inline tick prompt | Medium | Keep prompt minimal; disable during flight, revert on error |
| Audit model has no user on non-login flows | Low | All views are `LoginRequiredMixin`; `request.user` always present |
| Pre-existing tasks have no history | Low | History starts from first completed/reopened event after deploy |
| `VisitLogCreateView` redirect surprises a user wanting a fresh log | Low | Only redirects when `?task=` targets a task that already has a log |

---

# Re-open + Participant Count — Implementation Plan

**Goal:** Make task completion reversible and capture participants at completion time.

**Architecture:** Backend adds a `TaskCompletionHistory` audit model plus two JSON endpoints (`task_complete` modified, `task_reopen` new); `VisitLogCreateView` redirects to edit when a task already has a log. Frontend adds an inline participant prompt + un-tick affordance on the planners and daily agenda.

**Tech Stack:** Django 6, SQLite (test/dev), Vanilla JS.

**UAT:** `tests/uat/reopen_completed_tasks_uat.md` — drafted before implementation.

## Tasks

1. Add `TaskCompletionHistory` model + migration (no tests — schema only).
2. Extend `test_task_complete.py` (participant capture, default 0, reuse, history) — RED.
3. Modify `task_complete_view` — GREEN.
4. Add `test_task_reopen.py` (reopen, history, redirect, POST-only, VisitLogCreateView redirect, planner edit routing) — RED.
5. Add `task_reopen_view` + URL — GREEN.
6. Add `VisitLogCreateView.get()` redirect — GREEN.
7. Update templates (weekly/monthly planners, daily agenda, visit_log_form) — GREEN.
8. Update `test_urls.py` POST_ONLY_NAMES — GREEN.
9. Full suite + `python lint.py`.
