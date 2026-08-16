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
- [x] Shared filter logic extracted to `core/services/visit_log_services.py` (single source for list + export)
- [x] Species filter semantics → exact `label` match (reconciles with species-row totals)
- [x] Total header in drill-down list → aggregate reconciles with card totals
- [x] `sort=section` → `section__name` with null sections last
- [x] Tests written and passing

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

---

# 2026-08-16 Dashboard Metric Drill-Down — Design (Final, Ready for Implementation)

> Final review pass over the 2026-08-14 design. Resolves four open points and
> locks the service-layer contract. Decisions below supersede any conflicting
> text above.

## Newly Locked Decisions

| # | Decision | Choice |
|---|----------|--------|
| 8 | Shared filter logic | Extract into `core/services/visit_log_services.py`; list + export views both delegate |
| 9 | Species filter matching | **Exact** `label` match (not icontains) so species-row totals reconcile |
| 10 | Drill-down total header | Render aggregate total in `visit_log_list.html` when a `metric` filter is active |
| 11 | `sort=section` semantics | `section__name` ascending, null sections last |

## Service Layer — `core/services/visit_log_services.py` (NEW)

Two functions; the list view (`VisitLogListView`) and the new export view
(`VisitLogExportView`) both consume them so filter/aggregate logic has a single
source of truth.

```python
def build_visit_log_queryset(params: dict) -> QuerySet:
    """Apply VisitLog list filters from request.GET params.

    Data Flow Contract:
      in:  params — {q, section, start_date, end_date, activity_type,
                     metric, species, sort}
      out: QuerySet[VisitLog], filtered + ordered, with
           select_related('section','task') and prefetch_related('metrics','photos')
      side effects: none
    """

def visit_log_total(queryset: QuerySet, metric: str | None, species: str | None) -> int:
    """Aggregate total for the active metric/species filter, for the list header.

    Data Flow Contract:
      in:  queryset (already filtered), metric ('litter'|'plant'|'weed'|'participants'),
           species (exact label)
      out: int — sum of matching Metric.value for litter/plant/weed;
           sum of VisitLog.participant_count for participants; 0 when no filter
      side effects: none
    """
```

### Filter semantics (final)

- `metric`: `litter` → `metrics__metric_type__in=('litter_general','litter_recyclable')`; `plant`/`weed` → exact type; `participants` → `participant_count__gt=0`. All `.distinct()`.
- `species`: `metrics__label=species` (**exact**), composed with `metric` → `.distinct()`.
- `sort`: `-date` (default), `date`, `section` (→ `section__name`, nulls last), `-participant_count`.
- Existing `q`, `section`, `start_date`, `end_date`, `activity_type` unchanged.

### Total header (reconciliation UI)

When a `metric` filter is active, render a one-line summary above the list:
e.g. "Litter — 123 bags", "Participation — 45 people", "Plants — 12", "Weeds — 8"
(species-narrowed when `species` present). Computed from the **current** filtered
queryset, so adding date filters narrows the total accordingly; with no date
filter it reconciles exactly with the dashboard card.

## Updated File Map

| File | Change |
|------|--------|
| `core/services/visit_log_services.py` | **NEW** — `build_visit_log_queryset`, `visit_log_total` |
| `core/views.py` | `VisitLogListView.get_queryset` delegates to service; add `VisitLogExportView` (delegates too) |
| `core/urls.py` | Add `export/visit-logs/` |
| `core/templates/core/visit_log_list.html` | Metric/species filters, sort dropdown, total header, Export button (carries current query string) |
| `core/templates/core/dashboard.html` | Card "View source" links + species row links (`\|urlencode`) |
| `core/tests/` | Service unit tests + view filter/sort/export tests |

## Updated Test Plan (additions to the mandatory plan above)

- Service: `visit_log_total` returns the correct sum for each of the 4 metrics and the species-narrowed case.
- Service: `species` uses **exact** match (a log labeled "Olive" is NOT returned when filtering "Wild Olive").
- View: `sort=section` orders by section name with null sections last.
- View: total header reconciles with the dashboard card total (no date filter).

---

