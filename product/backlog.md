# Project Backlog: River Rehabilitation Management

> **Status:** 5 completed, 6 new items pending, ordered by complexity (2026-02-20)

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

## Completed Items

### 1. Feature: Enhanced Weeding Data Capture ✅ DONE
**Target:** `core/templates/core/visit_log_form.html`
- **Status:** Implemented
- **PRD:** `product/Done/weeding_data.md`
- **Implementation:** 
  - Added `('weed', 'Weeding / Removal')` to `Metric.METRIC_TYPE_CHOICES`
  - Created `addWeedMetric()` JavaScript function
  - Weeding section placed below Planting with +/- buttons

### 2. Feature: Monthly Calendar View ✅ DONE
**Target:** `core/templates/core/monthly_planner.html`
- **Status:** Implemented
- **PRD:** `product/Done/monthly_view.md`
- **Implementation:**
  - `MonthlyPlannerView` created in views.py
  - Calendar grid with Monday start
  - Task badges with section color coding
  - Toggle between Weekly/Monthly views

### 3. Feature: Time-Stamped Stage Tracking ✅ DONE
**Target:** `core/models.py` (Section), `core/templates/core/section_detail.html`
- **Status:** Implemented
- **PRD:** `product/Done/stage_tracking.md`
- **Implementation:**
  - `SectionStageHistory` model created
  - Automated capture on stage change
  - Timeline visualization on section detail

### 4. Feature: Global Activity Dashboard ("All Activities") ✅ DONE
**Target:** New View / Dashboard
- **Status:** Implemented
- **PRD:** `product/Done/dashboard.md`
- **Implementation:**
  - `GlobalDashboardView` at `/dashboard/`
  - Global impact counters (litter, plants, weeds)
  - Recent activity feed
  - Stage distribution breakdown

### 5. Feature: Task Template Management Interface ✅ DONE
**Target:** `core/templates/core/task_template_form.html`
- **Status:** Implemented
- **PRD:** `product/Done/template_management.md`
- **Implementation:**
  - `TaskTemplateListView`, `TaskTemplateCreateView`, `TaskTemplateUpdateView`, `TaskTemplateDeleteView`
  - CRUD at `/templates/`, `/templates/create/`, `/templates/<pk>/edit/`
  - Consistent styling with SectionForm

### 6. Feature: Highlight Current Date in Weekly Planner ✅ DONE
**Target:** `core/templates/core/weekly_planner.html`
- **Status:** Implemented
- **Implementation:**
  - Added today-highlight CSS class with light blue tint
  - Added `today` to WeeklyPlannerView context
  - Highlights both header day number and grid cells in Team/Manager rows

### 7. Feature: Relative Progress Bars for Lifecycle Stages ✅ DONE
**Target:** `core/templates/core/dashboard.html`, `core/views.py`
- **Status:** Implemented
- **Implementation:**
  - Added `percentage` field to each stage in stage_distribution
  - Each bar width = (stage count / max count) * 100%
  - Dashboard now shows relative distribution across stages

### 9. Feature: Remove Success Metrics Card ✅ DONE
**Target:** `core/templates/core/dashboard.html`
- **Status:** Implemented
- **Implementation:**
  - Removed the Success Metrics card that showed unclear "100%"
  - Updated grid from 4 columns to 3 columns

---

## New Backlog Items (Ordered by Complexity)

### LOW COMPLEXITY

*(No low complexity items remaining)*

---

### MEDIUM COMPLEXITY

#### 8. Feature: Edit Log Entry from Completed Task
**Target:** `core/templates/core/daily_agenda.html`, `core/views.py`
- **Complexity:** Medium
- **Requirement:** When editing a completed task, redirect to edit the Visit Log instead of the Task.
- **Details:**
  - If task `is_completed=True` and has an associated VisitLog, the Edit button should navigate to the VisitLog edit view
  - If task is not completed (pre-completion), continue to edit the Task as normal
  - Need to determine how to handle tasks completed without a VisitLog (fallback to Task edit)

#### 9. Feature: Remove Success Metrics Card
**Target:** `core/templates/core/dashboard.html`
- **Complexity:** Low
- **Requirement:** Remove the "Success Metrics" card from the dashboard.
- **Details:**
  - Card shows unclear "100%" with "All section data validated"
  - Simply remove the card entirely

#### 10. Feature: Sections with Recent Activity on Dashboard
**Target:** `core/templates/core/dashboard.html`, `core/views.py`
- **Complexity:** Medium
- **Requirement:** Show sections that have recent activity in addition to the activity feed.
- **Details:**
  - Add a section showing "Active Sections" or "Sections with Recent Activity"
  - Display as a list or grid of section cards with their color codes
  - Show last activity date for each section
  - Complements the existing activity feed by highlighting which sections are engaged

---

### HIGH COMPLEXITY

#### 11. Feature: Detailed Planting Metrics on Dashboard
**Target:** `core/templates/core/dashboard.html`, `core/views.py`
- **Complexity:** High
- **Requirement:** Separate indigenous planting into number of species and number of individuals per species.
- **Details:**
  - Show total number of unique species planted
  - Show top 5 species breakdown (e.g., "Restio: 150, Bulbinella: 80, etc.")
  - Current display shows only total plants count
  - Update the Re-Planting card to display this detailed info

---

**Complexity Rating (New Items):**
- **Low:** (None remaining)
- **Medium:** Items 8, 10
- **High:** Item 11

---

**Next Steps:**
1. Review implemented features for any refinements needed
2. Consider new features for the backlog
3. Begin testing and user feedback collection
