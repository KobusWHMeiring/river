# Mobile Responsiveness Implementation Plan

**Target Views:** Daily Agenda (`daily_agenda.html`) and Visit Log Form (`visit_log_form.html`)  
**Priority:** High - Field workers need mobile access for logging activities  
**Estimated Effort:** Medium-High (3-5 days)  
**Last Updated:** 2026-02-24

---

## 1. Executive Summary

### Current State
The Liesbeek Management System is primarily desktop-focused with a fixed sidebar navigation (256px) and horizontal layouts. While the Daily Agenda has basic responsive elements, the Visit Log Form and overall navigation require significant mobile optimization for field use.

### Goal
Transform the day view and logging interface into a mobile-first experience that allows field workers to:
- Quickly view and complete daily tasks on mobile devices
- Log activities efficiently with thumb-friendly controls
- Navigate the application without horizontal scrolling
- Access critical information at a glance

---

## 2. User Personas & Use Cases

### Primary Persona: Field Worker
- **Device:** Smartphone (primarily), occasionally tablet
- **Context:** Outdoors, near river sections, potentially wearing gloves
- **Primary Tasks:**
  1. View today's assigned tasks (Daily Agenda)
  2. Log completed work with metrics (Visit Log)
  3. Take and upload photos
  4. Quickly mark tasks complete

### Secondary Persona: Manager (Mobile)
- **Device:** Tablet or phone for quick checks
- **Context:** Away from desk, checking progress
- **Primary Tasks:**
  1. Review team activity
  2. Quick status checks

---

## 3. Mobile Breakpoint Strategy

### Breakpoints (Tailwind)
```
sm: 640px   - Large phones / small tablets
md: 768px   - Tablets / small laptops  
lg: 1024px  - Laptops / desktops (current design)
xl: 1280px  - Large desktops
```

### Mobile-First Approach
- Design for 375px minimum width (iPhone SE)
- Progressive enhancement for larger screens
- Ensure touch targets minimum 44x44px
- Optimize for one-handed use where possible

---

## 4. Component-Level Changes

### 4.1 Global Navigation (base.html)

**Current:** Fixed 256px sidebar on left

**Mobile Solution:**
- **≤768px:** Collapse sidebar to bottom navigation bar
  - 5-icon bottom bar: Dashboard, Planner, Agenda, Sections, More
  - Hide text labels, show icons only
  - "More" reveals slide-up menu for Templates, Admin, Logout
  - Add hamburger menu for secondary navigation

**Implementation:**
```html
<!-- Mobile bottom nav (hidden on desktop) -->
<nav class="fixed bottom-0 left-0 right-0 bg-white border-t border-slate-200 
            flex justify-around items-center h-16 z-50 md:hidden">
  <a href="{% url 'dashboard' %}" class="flex flex-col items-center p-2">
    <span class="material-symbols-outlined">analytics</span>
  </a>
  <!-- ... other nav items -->
</nav>

<!-- Desktop sidebar (hidden on mobile) -->
<aside class="hidden md:flex w-64 ...">
  <!-- existing sidebar -->
</aside>
```

**Files to Modify:**
- `templates/base.html` - Navigation structure
- Add new CSS for mobile nav transitions

---

### 4.2 Daily Agenda (daily_agenda.html)

**Current Issues:**
- Header buttons stack awkwardly on mobile
- Task cards have horizontal action buttons that may overflow
- Fixed max-width container limits content width
- "Add Log" button competes with header space

**Mobile Solution:**

#### Header Redesign (Mobile)
```html
<header class="px-4 py-3 border-b border-slate-200 md:px-8 md:h-16">
  <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-2">
    <!-- Date on mobile: Compact format -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-lg font-bold md:text-xl">
          {{ today|date:"D, M j" }}  <!-- Mobile: "Mon, Feb 24" -->
        </h1>
        <p class="text-xs text-slate-500 uppercase">Daily Agenda</p>
      </div>
      <!-- Floating action button for Add Log -->
      <a href="{% url 'visit_log_create' %}" 
         class="md:hidden fixed bottom-20 right-4 w-14 h-14 bg-primary text-white 
                rounded-full shadow-lg flex items-center justify-center z-40">
        <span class="material-symbols-outlined text-2xl">add</span>
      </a>
    </div>
  </div>
</header>
```

