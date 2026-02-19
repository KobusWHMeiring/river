# PRD: Context-Aware Visit Logging

## 1. Problem Statement
The current "Log Activity" form is a "one-size-fits-all" interface. Regardless of whether a team is performing a "Litter Run" or "Deep Weeding," they see the same list of fields. This creates visual clutter and requires repetitive typing of species names or notes that were already defined in the planning phase.

## 2. Strategic Goal
To create a "Smart Form" that adapts its UI and pre-populates data based on the **Task Type**. This reduces field-entry time by ~50% and ensures that data collection is focused on the specific goals of the planned task.

## 3. Proposed Scope
- **Dynamic UI Sections (Priority Weighting):** Automatically expand the most relevant metric block based on `task_type` and collapse others to reduce scroll length.
- **Note Pre-population:** Automatically copy the `task.instructions` into the `visit_log.notes` field.
- **Admin Optimization:** For tasks categorized as "Admin," hide the metrics section entirely to provide a clean reporting interface for meetings or site inspections.
- **Header Context:** Display a summary of the planned task at the top of the form for reference.

## 4. Technical Constraints
- **Flexibility:** Collapsed sections must remain accessible (expandable) in case a team performs secondary work (e.g., finding litter during a weeding shift).
- **Template Integration:** Use the `task_type` from the linked `TaskTemplate` to drive the initial state of the form.

## 5. Implementation Details

### Mapping Logic (Initial Form State)
| Task Type | Litter Section | Weeding Section | Planting Section |
| :--- | :--- | :--- | :--- |
| **Litter Run** | Expanded | Collapsed | Collapsed |
| **Weeding** | Collapsed | Expanded | Collapsed |
| **Planting** | Collapsed | Collapsed | Expanded |
| **Admin** | Hidden | Hidden | Hidden |
| **Unplanned** | Expanded | Expanded | Expanded |

### Note Prefill Strategy
When the form loads with a `task_id`, the `notes` textarea should be initialized with the raw `task.instructions`. The field remains fully editable, allowing the user to append their specific observations or "as-built" details.

---

# User Stories

## Story 1: Focus-First Weeding
**Value Proposition:** As a Supervisor, when I log a "Weeding" task, I want the weeding counters front-and-center so I can start logging immediately, but still be able to log the 2 bags of litter we found.
**AC:**
- [ ] Weeding section is expanded by default for `task_type == 'weeding'`.
- [ ] Litter section is collapsed but can be toggled open.

## Story 2: Clean Admin Reporting
**Value Proposition:** As a Manager, when I'm logging an "Admin" site visit, I don't want to see any bag or plant counters, so the form remains professional and uncluttered.
**AC:**
- [ ] All metric sections are hidden when `task_type == 'admin'`.
- [ ] Form displays only the Notes and Photo upload areas.

## Story 3: Contextual Continuity
**Value Proposition:** As a Team Member, I don't want to re-type the work description I already saw in the planner.
**AC:**
- [ ] The `notes` field is pre-filled with the task's instructions upon page load.
- [ ] The user can edit or delete this text if the work performed differed from the plan.
