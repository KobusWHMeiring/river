**Generated on:** 2026-08-16 20:23:29

### File Structure
```
.
└── .env
└── .env.example
└── .gitignore
└── .pi
    └── extensions
        └── backlog-checkpoint.ts
        └── uat-checklist
            └── checklist.ts
            └── index.ts
    └── extensions copy
└── config_gen.py
└── core
    └── __init__.py
    └── admin.py
    └── fixtures
        └── task_templates.json
    └── forms.py
    └── management
        └── __init__.py
        └── commands
            └── __init__.py
            └── cleanup_photos.py
            └── preflight_template_tasktypes.py
            └── sync_from_prod.py
    └── models.py
    └── services
        └── task_services.py
        └── visit_log_services.py
    └── templates
        └── core
            └── daily_agenda.html
            └── dashboard.html
            └── includes
                └── form_errors.html
                └── todo_card.html
            └── monthly_planner.html
            └── section_confirm_delete.html
            └── section_detail.html
            └── section_form.html
            └── section_list.html
            └── task_confirm_delete.html
            └── task_form.html
            └── task_template_confirm_delete.html
            └── task_template_form.html
            └── task_template_list.html
            └── task_type_confirm_delete.html
            └── task_type_form.html
            └── task_type_list.html
            └── todo_kanban.html
            └── visit_log_form.html
            └── visit_log_list.html
            └── weekly_planner.html
    └── templatetags
        └── __init__.py
        └── custom_filters.py
        └── form_tags.py
    └── tests
        └── __init__.py
        └── performance
            └── base.py
            └── test_budgets.py
            └── test_discovery.py
        └── test_chairperson.py
        └── test_dashboard.py
        └── test_form_errors.py
        └── test_log_and_complete.py
        └── test_monthly.py
        └── test_section_detail.py
        └── test_task_complete.py
        └── test_task_reopen.py
        └── test_task_search.py
        └── test_task_series.py
        └── test_todo_kanban.py
        └── test_urls.py
        └── test_visit_log_filters.py
        └── test_visit_log_form.py
        └── test_weeding.py
    └── urls.py
    └── views.py
└── coremanagementcommands
└── db.sqlite3
└── debug_river.sh
└── deploy.sh
└── DEVELOPER_HANDOVER.md
└── docs
    └── MEDIA_SETUP.md
    └── PRODUCTION_CHECKLIST.md
└── feature-status.sh
└── icon-usage-report.txt
└── implementation_log_2026-08-11.md
└── lint.py
└── manage.py
└── new-feature.sh
└── Prep_Sheets_2026-02-18.pdf
└── product
    └── backlog.md
    └── backlog.py
    └── context
        └── backlog-loop-design.md
        └── build_principles.md
        └── learnings.md
        └── prinicples
            └── abseil-vs-build-principles-comparison.html
            └── archguard
                └── __init__.py
                └── __main__.py
                └── audit_writer.py
                └── rules
                    └── __init__.py
                    └── css_js.py
                    └── python_ast.py
                    └── templates.py
                └── tests
                    └── __init__.py
                    └── test_rules.py
                └── violation.py
            └── consolidated-sprint-plan.html
            └── performance-testing.md
            └── pm-brief.md
            └── river-archguard-assessment.html
        └── project_overview.md
        └── SESSION_CHECKPOINT.json
        └── stack.md
        └── ui_standards.md
    └── debug
        └── deploy.md
        └── edit_log.md
    └── designs
        └── field-activity-deep-dive.html
        └── log_avtivity.png
        └── planner-activity-indicators-options.html
        └── planner-insights-gap-analysis.html
        └── tasks.html
    └── Done
        └── active_sections_dashboard.md
        └── all_logs_view.md
        └── chairperson_role.md
        └── context_aware_logging.md
        └── dashboard-metric-drilldown.md
        └── dashboard.md
        └── data_export_excel.md
        └── detailed_planting_metrics.md
        └── edit_completed_task.md
        └── form-validation-error-display.md
        └── implemenation.md
        └── investigation_handover.md
        └── kanban-snap-back-bug.md
        └── lifecycle-progress-data-source.md
        └── log_layout.md
        └── mobile_responsive_implementation.md
        └── monthly_view.md
        └── multi_day_tasks.md
        └── planner-activity-indicators.md
        └── planner-search.md
        └── planner_interaction_update.md
        └── prd_zone_view
        └── quick-specs-participants-typeable.md
        └── reopen-completed-tasks.md
        └── rolling_todo_list.md
        └── section-days-worked-metric.md
        └── section_mapping.md
        └── stage_tracking.md
        └── styling.md
        └── success_metrics_card.md
        └── task_template_data.md
        └── template_management.md
        └── tick-to-complete-planner.md
        └── weeding_data.md
        └── weekly_planner_navigation.md
    └── prompts
        └── arch.md
        └── DEV.md
        └── PM.md
        └── po.md
    └── ready
    └── refinement
        └── dynamic-kanban-columns.md
        └── performance-testing-backlog.md
        └── playwright_e2e_testing.md
    └── technical
└── progress_log.json
└── requirements.txt
└── river
    └── .env
    └── __init__.py
    └── asgi.py
    └── core
        └── __init__.py
        └── admin.py
        └── apps.py
        └── models.py
        └── views.py
    └── deploy.sh
    └── nginx_config
    └── psql_setup.sql
    └── river_web.service
    └── settings.py
    └── STEPS.md
    └── urls.py
    └── wsgi.py
└── scripts
    └── update_icons.py
└── summarise.py
└── switch-feature.sh
└── sync-feature.sh
└── templates
    └── admin
        └── base_site.html
    └── base.html
└── test_db.sqlite3
└── tests
    └── uat
        └── dashboard_metric_drilldown-uat-results.json
        └── dashboard_metric_drilldown_uat.md
        └── form_validation_error_display-uat-results.json
        └── form_validation_error_display_uat.md
        └── participants-typeable_uat.md
        └── planner_activity_indicators-uat-results.json
        └── planner_activity_indicators_uat.md
        └── planner_search-uat-results.json
        └── planner_search_uat.md
        └── reopen_completed_tasks-uat-results.json
        └── reopen_completed_tasks_uat.md
        └── section_days_worked-uat-results.json
        └── section_days_worked_uat.md
```