#### Task Cards (Mobile-Optimized)
```html
<!-- Mobile: Full-width, vertical action layout -->
<div class="bg-white rounded-xl border border-slate-200 shadow-sm 
            overflow-hidden border-l-4 mb-4 md:mb-6"
     style="border-left-color: {{ task.section.color_code|default:'#94a3b8' }}">
  
  <div class="p-4">
    <!-- Section badge and assignee -->
    <div class="flex items-center justify-between mb-2">
      <span class="text-[10px] font-bold uppercase tracking-wide px-2 py-0.5 rounded"
            style="background-color: {{ task.section.color_code }}20; 
                   color: {{ task.section.color_code }}">
        {{ task.section.name|default:"No Section" }}
      </span>
      <span class="text-[10px] text-slate-400 uppercase">{{ task.assignee_type|title }}</span>
    </div>
    
    <!-- Instructions -->
    <h3 class="text-sm font-semibold text-slate-800 mb-3">
      {{ task.instructions|truncatechars:150 }}
    </h3>
    
    <!-- Mobile: Stacked full-width buttons -->
    <div class="flex flex-col gap-2 md:flex-row md:items-center">
      <a href="{% url 'visit_log_create' %}?task={{ task.pk }}" 
         class="w-full md:w-auto flex items-center justify-center gap-2 
                bg-primary text-white py-3 px-4 rounded-lg text-sm font-bold">
        <span class="material-symbols-outlined">edit_note</span>
        Log & Complete
      </a>
      
      <!-- Mobile: Icon-only secondary actions -->
      <div class="flex gap-2 justify-end md:justify-start">
        <a href="{% url 'task_edit' task.pk %}" 
           class="w-10 h-10 flex items-center justify-center border border-slate-200 
                  rounded-lg text-slate-400">
          <span class="material-symbols-outlined">edit</span>
        </a>
        <a href="{% url 'task_delete' task.pk %}" 
           class="w-10 h-10 flex items-center justify-center border border-slate-200 
                  rounded-lg text-slate-400">
          <span class="material-symbols-outlined">delete</span>
        </a>
      </div>
    </div>
  </div>
</div>
```

#### Completed Task Cards (Mobile)
- Reduce opacity further on mobile for visual distinction
- Show "Completed" badge prominently
- Disable/hide edit actions (or make them less prominent)

#### Empty State (Mobile)
```html
<div class="py-12 px-4 text-center">
  <span class="material-symbols-outlined text-4xl text-slate-300 mb-3">
    calendar_today
  </span>
  <h3 class="text-base font-bold mb-1">No Tasks Today</h3>
  <p class="text-sm text-slate-500">Add a log or check the weekly planner.</p>
  
  <!-- Mobile: Quick action buttons -->
  <div class="flex flex-col gap-3 mt-6 md:flex-row md:justify-center">
    <a href="{% url 'visit_log_create' %}" class="...">Add Log</a>
    <a href="{% url 'weekly_planner' %}" class="...">View Week</a>
  </div>
</div>
```

**Files to Modify:**
- `core/templates/core/daily_agenda.html`

---

### 4.3 Visit Log Form (visit_log_form.html)

**Current Issues:**
- Complex 2-column grid layouts break on mobile
- Counter buttons too small for touch (40px)
- Photo upload area may be too large for mobile
- Form sections take too much vertical space
- Collapsible sections need better mobile handling

**Mobile Solution:**

#### Header (Mobile)
```html
<header class="px-4 py-3 border-b border-slate-200 md:px-8 md:h-16">
  <div class="flex items-center justify-between">
    <div>
      <h1 class="text-lg font-bold">Add Log</h1>
      <p class="text-xs text-slate-500 uppercase">Daily Reporting</p>
    </div>
    <!-- Cancel as icon button on mobile -->
    <a href="{{ next|default:url_daily_agenda }}" 
       class="w-10 h-10 flex items-center justify-center text-slate-400 md:hidden">
      <span class="material-symbols-outlined">close</span>
    </a>
  </div>
</header>
```

#### Core Details Section (Mobile)
```html
<!-- Mobile: Single column, stacked fields -->
<div class="grid grid-cols-1 gap-4 md:grid-cols-2 md:gap-8">
  
  <!-- Date - Full width on mobile -->
  <div class="space-y-2">
    <label class="block text-sm font-bold text-slate-700">Date</label>
    <div class="relative">
      <span class="absolute inset-y-0 left-3 flex items-center text-slate-400">
        <span class="material-symbols-outlined">calendar_today</span>
      </span>
      <input type="date" 
             class="w-full pl-10 pr-4 py-3 bg-white border border-slate-200 
                    rounded-lg text-base">  <!-- Larger text for mobile -->
    </div>
  </div>
  
  <!-- Section - Full width on mobile -->
  <div class="space-y-2">
    <label class="block text-sm font-bold text-slate-700">River Section</label>
    <div class="relative">
      <span class="absolute inset-y-0 left-3 flex items-center text-slate-400">
        <span class="material-symbols-outlined">location_on</span>
      </span>
      <select class="w-full pl-10 pr-10 py-3 bg-white border border-slate-200 
                     rounded-lg text-base appearance-none">
        <!-- options -->
      </select>
    </div>
  </div>
  
  <!-- Notes - Full width -->
  <div class="space-y-2 md:col-span-2">
    <label class="block text-sm font-bold text-slate-700">Notes</label>
    <textarea rows="4" 
              class="w-full px-4 py-3 bg-white border border-slate-200 
                     rounded-lg text-base min-h-[120px]"
              placeholder="Describe work completed..."></textarea>
  </div>
</div>
```

