# PRD: Playwright E2E Testing Implementation

## 1. Problem Statement

The River Project currently lacks end-to-end (E2E) testing, making it difficult to:
- Verify critical user workflows function correctly across browsers and devices
- Catch regressions in UI interactions (drag-and-drop, modals, navigation)
- Validate mobile responsiveness consistently
- Ensure accessibility requirements are met
- Prevent deployment of broken features to production

## 2. Strategic Goal

Implement a comprehensive Playwright E2E testing suite that provides:
- Cross-browser testing (Chrome, Firefox, Safari/WebKit)
- Mobile device emulation (iPhone, iPad, Android)
- Automated regression testing for core user workflows
- Visual regression testing capabilities
- CI/CD integration for pre-deployment validation

## 3. Proposed Scope

### Core Implementation:
- **Python-based Playwright:** Use `pytest-playwright` for Django integration
- **Test Structure:** Organized by feature in `e2e/` directory
- **Device Coverage:** Desktop (1920x1080), Tablet (768x1024), Mobile (375x812)
- **Critical Workflows:** Daily agenda, task management, visit logging, section navigation
- **Visual Testing:** Screenshot comparisons for UI consistency

### Inclusions:
- Authentication flow testing
- CRUD operations on tasks and sections
- Drag-and-drop Kanban board interactions
- Form validation and submission
- Mobile navigation and touch interactions
- Accessibility checks (axe-core integration)

### Exclusions:
- Performance/load testing (use separate tools like Locust)
- API endpoint testing (unit tests cover this)
- Third-party integrations (mock external services)

## 4. UX/UI Testing Requirements

### Mobile-First Testing:
- All tests must run on mobile viewport by default
- Touch target verification (minimum 44px)
- Bottom navigation visibility and functionality
- Swipe gestures where applicable

### Desktop Testing:
- Sidebar navigation interactions
- Drag-and-drop Kanban board
- Modal and popup behavior
- Keyboard navigation (accessibility)

## 5. Technical Challenges

1. **Test Data Management:** Setting up consistent test data across test runs
2. **Authentication:** Handling Django admin authentication in E2E tests
3. **File Uploads:** Testing photo uploads in visit logs
4. **Timing Issues:** Waiting for AJAX calls (Kanban updates) and animations
5. **Environment Consistency:** Ensuring tests run identically in CI and local dev

## 6. Success Criteria

- **Coverage:** 80% of critical user paths covered by E2E tests
- **Performance:** Test suite completes in under 10 minutes
- **Reliability:** <5% flaky test rate (tests passing consistently)
- **Maintainability:** Tests use page object pattern for reusability
- **CI Integration:** All tests pass before merging to main branch

---

# Technical Blueprint: Playwright E2E Testing

## 1. Dependencies & Setup

### Python Packages (`requirements-dev.txt`):
```
pytest-playwright>=0.4.0
playwright>=1.40.0
pytest-django>=4.7.0
pytest-xdist>=3.5.0  # Parallel test execution
```

> ⚠️ **Not yet installed.** `requirements.txt` has only runtime deps (Django,
> psycopg2, Pillow, …) — no pytest, pytest-django, pytest-playwright, or
> pytest-xdist, and no `requirements-dev.txt` exists. The project currently runs
> tests via Django's unittest runner (`manage.py test`). Adopting Playwright means
> adopting pytest. **Decision needed:** confirm pytest as the E2E runner first.

### Browser Installation:
```bash
playwright install chromium firefox webkit
playwright install-deps chromium  # Install OS dependencies
```

## 2. Directory Structure

```
e2e/
├── conftest.py                 # Shared fixtures and configuration
├── pages/                      # Page Object Models
│   ├── __init__.py
│   ├── base_page.py           # Common page operations
│   ├── login_page.py
│   ├── daily_agenda_page.py
│   ├── task_kanban_page.py
│   ├── task_form_page.py
│   └── section_list_page.py
├── tests/                      # Test files organized by feature
│   ├── test_authentication.py
│   ├── test_daily_agenda.py
│   ├── test_task_kanban.py
│   ├── test_task_management.py
│   ├── test_section_management.py
│   ├── test_visit_logging.py
│   └── test_mobile_responsive.py
├── fixtures/                   # Test data and utilities
│   ├── __init__.py
│   └── test_data.py
└── screenshots/                # Baseline screenshots for visual testing
    └── .gitkeep
```

