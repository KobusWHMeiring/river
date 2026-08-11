# Build Principles: River Project

## I. Architectural Layout
*   **Service Layer Pattern:** Business logic must live in `services/`. Models are for schema and properties; Views are for HTTP routing and context preparation; Services are for "doing things" (e.g., `create_task_series`).
*   **No Logic in Templates:** Templates must only display data. Use template tags or model properties for complex formatting or checks.
*   **Relational Integrity:** Use standard Django AutoField (Integer) for Primary Keys. Use `UUIDField` only for specific grouping needs (e.g., `group_id` for task series).
*   **Database:** Use SQLite for local development and PostgreSQL for production (managed via `DATABASE_URL`). Note: Images are stored on the filesystem (media/), metadata only in DB.

## II. AI-Specific Guardrails
*   **Silent Errors are Prohibited:** Never use bare `except: pass`. All caught exceptions must be logged or handled gracefully. Guard expensive log formatting in loops with `logger.isEnabledFor()` to avoid wasted string allocations when the log level is disabled.
*   **Schema Before Logic:** No View code can be written until the `models.py` change is approved and migrations are generated.
*   **Type Hinting:** All Service functions must have Python type hints to ensure clarity in data flow.

## III. Frontend & UX
*   **High Information Density:** Prefer compact lists and split-cell layouts (like the planners) to maximize visible data.
*   **Professional Aesthetic:** Use subtle borders (`border-slate-200`), muted colors, and consistent spacing.
*   **Vanilla First:** Use Vanilla JavaScript (Native DOM APIs) for interactivity. Keep external dependencies minimal.
*   **Context Preservation:** Maintain user context (e.g., current date, selected filters) when navigating between views using URL parameters and the `next` redirect pattern.

## IV. Testing (ToBe)
*   **Playwright Implementation:** Future goal to implement Playwright for end-to-end integration testing of complex UI flows (e.g., planners, modals).

## V. The "Institutional Memory" Law
*   **ADR (Architectural Decision Records):** Any major change in data flow or new library must be recorded in `docs/adr/000X_reason.md`.
*   **Verification:** Fulfill the entire lifecycle: Research -> Strategy -> Execution -> Validation. A task is not complete until behavioral correctness is verified.

## VI. Performance Patterns (Abseil-Derived)

These principles are derived from cross-pollination analysis of Google's Abseil Performance Hints, adapted for Django/ORM contexts. They complement the Architectural Layout (§I) by governing query shape and runtime behavior.

*   **Bulk Over Loop:** Never call `.save()` inside a `for` loop. For creating multiple objects, use `bulk_create()`. For updating, use `bulk_update()`. Wrap in `@transaction.atomic`. This is the single most common performance killer after N+1 queries.
*   **Use `.only()` / `.defer()` for List Contexts:** When fetching QuerySets for list views (tables, dropdowns, card grids), use `.only('field1', 'field2')` to limit columns fetched. For large JSONFields not needed in list context, use `.defer('large_field')`. Fetching all columns for large result sets wastes memory and I/O.
*   **Prefer `.values()` / `.values_list()` for Read-Only Rendering:** When QuerySets are only used to build dicts, JSON responses, or simple template renders (no model methods called), use `.values()` or `.values_list()` instead of full model instantiation. Model deserialization is expensive — `.values()` is 3-5× faster for read-only contexts.
*   **Guard Log Calls in Loops:** Use `if logger.isEnabledFor(logging.DEBUG):` before expensive log formatting (f-strings, `.format()`) inside loops. F-strings evaluate eagerly even if the logger discards the message.
*   **Precompute Once, Pass via Context:** If a QuerySet result is needed by multiple code paths within one HTTP request, materialize it once in the view and pass it. Django QuerySets are lazy but not cached across different call sites.
*   **Always `.select_related()` in List Views:** Every list view rendering FK relationships must use `.select_related()` to avoid N+1 queries. Audit templates for `{{ object.foreign_key.field }}` access and ensure the corresponding FK is in `.select_related()`.
