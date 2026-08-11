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
        """Context manager that yields query count after block executes."""
        with CaptureQueriesContext(connections['default']) as ctx:
            yield ctx
        # Access ctx.captured_queries after the context exits
        # but we return ctx so caller can check len(ctx.captured_queries)

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
