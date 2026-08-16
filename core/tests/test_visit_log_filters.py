from datetime import date

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

from core.models import Section, VisitLog, Metric
from core.services.visit_log_services import base_visit_log_queryset, build_visit_log_queryset


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

    def test_metric_litter_covers_both_types(self):
        self.assertEqual(set(build_visit_log_queryset({'metric': 'litter'})), {self.litter})

    def test_metric_plant(self):
        self.assertEqual(set(build_visit_log_queryset({'metric': 'plant'})), {self.plant, self.plant_reed})

    def test_metric_weed(self):
        self.assertEqual(set(build_visit_log_queryset({'metric': 'weed'})), {self.weed})

    def test_metric_participants_excludes_zero(self):
        self.assertEqual(set(build_visit_log_queryset({'metric': 'participants'})), {self.litter, self.plant, self.plant_reed, self.weed})

    def test_species_exact_match(self):
        qs = build_visit_log_queryset({'metric': 'plant', 'species': 'Restio'})
        self.assertEqual(set(qs), {self.plant})  # NOT plant_reed

    def test_sort_oldest(self):
        self.assertEqual(list(build_visit_log_queryset({'sort': 'date'}))[0], self.litter)

    def test_sort_section_null_last(self):
        names = [v.section.name if v.section else None for v in build_visit_log_queryset({'sort': 'section'})]
        self.assertEqual(names, ['Alpha', 'Alpha', 'Beta', 'Beta', None])

    def test_sort_participants_desc(self):
        self.assertEqual(list(build_visit_log_queryset({'sort': '-participant_count'}))[0], self.litter)
