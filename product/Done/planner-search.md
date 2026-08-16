# PRD: Planner Search / Jump-to

**Status:** Shipped — UAT 9/9 passed (2026-08-16).
**Source:** Sarah Schumann (Director), 2026-08-12

## 1. Problem Statement

There is no way to search the planner. To find a past event (e.g. back to March), Sarah must navigate week-by-week on the monthly view — slow and error-prone. She wants a search button at the top of the planner to quickly find something.

## 2. Strategic Goal

Add a search affordance to the planner so users can locate a task/event by keyword or date and jump straight to it, without paging week-by-week.

## 3. What We Know (Current Behaviour)

- **Weekly planner** (`WeeklyPlannerView`, `weekly_planner.html`): navigated via `?week=YYYY-MM-DD`; prev/next week buttons.
- **Monthly planner** (`MonthlyPlannerView`, `monthly_planner.html`): navigated via `?year=&month=`; prev/next month buttons; tasks grouped by date (`tasks_by_date`).
- **No search / filter / jump-to-date control** exists on either planner.
- Tasks have searchable fields: `instructions` (text), `section.name`, `template.name` / `template.task_type.name`, `assignee_type`, `date`, `is_completed`.

## 4. Proposed Scope

- Add a search control at the top of the planner.
- Support two complementary behaviours (confirm which are needed):
  1. **Keyword search** over task instructions / section / task type, returning matching tasks with a jump link.
  2. **Jump-to-date** (a date picker or "go to month") so the user can land directly on a past date/month without week-by-week navigation.
- Results should link back to the correct week/month view with the relevant date/context preserved.

### Explicitly Out of Scope (initial)
- Full-text search infrastructure (Solr/Elasticsearch) — a simple `icontains` filter over the small task table is sufficient.
- Cross-planner editing or bulk actions from search results.

## 5. Open Questions / Decisions Needed

1. **Search vs jump-to-date:** Does Sarah want keyword search, a date picker, or both? (The "look back to March" example is date-driven, but "find something" suggests keyword.)
2. **Planner coverage:** Both weekly and monthly planners, or just monthly (where the pain is)?
3. **Results presentation:** inline dropdown under the search box, a modal, or a dedicated results page? Recommend an inline dropdown/modal with jump links.
4. **Search fields:** instructions only, or also section name and task type?
5. **Scope of search:** all-time, or within a date window?

## 6. Success Criteria (high-level)

- A user can find a March event without week-by-week navigation.
- Search results (or date jump) land the user on the correct planner view with the task visible.
- Keyword search returns relevant tasks quickly.

## 7. Likely Touch Points

| Area | File | Note |
|------|------|------|
| Views | `core/views.py` — `WeeklyPlannerView` / `MonthlyPlannerView` | Search param handling |
| URLs | `core/urls.py` | Possibly a search endpoint |
| Templates | `weekly_planner.html`, `monthly_planner.html` | Search control + results UI |
| Tests | `core/tests/test_monthly.py`, `test_urls.py` | Search + jump tests |

## 8. Pre-Flight Checklist

- [x] Search vs jump-to-date (or both) confirmed → both
- [x] Planner coverage confirmed → both weekly and monthly
- [x] Results presentation chosen → inline dropdown (live)
- [x] Search fields + scope confirmed → all tasks, all time, instructions/section/task type/template
- [ ] Tests written and passing

---

# 2026-08-14 Planner Search / Jump-to — Design

## Locked Decisions

| # | Decision | Choice |
|---|----------|--------|
| 1 | Mode | Both keyword search + date jump |
| 2 | Keyword scope | All tasks (non-rolling), all time; match instructions + section name + task type/template name |
| 3 | Results | Inline dropdown, live (debounced) |
| 4 | Result click | Preserve view (weekly→week, monthly→month) + highlight/scroll to the task |
| 5 | Date jump | Single `<input type="date">` → that date's month (monthly) or week (weekly) |
| 6 | Coverage | Both weekly and monthly planners |

## New Search Endpoint

- `GET /tasks/search/?q=…` → JSON list of top **8** matches:
  `id`, `instructions` (truncated), `date`, `section name`, `task type name`, `task type code`.
