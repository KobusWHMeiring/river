"""
Performance test infrastructure for query budget enforcement.

Uses Django's built-in CaptureQueriesContext — zero extra dependencies.
Works identically on SQLite (dev) and PostgreSQL (prod).
"""

from django.test import TestCase, Client, override_settings
from django.test.utils import CaptureQueriesContext
from django.db import connections
from django.contrib.auth.models import User
from contextlib import contextmanager


# Query budgets per endpoint. Budget = measured baseline + headroom.
# Measured 2026-08-16 (after N+1 fixes in views/forms). Raise only with
# justification documented in product/refinement/performance-testing-backlog.md.
BUDGETS = {
    'Dashboard': 17,
    'Weekly Planner': 9,
    'Monthly Planner': 9,
    'Daily Agenda': 5,
    'Section List': 5,
    'Section Detail': 14,
    'Visit Log List': 6,
    'Visit Log Create (GET)': 8,
    'Visit Log Create (POST)': 9,
    'Task Create': 9,
    'Task Templates': 5,
    'Task Types': 5,
    'Data Export': 45,
}


class PerformanceTestCase(TestCase):
    """Base class for performance tests. Provides authenticated client + query counting."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.perf_user = User.objects.create_superuser(
            username='perftest', password='testpass', email='perftest@example.com'
        )

    def setUp(self):
        self.perf_client = Client()
        self.perf_client.login(username='perftest', password='testpass')

    @contextmanager
    def count_queries(self):
        """Context manager that yields a counter dict whose 'count' key is
        populated with the number of queries after the measured block exits."""
        counter = {'count': 0}
        with CaptureQueriesContext(connections['default']) as ctx:
            yield counter
        counter['count'] = len(ctx.captured_queries)

    def assert_query_count(self, actual, budget, endpoint):
        """Assert query count is within budget, with a helpful failure message."""
        self.assertLessEqual(
            actual,
            budget,
            f"\n{endpoint}: {actual} queries exceeds budget of {budget}.\n"
            f"Excess: {actual - budget}.\n"
            f"If this is intentional, raise the budget in test_budgets.py "
            f"and document why in product/refinement/performance-testing-backlog.md."
        )

    def assert_no_query_growth(self, endpoint, before, after):
        """Assert adding data did not increase the query count (N+1 guard)."""
        self.assertLessEqual(
            after,
            before,
            f"\n{endpoint}: query count grew from {before} to {after} after adding data.\n"
            f"This is an N+1 regression — fix the view's queryset "
            f"(select_related/prefetch_related) rather than weakening this assertion."
        )
