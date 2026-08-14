# Quick Specs: Participant Count + Typeable Litter Bags

> Combined quick specs for Sarah's requests #5 and #7. Low complexity — no full PRD needed.

---

## Spec 1: Participant Count on Dashboard (#5)

### Problem
The Impact Dashboard tracks litter bags, plants, and weeds — but has no visibility into how many people participated. Sarah wants a participant count alongside the other impact metrics.

### Design

**Model change:** Add `participant_count` to `VisitLog`:

```python
# core/models.py — VisitLog
participant_count = models.PositiveIntegerField(default=0)
```

**Form:** Add a number input to `VisitLogForm` in the Core Details section:
```html
<input type="number" name="participant_count" min="0" value="0"
       class="w-full pl-10 pr-4 py-3 ...">
```

**Dashboard:** Add aggregation in `DashboardView`:
```python
total_participants = VisitLog.objects.aggregate(Sum('participant_count'))['participant_count__sum'] or 0
```

**Template:** New stat card alongside existing Litter/Re-Planting/Invasives cards:
```html
<div class="stat-card border-t-4 border-t-purple-500">
  👥 Participants
  {{ total_participants }} People
</div>
```

### File Map

| File | Change |
|------|--------|
| `core/models.py` | Add `participant_count` field to `VisitLog` |
| `core/forms.py` | Add field to `VisitLogForm.Meta.fields` |
| `core/views.py` | Add aggregation to `DashboardView` |
| `core/templates/core/visit_log_form.html` | Add number input in Core Details |
| `core/templates/core/dashboard.html` | Add participant stat card |
| Migration | `python manage.py makemigrations` |

### Test Plan
- [ ] Migration applies cleanly
- [ ] Existing visit logs default to `participant_count=0`
- [ ] Dashboard shows correct `Sum()` of participant counts
- [ ] Form saves and displays participant count correctly

### Risks
None — additive field with default, no existing data affected.

---

## Spec 2: Typeable Litter Bag Counts (#7)

### Problem
The visit log form uses +/- buttons for litter bag counters. Sarah finds clicking tedious for large counts and wants to type the number directly.

### Design

Replace the +/- button UI with `<input type="number">` fields. The current hidden inputs (`litter_general_input`, `litter_recyclable_input`) already store the values — we just swap the display.

**Current UI:**
```
  [−]  0  [+]    General Litter Bags
```

**New UI:**
```
  [  0  ]  General Litter Bags
```

A plain number input styled to match the existing form aesthetic. Min 0, no max.

**JavaScript changes:**
- Remove the `updateCounter()` calls for litter inputs
- Add a small `oninput` handler to sync display (if needed) — but with direct `<input>`, no JS needed at all for the basic flow

### File Map

| File | Change |
|------|--------|
| `core/templates/core/visit_log_form.html` | Replace +/- button blocks with `<input type="number">` for litter_general and litter_recyclable |

### Test Plan
- [ ] Type a number directly into litter bag fields
- [ ] Submit form — values persist correctly
- [ ] Edit an existing log — values display and can be modified
- [ ] Zero and negative values handled (min=0 prevents negatives)
- [ ] Existing weeding/planting +/- buttons unaffected

### Risks
None — template-only change, no database or view changes.

---

*Quick specs written 2026-08-11. These are small enough to implement directly from this spec without a full PRD.*

---

## 2026-08-11 Participant Count + Typeable Litter Bags — Design

*Design approved 2026-08-11. See resolution of readiness review gaps below.*

### Spec 1: Participant Count — Resolved Gaps

**Grid layout:** `lg:grid-cols-3` → `lg:grid-cols-4` on dashboard stat cards row.

**Form widget:** Add `widgets` entry in `VisitLogForm.Meta`:
```python
'participant_count': forms.NumberInput(attrs={'min': 0}),
```

