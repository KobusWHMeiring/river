# PRD: Dashboard Metric Drill-Down ("Where does this number come from?")

**Status:** In Refinement — design drafted 2026-08-14 (awaiting review)
**Source:** Sarah Schumann (Director), 2026-08-12

## 1. Problem Statement

The Impact Dashboard shows aggregate metric cards (Litter Removed, Participation, Re-Planting, Invasives Removed), but a manager cannot see *which* events/tasks contributed to a number. Sarah wants to click each metric and see the source events/tasks, similar to the Recent Activity list.

## 2. Strategic Goal

Make every dashboard metric traceable — click a metric and see the underlying VisitLogs (and their linked tasks/sections) that produced it — so managers can trust and investigate the numbers.

## 3. What We Know (Current Behaviour)

- **Aggregation** happens in `GlobalDashboardView.get_context_data()` (`core/views.py`):
  - Litter / Plants / Weeds = `Sum('value')` over `Metric` filtered by `metric_type`.
  - Participants = `Sum('participant_count')` over `VisitLog`.
- **Recent Activity feed** (`dashboard.html`, `recent_visits`) already lists `VisitLog`s with section badge, task link, notes, per-metric chips (`metric.value metric.label`), and photos. This is exactly the list-style presentation Sarah wants to reuse.
- **"View All Logs"** links to `visit_log_list` (Master Activity Log, `product/Done/all_logs_view.md`), but that list is not filtered per metric.
- There is currently **no per-metric drill-down** — the stat cards are static text.

### Data model notes
- A metric is tied to a `VisitLog` via `Metric.visit` (FK), and a `VisitLog` is tied to an optional `Task` (`VisitLog.task`) and optional `Section`.
- So the "source" of a metric is the `VisitLog`, which can point back to its `Task` and `Section`.

## 4. Proposed Scope

- Make each metric card (Litter, Participation, Plants, Invasives) clickable — or add a clear "View source" affordance on each.
- Clicking opens a filtered list of the contributing events (VisitLogs), using the Recent Activity list pattern.
- Optionally include the species breakdown rows (plants/weeds) as drill-downs too.

### Explicitly Out of Scope (initial)
- Changing the aggregation logic or metric definitions.
- Excel export of drill-downs (could be a follow-up).
- Editing records from the drill-down (read-only view first).

## 5. Open Questions / Decisions Needed