## 3. Configuration (`e2e/conftest.py`)

```python
import pytest
from playwright.sync_api import Page, expect
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    """Ensure database is available for all tests."""
    pass

@pytest.fixture
def base_url(live_server):
    """Django test server base URL (random port) — never hardcode localhost:8000.

    Note: app URLs are namespaced under `/core/` (e.g. `/core/todo/`, not `/todo/`),
    except `/admin/...`.
    """
    return live_server.url

@pytest.fixture
def authenticated_page(page: Page, django_db_blocker, base_url) -> Page:
    """Fixture that logs in a test user and returns authenticated page."""
    with django_db_blocker.unblock():
        user = User.objects.create_superuser(
            username='testadmin',
            email='test@example.com',
            password='testpass123'
        )
    
    # Navigate to login page
    page.goto(f'{base_url}/admin/login/')
    
    # Fill in credentials
    page.fill('input[name="username"]', 'testadmin')
    page.fill('input[name="password"]', 'testpass123')
    page.click('input[type="submit"]')
    
    # Wait for redirect to admin or dashboard
    page.wait_for_load_state('networkidle')
    
    yield page
    
    # Cleanup
    with django_db_blocker.unblock():
        user.delete()

@pytest.fixture(params=[
    {"name": "Desktop Chrome", "viewport": {"width": 1920, "height": 1080}},
    {"name": "iPad", "viewport": {"width": 768, "height": 1024}},
    {"name": "iPhone 12", "viewport": {"width": 390, "height": 844}},
    {"name": "Pixel 5", "viewport": {"width": 393, "height": 851}},
])
def device_viewport(request):
    """Parametrize tests across different device viewports."""
    return request.param

@pytest.fixture(autouse=True)
def set_viewport(page: Page, device_viewport):
    """Automatically set viewport size for each test."""
    page.set_viewport_size(device_viewport["viewport"])
    yield
```

## 4. Page Object Models

### Base Page (`e2e/pages/base_page.py`):
```python
from playwright.sync_api import Page, expect

class BasePage:
    """Base page object with common operations."""
    
    def __init__(self, page: Page):
        self.page = page
    
    def navigate(self, path: str):
        """Navigate to a specific path."""
        self.page.goto(path)  # relative — resolved against the base_url fixture (live_server.url)
        self.page.wait_for_load_state('networkidle')
    
    def click_link(self, text: str):
        """Click a link by text content."""
        self.page.click(f'text={text}')
    
    def fill_form_field(self, label: str, value: str):
        """Fill a form field by its label."""
        self.page.fill(f'input[placeholder*="{label}"], label:has-text("{label}") + input', value)
    
    def assert_no_console_errors(self):
        """Assert no console errors occurred."""
        logs = self.page.evaluate("() => { return window.errors || []; }")
        assert len(logs) == 0, f"Console errors found: {logs}"
    
    def take_screenshot(self, name: str):
        """Take a screenshot for debugging."""
        self.page.screenshot(path=f"e2e/screenshots/{name}.png")
```

