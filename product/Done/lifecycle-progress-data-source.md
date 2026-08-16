# PRD: Lifecycle Progress Data Source (Community Stage)

**Status:** Done — Community stage hidden from the Lifecycle Progress widget (decision: remove for now)
**Source:** Sarah Schumann (Director), 2026-08-12

## 1. Problem Statement

Sarah asks where the dashboard's "Lifecycle Progress" stages pull their data from, and reports that community events (e.g. the "community planting day" task type) are not showing up as "Community" sections.

## 2. Strategic Goal

Clarify the data source of Lifecycle Progress, then make it correctly reflect community activity (either via a data fix or a small feature change).

## 3. What We Know (Current Behaviour — this answers the "where does it come from" question)

- **Lifecycle Progress is driven by `Section.current_stage`, NOT by task types or activity.**
- In `GlobalDashboardView.get_context_data()` (`core/views.py`), `stage_counts = Section.objects.values('current_stage').annotate(count=Count('id'))`, then `stage_distribution` is built from `Section.STAGE_CHOICES` (Mitigation, Clearing, Planting, Follow-up, Community). Each bar = number of *sections* whose `current_stage` field equals that stage.
- `Section.STAGE_CHOICES` **does include** `('community', 'Community')` (`core/models.py`).
- A task of type "community planting day" has **no effect** on the lifecycle bars — it only affects the task/planner and, if logged, the metrics. The "Community" bar will show `0 Sections` until at least one `Section` has `current_stage = 'community'`.

### Root cause
The most likely reason "no sections come up as community" is that **no `Section` record has `current_stage` set to `'community'`** — it's a data/classification issue, not a missing stage or missing feature. The director may also be conflating *task type* with *section lifecycle stage* (two different concepts in the model).

## 4. Proposed Options (for refinement discussion)

- **Option A — Data fix only (no code):** Reclassify the relevant sections to the `community` stage via the section edit form. Fastest; zero code.
- **Option B — Clarify + data fix:** Update dashboard copy to make clear Lifecycle Progress = section stage, and add a small "X sections in Community" hint or tooltip. Then reclassify sections.
- **Option C — Activity-derived community view (feature):** If Sarah actually wants community *activity* to surface independently of section stage, add a separate "Community activity" indicator (e.g. based on task types / logs) rather than changing the lifecycle bars.

## 5. Open Questions / Decisions Needed

1. Which sections should be in the **Community** stage? (List them.)
2. Is "community planting day" a distinct `TaskType` that should map to community activity, or is it just a template name? Check `TaskType`/`TaskTemplate` records.
3. Does Sarah want the lifecycle bars to stay **section-based** (current design) or become **activity-based**?
4. Is this a bug (data misclassified) or a feature (community activity tracking)? Recommend confirming before any code.

## 6. Success Criteria (high-level)

- The data source of Lifecycle Progress is documented and (if needed) clarified in the UI.
- Community events are correctly represented — either sections appear under "Community", or community activity is shown via the chosen approach.
- No confusion remains between task type and section stage.

## 7. Likely Touch Points

| Area | File | Note |
|------|------|------|
| Data | `Section` records / section edit form | Reclassify sections (Option A/B) |
| Dashboard view | `core/views.py` — `GlobalDashboardView` | Only if activity-derived (Option C) |
| Dashboard template | `core/templates/core/dashboard.html` | Copy/tooltip clarification |
| Task types | `TaskType` / `TaskTemplate` records | Confirm community planting day mapping |

## 8. Pre-Flight Checklist

- [x] Root cause confirmed (sections not classified as community) by inspecting data
- [ ] Sections to reclassify listed — moot while the stage is hidden
- [x] Task type vs section stage distinction confirmed with stakeholder
- [x] Option chosen — hide the Community stage for now (see Resolution)

## 9. Resolution (2026-08-16)

**Decision:** For now, remove the "Community" stage from the Lifecycle Progress widget on the dashboard. Community remains a valid `Section` stage (sections can still be classified as "Community" in the edit form), but it is hidden from the dashboard's lifecycle bars until community activity tracking is revisited.

**Implementation:**
- `core/views.py` — `GlobalDashboardView.get_context_data()` now skips `community` when building `stage_distribution`.
- `Section.STAGE_CHOICES` is unchanged, so the section edit form still offers "Community".
- Tests: `core/tests/test_dashboard.py` (13 tests) pass.

**Deferred (open questions intentionally left unresolved):**
- Which sections belong in the Community stage (reclassification) — moot while the stage is hidden.
- Whether "community planting day" should map to community activity — revisit if activity-based community tracking is wanted (original Option C).
