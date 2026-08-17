# Performance Query Budgets

Query-count budgets catch N+1 regressions before they ship. Every critical
endpoint has a budget (measured baseline + headroom) enforced by
`core/tests/performance/test_budgets.py`.

## Running the suite

```bash
# Full suite (includes the performance tests)
python manage.py test

# Performance tests only
python manage.py test core.tests.performance

# Discovery — measure current counts, no assertions
python manage.py test core.tests.performance.test_discovery -v 2
```

Budgets are enforced by the normal `manage.py test` run. There is no separate
CI pipeline — the local suite is the gate.

## Budgets

Defined in `core/tests/performance/base.py` as the `BUDGETS` dict, keyed by
endpoint name (e.g. `'Dashboard'`, `'Weekly Planner'`, `'Data Export'`). Each
value is the measured baseline + headroom, captured 2026-08-16 after the N+1
fixes (see `product/refinement/performance-testing-backlog.md`).

## Budget-adjustment process

When a budget test fails, do **not** silently raise the number:

1. **Investigate first.** Is the extra query avoidable? Usually it's a missing
   `select_related`/`prefetch_related` or a `.count()` in a template loop.
   Fix that rather than raising the budget.
2. **If unavoidable**, raise the budget in `base.py` and document why in the
   same commit:

   ```
   Budget: 10 → 12 — added task-type icons to weekly planner cells
   (one extra prefetch_related for task-type icons)
   ```

3. **Reviewer sanity check:** "Could this be done with existing queries?"

## Known-issues suppression

For an endpoint that legitimately exceeds its baseline and cannot be optimized
away, add an entry to `core/tests/performance/known_issues.py` instead of
raising the budget. The endpoint gets a higher tolerated cap while the ticket
is open, and the test still fails if it blows past that cap.

```python
KNOWN_ISSUES = {
    'Data Export': {
        'cap': 60,
        'ticket': 'product/refinement/perf-export-bulk.md',
        'note': 'Multi-sheet Excel; raw count is data-proportional.',
    },
}
```

The key must match a `BUDGETS` key. `effective_cap()` (same module) resolves an
endpoint to `(cap, issue)`, and `PerformanceTestCase.assert_endpoint_budget()`
consults it.

## What the budgets guard against

- **Budget tests** (`test_budgets.py`) — absolute per-endpoint query ceilings.
- **N+1 growth tests** (`test_n1_growth.py`) — query count must stay flat as
  data volume grows (the real N+1 guard).
- **Known-issues** (`known_issues.py`) — tracked, tolerated overages.
