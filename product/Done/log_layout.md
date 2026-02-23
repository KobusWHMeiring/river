# PRD: Fix Collapsible Layout in Visit Log Form

## 1. Problem Statement

In the "Log Activity" form (`visit_log_form.html`), the collapsible sections for "Weeding Data" and "Planting Data" are not functioning correctly. When a user adds a new data entry (e.g., a new plant species), the input fields for that entry appear outside of the collapsible container. Furthermore, when the section is collapsed, these dynamically added fields remain visible on the page instead of being hidden. This creates a confusing and broken user interface.

As evidenced by user-provided screenshots, the input fields for "Plant Species" are rendered below the main "Planting Data" container, detached from their intended parent.

## 2. Strategic Goal

To fix the layout and functionality of the collapsible sections in the visit log form, ensuring that all content, including dynamically added fields, is correctly contained within the appropriate section and is hidden when the section is collapsed. This will restore the intended "focus-first" user experience for data entry.

## 3. Analysis of the Current Failure

The root cause of this issue is a structural flaw in the HTML of `core/templates/core/visit_log_form.html`.

1.  **Incorrect Nesting:** The "Weeding Data" and "Planting Data" sections currently have a nested `div` structure:
    ```html
    <!-- Example of the broken structure -->
    <div class="section-content p-6">
        <div id="plantMetrics" class="space-y-4">
            <!-- Dynamically added content goes here -->
        </div>
    </div>
    ```
2.  **JavaScript Target:** The `addMetric()` JavaScript function correctly targets the inner `div` (e.g., `id="plantMetrics"`) to append new input fields.
3.  **CSS Hiding Target:** The CSS and collapse/expand JavaScript are designed to hide the outer `div` (the one with the `.section-content` class).

While logically this should work, the visual evidence from the screenshot proves that the browser is rendering the dynamically-added elements outside of the main component body. This points to a subtle DOM structure issue where the unnecessary layer of nesting causes the new elements to be misplaced. The working "Litter Collection" section does not have this extra layer of nesting, which is strong evidence that this is the source of the problem.

## 4. Proposed Solution

The fix is to flatten the HTML structure for the "Weeding Data" and "Planting Data" sections to eliminate the unnecessary nesting and make them structurally identical to the working "Litter Collection" section.

-   **Target File:** `core/templates/core/visit_log_form.html`

### Step 1: Fix the "Weeding Data" Section

The HTML for the weeding content area should be changed as follows:

**FROM:**
```html
                        <div class="section-content p-6">
                            <div id="weedMetrics" class="space-y-4">
                            </div>
                        </div>
```

**TO:**
```html
                        <div id="weedMetrics" class="section-content p-6 space-y-4">
                        </div>
```

### Step 2: Fix the "Planting Data" Section

Similarly, the HTML for the planting content area should be changed:

**FROM:**
```html
                        <div class="section-content p-6">
                            <div id="plantMetrics" class="space-y-4">
                                <!-- Existing content for the first plant metric -->
                            </div>
                        </div>
```

**TO:**
```html
                        <div id="plantMetrics" class="section-content p-6 space-y-4">
                                <!-- Existing content for the first plant metric -->
                        </div>
```

### Why This Works

By merging the `id` (`plantMetrics`/`weedMetrics`) and the classes (`section-content`, `p-6`, `space-y-4`) into a single `div`, we achieve two things:
1.  The JavaScript function `addMetric()` will now directly append new input fields into the `div` that has the `.section-content` class.
2.  The CSS rule `.section-collapsed .section-content { display: none !important; }` will now correctly hide the container and all of its children, including the dynamically added ones.

This removes the ambiguity from the DOM structure and ensures all content behaves as expected within the collapsible panel.