### Summarized Key Files
#### `SUMMARY: core/admin.py`
```python
@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    # ... implementation hidden ...

class SectionStageHistoryInline(admin.TabularInline):
    # ... implementation hidden ...

@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    # ... implementation hidden ...

@admin.register(TaskTemplate)
class TaskTemplateAdmin(admin.ModelAdmin):
    # ... implementation hidden ...

class MetricInline(admin.TabularInline):
    # ... implementation hidden ...

class PhotoInline(admin.TabularInline):
    # ... implementation hidden ...

@admin.register(VisitLog)
class VisitLogAdmin(admin.ModelAdmin):
    # ... implementation hidden ...

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    # ... implementation hidden ...

@admin.register(Metric)
class MetricAdmin(admin.ModelAdmin):
    # ... implementation hidden ...

@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    # ... implementation hidden ...
```

#### `SUMMARY: core/forms.py`
```python
class SectionForm(forms.ModelForm):  # Binds to model: Section
    # ... implementation hidden ...

class TaskTypeForm(forms.ModelForm):  # Binds to model: TaskType
    # ... implementation hidden ...

class TaskTemplateForm(forms.ModelForm):  # Binds to model: TaskTemplate
    # ... implementation hidden ...

class TaskForm(forms.ModelForm):  # Binds to model: Task
    # ... implementation hidden ...

class VisitLogForm(forms.ModelForm):  # Binds to model: VisitLog
    # ... implementation hidden ...

class MetricForm(forms.ModelForm):  # Binds to model: Metric
    # ... implementation hidden ...

class PhotoForm(forms.ModelForm):  # Binds to model: Photo
    # ... implementation hidden ...

class BaseMetricFormSet(forms.BaseInlineFormSet):
    # ... implementation hidden ...

class BasePhotoFormSet(forms.BaseInlineFormSet):
    # ... implementation hidden ...
```

