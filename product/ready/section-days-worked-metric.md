# PRD: Section "Days Worked" Metric + Remove Litter Bags from Section Metrics

**Status:** Ready — design approved 2026-08-16
**Source:** Sarah Schumann (Director), 2026-08-12

## 1. Problem Statement

1. The section detail page does not show how many days have been worked on a section. Sarah wants a "days worked" metric at the top of each section page, pulled from the planner.
2. The "Total Litter Bags" card on the section page is misleading, because litter collection is usually not tied to a specific section. Sarah wants it removed from the section metrics.

## 2. Strategic Goal

Make section metrics reflect *field effort* (days worked) rather than misleading litter totals, so managers can see how much work a section has received at a glance.

## 3. What We Know (Current Behaviour)

- **Section detail metrics grid** (`section_detail.html`, ~lines 63–92) currently shows **four** cards:
  1. Total Litter Bags (`total_bags_general + total_bags_recyclable`)
  2. Total Plants (`total_plants`)
  3. Weeds Removed (`total_weeds`)
  4. Days in Stage (`days_in_stage`)
- These come from `SectionDetailView.get_context_data()` (`core/views.py`):
  - `total_bags_*` / `total_plants` / `total_weeds` = `Metric.objects.filter(visit__section=section)` sums.
  - `days_in_stage` = time since latest `SectionStageHistory` change (or section created).
- **"Days worked" is not currently computed.** There is no distinct-date count of work for a section.
- Planner tasks are `Task` records with `date` + `section` (and `is_rolling=False` for planner tasks). Visit logs are `VisitLog` records with `date` + `section`.

### Data investigation (2026-08-14)

Queried the dev DB to compare the two candidate definitions of "Days Worked":

| Definition | Distinct dates | Notes |
|------------|----------------|-------|
| Planned (`Task.date`, `is_rolling=False`) | 115 total (8–36 per section) | Meaningful spread across sections |
| Actual (`VisitLog.date`) | 15 total (0–6 per section) | Near-zero; 14 of 31 logs have no section |

**Verdict:** planned dates (`Task.date`) is the only useful definition today — actual-logged days are too sparse to tell a story.

**Data caveat:** 155 of 316 non-rolling tasks have no section. Analysis shows these are *mostly correctly* section-less (admin/training/meetings ~83, Weekly Litter Run ~32, ad-hoc ~38). Only ~3–4 are genuine field tasks missing a section — a small data cleanup, not a blocker.

## 4. Proposed Scope

- Add a **"Days Worked"** metric card to the section detail page, computed from distinct dates with work (planner tasks and/or visit logs — see open questions).
- Remove the **"Total Litter Bags"** card from the section detail page (and stop computing/rendering it if unused).
- Keep Plants, Weeds, and Days in Stage.

### Explicitly Out of Scope (initial)
- Removing litter from the global dashboard (dashboard aggregates all litter regardless of section — unchanged).
- Changing how litter metrics are stored/associated (a larger data-model question; out of scope unless the team decides litter should never carry a section).

## 5. Locked Decisions

