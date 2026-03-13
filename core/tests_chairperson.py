from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta
from core.models import Section, Task, TaskTemplate, TaskType

class ChairpersonRoleTests(TestCase):
    """Tests for the Chairperson role integration."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

        # Create a section
        self.section = Section.objects.create(
            name='Strategy Section',
            color_code='#FF00FF'
        )

        # Create a task type
        self.task_type = TaskType.objects.create(
            name='Strategy',
            code='strategy'
        )

    def test_chairperson_assignee_type(self):
        """Verify that a task can be created with chairperson assignee type."""
        task = Task.objects.create(
            date=timezone.now().date(),
            section=self.section,
            assignee_type='chairperson',
            instructions='Board meeting prep'
        )
        self.assertEqual(task.assignee_type, 'chairperson')
        self.assertEqual(str(task), f"{task.date} - Strategy Section - Chairperson")

    def test_chairperson_template(self):
        """Verify that task templates can be created for chairperson."""
        template = TaskTemplate.objects.create(
            name='Donor Relations',
            task_type=self.task_type,
            assignee_type='chairperson',
            default_instructions='Contact donors for annual fundraiser'
        )
        self.assertEqual(template.assignee_type, 'chairperson')

    def test_weekly_planner_chairperson_context(self):
        """Verify that WeeklyPlannerView includes chairperson templates in context."""
        TaskTemplate.objects.create(
            name='Chairperson Task',
            task_type=self.task_type,
            assignee_type='chairperson',
            default_instructions='Strategy work'
        )
        
        response = self.client.get('/core/planner/weekly/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('chairperson_task_templates', response.context)
        self.assertEqual(len(response.context['chairperson_task_templates']), 1)
        self.assertEqual(response.context['chairperson_task_templates'][0].name, 'Chairperson Task')

    def test_monthly_planner_chairperson_context(self):
        """Verify that MonthlyPlannerView includes chairperson templates in context."""
        TaskTemplate.objects.create(
            name='Chairperson Monthly Task',
            task_type=self.task_type,
            assignee_type='chairperson',
            default_instructions='Monthly strategy'
        )
        
        response = self.client.get('/core/planner/monthly/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('chairperson_task_templates', response.context)
        self.assertEqual(len(response.context['chairperson_task_templates']), 1)
        self.assertEqual(response.context['chairperson_task_templates'][0].name, 'Chairperson Monthly Task')

    def test_daily_agenda_chairperson_ordering(self):
        """Verify that chairperson tasks appear first in daily agenda due to 'c' coming before 'm' and 't'."""
        today = timezone.now().date()
        Task.objects.create(date=today, assignee_type='team', instructions='Team task')
        Task.objects.create(date=today, assignee_type='manager', instructions='Manager task')
        Task.objects.create(date=today, assignee_type='chairperson', instructions='Chairperson task')
        
        response = self.client.get(f'/core/daily-agenda/?date={today}')
        self.assertEqual(response.status_code, 200)
        tasks = response.context['tasks']
        self.assertEqual(tasks[0].assignee_type, 'chairperson')
        self.assertEqual(tasks[1].assignee_type, 'manager')
        self.assertEqual(tasks[2].assignee_type, 'team')
