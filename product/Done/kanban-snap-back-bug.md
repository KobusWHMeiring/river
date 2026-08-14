# PRD: Kanban "Move to Done" Snap-Back Bug

> **Date:** 2026-08-11
> **Source:** Sarah's request list, item #1
> **Priority:** P0 (production bug)

---

## 1. Bug Description

**Reported:** "To do list is broken — when you click move it to done it moves back to to do."

The Kanban board at `/todo/` allows users to drag task cards between columns (To Do → Doing → Done). When a user drags a card to the "Done" column, the card visually snaps back to its original column or reverts on next page load.

**Affected views:** `core/templates/core/todo_kanban.html`, `core/views.py` (`TodoUpdateAPI`), `core/services/task_services.py` (`move_todo_task`)

---

## 2. Reproduction (Working Hypothesis)

1. Navigate to `/todo/`
2. Drag any task card from "To Do" or "Doing" into the "Done" column
3. Observe one of: (a) card snaps back immediately, or (b) card stays visually in Done but reverts on page refresh

---

## 3. Root Cause Analysis

### What the code does:

| Layer | Mechanism |
|-------|-----------|
| **Frontend** | SortableJS `onEnd` fires → `updateTaskStatus(taskId, newStatus, newIndex)` → `fetch()` POST to `/todo/update/` |
| **Backend API** | `TodoUpdateAPI.post()` → parses JSON → calls `move_todo_task(task_id, new_status, new_index)` |
| **Backend Service** | `move_todo_task()` — `select_for_update()` on the task, re-indexes source + target columns in a `transaction.atomic()` block |

### Suspected causes (ordered by likelihood):

1. **Unhandled fetch failure (HIGH LIKELIHOOD):** The `updateTaskStatus` function handles `!data.success` but has **no `.catch()`** for network-level failures (connection refused, timeout, 500 error). When the fetch fails silently, the DOM card stays visually in the new column while the backend hasn't persisted the change. On next page load, the card is back in its original column.

   ```javascript
   // Current code (todo_kanban.html):
   fetch(updateUrl, { ... })
   .then(response => response.json())
   .then(data => {
       if (!data.success) {
           alert('Failed to update task.');
           window.location.reload();
       }
   });
   // NO .catch() — network errors are swallowed
   ```

2. **CSRF token staleness (MEDIUM LIKELIHOOD):** The CSRF token is rendered at page load as `{{ csrf_token }}`. If the page is left open for an extended period, the token may expire, causing the POST to receive a 403. No 403 handler exists.

3. **Backend `move_todo_task` edge case (LOW LIKELIHOOD):** The service logic was inspected and appears correct for standard flows. Possible edge: if `new_index` from SortableJS doesn't match the actual insertion index (e.g., due to DOM vs. server state mismatch from a previous failed update), the task could be placed at an unexpected position.

4. **SortableJS DOM conflict (LOW LIKELIHOOD):** If SortableJS's animation fires after the DOM element has already been re-parented by a competing update, visual snap-back could occur. Unlikely given the single-user, single-interaction-at-a-time usage pattern.

### Existing test gap:
- `test_todo_kanban.py` has 4 tests covering service logic, API happy path, view grouping, and exclusions
- **No test for:** fetch failure recovery, CSRF expiry, concurrent moves, or the full drag-to-Done UX flow (requires Playwright)

---

## 4. Proposed Fix

### Fix A: Frontend hardening (Recommended — lowest risk, fastest)

1. Add `.catch()` to the fetch chain with user-visible error + page reload:

   ```javascript
   fetch(updateUrl, { ... })
   .then(response => {
       if (!response.ok) throw new Error(`HTTP ${response.status}`);
       return response.json();
   })
   .then(data => {
       if (!data.success) throw new Error(data.error || 'Update failed');
   })
   .catch(error => {
       console.error('Kanban update failed:', error);
       alert('Failed to update task. The page will reload.');
       window.location.reload();
   });
   ```

2. Add a visual "saving" state to the card while the fetch is in-flight to give the user feedback that something is happening.

3. Optionally: add a manual "Move to Done" button on each card as a fallback interaction (addresses Sarah's "click" language — she may prefer clicking over dragging).

### Fix B: Backend hardening (Defense in depth)

1. Add input validation at `TodoUpdateAPI` — validate `task_id` exists before calling service.
2. Add logging to `move_todo_task` to surface failures in production.

### Fix C: Playwright E2E test (Future)

Once the fix is in, add a Playwright test that drags a card to Done and asserts it stays there after page reload. This is part of the next sprint's Playwright work.

---

## 5. Investigation Steps (Do First)

Before implementing any fix, reproduce the bug:

1. **Pull production DB:** Use `sync_from_prod.py` (to be built) to get real data
2. **Try to reproduce locally:** Drag multiple cards to Done, refresh, observe
3. **Check browser console:** Are there 403, 500, or network errors on the fetch?
4. **Check CSRF:** Leave the kanban page open for 30+ minutes, then try to drag
5. **Inspect DB state:** After a snap-back, check if `todo_status` changed in the DB

---

## 6. Acceptance Criteria

- [ ] Dragging a card to Done persists across page refresh
- [ ] Dragging a card to Doing persists across page refresh
- [ ] Network failure during drag shows a user-visible error message (not silent failure)
- [ ] CSRF expiry shows a user-visible error message
- [ ] Existing `test_todo_kanban.py` tests still pass
- [ ] New test: API returns 400 for invalid task_id
- [ ] New test: API returns 400 for invalid status value

---

## 7. Dependencies

- **Blocks:** Nothing
- **Blocked by:** `sync_from_prod.py` (strongly recommended for reproduction, not strictly required)
- **Related:** 1.1 (`.select_related()` audit — Kanban view should be included), 1.2 (Performance Discovery — add Kanban endpoint)

---

## 8. Effort Estimate

| Step | Time |
|------|------|
| Reproduce bug (with/without prod data) | 15 min |
| Implement Fix A | 20 min |
| Write additional tests | 15 min |
| Verify fix | 10 min |
| **Total** | **~1h** |
