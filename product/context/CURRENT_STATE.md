**Generated on:** 2026-02-18 12:24:10

### File Structure
```
.
└── .env
└── .env.example
└── .gitignore
└── config_gen.py
└── core
    └── admin.py
    └── fixtures
        └── task_templates.json
    └── forms.py
    └── management
        └── commands
            └── cleanup_photos.py
    └── models.py
    └── templates
        └── core
            └── daily_agenda.html
            └── section_confirm_delete.html
            └── section_detail.html
            └── section_form.html
            └── section_list.html
            └── task_confirm_delete.html
            └── task_form.html
            └── visit_log_form.html
            └── weekly_planner.html
    └── urls.py
    └── views.py
└── coremanagementcommands
└── db.sqlite3
└── deploy.sh
└── DEVELOPER_HANDOVER.md
└── docs
    └── MEDIA_SETUP.md
    └── PRODUCTION_CHECKLIST.md
└── feature-status.sh
└── manage.py
└── new-feature.sh
└── Prep_Sheets_2026-02-18.pdf
└── product
    └── context
        └── learnings.md
        └── po.md
        └── stack.md
        └── ui_standards.md
    └── debug
        └── deploy.md
    └── Done
        └── prd_zone_view
        └── styling.md
    └── investigation_handover.md
    └── Ready
        └── implemenation.md
        └── task_template_data.md
    └── redesign
        └── calendar.html
        └── daily_agenda.html
        └── log_form.html
        └── new_task.html
        └── section_deest.html
        └── zones.html
    └── refinement
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
        └── tests.py
        └── views.py
    └── settings.py
    └── urls.py
    └── wsgi.py
└── summarise.py
└── switch-feature.sh
└── sync-feature.sh
└── templates
    └── admin
        └── base_site.html
    └── base.html
└── test_db.sqlite3
```

### Summarized Key Files
#### `SUMMARY: core/admin.py`
```python
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

class BasePhotoFormSet(forms.BaseInlineFormSet):
    # ... implementation hidden ...
```

#### `SUMMARY: core/models.py`
```python
class Section(models.Model):
    STAGE_CHOICES = [('mitigation', 'Mitigation'), ('clearing', 'Clearing'), ('planting', 'Planting'), ('follow_up', 'Follow-up'), ('community', 'Community')]
    name = models.CharField(max_length=100, unique=True)
    color_code = models.CharField(max_length=7, default='#808080')
    current_stage = models.CharField(max_length=20, choices=STAGE_CHOICES, default='mitigation')
    description = models.TextField(blank=True)
    position = models.PositiveIntegerField(default=0, help_text='Order of the section (upstream to downstream)')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class TaskTemplate(models.Model):
    TASK_TYPE_CHOICES = [('litter_run', 'Litter Run'), ('weeding', 'Weeding'), ('planting', 'Planting'), ('admin', 'Admin')]
    ASSIGNEE_TYPE_CHOICES = [('team', 'Team'), ('manager', 'Manager')]
    name = models.CharField(max_length=100)
    task_type = models.CharField(max_length=20, choices=TASK_TYPE_CHOICES)
    assignee_type = models.CharField(max_length=10, choices=ASSIGNEE_TYPE_CHOICES, default='team')
    default_instructions = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class Task(models.Model):
    ASSIGNEE_TYPE_CHOICES = [('team', 'Team'), ('manager', 'Manager')]
    date = models.DateField()
    section = models.ForeignKey(Section, on_delete=models.CASCADE, null=True, blank=True)
    assignee_type = models.CharField(max_length=10, choices=ASSIGNEE_TYPE_CHOICES, default='team')
    instructions = models.TextField()
    is_completed = models.BooleanField(default=False)
    template = models.ForeignKey(TaskTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class VisitLog(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, null=True, blank=True)
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    date = models.DateField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Metric(models.Model):
    METRIC_TYPE_CHOICES = [('litter_general', 'Litter (General)'), ('litter_recyclable', 'Litter (Recyclable)'), ('plant', 'Plant')]
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
```

#### `SUMMARY: core/views.py`
```python
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

def task_complete_view(request, pk):
    # ... implementation hidden ...
```

#### `SUMMARY: river/core/tests.py`
```python
# Test Coverage Summary for tests.py

class DailyAgendaViewTests:
    - def test_returns_all_tasks_for_date(self):
    - def test_ordering(self):
```

#### `SUMMARY: river/settings.py`
```python
BASE_DIR = Path(__file__).resolve().parent.parent
DEBUG = env.bool('DEBUG', default=True)
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
    # Section URLs
    path('sections/', views.SectionListView.as_view(), name='section_list'),
    path('sections/<int:pk>/', views.SectionDetailView.as_view(), name='section_detail'),
    path('sections/create/', views.SectionCreateView.as_view(), name='section_create'),
    path('sections/<int:pk>/edit/', views.SectionUpdateView.as_view(), name='section_edit'),
    path('sections/<int:pk>/delete/', views.SectionDeleteView.as_view(), name='section_delete'),
    
    # Weekly Planner URLs
    path('weekly-planner/', views.WeeklyPlannerView.as_view(), name='weekly_planner'),
    path('tasks/create/', views.TaskCreateView.as_view(), name='task_create'),
    path('tasks/<int:pk>/edit/', views.TaskUpdateView.as_view(), name='task_edit'),
    path('tasks/<int:pk>/delete/', views.TaskDeleteView.as_view(), name='task_delete'),
    
    # Daily Agenda URLs
    path('daily-agenda/', views.DailyAgendaView.as_view(), name='daily_agenda'),
    path('tasks/<int:pk>/complete/', views.task_complete_view, name='task_complete'),
    
    # Visit Log URLs
    path('visit-logs/create/', views.VisitLogCreateView.as_view(), name='visit_log_create'),
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

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', SectionListView.as_view(), name='home'),
    path('core/', include('core.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

```

