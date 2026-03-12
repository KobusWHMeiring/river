# Project Backlog v1: Production Feedback & Enhancements

> **Date:** 2026-03-11
> **Context:** First week of production usage feedback (v1.0)

This backlog captures the immediate needs identified by Jess and the team after the first week of real-world use.

---

## 1. Feature: 'Quick Log' from Planner
**Target:** `core/templates/core/weekly_planner.html`, `core/templates/core/monthly_planner.html`
- **Requirement:** Add a "New Log" button directly on the planner pages next to the "New Task" button.
- **Goal:** Allow users to log unplanned activities immediately without needing to navigate to the Sections page or create a Task first.
- **Refinement Questions:**
  - Should the "New Log" button default the date to "Today" or the first day of the currently viewed week/month?
  - When clicking "New Log" from a specific day in the grid (if we add it there), should it pre-populate that day's date?
  - Should we maintain a "General" log option for logs not tied to a specific section, or is a section always mandatory?

## 2. Feature: Global Rolling To-Do List
**Target:** New View (`/todo/`), `core/models.py`
- **Requirement:** A dedicated "To-Do List" page for tasks that aren't tied to a specific date or section and can be "ticked off" as they are completed.
- **Goal:** Manage high-priority rolling items that don't fit into the daily/weekly schedule.
- **Refinement Questions:**
  - **Priority:** What priority levels are needed? (e.g., Low, Medium, High, Urgent). Should these be color-coded?
  - **Section Tie:** If a task is not tied to a section, should it still be visible on the Global Dashboard?
  - **Integration:** Should these "Rolling Tasks" appear at the top of the "Daily Agenda" until completed?
  - **Task Model:** Should we expand the existing `Task` model with a `priority` and `is_rolling` flag, or create a separate `TodoItem` model?

## 3. Feature: Multi-Day Tasks (Task Duration)
**Target:** `core/models.py`, `core/forms.py`, Planner Views
- **Requirement:** Allow tasks to have a start and end date so they can "roll over" for several days (e.g., a whole week of weeding in Section A).
- **Goal:** Reduce repetitive data entry for multi-day operations.
- **Refinement Questions:**
  - **Completion Logic:** If a task spans 5 days, does ticking it off on Monday complete the *entire* block, or should it create 5 individual task instances?
  - **Visuals:** In the Monthly Planner, should this appear as a continuous bar (Gantt style) or as repeating badges on each day?
  - **Editing:** If a user edits the instructions for a multi-day task, should it update all days in that range?

## 4. Feature: Data Export for Reporting
**Target:** `core/views.py`, Dashboard, Section List
- **Requirement:** Functional "Export" buttons on the Sections list and the Global Dashboard to assist with donor reporting.
- **Goal:** Enable managers to extract raw data and summaries for external reports.
- **Refinement Questions:**
  - **Format:** What is the preferred format? (CSV for data analysis, Excel for easy reading, or PDF for "ready-to-send" reports?)
  - **Dashboard Export:** Should this be a summary of the current view (counters and charts) or a dump of all logs in the selected period?
  - **Filtering:** Do we need to allow users to select a specific date range (e.g., "Last Quarter") before exporting?
  - **Metrics:** Should the export include photo links or just text/numeric data?

---

## Priority Ranking (Suggested)

1. **Export Functionality (High):** Critical for donor reporting and data safety.
2. **Quick Log (Medium):** High frequency UX improvement for field workers.
3. **Multi-Day Tasks (Medium):** Significant time-saver for managers during weekly planning.
4. **To-Do List (Low):** New workflow addition that requires structural decisions.