#### `SUMMARY: core/models.py`
```python
class TaskType(models.Model):
    ASSIGNEE_CHOICES = [('team', 'Team'), ('manager', 'Manager'), ('chairperson', 'Chairperson'), ('all', 'All')]
    name = models.CharField(max_length=50, unique=True)
    code = models.CharField(max_length=20, unique=True, help_text="Short code used internally (e.g., 'litter_run', 'weeding')")
    description = models.TextField(blank=True, help_text='Optional description of this task type')
    applicable_to = models.CharField(max_length=15, choices=ASSIGNEE_CHOICES, default='all', help_text='Which assignee types this task type is applicable to')
    is_active = models.BooleanField(default=True, help_text='Only active task types are shown in dropdowns')
    position = models.PositiveIntegerField(default=0, help_text='Order in which task types appear')
    icon_name = models.CharField(max_length=50, default='task', help_text="Material Symbols icon name (e.g., 'delete_sweep', 'grass', 'forest')")
    color_class = models.CharField(max_length=150, default='bg-slate-50 text-slate-600 border-slate-100', help_text="Tailwind CSS classes for styling (e.g., 'bg-amber-50 text-amber-600 border-amber-100')")
    created_at = models.DateTimeField(auto_now_add=True)

class Status(models.Model):
    name = models.CharField(max_length=50, unique=True)
    color_code = models.CharField(max_length=7, default='#808080', help_text='Hex color code for visual distinction')
    is_active = models.BooleanField(default=True, help_text='Only active statuses are shown in dropdowns')
    position = models.PositiveIntegerField(default=0, help_text='Order in which statuses appear')
    created_at = models.DateTimeField(auto_now_add=True)

class Section(models.Model):
    STAGE_CHOICES = [('mitigation', 'Mitigation'), ('clearing', 'Clearing'), ('planting', 'Planting'), ('follow_up', 'Follow-up'), ('community', 'Community')]
    name = models.CharField(max_length=100, unique=True)
    color_code = models.CharField(max_length=7, default='#808080')
    current_stage = models.CharField(max_length=20, choices=STAGE_CHOICES, default='mitigation')
    status = models.ForeignKey(Status, on_delete=models.SET_NULL, null=True, blank=True, help_text='Current status of this section')
    description = models.TextField(blank=True)
    position = models.PositiveIntegerField(default=0, help_text='Order of the section (upstream to downstream)')
    boundary_data = models.JSONField(default=dict, blank=True, help_text='GeoJSON-style polygon coordinates for section boundaries')
    center_point = models.JSONField(default=dict, blank=True, help_text='GeoJSON-style center point coordinates [lng, lat]')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class TaskTemplate(models.Model):
    ASSIGNEE_TYPE_CHOICES = [('team', 'Team'), ('manager', 'Manager'), ('chairperson', 'Chairperson')]
    name = models.CharField(max_length=100)
    task_type = models.ForeignKey(TaskType, on_delete=models.SET_NULL, null=True, blank=True, help_text='Category of task', related_name='templates')
    assignee_type = models.CharField(max_length=15, choices=ASSIGNEE_TYPE_CHOICES, default='team')
    default_instructions = models.TextField()
    is_active = models.BooleanField(default=True, help_text='Inactive templates are hidden from task creation but preserved for existing tasks')
    created_at = models.DateTimeField(auto_now_add=True)

class Task(models.Model):
    ASSIGNEE_TYPE_CHOICES = [('team', 'Team'), ('manager', 'Manager'), ('chairperson', 'Chairperson')]
    TODO_STATUS_CHOICES = [('todo', 'To Do'), ('doing', 'Doing'), ('done', 'Done')]
    date = models.DateField(null=True, blank=True)
    section = models.ForeignKey(Section, on_delete=models.CASCADE, null=True, blank=True)
    assignee_type = models.CharField(max_length=15, choices=ASSIGNEE_TYPE_CHOICES, default='team')
    instructions = models.TextField()
    is_completed = models.BooleanField(default=False)
    template = models.ForeignKey(TaskTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    group_id = models.UUIDField(null=True, blank=True, db_index=True, help_text='Links tasks created as a series')
    is_rolling = models.BooleanField(default=False, db_index=True)
    is_urgent = models.BooleanField(default=False)
    todo_status = models.CharField(max_length=10, choices=TODO_STATUS_CHOICES, default='todo', db_index=True)
    todo_position = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class VisitLog(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, null=True, blank=True)
    section = models.ForeignKey(Section, on_delete=models.CASCADE, null=True, blank=True, help_text='River section where activity took place (optional for general logs)')
    date = models.DateField()
    notes = models.TextField(blank=True)
    participant_count = models.PositiveIntegerField(default=0, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Metric(models.Model):
    METRIC_TYPE_CHOICES = [('litter_general', 'Litter (General)'), ('litter_recyclable', 'Litter (Recyclable)'), ('plant', 'Plant'), ('weed', 'Weeding / Removal')]
    visit = models.ForeignKey(VisitLog, on_delete=models.CASCADE, related_name='metrics')
    metric_type = models.CharField(max_length=20, choices=METRIC_TYPE_CHOICES)
    label = models.CharField(max_length=100, blank=True)
    value = models.PositiveIntegerField(default=0)

class Photo(models.Model):
    file = models.ImageField(upload_to='photos/%Y/%m/%d/')
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    visit = models.ForeignKey(VisitLog, on_delete=models.CASCADE, null=True, blank=True, related_name='photos')
    description = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

class SectionStageHistory(models.Model):
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='stage_history')
    stage = models.CharField(max_length=20, choices=Section.STAGE_CHOICES)
    # Choices: STAGE_CHOICES, name, color_code, current_stage, status, description, position, boundary_data, center_point, created_at, updated_at
    changed_at = models.DateTimeField()
    notes = models.TextField(blank=True)

class TaskCompletionHistory(models.Model):
    ACTION_CHOICES = [('completed', 'Completed'), ('reopened', 'Reopened')]
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='completion_history')
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    changed_at = models.DateTimeField(default=timezone.now)
```

