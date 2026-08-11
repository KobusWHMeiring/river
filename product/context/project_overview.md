# Project Overview: Liesbeek River Rehabilitation Management System

**Last Updated:** 2026-08-11

## 1. Project Purpose

A comprehensive web-based management system for coordinating river rehabilitation activities along the Liesbeek River. The platform enables managers to plan, track, and report on conservation tasks including litter collection, weeding, planting, and administrative activities across multiple river sections.

## 2. Current State Summary

The application is **in active production use** by a small field operations team. All core features from the initial backlog have been implemented and are operational. The current focus is on foundation stabilization (documentation, enforcement, logging, performance budgets) before tackling the next wave of user-facing features.

### Application Status
- **Core Features:** ✅ Complete
- **Database:** Populated with real-world task templates (19 templates) and example sections (8 sections)
- **Testing:** Unit test coverage for monthly and dashboard views; Playwright E2E planned
- **Deployment:** Live in production with deployment scripts configured
- **Production Feedback:** First week of real-world use captured in `backlog_v1.md`

## 3. Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend Framework** | Django 6.0.2 |
| **Language** | Python 3.x |
| **Database** | SQLite (Development), PostgreSQL (Production target) |
| **Templating** | Django Template Language (DTL) |
| **Styling** | Tailwind CSS with Material Symbols |
| **Interactivity** | Vanilla JavaScript (Native DOM APIs) |
| **Mapping** | Leaflet.js (CDN) |
| **Environment** | python-environ |

## 4. Completed Features

### ✅ Section Management
- **CRUD Operations:** Full create, read, update, delete for river sections
- **Spatial Mapping:** Lite GIS implementation using GeoJSON in JSONField
- **Leaflet.js Integration:** Interactive map with polygon drawing/editing
- **Visual Stages:** Sections categorized by lifecycle stage (Mitigation, Clearing, Planting, Follow-up, Community)
- **Bidirectional Sync:** Map hover synchronizes with list items

### ✅ Task Planning & Scheduling
- **Weekly Planner:** 7-day view with Team/Manager split
- **Monthly Planner:** Full month calendar view with high-density task display
- **Daily Agenda:** Daily task list with completion tracking
- **Task Creation:** Modal-based task creation with template auto-population
- **Context Navigation:** Seamless switching between weekly/monthly views preserving temporal context

### ✅ Task Templates
- **19 Real-World Templates:** Based on actual field activities
- **Template Types:** Litter Run, Weeding, Planting, Admin
- **Auto-Population:** Instructions auto-fill from template selection
- **Template Management:** Full CRUD interface (moved from Django Admin to core UI)

### ✅ Visit Logging (Context-Aware)
- **Smart Form:** Adapts UI based on task type
- **Pre-Population:** Notes field auto-fills from task instructions
- **Dynamic Sections:** Litter, Weeding, Planting sections expand/collapse based on task type
- **Admin Mode:** Clean interface (no metrics) for administrative tasks
- **Photo Upload:** Image capture with description

### ✅ Data Collection
- **Litter Tracking:** General and recyclable bag counters
- **Weeding Data:** Species-specific removal tracking with quantity
- **Planting Data:** Species-specific planting tracking
- **Metrics:** Flexible metric system supporting multiple data types

### ✅ Global Dashboard
- **Overview Metrics:** Total bags collected, plants planted, weeding sessions
- **Section Comparisons:** Cross-section activity visualization
- **Recent Activity:** Latest visit logs across all sections

### ✅ Stage Tracking
- **Lifecycle History:** Track section stage transitions over time
- **Historical Log:** Timestamped record of all stage changes
- **Timeline Visualization:** View progress through rehabilitation phases

### ✅ Multi-Day Task Series
- **Date Ranges:** Tasks can span multiple days via start/end dates
- **Bulk Creation:** Tasks auto-generated for each day in the range
- **Group Tracking:** Linked via shared `group_id` UUID

### ✅ Data Export
- **Excel Export:** Multi-sheet Excel workbook export
- **Sections + Tasks:** Separate sheets for sections and tasks data
- **Dashboard Integration:** Export accessible from dashboard

### ✅ Rolling To-Do List (Kanban)
- **Drag-and-Drop:** Kanban board with To Do / In Progress / Done columns
- **Position Tracking:** Integer-based position re-indexing for ordering
- **Global View:** Tasks not tied to specific dates or sections

### ✅ Chairperson Role
- **Role Support:** Chairperson assignee type alongside Team and Manager
- **Planner Integration:** Chairperson-specific rows in weekly/monthly planners

### ✅ Mobile Responsive
- **Responsive Layout:** All views adapt to mobile screen sizes
- **Touch-Friendly:** Kanban drag-and-drop and form controls work on mobile

### ✅ Redirect Context Preservation
- **next Parameter:** Redirect context preserved across form validation cycles
- **Form Errors:** Users return to correct view after correcting validation errors

## 5. Data Model Overview

### Core Entities

