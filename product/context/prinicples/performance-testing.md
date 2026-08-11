# Performance Regression Testing

## Quick Start

```bash
# Run all performance tests (use --reuse-db for speed after first run)
python -m pytest tests/performance/ --reuse-db -v

# Run only budget assertion tests (skip discovery)
python -m pytest tests/performance/ --reuse-db -v --ignore=tests/performance/test_discovery.py

# Run with stop-on-first-failure
python -m pytest tests/performance/ --reuse-db -x --tb=short
```

## What's Tested

| Test | Type | File |
|------|------|------|
| Discovery (Phase 0) | Measurement only, no assertions | `test_discovery.py` |
| Kanban board | Budget + N+1 growth | `test_dashboard.py` |
| Planner | Budget | `test_dashboard.py` |
| Finance dashboard | Budget (KNOWN issue, cap=95) | `test_dashboard.py` |
| Rapid Logger POST | Budget | `test_rapid_logger.py` |
| Cashbook | Budget | `test_cashbook.py` |
| Routine summary | Budget | `test_routines.py` |
| Task detail modal | Budget (KNOWN issue, cap=13) | `test_routines.py` |
| Entity list | Budget + N+1 growth | `test_list_views.py` |
| Inventory list | Budget (KNOWN issue, cap=13) | `test_list_views.py` |
| Invoice list | Budget + N+1 growth | `test_list_views.py` |

## Known Issues

Known over-budget endpoints are suppressed via `tests/performance/known_issues.py`.
Each has a cap (actual + 2) and a ticket to a fix PRD in `docs/product/02_refinement/`.

| Endpoint | Actual | Cap | Ticket |
|----------|--------|-----|--------|
| `/kanban/` | 13 | 15 | `perf-kanban-n1.md` |
| `/planner/` | 26 | 28 | `perf-planner-values.md` |
| `/finance/` | 88 | 95 | `perf-finance-dashboard.md` |
| `/inventory/` | 11 | 13 | `perf-inventory-n1.md` |
| `/tasks/<id>/detail/` | 11 | 13 | `perf-taskmodal-n1.md` |

## Budget Adjustment Process

When a feature legitimately needs more queries:

1. Developer discovers budget exceeded in test
2. Raises the budget AND documents why:
   ```
   Budget: 12 → 14 — added entity name display on kanban cards
   (1 extra prefetch + 1 FK join)
   ```
3. Reviewer sanity-checks: "Could this be done with one query?"
4. Budget change committed alongside feature

**Anti-pattern:** Don't raise budgets silently. Each raise signals a new DB interaction was added.

## Architecture

- `conftest.py` — `perf_client` (Django `Client`, not DRF `APIClient`), `assert_query_count`, `count_queries`
- `known_issues.py` — suppression dictionary for known N+1 problems
- Uses `CaptureQueriesContext` (Django built-in) — no extra dependencies
- All tests use `@pytest.mark.django_db` with PostgreSQL

## Troubleshooting

**"database 'test_homitini_db' does not exist":** The test DB was dropped mid-run.
Kill lingering connections and rerun:
```bash
python -c "
import psycopg
conn = psycopg.connect('host=localhost dbname=postgres user=homitini_user password=a_strong_password')
conn.autocommit = True
conn.execute(\"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'test_homitini_db'\")
conn.execute('DROP DATABASE IF EXISTS test_homitini_db')
conn.close()
"
```

**Migration errors (column already exists):** This is a pre-existing project migration
issue with `core_droneimageryoverlay.area`. Use `--reuse-db` to avoid fresh migration runs.