| # | Decision | Choice |
|---|----------|--------|
| 1 | Definition of "Days Worked" | Distinct `Task.date` for the section (`is_rolling=False`), no task-type filter |
| 2 | Time window | Dates up to today (`date__lte=today`) — excludes future tasks |
| 3 | Metric label | "Days Worked" (kept, per Director's request) |
| 4 | Card layout | Remove Litter Bags, add Days Worked → 4 cards remain (`sm:grid-cols-4`) |
| 5 | Litter data handling | Hide-only (do not re-associate litter logs with sections) |

### Follow-up (out of scope for this PRD)

**Surfacing section-less tasks at dashboard level** — considered and rejected *as a metric*: "155 section-less tasks" conflates correctly-section-less admin/training, by-design section-less litter runs, and a handful of genuine data misses. A count would be a false alarm. If org-wide / non-section work should be visible on the dashboard, that is a separate feature (candidate for its own refinement PRD), not part of this metric change.

**Genuine data misses to fix separately** (3 tasks):
- id 302 — Community Planting Day → link to Rondebosch
- id 246 — → link to Fynbos Snake
- id 88 — spans Mowbray + Fynbos Snake (single-section FK limitation; pick one or leave)

## 6. Success Criteria (high-level)

- Section detail page shows a "Days Worked" metric at the top.
- "Total Litter Bags" is removed from the section detail page.
- Plants, Weeds, and Days in Stage remain correct.

## 7. Likely Touch Points

| Area | File | Note |
|------|------|------|
| View | `core/views.py` — `SectionDetailView.get_context_data()` | Add days-worked computation; drop litter context |
| Template | `core/templates/core/section_detail.html` | Swap Litter card for Days Worked card |
| Tests | `core/tests/` (section detail tests) | Days-worked count + litter removal |

## 8. Pre-Flight Checklist

- [x] "Days worked" definition confirmed (distinct `Task.date`, `is_rolling=False`, no type filter)
- [x] Time window for the metric confirmed (dates up to today — `date__lte=today`)
- [x] Metric label confirmed ("Days Worked")
- [x] Grid layout after card swap confirmed (4 cards)
- [x] Litter data handling decided (hide-only)
- [ ] Tests written and passing
- [ ] Manual visual verification on section detail page

---

# 2026-08-16 Section Days Worked — Design (approved)

## Final Locked Decisions

| # | Decision | Choice |
|---|----------|--------|
| 1 | Definition | Distinct `Task.date` for the section, `is_rolling=False`, no task-type filter |
| 2 | Time window | Dates up to today (`date__lte=today`) — future tasks excluded |
| 3 | Label | "Days Worked" (kept as-is) |
| 4 | Layout | Remove Litter Bags card, add Days Worked → 4 cards (`sm:grid-cols-4`) |
| 5 | Litter | Hide-only (no re-association) |

## Implementation

### View — `core/views.py` (`SectionDetailView.get_context_data()`)
- Add:
  ```python
  days_worked = Task.objects.filter(section=section, is_rolling=False, date__lte=today).values('date').distinct().count()
  ```
- Remove the two `total_bags_general` / `total_bags_recyclable` sum lines and their context entries.
- Add `days_worked` to context.

### Template — `core/templates/core/section_detail.html`
- Replace the "Total Litter Bags" card with "Days Worked":
  - Title: `Days Worked`
  - Value: `{{ days_worked }}`
  - Subtitle: `Days with planned work to date`
- Grid remains `sm:grid-cols-4`.

### Tests — new `core/tests/test_section_detail.py`
- `test_days_worked_counts_distinct_dates`
- `test_days_worked_excludes_future_dates`
- `test_days_worked_excludes_rolling`
- `test_days_worked_zero_when_no_tasks`
- `test_litter_bags_card_removed`
- `test_days_worked_card_rendered`

### No model change, no migration, no URL change.

## Verification / UAT
- Unit tests pass + `python lint.py`
- Manual: open a section with known task dates → Days Worked = distinct past dates; Litter Bags gone; 4 cards remain.

---

# Section Days Worked — Implementation Plan

**Goal:** Add a "Days Worked" metric card to the section detail page and remove the misleading "Total Litter Bags" card.

**Architecture:** One read-only aggregate added to `SectionDetailView` context; the template swaps one card. No model/migration/URL changes. Logic stays in the view (matches existing metric-sum aggregation; YAGNI).

**Tech Stack:** Django 6, SQLite (test/dev), Django TestCase.

**UAT:** `tests/uat/section_days_worked_uat.md` — drafted before implementation.

---

### Task 1: Write failing tests

**Files:**
- Create: `core/tests/test_section_detail.py`

- [ ] **Step 1: Write the failing test file**

```python
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
            name='Days Worked Section',
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
```

- [ ] **Step 2: Run tests to verify they fail (RED)**

Run: `python manage.py test core.tests.test_section_detail -v 2`
Expected: FAIL — `days_worked` missing from context (KeyError) and "Total Litter Bags" still rendered.

---

### Task 2: Implement the view change

**Files:**
- Modify: `core/views.py`

- [ ] **Step 1: Remove litter sums, add days_worked**

In `SectionDetailView.get_context_data()`, replace:
```python
        # Cumulative Metrics
        metrics = Metric.objects.filter(visit__section=section)
        total_bags_general = metrics.filter(metric_type='litter_general').aggregate(total=Sum('value'))['total'] or 0
        total_bags_recyclable = metrics.filter(metric_type='litter_recyclable').aggregate(total=Sum('value'))['total'] or 0
        total_plants = metrics.filter(metric_type='plant').aggregate(total=Sum('value'))['total'] or 0
        total_weeds = metrics.filter(metric_type='weed').aggregate(total=Sum('value'))['total'] or 0
```
with:
```python
        # Cumulative Metrics
        metrics = Metric.objects.filter(visit__section=section)
        total_plants = metrics.filter(metric_type='plant').aggregate(total=Sum('value'))['total'] or 0
        total_weeds = metrics.filter(metric_type='weed').aggregate(total=Sum('value'))['total'] or 0

        # Days Worked — distinct planned dates up to today (no type filter, excludes rolling/future)
        days_worked = Task.objects.filter(section=section, is_rolling=False, date__lte=today).values('date').distinct().count()
```

- [ ] **Step 2: Swap context entries**

In the same `context.update({...})`, remove `total_bags_general` / `total_bags_recyclable` and add `days_worked`:
```python
        context.update({
            'total_plants': total_plants,
            'total_weeds': total_weeds,
            'days_worked': days_worked,
            'weeding_summary': weeding_summary,
            'past_visits': past_visits,
            'stage_history': stage_history,
            'timeline_items': timeline_items,
            'today_tasks': today_tasks,
            'future_tasks': future_tasks,
            'today': today,
            'days_in_stage': days_in_stage
        })
```

- [ ] **Step 3: Run context tests (GREEN for logic)**

Run: `python manage.py test core.tests.test_section_detail -v 2`
Expected: `test_days_worked_counts_distinct_dates`, `test_days_worked_excludes_future_dates`, `test_days_worked_excludes_rolling`, `test_days_worked_zero_when_no_tasks`, `test_litter_bags_card_removed` PASS; `test_days_worked_card_rendered` still FAILS (template not updated).

---

### Task 3: Implement the template change

**Files:**
- Modify: `core/templates/core/section_detail.html`

- [ ] **Step 1: Swap the first metric card**

Replace:
```html
                <div class="bg-white dark:bg-slate-900 rounded-2xl border-t-4 p-6 flex flex-col items-center justify-center text-center shadow-sm border-x border-b border-slate-200 dark:border-slate-800" style="border-top-color: {{ section.color_code }};">
                    <span class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2">Total Litter Bags</span>
                    <div class="text-4xl font-light text-slate-900 dark:text-white mb-1">{{ total_bags_general|add:total_bags_recyclable }}</div>
                    <span class="text-[10px] text-slate-400 font-medium">{{ total_bags_general }} General / {{ total_bags_recyclable }} Recyclable</span>
                </div>
```
with:
```html
                <div class="bg-white dark:bg-slate-900 rounded-2xl border-t-4 p-6 flex flex-col items-center justify-center text-center shadow-sm border-x border-b border-slate-200 dark:border-slate-800" style="border-top-color: {{ section.color_code }};">
                    <span class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2">Days Worked</span>
                    <div class="text-4xl font-light text-slate-900 dark:text-white mb-1">{{ days_worked }}</div>
                    <span class="text-[10px] text-slate-400 font-medium">Days with planned work to date</span>
                </div>
```

- [ ] **Step 2: Run the full test file (GREEN)**

Run: `python manage.py test core.tests.test_section_detail -v 2`
Expected: all 6 tests PASS.

---

### Task 4: Full suite + lint + commit

- [ ] **Step 1: Run the full test suite**

Run: `python manage.py test`
Expected: all tests pass (no regressions).

- [ ] **Step 2: Run the linter**

Run: `python lint.py`
Expected: no violations.

- [ ] **Step 3: Commit**

```bash
git add core/tests/test_section_detail.py core/views.py core/templates/core/section_detail.html tests/uat/section_days_worked_uat.md
git commit -m "feat: add days-worked metric and remove litter bags from section detail"
```
