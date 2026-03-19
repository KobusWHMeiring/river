import uuid
from datetime import date, timedelta
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from core.models import Task, Section, TaskTemplate, TaskType
from core.services.task_services import create_task_series, update_task_series, delete_task_series

User = get_user_model()

class TaskSeriesServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.section = Section.objects.create(name='Test Section', color_code='#FFFFFF')
        self.task_type = TaskType.objects.create(name='Litter Run', code='litter_run', applicable_to='team')
        self.template = TaskTemplate.objects.create(
            name='Daily Litter Pick',
            task_type=self.task_type,
            assignee_type='team',
            default_instructions='Pick up all litter.'
        )
        self.base_task_data = {
            'section': self.section,
            'assignee_type': 'team',
            'instructions': 'Clean up the area.',
            'template': self.template,
        }

    def test_create_task_series_basic(self):
        # March 2, 2026 is Monday
        start_date = date(2026, 3, 2) # Monday
        end_date = date(2026, 3, 4)   # Wednesday (3 days: Mon, Tue, Wed)
        
        # Test with exclude_weekends=True (default)
        tasks_created = create_task_series(self.base_task_data, start_date, end_date, exclude_weekends=True)
        self.assertEqual(tasks_created, 3) 

        self.assertEqual(Task.objects.count(), 3)
        task = Task.objects.first()
        self.assertIsNotNone(task.group_id)

    def test_create_task_series_skips_weekends(self):
        # March 6 (Fri) to March 9 (Mon)
        start_date = date(2026, 3, 6)  # Friday
        end_date = date(2026, 3, 9)    # Monday
        # Expected: Fri, Mon (2 tasks)
        tasks_created = create_task_series(self.base_task_data, start_date, end_date, exclude_weekends=True)
        self.assertEqual(tasks_created, 2)
        self.assertEqual(Task.objects.count(), 2)
        self.assertTrue(Task.objects.filter(date=date(2026, 3, 6)).exists())
        self.assertTrue(Task.objects.filter(date=date(2026, 3, 9)).exists())
        self.assertFalse(Task.objects.filter(date=date(2026, 3, 7)).exists()) # Saturday
        self.assertFalse(Task.objects.filter(date=date(2026, 3, 8)).exists()) # Sunday

    def test_create_task_series_90_day_limit(self):
        start_date = date(2026, 1, 1)
        end_date = date(2026, 4, 15) # > 90 days

        with self.assertRaises(ValueError):
            create_task_series(self.base_task_data, start_date, end_date)
        
        self.assertEqual(Task.objects.count(), 0)

    def test_update_single_task(self):
        start_date = date(2026, 3, 2)
        end_date = date(2026, 3, 4)
        create_task_series(self.base_task_data, start_date, end_date)
        
        task_to_update = Task.objects.get(date=date(2026, 3, 3))
        original_group_id = task_to_update.group_id

        update_data = {'instructions': 'Updated instructions for single task.'}
        updated_count = update_task_series(
            task_to_update.group_id, 
            update_data, 
            update_all=False, 
            current_task_id=task_to_update.id
        )
        self.assertEqual(updated_count, 1)

        task_to_update.refresh_from_db()
        self.assertEqual(task_to_update.instructions, 'Updated instructions for single task.')

        other_task = Task.objects.get(date=date(2026, 3, 2))
        self.assertEqual(other_task.instructions, self.base_task_data['instructions'])

    def test_update_task_series_all(self):
        start_date = date(2026, 3, 2)
        end_date = date(2026, 3, 4)
        create_task_series(self.base_task_data, start_date, end_date)
        
        series_tasks = Task.objects.filter(date__range=[start_date, end_date])
        group_id = series_tasks.first().group_id
        
        new_section = Section.objects.create(name='New Section', color_code='#000000')
        update_data = {
            'instructions': 'Updated instructions for entire series.',
            'section': new_section,
            'assignee_type': 'manager',
        }
        
        completed_task = Task.objects.get(date=date(2026, 3, 3))
        completed_task.is_completed = True
        completed_task.save()

        updated_count = update_task_series(
            group_id, 
            update_data, 
            update_all=True, 
            current_task_id=series_tasks.first().id
        )
        self.assertEqual(updated_count, 3)

        for task in series_tasks:
            task.refresh_from_db()
            self.assertEqual(task.instructions, 'Updated instructions for entire series.')
            self.assertEqual(task.section, new_section)

        completed_task.refresh_from_db()
        self.assertTrue(completed_task.is_completed)

    def test_delete_single_task(self):
        start_date = date(2026, 3, 2)
        end_date = date(2026, 3, 4)
        create_task_series(self.base_task_data, start_date, end_date)
        
        task_to_delete = Task.objects.get(date=date(2026, 3, 3))
        
        deleted_count = delete_task_series(
            task_to_delete.group_id, 
            delete_all=False, 
            current_task_id=task_to_delete.id
        )
        self.assertEqual(deleted_count, 1)
        self.assertEqual(Task.objects.count(), 2)

    def test_delete_task_series_all(self):
        start_date = date(2026, 3, 2)
        end_date = date(2026, 3, 4)
        create_task_series(self.base_task_data, start_date, end_date)
        
        task_in_series = Task.objects.first()
        group_id = task_in_series.group_id

        deleted_count = delete_task_series(
            group_id, 
            delete_all=True, 
            current_task_id=task_in_series.id
        )
        self.assertEqual(deleted_count, 3)
        self.assertEqual(Task.objects.count(), 0)

class TaskSeriesViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client.login(username='testuser', password='password')
        self.section = Section.objects.create(name='Test Section', color_code='#FFFFFF')
        self.task_type = TaskType.objects.create(name='Litter Run', code='litter_run', applicable_to='team')
        self.template = TaskTemplate.objects.create(
            name='Daily Litter Pick',
            task_type=self.task_type,
            assignee_type='team',
            default_instructions='Pick up all litter.'
        )
        self.base_task_data = {
            'section': self.section,
            'assignee_type': 'team',
            'instructions': 'Clean up the area.',
            'template': self.template,
        }
        self.another_section = Section.objects.create(name='Another Section', color_code='#000000')

    def test_task_create_series_post_request(self):
        start_date = date(2026, 3, 2) # Monday
        end_date = date(2026, 3, 6)   # Friday
        
        response = self.client.post(reverse('task_create'), {
            'date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'exclude_weekends': 'on',
            'section': self.section.id,
            'assignee_type': 'team',
            'instructions': 'Series task instructions.',
            'template': self.template.id,
        })
        self.assertEqual(response.status_code, 302)

        tasks = Task.objects.all().order_by('date')
        self.assertEqual(tasks.count(), 5) # Mon-Fri

    def test_task_create_series_post_request_include_weekends(self):
        start_date = date(2026, 3, 7) # Saturday
        end_date = date(2026, 3, 8)   # Sunday
        
        response = self.client.post(reverse('task_create'), {
            'date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'exclude_weekends': '', 
            'section': self.section.id,
            'assignee_type': 'team',
            'instructions': 'Weekend series task instructions.',
            'template': self.template.id,
        })
        self.assertEqual(response.status_code, 302)
        
        tasks = Task.objects.all().order_by('date')
        self.assertEqual(tasks.count(), 2) # Sat, Sun

    def test_task_create_series_post_request_validation_error(self):
        start_date = date(2026, 1, 1)
        end_date = date(2026, 4, 15) # > 90 days

        response = self.client.post(reverse('task_create'), {
            'date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'exclude_weekends': 'on',
            'section': self.section.id,
            'assignee_type': 'team',
            'instructions': 'Too long series.',
            'template': self.template.id,
        })
        self.assertEqual(response.status_code, 200) 
        # Manually check for error since assertFormError is finicky with some view patterns
        self.assertTrue('form' in response.context)
        self.assertTrue('end_date' in response.context['form'].errors)

    def test_task_update_single_task_from_series(self):
        start_date = date(2026, 3, 2)
        end_date = date(2026, 3, 4)
        create_task_series(self.base_task_data, start_date, end_date)
        
        task_to_update = Task.objects.get(date=date(2026, 3, 3))

        response = self.client.post(reverse('task_edit', args=[task_to_update.id]), {
            'date': task_to_update.date.strftime('%Y-%m-%d'),
            'section': self.section.id,
            'assignee_type': 'team',
            'instructions': 'Single task updated instructions.',
            'template': self.template.id,
            'update_all_in_series': '',
        })
        self.assertEqual(response.status_code, 302)
        task_to_update.refresh_from_db()
        self.assertEqual(task_to_update.instructions, 'Single task updated instructions.')

    def test_task_update_series_all_tasks(self):
        start_date = date(2026, 3, 2)
        end_date = date(2026, 3, 4)
        create_task_series(self.base_task_data, start_date, end_date)
        
        task_in_series = Task.objects.first()
        group_id = task_in_series.group_id
        
        response = self.client.post(reverse('task_edit', args=[task_in_series.id]), {
            'date': task_in_series.date.strftime('%Y-%m-%d'),
            'section': self.another_section.id,
            'assignee_type': 'manager',
            'instructions': 'Updated all series instructions.',
            'template': self.template.id,
            'update_all_in_series': 'on',
        })
        self.assertEqual(response.status_code, 302)

        for task in Task.objects.filter(group_id=group_id):
            task.refresh_from_db()
            self.assertEqual(task.instructions, 'Updated all series instructions.')

    def test_task_delete_single_task_from_series(self):
        start_date = date(2026, 3, 2)
        end_date = date(2026, 3, 4)
        create_task_series(self.base_task_data, start_date, end_date)
        
        task_to_delete = Task.objects.get(date=date(2026, 3, 3))

        response = self.client.post(reverse('task_delete', args=[task_to_delete.id]), {
            'delete_all': 'false'
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Task.objects.count(), 2)

    def test_task_delete_series_all_tasks(self):
        start_date = date(2026, 3, 2)
        end_date = date(2026, 3, 4)
        create_task_series(self.base_task_data, start_date, end_date)
        
        task_in_series = Task.objects.first()

        response = self.client.post(reverse('task_delete', args=[task_in_series.id]), {
            'delete_all': 'true'
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Task.objects.count(), 0)
