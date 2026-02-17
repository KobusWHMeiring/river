from django.test import TestCase, RequestFactory
from django.utils import timezone
from core.models import Task, Section
from core.views import DailyAgendaView
from datetime import date

class DailyAgendaViewTests(TestCase):
    def setUp(self):
        self.section = Section.objects.create(
            name='Test Section',
            color_code='#FF0000',
            current_stage='clearing'
        )
        
    def test_returns_all_tasks_for_date(self):
        # Create tasks for today
        today = date.today()
        team_task = Task.objects.create(
            date=today,
            assignee_type='team',
            instructions='Team task',
            section=self.section
        )
        manager_task = Task.objects.create(
            date=today,
            assignee_type='manager',
            instructions='Manager task',
            section=self.section
        )
        
        # Create task for different date (should not appear)
        tomorrow = today.replace(day=today.day + 1)
        Task.objects.create(
            date=tomorrow,
            assignee_type='team',
            instructions='Tomorrow task',
            section=self.section
        )
        
        # Get view queryset
        factory = RequestFactory()
        request = factory.get(f'/daily-agenda/?date={today}')
        request.user = type('User', (), {'is_authenticated': True})()
        
        view = DailyAgendaView()
        view.request = request
        view.kwargs = {}
        
        queryset = view.get_queryset()
        
        # Should return 2 tasks for today
        self.assertEqual(queryset.count(), 2)
        self.assertIn(team_task, queryset)
        self.assertIn(manager_task, queryset)
        
    def test_ordering(self):
        today = date.today()
        # Create tasks in mixed order
        task2 = Task.objects.create(
            date=today,
            assignee_type='manager',
            instructions='Manager task',
            section=self.section
        )
        task1 = Task.objects.create(
            date=today,
            assignee_type='team',
            instructions='Team task A',
            section=self.section
        )
        task3 = Task.objects.create(
            date=today,
            assignee_type='team',
            instructions='Team task B',
            section=None  # No section
        )
        
        view = DailyAgendaView()
        view.request = RequestFactory().get(f'/daily-agenda/?date={today}')
        view.request.user = type('User', (), {'is_authenticated': True})()
        view.kwargs = {}
        
        queryset = view.get_queryset()
        tasks = list(queryset)
        
        # Should order by assignee_type (manager first), then section__name
        # manager task first
        self.assertEqual(tasks[0].assignee_type, 'manager')
        # team tasks next, ordered by section name (nulls last)
        self.assertEqual(tasks[1].section, self.section)
        self.assertEqual(tasks[2].section, None)
