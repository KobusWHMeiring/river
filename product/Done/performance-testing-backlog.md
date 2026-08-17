# Performance Regression Testing — River Backlog

> **Inspired by:** Homtini `tests/performance/` suite & Abseil Performance Hints  
> **Date:** 2026-08-11 (updated 2026-08-16)  
> **Goal:** Per-endpoint query budgets with CI enforcement, N+1 growth detection, and a documented budget-adjustment process  
> **Status:** ✅ BL-1→BL-5 + BL-7 done (Django `TestCase`, not pytest) · N+1 fixes applied · BL-6 deferred (no CI in repo)

---

## Homtini Approach → River Translation

Homtini's performance suite has 4 key concepts. Here's how they map:

| Homtini Concept | River Equivalent | Notes |
|---|---|---|
| `CaptureQueriesContext` (Django built-in) | Same — zero extra dependencies | Works with SQLite + PostgreSQL |
| Per-endpoint query budgets | Same — critical River endpoints below | Budgets will be lower (simpler app) |
| N+1 growth tests (vary data, assert query count stable) | Same — especially valuable for planners | Monthly planner with many tasks is the stress test |
| Known issues suppression + tickets | Same — `known_issues.py` + `product/refinement/` tickets | |
| `--reuse-db` for speed | Same | SQLite is already fast, but `--reuse-db` still helps |
| PostgreSQL test DB | SQLite in dev is fine; run against PostgreSQL in CI | SQLite query counting works identically |
| HTMX partial endpoints | N/A — River is full page loads | Simpler: fewer endpoints to test |

---

## Critical Endpoints (12 endpoints / 13 measurements)

Ordered by traffic × complexity × risk of N+1 regression. The Visit Log Create
endpoint is measured twice (GET and POST), giving 13 measurements across 12 URLs.

| # | Endpoint | View | Why Critical |
|---|----------|------|-------------|
| 1 | `/core/dashboard/` | `GlobalDashboardView` | Aggregates across all sections, stages, visit logs. Highest query risk. |
| 2 | `/core/planner/weekly/` | `WeeklyPlannerView` | 7-day grid × 3 assignee types × N sections. Historical N+1 hotspot. |
| 3 | `/core/planner/monthly/` | `MonthlyPlannerView` | 30-day grid × 3 assignee types × N sections. Highest data density. |
| 4 | `/core/daily-agenda/` | `DailyAgendaView` | Daily task list with section FK. Already fixed one N+1 here. |
| 5 | `/core/sections/` | `SectionListView` | Section list + Leaflet map with GeoJSON serialization. |
| 6 | `/core/sections/<pk>/` | `SectionDetailView` | Photos, stage history, visit logs for one section. |
| 7 | `/core/visit-logs/` | `VisitLogListView` | Master log with search/filter. Paginated but query-heavy. |
| 8 | `/core/visit-logs/create/` | `VisitLogCreateView` | Inline formsets (metrics + photos). POST budget matters for field use. |
| 9 | `/core/tasks/create/` | `TaskCreateView` | Modal form — called from planner cells. |
| 10 | `/core/templates/` | `TaskTemplateListView` | Template CRUD list. Simple, baseline test. |
| 11 | `/core/task-types/` | `TaskTypeListView` | Task type CRUD list. Simple, baseline test. |
| 12 | `/core/export/` | `DataExportView` | Multi-sheet Excel. Budget should assert no runaway queries, but raw count will be high. |

---

## Query Budgets (Measured)

Budgets below are the **measured baseline + headroom** from the Discovery run
(`core/tests/performance/test_discovery.py`), captured 2026-08-16 *after* the N+1
fixes below were applied. They are enforced by `core/tests/performance/test_budgets.py`.
Raise a budget only with a documented reason (see BL-7).

| # | Endpoint | Method | Budget | Notes |
|---|----------|--------|--------|-------|
| 1 | `/core/dashboard/` | GET | 17 | Many aggregate widgets — fixed count, not per-row. |
| 2 | `/core/planner/weekly/` | GET | 9 | Scales flat with task count (verify via BL-4). |
| 3 | `/core/planner/monthly/` | GET | 9 | Same shape as weekly over 30 days. |
| 4 | `/core/daily-agenda/` | GET | 5 | |
| 5 | `/core/sections/` | GET | 5 | `.select_related('status')` applied. |
| 6 | `/core/sections/<pk>/` | GET | 14 | Many widgets; fixed count. |
| 7 | `/core/visit-logs/` | GET | 6 | Paginated + prefetch. |
| 8 | `/core/visit-logs/create/` | GET | 8 | |
| 8b | `/core/visit-logs/create/` | POST | 9 | Form + metrics + photos save. |
| 9 | `/core/tasks/create/` | GET | 9 | Template dropdown `.select_related('task_type')` applied. |
| 10 | `/core/templates/` | GET | 5 | `.select_related('task_type')` applied. |
| 11 | `/core/task-types/` | GET | 5 | `Count('templates')` annotation applied. |
| 12 | `/core/export/` | GET | 45 | Multi-sheet Excel — inherently data-proportional; cap prevents runaway. |