**Placement in Core Details:** New standalone row between Date/Section row and Task row, constrained to `max-w-xs`:
```html
<div class="space-y-2">
    <label class="block text-sm font-bold text-slate-700 dark:text-slate-300 tracking-tight">
        Number of Participants
    </label>
    <div class="relative max-w-xs">
        <span class="absolute inset-y-0 left-3 flex items-center text-slate-400 pointer-events-none">
            <span class="material-symbols-outlined text-lg">groups</span>
        </span>
        <input type="number" name="participant_count" min="0" value="{{ form.participant_count.value|default:0 }}"
               class="w-full pl-10 pr-4 py-3 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-base focus:ring-2 focus:ring-primary/20 focus:border-primary dark:text-slate-200">
    </div>
</div>
```

**Dashboard card:** Purple stat card using `groups` Material Symbol icon, matching existing card pattern:
```html
<div class="stat-card border-t-4 border-t-purple-500">
    <div class="flex justify-between items-start mb-4">
        <span class="p-2 bg-purple-50 dark:bg-purple-900/30 rounded-lg text-purple-600 dark:text-purple-400">
            <span class="material-symbols-outlined">groups</span>
        </span>
        <span class="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Participation</span>
    </div>
    <div class="text-3xl font-bold text-slate-900 dark:text-white mb-1">{{ total_participants }} <span class="text-sm font-medium text-slate-400 uppercase">People</span></div>
    <p class="text-[10px] text-slate-500 font-medium uppercase tracking-wider">Total volunteers across all visits</p>
</div>
```

### Spec 2: Typeable Litter Bags — Resolved Gaps

**Input names:** Reuse existing hidden inputs — change `type="hidden"` to `type="number"` on `name="metrics-0-value"` and `name="metrics-1-value"`. Formset submission unchanged.

**JS cleanup:** Remove `litter_general: 0` and `litter_recyclable: 0` from `counters` object init. `updateCounter()` function preserved (used by weeding/planting). Remove `onclick="updateCounter(...)"` from the removed buttons.

**Visual spec:**
```html
<input type="number" name="metrics-0-value" min="0" value="{{ metric_formset.0.value.value|default:0 }}"
       class="w-24 px-0 py-2 text-center text-2xl md:text-3xl font-bold bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary dark:text-white appearance-none">
```
- `w-24` compact width, centered in parent card
- `text-2xl md:text-3xl font-bold` matches old display span
- `appearance-none` removes browser spinner arrows
- Hidden `metric_type` and `label` inputs preserved below

---

## 2026-08-11 Participant Count + Typeable Litter Bags — Implementation Plan

**Goal:** Add participant tracking to VisitLog/Dashboard and replace litter bag +/- buttons with typeable number inputs.

**Architecture:** Two additive changes sharing the same files. Spec 1 adds a model field + form field + dashboard aggregation + stat card. Spec 2 is a template-only UI swap (hidden input → visible number input) with minor JS cleanup.

**Tech Stack:** Django 6.0.2, Python 3.x, Django Template Language, Tailwind CSS, Vanilla JS

**UAT:** `tests/uat/participants-typeable_uat.md` — drafted before implementation

---

### Task 1: Add `participant_count` to VisitLog model

**Files:**
- Modify: `core/models.py`

- [ ] **Step 1: Add field to VisitLog**

In `core/models.py`, inside the `VisitLog` class (after `notes` field, line 213):

```python
participant_count = models.PositiveIntegerField(default=0)
```

- [ ] **Step 2: Generate and apply migration**

```bash
python manage.py makemigrations
python manage.py migrate
```

Expected: `core/migrations/XXXX_add_participant_count.py` created, applied cleanly.

- [ ] **Step 3: Verify existing rows default to 0**

```bash
python manage.py shell -c "from core.models import VisitLog; print(VisitLog.objects.filter(participant_count__isnull=True).count())"
```

Expected: `0` (no NULLs)

- [ ] **Step 4: Commit**

```bash
git add core/models.py core/migrations/
git commit -m "feat: add participant_count to VisitLog model"
```