#### Metrics Section (Mobile-Optimized Counters)
```html
<!-- Litter Collection - Mobile optimized -->
<div class="grid grid-cols-1 gap-4 md:grid-cols-2 md:gap-8">
  
  <!-- General Litter -->
  <div class="p-4 bg-slate-50 rounded-xl border border-slate-200 text-center md:p-6">
    <span class="material-symbols-outlined text-xl text-slate-400 mb-2 md:text-2xl">
      delete
    </span>
    <h5 class="text-[10px] font-bold text-slate-500 uppercase mb-3 md:mb-4">
      General Litter Bags
    </h5>
    
    <!-- Mobile: Larger touch targets (48px) -->
    <div class="flex items-center justify-center gap-4 md:gap-6">
      <button type="button" onclick="updateCounter('litter_general', -1)" 
              class="w-12 h-12 rounded-full border-2 border-slate-300 flex items-center 
                     justify-center text-slate-500 active:bg-slate-100 md:w-10 md:h-10">
        <span class="material-symbols-outlined text-xl">remove</span>
      </button>
      <span class="text-2xl font-bold min-w-[3rem] md:text-3xl" 
            id="litter_general_value">0</span>
      <button type="button" onclick="updateCounter('litter_general', 1)"
              class="w-12 h-12 rounded-full border-2 border-slate-300 flex items-center 
                     justify-center text-slate-500 active:bg-slate-100 md:w-10 md:h-10">
        <span class="material-symbols-outlined text-xl">add</span>
      </button>
    </div>
  </div>
  
  <!-- Recyclable Litter - Same pattern -->
  <div class="p-4 bg-slate-50 rounded-xl border border-slate-200 text-center md:p-6">
    <!-- Same structure as General Litter -->
  </div>
</div>
```

#### Dynamic Metrics (Weeding/Planting) - Mobile
```html
<!-- Mobile: Full width, stacked layout -->
<div id="weedMetrics" class="section-content p-4 space-y-3 md:p-6 md:space-y-4">
  <!-- Dynamically added metrics will follow this pattern -->
</div>

<!-- Template for new metric row (mobile) -->
<div class="flex flex-col gap-3 p-3 bg-slate-50 rounded-xl border border-slate-200 
            md:grid md:grid-cols-12 md:items-end">
  
  <!-- Species input - full width on mobile -->
  <div class="md:col-span-7">
    <label class="text-[10px] font-bold text-slate-400 uppercase">Species</label>
    <input type="text" placeholder="e.g., Wattle" 
           class="w-full px-3 py-3 bg-white border border-slate-200 rounded-lg text-base">
  </div>
  
  <!-- Counter - inline on mobile -->
  <div class="flex items-center justify-between bg-white px-3 py-2 rounded-lg 
              border border-slate-200 md:col-span-5">
    <button type="button" class="w-10 h-10 flex items-center justify-center text-slate-400">
      <span class="material-symbols-outlined">remove</span>
    </button>
    <span class="font-bold text-base">0</span>
    <button type="button" class="w-10 h-10 flex items-center justify-center text-slate-400">
      <span class="material-symbols-outlined">add</span>
    </button>
  </div>
</div>
```

#### Photo Upload Section (Mobile)
```html
<!-- Mobile: Stacked layout, touch-friendly upload area -->
<div class="space-y-4">
  
  <!-- Photo upload - larger touch target on mobile -->
  <div class="space-y-2">
    <label class="block text-sm font-bold text-slate-700">Photo</label>
    <div id="photoUploadContainer" class="relative group">
      <div class="border-2 border-dashed border-slate-200 rounded-2xl p-8 text-center 
                  bg-slate-50 group-active:border-primary/50 transition-all cursor-pointer 
                  overflow-hidden min-h-[160px] flex flex-col items-center justify-center md:p-10 md:min-h-[200px]">
        <img id="photoPreview" class="absolute inset-0 w-full h-full object-cover hidden">
        <div id="uploadPlaceholder" class="flex flex-col items-center gap-2">
          <span class="material-symbols-outlined text-3xl text-slate-300 md:text-4xl">
            add_a_photo
          </span>
          <p class="text-sm font-medium text-slate-600">Tap to take photo</p>
          <p class="text-xs text-slate-400">or choose from gallery</p>
        </div>
        <input type="file" name="photos-0-file" accept="image/*" capture="environment" 
               onchange="previewPhoto(this)" 
               class="absolute inset-0 opacity-0 cursor-pointer">
      </div>
    </div>
  </div>
  
  <!-- Description - below photo on mobile -->
  <div class="space-y-2">
    <label class="block text-sm font-bold text-slate-700">Description</label>
    <textarea name="photos-0-description" rows="3" 
              class="w-full px-4 py-3 bg-white border border-slate-200 rounded-lg text-base"
              placeholder="What does this photo show?"></textarea>
  </div>
</div>
```

