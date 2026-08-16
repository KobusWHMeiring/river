from datetime import timedelta

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import User
from core.models import Section, VisitLog, Metric, Task, TaskType, TaskTemplate

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

    def test_participant_count_aggregation(self):
        """Dashboard should sum participant_count across all visits."""
        VisitLog.objects.create(section=self.section1, date=timezone.now().date(), participant_count=5)
        VisitLog.objects.create(section=self.section2, date=timezone.now().date(), participant_count=3)
        VisitLog.objects.create(section=self.section1, date=timezone.now().date(), participant_count=0)

        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_participants'], 8)

    def test_participant_count_defaults_to_zero(self):
        """Existing visits with default participant_count=0 should not crash aggregation."""
        VisitLog.objects.create(section=self.section1, date=timezone.now().date())

        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_participants'], 0)


class DashboardWeeklyActivityTests(TestCase):
    """Planner activity indicators: weekly task-type tags on the dashboard."""

    def setUp(self):
        self.user = User.objects.create_superuser(username='admin_weekly', password='password', email='admin_weekly@example.com')
        self.client = Client()
        self.client.login(username='admin_weekly', password='password')

        # Task types (codes are the source of truth for tags)
        self.litter_type, _ = TaskType.objects.get_or_create(code='litter_run', defaults={'name': 'Litter Run'})
        self.weeding_type, _ = TaskType.objects.get_or_create(code='weeding', defaults={'name': 'Weeding'})
        self.planting_type, _ = TaskType.objects.get_or_create(code='planting', defaults={'name': 'Planting'})
        self.admin_type, _ = TaskType.objects.get_or_create(code='admin', defaults={'name': 'Admin'})

        self.litter_tpl, _ = TaskTemplate.objects.get_or_create(
            name='Weekly Litter', defaults={'task_type': self.litter_type, 'default_instructions': 'Litter'}
        )
        self.weeding_tpl, _ = TaskTemplate.objects.get_or_create(
            name='Weekly Weeding', defaults={'task_type': self.weeding_type, 'default_instructions': 'Weed'}
        )
        self.planting_tpl, _ = TaskTemplate.objects.get_or_create(
            name='Weekly Planting', defaults={'task_type': self.planting_type, 'default_instructions': 'Plant'}
        )
        self.admin_tpl, _ = TaskTemplate.objects.get_or_create(
            name='Weekly Admin', defaults={'task_type': self.admin_type, 'default_instructions': 'Admin'}
        )

        self.section_clear = Section.objects.create(name='Weekly Clearing', color_code='#111111', current_stage='clearing')
        self.section_plant = Section.objects.create(name='Weekly Planting', color_code='#222222', current_stage='planting')

        self.today = timezone.now().date()
        self.monday = self.today - timedelta(days=self.today.weekday())

    def _task(self, date, section, template, **kwargs):
        return Task.objects.create(date=date, section=section, instructions='Test', template=template, **kwargs)

    def test_weekly_activity_aggregation(self):
        # This week: clearing section has litter + weeding, planting section has planting
        self._task(self.monday, self.section_clear, self.litter_tpl)
        self._task(self.monday, self.section_clear, self.weeding_tpl)
        self._task(self.monday, self.section_plant, self.planting_tpl)

        # Section with no tasks this week
        Section.objects.create(name='Weekly Empty', color_code='#333333', current_stage='mitigation')
        # Section with tasks next week (should not appear)
        next_week_section = Section.objects.create(name='Weekly Next', color_code='#444444', current_stage='mitigation')
        self._task(self.monday + timedelta(days=7), next_week_section, self.litter_tpl)

        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)

        activity = response.context['section_weekly_activity']
        self.assertEqual(set(activity.keys()), {self.section_clear.pk, self.section_plant.pk})
        self.assertEqual(activity[self.section_clear.pk], ['litter_run', 'weeding'])
        self.assertEqual(activity[self.section_plant.pk], ['planting'])

        # Tags actually render in the template
        self.assertContains(response, 'bg-red-50 text-red-600 border-red-100')
        self.assertContains(response, 'bg-green-50 text-green-600 border-green-100')

    def test_weekly_activity_includes_completed_tasks(self):
        self._task(self.monday, self.section_clear, self.litter_tpl, is_completed=True)

        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.context['section_weekly_activity'][self.section_clear.pk], ['litter_run'])

    def test_weekly_activity_skips_tasks_without_template(self):
        Task.objects.create(date=self.monday, section=self.section_clear, instructions='No template')

        response = self.client.get(reverse('dashboard'))
        self.assertNotIn(self.section_clear.pk, response.context['section_weekly_activity'])

    def test_weekly_activity_skips_sectionless_tasks(self):
        # Section-less tasks are the planner's "Admin" convention
        self._task(self.monday, None, self.litter_tpl)

        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        activity = response.context['section_weekly_activity']
        stage_activity = response.context['stage_weekly_activity']
        self.assertNotIn(None, activity)
        self.assertEqual(stage_activity, {})

    def test_no_sections_have_tasks_this_week(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.context['section_weekly_activity'], {})
        self.assertEqual(response.context['stage_weekly_activity'], {})

    def test_stage_weekly_activity(self):
        # Two sections in "Planting" stage: one planting, one weeding
        planting_b = Section.objects.create(name='Weekly Planting B', color_code='#555555', current_stage='planting')
        self._task(self.monday, self.section_plant, self.planting_tpl)
        self._task(self.monday, planting_b, self.weeding_tpl)
        # Admin task on a planting section must be excluded from lifecycle bars
        self._task(self.monday, self.section_plant, self.admin_tpl)

        response = self.client.get(reverse('dashboard'))
        stage_activity = response.context['stage_weekly_activity']

        self.assertEqual(stage_activity.get('planting'), {'planting', 'weeding'})
        self.assertNotIn('admin', stage_activity.get('planting', set()))

    def test_stage_weekly_activity_empty_stage_has_no_entry(self):
        # Only a clearing task; planting stage has sections but no tasks
        self._task(self.monday, self.section_clear, self.litter_tpl)

        response = self.client.get(reverse('dashboard'))
        stage_activity = response.context['stage_weekly_activity']

        self.assertEqual(stage_activity.get('clearing'), {'litter_run'})
        self.assertNotIn('planting', stage_activity)
