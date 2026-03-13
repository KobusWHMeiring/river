from django.test import TestCase, RequestFactory
from datetime import date, timedelta
from core.models import Task, Section
from core.views import DailyAgendaView

class DailyAgendaViewTests(TestCase):
    def setUp(self):
        self.section = Section.objects.create(
            name='Test Section A', # Renamed for clarity in ordering
            color_code='#FF0000',
            current_stage='clearing'
        )
        self.section_b = Section.objects.create( # Another section for ordering
            name='Test Section B',
            color_code='#0000FF',
            current_stage='planting'
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
        tomorrow = today + timedelta(days=1) # Use timedelta for date arithmetic
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
        # Create tasks in mixed order, ensuring predictable sorting
        task_team_none = Task.objects.create( # team, None
            date=today,
            assignee_type='team',
            instructions='Team task C',
            section=None
        )
        task_manager_b = Task.objects.create( # manager, Section B
            date=today,
            assignee_type='manager',
            instructions='Manager task B',
            section=self.section_b
        )
        task_team_a = Task.objects.create( # team, Section A
            date=today,
            assignee_type='team',
            instructions='Team task A',
            section=self.section
        )
        task_manager_a = Task.objects.create( # manager, Section A
            date=today,
            assignee_type='manager',
            instructions='Manager task A',
            section=self.section
        )
        
        view = DailyAgendaView()
        view.request = RequestFactory().get(f'/daily-agenda/?date={today}')
        view.request.user = type('User', (), {'is_authenticated': True})()
        view.kwargs = {}
        
        queryset = view.get_queryset()
        tasks = list(queryset)
        
        # Expected order (assignee_type ASC, section__name ASC - NULLS FIRST for SQLite/Postgres default)
        # 1. Manager tasks (by section name)
        # 2. Team tasks (by section name, None first)
        self.assertEqual(len(tasks), 4)

        # Manager tasks first, then sorted by section name
        self.assertEqual(tasks[0], task_manager_a)
        self.assertEqual(tasks[1], task_manager_b)
        
        # Team tasks next, sorted by section name (None first, then Section A)
        self.assertEqual(tasks[2], task_team_none) # None is sorted before 'Test Section A'
        self.assertEqual(tasks[3], task_team_a)