### Task Kanban Page (`e2e/pages/task_kanban_page.py`):
```python
from playwright.sync_api import Page, expect
from .base_page import BasePage

class TaskKanbanPage(BasePage):
    """Page object for the Rolling To-Do Kanban board."""
    
    def __init__(self, page: Page):
        super().__init__(page)
        self.path = '/core/todo/'
    
    def navigate(self):
        """Navigate to Kanban board."""
        super().navigate(self.path)
        # Wait for columns to be visible
        expect(self.page.locator('#todo')).to_be_visible()
    
    def create_task(self, instructions: str, assignee_type: str = 'team', urgent: bool = False):
        """Create a new rolling task via modal."""
        # Click New Task button
        self.page.click('text=New Task')
        
        # Wait for modal
        expect(self.page.locator('#taskModal')).to_be_visible()
        
        # Fill form
        self.page.fill('textarea[name="instructions"]', instructions)
        self.page.click(f'input[value="{assignee_type}"]')
        
        if urgent:
            self.page.check('input[name="is_urgent"]')
        
        # Submit
        self.page.click('button[type="submit"]')
        
        # Wait for modal to close
        expect(self.page.locator('#taskModal')).not_to_be_visible()
    
    def drag_task_to_column(self, task_text: str, target_column: str):
        """Drag a task card to a different column."""
        # Find task card
        task_card = self.page.locator(f'.kanban-column div:has-text("{task_text}")').first
        
        # Get target column
        target = self.page.locator(f'#{target_column}')
        
        # Perform drag and drop
        task_card.drag_to(target)
        
        # Wait for AJAX update
        self.page.wait_for_timeout(500)  # Small delay for re-indexing
    
    def get_tasks_in_column(self, column_id: str) -> list:
        """Get list of task texts in a column."""
        column = self.page.locator(f'#{column_id}')
        tasks = column.locator('[data-task-id]').all_text_contents()
        return tasks
    
    def delete_task(self, task_text: str):
        """Delete a task from the board."""
        # Hover over task to reveal delete button
        task = self.page.locator(f'.kanban-column div:has-text("{task_text}")').first
        task.hover()
        
        # Click delete
        task.locator('a[title="Delete Task"]').click()
        
        # Confirm deletion (if confirmation dialog exists)
        self.page.click('text=Confirm')  # Adjust based on actual UI
    
    def assert_task_in_column(self, task_text: str, column_id: str):
        """Assert a task exists in a specific column."""
        column = self.page.locator(f'#{column_id}')
        expect(column.locator(f'text={task_text}')).to_be_visible()
```

## 5. Test Implementation Examples

### Authentication Tests (`e2e/tests/test_authentication.py`):
```python
import pytest
from playwright.sync_api import Page, expect

def test_admin_login(page: Page, live_server):
    """Test admin can log in successfully."""
    page.goto(f'{live_server.url}/admin/login/')
    
    # Fill credentials
    page.fill('input[name="username"]', 'admin')
    page.fill('input[name="password"]', 'adminpass')
    page.click('input[type="submit"]')
    
    # Assert redirect to admin dashboard
    expect(page).to_have_url(f'{live_server.url}/admin/')
    expect(page.locator('text=Site administration')).to_be_visible()

def test_invalid_login_shows_error(page: Page, live_server):
    """Test invalid credentials show error message."""
    page.goto(f'{live_server.url}/admin/login/')
    
    page.fill('input[name="username"]', 'wronguser')
    page.fill('input[name="password"]', 'wrongpass')
    page.click('input[type="submit"]')
    
    # Should stay on login page with error
    expect(page).to_have_url(f'{live_server.url}/admin/login/')
    expect(page.locator('.errornote')).to_be_visible()
```

### Kanban Board Tests (`e2e/tests/test_task_kanban.py`):
```python
import pytest
from playwright.sync_api import Page, expect
from e2e.pages.task_kanban_page import TaskKanbanPage

class TestTaskKanban:
    def test_create_rolling_task(self, authenticated_page: Page):
        """Test creating a new rolling task."""
        kanban = TaskKanbanPage(authenticated_page)
        kanban.navigate()
        
        # Create task
        kanban.create_task(
            instructions="Test rolling task",
            assignee_type="team",
            urgent=True
        )
        
        # Assert task appears in To Do column
        kanban.assert_task_in_column("Test rolling task", "todo")
    
    def test_drag_task_to_doing(self, authenticated_page: Page):
        """Test dragging task from Todo to Doing column."""
        kanban = TaskKanbanPage(authenticated_page)
        kanban.navigate()
        
        # Create a task first
        kanban.create_task("Task to move")
        
        # Drag to Doing
        kanban.drag_task_to_column("Task to move", "doing")
        
        # Assert task moved
        kanban.assert_task_in_column("Task to move", "doing")
    
    def test_urgent_task_has_visual_indicator(self, authenticated_page: Page):
        """Test urgent tasks display urgent badge."""
        kanban = TaskKanbanPage(authenticated_page)
        kanban.navigate()
        
        kanban.create_task("Urgent task", urgent=True)
        
        # Check for urgent indicator
        task = authenticated_page.locator('text=Urgent task')
        expect(task.locator('..').locator('text=Urgent')).to_be_visible()
```

