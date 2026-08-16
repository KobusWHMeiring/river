from datetime import date

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

from core.models import Section, VisitLog, Metric
from core.services.visit_log_services import base_visit_log_queryset


class VisitLogServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(username='filters', password='password', email='f@example.com')
        self.client = Client()
        self.client.login(username='filters', password='password')

        self.alpha, _ = Section.objects.get_or_create(name='Alpha', defaults={'color_code': '#111111', 'current_stage': 'clearing'})
        self.beta, _ = Section.objects.get_or_create(name='Beta', defaults={'color_code': '#222222', 'current_stage': 'planting'})

        self.litter = VisitLog.objects.create(section=self.alpha, date=date(2026, 8, 1), participant_count=4, notes='litter note')
        Metric.objects.create(visit=self.litter, metric_type='litter_general', value=5)
        Metric.objects.create(visit=self.litter, metric_type='litter_recyclable', value=3)

        self.plant = VisitLog.objects.create(section=self.beta, date=date(2026, 8, 2), participant_count=2, notes='plant note')
        Metric.objects.create(visit=self.plant, metric_type='plant', label='Restio', value=10)

        self.plant_reed = VisitLog.objects.create(section=self.alpha, date=date(2026, 8, 3), participant_count=1, notes='reed note')
        Metric.objects.create(visit=self.plant_reed, metric_type='plant', label='Restio reed', value=7)

        self.weed = VisitLog.objects.create(section=self.beta, date=date(2026, 8, 4), participant_count=3, notes='weed note')
        Metric.objects.create(visit=self.weed, metric_type='weed', label='Wattle', value=15)

        self.zero = VisitLog.objects.create(section=None, date=date(2026, 8, 5), participant_count=0, notes='zero note')

    def test_base_section_filter(self):
        qs = base_visit_log_queryset({'section': str(self.alpha.id)})
        self.assertEqual(set(qs), {self.litter, self.plant_reed})

    def test_base_search_filter(self):
        qs = base_visit_log_queryset({'q': 'weed note'})
        self.assertEqual(set(qs), {self.weed})

    def test_base_activity_type_filter(self):
        qs = base_visit_log_queryset({'activity_type': 'planned'})
        # None of these fixtures have a Task, so planned => empty
        self.assertEqual(set(qs), set())
