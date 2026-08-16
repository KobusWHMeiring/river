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