```
Section (River Sections)
├── name, color_code, current_stage
├── boundary_data (GeoJSON polygon)
├── center_point (GeoJSON point)
└── stage_history (SectionStageHistory)

TaskTemplate (Reusable Task Patterns)
├── name, task_type (litter_run/weeding/planting/admin)
├── assignee_type (team/manager)
└── default_instructions

Task (Scheduled Work)
├── date, section, assignee_type
├── instructions, is_completed
└── template (FK to TaskTemplate)

VisitLog (Completed Work Record)
├── task (optional FK), section, date
├── notes
├── metrics (Metric inline)
└── photos (Photo inline)

Metric (Quantifiable Data)
├── metric_type (litter_general/litter_recyclable/plant/weed)
├── label (species name), value

Photo (Visual Documentation)
├── file, section, visit, description
```

## 6. Key UI/UX Patterns

### Design Principles
- **High Information Density:** Maximize data visibility (e.g., 4+ visits per page)
- **Professional Aesthetic:** Clean, muted colors with subtle borders
- **Context Preservation:** Maintain temporal state when switching views
- **Progressive Disclosure:** Hide secondary actions behind hover states
- **Bidirectional Linking:** Map and list views stay synchronized

### Interaction Patterns
- **Modal Forms:** Quick actions without page navigation
- **Collapsible Sections:** Expand/collapse for focus-first data entry
- **Color Coding:** Section colors on borders for quick scanning
- **Overflow Handling:** "+X more" pattern for limited space
- **Native Experience:** Prefer browser behaviors for accessibility

## 7. Recent Learnings & Best Practices

### Django Patterns
1. **Form Queryset Timing:** Initialize `ModelChoiceField.queryset` in `__init__`, not at module level
2. **Query Optimization:** Use `select_related()` for ForeignKey relationships in list views
3. **Template Safety:** Use explicit `{% if %}` checks when accessing attributes of potentially-None objects
4. **Calendar Generation:** Use Python's `calendar.Calendar()` instead of manual date math
5. **Data Processing:** Group/filter data in views, not templates (dictionary lookups vs iteration)

### Frontend Patterns
1. **Coordinate Systems:** GeoJSON uses [lng, lat], Leaflet uses [lat, lng] - convert appropriately
2. **Hidden Form Fields:** Use `HiddenInput` for data populated via JavaScript
3. **CSS Transitions:** Use class toggling with transitions for smooth UX
4. **Server-Client Communication:** Embed Django template variables in JavaScript for configuration

### GIS & Mapping
1. **Lite GIS:** JSONField can store spatial data without PostGIS for simple use cases
2. **Progressive Enhancement:** Support both full boundaries and center point fallbacks
3. **Drawing Tools:** Restrict Leaflet.draw to needed shapes only

## 8. Remaining Backlog

The following features are planned for upcoming sprints. See `product/backlog.md` for the authoritative, prioritized list.

### Next Sprint (from `progress_log.json`)
1. **Playwright E2E Testing** — End-to-end integration tests for complex UI flows (planners, modals, Kanban)
2. **Enhanced Weeding Data Capture** — Species-specific removal tracking mirroring the planting interface
3. **Stage Tracking Visualization** — Polished timeline visualization for section stage history

### Production Feedback (from Jess, via `backlog_v1.md`)
- Quick Log from Planner — Log unplanned activities without navigating away
- Participant count on Impact Dashboard
- Tick-to-complete on planner tasks
- Typeable litter bag counts on dashboard
- Planner activity reflected in section/lifecycle boxes
- Export planner to Excel

## 9. File Structure Overview

```
river/
├── core/                      # Main application
│   ├── models.py             # Section, Task, VisitLog, Metric, Photo
│   ├── views.py              # All view classes (planners, logs, dashboards)
│   ├── forms.py              # Model forms and formsets
│   ├── urls.py               # URL routing
│   ├── templates/core/       # All HTML templates
│   ├── fixtures/             # Task template data
│   └── templatetags/         # Custom template filters
├── river/                     # Project configuration
│   ├── settings.py
│   └── urls.py
├── product/                   # Product documentation
│   ├── context/              # Current state, stack, learnings
│   ├── Done/                 # Completed feature PRDs
│   ├── Ready/                # PRDs ready for implementation
│   └── refinement/           # In-progress refinements
├── docs/                      # Technical documentation
└── templates/                 # Base templates
```

## 10. Current Sprint (2026-08-11)

**Foundation Stabilization Sprint** — see `product/context/prinicples/consolidated-sprint-plan.html` for the full plan.

1. **Context Hygiene:** Refresh docs, register in composing-context, clean up backlog
2. **Code Quality:** Fix `save()` in loop → `bulk_create()`, add `@transaction.atomic`
3. **Bug Fix:** Kanban to-do items snapping back from Done
4. **Ops:** `sync_from_prod.py` management command for pulling production DB
5. **Enforcement:** `.select_related()` on list views, performance budgets, structured logging

---

**System Health:** ✅ Operational  
**Development Status:** ✅ Feature-Complete (Core)  
**Documentation:** ✅ Current  
