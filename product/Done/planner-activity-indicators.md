# PRD: Planner Activity → Section/Lifecycle Indicators

## 1. Problem Statement

Currently, when viewing the Global Impact Dashboard, a manager can see which sections have been active recently (via the Active Sections list) and how sections are distributed across lifecycle stages (via the Lifecycle Progress bars). However, there is no way to see **what activities are planned for this week** without navigating into each section or the planner. Sarah wants to know at a glance: "What's happening this week on each section?"

## 2. Strategic Goal

Surface current-week task activity on the dashboard's Active Sections list and Lifecycle Progress bars, so managers can assess this week's workload distribution across sections and stages without leaving the dashboard.

## 3. Proposed Scope

- **Active Sections List:** For each section with tasks this week, show colored text tags indicating the task types (Litter, Weed, Plant, Admin).
- **Lifecycle Progress Bars:** For each stage, show colored text tags indicating the task types active across all sections in that stage this week (field types only — no Admin).
- **Time Window:** Calendar week (Monday–Sunday), matching the planner.
- **Visual Style:** Compact colored text tags (Option C from design options — see `product/designs/planner-activity-indicators-options.html`).

### Explicitly Out of Scope
- Changing the planner views (weekly/monthly)
- Section list or section detail pages
- Rolling to-do (Kanban) tasks
- Planner export or any other feature

## 4. Design Decisions

| Decision | Rationale |
|----------|-----------|
| Calendar week (Mon–Sun) | Matches planner week; avoids "last 7 days" confusion mid-week |
| Include completed tasks | Indicator reflects the week's plan, not remaining work |
| Skip tasks with no template | No `TaskType.code` = nothing meaningful to label |
| Skip tasks with no section | Section-less tasks are the planner's "Admin" convention (`task.section=None`); no section/stage to key on, so excluded from both lists |
| Filter Admin from Lifecycle bars | Admin tasks aren't field-relevant for stage classification |
| Colored text tags | Most accessible, matches existing dashboard badge patterns |
| In-view aggregation (no new service file) | Single-use dashboard context; YAGNI. Extract later if reused. |

## 5. Technical Constraints

- **Query pattern:** One additional query on `Task` filtered by date range, with `.select_related('template__task_type', 'section')`. Rolling tasks (`is_rolling=True`) are excluded.
- **Aggregation:** Build `{section_id: set(task_type_codes)}` dicts in Python — one for Active Sections, one for Lifecycle stages (grouped by `section.current_stage`). Guard `task.section is None` (section-less "Admin" tasks) and skip them from both dicts.
- **Template:** Add indicator tags to existing `dashboard.html` — no new templates.
- **Performance:** The current dashboard view already queries `Task` for other purposes — this adds a lightweight date-filtered query on ~8 sections' worth of planner tasks. Query count increase: ≤1.

---

# User Stories

## Story 1: Section Activity Tags on Active Sections List

**Value Proposition:** As a Manager viewing the dashboard, I want to see colored tags next to each active section showing what task types are scheduled this week, so I can assess workload distribution at a glance.

**Technical Implementation Path:**
- Target File: `core/views.py` — `DashboardView.get_context_data()`
  - Add query: `Task.objects.filter(date__range=[mon, sun], is_rolling=False).select_related('template__task_type', 'section')`
  - Build `section_weekly_activity: dict[int, list[str]]` — section ID → sorted list of unique task type codes
  - Build `stage_weekly_activity: dict[str, set[str]]` — stage key → set of task type codes across sections in that stage (field types only: litter_run, weeding, planting)
  - Guard `task.section is None` (section-less "Admin" tasks) before keying either dict — skip to avoid `AttributeError`
- Target File: `core/templates/core/dashboard.html`
  - In Active Sections loop, add indicator tags below section name
  - In Lifecycle Progress loop, add indicator tags above progress bars