#### `SUMMARY: core/views.py`
```python
@login_required
def section_reorder_view(request):
    """AJAX endpoint to reorder sections by updating their position field."""
    # ... implementation hidden ...

class TodoKanbanView(LoginRequiredMixin, ListView):  # Renders: core/todo_kanban.html
    # ... implementation hidden ...

@method_decorator(csrf_exempt, name='dispatch')
class TodoUpdateAPI(LoginRequiredMixin, View):
    """AJAX endpoint to handle Kanban drag-and-drop updates."""
    # ... implementation hidden ...

class GlobalDashboardView(LoginRequiredMixin, ListView):  # Renders: core/dashboard.html
    # ... implementation hidden ...

class SectionListView(LoginRequiredMixin, ListView):  # Renders: core/section_list.html
    # ... implementation hidden ...

class SectionDetailView(LoginRequiredMixin, DetailView):  # Renders: core/section_detail.html
    # ... implementation hidden ...

class SectionCreateView(LoginRequiredMixin, CreateView):  # Renders: core/section_form.html
    # ... implementation hidden ...

class SectionUpdateView(LoginRequiredMixin, UpdateView):  # Renders: core/section_form.html
    # ... implementation hidden ...

class SectionDeleteView(LoginRequiredMixin, DeleteView):  # Renders: core/section_confirm_delete.html
    # ... implementation hidden ...

class WeeklyPlannerView(LoginRequiredMixin, ListView):  # Renders: core/weekly_planner.html
    # ... implementation hidden ...

class MonthlyPlannerView(LoginRequiredMixin, ListView):  # Renders: core/monthly_planner.html
    # ... implementation hidden ...

class DailyAgendaView(LoginRequiredMixin, ListView):  # Renders: core/daily_agenda.html
    # ... implementation hidden ...

class TaskCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):  # Renders: core/task_form.html
    # ... implementation hidden ...

class TaskUpdateView(LoginRequiredMixin, UpdateView):  # Renders: core/task_form.html
    # ... implementation hidden ...

class TaskDeleteView(LoginRequiredMixin, DeleteView):  # Renders: core/task_confirm_delete.html
    # ... implementation hidden ...

class VisitLogCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):  # Renders: core/visit_log_form.html
    # ... implementation hidden ...

class VisitLogUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):  # Renders: core/visit_log_form.html
    # ... implementation hidden ...

@login_required
def task_complete_view(request, pk):
    # ... implementation hidden ...

@login_required
def task_reopen_view(request, pk):
    # ... implementation hidden ...

@login_required
def task_search_view(request):
    """JSON search endpoint for the planner search box (keyword search)."""
    # ... implementation hidden ...

class TaskTemplateListView(LoginRequiredMixin, ListView):  # Renders: core/task_template_list.html
    # ... implementation hidden ...

class TaskTemplateCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):  # Renders: core/task_template_form.html
    # ... implementation hidden ...

class TaskTemplateUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):  # Renders: core/task_template_form.html
    # ... implementation hidden ...

class TaskTemplateDeleteView(LoginRequiredMixin, DeleteView):  # Renders: core/task_template_confirm_delete.html
    # ... implementation hidden ...

class VisitLogListView(LoginRequiredMixin, ListView):  # Renders: core/visit_log_list.html
    """Master Activity Log - comprehensive view of all visit logs with search and filtering."""
    # ... implementation hidden ...

class TaskTypeListView(LoginRequiredMixin, ListView):  # Renders: core/task_type_list.html
    # ... implementation hidden ...

class TaskTypeCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):  # Renders: core/task_type_form.html
    # ... implementation hidden ...

class TaskTypeUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):  # Renders: core/task_type_form.html
    # ... implementation hidden ...

class TaskTypeDeleteView(LoginRequiredMixin, DeleteView):  # Renders: core/task_type_confirm_delete.html
    # ... implementation hidden ...

class DataExportView(LoginRequiredMixin, View):
    """View to generate a comprehensive multi-sheet Excel export."""
    # ... implementation hidden ...

class VisitLogExportView(LoginRequiredMixin, View):
    """Single-sheet Excel export of the filtered Master Activity Log."""
    # ... implementation hidden ...

class PlannerExportView(LoginRequiredMixin, View):
    """Export the weekly or monthly planner view to Excel."""
    # ... implementation hidden ...

def planner_insights_view(request):
    """Serve the planner insights pages for Sarah's review."""
    # ... implementation hidden ...
```

