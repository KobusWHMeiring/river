# UAT: Planner Activity Indicators on Dashboard

**Feature slug:** `planner_activity_indicators`
**Drafted:** 2026-08-16 (after implementation)

## Pre-test setup
- Logged-in manager (dashboard access).
- Tasks scheduled in the **current calendar week (Mon–Sun)** in the Weekly Planner, using real templates:
  - Section A → a Litter task (this week)
  - Section B → a Weed task (this week)
  - Section C → a Plant task (this week)
  - Section D → an Admin task (this week)
- Note: the "Active Sections" list only shows sections with visit activity in the last 30 days. Use sections that already appear there, or the tags simply won't be visible for that section (expected — tags live on that list).
- Also useful: a completed task this week, a task with no template, and a task with no section.

---

## Scenario 1: Field tags on Active Sections
1. Open the Impact Dashboard.
2. Find the Active Sections list.
3. Locate Section A (Litter task this week).
4. **Expected:** A red "Litter" tag below its name.
5. Repeat for Weed (amber "Weed") and Plant (green "Plant").

## Scenario 2: Admin tag on Active Sections
1. Locate Section D (Admin task this week).
2. **Expected:** An indigo "Admin" tag below its name.

## Scenario 3: No tag when no tasks this week
1. Find an Active Section that has no tasks this week.
2. **Expected:** No tags below its name (layout unchanged).

## Scenario 4: Field tags on Lifecycle bars
1. Look at the Lifecycle Progress bars.
2. Find the stage containing Section A (Litter task).
3. **Expected:** A red "Litter" tag above that stage's progress bar.
4. Repeat for Weed (amber) and Plant (green) stages.

## Scenario 5: Admin excluded from Lifecycle bars
1. Find the stage containing Section D (Admin task).
2. **Expected:** No indigo "Admin" tag above that bar (admin is not a field activity).

## Scenario 6: Completed tasks still count
1. Mark one of this week's tasks complete (e.g. the Litter task).
2. Reload the dashboard.
3. **Expected:** The tag still appears for that section/stage (indicator reflects the week's plan, not remaining work).

## Scenario 7: Time window is Mon–Sun
1. Ensure a task is dated **next week** (or last week) only.
2. **Expected:** No tag appears for that section (only the current calendar week counts).

## Scenario 8: Task with no template is skipped
1. Create a task this week with no template.
2. **Expected:** No "Custom" tag; that task contributes nothing.

## Scenario 9: Section-less ("Admin") task is skipped
1. Create a task this week with no section (the planner's "Admin" convention).
2. **Expected:** The dashboard renders normally; no tag is shown anywhere for that task.

## Scenario 10: Empty state
1. With no tasks scheduled this week at all, reload the dashboard.
2. **Expected:** No tags appear in Active Sections or Lifecycle bars; the page renders normally.

## Error scenario
- None — read-only view change with no user input or network calls.

## Data integrity checks (after testing)
No schema or data changes — nothing to verify in the database.

## Sign-off
| Role | Name | Date | Result |
|------|------|------|--------|
| Tester | | | |
| Director | Sarah Schumann | | |
