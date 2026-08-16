# UAT: Planner Search / Jump-to

**Feature slug:** `planner_search`
**Drafted:** 2026-08-16 (before implementation)

## Pre-test setup
- Logged-in user (team or manager).
- Dev DB has 317 non-rolling tasks; ~49% have no section, ~19% have no template.
- Known searchable strings: "litter" (instructions/template), a section name, a task-type name (e.g. "Weeding"), and "Intern training" (a task with **no section** and no template).

---

## Scenario 1: Keyword search returns live results (weekly planner)
1. Open Weekly Planner.
2. Type `litter` into the search box (top header).
3. **Expected:** Within ~300ms an inline dropdown lists up to 8 matching tasks, newest first, each showing instructions snippet + section name + task type name.
4. Click a result.
5. **Expected:** Page navigates to the **result's own week** (`?week=<result date>&highlight=<task_id>`), and that task card scrolls into view and briefly glows.

## Scenario 2: Jump-to-date (weekly)
1. On Weekly Planner, pick a past date (e.g. a March date) in the date input.
2. **Expected:** Page navigates to that date's week (`?week=<date>`).

## Scenario 3: Search + jump on monthly planner
1. Open Monthly Planner.
2. Search for a string you know matches a past event (e.g. `litter`).
3. Click a result dated in a different month.
4. **Expected:** Page navigates to the **result's month** (`?year=&month=&highlight=<task_id>`), and the correct day-cell badge is highlighted.

## Scenario 4: Null section/template fallback
1. Search `Intern training` (a task with no section and no template).
2. **Expected:** Result shows **"No Section"** and **"Custom Task"** (no blank/null/`None` text).
3. Click it.
4. **Expected:** It lands on the correct week and the card (rendered with "General"/"Admin"/"Strategy" + "Custom Task" fallbacks) is highlighted.

## Scenario 5: No matches / blank query
1. Search `zzzzz`.
2. **Expected:** Empty state (dropdown shows "No results" or simply doesn't open).
3. Clear the box (or enter spaces).
4. **Expected:** No dropdown appears.

## Scenario 6: Rolling (Kanban) tasks excluded
1. Note the text of a rolling to-do item on the Kanban board.
2. Search that text in the planner search.
3. **Expected:** The rolling task does **not** appear (planner search is non-rolling only).

## Scenario 7: Special characters don't break search
1. Search `%` and then `_` and then `"`.
2. **Expected:** No error; results treat the characters literally (likely empty list).

## Error scenario
- Log out, then directly GET `/core/tasks/search/?q=litter`.
- **Expected:** 302 redirect to the login page (no JSON/task text leaked to anonymous users).

## Data integrity checks (after testing)
```sql
-- Search endpoint caps at 8 and is newest-first (spot check):
-- run the same query manually and confirm ordering/limit.

-- Null handling: every returned section_name is a non-empty string.
```

## Sign-off
| Role | Name | Date | Result |
|------|------|------|--------|
| Tester | | | |
| Director | Sarah Schumann | | |
