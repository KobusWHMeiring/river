"""
N+1 growth tests (BL-4).

Verify that data-proportional endpoints stay flat: adding more rows must NOT add
more queries. Each test seeds a small baseline (so the fixed "empty → non-empty"
cost is already paid), measures the baseline query count, bulk-creates N extra
records, re-measures, and asserts the count did not grow.

If a test fails, the view has an N+1 query. Fix the view's get_queryset()
(e.g. add select_related/prefetch_related) rather than weakening the assertion.
"""

import calendar
from datetime import date, timedelta

from django.urls import reverse
from django.utils import timezone

from core.models import Section, Task, TaskTemplate, TaskType, VisitLog

from .base import PerformanceTestCase


class NPlusOneGrowthTests(PerformanceTestCase):
    """Query counts must stay flat as data volume grows."""

    def setUp(self):
        super().setUp()
        self.today = timezone.now().date()
        self.monday = self.today - timedelta(days=self.today.weekday())
        self.section = Section.objects.create(name='Growth Test Section', position=0)
        self.task_type = TaskType.objects.create(name='Growth Type', code='growth')
        self.template = TaskTemplate.objects.create(
            name='Growth Template',
            task_type=self.task_type,
            default_instructions='Growth',
            assignee_type='team',
        )

    def _get_count(self, url):
        with self.count_queries() as counter:
            response = self.perf_client.get(url)
            self.assertEqual(response.status_code, 200, f"{url} returned {response.status_code}")
        return counter['count']

    def _task(self, day, instructions):
        return Task(
            date=day,
            section=self.section,
            assignee_type='team',
            instructions=instructions,
            template=self.template,
        )

    def test_weekly_planner_no_n1_growth(self):
        url = reverse('weekly_planner')
        Task.objects.bulk_create([self._task(self.monday, 'baseline')])
        before = self._get_count(url)

        Task.objects.bulk_create([
            self._task(self.monday + timedelta(days=i % 7), f'Growth task {i}')
            for i in range(30)
        ])

        after = self._get_count(url)
        self.assert_no_query_growth('Weekly Planner', before, after)

    def test_monthly_planner_no_n1_growth(self):
        url = reverse('monthly_planner')
        Task.objects.bulk_create([
            self._task(date(self.today.year, self.today.month, 1), 'baseline')
        ])
        before = self._get_count(url)

        days_in_month = calendar.monthrange(self.today.year, self.today.month)[1]
        Task.objects.bulk_create([
            self._task(date(self.today.year, self.today.month, (i % days_in_month) + 1), f'Growth month {i}')
            for i in range(60)
        ])

        after = self._get_count(url)
        self.assert_no_query_growth('Monthly Planner', before, after)

    def test_daily_agenda_no_n1_growth(self):
        url = reverse('daily_agenda')
        # Baseline: one incomplete + one completed task (with a visit log).
        Task.objects.create(
            date=self.today, section=self.section, assignee_type='team',
            instructions='baseline incomplete', template=self.template,
        )
        completed = Task.objects.create(
            date=self.today, section=self.section, assignee_type='team',
            instructions='baseline completed', template=self.template, is_completed=True,
        )
        VisitLog.objects.create(task=completed, section=self.section, date=self.today, notes='baseline log')
        before = self._get_count(url)

        # 20 incomplete + 20 completed tasks (each completed task gets a visit log).
        Task.objects.bulk_create([
            self._task(self.today, f'growth incomplete {i}')
            for i in range(20)
        ])
        for i in range(20):
            t = Task.objects.create(
                date=self.today, section=self.section, assignee_type='team',
                instructions=f'growth completed {i}', template=self.template, is_completed=True,
            )
            VisitLog.objects.create(task=t, section=self.section, date=self.today, notes=f'growth log {i}')

        after = self._get_count(url)
        self.assert_no_query_growth('Daily Agenda', before, after)

    def test_section_list_no_n1_growth(self):
        url = reverse('section_list')
        before = self._get_count(url)

        Section.objects.bulk_create([
            Section(name=f'Growth Section {i}', position=i + 1)
            for i in range(10)
        ])

        after = self._get_count(url)
        self.assert_no_query_growth('Section List', before, after)

    def test_visit_log_list_no_n1_growth(self):
        url = reverse('visit_log_list')
        VisitLog.objects.bulk_create([
            VisitLog(section=self.section, date=self.today, notes=f'Baseline log {i}')
            for i in range(5)
        ])
        before = self._get_count(url)

        VisitLog.objects.bulk_create([
            VisitLog(section=self.section, date=self.today, notes=f'Growth log {i}')
            for i in range(50)
        ])

        after = self._get_count(url)
        self.assert_no_query_growth('Visit Log List', before, after)

    def test_dashboard_no_n1_growth(self):
        url = reverse('dashboard')
        VisitLog.objects.bulk_create([
            VisitLog(section=self.section, date=self.today, notes='Baseline dash')
        ])
        before = self._get_count(url)

        # 20 logs across the last 20 days — all within the 30-day active window.
        VisitLog.objects.bulk_create([
            VisitLog(section=self.section, date=self.today - timedelta(days=i), notes=f'Dash {i}')
            for i in range(20)
        ])

        after = self._get_count(url)
        self.assert_no_query_growth('Dashboard', before, after)
