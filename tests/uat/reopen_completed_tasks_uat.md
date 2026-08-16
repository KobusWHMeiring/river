# UAT: Re-open Completed Tasks + Participant Count

**Feature slug:** `reopen_completed_tasks`
**Drafted:** 2026-08-14 (before implementation)

## Pre-test setup
- Logged-in user (team or manager).
- A task scheduled this week (weekly planner) with no VisitLog yet.
- A second task already completed via the full log form (has a rich VisitLog with metrics/participants).

---

## Scenario 1: Tick-to-complete with participant capture (weekly planner)
1. Open Weekly Planner.
2. Click the tick (check box) on an incomplete task card.
3. **Expected:** A compact inline prompt appears with a "participants" number input and Confirm/Cancel.
4. Enter `4` participants and Confirm.
5. **Expected:** Card becomes completed (strikethrough, faded, green check). The page refreshes.
6. Open Daily Agenda for that date.
7. **Expected:** Task shows as Completed; its "Edit Log" opens the VisitLog with participant count `4`.

## Scenario 2: Tick with no participants → 0
1. Tick an incomplete task, leave participants blank, Confirm.
2. **Expected:** Task completes; VisitLog participant count = `0`.

## Scenario 3: Re-open (un-tick) a completed task
1. On Weekly Planner, hover a completed task card.
2. Click the un-tick (undo/re-open) affordance.
3. **Expected:** Card returns to incomplete (tick box returns, strikethrough removed). VisitLog still exists.
4. Open Daily Agenda; edit the log for that task.
5. **Expected:** Log data (metrics, photos, participants) is preserved. A "Completion History" list shows `Completed` then `Reopened` events.

## Scenario 4: Re-complete after re-open (one work record)
1. Re-tick the task from Scenario 3, entering `6` participants.
2. **Expected:** Task completes; the SAME VisitLog is updated to `6` participants (no second log).

## Scenario 5: Edit routing on completed task (planners)
1. On Weekly Planner, hover a completed task.
2. **Expected:** Edit affordance appears and links to the VisitLog edit form (not task edit), because the task has a log.
3. If a completed task has NO VisitLog, Edit links to task edit (fallback).

## Scenario 6: Full-log-form duplicate prevention
1. For a task that already has a VisitLog, navigate to `Add Log` with `?task=<id>`.
2. **Expected:** You are redirected to the existing VisitLog's edit form (with `next` preserved), not a blank create form.

## Scenario 7: Double-tick protection
1. Immediately after completing, attempt to tick again (or POST `/complete/` twice).
2. **Expected:** Second request returns `already_completed`; no duplicate VisitLog or history spam.

## Error scenario
- Network failure during tick: UI reverts (tick box returns, not completed).

## Data integrity checks (after testing)
```sql
-- No task has more than one VisitLog
SELECT task_id, COUNT(*) FROM core_visitlog WHERE task_id IS NOT NULL GROUP BY task_id HAVING COUNT(*) > 1;

-- Every completion/reopen has a history row
SELECT action, COUNT(*) FROM core_taskcompletionhistory GROUP BY action;
```

## Sign-off
| Role | Name | Date | Result |
|------|------|------|--------|
| Tester | | | |
| Director | Sarah Schumann | | |