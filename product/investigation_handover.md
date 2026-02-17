# Investigation Handover: 500 Error on /core/daily-agenda/

## Investigation Status
**Date**: 2026-02-16  
**Current Status**: Partially Resolved - Template errors fixed, but 500 error may persist  
**Investigator**: AI Assistant  
**Next Investigator**: [Your Name]

## Problem Statement
Accessing `/core/daily-agenda/` results in a 500 Internal Server Error. Initial investigation identified template rendering issues, but the root cause may be deeper.

## Debugging Completed So Far

### 1. Initial Error Analysis
- **Error**: `500 Internal Server Error` on GET request to `/core/daily-agenda/`
- **Server Log**: Minimal details in browser, full error in Django console
- **Timing**: Error occurs immediately on page load

### 2. Template Issues Identified and Fixed
**Files Modified**:
- `core/templates/core/daily_agenda.html`
- `core/templates/core/weekly_planner.html`

**Problem**: Templates were accessing attributes of `None` when `task.section` was null:
```html
<!-- ERROR: Causes AttributeError when task.section is None -->
{{ task.section.name|default:"No Section" }}
{{ task.section.color_code|default:'#808080' }}
```

**Solution**: Replaced with explicit `{% if %}` checks:
```html
<!-- FIXED: Handles None properly -->
{% if task.section %}
    {{ task.section.name }}
{% else %}
    No Section
{% endif %}
```

### 3. Authentication Check
- View uses `LoginRequiredMixin`
- Created test superuser: `username=test`
- Login URL: `/accounts/login/`
- Login redirect: `/`

### 4. Database State Verification
- **Sections**: 8 example sections created via migration `0003_add_example_sections.py`
- **Task Templates**: 19 templates (3 original + 16 real-world) via migration `0002_add_real_world_task_templates.py`
- **Test Tasks**: Created 2 test tasks (one with section, one without)

### 5. View Logic Test
- `DailyAgendaView` tested in isolation - works correctly
- Query filters: `date=today` and `assignee_type='team'`
- Ordering: `section__name`

## Potential Root Causes Still to Investigate

### Priority 1: Template Rendering Chain
1. **Base Template Issues**: `templates/base.html` may have errors
2. **Static Files**: Missing Bootstrap/CDN links
3. **Template Inheritance**: `{% extends 'base.html' %}` chain issues

### Priority 2: Authentication/Authorization
1. **Login Required**: User not authenticated
2. **Middleware Issues**: Authentication middleware configuration
3. **Session Problems**: Cookie/session issues

### Priority 3: Database/Query Issues
1. **Query Errors**: `section__name` ordering when section is `None`
2. **Database Connection**: SQLite file permissions/corruption
3. **Migration State**: Inconsistent migration application

### Priority 4: Server Configuration
1. **DEBUG Setting**: Should be `True` for development
2. **ALLOWED_HOSTS**: May be restricting access
3. **Static Files**: Incorrect `STATIC_URL` or `STATIC_ROOT`

## Diagnostic Print Statements to Add

### 1. Add to `core/views.py` - DailyAgendaView:
```python
class DailyAgendaView(LoginRequiredMixin, ListView):
    model = Task
    template_name = 'core/daily_agenda.html'
    context_object_name = 'tasks'
    
    def get_queryset(self):
        today = timezone.now().date()
        print(f"[DEBUG] DailyAgendaView - Date filter: {today}")
        print(f"[DEBUG] DailyAgendaView - User: {self.request.user}")
        
        queryset = Task.objects.filter(
            date=today,
            assignee_type='team'
        ).order_by('section__name')
        
        print(f"[DEBUG] DailyAgendaView - Query count: {queryset.count()}")
        for task in queryset:
            print(f"[DEBUG] Task: {task.id}, Section: {task.section}, Completed: {task.is_completed}")
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['today'] = timezone.now().date()
        print(f"[DEBUG] DailyAgendaView context keys: {list(context.keys())}")
        return context
```

### 2. Add to `templates/base.html` (temporary):
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Liesbeek Master Plan{% endblock %}</title>
    
    <!-- DEBUG: Check CDN loading -->
    <script>
        console.log("[DEBUG] Base template loading...");
        console.log("[DEBUG] User agent:", navigator.userAgent);
    </script>
    
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css">
    
    <style>
        /* Existing styles... */
    </style>
</head>
<body>
    <!-- DEBUG: Check template rendering -->
    <div style="display: none;" id="debug-info">
        Template: {{ request.resolver_match.url_name|default:"unknown" }}
        User: {{ request.user.username|default:"anonymous" }}
    </div>
    
    <!-- Existing content... -->
```

### 3. Create Diagnostic Middleware (temporary):
Create `core/middleware.py`:
```python
import traceback

class DebugMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        print(f"[DEBUG MIDDLEWARE] Request path: {request.path}")
        print(f"[DEBUG MIDDLEWARE] User: {request.user}")
        print(f"[DEBUG MIDDLEWARE] Authenticated: {request.user.is_authenticated}")
        
        response = self.get_response(request)
        
        print(f"[DEBUG MIDDLEWARE] Response status: {response.status_code}")
        print(f"[DEBUG MIDDLEWARE] Response content-type: {response.get('Content-Type', 'unknown')}")
        
        return response
    
    def process_exception(self, request, exception):
        print(f"[DEBUG MIDDLEWARE] EXCEPTION: {exception}")
        print(f"[DEBUG MIDDLEWARE] TRACEBACK:")
        traceback.print_exc()
        return None
