# PRD: Dynamic Kanban Columns (Add / Rename / Reorder / Delete)

**Status:** In Refinement — design approved 2026-08-14 (awaiting build)
**Source:** Product/engineering backlog, 2026-08-14

## 1. Problem Statement

The "Rolling To-Do List" kanban board is hardcoded to three columns — **To Do, Doing, Done**. There is no way to add a column (e.g. "Blocked", "Backlog", "In Review") or rename/reorder the existing ones. The board should behave like a real kanban, where the workflow stages are owned by the user, not fixed in the code.

## 2. Strategic Goal

Make the kanban columns first-class, user-managed entities — add, rename, reorder, and delete columns — so the rolling to-do list can reflect however the team actually works.

## 3. What We Know (Current Behaviour)

- The board lives on `Task.is_rolling=True` only, and is a single **shared** board (no per-user state).
- Columns are **hardcoded in the template** (`todo_kanban.html`): three `<div>`s — To Do / Doing / Done.
- `Task.todo_status` is a `CharField` with `TODO_STATUS_CHOICES = [('todo','To Do'), ('doing','Doing'), ('done','Done')]`, plus integer `todo_position` for ordering within a column.
- Drag-and-drop uses SortableJS → `TodoUpdateAPI` (`POST /todo/update/`) → `move_todo_task()`, which **validates the status against the hardcoded list** `['todo','doing','done']`.
- "Done" is special: it renders a green check + "Completed" label, and every card has a hardcoded "Move to Done" button (`todo_card.html`).
- The general **task edit form** (`task_form.html`) also shows a "Kanban Status" dropdown (only when "Rolling To-Do" is checked), driven by the same hardcoded choices.
- `todo_status` exists on *all* tasks, but only rolling tasks use it — no report, planner, or dashboard view reads it. Blast radius is contained to: board, task form, `TodoUpdateAPI`, the service, and tests.

## 4. Proposed Scope

- Replace the fixed three columns with a dynamic, ordered set of columns.
- Support: **add**, **rename**, **reorder** (drag), and **delete** columns.
- New rolling tasks enter the **leftmost** column.
- Columns are **global** (shared by all users).

### Explicitly Out of Scope (initial)

- Per-user / personal columns.
- Per-column colours (a neutral dot for now; a `color` field can be added later as an additive migration).
- WIP limits, column descriptions, or any per-column automation.

## 5. Locked Decisions

| # | Decision | Choice |
|---|----------|--------|
| 1 | Column model | Fully dynamic — no special "Done" semantics |
| 2 | Visibility | Global (one shared board) |
| 3 | Delete | Block deletion of non-empty columns; also block deleting the *last* remaining column |
| 4 | Entry point | Leftmost column receives new tasks |
| 5 | Reorder | Drag-to-reorder columns (header handle) |
| 6 | Colour | Neutral dot for all columns (no colour) |
| 7 | Error handling | Inline toasts (no `alert()`s), clear messages for delete-block and drag failures |
| 8 | Approach | New `KanbanColumn` model + `Task.column` FK with `on_delete=PROTECT` |

---

## 2026-08-14 Dynamic Kanban Columns — Design

### Data model (`core/models.py`)

```python
class KanbanColumn(models.Model):
    name = models.CharField(max_length=50, unique=True)
    position = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['position', 'id']

    def __str__(self):
        return self.name
```

**`Task` changes:**
- **Remove** `todo_status` (CharField + its index).
- **Add** `column = models.ForeignKey(KanbanColumn, on_delete=models.PROTECT, null=True, blank=True, related_name='tasks')`.
- Keep `todo_position` (index within a column).
- `PROTECT` = database-enforced "can't delete a column that has tasks". Non-rolling (planner) tasks keep `column = NULL`.

### Migration (schema + data)

1. Create `KanbanColumn`; add nullable `Task.column`.
2. **Data migration:** create three columns — "To Do" (0), "Doing" (1), "Done" (2) — then map existing rolling tasks by their old `todo_status` value.
3. Drop `Task.todo_status`.

### Services — new `core/services/kanban_services.py`

Move the existing `move_todo_task` here (adapted to `column_id`), plus:

```python
def create_column(name: str) -> KanbanColumn
def rename_column(column_id: int, name: str) -> KanbanColumn
def delete_column(column_id: int) -> None      # raises on non-empty / last column
def reorder_columns(ordered_ids: list[int]) -> None
def move_todo_task(task_id: int, column_id: int, new_index: int) -> None
```

