from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from core.models import Section, Task, VisitLog, Metric


class SectionDaysWorkedTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_superuser(
            username='daysworked', password='testpass123', email='d@example.com'
        )
        self.client.login(username='daysworked', password='testpass123')
        self.section = Section.objects.create(
            name='Test Section',
            color_code='#11AA22',
            current_stage='planting'
        )
        self.today = timezone.now().date()

    def test_days_worked_counts_distinct_dates(self):
        Task.objects.create(date=self.today - timedelta(days=1), section=self.section, assignee_type='team', instructions='A')
        Task.objects.create(date=self.today - timedelta(days=1), section=self.section, assignee_type='team', instructions='B same day')
        Task.objects.create(date=self.today - timedelta(days=2), section=self.section, assignee_type='team', instructions='C')
        Task.objects.create(date=self.today - timedelta(days=3), section=self.section, assignee_type='team', instructions='D')

        response = self.client.get(reverse('section_detail', kwargs={'pk': self.section.pk}))

        self.assertEqual(response.context['days_worked'], 3)

    def test_days_worked_excludes_future_dates(self):
        Task.objects.create(date=self.today + timedelta(days=2), section=self.section, assignee_type='team', instructions='Future')

        response = self.client.get(reverse('section_detail', kwargs={'pk': self.section.pk}))

        self.assertEqual(response.context['days_worked'], 0)

    def test_days_worked_excludes_rolling(self):
        Task.objects.create(section=self.section, assignee_type='team', instructions='Rolling', is_rolling=True)

        response = self.client.get(reverse('section_detail', kwargs={'pk': self.section.pk}))

        self.assertEqual(response.context['days_worked'], 0)

    def test_days_worked_zero_when_no_tasks(self):
        response = self.client.get(reverse('section_detail', kwargs={'pk': self.section.pk}))

        self.assertEqual(response.context['days_worked'], 0)

    def test_litter_bags_card_removed(self):
        visit = VisitLog.objects.create(section=self.section, date=self.today, notes='v')
        Metric.objects.create(visit=visit, metric_type='litter_general', label='gen', value=5)

        response = self.client.get(reverse('section_detail', kwargs={'pk': self.section.pk}))

        self.assertNotIn('total_bags_general', response.context)
        self.assertNotIn('total_bags_recyclable', response.context)
        self.assertNotContains(response, 'Total Litter Bags')

    def test_days_worked_card_rendered(self):
        Task.objects.create(date=self.today, section=self.section, assignee_type='team', instructions='Today')

        response = self.client.get(reverse('section_detail', kwargs={'pk': self.section.pk}))

        self.assertContains(response, 'Days Worked')
