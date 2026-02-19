# PRD: Weekly Planner Navigation

## 1. Problem Statement
The Weekly Planner currently shows only the current week and provides non-functional navigation buttons (Previous, Next, Current Week). Users cannot view past or future weeks to review historical plans or schedule ahead.

## 2. Strategic Goal
To enable temporal navigation within the Weekly Planner, allowing users to move seamlessly between weeks while maintaining the existing interactive day-cell functionality.

## 3. Proposed Scope
- **Week Navigation Controls:** Make the existing chevron buttons functional:
  - **Previous Week:** Navigate to the week immediately before the currently displayed week
  - **Next Week:** Navigate to the week immediately after the currently displayed week
  - **Current Week:** Return to the week containing today's date
- **Date Parameter Support:** Modify the `WeeklyPlannerView` to accept a `date` GET parameter (YYYY-MM-DD format) that determines which week to display
- **Week Display:** Update the week range display (e.g., "Feb 16 – Feb 22") to reflect the navigated week
- **Task Filtering:** Ensure tasks are filtered to the displayed week's date range

## 4. Technical Constraints
- **Parameter Consistency:** Use `date` parameter (matching `DailyAgendaView`) in `YYYY-MM-DD` format
- **Week Start Day:** Maintain Sunday as the week start (current behavior: `start_of_week = today - timedelta(days=today.weekday() + 1)`)
- **Fallback Logic:** Invalid or missing `date` parameters should default to the current week
- **URL Structure:** Navigation should work via simple GET requests (e.g., `/weekly-planner/?date=2026-02-09`)
- **Template Updates:** Convert static button elements to functional anchor tags with calculated URLs

## 5. User Stories

### Story 1: Week-to-Week Navigation
**Value Proposition:** As a Manager, I want to click Previous/Next buttons to see adjacent weeks, so I can review past work and plan for future weeks without waiting for time to pass.
**AC:**
- [ ] Clicking "Previous Week" (left chevron) loads the immediately preceding week
- [ ] Clicking "Next Week" (right chevron) loads the immediately following week
- [ ] The week range display updates to reflect the new week
- [ ] Tasks displayed are filtered to the selected week's date range

### Story 2: "Current Week" Reset
**Value Proposition:** As a Supervisor, I want a quick way to return to the current week after navigating to past/future weeks, so I can focus on today's priorities.
**AC:**
- [ ] Clicking "Current Week" loads the week containing today's date
- [ ] The button clears any `date` parameter from the URL
- [ ] Week range display shows the current week's dates
- [ ] All day-cell interactive behaviors (context-aware navigation) remain functional

### Story 3: Direct Week Access via URL
**Value Proposition:** As a Power User, I want to bookmark or share specific week views, so I can reference planning sessions or coordinate with team members.
**AC:**
- [ ] The `WeeklyPlannerView` accepts a `date` GET parameter
- [ ] Any valid date in `YYYY-MM-DD` format displays the containing week
- [ ] Invalid dates fall back to the current week
- [ ] The URL reflects the selected week (e.g., `?date=2026-02-09`)

---

**CRITICAL DECISION:**
Should the "Current Week" button:
1. Navigate to the week containing today's date (default behavior when no `date` parameter is present), OR
2. Explicitly clear any `date` parameter and reload the page without parameters?

**Recommendation:** Option 1 (navigate to today's week) is more intuitive—users expect "Current Week" to show this week regardless of URL state. This can be implemented by generating a URL with `date=today` rather than clearing the parameter.