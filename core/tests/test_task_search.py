from datetime import date
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from core.models import Section, Task, TaskTemplate, TaskType
from core.services.task_services import search_planner_tasks


class SearchPlannerTasksTests(TestCase):
    def setUp(self):
        self.task_type, _ = TaskType.objects.get_or_create(
            code='weeding', defaults={'name': 'Weeding'})
        self.template = TaskTemplate.objects.create(
            name='Remove Wattle', task_type=self.task_type,
            assignee_type='team', default_instructions='Cut wattle')
        self.section, _ = Section.objects.get_or_create(
            name='Upper Liesbeek', defaults={'color_code': '#808080'})

    def make_task(self, **kw):
        defaults = dict(date=date(2026, 3, 5), section=self.section,
                        assignee_type='team', instructions='Default',
                        template=self.template)
        defaults.update(kw)
        return Task.objects.create(**defaults)

    def test_matches_instructions(self):
        self.make_task(instructions='Collect litter bags')
        results = search_planner_tasks('litter')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['instructions'][:20], 'Collect litter bags')

    def test_matches_section_name(self):
        self.make_task(instructions='Do a thing')
        self.assertEqual(len(search_planner_tasks('Upper Liesbeek')), 1)

    def test_matches_task_type_name(self):
        self.make_task(instructions='Do a thing')
        results = search_planner_tasks('Weeding')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['task_type_name'], 'Weeding')

    def test_matches_template_name(self):
        self.make_task(instructions='Do a thing')
        self.assertEqual(len(search_planner_tasks('Remove Wattle')), 1)

    def test_excludes_rolling(self):
        self.make_task(instructions='litter on kanban', is_rolling=True)
        self.assertEqual(search_planner_tasks('litter'), [])

    def test_orders_by_date_desc_and_caps_at_8(self):
        for i in range(10):
            self.make_task(instructions=f'litter task {i}', date=date(2026, 3, 1 + i))
        results = search_planner_tasks('litter')
        self.assertEqual(len(results), 8)
        dates = [r['date'] for r in results]
        self.assertEqual(dates, sorted(dates, reverse=True))

    def test_blank_query_returns_empty(self):
        self.make_task(instructions='litter')
        self.assertEqual(search_planner_tasks(''), [])
        self.assertEqual(search_planner_tasks('   '), [])

    def test_special_chars_do_not_crash(self):
        self.make_task(instructions='100% done')
        self.assertEqual(len(search_planner_tasks('%')), 1)   # literal % match
        self.assertEqual(search_planner_tasks('_'), [])        # literal _, no crash
        self.assertEqual(search_planner_tasks('"'), [])        # quote, no crash

    def test_null_section_and_template_fallback(self):
        Task.objects.create(date=date(2026, 3, 5), assignee_type='team',
                            instructions='Intern training', section=None, template=None)
        results = search_planner_tasks('Intern')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['section_name'], 'No Section')
        self.assertEqual(results[0]['task_type_name'], 'Custom Task')
        self.assertEqual(results[0]['task_type_code'], '')


class TaskSearchViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='s', password='pw')
        self.client = Client()

    def test_url_resolves(self):
        self.assertEqual(reverse('task_search'), '/core/tasks/search/')

    def test_authenticated_returns_json(self):
        self.client.login(username='s', password='pw')
        resp = self.client.get('/core/tasks/search/', {'q': 'litter'})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'application/json')
        self.assertIn('results', resp.json())

    def test_unauthenticated_redirects(self):
        resp = self.client.get('/core/tasks/search/', {'q': 'litter'})
        self.assertEqual(resp.status_code, 302)
