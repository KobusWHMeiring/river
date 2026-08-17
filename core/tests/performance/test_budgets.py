"""
Budget assertion tests for the 12 critical endpoints.

Each endpoint must stay within its query budget (see BUDGETS in base.py).
Budgets are set from the discovery baseline (test_discovery.py) plus a small
headroom. A failure means a regression added queries — fix the regression
rather than silently raising the budget. If raising the budget is justified,
update BUDGETS and document why in
product/refinement/performance-testing-backlog.md.
"""

from django.urls import reverse

from core.models import Section

from .base import PerformanceTestCase


class BudgetTests(PerformanceTestCase):
    """Assert every critical endpoint stays within its query budget."""

    def setUp(self):
        super().setUp()
        # Guarantee a section exists for the Section Detail endpoint.
        self.section = Section.objects.first()
        if self.section is None:
            self.section = Section.objects.create(name='Budget Test Section', position=0)

    def _assert_get(self, name, url):
        with self.count_queries() as counter:
            response = self.perf_client.get(url)
            self.assertEqual(response.status_code, 200, f"{name} returned {response.status_code}")
        self.assert_endpoint_budget(counter['count'], name)

    def test_dashboard_budget(self):
        self._assert_get('Dashboard', reverse('dashboard'))

    def test_weekly_planner_budget(self):
        self._assert_get('Weekly Planner', reverse('weekly_planner'))

    def test_monthly_planner_budget(self):
        self._assert_get('Monthly Planner', reverse('monthly_planner'))

    def test_daily_agenda_budget(self):
        self._assert_get('Daily Agenda', reverse('daily_agenda'))

    def test_section_list_budget(self):
        self._assert_get('Section List', reverse('section_list'))

    def test_section_detail_budget(self):
        url = reverse('section_detail', kwargs={'pk': self.section.pk})
        self._assert_get('Section Detail', url)

    def test_visit_log_list_budget(self):
        self._assert_get('Visit Log List', reverse('visit_log_list'))

    def test_visit_log_create_get_budget(self):
        self._assert_get('Visit Log Create (GET)', reverse('visit_log_create'))

    def test_visit_log_create_post_budget(self):
        url = reverse('visit_log_create')
        post_data = {
            'date': '2026-08-16',
            'section': self.section.pk,
            'notes': 'budget test',
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
        with self.count_queries() as counter:
            response = self.perf_client.post(url, post_data)
            self.assertIn(
                response.status_code,
                [200, 302],
                f"Visit Log Create (POST) returned {response.status_code}",
            )
        self.assert_endpoint_budget(counter['count'], 'Visit Log Create (POST)')

    def test_task_create_budget(self):
        self._assert_get('Task Create', reverse('task_create'))

    def test_task_templates_budget(self):
        self._assert_get('Task Templates', reverse('task_template_list'))

    def test_task_types_budget(self):
        self._assert_get('Task Types', reverse('task_type_list'))

    def test_data_export_budget(self):
        self._assert_get('Data Export', reverse('data_export'))
