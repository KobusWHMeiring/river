# PRD: Master Activity Log ("View All Logs")

## 1. Problem Statement
Currently, visit logs are fragmented. They appear as a "Top 15" list on the Dashboard or are tucked away inside individual Section Detail pages. There is no central "Master Log" where a manager can browse, search, or audit the entire history of work across the whole river without section-specific filters.

## 2. Strategic Goal
To provide a comprehensive, searchable, and paginated "Master Audit Trail" of all project activities, ensuring absolute transparency and making it easy to find specific historical records across any date range or section.

## 3. Proposed Scope
- **Full History List:** A paginated view of every `VisitLog` entry in the system.
- **Global Search:** Search through notes, section names, and task descriptions.
- **Filtering:** 
  - Filter by Section.
  - Filter by Date Range (Start/End).
  - Filter by Activity Type (Planned vs. Unplanned).
- **Rich List Items:** Each row should show section badges, primary metrics (litter, plants, weeds), and photo thumbnails, mirroring the dashboard's "Recent Activity" style but optimized for a list.

## 4. Technical Constraints
- **Performance:** Use Django's `ListView` with `paginate_by` (e.g., 25 logs per page).
- **Query Optimization:** Heavy use of `select_related('section', 'task')` and `prefetch_related('metrics', 'photos')` to prevent N+1 query issues.
- **UI Consistency:** Reuse the "Activity Feed" component styling from the Dashboard for familiarity.

## 5. Implementation Details

### URL Structure
- `/visit-logs/` - The main paginated list.
- Supports query parameters for filtering: `?section=5&start_date=2026-01-01&q=litter`.

### Search Logic
Search should be "fuzzy" across the `notes` field and the `section__name`.

### Visual Design
- Maintain the "Subtle & Professional" aesthetic.
- Use the same section-color badges as the rest of the app.
- Ensure the "View All Logs" button on the Dashboard links directly to this page.

---

# User Stories

## Story 1: The Master Audit Trail
**Value Proposition:** As a Manager, I want a single place to see all work history, so that I can prepare for annual reporting or audits without jumping between 20 different section pages.
**AC:**
- [ ] View displays all logs in reverse chronological order.
- [ ] Pagination allows navigation through hundreds of records without performance lag.

## Story 2: Global Search and Filtering
**Value Proposition:** As a Manager, I want to find every time we mentioned "wildlife" or "spill" across the entire river, so I can track environmental incidents geographically.
**AC:**
- [ ] Search bar filters the list in real-time or on submit.
- [ ] Date range filters correctly bound the results.

## Story 3: Deep Link Integration
**Value Proposition:** As a Supervisor, I want to click "View All Logs" from my dashboard and see the full history immediately, so I can find an entry from last month that I need to edit.
**AC:**
- [ ] Dashboard button is functional.
- [ ] Each log in the list links back to the Section Detail timeline or a dedicated log detail view.
