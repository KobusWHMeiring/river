# PRD: Planner Interaction Update (Context-Aware Navigation)

## 1. Problem Statement
The current interaction model for the Weekly Planner requires users to find specific small buttons (like the '+' icon) or click exactly on a task title. This can be cumbersome on mobile or for quick planning.

## 2. Strategic Goal
To simplify navigation by making entire "Day Cells" interactive. The system will intelligently decide whether to take the user to the **Daily Agenda** (to view/complete work) or the **Add Task** screen (to plan work) based on the cell's content.

## 3. Proposed Scope
- **Weekly Planner Update:** 
  - If a day/section cell contains tasks: Clicking anywhere in that cell navigates to the `DailyAgendaView` for that date.
  - If a cell is empty: Clicking the cell opens the `TaskCreate` modal/form.
- **Monthly Planner Parity:** The same logic applies to the larger calendar grid.
- **Visual Feedback:** Cells should have a subtle hover effect (pointer cursor, light background change) to indicate they are clickable.

## 4. Technical Constraints
- **Weekly Grid:** Since the weekly grid is organized by Section (Y-axis) and Day (X-axis), clicking an empty cell should auto-populate both the **Date** and the **Section** in the "Add Task" form.
- **Monthly Grid:** Since the monthly grid is organized by Day only, clicking an empty cell should auto-populate only the **Date**.

## 5. User Stories

### Story 1: "Quick View" Navigation
**Value Proposition:** As a Supervisor, I want to click on a day that has tasks and be taken straight to the agenda, so I can start marking things as complete without precise clicking.
**AC:**
- [ ] Entire cell area is clickable.
- [ ] Logic detects presence of tasks and routes to Daily Agenda.

### Story 2: "Quick Plan" Creation
**Value Proposition:** As a Manager, I want to click an empty slot in the schedule and immediately start typing a new task, so that planning feels fast and fluid.
**AC:**
- [ ] Clicking an empty cell opens the task creation interface.
- [ ] The Date and (if applicable) Section are pre-filled in the form.
