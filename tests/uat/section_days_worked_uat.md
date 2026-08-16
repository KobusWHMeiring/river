# UAT: Section "Days Worked" Metric + Remove Litter Bags

**Feature slug:** `section_days_worked`
**Drafted:** 2026-08-16 (before implementation)

## Pre-test setup
- Logged-in user (team or manager).
- One section ("test fixture") with:
  - 4 past-dated planner tasks across 3 distinct dates (one date has 2 tasks),
  - 1 future-dated planner task,
  - 1 rolling (Kanban) task.
- Expected "Days Worked" for this section = `3`.

---

## Scenario 1: Days Worked counts distinct past dates
1. Open the section detail page for the fixture section.
2. **Expected:** The "Days Worked" card shows `3` — distinct dates, not task count (the date with 2 tasks counts once).

## Scenario 2: Future tasks excluded
1. Confirm the future-dated task appears under "Upcoming Work".
2. **Expected:** "Days Worked" is still `3` (future task not counted).

## Scenario 3: Rolling (Kanban) tasks excluded
1. Confirm the rolling task is on the Kanban (rolling to-do).
2. **Expected:** "Days Worked" is still `3`.

## Scenario 4: Litter Bags card removed
1. Scroll the metric cards at the top of the section page.
2. **Expected:** No "Total Litter Bags" card anywhere.
3. **Expected:** Exactly 4 cards — Days Worked, Total Plants, Weeds Removed, Days in Stage.

## Scenario 5: Zero state
1. Open a section with no past-dated planner tasks.
2. **Expected:** "Days Worked" shows `0`.

## Error scenario
- None — this is a read-only view change with no user input or network calls.

## Data integrity checks (after testing)
No schema or data changes — nothing to verify in the database.

## Sign-off
| Role | Name | Date | Result |
|------|------|------|--------|
| Tester | | | |
| Director | Sarah Schumann | | |