---

## N+1 Fixes Applied (2026-08-16)

The Discovery run surfaced four N+1 hotspots. All fixed:

| Endpoint | Fix | Before → After |
|----------|-----|----------------|
| Section List | `SectionListView.get_queryset()` → `.select_related('status')` | 12 → 3 |
| Task Templates | `TaskTemplateListView.get_queryset()` → `.select_related('task_type')` | 19 → 3 |
| Task Types | `TaskTypeListView.get_queryset()` → `.annotate(template_count=Count('templates'))` + template uses `task_type.template_count` | 6 → 3 |
| Task Create | `TaskForm` template field queryset → `.select_related('task_type')` (fixes `__str__` N+1 in dropdown) | 23 → 7 |
| Weekly Planner | `WeeklyPlannerView.get_queryset()` → `.select_related('section', 'template')` (surfaced by BL-4 growth test) | 67 → 7 with 30 tasks |
| Daily Agenda | `DailyAgendaView.get_queryset()` → `.select_related('section')` + `.prefetch_related('visitlog_set')` (surfaced by BL-4 growth test) | 66 → 6 with 40 tasks |

---

## N+1 Growth Tests

For endpoints that scale with data volume, add a growth assertion: create N records, assert query count = baseline (not baseline + N).

| Endpoint | Growth Test | Create | Assert |
|----------|------------|--------|--------|
| Weekly Planner | Create 30 extra tasks across week | 30 | Query count unchanged |
| Monthly Planner | Create 60 extra tasks across month | 60 | Query count unchanged |
| Daily Agenda | Create 20 incomplete + 20 completed tasks (completed ones get a visit log) | 40 | Query count unchanged |
| Section List | Create 10 extra sections | 10 | Query count unchanged |
| Visit Log List | Create 50 extra visit logs (paginated, page 1) | 50 | Query count unchanged |
| Dashboard | Create 20 extra visit logs across sections | 20 | Query count unchanged (aggregates, not per-row) |

> **Implemented** (BL-4, 2026-08-16) as `core/tests/performance/test_n1_growth.py` — 6 tests,
> all passing. Surfaced and fixed two real N+1s: the Weekly Planner queried
> `section` and `template` per task (7 → 67 queries with 30 tasks) and the Daily
> Agenda queried `section` and the completed-task visit log per task (6 → 66 with
> 40 tasks); `select_related`/`prefetch_related` keep both flat.

---

## Implementation Plan (Backlog Items)

> **Note:** The actual implementation uses Django's unittest `TestCase` (via
> `manage.py test`), not pytest. Remaining items (BL-4+) should be written as
> `PerformanceTestCase` subclasses to match `core/tests/performance/base.py`.

### BL-1: Create Test Infrastructure (P0) — ✅ DONE

> **Implemented** (commit `75d3fd0`) as `core/tests/performance/base.py` — a Django
> `TestCase` base class (`PerformanceTestCase`) with an authenticated client,
> `count_queries()` and `assert_query_count()`. Uses unittest (via `manage.py test`),
> not the pytest fixtures sketched below (retained for reference only).

**File:** `core/tests/performance/conftest.py`

```python
import pytest
from django.test import Client, override_settings
from django.test.utils import CaptureQueriesContext
from django.db import connections, reset_queries

@pytest.fixture
def perf_client():
    """Django test client for performance testing."""
    return Client()

@pytest.fixture
def count_queries():
    """Context manager that returns query count."""
    class QueryCounter:
        def __enter__(self):
            self.ctx = CaptureQueriesContext(connections['default'])
            self.ctx.__enter__()
            return self
        def __exit__(self, *args):
            self.ctx.__exit__(*args)
        @property
        def count(self):
            return len(self.ctx.captured_queries)
    return QueryCounter

def assert_query_count(actual, budget, endpoint):
    """Assert query count is within budget, with helpful message."""
    assert actual <= budget, (
        f"{endpoint}: {actual} queries exceeds budget of {budget}. "
        f"Excess: {actual - budget}. "
        f"If this is intentional, raise the budget and document why."
    )
```