#### Form Actions (Mobile)
```html
<!-- Mobile: Stacked full-width buttons, fixed at bottom -->
<div class="sticky bottom-16 left-0 right-0 bg-white border-t border-slate-200 
            p-4 flex flex-col gap-3 md:static md:bg-transparent md:border-t-0 md:p-0 md:flex-row md:justify-end">
  
  <a href="{{ next|default:url_daily_agenda }}" 
     class="w-full md:w-auto px-6 py-3 border border-slate-200 text-slate-600 
            rounded-xl text-sm font-bold text-center md:px-8">
    Cancel
  </a>
  
  <button type="submit" 
          class="w-full md:w-auto px-6 py-3 bg-primary text-white rounded-xl text-sm 
                 font-bold shadow-lg flex items-center justify-center gap-2 md:px-10">
    <span class="material-symbols-outlined">check_circle</span>
    Submit Log
  </button>
</div>
```

#### Collapsible Sections - Mobile Enhancements
- Increase header tap area to minimum 48px height
- Add visual feedback on tap (active states)
- Consider keeping sections expanded by default on mobile (less tapping)
- Use accordion-style where only one section open at a time

```css
/* Mobile-specific collapsible styles */
@media (max-width: 768px) {
  .section-header {
    min-height: 48px;
    padding: 12px 16px;
  }
  
  .section-header:active {
    background-color: rgba(0,0,0,0.05);
  }
}
```

**Files to Modify:**
- `core/templates/core/visit_log_form.html`

---

## 5. Progressive Enhancement Strategy

### Phase 1: Critical Mobile Layout (MVP)
**Priority:** High  
**Files:** base.html, daily_agenda.html

1. Implement mobile navigation (bottom bar)
2. Fix daily agenda layout for mobile
3. Ensure forms are usable (no overflow)
4. Test on actual mobile devices

### Phase 2: Form Optimization
**Priority:** High  
**Files:** visit_log_form.html

1. Optimize visit log form layout
2. Increase touch target sizes
3. Implement sticky submit buttons
4. Add mobile-specific form validation UI

### Phase 3: Polish & UX Enhancements
**Priority:** Medium

1. Add swipe gestures (e.g., swipe to complete task)
2. Implement pull-to-refresh
3. Add haptic feedback for buttons (if supported)
4. Optimize photo capture flow

### Phase 4: Advanced Mobile Features
**Priority:** Low

1. Offline mode / PWA capabilities
2. Geolocation tagging for logs
3. Voice notes
4. Quick-action widgets

---

## 6. Technical Implementation Details

### 6.1 CSS Architecture

Create new mobile-specific styles in a dedicated CSS file:

```css
/* static/css/mobile.css */

/* Mobile navigation */
.mobile-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 64px;
  background: white;
  border-top: 1px solid #e2e8f0;
  display: flex;
  justify-content: space-around;
  align-items: center;
  z-index: 50;
}

.mobile-nav a {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8px;
  color: #64748b;
  text-decoration: none;
}

.mobile-nav a.active {
  color: #166534;
}

/* Ensure content isn't hidden behind mobile nav */
.mobile-content {
  padding-bottom: 80px; /* 64px nav + 16px padding */
}

/* Touch-friendly form elements */
@media (max-width: 768px) {
  input, select, textarea, button {
    font-size: 16px; /* Prevents iOS zoom on focus */
  }
  
  .touch-target {
    min-height: 44px;
    min-width: 44px;
  }
}
```

### 6.2 JavaScript Enhancements

