from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from core.models import Section, Task, TaskTemplate, TaskType, VisitLog, TaskCompletionHistory


class TaskCompleteViewTests(TestCase):
    """Tests for the task_complete_view AJAX and redirect behavior."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

        self.section = Section.objects.create(
            name='Test Section',
            color_code='#FF5733'
        )

        self.task_type, _ = TaskType.objects.get_or_create(
            code='litter_run',
            defaults={'name': 'Litter Run'}
        )

        self.template = TaskTemplate.objects.create(
            name='Test Template',
            task_type=self.task_type,
            assignee_type='team',
            default_instructions='Collect litter along the riverbank'
        )

        self.task = Task.objects.create(
            date=timezone.now().date(),
            section=self.section,
            assignee_type='team',
            instructions='Collect litter along the riverbank',
            is_completed=False,
            template=self.template
        )

    def test_task_complete_ajax(self):
        """POST with AJAX header: task marked complete, VisitLog created, JSON success returned."""
        url = f'/core/tasks/{self.task.id}/complete/'
        response = self.client.post(
            url,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertTrue(data['success'])

        # Verify task is now completed
        self.task.refresh_from_db()
        self.assertTrue(self.task.is_completed)

        # Verify VisitLog was created
        visit_log = VisitLog.objects.filter(task=self.task).first()
        self.assertIsNotNone(visit_log)
        self.assertEqual(visit_log.section, self.task.section)
        self.assertEqual(visit_log.date, timezone.now().date())
        self.assertIn('Task completed', visit_log.notes)
        self.assertIn(self.task.instructions, visit_log.notes)

    def test_task_complete_already_completed_ajax(self):
        """POST to already-completed task returns JSON error."""
        self.task.is_completed = True
        self.task.save()

        initial_visit_log_count = VisitLog.objects.filter(task=self.task).count()

        url = f'/core/tasks/{self.task.id}/complete/'
        response = self.client.post(
            url,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertFalse(data['success'])
        self.assertEqual(data['error'], 'already_completed')

        # Verify no duplicate VisitLog was created
        self.assertEqual(
            VisitLog.objects.filter(task=self.task).count(),
            initial_visit_log_count
        )

    def test_task_complete_non_ajax_redirect(self):
        """Non-AJAX POST should still redirect to daily agenda (backward compatibility)."""
        url = f'/core/tasks/{self.task.id}/complete/'
        response = self.client.post(url)

        # Should be a redirect (302)
        self.assertEqual(response.status_code, 302)

        # Task should be completed
        self.task.refresh_from_db()
        self.assertTrue(self.task.is_completed)

        # VisitLog should be created
        visit_log = VisitLog.objects.filter(task=self.task).first()
        self.assertIsNotNone(visit_log)

    def test_task_complete_ajax_no_section(self):
        """AJAX completion for task without section should still work."""
        task_no_section = Task.objects.create(
            date=timezone.now().date(),
            section=None,
            assignee_type='team',
            instructions='A general task',
            is_completed=False,
        )

        url = f'/core/tasks/{task_no_section.id}/complete/'
        response = self.client.post(
            url,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])

        task_no_section.refresh_from_db()
        self.assertTrue(task_no_section.is_completed)

        visit_log = VisitLog.objects.filter(task=task_no_section).first()
        self.assertIsNotNone(visit_log)
        # section can be None on VisitLog
        self.assertIsNone(visit_log.section)

    def test_task_complete_with_participant_count(self):
        """POST with participant_count writes that value to the VisitLog."""
        url = f'/core/tasks/{self.task.id}/complete/'
        response = self.client.post(
            url,
            {'participant_count': '5'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])

        visit_log = VisitLog.objects.get(task=self.task)
        self.assertEqual(visit_log.participant_count, 5)

    def test_task_complete_default_participant_zero(self):
        """POST without participant_count defaults the VisitLog to 0."""
        url = f'/core/tasks/{self.task.id}/complete/'
        response = self.client.post(
            url,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        self.assertTrue(response.json()['success'])
        visit_log = VisitLog.objects.get(task=self.task)
        self.assertEqual(visit_log.participant_count, 0)

    def test_task_complete_reuses_existing_visit_log(self):
        """Re-completing a task updates the existing VisitLog instead of creating a new one."""
        existing = VisitLog.objects.create(
            task=self.task,
            section=self.section,
            date=timezone.now().date(),
            notes='Prior work',
            participant_count=2
        )

        url = f'/core/tasks/{self.task.id}/complete/'
        response = self.client.post(
            url,
            {'participant_count': '7'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        self.assertTrue(response.json()['success'])
        self.assertEqual(VisitLog.objects.filter(task=self.task).count(), 1)
        existing.refresh_from_db()
        self.assertEqual(existing.participant_count, 7)

    def test_task_complete_negative_participant_clamped_to_zero(self):
        """A negative participant_count on complete is clamped to 0, never persisted."""
        url = f'/core/tasks/{self.task.id}/complete/'
        response = self.client.post(
            url,
            {'participant_count': '-5'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])

        visit_log = VisitLog.objects.get(task=self.task)
        self.assertEqual(visit_log.participant_count, 0)

    def test_task_complete_creates_history_event(self):
        """Completing a task records a 'completed' audit event."""
        url = f'/core/tasks/{self.task.id}/complete/'
        response = self.client.post(
            url,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        self.assertTrue(response.json()['success'])
        event = TaskCompletionHistory.objects.get(task=self.task)
        self.assertEqual(event.action, 'completed')
        self.assertEqual(event.user, self.user)
