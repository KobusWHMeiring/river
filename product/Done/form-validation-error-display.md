# PRD: Form Validation Error Display (Required Fields Must Be Visible)

**Status:** In Refinement — problem identified 2026-08-16 (needs investigation + design)
**Source:** UAT session, 2026-08-16

## 1. Problem Statement

Several forms in the app can fail validation in ways that are invisible or misleading to the user:

- Errors reference fields that are **not rendered on the form** (hidden or conditionally excluded), so the user cannot fix them.
- Some submissions fail silently — the page reloads with no error message — because form/formset validation errors are never rendered.

**Concrete instance found during UAT (2026-08-16):** On the Visit Log edit form for an *admin*-type task, the Metrics section is hidden (`{% if task_type != 'admin' %}`), but the client still submitted `TOTAL_FORMS=2` metric forms. The server then reported "metric_type required" / "value required" for two metric rows that were nowhere visible on the page.

## 2. Strategic Goal

Ensure that whenever a form fails validation, every error message maps to a field the user can actually see and fix — no phantom errors, no silent failures.

## 3. What We Know (Current Behaviour)

- `base.html` renders Django `messages`, and many views use `SuccessMessageMixin` — but **form-level and formset-level validation errors are rendered inconsistently** across templates.
- `core/templates/core/visit_log_form.html` renders `form.date` and `form.section` errors inline, but had **no** rendering of `form.errors`, `metric_formset` errors, or `photo_formset` errors (a banner was added 2026-08-16 as a stopgap).
- `Metric.metric_type` and `Metric.value` are required (`core/models.py`), but the metric inputs are hand-written in the template and conditionally hidden by `task_type`, while the client JS hardcodes `TOTAL_FORMS`.
- `task_complete_view` / `task_reopen_view` did **not** set a success message after saving (a toast was added 2026-08-16 as a stopgap).

## 4. Proposed Scope

- **Audit all forms** (VisitLog create/edit, task create/edit, template management, section forms, photo/metric formsets, login, etc.) for:
  1. Validation errors that are not rendered at all.
  2. Required fields that can be hidden/absent while still submitted (or expected but not rendered).
  3. Success/error feedback consistency (toasts/messages after save).
- **Standardise error rendering** — a shared, accessible error-summary pattern (banner + inline field errors) so no validation failure is silent.
- **Align conditional rendering with validation** — fields hidden by task type/context must not be required; formsets must not expect forms that aren't rendered.

### Explicitly Out of Scope (initial)
- Redesigning form layouts.
- Changing data models or validation rules (only fixing *display* of existing rules, unless a rule itself is wrong).

## 5. Open Questions / Decisions Needed

- Which forms are in scope? (audit needed to enumerate)
- Should hidden-but-required fields be made visible, or made optional/handled server-side?
- One shared error-banner partial vs. per-template markup?
- Is the admin-task metric case fixed by the `TOTAL_FORMS=0` client fix alone, or is a server-side guard also needed?

## 6. Known Related Work (this session, 2026-08-16)

- `task_complete_view` / `task_reopen_view`: success toast added.
- `visit_log_form.html`: error banner added + admin-task `TOTAL_FORMS` fix.
- New regression tests: `core/tests/test_visit_log_form.py`.

---

## 2026-08-16 Form Validation Error Display — Design

### Decisions (from refinement)
1. **Server-side guard for admin-task metrics (option B).** When the resolved task type is `admin`, the visit-log views neutralise the metric formset (validate/save nothing) so phantom metric forms can never fail validation, even if a stale client sends `TOTAL_FORMS > 0`.
2. **Standardisation via a Django inclusion tag (option B).** Error-flattening logic lives in Python (`render_form_errors`), feeding a shared partial — per BUILD PRINCIPLES §I "No Logic in Templates".
3. **Scope.** Fix the visit-log phantom-error case first, then standardise error display across all five form templates (`visit_log_form`, `section_form`, `task_form`, `task_template_form`, `task_type_form`).

### Architecture
- New inclusion tag `{% render_form_errors form [formset ...] %}` flattens `form.non_field_errors()`, per-field errors (with human label + `#id_<field>` anchor), and each formset's `non_form_errors` + per-form field errors into one list.
- A shared partial `core/templates/core/includes/form_errors.html` renders an accessible banner (`role="alert"`, `aria-live="assertive"`, `data-testid="form-errors"`) and renders nothing when there are no errors.
- `resolve_task_type(task)` helper (in `core/services/task_services.py`) centralises the `task.template.task_type.code or 'unplanned'` logic used by both views.

### Components / File map
- **New:** `core/templatetags/form_tags.py` — the `render_form_errors` inclusion tag.
- **New:** `core/templates/core/includes/form_errors.html` — the shared error-summary banner partial.
- **Edit:** `core/services/task_services.py` — add `resolve_task_type(task) -> str`.
- **Edit:** `core/views.py` — use the helper in both visit-log views; add the admin guard in `form_valid`; remove leftover `print("[DEBUG] …")` statements.
- **Edit:** `core/templates/core/visit_log_form.html` — replace the inline stopgap banner with the tag; add the two missing inline errors (`notes`, `participant_count`) and an `id` on the participant input.
- **Edit:** `core/templates/core/section_form.html`, `task_form.html`, `task_template_form.html`, `task_type_form.html` — add `{% load form_tags %}` + `{% render_form_errors form %}` after `{% csrf_token %}`.
- **Edit:** `core/tests/test_visit_log_form.py` — update the admin metric test to assert the guard (302, 0 metrics) and add a non-admin photo-error test; add `core/tests/test_form_errors.py` for the tag.

### Data flow
Submit → view resolves the final task type from `form.cleaned_data['task']` → if `admin`, replace `metric_formset` with an empty `MetricFormSet()` → validation proceeds (photos unaffected) → save skips metrics. Non-admin → formset validated as today → any error surfaces in the banner + inline.

### Error handling & accessibility
Banner announces all errors with field anchor links; inline errors remain next to inputs; no silent failures.

### Testing
- `test_admin_task_edit_ignores_phantom_metrics`: admin task + stale `TOTAL_FORMS=2` + no metric data → 302, 0 metrics.
- `test_non_admin_photo_error_renders_banner`: non-admin log + photo with short description → 200 + banner with the description error.
- `test_form_errors.py`: unit-test the tag with an invalid `TaskForm` (label + anchor) and an invalid `MetricFormSet` ("Metrics 1 · Metric type" label).

### Risks / Explicitly out of scope
- Litter/plant metric index-mapping edge case (forms 0/1 assumed to be litter) — theoretical; separate investigation.
- Model-level uniqueness (e.g. duplicate `TaskType.name` → 500) — a validation rule, not display.
- Extracting formset-save logic into a service — larger refactor, not needed for this fix.
- Redesigning form layouts or changing data models / validation rules.
