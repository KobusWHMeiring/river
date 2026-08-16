from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse

from core.models import Section, Task, TaskTemplate, TaskType, VisitLog, TaskCompletionHistory


class TaskReopenViewTests(TestCase):
    """Tests for the task_reopen_view AJAX and redirect behaviour."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='reopentest',
            password='testpass123'
        )
        self.client.login(username='reopentest', password='testpass123')

        self.section = Section.objects.create(
            name='Reopen Section',
            color_code='#336699'
        )
        self.task = Task.objects.create(
            date=timezone.now().date(),
            section=self.section,
            assignee_type='team',
            instructions='Reopen me',
            is_completed=True,
        )
        self.visit_log = VisitLog.objects.create(
            task=self.task,
            section=self.section,
            date=timezone.now().date(),
            notes='Rich completed work',
            participant_count=4
        )

    def test_reopen_ajax(self):
        """POST with AJAX header flips is_completed to False and preserves the VisitLog."""
        url = f'/core/tasks/{self.task.id}/reopen/'
        response = self.client.post(
            url,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])

        self.task.refresh_from_db()
        self.assertFalse(self.task.is_completed)

        self.assertTrue(
            VisitLog.objects.filter(task=self.task, pk=self.visit_log.pk).exists()
        )

    def test_reopen_creates_history_event(self):
        """Reopening records a 'reopened' audit event for the task."""
        url = f'/core/tasks/{self.task.id}/reopen/'
        self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        event = TaskCompletionHistory.objects.get(task=self.task, action='reopened')
        self.assertEqual(event.user, self.user)

    def test_reopen_non_ajax_redirect(self):
        """Non-AJAX POST redirects (to daily agenda) but still reopens the task."""
        url = f'/core/tasks/{self.task.id}/reopen/'
        response = self.client.post(url)

        self.assertEqual(response.status_code, 302)
        self.task.refresh_from_db()
        self.assertFalse(self.task.is_completed)

    def test_reopen_requires_post(self):
        """GET to the reopen endpoint is rejected and leaves the task completed."""
        url = f'/core/tasks/{self.task.id}/reopen/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, 405)
        self.task.refresh_from_db()
        self.assertTrue(self.task.is_completed)

    def test_reopen_rich_log_preserved(self):
        """Reopening a task completed via the full log form keeps the log and its data."""
        url = f'/core/tasks/{self.task.id}/reopen/'
        response = self.client.post(
            url,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertTrue(response.json()['success'])

        self.visit_log.refresh_from_db()
        self.assertEqual(self.visit_log.participant_count, 4)
        self.assertEqual(self.visit_log.notes, 'Rich completed work')


class VisitLogCreateViewRedirectTests(TestCase):
    """Edge case: creating a log for a task that already has one redirects to edit."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='redirecttest',
            password='testpass123'
        )
        self.client.login(username='redirecttest', password='testpass123')

        self.section = Section.objects.create(name='Redirect Section')
        self.task = Task.objects.create(
            date=timezone.now().date(),
            section=self.section,
            instructions='Already logged',
            is_completed=True,
        )
        self.visit_log = VisitLog.objects.create(
            task=self.task,
            section=self.section,
            date=timezone.now().date(),
            notes='Existing'
        )

    def test_get_redirects_to_edit_when_task_has_log(self):
        url = reverse('visit_log_create') + f'?task={self.task.pk}'
        response = self.client.get(url)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse('visit_log_edit', kwargs={'pk': self.visit_log.pk})
        )

    def test_get_redirect_preserves_next(self):
        next_url = '/core/planner/'
        url = reverse('visit_log_create') + f'?task={self.task.pk}&next={next_url}'
        response = self.client.get(url)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            reverse('visit_log_edit', kwargs={'pk': self.visit_log.pk}) + f'?next={next_url}'
        )

    def test_get_creates_normally_when_no_log(self):
        task_no_log = Task.objects.create(
            date=timezone.now().date(),
            section=self.section,
            instructions='No log yet',
        )
        url = reverse('visit_log_create') + f'?task={task_no_log.pk}'
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)


class PlannerEditRoutingTests(TestCase):
    """Completed-task edit links on the weekly planner point to the VisitLog edit form."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='routingtest',
            password='testpass123'
        )
        self.client.login(username='routingtest', password='testpass123')

        self.section = Section.objects.create(name='Routing Section')
        today = timezone.now().date()
        self.task = Task.objects.create(
            date=today,
            section=self.section,
            assignee_type='team',
            instructions='Completed routing task',
            is_completed=True,
        )
        self.visit_log = VisitLog.objects.create(
            task=self.task,
            section=self.section,
            date=today,
            notes='Done'
        )

    def test_completed_task_edit_link_points_to_visit_log_edit(self):
        response = self.client.get(reverse('weekly_planner'))

        self.assertEqual(response.status_code, 200)
        expected = reverse('visit_log_edit', kwargs={'pk': self.visit_log.pk})
        self.assertIn(expected, response.content.decode())


class VisitLogHistoryRenderingTests(TestCase):
    """The VisitLog edit form lists completion-history events when linked to a task."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='historytest',
            password='testpass123'
        )
        self.client.login(username='historytest', password='testpass123')

        self.section = Section.objects.create(name='History Section')
        self.task = Task.objects.create(
            date=timezone.now().date(),
            section=self.section,
            instructions='History task',
            is_completed=True,
        )
        self.visit_log = VisitLog.objects.create(
            task=self.task,
            section=self.section,
            date=timezone.now().date(),
            notes='Logged',
        )
        TaskCompletionHistory.objects.create(
            task=self.task, action='completed', user=self.user
        )
        TaskCompletionHistory.objects.create(
            task=self.task, action='reopened', user=self.user
        )

    def test_history_renders_on_visit_log_edit(self):
        response = self.client.get(
            reverse('visit_log_edit', kwargs={'pk': self.visit_log.pk})
        )

        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn('Completion History', html)
        self.assertIn('Completed', html)
        self.assertIn('Reopened', html)
