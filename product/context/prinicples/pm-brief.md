# PM Brief: River Foundation Sprint

> Hand this to your PM alongside `product/context/prinicples/consolidated-sprint-plan.html`.
> This brief gives them the "what and why" — the plan has the "how."

---

## 30-Second Orientation

**River** is a Django web app for managing river rehabilitation along the Liesbeek River. Think: task planning on a weekly/monthly calendar, logging field work (litter collected, plants put in, weeds removed), dashboards, maps, and data export. It's a single-developer project, ~25 views, ~18 templates, live in production, used by a small field operations team.

**The problem:** The project was built rapidly (Feb-Mar 2026). The code works. But the scaffolding around it — documentation, enforcement of principles, performance visibility, logging — hasn't kept pace with the feature growth. Before adding more features, we need to stabilize.

**This sprint** doesn't deliver user-facing features. It delivers confidence: confidence that context is current, that principles are enforced, that we'll know if performance degrades, and that we can see what's happening in production.

---

## Key Files to Read (15 min total)

Read these in order. Skip everything else.

| # | File | Why | Time |
|---|------|-----|------|
| 1 | `product/context/project_overview.md` | Understands what the app does, its data model, and what's been built | 5 min |
| 2 | `product/context/build_principles.md` | The rules the dev AI must follow. Note: they're unenforced right now | 3 min |
| 3 | `progress_log.json` | What's done, what's stalled, what's next. The institutional memory | 2 min |
| 4 | `product/backlog.md` | The current backlog. Note: it's stale — some "pending" items are done | 3 min |
| 5 | `product/backlog_v1.md` | Production feedback from Jess (first week of real use) | 2 min |

Then open `product/context/prinicples/consolidated-sprint-plan.html` and skim the Phase headers and the "What You'll Have After This Sprint" section.

---

## Questions for the PM to Challenge

The plan assumes these things. If any are wrong, we should adjust before executing:

### 1. Are we prioritizing the right things?

The plan invests ~12 hours in infrastructure before touching any feature from the backlog. The argument is: foundations first, features second. But is there a user-facing fire that needs putting out *right now*? Is Jess (or whoever is using the app daily) blocked on anything?

### 2. Is "performance budgets" the right metric?

The plan proposes per-endpoint query budgets (e.g., "the dashboard must load in ≤ 8 queries"). This catches N+1 regressions — the most common performance bug in Django. But is page load time what users actually care about? Would they rather we measure time-to-interactive? Or is "it works, don't break it" sufficient?

### 3. Are we over-engineering for a small app?

River has ~25 views. Homtini (where the ArchGuard and performance testing patterns come from) has hundreds. Is deterministic static analysis + per-endpoint query budgets appropriate for a single-developer, single-app project? Or would a simpler checklist + code review discipline suffice?

### 4. What's the urgency on logging?

The plan includes setting up structured logging + Sentry. This is partly motivated by the user's explicit goal ("improve logging/uptime management"). Is there a specific incident that drove this? Are there silent failures in production we're not seeing?

### 5. The backlog is stale — what's actually next?

`progress_log.json` says the next three steps are Playwright E2E, Enhanced Weeding Data, and Stage Tracking Visualization. `backlog_v1.md` has Quick Log, Rolling To-Do, Multi-Day Tasks, and Data Export (some of which are done). Which of these actually matters most to users? We should settle this before the next sprint.

---

## Context the PM Does NOT Need to Read

These are implementation artifacts. They're reference material if the PM is curious, but not required for the brainstorm:

- `product/context/prinicples/abseil-vs-build-principles-comparison.html` — C++ performance principles mapped to Django. Interesting but academic.
- `product/context/prinicples/archguard/` — The ArchGuard source code. Implementation detail.
- `product/context/prinicples/performance-testing.md` — Homtini's perf test README. Implementation detail.
- `product/context/learnings.md` — 58KB of debugging war stories. Great institutional memory, not PM reading.
- `product/context/CURRENT_STATE.md` — Auto-generated codebase dump. Regenerated on demand.
- `product/context/stack.md`, `product/context/ui_standards.md` — Reference material.
- `DEVELOPER_HANDOVER.md` — Stale. Being archived in this sprint.

---

## The One-Line Ask

> "Review the consolidated sprint plan. Challenge the priorities. Tell us if we're solving the right problems in the right order, or if we should redirect effort toward user-facing work. We'll adjust and execute."