- `task_search_view` uses `LoginRequiredMixin` (consistent with every other view — no unauthenticated JSON leakage).
- Null `section` / `template` render graceful fallbacks (`"No Section"` / `"Custom Task"`), never `None`/`null` in the JSON payload (see Data Notes).
- Query shape (lives in `search_planner_tasks(q: str) -> list[dict]` in `core/services/task_services.py`; the view is a thin JSON wrapper):

```python
Task.objects.filter(is_rolling=False).filter(
    Q(instructions__icontains=q) |
    Q(section__name__icontains=q) |
    Q(template__name__icontains=q) |
    Q(template__task_type__name__icontains=q)
).select_related('section', 'template__task_type').order_by('-date')[:8]
```

- Blank/whitespace `q` → empty list.
- `is_rolling=False` keeps Kanban items out (planner only).

## Frontend

- **Search box** in the planner header; debounced (~250ms) `fetch` to the search endpoint; renders the dropdown.
- Each result is a link that stays in the **same view type** (weekly↔weekly, monthly↔monthly) but jumps to the **result's own date**: weekly → `?week=<result's Monday>&highlight=<task_id>`, monthly → `?year=<year>&month=<month>&highlight=<task_id>`.
- **Date input** in the header; on change → weekly: `?week=<date>`, monthly: `?year=<year>&month=<month>`.
- **Highlight:** on load, if `?highlight=<id>` is present, scroll to and briefly glow that task card (weekly) / day-cell badge (monthly).

## File Map

| File | Change |
|------|--------|
| `core/services/task_services.py` | Add `search_planner_tasks(q: str) -> list[dict]` (query logic) |
| `core/views.py` | Add `task_search_view` (JSON) — thin wrapper over the service |
| `core/urls.py` | Add `tasks/search/` |
| `weekly_planner.html`, `monthly_planner.html` | Search box + dropdown + date input + JS (debounce, highlight scroll) |
| `core/tests/` | Search endpoint tests |

## Test Plan (MANDATORY)

- Unit: search matches instructions, section name, task type, and template name.
- Unit: excludes rolling tasks; orders by `-date`; caps at 8.
- Unit: blank query returns empty list; no matches returns empty list.
- Edge: query with special characters (`%`, `_`, quotes) doesn't crash `icontains`.

## Data Notes (dev DB, 2026-08-16)

- 317 non-rolling tasks total; **155 have `section = NULL` (~49%)** and **60 have `template = NULL` (~19%)**; `date` is never NULL (0).
- Null-section tasks already render in both planners with per-assignee fallback labels (weekly: "General"/"Admin"/"Strategy"; monthly: grouped by date regardless of section), so jump + highlight works for them — the search dropdown must match this behaviour, not assume every task has a section/template.
- `select_related('section', 'template__task_type')` returns `None` for null FKs (safe); the JSON builder must coalesce these to the fallback strings above.

## Note

Both planners get the same controls; the only difference is the jump target (week vs month).

---

# Planner Search / Jump-to — Implementation Plan

**Goal:** Add a keyword search box and a jump-to-date input to both planners, with a debounced JSON endpoint and click-to-jump highlighting.

**Architecture:** A read-only `search_planner_tasks(q)` service in `core/services/task_services.py` does the query and returns JSON-ready dicts; a thin `@login_required` function view wraps it as JSON; both planner templates share a vanilla-JS search/dropdown/highlight snippet that differs only in its jump-URL construction.

**Tech Stack:** Django 6 CBVs/function views, `Q` + `icontains`, `select_related`, vanilla JS (`fetch`, `URLSearchParams`, `scrollIntoView`), Tailwind.

**UAT:** `tests/uat/planner_search_uat.md` — drafted before implementation.

---

### Task 1: Search service function (TDD)

**Files:**
- Create: `core/tests/test_task_search.py`
- Modify: `core/services/task_services.py`

- [ ] **Step 1: Write the failing tests**

`core/tests/test_task_search.py`:

```python
from datetime import date
from django.test import TestCase
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse
from core.models import Section, Task, TaskTemplate, TaskType
from core.services.task_services import search_planner_tasks