---

### Task 2: Add `participant_count` to VisitLogForm

**Files:**
- Modify: `core/forms.py`

- [ ] **Step 1: Add field to Meta.fields and widget**

In `core/forms.py`, inside `VisitLogForm.Meta` (line 163), change:

```python
fields = ['task', 'section', 'date', 'notes', 'participant_count']
widgets = {
    'date': forms.DateInput(attrs={'type': 'date'}),
    'notes': forms.Textarea(attrs={'rows': 3}),
    'participant_count': forms.NumberInput(attrs={'min': 0}),
}
```

- [ ] **Step 2: Verify form renders correctly**

```bash
python manage.py shell -c "from core.forms import VisitLogForm; f = VisitLogForm(); print('participant_count' in f.fields)"
```

Expected: `True`

- [ ] **Step 3: Commit**

```bash
git add core/forms.py
git commit -m "feat: add participant_count to VisitLogForm"
```

---

### Task 3: Add participant_count input to visit log form template

**Files:**
- Modify: `core/templates/core/visit_log_form.html`

- [ ] **Step 1: Add participant_count input in Core Details**

Insert between the Date/Section grid row and the Task row (after line ~183, after the `</div>` closing the grid div, before the `<!-- Task/Activity -->` comment):

```html
<!-- Participants -->
<div class="space-y-2">
    <label class="block text-sm font-bold text-slate-700 dark:text-slate-300 tracking-tight">
        Number of Participants
    </label>
    <div class="relative max-w-xs">
        <span class="absolute inset-y-0 left-3 flex items-center text-slate-400 pointer-events-none">
            <span class="material-symbols-outlined text-lg">groups</span>
        </span>
        <input type="number" name="participant_count" min="0" value="{{ form.participant_count.value|default:0 }}"
               class="w-full pl-10 pr-4 py-3 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-base focus:ring-2 focus:ring-primary/20 focus:border-primary dark:text-slate-200">
    </div>
</div>
```

- [ ] **Step 2: Commit**

```bash
git add core/templates/core/visit_log_form.html
git commit -m "feat: add participant_count input to visit log form"
```

---

### Task 4: Add participant aggregation to dashboard view

**Files:**
- Modify: `core/views.py`

- [ ] **Step 1: Add aggregation to GlobalDashboardView.get_context_data()**

In `core/views.py`, inside `GlobalDashboardView.get_context_data()` (after the existing aggregation block, around line 123), add:

```python
# Participant Count
total_participants = VisitLog.objects.aggregate(Sum('participant_count'))['participant_count__sum'] or 0
```

And in the `context.update({...})` dict (around line 175), add:

```python
'total_participants': total_participants,
```

- [ ] **Step 2: Commit**

```bash
git add core/views.py
git commit -m "feat: add participant_count aggregation to dashboard view"
```

---

### Task 5: Write participant_count dashboard tests (TDD)

**Files:**
- Modify: `core/tests/test_dashboard.py`

- [ ] **Step 1: Add test for participant aggregation**

Add these test methods to the `DashboardTests` class:

```python
def test_participant_count_aggregation(self):
    """Dashboard should sum participant_count across all visits."""
    v1 = VisitLog.objects.create(section=self.section1, date=timezone.now().date(), participant_count=5)
    v2 = VisitLog.objects.create(section=self.section2, date=timezone.now().date(), participant_count=3)
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
```

- [ ] **Step 2: Run tests — expect FAIL**

```bash
python manage.py test core.tests.test_dashboard.DashboardTests.test_participant_count_aggregation -v 2
python manage.py test core.tests.test_dashboard.DashboardTests.test_participant_count_defaults_to_zero -v 2
```

Expected: FAIL (Task 4 already added the aggregation, so these may actually PASS after Task 4 — run them now to verify)

- [ ] **Step 3: Run full test suite**

```bash
python manage.py test core.tests.test_dashboard -v 2
```