```javascript
// static/js/mobile.js

// Mobile navigation toggle
document.addEventListener('DOMContentLoaded', function() {
  // Handle mobile menu
  const menuToggle = document.getElementById('mobile-menu-toggle');
  const mobileMenu = document.getElementById('mobile-menu');
  
  if (menuToggle && mobileMenu) {
    menuToggle.addEventListener('click', function() {
      mobileMenu.classList.toggle('hidden');
    });
  }
  
  // Hide mobile nav on scroll down, show on scroll up
  let lastScroll = 0;
  const mobileNav = document.querySelector('.mobile-nav');
  
  if (mobileNav) {
    window.addEventListener('scroll', function() {
      const currentScroll = window.pageYOffset;
      
      if (currentScroll > lastScroll && currentScroll > 100) {
        mobileNav.style.transform = 'translateY(100%)';
      } else {
        mobileNav.style.transform = 'translateY(0)';
      }
      
      lastScroll = currentScroll;
    });
  }
});

// Enhance counter buttons for touch
document.querySelectorAll('.counter-btn').forEach(btn => {
  btn.addEventListener('touchstart', function() {
    this.classList.add('active');
  });
  btn.addEventListener('touchend', function() {
    this.classList.remove('active');
  });
});
```

### 6.3 Template Conditionals

Use Django's request object to detect mobile:

```html
<!-- Check for mobile user agent -->
{% if request.user_agent.is_mobile %}
  <!-- Mobile-specific markup -->
{% else %}
  <!-- Desktop markup -->
{% endif %}

<!-- Or use CSS media queries (preferred) -->
<div class="hidden md:block">Desktop only</div>
<div class="md:hidden">Mobile only</div>
```

### 6.4 Viewport & Meta Tags

Ensure base.html has proper mobile viewport:

```html
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0">
<meta name="theme-color" content="#166534">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
```

---

## 7. Testing Strategy

### 7.1 Device Testing Matrix

| Device | Screen Size | Priority | Focus Areas |
|--------|-------------|----------|-------------|
| iPhone SE | 375x667 | High | Minimum width, touch targets |
| iPhone 14 Pro | 393x852 | High | Modern iOS, notch handling |
| Samsung S23 | 360x780 | High | Android, different density |
| iPad Mini | 768x1024 | Medium | Tablet layout, sidebar toggle |
| iPad Pro | 1024x1366 | Low | Large tablet, near-desktop |

### 7.2 Test Scenarios

1. **Navigation**
   - [ ] Bottom nav visible on mobile, hidden on desktop
   - [ ] Active state shows correctly
   - [ ] All links work and route correctly
   - [ ] Menu toggles properly

2. **Daily Agenda**
   - [ ] Task cards stack vertically on mobile
   - [ ] All action buttons accessible
   - [ ] Floating action button positioned correctly
   - [ ] Completed tasks visually distinct
   - [ ] Empty state renders correctly

3. **Visit Log Form**
   - [ ] No horizontal scrolling
   - [ ] All fields accessible
   - [ ] Counter buttons easy to tap
   - [ ] Photo upload works with camera
   - [ ] Collapsible sections expand/collapse
   - [ ] Submit button always visible
   - [ ] Form submits correctly

4. **Performance**
   - [ ] Page load < 3s on 3G
   - [ ] Images optimized
   - [ ] No layout shift during load

### 7.3 Browser Testing

- Safari (iOS 15+)
- Chrome (Android 12+)
- Samsung Internet
- Firefox Mobile

---

## 8. Accessibility Considerations

### 8.1 Mobile Accessibility Requirements

- Touch targets minimum 44x44px (WCAG 2.5.5)
- Color contrast ratio 4.5:1 minimum
- Screen reader labels for all interactive elements
- Focus indicators visible on mobile
- Support for iOS/Android accessibility features

### 8.2 VoiceOver/TalkBack Support

```html
<!-- Add descriptive labels -->
<button aria-label="Increase general litter count">
  <span class="material-symbols-outlined">add</span>
</button>

<!-- Group related controls -->
<div role="group" aria-label="Litter collection metrics">
  <!-- counters -->
</div>
```

---

## 9. Performance Optimizations

### 9.1 Mobile-Specific Optimizations

1. **Lazy Loading**
   ```html
   <img loading="lazy" src="...">
   ```

2. **Image Optimization**
   - Compress photos before upload
   - Use appropriate sizes for mobile
   - Implement srcset for responsive images

3. **CSS/JS**
   - Minify mobile.css separately
   - Defer non-critical JavaScript
   - Use CSS containment where possible

4. **Touch Events**
   ```javascript
   // Use passive listeners for scroll
   window.addEventListener('scroll', handler, { passive: true });
   ```

---

## 10. Implementation Checklist

### Pre-Implementation
- [ ] Set up mobile testing environment (BrowserStack or physical devices)
- [ ] Review existing Tailwind classes for mobile compatibility
- [ ] Identify all breakpoints needed
- [ ] Create mobile.css file
- [ ] Update base.html with mobile nav

### Phase 1: Navigation
- [ ] Implement mobile bottom navigation
- [ ] Add hamburger menu for secondary items
- [ ] Test navigation flow on mobile
- [ ] Ensure proper z-index layering

