"""
Discovery phase: measure current query counts for all 12 critical endpoints.

Run once to capture baseline query counts. No assertions — purely measurement.
Output goes to stdout for capturing into the budget-setting phase.

Usage:
    python manage.py test core.tests.performance.test_discovery -v 2
"""

from django.test.utils import CaptureQueriesContext
from django.db import connections
from django.urls import reverse
from core.models import Section
from .base import PerformanceTestCase


class DiscoveryTests(PerformanceTestCase):
    """Measure current query counts. No budget assertions — measurement only."""

    def _measure(self, name, url, method='GET', data=None):
        """Hit an endpoint and return query count."""
        if method == 'GET':
            with CaptureQueriesContext(connections['default']) as ctx:
                response = self.perf_client.get(url)
                self.assertEqual(response.status_code, 200, f"{name} returned {response.status_code}")
            return len(ctx.captured_queries)
        elif method == 'POST':
            with CaptureQueriesContext(connections['default']) as ctx:
                response = self.perf_client.post(url, data)
                # POST may return 302 (redirect) on success
                self.assertIn(response.status_code, [200, 302], f"{name} returned {response.status_code}")
            return len(ctx.captured_queries)

    def test_discovery_all_endpoints(self):
        """Discovery: measure and print query counts for all 12 endpoints."""
        results = []

        # 1. Dashboard
        q = self._measure('Dashboard', reverse('dashboard'))
        results.append(('Dashboard', reverse('dashboard'), q))

        # 2. Weekly Planner
        q = self._measure('Weekly Planner', reverse('weekly_planner'))
        results.append(('Weekly Planner', reverse('weekly_planner'), q))

        # 3. Monthly Planner
        q = self._measure('Monthly Planner', reverse('monthly_planner'))
        results.append(('Monthly Planner', reverse('monthly_planner'), q))

        # 4. Daily Agenda
        q = self._measure('Daily Agenda', reverse('daily_agenda'))
        results.append(('Daily Agenda', reverse('daily_agenda'), q))

        # 5. Section List
        q = self._measure('Section List', reverse('section_list'))
        results.append(('Section List', reverse('section_list'), q))

        # 6. Section Detail (needs a real section PK)
        section = Section.objects.first()
        if section:
            url = reverse('section_detail', kwargs={'pk': section.pk})
            q = self._measure('Section Detail', url)
            results.append(('Section Detail', url, q))
        else:
            results.append(('Section Detail', 'SKIP (no sections)', 0))

        # 7. Visit Log List
        q = self._measure('Visit Log List', reverse('visit_log_list'))
        results.append(('Visit Log List', reverse('visit_log_list'), q))

        # 8. Visit Log Create (GET)
        q = self._measure('Visit Log Create (GET)', reverse('visit_log_create'))
        results.append(('Visit Log Create (GET)', reverse('visit_log_create'), q))

        # 8b. Visit Log Create (POST) — minimal valid submission
        post_data = {
            'date': '2026-08-11',
            'section': section.pk if section else '',
            'notes': 'perf test',
            'participant_count': '0',
            'metrics-TOTAL_FORMS': '2',
            'metrics-INITIAL_FORMS': '0',
            'metrics-MIN_NUM_FORMS': '0',
            'metrics-MAX_NUM_FORMS': '1000',
            'metrics-0-metric_type': 'litter_general',
            'metrics-0-label': 'General Litter',
            'metrics-0-value': '0',
            'metrics-1-metric_type': 'litter_recyclable',
            'metrics-1-label': 'Recyclable Litter',
            'metrics-1-value': '0',
            'photos-TOTAL_FORMS': '1',
            'photos-INITIAL_FORMS': '0',
            'photos-MIN_NUM_FORMS': '0',
            'photos-MAX_NUM_FORMS': '1000',
        }
        q = self._measure('Visit Log Create (POST)', reverse('visit_log_create'), method='POST', data=post_data)
        results.append(('Visit Log Create (POST)', reverse('visit_log_create'), q))

        # 9. Task Create
        q = self._measure('Task Create', reverse('task_create'))
        results.append(('Task Create', reverse('task_create'), q))

        # 10. Task Templates
        q = self._measure('Task Templates', reverse('task_template_list'))
        results.append(('Task Templates', reverse('task_template_list'), q))

        # 11. Task Types
        q = self._measure('Task Types', reverse('task_type_list'))
        results.append(('Task Types', reverse('task_type_list'), q))

        # 12. Data Export
        q = self._measure('Data Export', reverse('data_export'))
        results.append(('Data Export', reverse('data_export'), q))

        # Print results table
        print("\n" + "=" * 80)
        print("QUERY COUNT DISCOVERY — BASELINE")
        print("=" * 80)
        print(f"{'Endpoint':<28s} {'Queries':>8s}  {'Budget':>8s}  {'Status':>8s}")
        print("-" * 80)

        proposed_budgets = {
            'Dashboard': 8,
            'Weekly Planner': 10,
            'Monthly Planner': 10,
            'Daily Agenda': 6,
            'Section List': 5,
            'Section Detail': 8,
            'Visit Log List': 7,
            'Visit Log Create (GET)': 5,
            'Visit Log Create (POST)': 8,
            'Task Create': 4,
            'Task Templates': 3,
            'Task Types': 3,
            'Data Export': 20,
        }

        total_under = 0
        total_over = 0

        for name, url, count in results:
            budget = proposed_budgets.get(name, '?')
            if budget == '?':
                status = '—'
            elif count <= budget:
                status = '✅ OK'
                total_under += 1
            else:
                status = f'❌ +{count - budget}'
                total_over += 1
            print(f"{name:<28s} {count:>8d}  {str(budget):>8s}  {status:>8s}")

        print("-" * 80)
        print(f"Under budget: {total_under}  Over budget: {total_over}  "
              f"Total endpoints: {len(results)}")
        print("=" * 80)
        print("Run with -v 2 to see this output. Copy budgets above into test_budgets.py.")
        print("=" * 80 + "\n")

        # Discovery never fails — measurement only
        self.assertTrue(True)
