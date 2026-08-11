# Performance Regression Testing — River Backlog

> **Inspired by:** Homtini `tests/performance/` suite & Abseil Performance Hints  
> **Date:** 2026-08-11  
> **Goal:** Per-endpoint query budgets with CI enforcement, N+1 growth detection, and a documented budget-adjustment process

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

## Critical Endpoints (12)

Ordered by traffic × complexity × risk of N+1 regression:

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

## Proposed Query Budgets

These are **initial estimates** based on codebase knowledge. Discovery runs will refine them.  
Budgets assume proper `.select_related()` is in place. If not, Discovery will reveal the real numbers.

| # | Endpoint | Method | Est. Budget | Notes |
|---|----------|--------|-------------|-------|
| 1 | `/core/dashboard/` | GET | 8 | 1× sections + 1× visit_logs + 1× metrics agg + 1× tasks + 1× stage dist + 3× misc |
| 2 | `/core/planner/weekly/` | GET | 10 | 1× week tasks + 1× sections (FK) + 1× templates + 1× task types + session/auth queries |
| 3 | `/core/planner/monthly/` | GET | 10 | Same shape as weekly, but over 30-day range. Should scale without extra queries. |
| 4 | `/core/daily-agenda/` | GET | 6 | 1× day tasks + 1× sections (FK) + session/auth |
| 5 | `/core/sections/` | GET | 5 | 1× sections + 1× statuses (FK) + session/auth |
| 6 | `/core/sections/<pk>/` | GET | 8 | 1× section + 1× visit_logs + 1× photos + 1× stage_history + 1× status |
| 7 | `/core/visit-logs/` | GET | 7 | 1× visit_logs (paginated) + 1× sections + 1× tasks + 1× metrics (prefetch) + session/auth |
| 8 | `/core/visit-logs/create/` | GET | 5 | 1× task (if ?task=) + 1× sections + 1× templates + session/auth |
| 8b | `/core/visit-logs/create/` | POST | 8 | Form save + metrics save + photos save. atomic block should batch. |
| 9 | `/core/tasks/create/` | GET | 4 | 1× sections + 1× templates + session/auth |
| 10 | `/core/templates/` | GET | 3 | 1× templates + session/auth |
| 11 | `/core/task-types/` | GET | 3 | 1× task_types + session/auth |
| 12 | `/core/export/` | GET | 20 | Multi-sheet. High count is acceptable — just prevent runaway. |

---

## N+1 Growth Tests

For endpoints that scale with data volume, add a growth assertion: create N records, assert query count = baseline (not baseline + N).

| Endpoint | Growth Test | Create | Assert |
|----------|------------|--------|--------|
| Weekly Planner | Create 30 extra tasks across week | 30 | Query count unchanged |
| Monthly Planner | Create 60 extra tasks across month | 60 | Query count unchanged |
| Section List | Create 10 extra sections | 10 | Query count unchanged |
| Visit Log List | Create 50 extra visit logs (paginated, page 1) | 50 | Query count unchanged |
| Dashboard | Create 20 extra visit logs across sections | 20 | Query count unchanged (aggregates, not per-row) |

---

## Implementation Plan (Backlog Items)

### BL-1: Create Test Infrastructure (P0 — prerequisite)

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

### BL-2: Discovery Phase — Measure Current Query Counts (P0)

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

### BL-3: Budget Assertion Tests for All Endpoints (P0)

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

### BL-4: N+1 Growth Tests (P1)

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

### BL-5: Known Issues Suppression (P1)

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

### BL-6: CI Integration (P1)

Add to CI pipeline (or `lint.py` pre-commit hook):

```bash
# Run performance tests (advisory mode — warn but don't fail)
python -m pytest core/tests/performance/ --reuse-db -v --tb=short

# Strict mode (fail on budget exceed) — for CI
python -m pytest core/tests/performance/ --reuse-db -v --tb=short -x
```

**Effort:** 15 minutes to add to CI config.

---

### BL-7: Budget Adjustment Documentation (P2)

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

| Item | Effort | Priority |
|------|--------|----------|
| BL-1: conftest.py infrastructure | 15 min | P0 |
| BL-2: Discovery run | 20 min | P0 |
| BL-3: Budget tests (12 endpoints) | 30 min | P0 |
| BL-4: N+1 growth tests (5 endpoints) | 1–2 hr | P1 |
| BL-5: Known issues suppression | 10 min | P1 |
| BL-6: CI integration | 15 min | P1 |
| BL-7: Budget adjustment docs | 10 min | P2 |
| **Total** | **~3–4 hours** | |

---

## River-Specific Considerations

### SQLite vs PostgreSQL
`CaptureQueriesContext` counts queries the same way on both backends. The query *counts* will be identical. What differs is query *latency* — but that's not what we're measuring here. We're measuring N+1 risk (query count scales with data), which is backend-agnostic.

### No HTMX = Simpler
Homtini has to test HTMX partial endpoints (returning HTML fragments). River does full page loads. Fewer endpoints, less complexity. The budgets above assume standard Django CBV patterns.

### Auth
River uses Django Admin login (`/admin/login/`). Performance tests need an authenticated client. Add a `perf_client` fixture that logs in:

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