### Phase 2: Daily Agenda
- [ ] Refactor task card layout for mobile
- [ ] Add floating action button
- [ ] Optimize header for mobile
- [ ] Test with various task counts
- [ ] Verify completed task styling

### Phase 3: Visit Log Form
- [ ] Convert grid layouts to mobile-friendly
- [ ] Increase counter button sizes
- [ ] Optimize photo upload area
- [ ] Implement sticky form actions
- [ ] Test collapsible sections
- [ ] Validate form submission on mobile

### Phase 4: Polish
- [ ] Add touch feedback states
- [ ] Optimize font sizes for mobile
- [ ] Test photo capture flow
- [ ] Add loading states
- [ ] Implement error handling UI

### Post-Implementation
- [ ] Run full test matrix
- [ ] Performance audit (Lighthouse)
- [ ] Accessibility audit
- [ ] User testing with field workers
- [ ] Documentation update

---

## 11. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Photo upload fails on mobile | High | Test on multiple devices, add error handling, support gallery selection |
| Form too long on mobile | Medium | Implement collapsible sections, sticky headers |
| Touch targets too small | High | Enforce 44px minimum, test with gloves |
| Performance issues on older phones | Medium | Optimize images, lazy loading, code splitting |
| iOS Safari quirks | Medium | Thorough iOS testing, use -webkit prefixes |
| Users prefer desktop | Low | Maintain desktop experience, mobile is additive |

---

## 12. Success Metrics

### Quantitative
- [ ] Mobile page load time < 3 seconds
- [ ] Form completion rate > 90% on mobile
- [ ] Zero horizontal scrolling issues
- [ ] 100% of interactive elements pass touch target size
- [ ] Lighthouse mobile score > 80

### Qualitative
- [ ] Field workers can log activities without assistance
- [ ] Navigation feels natural on mobile
- [ ] Photo capture works seamlessly
- [ ] Forms are easy to complete with one hand

---

## 13. Related Documents

- `product/context/project_overview.md` - Project context
- `product/context/ui_standards.md` - UI design standards
- `product/context/stack.md` - Technology stack
- `product/Done/log_layout.md` - Previous logging form improvements
- `core/templates/core/daily_agenda.html` - Daily agenda template
- `core/templates/core/visit_log_form.html` - Visit log form template
- `templates/base.html` - Base template with navigation

---

## 14. Next Steps

1. **Review this plan** with stakeholders
2. **Set up mobile testing environment**
3. **Create feature branch** for mobile implementation
4. **Start with Phase 1** (Navigation + Daily Agenda)
5. **Test early and often** on real devices
6. **Iterate based on feedback** from field workers

---

## 15. Appendix: Implementation & Testing Guide for Next Agent

### 15.1 Playwright Testing Strategy

**Testing Library:** Playwright for cross-browser mobile testing  
**Why Playwright:** Built-in mobile emulation, screenshot comparisons, touch event simulation

#### Recommended Playwright Setup

```javascript
// playwright.config.js additions for mobile testing
projects: [
  {
    name: 'Mobile Chrome',
    use: {
      ...devices['Pixel 5'],
    },
  },
  {
    name: 'Mobile Safari',
    use: {
      ...devices['iPhone 12'],
    },
  },
  {
    name: 'iPad',
    use: {
      ...devices['iPad (gen 7)'],
    },
  },
],
```

#### Critical Test Cases for Playwright

```javascript
// tests/mobile-daily-agenda.spec.js

const { test, expect } = require('@playwright/test');

test.describe('Daily Agenda Mobile', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/daily-agenda/');
    await page.setViewportSize({ width: 375, height: 812 }); // iPhone X size
  });

  test('task cards stack vertically without overflow', async ({ page }) => {
    // Check no horizontal scroll
    const body = await page.locator('body');
    const scrollWidth = await body.evaluate(el => el.scrollWidth);
    const clientWidth = await body.evaluate(el => el.clientWidth);
    expect(scrollWidth).toBe(clientWidth);
  });

  test('floating action button is visible and clickable', async ({ page }) => {
    const fab = await page.locator('[data-testid="mobile-add-log-btn"]');
    await expect(fab).toBeVisible();
    
    // Check touch target size
    const box = await fab.boundingBox();
    expect(box.width).toBeGreaterThanOrEqual(44);
    expect(box.height).toBeGreaterThanOrEqual(44);
  });

  test('all interactive elements have minimum touch target', async ({ page }) => {
    const buttons = await page.locator('button, a, [role="button"]').all();
    for (const button of buttons) {
      const box = await button.boundingBox();
      if (box) {
        expect(box.width).toBeGreaterThanOrEqual(44);
        expect(box.height).toBeGreaterThanOrEqual(44);
      }
    }
  });

  test('bottom navigation appears on mobile', async ({ page }) => {
    const mobileNav = await page.locator('[data-testid="mobile-nav"]');
    await expect(mobileNav).toBeVisible();
    
    // Desktop sidebar should be hidden
    const desktopSidebar = await page.locator('aside.w-64');
    await expect(desktopSidebar).toBeHidden();
  });

  test('completed tasks have reduced opacity', async ({ page }) => {
    const completedTask = await page.locator('[data-testid="completed-task"]').first();
    const opacity = await completedTask.evaluate(el => 
      window.getComputedStyle(el).opacity
    );
    expect(parseFloat(opacity)).toBeLessThan(1);
  });
});
```

