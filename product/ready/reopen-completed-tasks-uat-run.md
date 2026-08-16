# Run UAT: Re-open Completed Tasks + Participant Count

**Status:** Ready — pending manual QA (no design decisions needed)
**Source:** Implementation session, 2026-08-14

## 1. Purpose

The "Re-open Completed Tasks + Participant Count" feature (`reopen-completed-tasks.md`) is implemented, unit-tested (67 tests passing), but the human acceptance scenarios have **not yet been run**. This item is the reminder to execute those UAT scenarios against the running app and record the result.

## 2. What to Do

Run every scenario in the UAT file and fill in the sign-off table:

- **UAT file:** `tests/uat/reopen_completed_tasks_uat.md`

The scenarios cover:
1. Tick-to-complete with participant capture (weekly planner).
2. Tick with no participants → 0.
3. Re-open (un-tick) a completed task; verify the VisitLog and its data are preserved.
4. Re-complete after re-open (one work record, no duplicate VisitLog).
5. Edit routing on completed tasks (planners → VisitLog edit, fallback task edit).
6. Full-log-form duplicate prevention (redirect to edit when `?task=` already has a log).
7. Double-tick protection (`already_completed`).
8. Error scenario (network failure reverts the UI).

Run the data-integrity SQL checks at the bottom of the UAT file after testing.

## 3. Acceptance

- [ ] All UAT scenarios pass (or failures recorded with notes).
- [ ] Sign-off table in `tests/uat/reopen_completed_tasks_uat.md` is completed.
- [ ] Data-integrity checks return no unexpected rows.

## 4. Notes

- The tick/re-open actions perform a full page refresh on success (confirmed acceptable by the Director).
- On completion of this item, the `reopen-completed-tasks.md` PRD and this item can be moved to `product/Done/`.