# Dashboard Metric Drill-Down Implementation Plan

**Goal:** Make every dashboard metric traceable — click a metric and see the VisitLogs that produced it, with a reconciling total header and filtered Excel export.

**Architecture:** Extract all VisitLog filtering/aggregation into a new service module (`core/services/visit_log_services.py`) consumed by both the list view and a new export view. Reuse the existing `visit_log_list` template for the drill-down, add "View source" affordances on the dashboard cards/species rows.

**Tech Stack:** Django 6.0 (class-based views), Django ORM, openpyxl, Tailwind templates, Django TestCase.

**UAT:** `tests/uat/dashboard_metric_drilldown_uat.md` — drafted before implementation.

> All commands run from the repo root with the virtualenv active
> (`venv/Scripts/activate` on Windows, or invoke `venv/Scripts/python.exe` directly).

## File Structure

- **Create:** `core/services/visit_log_services.py`
- **Create:** `core/tests/test_visit_log_filters.py`
- **Modify:** `core/views.py`, `core/urls.py`, `core/templates/core/visit_log_list.html`, `core/templates/core/dashboard.html`

## Risks (BUILD_PRINCIPLES)

- `core/views.py` is already 60KB (pre-existing, §8 violation). This feature keeps view methods thin by delegating to the service, but the file grows by ~40 lines (export view). Splitting `views.py` is a follow-up, not this PRD's scope.
- `VisitLogListView.get_context_data` is already > 20 lines (pre-existing, §5). We add a few context keys but keep the filter/aggregate logic in the service.

---

## Task 1: Service — `base_visit_log_queryset` (extract existing filters)

**Files:**
- Create: `core/services/visit_log_services.py`
- Test: `core/tests/test_visit_log_filters.py`

- [ ] **Step 1: Write the failing test**

```python
# core/tests/test_visit_log_filters.py
from datetime import date

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

from core.models import Section, VisitLog, Metric
from core.services.visit_log_services import (
    base_visit_log_queryset,
    build_visit_log_queryset,
    visit_log_total,
    metric_total_display,
)


class VisitLogServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(username='filters', password='password', email='f@example.com')
        self.client = Client()
        self.client.login(username='filters', password='password')

        self.alpha, _ = Section.objects.get_or_create(name='Alpha', defaults={'color_code': '#111111', 'current_stage': 'clearing'})
        self.beta, _ = Section.objects.get_or_create(name='Beta', defaults={'color_code': '#222222', 'current_stage': 'planting'})

        self.litter = VisitLog.objects.create(section=self.alpha, date=date(2026, 8, 1), participant_count=4, notes='litter note')
        Metric.objects.create(visit=self.litter, metric_type='litter_general', value=5)
        Metric.objects.create(visit=self.litter, metric_type='litter_recyclable', value=3)

        self.plant = VisitLog.objects.create(section=self.beta, date=date(2026, 8, 2), participant_count=2, notes='plant note')
        Metric.objects.create(visit=self.plant, metric_type='plant', label='Restio', value=10)

        self.plant_reed = VisitLog.objects.create(section=self.alpha, date=date(2026, 8, 3), participant_count=1, notes='reed note')
        Metric.objects.create(visit=self.plant_reed, metric_type='plant', label='Restio reed', value=7)

        self.weed = VisitLog.objects.create(section=self.beta, date=date(2026, 8, 4), participant_count=3, notes='weed note')
        Metric.objects.create(visit=self.weed, metric_type='weed', label='Wattle', value=15)

        self.zero = VisitLog.objects.create(section=None, date=date(2026, 8, 5), participant_count=0, notes='zero note')

    def test_base_section_filter(self):
        qs = base_visit_log_queryset({'section': str(self.alpha.id)})
        self.assertEqual(set(qs), {self.litter, self.plant_reed})

    def test_base_search_filter(self):
        qs = base_visit_log_queryset({'q': 'weed note'})
        self.assertEqual(set(qs), {self.weed})

    def test_base_activity_type_filter(self):
        qs = base_visit_log_queryset({'activity_type': 'planned'})
        # None of these fixtures have a Task, so planned => empty
        self.assertEqual(set(qs), set())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test core.tests.test_visit_log_filters -v 2`
