# Project Backlog: River Rehabilitation Management

> **Last Updated:** 2026-08-11
> **Status:** Foundation sprint in progress. Backlog consolidated from `backlog_v1.md` (Jess's production feedback) and Sarah's latest requests.

---

## Current Sprint: Foundation Stabilization

See `product/context/prinicples/consolidated-sprint-plan.html` for the full plan. This sprint focuses on docs hygiene, code quality fixes, Kanban bug fix, ops tooling, and performance enforcement. No user-facing features this sprint.

---

## Next Sprint (from `progress_log.json` next_three_steps)

These are the next user-facing features once foundations are stable:

### 1. Playwright E2E Testing
**Priority:** High | **Complexity:** High
- End-to-end integration tests for complex UI flows (planners, modals, Kanban drag-and-drop)
- Builds confidence for refactoring planner templates and extracting partials

### 2. Enhanced Weeding Data Capture
**Priority:** Medium | **Complexity:** Medium
- Species-specific removal tracking mirroring the existing planting interface
- Multiple species entries per log with quantity tracking
- Maintain the "Forest Green" aesthetic with +/- tactile buttons

### 3. Stage Tracking Visualization
**Priority:** Medium | **Complexity:** Medium
- Polished timeline visualization for section stage history
- `SectionStageHistory` model already exists — this is the UI layer

---

## Production Feedback Backlog

Items from Jess (first week of production use) and Sarah's latest request list. Each should get its own PRD before implementation.

### 4. Quick Log from Planner
**Source:** Jess (`backlog_v1.md` #1) | **Complexity:** Medium
- "New Log" button on planner pages next to "New Task"
- Log unplanned activities without navigating to Sections or creating a Task first
- Refinement needed: date default, section pre-population

### 5. Impact Overview — Participant Count
**Source:** Sarah #2 | **Complexity:** Low
- Add a metric for number of participants alongside existing plants, litter bags, etc.
- Surface on the global impact dashboard

### 6. Planner — Tick to Complete + Log
**Source:** Sarah #3 | **Complexity:** Medium
- Complete tasks on planner with a tick (not just log-and-complete flow)
- Streamline the completion workflow from the planner views

### 7. Impact Dashboard — Typeable Litter Bag Count
**Source:** Sarah #4 | **Complexity:** Low
- Replace +/- click counters with typeable number inputs for litter bags
- Speeds up data entry for large counts

### 8. Planner Activity → Section/Lifecycle Indicators
**Source:** Sarah #5 | **Complexity:** Medium-High
- If a section has tasks this week (planting, weeding, etc.), show those task types as indicators next to the section name
- Same for lifecycle progress boxes — reflect current week's activities
- Needs PRD: query pattern, template changes, performance consideration

### 9. Export Planner to Excel
**Source:** Sarah #6 | **Complexity:** Medium
- Export the weekly/monthly planner view to Excel
- Builds on existing Excel export infrastructure

---

## Remaining from Original Backlog

Items from the original `backlog.md` that are still pending:

### 10. Edit Log Entry from Completed Task
**Complexity:** Medium
- When editing a completed task, redirect to edit the Visit Log instead of the Task
- If task `is_completed=True` and has an associated VisitLog, navigate to VisitLog edit
- Fallback to Task edit if no VisitLog exists

### 11. Sections with Recent Activity on Dashboard
**Complexity:** Medium
- Show "Active Sections" on the global dashboard as a list/grid with color codes
- Display last activity date per section
- Complements the existing activity feed

### 12. Detailed Planting Metrics on Dashboard
**Complexity:** High
- Separate indigenous planting into number of species vs. individuals per species
- Show top 5 species breakdown (e.g., "Restio: 150, Bulbinella: 80")
- Update the Re-Planting card to display detailed info

---

## Completed (Archive)

These items were implemented between Feb–Mar 2026 and are documented in `product/Done/`:

| # | Feature | PRD |
|---|---------|-----|
| 1 | Enhanced Weeding Data Capture (basic) | `product/Done/weeding_data.md` |
| 2 | Monthly Calendar View | `product/Done/monthly_view.md` |
| 3 | Time-Stamped Stage Tracking (basic) | `product/Done/stage_tracking.md` |
| 4 | Global Activity Dashboard | `product/Done/dashboard.md` |
| 5 | Task Template Management Interface | `product/Done/template_management.md` |
| 6 | Highlight Current Date in Weekly Planner | — |
| 7 | Relative Progress Bars for Lifecycle Stages | — |
| 8 | Remove Success Metrics Card | — |
| 9 | Chairperson Role Integration | — |
| 10 | Multi-Day Task Series | — |
| 11 | Data Export to Excel | — |
| 12 | Global Rolling To-Do List (Kanban) | — |
| 13 | Mobile Responsive Layout | — |
| 14 | Redirect Context Preservation | — |

---

**Next Steps:**
1. Complete Foundation Stabilization Sprint
2. Write PRDs for items 4–9 (production feedback) and items 1–3 (next sprint)
3. Begin next sprint with Playwright E2E → Enhanced Weeding → Stage Tracking Viz