1. **Granularity:** Drill into `VisitLog`s (events) or `Task`s (planned work)? The director said "events/tasks" — recommend drilling into VisitLogs (the actual recorded data), which already link back to Tasks. Confirm.
2. **Reuse vs new view:** Filter the existing `visit_log_list` via a query param (e.g. `?metric_type=litter_general`), or build a dedicated drill-down view? Recommend reusing `visit_log_list` with a filter param.
3. **Which metrics:** All 4 stat cards, plus plant/weed species breakdowns, or just the top-level cards?
4. **Participants** is summed over `VisitLog` (not `Metric`) — so its drill-down lists VisitLogs with `participant_count > 0`, not metric chips. Confirm that's the right source list.
5. **Date range:** Should the drill-down show all-time contributors or a recent window (matching the dashboard's current all-time totals)?

## 6. Success Criteria (high-level)

- Clicking any dashboard metric shows the list of events/tasks that produced it.
- The list reuses the Recent Activity visual pattern (section, task, notes, metrics, date).
- The numbers in the drill-down reconcile with the metric card total.

## 7. Likely Touch Points

| Area | File | Note |
|------|------|------|
| Dashboard view | `core/views.py` — `GlobalDashboardView` | Add links/filters |
| Dashboard template | `core/templates/core/dashboard.html` | Make cards clickable |
| Log list | `core/views.py` — `VisitLogListView` + `visit_log_list.html` | Add `metric_type`/participant filter |
| URLs | `core/urls.py` | Reuse `visit_log_list` with param |
| Tests | `core/tests/test_dashboard.py` | Drill-down link + filter tests |

## 8. Pre-Flight Checklist

- [x] Drill-down granularity (VisitLogs vs Tasks) confirmed → VisitLogs (events)
- [x] Reuse vs new view decided → Approach A (reuse `visit_log_list`)
- [x] Metric coverage decided → 4 cards + species rows (Option B)
- [x] Participant drill-down source confirmed → `participant_count > 0`
- [x] Date-range behaviour decided → all-time default (reconciles with cards)
- [x] Inspection-tools scope decided → metric/species filters + sort + export
- [ ] Tests written and passing

---

# 2026-08-14 Dashboard Metric Drill-Down — Design

## Locked Decisions

| # | Decision | Choice |
|---|----------|--------|
| 1 | Granularity | VisitLogs (events), each linking back to Task/Section |
| 2 | Interaction | Approach A — reuse `visit_log_list` with filter params |
| 3 | Inspection toolkit | Metric/species filters + sort + filtered export (one PRD) |
| 4 | Drill-down scope | 4 metric cards + plant/weed species rows |
| 5 | Sort options | Newest (default), Oldest, Section A–Z, Participants high→low |
| 6 | Export | Filtered results → single-sheet Excel (openpyxl), new endpoint |
| 7 | Affordance | "View source" link per card (not whole-card click; avoids nested links with species rows) |

## Interaction

- Each of the 4 metric cards gets a **"View source"** affordance (icon/link in the card header) → `visit_log_list?metric=<value>`.
- **Species rows** are clickable → `visit_log_list?metric=plant&species=<label>` (or `metric=weed&species=`).
- Whole-card click is avoided because cards contain species rows that are themselves links (nested links are invalid HTML).

## New Filter Params on `VisitLogListView`

- `metric`: `litter` | `plant` | `weed` | `participants`
  - `litter` → logs with any `litter_general` **or** `litter_recyclable` metric
  - `plant` → logs with a `plant` metric
  - `weed` → logs with a `weed` metric
  - `participants` → logs with `participant_count > 0`
- `species`: `Metric.label__icontains` (combined with `metric` when both present)
- Existing `q`, `section`, `start_date`, `end_date`, `activity_type` remain unchanged.
- Implementation note: metric filters use `filter(metrics__metric_type=...)` + `.distinct()` to avoid duplicate rows from the M2M-style join.

## Sort (new `sort` param)

- `-date` (default, current behaviour), `date`, `section`, `-participant_count`.

## Export (new endpoint `export/visit-logs/`)

- Single-sheet Excel via openpyxl (matches existing `DataExportView` style), respecting **all** active filters + sort.
- One row per log, columns: Date, Section, Task (template name or "Unplanned"), Task type, Participants, General bags, Recyclable bags, Plants (summarised `Species: count; …`), Weeds (summarised), Notes.

## Reconciliation Default

- Drill-down links carry **no date filter** by default (all-time), so the list reconciles with the card totals. Users narrow with the page's date filters afterwards.

## File Map

| File | Change |
|------|--------|
| `core/views.py` | Extend `VisitLogListView.get_queryset` (metric/species/sort); add `VisitLogExportView` |
| `core/urls.py` | Add `export/visit-logs/` |
| `core/templates/core/visit_log_list.html` | Metric + species filters, sort dropdown, Export button |
| `core/templates/core/dashboard.html` | Card "View source" links + species row links |
| `core/tests/` | Filter/sort/export tests |

## Test Plan (MANDATORY)

- Unit: each `metric` filter returns the right logs (`litter` covers both litter types; `participants` covers `>0`).
- Unit: `species` narrows correctly (and composes with `metric`).
- Unit: sort orders correctly for all four options.
- Unit: export respects filters/sort and produces the expected columns + row count.
- Edge: a metric/species filter with no matches returns an empty list (no crash).

## Data Notes (current state, not blockers)

- Participants drill-down currently returns 1 log (sparse; improves after PRD #1 ships).
- Weeds drill-down returns empty until weeding data is captured.
- Plant species drill-down is rich (26 species, 257 plants) — the main justification for species-level drill-down.
