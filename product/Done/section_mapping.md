# PRD: Section Mapping & Spatial Visualization

## 1. Problem Statement
River sections are currently managed as a linear list. While they are ordered "Upstream to Downstream," users lack a spatial understanding of where one section ends and the next begins. Managers cannot see "at a glance" which physical areas of the river are currently in which stage (e.g., seeing a red "Clearing" polygon next to a green "Stable" polygon).

## 2. Strategic Goal
To transform the Section List into a spatial tool where the physical boundaries of the river are represented. This provides immediate geographical context and prepares the application for future GIS-based environmental reporting.

## 3. Proposed Scope
- **Interactive Map Header:** A Leaflet.js map at the top of `section_list.html`.
- **Section Polygons:** Sections represented as shapes (polygons) rather than markers.
- **Dynamic Styling:** Polygons colored according to the Section's `color_code` or `current_stage`.
- **Navigation:** Clicking a polygon redirects to the `SectionDetailView`.
- **Boundary Definition:** A drawing interface in the Section Form (Admin or Frontend) to define these areas.

## 4. Technical Constraints
- **Lite GIS Approach:** Use a `JSONField` to store coordinate arrays to avoid heavy PostGIS/GDAL dependencies.
- **Library:** Leaflet.js (Standard, lightweight, open-source).
- **Responsive:** The map must be touch-friendly for field tablet use.

## 5. Implementation Details

### Data Model Change
Add a `boundary_data` field (JSONField) to the `Section` model to store a GeoJSON-style array of coordinates.

### The Drawing Interface
To make data entry possible, we will use **Leaflet.draw** in the Section creation form.
1. User sees a map.
2. User clicks points along the river bank to create a shape.
3. On save, the coordinates are serialized to JSON and stored in the database.

### Dashboard Integration
The map will be synchronized with the section list. Hovering over a list item will highlight the polygon on the map, and vice versa.

---

# User Stories

## Story 1: Visualizing the River
**Value Proposition:** As a Manager, I want to see the entire river colored by management stage, so I can see where my bottlenecks are geographically.
**AC:**
- [ ] Map displays on Section List page.
- [ ] Polygons show the actual boundaries of the sections.
- [ ] Polygons are color-coded based on the Section's `color_code`.

## Story 2: Spatial Navigation
**Value Proposition:** As a Supervisor, I want to click on a specific area of the map to open that section's logs, so I don't have to scroll through a long list.
**AC:**
- [ ] Clicking a polygon opens the `section_detail` page.
- [ ] Hovering over a polygon shows a tooltip with the Section Name and Current Stage.

## Story 3: Defining Boundaries
**Value Proposition:** As an Admin, I want to "draw" a new section on the map when we expand our operations, so I don't have to manually find coordinates.
**AC:**
- [ ] Section Form includes a map widget.
- [ ] Admin can draw, edit, or delete a polygon on this map.
- [ ] Coordinates are automatically updated in the database on save.

---

**CRITICAL DECISION:**
Do we use a single "Center Point" as a fallback if no polygon is defined?
**Recommendation:** Yes. It allows for a gradual rollout where some sections have shapes and others just have markers until they are updated.