Expected: FAIL — `ModuleNotFoundError: core.services.visit_log_services`

- [ ] **Step 3: Write `base_visit_log_queryset`**

```python
# core/services/visit_log_services.py
"""Shared filtering and aggregation for VisitLog list and export views."""
from datetime import datetime
from typing import Optional

from django.db.models import F, Q, QuerySet, Sum

from ..models import VisitLog


def base_visit_log_queryset(params: dict) -> QuerySet:
    """Apply search/section/date/activity-type filters and prefetch relations.

    Data Flow Contract:
      in:  params — request.GET-like mapping with optional keys
           q, section, start_date, end_date, activity_type
      out: QuerySet[VisitLog] with select_related('section','task') and
           prefetch_related('metrics','photos')
      side effects: none
    """
    queryset = VisitLog.objects.select_related('section', 'task').prefetch_related('metrics', 'photos')

    search_query = params.get('q')
    if search_query:
        queryset = queryset.filter(
            Q(notes__icontains=search_query)
            | Q(section__name__icontains=search_query)
            | Q(task__template__name__icontains=search_query)
        )

    section_id = params.get('section')
    if section_id:
        queryset = queryset.filter(section_id=section_id)

    start_date = params.get('start_date')
    if start_date:
        try:
            queryset = queryset.filter(date__gte=datetime.strptime(start_date, '%Y-%m-%d').date())
        except (ValueError, TypeError):
            pass

    end_date = params.get('end_date')
    if end_date:
        try:
            queryset = queryset.filter(date__lte=datetime.strptime(end_date, '%Y-%m-%d').date())
        except (ValueError, TypeError):
            pass

    activity_type = params.get('activity_type')
    if activity_type == 'planned':
        queryset = queryset.filter(task__isnull=False)
    elif activity_type == 'unplanned':
        queryset = queryset.filter(task__isnull=True)

    return queryset
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python manage.py test core.tests.test_visit_log_filters -v 2`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add core/services/visit_log_services.py core/tests/test_visit_log_filters.py
git commit -m "feat(visit-log): add base queryset service + tests"
```

---

## Task 2: Service — metric/species filters + sort in `build_visit_log_queryset`

**Files:**
- Modify: `core/services/visit_log_services.py`
- Test: `core/tests/test_visit_log_filters.py`

- [ ] **Step 1: Write the failing tests**

```python
# append to VisitLogServiceTests in core/tests/test_visit_log_filters.py
    def test_metric_litter_covers_both_types(self):
        self.assertEqual(set(build_visit_log_queryset({'metric': 'litter'})), {self.litter})

    def test_metric_plant(self):
        self.assertEqual(set(build_visit_log_queryset({'metric': 'plant'})), {self.plant, self.plant_reed})

    def test_metric_weed(self):
        self.assertEqual(set(build_visit_log_queryset({'metric': 'weed'})), {self.weed})

    def test_metric_participants_excludes_zero(self):
        self.assertEqual(set(build_visit_log_queryset({'metric': 'participants'})), {self.litter, self.plant, self.plant_reed, self.weed})

    def test_species_exact_match(self):
        qs = build_visit_log_queryset({'metric': 'plant', 'species': 'Restio'})
        self.assertEqual(set(qs), {self.plant})  # NOT plant_reed

    def test_sort_oldest(self):
        self.assertEqual(list(build_visit_log_queryset({'sort': 'date'}))[0], self.litter)

    def test_sort_section_null_last(self):
        names = [v.section.name if v.section else None for v in build_visit_log_queryset({'sort': 'section'})]
        self.assertEqual(names, ['Alpha', 'Alpha', 'Beta', 'Beta', None])

    def test_sort_participants_desc(self):
        self.assertEqual(list(build_visit_log_queryset({'sort': '-participant_count'}))[0], self.litter)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test core.tests.test_visit_log_filters -v 2`
Expected: FAIL — `AttributeError: build_visit_log_queryset` not defined

- [ ] **Step 3: Implement `build_visit_log_queryset`**

```python
# append to core/services/visit_log_services.py
_METRIC_TYPES = {
    'litter': ('litter_general', 'litter_recyclable'),
    'plant': ('plant',),
    'weed': ('weed',),
}


