# UAT: Form Validation Error Display

**Feature slug:** `form_validation_error_display`
**Drafted:** 2026-08-16 (after implementation)

## Pre-test setup
- Logged-in user (team or manager).
- A task whose template has task type **Admin** (e.g. "Outreach"), completed with a VisitLog.
- A task whose template has task type **Litter Run** (or any non-admin type), completed with a VisitLog.

---

## Scenario 1: Admin log edit shows no metrics and saves cleanly
1. Open Daily Agenda → find the completed Admin task → Edit Log.
2. **Expected:** No "Metrics & Collection" section is shown.
3. Change the participant count, then Submit.
4. **Expected:** Page redirects (no error), and the change is saved.

## Scenario 2: Stale client phantom metrics are ignored (admin)
1. This is the regression from the PRD: an admin task's log must never fail on invisible "metric_type required" / "value required".
2. In the browser, open the admin log edit, then in DevTools set the hidden `metrics-TOTAL_FORMS` input to `2` and submit.
3. **Expected:** Save succeeds (redirect), no error banner, and no phantom metrics are created.

## Scenario 3: Non-admin log with a real error shows the banner
1. Open the Litter Run log edit.
2. Add a photo but enter a description shorter than 10 characters.
3. Submit.
4. **Expected:** Page reloads with a red error-summary banner "Please correct the errors below" listing the photo description error.

## Scenario 4: Inline errors next to fields
1. On the visit log form, clear the Date field and submit.
2. **Expected:** The banner lists "Date" and a red inline error appears directly under the Date input.
3. Enter a negative participant count and submit.
4. **Expected:** An inline error appears under the participant input.

## Scenario 5: Section form error summary
1. Go to Sections → Create Section, leave Name blank, submit.
2. **Expected:** A red banner appears at the top of the form listing the Name error, plus the inline error under the field.

## Scenario 6: Task form error summary
1. Create a Task (non-rolling), leave the date blank, submit.
2. **Expected:** Banner lists "Date" error ("Date is required for non-rolling tasks.") and inline error under the field.

## Scenario 7: Template & Task Type forms error summary
1. Create a Task Template with a blank name, submit.
2. **Expected:** Banner + inline error appear.
3. Create a Task Type with a blank name or code, submit.
4. **Expected:** Banner + inline error appear.

## Scenario 8: Success feedback still works
1. Complete a task (tick) and re-open it.
2. **Expected:** The success toast ("Task completed successfully." / "Task re-opened.") still appears.
3. Save a visit log edit.
4. **Expected:** Success message appears (no error banner when valid).

## Accessibility check
- On any errored form, the banner is announced (role="alert") and field labels link to their inputs.