### Mobile Responsive Tests (`e2e/tests/test_mobile_responsive.py`):
```python
import pytest
from playwright.sync_api import Page, expect

@pytest.mark.parametrize("viewport", [
    {"width": 375, "height": 812, "name": "iPhone X"},
    {"width": 390, "height": 844, "name": "iPhone 12"},
    {"width": 393, "height": 851, "name": "Pixel 5"},
])
def test_no_horizontal_scroll_on_mobile(authenticated_page: Page, viewport):
    """Test that pages don't have horizontal scroll on mobile devices."""
    authenticated_page.set_viewport_size(viewport)
    authenticated_page.goto('/core/todo/')
    
    # Check scroll width equals client width (no horizontal overflow)
    body = authenticated_page.locator('body')
    scroll_width = body.evaluate('el => el.scrollWidth')
    client_width = body.evaluate('el => el.clientWidth')
    
    assert scroll_width == client_width, f"Horizontal scroll detected on {viewport['name']}"

def test_mobile_bottom_navigation_visible(authenticated_page: Page):
    """Test mobile bottom navigation is visible on small screens."""
    authenticated_page.set_viewport_size({"width": 375, "height": 812})
    authenticated_page.goto('/core/daily-agenda/')
    
    # Mobile nav should be visible
    expect(authenticated_page.locator('[data-testid="mobile-nav"]')).to_be_visible()
    
    # Desktop sidebar should be hidden
    expect(authenticated_page.locator('aside.w-64')).to_be_hidden()

def test_touch_targets_minimum_size(authenticated_page: Page):
    """Test all interactive elements meet minimum touch target size (44px)."""
    authenticated_page.set_viewport_size({"width": 375, "height": 812})
    authenticated_page.goto('/core/todo/')
    
    # Get all interactive elements
    elements = authenticated_page.locator('button, a, [role="button"], input[type="checkbox"]').all()
    
    for element in elements:
        box = element.bounding_box()
        if box:
            assert box['width'] >= 44, f"Element width {box['width']}px < 44px minimum"
            assert box['height'] >= 44, f"Element height {box['height']}px < 44px minimum"
```

## 6. Running Tests

### Local Development:
```bash
# Run all E2E tests
pytest e2e/ -v

# Run with headed browser (visible)
pytest e2e/ --headed -v

# Run specific test file
pytest e2e/tests/test_task_kanban.py -v

# Run with UI mode (interactive debugging)
pytest e2e/ --headed --browser chromium

# Run parallel tests (4 workers)
pytest e2e/ -n 4

# Run on specific device
pytest e2e/tests/test_mobile_responsive.py --viewport "iPhone 12"

# Generate HTML report
pytest e2e/ --html=report.html --self-contained-html
```

### CI/CD Integration (GitHub Actions):
```yaml
name: E2E Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
          playwright install chromium
      - name: Run Django migrations
        run: python manage.py migrate
      - name: Run E2E tests
        run: pytest e2e/ -v --browser chromium
      - name: Upload screenshots on failure
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: screenshots
          path: e2e/screenshots/
```

## 7. Test Data Management

### Fixtures (`e2e/fixtures/test_data.py`):
```python
import pytest
from django.test import Client
from core.models import Section, Task, TaskTemplate, TaskType

@pytest.fixture
def sample_section(db):
    """Create a sample section for testing."""
    return Section.objects.create(
        name="Test Section",
        current_stage="mitigation",
        position=1
    )

@pytest.fixture
def sample_task_type(db):
    """Create a sample task type."""
    return TaskType.objects.create(
        name="Weeding",
        code="weeding",
        color_class="bg-green-100"
    )

@pytest.fixture
def sample_rolling_tasks(db, sample_section, sample_task_type):
    """Create sample rolling tasks for Kanban testing."""
    tasks = []
    for i, status in enumerate(['todo', 'todo', 'doing', 'done']):
        task = Task.objects.create(
            instructions=f"Test Task {i+1}",
            is_rolling=True,
            todo_status=status,
            todo_position=i,
            section=sample_section,
            assignee_type='team'
        )
        tasks.append(task)
    return tasks
```

## 8. Step-by-Step Implementation Checklist

1. **Setup:**
   - [ ] Add pytest-playwright to requirements-dev.txt
   - [ ] Create e2e/ directory structure
   - [ ] Install Playwright browsers: `playwright install`
   - [ ] Create conftest.py with fixtures
   - [ ] Verify tests can connect to Django test server

