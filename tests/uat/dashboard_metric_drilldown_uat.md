# UAT: Dashboard Metric Drill-Down ("Where does this number come from?")

**Feature slug:** `dashboard_metric_drilldown`
**Drafted:** 2026-08-16 (before implementation)

## Pre-test setup
- Logged-in user (team or manager).
- Seed data (or confirm in the test DB) covering every path:
  - A log with `litter_general` **and** `litter_recyclable` metrics (same visit).
  - A second log with only `litter_general`.
  - A log with `plant` metrics carrying a species `label` (e.g. `Restio`), plus a
    **different** log with a `plant` metric labelled `Restio reed` (to prove exact-match).
  - A log with `participant_count > 0`, and one with `participant_count = 0`.
  - A log with no `section` (null section) to test Section A–Z sort.
  - (Optional) A `weed` metric, or none at all to exercise the empty state.

---

## Scenario 1: Litter "View source" happy path
1. Open the Impact Dashboard.
2. On the **Litter Removed** card, click **View source**.
3. **Expected:** Lands on `visit_log_list?metric=litter`.
4. **Expected:** The list shows only logs containing a `litter_general` **or**
   `litter_recyclable` metric.
5. **Expected:** A total header reads **"Litter — N bags"** where `N` equals the
   Litter Removed card total on the dashboard.

## Scenario 2: Participation drill-down
1. On the dashboard, click **View source** on the **Participation** card.
2. **Expected:** Lands on `visit_log_list?metric=participants`; only logs with
   `participant_count > 0` appear (the `0`-participant log is absent).
3. **Expected:** Header reads **"Participation — N people"** matching the card.

## Scenario 3: Plant species row drill-down (exact match)
1. On the **Re-Planting** card, click the species row `Restio`.
2. **Expected:** Lands on `visit_log_list?metric=plant&species=Restio`.
3. **Expected:** Only the log with the **exact** label `Restio` appears — the
   `Restio reed` log does **not** appear.
4. **Expected:** Header total equals the `Restio` count shown on that species row.

## Scenario 4: Weeds empty state
1. Click **View source** on the **Invasives Removed** card.
2. **Expected:** With no weed data, the list shows the "No logs found" empty state
   and the header reads **"Weeds — 0"** (no crash).

## Scenario 5: Sorting
1. On `visit_log_list`, use the sort dropdown for each option:
   - **Newest** (default) → newest date first.
   - **Oldest** → oldest date first.
   - **Section A–Z** → alphabetical by section name, with the no-section log **last**.
   - **Participants high→low** → highest `participant_count` first.

## Scenario 6: Filtered export
1. On `visit_log_list`, set `metric=litter` and a date range, then click **Export**.
2. **Expected:** A `.xlsx` downloads with one row per matching log and columns:
   Date, Section, Task, Task Type, Participants, General Bags, Recyclable Bags,
   Plants, Weeds, Notes.
3. **Expected:** Row count matches the filtered list; General/Recyclable bags per
   row reflect that log's metric values.

## Scenario 7: Reconciliation (no date filter)
1. For each of the 4 cards, drill down and confirm the total header equals the
   dashboard card number exactly.

## Scenario 8: Filters compose with drill-down
1. On the litter drill-down, add a Section filter and a Start Date.
2. **Expected:** The list and the total header both narrow to the filtered subset.

## Error scenario
- Navigate to `visit_log_list?metric=bogus` directly.
- **Expected:** No crash; behaves like an unfiltered list (unknown metric ignored).

## Data integrity checks (after testing)
```sql
-- Every log with a litter metric is returned by the litter filter (sanity):
-- (run in shell: confirm the drill-down count == logs with litter metrics)
SELECT COUNT(DISTINCT visit_id) FROM core_metric
 WHERE metric_type IN ('litter_general','litter_recyclable');

-- No export should produce duplicate rows for a single log.
```

## Sign-off
| Role | Name | Date | Result |
|------|------|------|--------|
| Tester | | | |
| Director | Sarah Schumann | | |
