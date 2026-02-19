from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import User
from core.models import Section, VisitLog, Metric, Task

class WeedingMetricTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(username='admin', password='password', email='admin@example.com')
        self.client = Client()
        self.client.login(username='admin', password='password')
        
        self.section = Section.objects.create(
            name='Test Section',
            color_code='#FF0000',
            current_stage='clearing'
        )

    def test_weed_metric_creation(self):
        visit = VisitLog.objects.create(
            section=self.section,
            date=timezone.now().date(),
            notes='Test visit'
        )
        metric = Metric.objects.create(
            visit=visit,
            metric_type='weed',
            label='Wattle',
            value=5
        )
        self.assertEqual(metric.metric_type, 'weed')
        self.assertEqual(metric.label, 'Wattle')
        self.assertEqual(metric.value, 5)

    def test_section_detail_weeding_summary(self):
        visit = VisitLog.objects.create(
            section=self.section,
            date=timezone.now().date(),
            notes='Test visit'
        )
        Metric.objects.create(visit=visit, metric_type='weed', label='Wattle', value=10)
        Metric.objects.create(visit=visit, metric_type='weed', label='Kikuyu', value=5)
        Metric.objects.create(visit=visit, metric_type='weed', label='Other', value=3)
        Metric.objects.create(visit=visit, metric_type='weed', label='Wattle', value=5) # Multiple entries for same species

        response = self.client.get(reverse('section_detail', kwargs={'pk': self.section.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_weeds'], 23)
        # Top 3 should be Wattle: 15, Kikuyu: 5, Other: 3
        self.assertIn('Wattle: 15', response.context['weeding_summary'])
        self.assertIn('Kikuyu: 5', response.context['weeding_summary'])
        self.assertIn('Other: 3', response.context['weeding_summary'])

    def test_visit_log_create_skips_zero_value_weed(self):
        post_data = {
            'date': timezone.now().date().isoformat(),
            'section': self.section.pk,
            'notes': 'Logged a weed removal with zero value',
            'metrics-TOTAL_FORMS': 4,
            'metrics-INITIAL_FORMS': 0,
            'metrics-MIN_NUM_FORMS': 0,
            'metrics-MAX_NUM_FORMS': 1000,
            
            'metrics-0-metric_type': 'litter_general',
            'metrics-0-label': 'General Litter',
            'metrics-0-value': 1,
            
            'metrics-1-metric_type': 'litter_recyclable',
            'metrics-1-label': 'Recyclable Litter',
            'metrics-1-value': 0,
            
            'metrics-2-metric_type': 'plant',
            'metrics-2-label': 'Some Plant',
            'metrics-2-value': 0,
            
            'metrics-3-metric_type': 'weed',
            'metrics-3-label': 'Empty Weed',
            'metrics-3-value': 0,
            
            'photos-TOTAL_FORMS': 1,
            'photos-INITIAL_FORMS': 0,
            'photos-MIN_NUM_FORMS': 0,
            'photos-MAX_NUM_FORMS': 1000,
        }
        
        response = self.client.post(reverse('visit_log_create'), post_data)
        self.assertEqual(response.status_code, 302)
        
        visit = VisitLog.objects.latest('id')
        # Only litter_general should be saved (others are 0)
        # Note: litter_general and litter_recyclable are NOT skipped even if 0, 
        # because the logic only targets 'plant' and 'weed'.
        # Actually, let's check what is saved.
        weed_metrics = Metric.objects.filter(visit=visit, metric_type='weed')
        self.assertEqual(weed_metrics.count(), 0)
        
        plant_metrics = Metric.objects.filter(visit=visit, metric_type='plant')
        self.assertEqual(plant_metrics.count(), 0)

        # Litter metrics should still exist
        litter_metrics = Metric.objects.filter(visit=visit, metric_type__startswith='litter')
        self.assertEqual(litter_metrics.count(), 2) 