#### `SUMMARY: river/settings.py`
```python
BASE_DIR = Path(__file__).resolve().parent.parent
SENTRY_DSN = os.environ.get('SENTRY_DSN')
DEBUG = env.bool('DEBUG', default=False)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])
INSTALLED_APPS = [
MIDDLEWARE = [
ROOT_URLCONF = 'river.urls'
TEMPLATES = [
WSGI_APPLICATION = 'river.wsgi.application'
DATABASES = {
USE_I18N = True
USE_TZ = True
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = env('STATIC_ROOT', default=BASE_DIR / 'staticfiles')
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5 MB
FILE_UPLOAD_PERMISSIONS = 0o644
LOGIN_URL = '/admin/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/admin/login/'```

### Full Content of Critical Files
#### `FULL: core/urls.py`
```python
from django.urls import path
from . import views

urlpatterns = [
    # Dashboard URL
    path('dashboard/', views.GlobalDashboardView.as_view(), name='dashboard'),
    
    # Section URLs
    path('sections/', views.SectionListView.as_view(), name='section_list'),
    path('sections/reorder/', views.section_reorder_view, name='section_reorder'),
    path('sections/<int:pk>/', views.SectionDetailView.as_view(), name='section_detail'),
    path('sections/create/', views.SectionCreateView.as_view(), name='section_create'),
    path('sections/<int:pk>/edit/', views.SectionUpdateView.as_view(), name='section_edit'),
    path('sections/<int:pk>/delete/', views.SectionDeleteView.as_view(), name='section_delete'),
    
    # Planner URLs (Weekly and Monthly)
    path('planner/', views.WeeklyPlannerView.as_view(), name='weekly_planner'),
    path('planner/weekly/', views.WeeklyPlannerView.as_view(), name='weekly_planner'),
    path('planner/monthly/', views.MonthlyPlannerView.as_view(), name='monthly_planner'),
    path('tasks/create/', views.TaskCreateView.as_view(), name='task_create'),
    path('tasks/<int:pk>/edit/', views.TaskUpdateView.as_view(), name='task_edit'),
    path('tasks/<int:pk>/delete/', views.TaskDeleteView.as_view(), name='task_delete'),
    
    # Daily Agenda URLs
    path('daily-agenda/', views.DailyAgendaView.as_view(), name='daily_agenda'),
    path('tasks/<int:pk>/complete/', views.task_complete_view, name='task_complete'),
    path('tasks/<int:pk>/reopen/', views.task_reopen_view, name='task_reopen'),
    path('tasks/search/', views.task_search_view, name='task_search'),
    
    # Kanban Board URLs
    path('todo/', views.TodoKanbanView.as_view(), name='todo_kanban'),
    path('todo/update/', views.TodoUpdateAPI.as_view(), name='todo_update'),
    
    # Visit Log URLs
    path('visit-logs/', views.VisitLogListView.as_view(), name='visit_log_list'),
    path('visit-logs/create/', views.VisitLogCreateView.as_view(), name='visit_log_create'),
    path('visit-logs/<int:pk>/edit/', views.VisitLogUpdateView.as_view(), name='visit_log_edit'),

    # Data Export URLs
    path('export/', views.DataExportView.as_view(), name='data_export'),
    path('export/planner/', views.PlannerExportView.as_view(), name='planner_export'),
    path('export/visit-logs/', views.VisitLogExportView.as_view(), name='visit_log_export'),

    # Insights page (temporary, for Sarah review)
    path('insights/', views.planner_insights_view, name='planner_insights'),

    # Task Template Management URLs
    path('templates/', views.TaskTemplateListView.as_view(), name='task_template_list'),
    path('templates/create/', views.TaskTemplateCreateView.as_view(), name='task_template_create'),
    path('templates/<int:pk>/edit/', views.TaskTemplateUpdateView.as_view(), name='task_template_edit'),
    path('templates/<int:pk>/delete/', views.TaskTemplateDeleteView.as_view(), name='task_template_delete'),

    # Task Type Management URLs
    path('task-types/', views.TaskTypeListView.as_view(), name='task_type_list'),
    path('task-types/create/', views.TaskTypeCreateView.as_view(), name='task_type_create'),
    path('task-types/<int:pk>/edit/', views.TaskTypeUpdateView.as_view(), name='task_type_edit'),
    path('task-types/<int:pk>/delete/', views.TaskTypeDeleteView.as_view(), name='task_type_delete'),
]

```

#### `FULL: river/urls.py`
```python
"""
URL configuration for river project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.views import SectionListView


def trigger_error(request):
    division_by_zero = 1 / 0


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', SectionListView.as_view(), name='home'),
    path('core/', include('core.urls')),
    path('sentry-debug/', trigger_error),
]

# Only serve media files through Django in DEBUG mode (development)
# In production, Nginx handles media serving
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

```

