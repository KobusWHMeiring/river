from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import User
from core.models import Section, VisitLog, Metric, Task

class DashboardTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(username='admin_dash', password='password', email='admin_dash@example.com')
        self.client = Client()
        self.client.login(username='admin_dash', password='password')
        
        self.section1, _ = Section.objects.get_or_create(name='Mowbray', defaults={'color_code': '#FF0000', 'current_stage': 'clearing'})
        self.section2, _ = Section.objects.get_or_create(name='Observatory', defaults={'color_code': '#00FF00', 'current_stage': 'planting'})

    def test_dashboard_aggregation(self):
        # Create visits with metrics
        v1 = VisitLog.objects.create(section=self.section1, date=timezone.now().date())
        Metric.objects.create(visit=v1, metric_type='litter_general', value=5)
        Metric.objects.create(visit=v1, metric_type='litter_recyclable', value=3)
        Metric.objects.create(visit=v1, metric_type='plant', label='Tree', value=10)
        
        v2 = VisitLog.objects.create(section=self.section2, date=timezone.now().date())
        Metric.objects.create(visit=v2, metric_type='litter_general', value=2)
        Metric.objects.create(visit=v2, metric_type='weed', label='Wattle', value=15)

        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # Check aggregated totals
        self.assertEqual(response.context['total_bags_general'], 7)
        self.assertEqual(response.context['total_bags_recyclable'], 3)
        self.assertEqual(response.context['total_bags'], 10)
        self.assertEqual(response.context['total_plants'], 10)
        self.assertEqual(response.context['total_weeds'], 15)

    def test_dashboard_empty_metrics(self):
        # Dashboard should not crash with zero metrics
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_bags'], 0)

    def test_recent_activity_feed(self):
        # Log a visit
        VisitLog.objects.create(section=self.section1, date=timezone.now().date(), notes="Recent Activity Test")
        
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # Verify the visit appears in the feed
        recent_visits = response.context['recent_visits']
        self.assertTrue(any(v.notes == "Recent Activity Test" for v in recent_visits))
        self.assertContains(response, "Mowbray")
        self.assertContains(response, "Recent Activity Test")

    def test_lifecycle_stage_distribution(self):
        # Data migration 0003 adds 8 sections:
        # Mowbray (clearing), San Souci (planting), Upper Liesbeek (mitigation), 
        # Observatory (follow_up), Rondebosch Common (community), Lower Liesbeek (clearing), 
        # UCT Grounds (planting), Black River Confluence (mitigation)
        # 
        # After setUp (get_or_create):
        # Mowbray -> clearing
        # Observatory -> planting (overrides follow_up if it was created as planting in defaults)
        
        # Let's verify current counts
        clearing_count = Section.objects.filter(current_stage='clearing').count()
        planting_count = Section.objects.filter(current_stage='planting').count()
        
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        
        dist = response.context['stage_distribution']
        clearing_data = next(item for item in dist if item['code'] == 'clearing')
        planting_data = next(item for item in dist if item['code'] == 'planting')
        
        self.assertEqual(clearing_data['count'], clearing_count)
        self.assertEqual(planting_data['count'], planting_count)
        
        # Change a stage
        self.section1.current_stage = 'planting'
        self.section1.save()
        
        response = self.client.get(reverse('dashboard'))
        dist = response.context['stage_distribution']
        clearing_data = next(item for item in dist if item['code'] == 'clearing')
        planting_data = next(item for item in dist if item['code'] == 'planting')
        
        self.assertEqual(clearing_data['count'], clearing_count - 1)
        self.assertEqual(planting_data['count'], planting_count + 1)