Expected: All tests PASS

- [ ] **Step 4: Commit**

```bash
git add core/tests/test_dashboard.py
git commit -m "test: add participant_count dashboard aggregation tests"
```

---

### Task 6: Add participant stat card to dashboard template

**Files:**
- Modify: `core/templates/core/dashboard.html`

- [ ] **Step 1: Change grid to lg:grid-cols-4**

On line 39, change:
```html
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
```
To:
```html
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
```

- [ ] **Step 2: Add Participants card**

Insert after the Litter card (after the closing `</div>` of the first stat-card, around line 51):

```html
<div class="stat-card border-t-4 border-t-purple-500">
    <div class="flex justify-between items-start mb-4">
        <span class="p-2 bg-purple-50 dark:bg-purple-900/30 rounded-lg text-purple-600 dark:text-purple-400">
            <span class="material-symbols-outlined">groups</span>
        </span>
        <span class="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Participation</span>
    </div>
    <div class="text-3xl font-bold text-slate-900 dark:text-white mb-1">{{ total_participants }} <span class="text-sm font-medium text-slate-400 uppercase">People</span></div>
    <p class="text-[10px] text-slate-500 font-medium uppercase tracking-wider">Total volunteers across all visits</p>
</div>
```

- [ ] **Step 3: Run tests**

```bash
python manage.py test core.tests.test_dashboard -v 2
```

Expected: All PASS

- [ ] **Step 4: Commit**

```bash
git add core/templates/core/dashboard.html
git commit -m "feat: add participant count stat card to dashboard"
```

---

### Task 7: Replace litter bag +/- buttons with typeable number inputs

**Files:**
- Modify: `core/templates/core/visit_log_form.html`

- [ ] **Step 1: Replace General Litter counter UI with number input**

Remove the entire `flex items-center justify-center gap-4 md:gap-6` div (buttons + display span) for General Litter, and change the hidden input to a visible number input.

**Before** (lines ~213-224):
```html
<div class="flex items-center justify-center gap-4 md:gap-6">
    <button type="button" onclick="updateCounter('litter_general', -1)" class="counter-btn w-12 h-12 md:w-10 md:h-10 rounded-full border-2 border-slate-300 dark:border-slate-600 flex items-center justify-center text-slate-500 hover:bg-white dark:hover:bg-slate-700 transition-colors active:bg-slate-100" data-testid="counter-btn" aria-label="Decrease general litter count">
        <span class="material-symbols-outlined text-xl">remove</span>
    </button>
    <span class="text-2xl md:text-3xl font-bold dark:text-white min-w-[3rem]" id="litter_general_value">{{ metric_formset.0.value.value|default:0 }}</span>
    <button type="button" onclick="updateCounter('litter_general', 1)" class="counter-btn w-12 h-12 md:w-10 md:h-10 rounded-full border-2 border-slate-300 dark:border-slate-600 flex items-center justify-center text-slate-500 hover:bg-white dark:hover:bg-slate-700 transition-colors active:bg-slate-100" data-testid="counter-btn" aria-label="Increase general litter count">
        <span class="material-symbols-outlined text-xl">add</span>
    </button>
</div>
<input type="hidden" name="metrics-0-metric_type" value="litter_general">
<input type="hidden" name="metrics-0-label" value="General Litter">
<input type="hidden" name="metrics-0-value" id="litter_general_input" value="{{ metric_formset.0.value.value|default:0 }}">
```

**After:**
```html
<input type="number" name="metrics-0-value" min="0" value="{{ metric_formset.0.value.value|default:0 }}"
       class="w-24 px-0 py-2 text-center text-2xl md:text-3xl font-bold bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary dark:text-white appearance-none">
<input type="hidden" name="metrics-0-metric_type" value="litter_general">
<input type="hidden" name="metrics-0-label" value="General Litter">
```

- [ ] **Step 2: Replace Recyclable Litter counter UI with number input**