All typed; `@transaction.atomic` where reindexing; errors surfaced as clear `ValueError`s (the view translates to JSON + toast).

### Views + URLs

Four tiny endpoints (each ~10 lines — parse JSON → call service → `JsonResponse`):

| URL | Action |
|-----|--------|
| `POST /todo/columns/create/` | create column at end |
| `POST /todo/columns/<id>/rename/` | rename |
| `POST /todo/columns/<id>/delete/` | delete (block non-empty/last) |
| `POST /todo/columns/reorder/` | set positions from ordered id list |

Modify `TodoUpdateAPI` → accept `column_id` (validate it exists) instead of `status`. Modify `TodoKanbanView.get_context_data` → fetch `columns` ordered and group rolling tasks by column.

### Templates

- **`todo_kanban.html`** — replace the 3 hardcoded columns with `{% for column in columns %}`. Column header: neutral dot, editable name, count, "⋯" menu (Rename / Delete). Columns reorderable via SortableJS on the container (drag on a header handle — avoids conflict with card drag). **"+ Add column"** at the end. Remove the hidden `todo_status="todo"`; new rolling tasks land in the leftmost column (set server-side).
- **`todo_card.html`** — remove the hardcoded "Move to Done" button and green "Completed" check (columns are now equal).
- **`task_form.html`** — replace the hardcoded "Kanban Status" dropdown with a dynamic column select (shown only for rolling tasks).

### Error handling

- Small vanilla JS `showToast(message, type)` helper; replace the two existing `alert()` calls.
- Delete-block → `{success: false, error: "Column 'X' still has N tasks — move them first."}` → error toast.
- Rename/create/reorder/drag failures → error toast; drag failures also revert/reload.

### File map

| File | Change |
|------|--------|
| `core/models.py` | +`KanbanColumn`, `Task.column`, −`todo_status` |
| `core/migrations/` | new schema + data migration |
| `core/services/kanban_services.py` | **new** — column CRUD + move logic |
| `core/views.py` | 4 new endpoints + adapt `TodoUpdateAPI` / `TodoKanbanView` |
| `core/urls.py` | 4 new routes |
| `core/forms.py` | `TaskForm.todo_status` → dynamic `column` field |
| `core/templates/core/todo_kanban.html` | dynamic columns, add/rename/delete/reorder, toasts |
| `core/templates/core/includes/todo_card.html` | drop done-specific UI |
| `core/templates/core/task_form.html` | dynamic status dropdown |
| `core/tests/test_todo_kanban.py` | extend + new column tests |

Structural compliance: endpoints stay under 20 lines (delegate to services); service functions typed; JS is vanilla + the already-present SortableJS; no logic in templates.

## 6. Success Criteria (high-level)

- A user can add, rename, reorder, and delete columns on the kanban board.
- New rolling tasks always land in the leftmost column.
- Deleting a non-empty column is blocked with a clear message; deleting the last column is blocked.
- Drag-and-drop of cards between columns keeps working after the change.
- Existing tasks are migrated to the correct columns with no data loss.

## 7. Pre-Flight Checklist

- [x] Design approved (approach A, dynamic + global + block-delete)
- [x] Locked decisions recorded
- [x] Current behaviour investigated (blast radius confirmed)
- [ ] Migration tested on a copy of the data
- [ ] Tests written and passing
- [ ] Manual visual verification of add/rename/reorder/delete + drag

## 8. Tests

- Column create (appends at end) / rename (unique name) / delete (empty ✓, non-empty ✗, last-column ✗) / reorder (positions update).
- Move task between columns (adapt existing tests to `column_id`).
- New rolling task lands in the leftmost column.
- Data migration: three old statuses map to three columns.

## 9. Risks

| Risk | Mitigation |
|------|-----------|
| Migration mis-maps existing tasks | Data migration maps exactly `todo/doing/done`; test on a copy first |
| Nested Sortable conflict (column vs card drag) | Column reorder drags on a header handle only |
| `move_todo_task` reindexing is intricate | Preserve existing logic, keyed on `column_id`, keep `select_for_update` + atomic |
| Planner tasks get a stray column | `column` nullable; only rolling tasks set it |
