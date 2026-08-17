from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse

from core.models import Section, Task, TaskTemplate, TaskType, VisitLog
from core.forms import VisitLogForm


class AdminTaskVisitLogEditTests(TestCase):
    """Admin tasks render no metric inputs; editing their log must not fail on
    phantom empty metric forms, and any real validation errors must be surfaced."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='adminlogtest', password='testpass123')
        self.client.login(username='adminlogtest', password='testpass123')

        self.admin_type = TaskType.objects.create(name='Admin', code='admin')
        self.template = TaskTemplate.objects.create(
            name='Outreach',
            task_type=self.admin_type,
            assignee_type='team',
            default_instructions='Admin outreach work',
        )
        self.section = Section.objects.create(name='Admin Section')
        self.task = Task.objects.create(
            date=timezone.now().date(),
            section=self.section,
            template=self.template,
            instructions='Admin outreach work',
            is_completed=True,
        )
        self.visit_log = VisitLog.objects.create(
            task=self.task,
            section=self.section,
            date=timezone.now().date(),
            notes='Task completed: Admin outreach work',
            participant_count=2,
        )

    def _post_data(self, **overrides):
        data = {
            'date': timezone.now().date().isoformat(),
            'section': self.section.id,
            'task': self.task.id,
            'participant_count': '3',
            'notes': 'Updated admin log',
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
        data.update(overrides)
        return data

    def test_admin_task_edit_accepts_no_metrics(self):
        """TOTAL_FORMS=0 (what the fixed JS sends for admin) saves successfully."""
        url = reverse('visit_log_edit', kwargs={'pk': self.visit_log.pk})
        response = self.client.post(url, self._post_data())

        self.assertEqual(response.status_code, 302, response.content[:800])
        self.visit_log.refresh_from_db()
        self.assertEqual(self.visit_log.participant_count, 3)
        self.assertEqual(self.visit_log.metrics.count(), 0)

    def test_admin_task_edit_ignores_phantom_metrics(self):
        """A stale client sending TOTAL_FORMS=2 with no metric data is now
        tolerated server-side for admin tasks (metrics are simply not expected)."""
        url = reverse('visit_log_edit', kwargs={'pk': self.visit_log.pk})
        response = self.client.post(
            url,
            self._post_data(**{'metrics-TOTAL_FORMS': '2'}),
        )

        self.assertEqual(response.status_code, 302, response.content[:800])
        self.visit_log.refresh_from_db()
        self.assertEqual(self.visit_log.metrics.count(), 0)

    def test_non_admin_metric_error_renders_banner(self):
        """A real metric validation error on a non-admin log still surfaces in the banner."""
        litter_type, _ = TaskType.objects.get_or_create(
            name='Litter Run', code='litter_run',
            defaults={'applicable_to': 'team'},
        )
        litter_template = TaskTemplate.objects.create(
            name='Litter Sweep',
            task_type=litter_type,
            assignee_type='team',
            default_instructions='Collect litter',
        )
        litter_task = Task.objects.create(
            date=timezone.now().date(),
            section=self.section,
            template=litter_template,
            instructions='Collect litter',
            is_completed=True,
        )
        litter_log = VisitLog.objects.create(
            task=litter_task,
            section=self.section,
            date=timezone.now().date(),
            notes='Litter run',
            participant_count=1,
        )

        # TOTAL_FORMS=1 with no metric-0 fields -> an empty metric form that
        # fails validation (metric_type required), which must surface in the banner.
        data = self._post_data(task=litter_task.id)
        data['metrics-TOTAL_FORMS'] = '1'

        url = reverse('visit_log_edit', kwargs={'pk': litter_log.pk})
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn('Please correct the errors below', html)
        self.assertIn('Metric type', html)


class VisitLogFormParticipantCountTests(TestCase):
    """Regression: participant_count must reject negative values at the form level."""

    def test_negative_participant_count_rejected(self):
        form = VisitLogForm(data={
            'date': '2026-08-17',
            'notes': 'test',
            'participant_count': '-5',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('participant_count', form.errors)
        self.assertIn('greater than or equal to 0', form.errors['participant_count'][0])

    def test_zero_participant_count_accepted(self):
        form = VisitLogForm(data={
            'date': '2026-08-17',
            'notes': 'test',
            'participant_count': '0',
        })
        self.assertTrue(form.is_valid(), form.errors)
