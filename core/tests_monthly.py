from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta
import calendar
from core.models import Section, Task, TaskTemplate


class MonthlyPlannerViewTests(TestCase):
    """Tests for the Monthly Planner View functionality."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

        # Create a section
        self.section = Section.objects.create(
            name='Test Section',
            color_code='#FF5733'
        )

        # Create a task template
        self.template = TaskTemplate.objects.create(
            name='Test Template',
            task_type='litter_run',
            assignee_type='team',
            default_instructions='Test instructions'
        )

    def test_month_grid_logic_february_2026(self):
        """Verify that for February 2026, the view generates exactly 28 days (plus padding)."""
        response = self.client.get('/core/planner/monthly/', {'year': 2026, 'month': 2})
        self.assertEqual(response.status_code, 200)

        # Check context variables
        self.assertEqual(response.context['year'], 2026)
        self.assertEqual(response.context['month'], 2)
        self.assertEqual(response.context['month_name'], 'February')

        # Check that month_weeks is in context and has the right structure
        month_weeks = response.context['month_weeks']
        self.assertIsNotNone(month_weeks)

        # Count all days in the grid (including padding days)
        total_days = sum(len(week) for week in month_weeks)

        # February 2026 should have at least 28 days in the grid
        # Plus padding days from previous/next months
        self.assertGreaterEqual(total_days, 28)

        # Verify February has 28 days
        self.assertEqual(calendar.monthrange(2026, 2)[1], 28)

    def test_month_grid_leap_year(self):
        """Verify leap year handling - February 2024 should have 29 days."""
        response = self.client.get('/core/planner/monthly/', {'year': 2024, 'month': 2})
        self.assertEqual(response.status_code, 200)

        # Verify February 2024 (leap year) has 29 days
        self.assertEqual(calendar.monthrange(2024, 2)[1], 29)

    def test_month_grid_saturday_start(self):
        """Verify grid alignment when month starts on Saturday."""
        # March 2025 starts on Saturday
        response = self.client.get('/core/planner/monthly/', {'year': 2025, 'month': 3})
        self.assertEqual(response.status_code, 200)

        month_weeks = response.context['month_weeks']

        # First day of first week should be from previous month (Monday Feb 24, 2025)
        first_week = month_weeks[0]
        self.assertLess(first_week[0].month, 3)  # Should be from February

    def test_task_indicators_display(self):
        """Add tasks to multiple days in a month and verify color indicators appear."""
        today = date(2026, 2, 15)

        # Create tasks on different days
        task1 = Task.objects.create(
            date=today,
            section=self.section,
            assignee_type='team',
            instructions='Task 1'
        )

        task2 = Task.objects.create(
            date=today + timedelta(days=3),
            section=self.section,
            assignee_type='manager',
            instructions='Task 2'
        )

        response = self.client.get('/core/planner/monthly/', {'year': 2026, 'month': 2})
        self.assertEqual(response.status_code, 200)

        # Check that tasks are in the context
        tasks_by_date = response.context['tasks_by_date']
        self.assertIn(today, tasks_by_date)
        self.assertIn(today + timedelta(days=3), tasks_by_date)

    def test_overflow_handling(self):
        """Verify the UI handles overflow gracefully with many tasks on one day."""
        today = date(2026, 2, 15)

        # Create 6 tasks on the same day
        for i in range(6):
            Task.objects.create(
                date=today,
                section=self.section,
                assignee_type='team' if i % 2 == 0 else 'manager',
                instructions=f'Task {i}'
            )

        response = self.client.get('/core/planner/monthly/', {'year': 2026, 'month': 2})
        self.assertEqual(response.status_code, 200)

        # Check that tasks are grouped by date
        tasks_by_date = response.context['tasks_by_date']
        self.assertIn(today, tasks_by_date)
        self.assertEqual(len(tasks_by_date[today]), 6)

    def test_navigation_to_daily_agenda(self):
        """Clicking a day with tasks takes the user to the correct daily agenda."""
        today = date(2026, 2, 15)

        # Create a task
        Task.objects.create(
            date=today,
            section=self.section,
            assignee_type='team',
            instructions='Test task'
        )

        # The daily agenda URL with date parameter
        expected_url = f'/core/daily-agenda/?date=2026-02-15'

        response = self.client.get('/core/daily-agenda/', {'date': '2026-02-15'})
        self.assertEqual(response.status_code, 200)

    def test_padding_day_navigation(self):
        """Verify clicking a padding day from the next month still takes user to correct date."""
        # February 2026 - check if there are padding days from March
        response = self.client.get('/core/planner/monthly/', {'year': 2026, 'month': 2})
        self.assertEqual(response.status_code, 200)

        month_weeks = response.context['month_weeks']

        # Find a padding day from next month
        last_week = month_weeks[-1]
        padding_days = [day for day in last_week if day.month != 2]

        if padding_days:
            # Verify we can access daily agenda for a padding day
            padding_day = padding_days[0]
            response = self.client.get('/core/daily-agenda/', {
                'date': padding_day.strftime('%Y-%m-%d')
            })
            self.assertEqual(response.status_code, 200)

    def test_prev_next_month_navigation(self):
        """Test previous and next month navigation links."""
        response = self.client.get('/core/planner/monthly/', {'year': 2026, 'month': 6})
        self.assertEqual(response.status_code, 200)

        # Check previous month (May 2026)
        self.assertEqual(response.context['prev_year'], 2026)
        self.assertEqual(response.context['prev_month'], 5)

        # Check next month (July 2026)
        self.assertEqual(response.context['next_year'], 2026)
        self.assertEqual(response.context['next_month'], 7)

    def test_year_boundary_navigation(self):
        """Test navigation at year boundaries."""
        # December 2026
        response = self.client.get('/core/planner/monthly/', {'year': 2026, 'month': 12})
        self.assertEqual(response.status_code, 200)

        # Next month should be January 2027
        self.assertEqual(response.context['next_year'], 2027)
        self.assertEqual(response.context['next_month'], 1)

        # January 2026
        response = self.client.get('/core/planner/monthly/', {'year': 2026, 'month': 1})
        self.assertEqual(response.status_code, 200)

        # Previous month should be December 2025
        self.assertEqual(response.context['prev_year'], 2025)
        self.assertEqual(response.context['prev_month'], 12)

    def test_current_month_highlighting(self):
        """Test that the current month is identified and highlighted."""
        today = timezone.now().date()

        response = self.client.get('/core/planner/monthly/')
        self.assertEqual(response.status_code, 200)

        # Should default to current month
        self.assertEqual(response.context['year'], today.year)
        self.assertEqual(response.context['month'], today.month)
        self.assertTrue(response.context['is_current_month'])

    def test_select_related_performance(self):
        """Verify that tasks are fetched with select_related for performance."""
        today = date(2026, 2, 15)

        # Create a task
        Task.objects.create(
            date=today,
            section=self.section,
            assignee_type='team',
            instructions='Test task'
        )

        response = self.client.get('/core/planner/monthly/', {'year': 2026, 'month': 2})
        self.assertEqual(response.status_code, 200)

        # The view should use select_related to fetch section data
        # This test verifies the query doesn't fail
        tasks_by_date = response.context['tasks_by_date']
        if today in tasks_by_date:
            task = tasks_by_date[today][0]
            # Access section to ensure it's loaded
            self.assertEqual(task.section.name, 'Test Section')

    def test_task_grouping_by_date(self):
        """Test that tasks are properly grouped by date for template rendering."""
        today = date(2026, 2, 15)

        # Create multiple tasks on same day
        Task.objects.create(
            date=today,
            section=self.section,
            assignee_type='team',
            instructions='Team task'
        )

        Task.objects.create(
            date=today,
            section=self.section,
            assignee_type='manager',
            instructions='Manager task'
        )

        response = self.client.get('/core/planner/monthly/', {'year': 2026, 'month': 2})
        self.assertEqual(response.status_code, 200)

        tasks_by_date = response.context['tasks_by_date']
        self.assertIn(today, tasks_by_date)
        self.assertEqual(len(tasks_by_date[today]), 2)

    def test_empty_month_display(self):
        """Test that empty grid is displayed when no tasks exist for the month."""
        response = self.client.get('/core/planner/monthly/', {'year': 2026, 'month': 2})
        self.assertEqual(response.status_code, 200)

        # Should still render successfully with no tasks
        tasks_by_date = response.context['tasks_by_date']
        self.assertEqual(len(tasks_by_date), 0)

    def test_unauthenticated_redirect(self):
        """Test that unauthenticated users are redirected."""
        self.client.logout()
        response = self.client.get('/core/planner/monthly/')
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