def build_visit_log_queryset(params: dict) -> QuerySet:
    """Build the full, sorted, de-duplicated VisitLog queryset for list/export.

    Data Flow Contract:
      in:  params — request.GET-like mapping with optional keys
           q, section, start_date, end_date, activity_type, metric, species, sort
      out: QuerySet[VisitLog] filtered, de-duplicated, ordered
      side effects: none
    """
    queryset = base_visit_log_queryset(params)

    metric = params.get('metric')
    if metric == 'participants':
        queryset = queryset.filter(participant_count__gt=0)
    elif metric in _METRIC_TYPES:
        queryset = queryset.filter(metrics__metric_type__in=_METRIC_TYPES[metric])

    species = params.get('species')
    if species:
        queryset = queryset.filter(metrics__label=species)

    if metric in _METRIC_TYPES or metric == 'participants' or species:
        queryset = queryset.distinct()

    sort = params.get('sort', '-date')
    if sort == 'date':
        queryset = queryset.order_by('date', '-created_at')
    elif sort == 'section':
        queryset = queryset.order_by(F('section__name').asc(nulls_last=True), '-date')
    elif sort == '-participant_count':
        queryset = queryset.order_by('-participant_count', '-date')
    else:
        queryset = queryset.order_by('-date', '-created_at')

    return queryset
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python manage.py test core.tests.test_visit_log_filters -v 2`
Expected: PASS (11 tests)

- [ ] **Step 5: Commit**

```bash
git add core/services/visit_log_services.py core/tests/test_visit_log_filters.py
git commit -m "feat(visit-log): metric/species/sort filters in service"
```

---

## Task 3: Service — `visit_log_total` + `metric_total_display`

**Files:**
- Modify: `core/services/visit_log_services.py`
- Test: `core/tests/test_visit_log_filters.py`

- [ ] **Step 1: Write the failing tests**

```python
# append to VisitLogServiceTests
    def test_total_litter(self):
        self.assertEqual(visit_log_total(base_visit_log_queryset({}), 'litter', None), 8)

    def test_total_plant(self):
        self.assertEqual(visit_log_total(base_visit_log_queryset({}), 'plant', None), 17)

    def test_total_plant_species(self):
        self.assertEqual(visit_log_total(base_visit_log_queryset({}), 'plant', 'Restio'), 10)

    def test_total_weed(self):
        self.assertEqual(visit_log_total(base_visit_log_queryset({}), 'weed', None), 15)

    def test_total_participants(self):
        self.assertEqual(visit_log_total(base_visit_log_queryset({}), 'participants', None), 10)

    def test_total_no_metric(self):
        self.assertEqual(visit_log_total(base_visit_log_queryset({}), None, None), 0)

    def test_metric_total_display(self):
        self.assertEqual(metric_total_display('litter', 8), 'Litter — 8 bags')
        self.assertEqual(metric_total_display('plant', 10, 'Restio'), 'Plants · Restio — 10')
        self.assertIsNone(metric_total_display(None, 0))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test core.tests.test_visit_log_filters -v 2`
Expected: FAIL — `ImportError: visit_log_total / metric_total_display`

- [ ] **Step 3: Implement `visit_log_total` + `metric_total_display`**

```python
# append to core/services/visit_log_services.py
METRIC_DISPLAY = {
    'litter': ('Litter', 'bags'),
    'participants': ('Participation', 'people'),
    'plant': ('Plants', ''),
    'weed': ('Weeds', ''),
}