```

Add to `settings.py`:
```python
MIDDLEWARE = [
    'core.middleware.DebugMiddleware',  # Add at the top
    # ... existing middleware
]
```

## Step-by-Step Investigation Plan

### Step 1: Enable Detailed Error Logging
1. Check `settings.py` for `DEBUG = True`
2. Check `ALLOWED_HOSTS = ['*']` for development
3. Run with `python manage.py runserver --verbosity 2`

### Step 2: Test Authentication Flow
1. Access `/admin/` and login with `username=test`
2. Check if session persists
3. Try accessing `/core/daily-agenda/` after login

### Step 3: Isolate Template Issues
1. Create minimal test template:
```html
<!-- test_template.html -->
<!DOCTYPE html>
<html>
<body>
    <h1>Test Template</h1>
    <p>If this loads, base template is the issue.</p>
</body>
</html>
```

2. Create test view:
```python
def test_view(request):
    return render(request, 'test_template.html')
```

### Step 4: Database Query Verification
Run diagnostic query:
```python
python manage.py shell -c "
from django.utils import timezone
from core.models import Task
today = timezone.now().date()
tasks = Task.objects.filter(date=today, assignee_type='team')
print(f'Tasks for today: {tasks.count()}')
for t in tasks:
    print(f'  ID: {t.id}, Section: {t.section}, Instructions: {t.instructions[:30]}...')
"
```

### Step 5: Check Static Files
1. Run `python manage.py collectstatic`
2. Check `STATIC_URL` and `STATIC_ROOT` in settings
3. Verify `static/` directory exists and has files

## Expected Console Output if Working

If the fix is successful, you should see:
```
[DEBUG] DailyAgendaView - Date filter: 2026-02-16
[DEBUG] DailyAgendaView - User: test
[DEBUG] DailyAgendaView - Query count: 2
[DEBUG] Task: 1, Section: Black River Confluence, Completed: False
[DEBUG] Task: 2, Section: None, Completed: False
[DEBUG] DailyAgendaView context keys: ['today', 'tasks', 'view']
[16/Feb/2026 21:30:00] "GET /core/daily-agenda/ HTTP/1.1" 200 4231
```

## If Error Persists

Check for these specific error patterns:

### Pattern A: TemplateSyntaxError
**Symptoms**: Error before view execution
**Check**: Template syntax, missing `{% endblock %}`, invalid tags

### Pattern B: AttributeError in Template
**Symptoms**: Error after "context keys" debug line
**Check**: All template variable accesses for `None` values

### Pattern C: Database Error
**Symptoms**: Error in `get_queryset()` method
**Check**: Database connection, migration state, query syntax

### Pattern D: Import Error
**Symptoms**: Error before any debug output
**Check**: Module imports in `views.py`, `models.py`, `forms.py`

## Files to Examine

### Critical Files:
1. `river/settings.py` - DEBUG, ALLOWED_HOSTS, middleware
2. `core/views.py` - DailyAgendaView and imports
3. `core/models.py` - Task model definition
4. `core/urls.py` - URL routing
5. `templates/base.html` - Base template structure

### Supporting Files:
6. `core/templates/core/daily_agenda.html` - Fixed template
7. `core/forms.py` - Form imports and logic
8. `core/admin.py` - Admin configuration
9. `manage.py` - Django project setup

## Quick Fixes to Try

### 1. Reset Database (if corruption suspected):
```bash
rm db.sqlite3
python manage.py migrate
python manage.py loaddata core/fixtures/task_templates.json
python manage.py createsuperuser
```

### 2. Clear Template Cache:
```bash
find . -name "*.pyc" -delete
find . -type d -name "__pycache__" -exec rm -rf {} +
```

### 3. Check Python Path:
```bash
python -c "import sys; print('\\n'.join(sys.path))"
python -c "import django; print(django.__file__)"
```

## Handover Notes

### What's Working:
- Database migrations applied successfully
- Task templates and sections exist
- View logic tested in isolation works
- Template syntax errors fixed

### What's Unknown:
- Exact error causing 500 (need console output)
- Authentication state during error
- Full stack trace

### Recommended Next Steps:
1. Add debug print statements as outlined above
2. Run server and capture full error output
3. Check Django console (not browser) for detailed error
4. Follow investigation plan step-by-step

### Time Estimate:
- **Initial debug**: 15-30 minutes with print statements
- **Root cause fix**: 30-60 minutes once identified
- **Testing/verification**: 15 minutes

## Contact for Context
- **Previous Investigator**: AI Assistant
- **Documentation**: See `product/learnings.md` for related fixes
- **Code Changes**: All changes committed to repository
- **Test Data**: 2 test tasks created (with/without sections)

---

**Investigation Handover Complete**  
*Use the debug statements above to identify the exact cause of the 500 error.*