Same pattern — remove buttons + display span, change hidden input to visible number input:

**Before** (lines ~231-241):
```html
<div class="flex items-center justify-center gap-4 md:gap-6">
    <button type="button" onclick="updateCounter('litter_recyclable', -1)" class="counter-btn w-12 h-12 md:w-10 md:h-10 rounded-full border-2 border-slate-300 dark:border-slate-600 flex items-center justify-center text-slate-500 hover:bg-white dark:hover:bg-slate-700 transition-colors active:bg-slate-100" data-testid="counter-btn" aria-label="Decrease recyclable litter count">
        <span class="material-symbols-outlined text-xl">remove</span>
    </button>
    <span class="text-2xl md:text-3xl font-bold dark:text-white min-w-[3rem]" id="litter_recyclable_value">{{ metric_formset.1.value.value|default:0 }}</span>
    <button type="button" onclick="updateCounter('litter_recyclable', 1)" class="counter-btn w-12 h-12 md:w-10 md:h-10 rounded-full border-2 border-slate-300 dark:border-slate-600 flex items-center justify-center text-slate-500 hover:bg-white dark:hover:bg-slate-700 transition-colors active:bg-slate-100" data-testid="counter-btn" aria-label="Increase recyclable litter count">
        <span class="material-symbols-outlined text-xl">add</span>
    </button>
</div>
<input type="hidden" name="metrics-1-metric_type" value="litter_recyclable">
<input type="hidden" name="metrics-1-label" value="Recyclable Litter">
<input type="hidden" name="metrics-1-value" id="litter_recyclable_input" value="{{ metric_formset.1.value.value|default:0 }}">
```

**After:**
```html
<input type="number" name="metrics-1-value" min="0" value="{{ metric_formset.1.value.value|default:0 }}"
       class="w-24 px-0 py-2 text-center text-2xl md:text-3xl font-bold bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary dark:text-white appearance-none">
<input type="hidden" name="metrics-1-metric_type" value="litter_recyclable">
<input type="hidden" name="metrics-1-label" value="Recyclable Litter">
```

- [ ] **Step 3: Clean up litter counters from JS**

In the `counters` object init (around lines 372-376), remove the two litter entries:

**Before:**
```javascript
const counters = {
    litter_general: 0,
    litter_recyclable: 0,
    metric_2: 0 // First plant
};
```

**After:**
```javascript
const counters = {
    metric_2: 0 // First plant
};
```

- [ ] **Step 4: Commit**

```bash
git add core/templates/core/visit_log_form.html
git commit -m "feat: replace litter bag +/- buttons with typeable number inputs"
```

---

### Task 8: Final verification

- [ ] **Step 1: Run full test suite**

```bash
python manage.py test core -v 2
```

Expected: All tests PASS

- [ ] **Step 2: Run lint**

```bash
python lint.py
```

Expected: No errors

- [ ] **Step 3: Manual smoke test**

- Start dev server, log in
- Create a visit log with participants and litter values
- Verify dashboard shows participant count and updated litter totals
- Edit the visit log, change values, verify persistence

- [ ] **Step 4: Commit any final tweaks**

```bash
git add -A
git commit -m "chore: final verification and cleanup for participants + typeable litter"
```

---

## Complete File Map

| File | Change | Task |
|------|--------|------|
| `core/models.py` | Add `participant_count` field | Task 1 |
| `core/migrations/` | Auto-generated migration | Task 1 |
| `core/forms.py` | Add field + widget | Task 2 |
| `core/templates/core/visit_log_form.html` | Participant input + typeable litter inputs + JS cleanup | Tasks 3, 7 |
| `core/views.py` | Add aggregation to dashboard context | Task 4 |
| `core/templates/core/dashboard.html` | Grid layout + stat card | Task 6 |
| `core/tests/test_dashboard.py` | Participant aggregation tests | Task 5 |
| `tests/uat/participants-typeable_uat.md` | UAT scenarios | (pre-written) |