def visit_log_total(queryset: QuerySet, metric: Optional[str] = None, species: Optional[str] = None) -> int:
    """Return the aggregate total for the active metric/species filter.

    Data Flow Contract:
      in:  queryset — base-filtered QuerySet[VisitLog] (from base_visit_log_queryset)
           metric — 'litter' | 'plant' | 'weed' | 'participants' | None
           species — exact Metric.label, or None
      out: int — sum of matching Metric.value for litter/plant/weed;
           sum of participant_count for participants; 0 when no metric
      side effects: none
    """
    if metric == 'litter':
        return queryset.filter(metrics__metric_type__in=('litter_general', 'litter_recyclable')).aggregate(total=Sum('metrics__value'))['total'] or 0
    if metric in ('plant', 'weed'):
        qs = queryset.filter(metrics__metric_type=metric)
        if species:
            qs = qs.filter(metrics__label=species)
        return qs.aggregate(total=Sum('metrics__value'))['total'] or 0
    if metric == 'participants':
        return queryset.aggregate(total=Sum('participant_count'))['total'] or 0
    return 0


def metric_total_display(metric: Optional[str], total: int, species: Optional[str] = None) -> Optional[str]:
    """Return the human summary line for the drill-down total header, or None.

    Data Flow Contract:
      in:  metric ('litter'|'plant'|'weed'|'participants'|None), total int, species str|None
      out: str like 'Litter — 8 bags' / 'Plants · Restio — 10', or None when no metric
      side effects: none
    """
    if not metric or metric not in METRIC_DISPLAY:
        return None
    label, unit = METRIC_DISPLAY[metric]
    if species:
        label = f'{label} · {species}'
    unit = f' {unit}' if unit else ''
    return f'{label} — {total}{unit}'
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python manage.py test core.tests.test_visit_log_filters -v 2`
Expected: PASS (18 tests)

- [ ] **Step 5: Commit**

```bash
git add core/services/visit_log_services.py core/tests/test_visit_log_filters.py
git commit -m "feat(visit-log): aggregate total + display helper"
```

---

## Task 4: Refactor `VisitLogListView` to delegate to the service

**Files:**
- Modify: `core/views.py`
- Test: `core/tests/test_visit_log_filters.py`

- [ ] **Step 1: Write the failing view tests**

```python
# append a new class to core/tests/test_visit_log_filters.py
class VisitLogListViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(username='listview', password='password', email='lv@example.com')
        self.client = Client()
        self.client.login(username='listview', password='password')
        self.section, _ = Section.objects.get_or_create(name='Gamma', defaults={'color_code': '#333333', 'current_stage': 'clearing'})
        v = VisitLog.objects.create(section=self.section, date=date(2026, 8, 1), participant_count=4)
        Metric.objects.create(visit=v, metric_type='litter_general', value=5)
        Metric.objects.create(visit=v, metric_type='litter_recyclable', value=3)

    def test_metric_filter_and_total_context(self):
        resp = self.client.get(reverse('visit_log_list'), {'metric': 'litter'})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['visit_log_total'], 8)
        self.assertEqual(resp.context['total_summary'], 'Litter — 8 bags')
        self.assertEqual(resp.context['selected_metric'], 'litter')
        self.assertEqual(resp.context['sort'], '-date')
        self.assertEqual(len(resp.context['visit_logs']), 1)

    def test_unfiltered_has_no_summary(self):
        resp = self.client.get(reverse('visit_log_list'))
        self.assertIsNone(resp.context['total_summary'])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test core.tests.test_visit_log_filters.VisitLogListViewTests -v 2`
Expected: FAIL — `KeyError: 'visit_log_total'` (context key missing)

- [ ] **Step 3: Rewrite the view methods**

Replace the existing `get_queryset` and `get_context_data` on `VisitLogListView` (around line 990) with:

```python
from .services.visit_log_services import (
    base_visit_log_queryset,
    build_visit_log_queryset,
    visit_log_total,
    metric_total_display,
)

