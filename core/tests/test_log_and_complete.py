from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse

from core.models import Section, Task, TaskTemplate, TaskType, VisitLog, TaskCompletionHistory


class LogAndCompleteTests(TestCase):
    """'Log and Complete' must mark the task complete even when the task already
    has a VisitLog (the create view redirects to the edit view in that case)."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='logcomplete', password='testpass123')
        self.client.login(username='logcomplete', password='testpass123')

        self.section = Section.objects.create(name='Log Complete Section')
        self.task_type, _ = TaskType.objects.get_or_create(
            code='litter_run', defaults={'name': 'Litter Run'}
        )
        self.template = TaskTemplate.objects.create(
            name='Cleanup', task_type=self.task_type, assignee_type='team',
            default_instructions='Clean the section',
        )
        # Reopened task: has a VisitLog but is not completed.
        self.task = Task.objects.create(
            date=timezone.now().date(),
            section=self.section,
            assignee_type='team',
            instructions='Rondebosch Rovers clean up',
            template=self.template,
            is_completed=False,
        )
        self.visit_log = VisitLog.objects.create(
            task=self.task,
            section=self.section,
            date=timezone.now().date(),
            notes='Task completed: prior work',
            participant_count=4,
        )

    def _post_data(self):
        return {
            'date': timezone.now().date().isoformat(),
            'section': self.section.id,
            'task': self.task.id,
            'participant_count': '5',
            'notes': 'Rondebosch Rovers clean up',
            'next': '',
            'metrics-TOTAL_FORMS': '0',
            'metrics-INITIAL_FORMS': '0',
            'metrics-MIN_NUM_FORMS': '0',
            'metrics-MAX_NUM_FORMS': '1000',
            'photos-TOTAL_FORMS': '0',
            'photos-INITIAL_FORMS': '0',
            'photos-MIN_NUM_FORMS': '0',
            'photos-MAX_NUM_FORMS': '1000',
        }

    def test_log_and_complete_redirects_to_edit_when_log_exists(self):
        url = reverse('visit_log_create') + f'?task={self.task.pk}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse('visit_log_edit', kwargs={'pk': self.visit_log.pk}),
        )

    def test_saving_log_edit_recompletes_task(self):
        url = reverse('visit_log_edit', kwargs={'pk': self.visit_log.pk})
        response = self.client.post(url, self._post_data())

        self.assertEqual(response.status_code, 302, response.content[:800])
        self.task.refresh_from_db()
        self.assertTrue(self.task.is_completed)
        self.assertTrue(
            TaskCompletionHistory.objects.filter(
                task=self.task, action='completed'
            ).exists()
        )

    def test_repeated_edit_does_not_duplicate_completion_history(self):
        self.task.is_completed = True
        self.task.save()
        TaskCompletionHistory.objects.create(
            task=self.task, action='completed', user=self.user
        )
        url = reverse('visit_log_edit', kwargs={'pk': self.visit_log.pk})
        response = self.client.post(url, self._post_data())

        self.assertEqual(response.status_code, 302, response.content[:800])
        self.assertEqual(
            TaskCompletionHistory.objects.filter(
                task=self.task, action='completed'
            ).count(),
            1,
        )
        self.task.refresh_from_db()
        self.assertTrue(self.task.is_completed)