2. **Page Objects:**
   - [ ] Implement BasePage with common operations
   - [ ] Create LoginPage for authentication
   - [ ] Create DailyAgendaPage for agenda workflows
   - [ ] Create TaskKanbanPage for drag-and-drop testing
   - [ ] Create TaskFormPage for form interactions
   - [ ] Create SectionListPage for section management

3. **Core Test Suites:**
   - [ ] test_authentication.py (login/logout flows)
   - [ ] test_daily_agenda.py (viewing, completing tasks)
   - [ ] test_task_kanban.py (CRUD, drag-drop, urgent toggle)
   - [ ] test_task_management.py (create, edit, delete, series)
   - [ ] test_visit_logging.py (log creation, metrics, photos)
   - [ ] test_mobile_responsive.py (viewport, touch targets, navigation)

4. **Advanced Features:**
   - [ ] Implement visual regression testing
   - [ ] Add accessibility checks with axe-core
   - [ ] Configure parallel test execution
   - [ ] Set up CI/CD pipeline integration
   - [ ] Create test documentation for team

## 9. Test Coverage Targets

| Feature | Critical Paths | Coverage Goal |
|---------|---------------|---------------|
| Authentication | Login, Logout, Permission checks | 100% |
| Daily Agenda | View, Complete tasks, Filter by date | 90% |
| Task Kanban | Create, Move, Delete, Urgent toggle | 95% |
| Task Forms | Create series, Edit, Validation | 85% |
| Visit Logs | Create log, Add metrics, Upload photos | 80% |
| Sections | View, Update stage | 70% |
| Mobile UI | Navigation, Touch targets, Responsive | 90% |

---

# User Stories

## Story 1: Playwright Infrastructure
**Value Proposition:** As a Developer, I want Playwright installed and configured so that I can write reliable E2E tests for the application.

**Acceptance Criteria:**
- [ ] `pytest-playwright` installed and configured
- [ ] Browsers (Chromium, Firefox, WebKit) installed
- [ ] `e2e/conftest.py` created with authentication fixture
- [ ] Tests can connect to Django test server
- [ ] Sample test runs successfully

**Test Plan:**
- Run `pytest e2e/test_sample.py` and verify it passes
- Verify screenshots are captured on failure

## Story 2: Page Object Models
**Value Proposition:** As a Developer, I want reusable page objects so that E2E tests are maintainable and readable.

**Acceptance Criteria:**
- [ ] BasePage implemented with common operations
- [ ] Page objects created for all major pages
- [ ] Page objects use data-testid attributes
- [ ] Tests use page objects exclusively

**Test Plan:**
- Review test code to ensure no direct page.locator calls in test files
- Verify page objects handle all common interactions

## Story 3: Critical Workflow Coverage
**Value Proposition:** As a QA Engineer, I want E2E tests covering critical paths so that regressions are caught before production.

**Acceptance Criteria:**
- [ ] Authentication flow tested
- [ ] Task creation (single and series) tested
- [ ] Kanban drag-and-drop tested
- [ ] Visit logging workflow tested
- [ ] All tests pass consistently (<5% flake rate)

**Test Plan:**
- Run full E2E suite 5 times locally
- All runs should pass without intervention
- Measure average execution time

## Story 4: Mobile Testing
**Value Proposition:** As a Product Manager, I want automated mobile testing so that mobile UX issues are caught early.

**Acceptance Criteria:**
- [ ] Tests run on mobile viewports (iPhone, Pixel)
- [ ] Touch target size verification automated
- [ ] Bottom navigation tested
- [ ] No horizontal scroll on mobile verified
- [ ] Mobile-specific interactions tested

**Test Plan:**
- Manually test mobile features, then automate
- Compare automated vs manual test results
- Verify tests catch known mobile issues

## Story 5: CI/CD Integration
**Value Proposition:** As a Tech Lead, I want E2E tests in CI/CD so that broken code cannot be merged.

**Acceptance Criteria:**
- [ ] GitHub Actions workflow configured
- [ ] Tests run on every PR
- [ ] PRs blocked if E2E tests fail
- [ ] Screenshots uploaded on failure
- [ ] Test duration < 10 minutes

**Test Plan:**
- Create test PR with intentional failure
- Verify CI blocks merge
- Verify artifacts include screenshots
- Measure CI execution time

---

**Status:** Ready for Implementation  
**Priority:** High  
**Estimated Effort:** 3-4 days  
**Dependencies:** None (can be implemented in parallel with features)