class SearchPlannerTasksTests(TestCase):
    def setUp(self):
        self.task_type = TaskType.objects.create(name='Weeding', code='weeding')
        self.template = TaskTemplate.objects.create(
            name='Remove Wattle', task_type=self.task_type,
            assignee_type='team', default_instructions='Cut wattle')
        self.section = Section.objects.create(name='Upper Liesbeek')

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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python manage.py test core.tests.test_task_search -v 2`
Expected: FAIL — `ImportError: cannot import name 'search_planner_tasks'`

- [ ] **Step 3: Implement the service function**

In `core/services/task_services.py`, add `from django.db.models import Q` to the imports, then append:

```python
def search_planner_tasks(q: str) -> list[dict]:
    """
    Data Flow Contract
    -------------------
    In:  q (str) — raw search text from the planner search box.
    Out: list[dict] — up to 8 matches, newest first. Keys: id, instructions
         (80 chars), date (ISO str or None), section_name, task_type_name,
         task_type_code.
    Side Effects: none (pure read).
    Fails: never raises on ordinary input; icontains escapes wildcards.
           Blank/whitespace q returns [].
    """
    q = (q or '').strip()
    if not q:
        return []

    tasks = (
        Task.objects.filter(is_rolling=False)
        .filter(
            Q(instructions__icontains=q)
            | Q(section__name__icontains=q)
            | Q(template__name__icontains=q)
            | Q(template__task_type__name__icontains=q)
        )
        .select_related('section', 'template__task_type')
        .order_by('-date')[:8]
    )

    results = []
    for t in tasks:
        tt = t.template.task_type if t.template else None
        results.append({
            'id': t.id,
            'instructions': t.instructions[:80],
            'date': t.date.isoformat() if t.date else None,
            'section_name': t.section.name if t.section else 'No Section',
            'task_type_name': tt.name if tt else 'Custom Task',
            'task_type_code': tt.code if tt else '',
        })
    return results
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python manage.py test core.tests.test_task_search -v 2`
Expected: PASS (9 tests)

- [ ] **Step 5: Commit**

```bash
git add core/services/task_services.py core/tests/test_task_search.py
git commit -m "feat: add planner search service (search_planner_tasks)"
```

---

### Task 2: Search URL + JSON view (TDD)

**Files:**
- Modify: `core/views.py`, `core/urls.py`
- Modify: `core/tests/test_task_search.py` (add view tests)

- [ ] **Step 1: Write the failing tests**

Append to `core/tests/test_task_search.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python manage.py test core.tests.test_task_search.TaskSearchViewTests -v 2`
Expected: FAIL — `NoReverseMatch` / 404 (no route, no view).

- [ ] **Step 3: Implement the view + URL**

In `core/views.py` line 24, add `search_planner_tasks` to the existing import:

```python
from .services.task_services import (
    create_task_series, update_task_series, delete_task_series,
    move_todo_task, search_planner_tasks,
)
```

Add the view (near `section_reorder_view`):

```python
@login_required
def task_search_view(request):
    """JSON search endpoint for the planner search box (keyword search)."""
    q = request.GET.get('q', '')
    return JsonResponse({'results': search_planner_tasks(q)})
```

In `core/urls.py`, add to the planner/task section:

```python
path('tasks/search/', views.task_search_view, name='task_search'),
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python manage.py test core.tests.test_task_search.TaskSearchViewTests -v 2`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add core/views.py core/urls.py core/tests/test_task_search.py
git commit -m "feat: add planner search JSON endpoint"
```

---

### Task 3: Frontend — search box, date jump, dropdown, highlight

**Files:**
- Modify: `core/templates/core/weekly_planner.html`
- Modify: `core/templates/core/monthly_planner.html`

No automated frontend tests (Playwright is a separate backlog item); verify via `tests/uat/planner_search_uat.md` + `python lint.py` + `python manage.py test core.tests.test_urls` (the URL smoke test auto-GETs the new endpoint).

- [ ] **Step 1: Add `data-task-id` to task cards/badges (for highlight)**

Weekly (3 × `.task-card` divs, one per assignee) and monthly (3 × `.task-badge` divs): add `data-task-id="{{ task.id }}"` to the outer `<div>` so the highlight JS can find it. Example (weekly team card):

```html
<div class="block bg-white ... task-card {% if task.is_completed %}opacity-60{% endif %}" data-task-id="{{ task.id }}" style="...">
```

- [ ] **Step 2: Add the search box + date input to the header controls**

In both templates, inside the header's controls `<div class="flex items-center gap-2 md:gap-3">` (the one holding the view toggle), add:

```html
<div class="relative">
  <input type="search" id="plannerSearch" placeholder="Search tasks…" autocomplete="off"
         class="w-40 md:w-56 pl-3 pr-3 py-1.5 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-xs md:text-sm text-slate-800 dark:text-slate-200 focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all outline-none">
  <div id="searchResults" class="absolute left-0 right-0 top-full mt-1 z-50 hidden max-h-80 overflow-y-auto bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg shadow-lg"></div>
</div>
<input type="date" id="plannerDateJump" title="Jump to date"
       class="pl-3 pr-3 py-1.5 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-xs md:text-sm text-slate-800 dark:text-slate-200 focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all outline-none">
```

- [ ] **Step 3: Append the search JS to `{% block extra_js %}`**

Add inside the existing `<script>` in each template's `extra_js` block, setting `PLANNER_VIEW` to `'weekly'` or `'monthly'` respectively:

```html
<script>
const SEARCH_URL = "{% url 'task_search' %}";
const PLANNER_VIEW = 'weekly';  // 'monthly' in monthly_planner.html
const searchInput = document.getElementById('plannerSearch');
const resultsBox = document.getElementById('searchResults');
const dateJump = document.getElementById('plannerDateJump');

let debounceTimer;
searchInput.addEventListener('input', () => {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(runSearch, 250);
});

function escapeHtml(s) {
  const d = document.createElement('div');
  d.textContent = s == null ? '' : String(s);
  return d.innerHTML;
}

function jumpUrl(r) {
  if (PLANNER_VIEW === 'weekly') return `?week=${r.date}&highlight=${r.id}`;
  const d = new Date(r.date + 'T00:00:00');
  return `?year=${d.getFullYear()}&month=${d.getMonth() + 1}&highlight=${r.id}`;
}

async function runSearch() {
  const q = searchInput.value.trim();
  if (!q) { resultsBox.classList.add('hidden'); return; }
  const resp = await fetch(`${SEARCH_URL}?q=${encodeURIComponent(q)}`);
  const data = await resp.json();
  const results = data.results || [];
  if (!results.length) {
    resultsBox.innerHTML = '<div class="px-3 py-2 text-xs text-slate-500">No results</div>';
  } else {
    resultsBox.innerHTML = results.map(r => `
      <a href="${jumpUrl(r)}" class="block px-3 py-2 hover:bg-slate-50 dark:hover:bg-slate-700 border-b border-slate-100 dark:border-slate-700 last:border-0">
        <span class="block text-xs font-semibold text-slate-800 dark:text-slate-200">${escapeHtml(r.instructions)}</span>
        <span class="block text-[10px] text-slate-500">${escapeHtml(r.section_name)} · ${escapeHtml(r.task_type_name)} · ${r.date}</span>
      </a>`).join('');
  }
  resultsBox.classList.remove('hidden');
}

dateJump.addEventListener('change', () => {
  if (!dateJump.value) return;
  if (PLANNER_VIEW === 'weekly') window.location = `?week=${dateJump.value}`;
  else {
    const d = new Date(dateJump.value + 'T00:00:00');
    window.location = `?year=${d.getFullYear()}&month=${d.getMonth() + 1}`;
  }
});

document.addEventListener('click', (e) => {
  if (!e.target.closest('#plannerSearch') && !e.target.closest('#searchResults')) {
    resultsBox.classList.add('hidden');
  }
});

const params = new URLSearchParams(window.location.search);
const hl = params.get('highlight');
if (hl) {
  const el = document.querySelector(`.task-card[data-task-id="${hl}"], .task-badge[data-task-id="${hl}"]`);
  if (el) {
    el.scrollIntoView({ block: 'center', behavior: 'smooth' });
    el.classList.add('ring-2', 'ring-amber-400');
    setTimeout(() => el.classList.remove('ring-2', 'ring-amber-400'), 2500);
  }
}
</script>
```

- [ ] **Step 4: Verify**

```bash
python lint.py
python manage.py test core.tests.test_urls core.tests.test_task_search -v 1
```
Expected: lint clean; all tests pass. Then run the manual `tests/uat/planner_search_uat.md` scenarios against the dev server.

- [ ] **Step 5: Commit**

```bash
git add core/templates/core/weekly_planner.html core/templates/core/monthly_planner.html
git commit -m "feat: add planner search UI (box, date jump, dropdown, highlight)"
```

---

### Final verification

```bash
python manage.py test -v 1
python lint.py
```

All green → feature is ready for UAT sign-off; then run the `maintaining-the-backlog` skill to record completion and move the PRD to `Done/`.
