# Project Backlog: River Rehabilitation Management

This backlog tracks upcoming features and enhancements requested by the client. These items will be decomposed into PRDs and Technical User Stories in the next phase.

## 1. Feature: Enhanced Weeding Data Capture
**Target:** `core/templates/core/visit_log_form.html`
- **Requirement:** Implement a "Removal" (Weeding) interface that mirrors the existing "Planting" interface.
- **Details:**
  - Allow users to record specific plant species being removed.
  - Support multiple species entries per log.
  - Track quantity or bags removed for each species.
  - Maintain the "Forest Green" aesthetic with +/- tactile buttons.

## 2. Feature: Monthly Calendar View
**Target:** `core/templates/core/weekly_planner.html`
- **Requirement:** Expand the planning capabilities from a 7-day view to a full month view.
- **Details:**
  - Provide a high-level overview of scheduled tasks across the month.
  - Maintain the Team/Manager row distinction if feasible in a monthly grid, or use a summarized status indicator.
  - Navigation between months.

## 3. Feature: Time-Stamped Stage Tracking
**Target:** `core/models.py` (Section), `core/templates/core/section_detail.html`
- **Requirement:** Track and visualize the history of a section's "Lifecycle Stage" transitions.
- **Details:**
  - Create a historical log whenever a section's `current_stage` is updated.
  - Store the timestamp, the old stage, and the new stage.
  - Visualize these changes on the section's timeline view to show progress over time (e.g., "3 months in Clearing", "Transitioned to Planting on 2026-01-15").

## 4. Feature: Global Activity Dashboard ("All Activities")
**Target:** New View / Dashboard
- **Requirement:** A centralized "Star" dashboard providing an overview of all activities across the entire river.
- **Details:**
  - High-level insights: Total bags collected, total plants planted, total weeding sessions.
  - Cross-section comparisons.
  - This dashboard will serve as the foundation for future analytics and ecological reporting.

## 5. Feature: Task Template Management Interface
**Target:** `core/templates/core/task_template_form.html`
- **Requirement:** Create a user-facing interface for managing `TaskTemplate` entries.
- **Details:**
  - Move template management from the Django Admin to the core application UI.
  - Allow managers to edit existing templates (Names, Types, Default Instructions).
  - Create new templates or retire old ones.
  - Ensure the interface is consistent with the `TaskForm` and `SectionForm` styling.

---
**Next Steps:**
1. Select a high-priority item from the backlog.
2. Generate a PRD in the `product/Ready/` folder.
3. Decompose into User Stories using the `po.md` protocol.
