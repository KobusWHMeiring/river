# Build Principles: River Project

## I. Architectural Layout
*   **Service Layer Pattern:** Business logic must live in `services/`. Models are for schema and properties; Views are for HTTP routing and context preparation; Services are for "doing things" (e.g., `create_task_series`).
*   **No Logic in Templates:** Templates must only display data. Use template tags or model properties for complex formatting or checks.
*   **Relational Integrity:** Use standard Django AutoField (Integer) for Primary Keys. Use `UUIDField` only for specific grouping needs (e.g., `group_id` for task series).
*   **Database:** Use SQLite for local development and PostgreSQL for production (managed via `DATABASE_URL`). Note: Images are stored on the filesystem (media/), metadata only in DB.

## II. AI-Specific Guardrails
*   **Silent Errors are Prohibited:** Never use bare `except: pass`. All caught exceptions must be logged or handled gracefully.
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