class VisitLogListView(LoginRequiredMixin, ListView):
    """Master Activity Log - comprehensive view of all visit logs with search and filtering."""
    model = VisitLog
    template_name = 'core/visit_log_list.html'
    context_object_name = 'visit_logs'
    paginate_by = 25

    def get_queryset(self):
        return build_visit_log_queryset(self.request.GET)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        metric = self.request.GET.get('metric')
        species = self.request.GET.get('species')
        context['sections'] = Section.objects.all()
        context['search_query'] = self.request.GET.get('q', '')
        context['selected_section'] = self.request.GET.get('section', '')
        context['start_date'] = self.request.GET.get('start_date', '')
        context['end_date'] = self.request.GET.get('end_date', '')
        context['activity_type'] = self.request.GET.get('activity_type', '')
        context['selected_metric'] = metric or ''
        context['selected_species'] = species or ''
        context['sort'] = self.request.GET.get('sort', '-date')
        total = visit_log_total(base_visit_log_queryset(self.request.GET), metric, species)
        context['visit_log_total'] = total
        context['total_summary'] = metric_total_display(metric, total, species)

        query_params = self.request.GET.copy()
        if 'page' in query_params:
            del query_params['page']
        context['query_params'] = query_params.urlencode()
        return context
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python manage.py test core.tests.test_visit_log_filters core.tests.test_dashboard -v 2`
Expected: PASS (dashboard tests still green — no regression)

- [ ] **Step 5: Commit**

```bash
git add core/views.py core/tests/test_visit_log_filters.py
git commit -m "refactor(visit-log): delegate filtering to service"
```

---

## Task 5: `VisitLogExportView` + URL

**Files:**
- Modify: `core/views.py`, `core/urls.py`
- Test: `core/tests/test_visit_log_filters.py`

- [ ] **Step 1: Write the failing test**

```python
# append to core/tests/test_visit_log_filters.py
import io
import openpyxl

class VisitLogExportViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(username='export', password='password', email='ex@example.com')
        self.client = Client()
        self.client.login(username='export', password='password')
        self.section, _ = Section.objects.get_or_create(name='Delta', defaults={'color_code': '#444444', 'current_stage': 'clearing'})
        v1 = VisitLog.objects.create(section=self.section, date=date(2026, 8, 1), participant_count=4, notes='export litter')
        Metric.objects.create(visit=v1, metric_type='litter_general', value=5)
        Metric.objects.create(visit=v1, metric_type='litter_recyclable', value=3)
        v2 = VisitLog.objects.create(section=self.section, date=date(2026, 8, 2), participant_count=1, notes='export plant')
        Metric.objects.create(visit=v2, metric_type='plant', label='Restio', value=10)

    def test_export_respects_metric_filter(self):
        resp = self.client.get(reverse('visit_log_export'), {'metric': 'litter'})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        wb = openpyxl.load_workbook(io.BytesIO(resp.content))
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        self.assertEqual(rows[0][0], 'Date')
        self.assertEqual(rows[0][5], 'General Bags')
        self.assertEqual(len(rows) - 1, 1)  # only the litter log
        self.assertEqual(rows[1][5], 5)     # general bags
        self.assertEqual(rows[1][6], 3)     # recyclable bags
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test core.tests.test_visit_log_filters.VisitLogExportViewTests -v 2`
Expected: FAIL — `NoReverseMatch: 'visit_log_export'`

- [ ] **Step 3: Add URL**

```python
# core/urls.py — add after the data export lines
    path('export/visit-logs/', views.VisitLogExportView.as_view(), name='visit_log_export'),