```javascript
// tests/mobile-visit-log.spec.js

test.describe('Visit Log Form Mobile', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/visit-logs/create/');
    await page.setViewportSize({ width: 375, height: 812 });
  });

  test('form has no horizontal scrolling', async ({ page }) => {
    const body = await page.locator('body');
    const hasHScroll = await body.evaluate(el => {
      return el.scrollWidth > el.clientWidth;
    });
    expect(hasHScroll).toBe(false);
  });

  test('counter buttons are large enough for touch', async ({ page }) => {
    const counters = await page.locator('[data-testid="counter-btn"]').all();
    expect(counters.length).toBeGreaterThan(0);
    
    for (const counter of counters) {
      const box = await counter.boundingBox();
      expect(box.width).toBeGreaterThanOrEqual(48); // 48px for mobile
      expect(box.height).toBeGreaterThanOrEqual(48);
    }
  });

  test('collapsible sections expand/collapse', async ({ page }) => {
    const section = await page.locator('[data-testid="collapsible-section"]').first();
    const content = section.locator('[data-testid="section-content"]');
    
    // Initially visible
    await expect(content).toBeVisible();
    
    // Click header to collapse
    await section.locator('[data-testid="section-header"]').click();
    await expect(content).toBeHidden();
    
    // Click again to expand
    await section.locator('[data-testid="section-header"]').click();
    await expect(content).toBeVisible();
  });

  test('sticky submit button stays visible on scroll', async ({ page }) => {
    // Scroll to bottom
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    
    const submitBtn = await page.locator('[data-testid="submit-log-btn"]');
    await expect(submitBtn).toBeInViewport();
  });

  test('photo upload area is accessible', async ({ page }) => {
    const uploadArea = await page.locator('[data-testid="photo-upload"]');
    await expect(uploadArea).toBeVisible();
    
    // Check minimum touch target
    const box = await uploadArea.boundingBox();
    expect(box.width).toBeGreaterThanOrEqual(160);
    expect(box.height).toBeGreaterThanOrEqual(160);
  });

  test('form submission works on mobile', async ({ page }) => {
    // Fill required fields
    await page.selectOption('select[name="section"]', '1');
    await page.fill('textarea[name="notes"]', 'Mobile test log entry');
    
    // Submit form
    await page.click('[data-testid="submit-log-btn"]');
    
    // Check for success or validation
    await expect(page.locator('text=success, text=error, or form validation')).toBeVisible();
  });
});
```

```javascript
// tests/mobile-navigation.spec.js

test.describe('Mobile Navigation', () => {
  test('bottom nav routes correctly', async ({ page }) => {
    await page.goto('/');
    await page.setViewportSize({ width: 375, height: 812 });
    
    // Click daily agenda
    await page.click('[data-testid="nav-agenda"]');
    await expect(page).toHaveURL(/daily-agenda/);
    
    // Click planner
    await page.click('[data-testid="nav-planner"]');
    await expect(page).toHaveURL(/planner/);
  });

  test('more menu reveals secondary options', async ({ page }) => {
    await page.goto('/');
    await page.setViewportSize({ width: 375, height: 812 });
    
    // Click more button
    await page.click('[data-testid="nav-more"]');
    
    // Check slide-up menu appears
    const menu = await page.locator('[data-testid="mobile-menu"]');
    await expect(menu).toBeVisible();
    
    // Check menu items
    await expect(menu.locator('text=Task Templates')).toBeVisible();
    await expect(menu.locator('text=Logout')).toBeVisible();
  });
});
```

### 15.2 Implementation Approach

#### Step-by-Step Implementation Order

**Phase 1: Foundation (Day 1)**
1. Update `base.html` viewport meta tag
2. Create `static/css/mobile.css` with base mobile styles
3. Implement mobile navigation component in `base.html`
4. Test: Navigation visible on mobile, hidden on desktop