**Dependencies:** Zero. Uses Django's built-in `CaptureQueriesContext` (available since Django 1.3).

**Effort:** 15 minutes. Copy Homtini's `conftest.py`, strip PostgreSQL-specific parts.

---

### BL-2: Discovery Phase — Measure Current Query Counts (P0) — ✅ DONE

> **Implemented** as `core/tests/performance/test_discovery.py` (unittest). Ran
> 2026-08-16 — results captured in "Query Budgets (Measured)" and "N+1 Fixes Applied"
> above. No assertions; measurement only.

**File:** `core/tests/performance/test_discovery.py`

**Goal:** Measure actual query counts for all 12 endpoints with the current codebase. No assertions — purely measurement. Outputs a table for setting initial budgets.

```python
import pytest
from django.test import Client
from django.test.utils import CaptureQueriesContext
from django.db import connections

ENDPOINTS = [
    ('Dashboard', '/core/dashboard/'),
    ('Weekly Planner', '/core/planner/weekly/'),
    ('Monthly Planner', '/core/planner/monthly/'),
    ('Daily Agenda', '/core/daily-agenda/'),
    ('Section List', '/core/sections/'),
    # ... etc
]

@pytest.mark.django_db
def test_discovery(perf_client):
    """Discovery: measure current query counts. No assertions."""
    print("\n--- Query Count Discovery ---")
    for name, url in ENDPOINTS:
        with CaptureQueriesContext(connections['default']) as ctx:
            response = perf_client.get(url)
            assert response.status_code == 200, f"{name} returned {response.status_code}"
        print(f"  {name:25s} {url:40s} → {len(ctx.captured_queries):3d} queries")
    print("--- End Discovery ---")
```

**Effort:** 20 minutes. Run once, capture results, set budgets from actuals.

---

### BL-3: Budget Assertion Tests for All Endpoints (P0) — ✅ DONE

> **Implemented** as `core/tests/performance/test_budgets.py` (unittest). Budgets are
> the shared `BUDGETS` dict in `core/tests/performance/base.py`, enforced with
> `assert_query_count()`. One test per endpoint.

**File:** `core/tests/performance/test_budgets.py`

One test per endpoint. Uses `assert_query_count()` from conftest. Budgets filled in after Discovery (BL-2).

```python
@pytest.mark.django_db
def test_dashboard_query_budget(perf_client, count_queries):
    with count_queries() as counter:
        response = perf_client.get('/core/dashboard/')
        assert response.status_code == 200
    assert_query_count(counter.count, budget=8, endpoint='Dashboard')
```

**Effort:** 30 minutes for all 12 endpoints.

---

### BL-4: N+1 Growth Tests (P1) — ✅ DONE

> **Implemented** as `core/tests/performance/test_n1_growth.py` (unittest). Six
> `PerformanceTestCase` tests seed a baseline, bulk-create extra rows, and assert
> the query count stays flat via `assert_no_query_growth()` (added to `base.py`).
> This surfaced and fixed a Weekly Planner and a Daily Agenda N+1 (see "N+1 Fixes Applied").

**File:** `core/tests/performance/test_n1_growth.py`

Create bulk data, re-measure, assert query count stays flat.

```python
@pytest.mark.django_db
def test_weekly_planner_n1_growth(perf_client, count_queries):
    """Creating 30 more tasks should not increase query count."""
    # Measure baseline
    with count_queries() as counter:
        response = perf_client.get('/core/planner/weekly/')
    baseline = counter.count

    # Create 30 extra tasks
    from core.models import Task, Section, TaskTemplate
    section = Section.objects.first()
    template = TaskTemplate.objects.first()
    from datetime import date, timedelta
    today = date.today()
    tasks = [
        Task(date=today + timedelta(days=i % 7), section=section,
             assignee_type='team', instructions='Test',
             template=template)
        for i in range(30)
    ]
    Task.objects.bulk_create(tasks)

    # Re-measure
    with count_queries() as counter2:
        response = perf_client.get('/core/planner/weekly/')
    assert_query_count(counter2.count, budget=baseline, endpoint='Weekly Planner (N+1)')
```

**Effort:** 1–2 hours for 5 growth tests.

---

### BL-5: Known Issues Suppression (P1) — ✅ DONE

> Implemented as `core/tests/performance/known_issues.py` (`KNOWN_ISSUES` + `effective_cap()`), wired into `assert_endpoint_budget()` in `base.py` and used by `test_budgets.py`. Currently empty (no over-budget endpoints). See `docs/performance-budgets.md`.