```

- [ ] **Step 4: Implement the view**

```python
# append to core/views.py (near DataExportView)
class VisitLogExportView(LoginRequiredMixin, View):
    """Single-sheet Excel export of the filtered Master Activity Log."""

    def get(self, request, *args, **kwargs):
        queryset = build_visit_log_queryset(request.GET)

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = 'Visit Logs'

        headers = ['Date', 'Section', 'Task', 'Task Type', 'Participants',
                   'General Bags', 'Recyclable Bags', 'Plants', 'Weeds', 'Notes']
        ws.append(headers)
        header_font = Font(bold=True, color='FFFFFF')
        header_fill = PatternFill(start_color='166534', end_color='166534', fill_type='solid')
        for cell in ws[1]:
            cell.font = header_font
            cell.fill = header_fill

        for visit in queryset:
            metrics = list(visit.metrics.all())
            general = sum(m.value for m in metrics if m.metric_type == 'litter_general')
            recyclable = sum(m.value for m in metrics if m.metric_type == 'litter_recyclable')
            plants = '; '.join(f"{m.label or 'Unlabeled'}: {m.value}" for m in metrics if m.metric_type == 'plant')
            weeds = '; '.join(f"{m.label or 'Unlabeled'}: {m.value}" for m in metrics if m.metric_type == 'weed')
            task = visit.task
            task_name = task.template.name if (task and task.template) else 'Unplanned'
            task_type = task.template.task_type.name if (task and task.template and task.template.task_type) else ''
            ws.append([
                visit.date.isoformat(),
                visit.section.name if visit.section else 'General',
                task_name,
                task_type,
                visit.participant_count,
                general,
                recyclable,
                plants,
                weeds,
                visit.notes,
            ])

        for col in 'ABCDEFGHIJ':
            ws.column_dimensions[col].width = 20

        output = io.BytesIO()
        wb.save(output)
        filename = f"visit_logs_{timezone.now().strftime('%Y%m%d_%H%M')}.xlsx"
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response
```

Note: `Font` and `PatternFill` are already imported at the top of `views.py`; `io`, `openpyxl`, `HttpResponse`, `timezone`, `LoginRequiredMixin`, `View`, `build_visit_log_queryset` are already available. Add the `visit_log_services` import if not already added in Task 4.

- [ ] **Step 5: Run test to verify it passes**

Run: `python manage.py test core.tests.test_visit_log_filters.VisitLogExportViewTests -v 2`
Expected: PASS (1 test)

- [ ] **Step 6: Commit**

```bash
git add core/views.py core/urls.py core/tests/test_visit_log_filters.py
git commit -m "feat(visit-log): filtered Excel export endpoint"
```

---

## Task 6: Template — `visit_log_list.html` (metric/sort filters, total header, export button)

**Files:**
- Modify: `core/templates/core/visit_log_list.html`
- Test: `core/tests/test_visit_log_filters.py`

- [ ] **Step 1: Write the failing test**

```python
# append to VisitLogListViewTests in core/tests/test_visit_log_filters.py
    def test_template_shows_total_header_and_export(self):
        resp = self.client.get(reverse('visit_log_list'), {'metric': 'litter'})
        self.assertContains(resp, 'Litter — 8 bags')
        self.assertContains(resp, 'Export')
        self.assertContains(resp, reverse('visit_log_export'))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test core.tests.test_visit_log_filters.VisitLogListViewTests.test_template_shows_total_header_and_export -v 2`
Expected: FAIL — total header/export absent

- [ ] **Step 3: Add metric + sort controls to the filter form**

In the filter form's first grid (after the End Date field), add a Metric dropdown and Sort dropdown. In the action-buttons row, add an Export button.

```html
<!-- Metric filter (after End Date div in the first grid) -->
<div class="space-y-1.5">
    <label class="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Metric</label>
    <select name="metric" class="w-full py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all text-slate-800 dark:text-slate-200 outline-none">
        <option value="">All Metrics</option>
        <option value="litter" {% if selected_metric == 'litter' %}selected{% endif %}>Litter</option>
        <option value="plant" {% if selected_metric == 'plant' %}selected{% endif %}>Plants</option>
        <option value="weed" {% if selected_metric == 'weed' %}selected{% endif %}>Weeds</option>
        <option value="participants" {% if selected_metric == 'participants' %}selected{% endif %}>Participation</option>
    </select>
</div>

<!-- Sort dropdown (in the same grid) -->
<div class="space-y-1.5">
    <label class="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Sort</label>
    <select name="sort" class="w-full py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all text-slate-800 dark:text-slate-200 outline-none">
        <option value="-date" {% if sort == '-date' %}selected{% endif %}>Newest</option>
        <option value="date" {% if sort == 'date' %}selected{% endif %}>Oldest</option>
        <option value="section" {% if sort == 'section' %}selected{% endif %}>Section A–Z</option>
        <option value="-participant_count" {% if sort == '-participant_count' %}selected{% endif %}>Participants high→low</option>
    </select>
