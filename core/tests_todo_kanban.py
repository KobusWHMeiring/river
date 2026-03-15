from django.test import TestCase, Client
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.utils import timezone
from core.models import Task, Section, TaskTemplate, TaskType
from core.services.task_services import move_todo_task
import json

class TodoKanbanTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create a test user or use admin if needed
        from django.contrib.auth.models import User
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client.login(username='testuser', password='password')
        
        self.section = Section.objects.create(name="Test Section")
        self.task_type = TaskType.objects.create(name="Test Type", code="test")
        self.template = TaskTemplate.objects.create(
            name="Test Template", 
            task_type=self.task_type,
            default_instructions="Test instructions"
        )

    def test_task_model_validation(self):
        """Test that date is required for non-rolling tasks but optional for rolling tasks."""
        # Rolling task - no date should be fine
        task1 = Task(
            instructions="Rolling task",
            is_rolling=True,
            todo_status='todo'
        )
        task1.full_clean()  # Should not raise
        task1.save()
        
        # Non-rolling task - no date should raise ValidationError
        task2 = Task(
            instructions="Non-rolling task",
            is_rolling=False
        )
        with self.assertRaises(ValidationError):
            task2.full_clean()

    def test_kanban_view_status_grouping(self):
        """Test that tasks are grouped correctly by status in the Kanban view."""
        Task.objects.create(instructions="Todo 1", is_rolling=True, todo_status='todo', todo_position=0)
        Task.objects.create(instructions="Doing 1", is_rolling=True, todo_status='doing', todo_position=0)
        Task.objects.create(instructions="Done 1", is_rolling=True, todo_status='done', todo_position=0)
        Task.objects.create(instructions="Done 2", is_rolling=True, todo_status='done', todo_position=1)
        
        response = self.client.get(reverse('todo_kanban'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['todo_tasks']), 1)
        self.assertEqual(len(response.context['doing_tasks']), 1)
        self.assertEqual(len(response.context['done_tasks']), 2)

    def test_move_todo_task_service(self):
        """Test the move_todo_task service logic for re-indexing."""
        t1 = Task.objects.create(instructions="Task 1", is_rolling=True, todo_status='todo', todo_position=0)
        t2 = Task.objects.create(instructions="Task 2", is_rolling=True, todo_status='todo', todo_position=1)
        t3 = Task.objects.create(instructions="Task 3", is_rolling=True, todo_status='todo', todo_position=2)
        
        # Move Task 3 to position 0
        move_todo_task(t3.id, 'todo', 0)
        
        t1.refresh_from_db()
        t2.refresh_from_db()
        t3.refresh_from_db()
        
        self.assertEqual(t3.todo_position, 0)
        self.assertEqual(t1.todo_position, 1)
        self.assertEqual(t2.todo_position, 2)
        
        # Move Task 1 to 'doing'
        move_todo_task(t1.id, 'doing', 0)
        t1.refresh_from_db()
        self.assertEqual(t1.todo_status, 'doing')
        self.assertEqual(t1.todo_position, 0)
        
        # Check remaining tasks in 'todo'
        t3.refresh_from_db()
        t2.refresh_from_db()
        self.assertEqual(t3.todo_position, 0)
        self.assertEqual(t2.todo_position, 1)

    def test_todo_update_api(self):
        """Test the AJAX API endpoint for Kanban updates."""
        task = Task.objects.create(instructions="API Task", is_rolling=True, todo_status='todo', todo_position=0)
        
        url = reverse('todo_update')
        data = {
            'task_id': task.id,
            'status': 'doing',
            'index': 0
        }
        
        response = self.client.post(
            url, 
            data=json.dumps(data), 
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        task.refresh_from_db()
        self.assertEqual(task.todo_status, 'doing')

    def test_exclusions_from_planners(self):
        """Test that rolling tasks are excluded from operational views."""
        # Create one rolling and one scheduled task
        Task.objects.create(instructions="Rolling", is_rolling=True)
        Task.objects.create(instructions="Scheduled", date=timezone.now().date(), is_rolling=False)
        
        # Check Weekly Planner
        response = self.client.get(reverse('weekly_planner'))
        self.assertEqual(len(response.context['tasks']), 1)
        self.assertEqual(response.context['tasks'][0].instructions, "Scheduled")
        
        # Check Daily Agenda
        response = self.client.get(reverse('daily_agenda'))
        self.assertEqual(len(response.context['tasks']), 1)
        self.assertEqual(response.context['tasks'][0].instructions, "Scheduled")