**File:** `core/tests/performance/known_issues.py`

```python
# Endpoints with known over-budget query counts.
# Each entry has a cap (actual + 2) and a ticket reference.
# These are suppressed in CI until the ticket is resolved.

KNOWN_ISSUES = {
    '/core/export/': {
        'cap': 25,
        'ticket': 'product/refinement/perf-export-bulk.md',
        'note': 'Multi-sheet Excel generation. Will always be high.',
    },
    # Add entries as Discovery reveals over-budget endpoints
}
```

**Effort:** 10 minutes to create, then maintain as issues are found.

---

### BL-6: CI Integration (P1) — ⏸️ DEFERRED

> Deferred: there is no CI pipeline in the repo (and `lint.py` is an AI audit tool, not a test runner). Perf tests already run via `manage.py test`; revisit if/when CI is set up.

Add to CI pipeline (or `lint.py` pre-commit hook):

```bash
# Run performance tests (advisory mode — warn but don't fail)
python -m pytest core/tests/performance/ --reuse-db -v --tb=short

# Strict mode (fail on budget exceed) — for CI
python -m pytest core/tests/performance/ --reuse-db -v --tb=short -x
```

**Effort:** 15 minutes to add to CI config.

---

### BL-7: Budget Adjustment Documentation (P2) — ✅ DONE

> Implemented as `docs/performance-budgets.md` (also documents how to run the perf suite and the known-issues process).

Add to `DEVELOPER_HANDOVER.md` or create `docs/performance-budgets.md`:

```markdown
## Performance Budget Adjustment Process

1. Discover budget exceeded in test
2. Raise budget AND document:
   ```
   Budget: 10 → 12 — added task type icons to weekly planner cells
   (1 extra prefetch_related for task type icons)
   ```
3. Reviewer sanity-checks: "Could this be done with existing queries?"
4. Budget change committed alongside feature
```

**Effort:** 10 minutes.

---

## Total Effort Estimate

| Item | Effort | Priority | Status |
|------|--------|----------|--------|
| BL-1: Test infrastructure | 15 min | P0 | ✅ DONE |
| BL-2: Discovery run | 20 min | P0 | ✅ DONE |
| BL-3: Budget tests (12 endpoints) | 30 min | P0 | ✅ DONE |
| BL-4: N+1 growth tests (5 endpoints) | 1–2 hr | P1 | ✅ DONE |
| BL-5: Known issues suppression | 10 min | P1 | ✅ DONE |
| BL-6: CI integration | 15 min | P1 | ⏸️ DEFERRED (no CI) |
| BL-7: Budget adjustment docs | 10 min | P2 | ✅ DONE |
| **Remaining** | **0 minutes** | | |

---

## River-Specific Considerations

### SQLite vs PostgreSQL
`CaptureQueriesContext` counts queries the same way on both backends. The query *counts* will be identical. What differs is query *latency* — but that's not what we're measuring here. We're measuring N+1 risk (query count scales with data), which is backend-agnostic.

### No HTMX = Simpler
Homtini has to test HTMX partial endpoints (returning HTML fragments). River does full page loads. Fewer endpoints, less complexity. The budgets above assume standard Django CBV patterns.

### Auth
River uses Django Admin login (`/admin/login/`). Performance tests need an authenticated client.

> **Implemented:** `PerformanceTestCase` creates a superuser in `setUpClass` and logs in
> via `self.perf_client.login()` in `setUp`. The pytest fixture sketch below is retained
> for reference only.

```python
@pytest.fixture
def perf_client():
    from django.contrib.auth.models import User
    client = Client()
    User.objects.create_superuser('perftest', 'test@test.com', 'testpass')
    client.login(username='perftest', password='testpass')
    return client
```

### Test Data
River has 19 task templates, 8 sections, and fixtures. The test DB should be seeded with `loaddata` or by creating minimal fixtures in test setup. For Discovery, use the existing fixtures. For growth tests, create data in the test.

---

## What This Gives You

1. **Every commit is performance-gated.** A new feature adding an N+1 query fails CI.
2. **No silent degradations.** The Monthly Planner view won't slowly grow from 8 to 25 queries without anyone noticing.
3. **Data-driven refactoring.** The Discovery run tells you exactly which endpoints need `.select_related()` — you don't guess.
4. **Safe refactoring.** When you add `.select_related()` to a view, the budget test confirms the query count dropped.
5. **Documented tradeoffs.** The "known issues" file makes technical debt visible and tracked, not hidden.
