"""Smoke tests: every app URL should resolve and return a non-error response.

This is the safety net that catches the class of bug behind the
``FileNotFoundError`` on ``/core/insights/`` (a view that 500'd because it
opened a file at a path that didn't exist). If a view crashes on a plain GET,
this test fails before the code ever reaches production.

How it works:
- Collect every *named* URL in the project (root + ``core.urls``).
- Skip admin (Django's own surface) and POST-only endpoints.
- GET each one as an authenticated superuser and require HTTP < 400.
"""

from django.test import TestCase, Client
from django.urls import get_resolver, reverse, URLPattern, URLResolver, NoReverseMatch
from django.contrib.auth.models import User
from django.utils import timezone

from core.models import Section, Task, TaskTemplate, TaskType, VisitLog


class UrlSmokeTests(TestCase):
    # POST-only endpoints: a plain GET is not a valid request for these, so a
    # non-2xx/3xx response is expected and they are excluded from the GET sweep.
    POST_ONLY_NAMES = {
        'section_reorder',
        'task_complete',
        'todo_update',
    }

    # Names deliberately excluded because they are not part of the app's own
    # HTML surface (admin is Django's, and any static/media serving has no name).
    EXCLUDED_PREFIXES = ('admin',)

    def setUp(self):
        self.user = User.objects.create_superuser(
            username='smoke_admin',
            password='password',
            email='smoke_admin@example.com',
        )
        self.client = Client()
        self.client.force_login(self.user)

        # Fixtures for parameterised URLs so reverse() has real objects.
        self.task_type = TaskType.objects.create(name='Smoke Type', code='smoke')
        self.section = Section.objects.create(name='Smoke Section')
        self.template = TaskTemplate.objects.create(
            name='Smoke Template',
            task_type=self.task_type,
            default_instructions='Smoke instructions',
        )
        self.task = Task.objects.create(
            date=timezone.now().date(),
            section=self.section,
            instructions='Smoke task',
        )
        self.visit = VisitLog.objects.create(
            section=self.section,
            date=timezone.now().date(),
            notes='Smoke visit',
        )

        # Map of URL name -> kwargs for every named URL that takes path args.
        # Adding a new parameterised URL means adding an entry here.
        self.kwargs_by_name = {
            'section_detail': {'pk': self.section.pk},
            'section_edit': {'pk': self.section.pk},
            'section_delete': {'pk': self.section.pk},
            'task_edit': {'pk': self.task.pk},
            'task_delete': {'pk': self.task.pk},
            'visit_log_edit': {'pk': self.visit.pk},
            'task_template_edit': {'pk': self.template.pk},
            'task_template_delete': {'pk': self.template.pk},
            'task_type_edit': {'pk': self.task_type.pk},
            'task_type_delete': {'pk': self.task_type.pk},
        }

    def _iter_url_names(self, urlpatterns=None, prefix=''):
        """Yield full names (e.g. ``dashboard``, ``admin:index``) recursively."""
        if urlpatterns is None:
            urlpatterns = get_resolver().url_patterns
        for pattern in urlpatterns:
            if isinstance(pattern, URLResolver):
                ns = pattern.namespace
                new_prefix = f'{prefix}:{ns}' if prefix and ns else (ns or prefix)
                yield from self._iter_url_names(pattern.url_patterns, new_prefix)
            elif isinstance(pattern, URLPattern) and pattern.name:
                yield f'{prefix}:{pattern.name}' if prefix else pattern.name

    def test_every_named_url_returns_a_non_error_response(self):
        failures = []
        for name in sorted(set(self._iter_url_names())):
            if name in self.POST_ONLY_NAMES or name.startswith(self.EXCLUDED_PREFIXES):
                continue

            kwargs = self.kwargs_by_name.get(name, {})
            try:
                url = reverse(name, kwargs=kwargs)
            except NoReverseMatch:
                failures.append(
                    f'{name}: needs path args but none are mapped in '
                    f'UrlSmokeTests.kwargs_by_name'
                )
                continue

            try:
                response = self.client.get(url)
            except Exception as exc:  # noqa: BLE001 - a view raising is the bug
                failures.append(f'{name} ({url}): raised {type(exc).__name__}: {exc}')
                continue

            if response.status_code >= 400:
                failures.append(f'{name} ({url}): HTTP {response.status_code}')

        self.assertEqual(
            failures,
            [],
            'The following URLs did not respond cleanly:\n' + '\n'.join(failures),
        )

    def test_planner_insights_pages(self):
        """The insights view serves both static analysis pages (the 500 culprit)."""
        for page in ('planner', 'field'):
            url = reverse('planner_insights')
            response = self.client.get(url, {'page': page})
            self.assertEqual(response.status_code, 200, f'page={page}')
            self.assertTrue(response.content.strip())