**Acceptance Criteria (AC):**
- [ ] Dashboard Active Sections list shows colored task type tags for each section with scheduled tasks this week
- [ ] Sections with no tasks this week show no tags (consistent with existing layout)
- [ ] Tags use the existing dashboard color palette (red=Litter, amber=Weed, green=Plant, indigo=Admin)
- [ ] Tags are keyboard-accessible and screen-reader friendly (text-based)

**The Test Plan (MANDATORY):**
- **Unit Test:** `test_weekly_activity_aggregation`: Create tasks for 2 sections with different types this week, 1 section with no tasks, 1 section with tasks next week. Verify `section_weekly_activity` dict has correct keys and task type sets.
- **Edge Case:** Section has only completed tasks → tags still appear.
- **Edge Case:** Section has tasks with no template → skipped, no "Custom" tag.
- **Edge Case:** Task with `section=None` (section-less "Admin" task) → skipped from both dicts, no crash, no tags.
- **Edge Case:** No sections have tasks this week → both dicts are empty, template renders no tags.

---

## Story 2: Activity Tags on Lifecycle Progress Bars

**Value Proposition:** As a Manager, I want to see what field activities are happening this week within each lifecycle stage, so I can see if, for example, the "Planting" stage sections have actual planting tasks scheduled.

**Technical Implementation Path:**
- Target File: `core/views.py` — same context data as Story 1
  - For each stage, collect task types across all sections currently in that stage
  - Filter to field types only (exclude `admin`)
- Target File: `core/templates/core/dashboard.html`
  - In Lifecycle Progress loop, add indicator tags above each progress bar

**Acceptance Criteria (AC):**
- [ ] Lifecycle Progress bars show field activity tags (Litter, Weed, Plant) when sections in that stage have corresponding tasks
- [ ] Admin tasks are excluded from lifecycle indicators
- [ ] Stages with no sections having tasks this week show no tags

**The Test Plan (MANDATORY):**
- **Unit Test:** `test_stage_weekly_activity`: Create 2 sections in "Planting" stage — one with a planting task, one with a weeding task. Verify stage dict shows both `planting` and `weeding` codes, but no `admin` even if an admin task exists.
- **Edge Case:** Task with `section=None` (section-less "Admin" task) → skipped from stage dict (no stage to attribute), no crash.
- **Edge Case:** A stage with zero sections → no entry in dict, no tags rendered.

---

## 6. File Map

| File | Change | Risk |
|------|--------|------|
| `core/views.py` | Add 2 queries + dict-building to `DashboardView.get_context_data()` | Low — additive context, no view logic change |
| `core/templates/core/dashboard.html` | Add tag HTML in Active Sections + Lifecycle Progress loops | Low — additive template code, no restructuring |
| `core/tests/test_dashboard.py` | Add unit tests for aggregation logic | None — new tests |
| `product/Done/planner_activity_indicators.md` | Move this PRD to Done on completion | None |

## 7. Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Query performance regression on dashboard | Low | One additional date-filtered query on Task. Dashboard already queries Task for other aggregations. 8 sections × ~5 tasks/week = negligible. |
| TaskType.code values diverge from tag colors | Low | Map uses explicit known codes; unknown codes are silently skipped. No crash. |
| Tags wrap on narrow viewports | Low | Use flex-wrap with small gap; tags are compact enough to fit even at mobile widths. Verify in Playwright when E2E infrastructure exists. |

---

## 8. Pre-Flight Checklist

- [x] Design options reviewed with stakeholder
- [x] Visual style confirmed (Option C: Colored Text Tags)
- [x] Edge cases resolved (no-template tasks, completed tasks, admin on lifecycle bars)
- [x] Query pattern validated against performance principles (§VI)
- [x] No new service file — single-use, YAGNI
- [x] No template restructuring — additive HTML only
- [x] Tests written and passing
- [ ] Manual visual verification on dashboard with production data

---

*Design appended 2026-08-11 — Planner Activity Indicators.*
*Design options reference: `product/designs/planner-activity-indicators-options.html`*