**Phase 2: Daily Agenda (Day 2-3)**
1. Refactor header section with mobile-optimized layout
2. Convert task cards to mobile-friendly vertical stack
3. Add floating action button (FAB) for quick log creation
4. Optimize completed task styling for mobile
5. Test with Playwright: viewport, touch targets, no overflow

**Phase 3: Visit Log Form (Day 3-4)**
1. Convert grid layouts to responsive single-column
2. Increase counter button sizes (48px on mobile)
3. Optimize collapsible sections for touch
4. Implement sticky form actions
5. Enhance photo upload area
6. Test with Playwright: form submission, scroll behavior, touch targets

**Phase 4: Testing & Polish (Day 5)**
1. Run full Playwright test suite
2. Fix any failing tests
3. Performance audit (Lighthouse)
4. Accessibility audit
5. Cross-browser verification

#### Code Implementation Tips

**1. Tailwind Class Strategy**
```html
<!-- Always use mobile-first classes -->
<!-- Bad: -->
<div class="grid-cols-2 md:grid-cols-1">

<!-- Good: -->
<div class="grid-cols-1 md:grid-cols-2">
```

**2. Mobile-Only Content**
```html
<!-- Use hidden/md:block pattern -->
<div class="md:hidden">
  <!-- Mobile-only: Bottom nav, FAB, etc. -->
</div>
<div class="hidden md:block">
  <!-- Desktop-only: Sidebar -->
</div>
```

**3. Touch Target Enforcement**
```css
/* mobile.css */
.touch-target {
  min-height: 44px;
  min-width: 44px;
}

/* Increase on mobile */
@media (max-width: 768px) {
  .counter-btn {
    width: 48px;
    height: 48px;
  }
}
```

**4. Testing Attributes**
Add `data-testid` attributes for reliable Playwright selectors:
```html
<button data-testid="counter-btn" ...>
<nav data-testid="mobile-nav" ...>
<div data-testid="collapsible-section" ...>
```

### 15.3 Common Gotchas

**1. iOS Safari Issues**
- Input zoom on focus (fix with `font-size: 16px`)
- 100vh includes URL bar (use `-webkit-fill-available`)
- Touch delays on buttons (use `touch-action: manipulation`)

**2. Django Template Context**
- Some views may not pass `request` to templates
- Check for mobile user agent in views if needed:
```python
# views.py
import re

def is_mobile(request):
    user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
    return bool(re.search(r'mobile|android|iphone|ipad', user_agent))
```

**3. Formset Handling**
- Dynamic metric rows need proper indexing on mobile
- Test that form submission works with added/removed rows
- Verify management form fields are correctly updated

**4. Photo Upload**
- iOS may require `capture="environment"` for camera
- Test file size limits on mobile networks
- Add loading state during upload

### 15.4 Testing Commands

```bash
# Run Playwright tests
npx playwright test tests/mobile-*.spec.js

# Run with specific device
npx playwright test --project="Mobile Chrome"

# Run with UI mode for debugging
npx playwright test --ui

# Generate report
npx playwright show-report

# Lighthouse mobile audit
npx lighthouse http://localhost:8000/daily-agenda/ \
  --emulated-form-factor=mobile \
  --throttling-method=simulate \
  --output=html
```

### 15.5 Debugging Tips

**Use Playwright Trace Viewer:**
```javascript
// playwright.config.js
trace: 'on-first-retry', // or 'retain-on-failure'
```

**Screenshot on Failure:**
```javascript
// In test
test.afterEach(async ({ page }, testInfo) => {
  if (testInfo.status !== testInfo.expectedStatus) {
    await page.screenshot({ path: `test-results/${testInfo.title}.png` });
  }
});
```

**Mobile DevTools:**
- Chrome: Toggle device toolbar (Ctrl+Shift+M)
- Test touch events with "Touch" enabled
- Simulate slow network conditions

### 15.6 Definition of Done

Before marking complete, verify:

**Functionality:**
- [ ] All tests pass (`npx playwright test`)
- [ ] No console errors on mobile
- [ ] Form submissions work correctly
- [ ] Navigation works on all mobile devices

**Visual:**
- [ ] No horizontal scrolling at 375px width
- [ ] All touch targets ≥44px (48px preferred)
- [ ] Text readable without zoom (16px minimum)
- [ ] Spacing adequate for thumb navigation

**Performance:**
- [ ] Lighthouse mobile score ≥80
- [ ] First Contentful Paint < 2s
- [ ] Time to Interactive < 4s

**Accessibility:**
- [ ] Screen reader labels present
- [ ] Focus indicators visible
- [ ] Color contrast WCAG AA compliant

---

**Status:** Ready for Implementation  
**Priority:** High  
**Assigned To:** TBD  
**Target Completion:** TBD  
**Testing Framework:** Playwright  
**Branch Strategy:** `feature/mobile-responsive`