</div>
```

```html
<!-- Export button (next to Clear Filters / Apply Filters) -->
<a href="{% url 'visit_log_export' %}{% if query_params %}?{{ query_params }}{% endif %}" class="px-4 py-2 text-xs font-medium text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200 transition-colors flex items-center gap-2">
    <span class="material-symbols-outlined text-sm">download</span>
    Export
</a>
```

- [ ] **Step 4: Add the total header above the list**

In the "Results Count" row (or immediately above the list), add:

```html
{% if total_summary %}
<p class="text-sm font-semibold text-emerald-700 dark:text-emerald-400">{{ total_summary }}</p>
{% endif %}
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python manage.py test core.tests.test_visit_log_filters -v 2`
Expected: PASS (all tests)

- [ ] **Step 6: Commit**

```bash
git add core/templates/core/visit_log_list.html core/tests/test_visit_log_filters.py
git commit -m "feat(visit-log): metric/sort filters, total header, export button"
```

---

## Task 7: Template — `dashboard.html` (View source links + species rows)

**Files:**
- Modify: `core/templates/core/dashboard.html`
- Test: `core/tests/test_dashboard.py`

- [ ] **Step 1: Write the failing test**

```python
# append to DashboardTests in core/tests/test_dashboard.py
    def test_drilldown_links_present(self):
        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, reverse('visit_log_list') + '?metric=litter')
        self.assertContains(response, reverse('visit_log_list') + '?metric=participants')
        self.assertContains(response, reverse('visit_log_list') + '?metric=plant')
        self.assertContains(response, reverse('visit_log_list') + '?metric=weed')

    def test_species_row_link(self):
        v = VisitLog.objects.create(section=self.section1, date=timezone.now().date())
        Metric.objects.create(visit=v, metric_type='plant', label='Restio', value=10)
        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, '?metric=plant&amp;species=Restio')
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python manage.py test core.tests.test_dashboard.DashboardTests.test_drilldown_links_present -v 2`
Expected: FAIL — links absent

- [ ] **Step 3: Add "View source" links to each card header**

In each of the 4 stat cards, wrap the card label with a "View source" link. Example for Litter:

```html
<div class="flex justify-between items-start mb-4">
    <span class="p-2 bg-blue-50 dark:bg-blue-900/30 rounded-lg text-blue-600 dark:text-blue-400">
        <span class="material-symbols-outlined">delete</span>
    </span>
    <a href="{% url 'visit_log_list' %}?metric=litter" class="text-[10px] font-bold text-primary uppercase tracking-widest hover:underline">Litter Removed · View source</a>
</div>
```

Apply the same pattern with `metric=participants`, `metric=plant`, `metric=weed` on the other three cards.

- [ ] **Step 4: Make species rows clickable**

In the plant breakdown loop, wrap each species row in a link:

```html
<a href="{% url 'visit_log_list' %}?metric=plant&amp;species={{ species.label|urlencode }}" class="flex justify-between text-xs hover:text-primary">
    <span class="text-slate-600 dark:text-slate-400 truncate max-w-[70%]">{{ species.label }}</span>
    <span class="text-slate-900 dark:text-white font-semibold">{{ species.total }}</span>
</a>
```

Do the same in the weed breakdown loop with `metric=weed`.

- [ ] **Step 5: Run tests to verify they pass**

Run: `python manage.py test core.tests.test_dashboard -v 2`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add core/templates/core/dashboard.html core/tests/test_dashboard.py
git commit -m "feat(dashboard): metric card View source links + species row drill-down"
```

---

## Task 8: Full suite + final commit

- [ ] **Step 1: Run the full test suite**

Run: `python manage.py test core -v 2`
Expected: PASS (no regressions across all existing tests)

- [ ] **Step 2: Run UAT**

Reference `tests/uat/dashboard_metric_drilldown_uat.md`. Have the user walk through the 8 scenarios.

- [ ] **Step 3: Commit any final fixes + mark the PRD checklist**

```bash
git add -A
# Update the PRD pre-flight checklist: check "Tests written and passing"
git commit -m "test(visit-log): full suite green for metric drill-down"
```

- [ ] **Step 4: Update `product/backlog.md` / `progress_log.json`** (per maintaining-the-backlog skill) to record completion.
