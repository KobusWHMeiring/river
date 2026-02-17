# River - Developer Handover Document

## Project Overview
**Project:** River (MVP 1)  
**Purpose:** System of Record for Liesbeek River rehabilitation management  
**Status:** MVP 1 Complete - Ready for User Acceptance Testing  
**Last Updated:** 2026-02-16  

## Quick Start Guide

### 1. Environment Setup
```bash
# Clone repository
git clone <repository-url>
cd river

# Create and activate virtual environment
python -m venv venv
source venv/Scripts/activate  # Windows
# source venv/bin/activate    # Linux/Mac

# Install dependencies
pip install django psycopg2-binary pillow

# Database setup (SQLite for dev, PostgreSQL for production)
python manage.py migrate
python manage.py loaddata core/fixtures/task_templates.json
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

### 2. Default Credentials
- **Admin URL:** http://127.0.0.1:8000/admin/
- **Default Admin:** username="admin" (password set during creation)
- **Application URL:** http://127.0.0.1:8000/core/weekly-planner/

## Architecture Overview

### Tech Stack
- **Backend:** Django 6.0.2 (Python 3.x)
- **Database:** SQLite (dev), PostgreSQL (production-ready config)
- **Frontend:** Bootstrap 5, Vanilla JavaScript
- **Storage:** Django FileField (S3/local ready)
- **Authentication:** Django Admin

### Project Structure
```
river/
├── river/     # Django project settings
│   ├── settings.py           # Configuration (DB, apps, static files)
│   ├── urls.py              # URL routing
│   └── wsgi.py
├── core/                     # Main application
│   ├── models.py            # All data models
│   ├── views.py             # Business logic
│   ├── forms.py             # Django forms
│   ├── admin.py             # Admin configurations
│   ├── urls.py              # App URL patterns
│   ├── templates/core/      # HTML templates
│   └── fixtures/            # Seed data
├── static/                   # Static files (CSS/JS)
├── media/                    # Uploaded files (photos)
├── templates/               # Base templates
└── manage.py
```

## Core Models Reference

### 1. Section (`core/models.py:11`)
```python
class Section(models.Model):
    STAGE_CHOICES = [
        ('mitigation', 'Mitigation'),
        ('clearing', 'Clearing'),
        ('planting', 'Planting'),
        ('follow_up', 'Follow-up'),
        ('community', 'Community'),
    ]
    # Fields: name, color_code, current_stage, description
```
**Purpose:** Master list of river sections with lifecycle tracking.

### 2. Task (`core/models.py:49`)
```python
class Task(models.Model):
    ASSIGNEE_TYPE_CHOICES = [
        ('team', 'Team'),
        ('manager', 'Manager'),
    ]
    # Fields: date, section, assignee_type, instructions, is_completed, template
```
**Purpose:** Scheduled work items for Team/Manager assignees.

### 3. TaskTemplate (`core/models.py:30`)
```python
class TaskTemplate(models.Model):
    TASK_TYPE_CHOICES = [
        ('litter_run', 'Litter Run'),
        ('weeding', 'Weeding'),
        ('planting', 'Planting'),
    ]
    # Fields: name, task_type, default_instructions
```
**Purpose:** Pre-defined task types with default instructions.

### 4. VisitLog (`core/models.py:70`)
```python
class VisitLog(models.Model):
    # Fields: task (optional), section, date, notes
```
**Purpose:** Records field work (planned or unplanned).

### 5. Metric (`core/models.py:89`)
```python
class Metric(models.Model):
    METRIC_TYPE_CHOICES = [
        ('litter_general', 'Litter (General)'),
        ('litter_recyclable', 'Litter (Recyclable)'),
        ('plant', 'Plant'),
    ]
    # Fields: visit, metric_type, label, value
```
**Purpose:** Quantitative data (litter bags, plant counts).

### 6. Photo (`core/models.py:105`)
```python
class Photo(models.Model):
    # Fields: file, section, visit (optional), description, timestamp
```
**Purpose:** Visual documentation with mandatory descriptions.

## Key Views & URLs

### Manager Views
- `/core/sections/` - Section registry (CRUD)
- `/core/weekly-planner/` - Weekly grid view
- `/core/tasks/create/` - Add new tasks

### Supervisor Views
- `/core/daily-agenda/` - Mobile-optimized daily tasks
- `/core/visit-logs/create/` - Log field work
- `/core/tasks/<pk>/complete/` - Mark tasks as complete

### Admin Interface
- `/admin/` - Full Django admin for all models
- Default redirect from root URL (`/`)

## Business Logic Highlights

### 1. Task Completion Flow (`core/views.py:145`)
```python
def task_complete_view(request, pk):
    task = get_object_or_404(Task, pk=pk)
    task.is_completed = True
    task.save()
    
    # Auto-create VisitLog for completed task
    VisitLog.objects.create(
        task=task,
        section=task.section,
        date=timezone.now().date(),
        notes=f"Task completed: {task.instructions}"
    )
```

### 2. Weekly Planner Date Logic (`core/views.py:47`)
```python
def get_queryset(self):
    # Sunday-start week calculation
    today = timezone.now().date()
    start_of_week = today - timedelta(days=today.weekday() + 1)
    end_of_week = start_of_week + timedelta(days=6)
    return Task.objects.filter(date__range=[start_of_week, end_of_week])
```

### 3. Metrics Formset Integration (`core/views.py:118`)
```python
def form_valid(self, form):
    # Handle nested Metric and Photo formsets
    metric_formset = MetricFormSet(self.request.POST)
    photo_formset = PhotoFormSet(self.request.POST, self.request.FILES)
    
    if metric_formset.is_valid() and photo_formset.is_valid():
        self.object = form.save()
        metric_formset.instance = self.object
        metric_formset.save()
        photo_formset.instance = self.object
        photo_formset.save()
```

## Database Migrations

### Applied Migrations
```bash
# Check current migrations
python manage.py showmigrations

# Create new migrations
python manage.py makemigrations core

# Apply migrations
python manage.py migrate

# Rollback if needed
python manage.py migrate core 0001  # Specific migration
```

### Data Migrations
- **0001_initial.py**: Initial schema creation
- **0002_add_real_world_task_templates.py**: Adds 16 real-world task templates based on last year's river rehabilitation activities (see `product/Ready/task_template_data.md` for details)
- **0003_add_example_sections.py**: Adds 8 example river sections (zones) including Mowbray and San Souci as mentioned in the PRD

### Important Indexes
- `Task.date + Task.assignee_type` (composite index)
- `Task.is_completed` (single field index)
- Automatic indexes on all ForeignKey fields

## Configuration Files

### 1. Settings (`river/settings.py`)
**Key Configurations:**
- `DATABASES`: SQLite for dev, PostgreSQL config commented
- `MEDIA_ROOT/MEDIA_URL`: File upload configuration
- `STATICFILES_DIRS`: Static file locations
- `TIME_ZONE`: 'Africa/Johannesburg'
- `LOGIN_REDIRECT_URL`: '/'

### 2. Production Considerations
```python
# To switch to PostgreSQL:
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'river_db',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# For S3 storage (MVP 2+):
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_ACCESS_KEY_ID = 'your-access-key'
AWS_SECRET_ACCESS_KEY = 'your-secret-key'
AWS_STORAGE_BUCKET_NAME = 'liesbeek-photos'
```

## Testing & Quality Assurance

### 1. Unit Tests (To Implement)
```python
# Example test structure
class SectionModelTest(TestCase):
    def test_section_creation(self):
        section = Section.objects.create(
            name="Mowbray",
            color_code="#FF0000",
            current_stage="clearing"
        )
        self.assertEqual(section.name, "Mowbray")
        self.assertEqual(section.get_current_stage_display(), "Clearing")
```

### 2. Integration Test Areas
1. **Weekly Planner:** Date range filtering, grid rendering
2. **Daily Agenda:** Mobile responsiveness, touch targets
3. **Visit Logger:** Formset validation, photo upload
4. **Admin Interface:** CRUD operations for all models

### 3. Edge Cases to Test
- Duplicate section names
- Negative metric values
- Large photo uploads (>10MB)
- Concurrent task completion
- Missing section references

## Maintenance Notes

### 1. Known Issues
- **LSP Warnings:** Type checking warnings in models/forms (non-blocking)
- **Template Loading:** Weekly Planner uses simplified template loading (AJAX recommended for production)
- **Error Handling:** Basic error pages (enhance for production)

### 2. Performance Considerations
- **Current Scale:** 10-30 sections, 100 tasks/week, 100 photos/month
- **Optimizations Needed for Scale:**
  - Pagination for photo galleries
  - Database query optimization for weekly views
  - Image compression for photo uploads

### 3. Security Notes
- **MVP:** Django admin authentication only
- **Future:** Implement role-based access control
- **File Uploads:** Basic validation (enhance for production)
- **Secrets:** Store in environment variables for production

## Deployment Checklist

### Development
- [x] Virtual environment configured
- [x] Dependencies installed
- [x] Database migrations applied
- [x] Superuser created
- [x] Fixtures loaded
- [x] Development server running

### Staging/Production
- [ ] PostgreSQL database configured
- [ ] Environment variables for secrets
- [ ] Static files collected (`python manage.py collectstatic`)
- [ ] Media storage configured (S3/local)
- [ ] Gunicorn/WSGI configuration
- [ ] Nginx/Apache reverse proxy
- [ ] SSL certificate (HTTPS)
- [ ] Backup strategy implemented
- [ ] Monitoring/alerting configured

## Future Development (MVP 2+)

### High Priority
1. **PDF Work Orders:** Generate printable work orders
2. **Map Integration:** GIS visualization of sections
3. **Rain Day Logic:** Automated rescheduling
4. **Section Grouping:** Organize sections into "Blocks"

### Medium Priority
5. **Role-Based Access:** Manager vs Supervisor permissions
6. **Data Export:** CSV/Excel reports
7. **Notifications:** Email/SMS alerts
8. **API Endpoints:** REST API for mobile apps

### Low Priority
9. **Offline Support:** Progressive Web App capabilities
10. **Advanced Analytics:** Ecological impact reporting
11. **Integration:** Connect with existing FoL systems
12. **Mobile App:** Native iOS/Android applications

## Troubleshooting Guide

### Common Issues

#### 1. Database Connection Errors
```bash
# Check PostgreSQL service
sudo systemctl status postgresql

# Test connection
python manage.py dbshell

# Reset SQLite database
rm db.sqlite3
python manage.py migrate
```

#### 2. Static Files Not Loading
```bash
# Collect static files
python manage.py collectstatic

# Check STATIC_ROOT setting
# Verify Nginx/Apache configuration
```

#### 3. Photo Upload Issues
```python
# Check MEDIA_ROOT permissions
sudo chmod -R 755 media/

# Verify file size limits (settings.py)
# MAX_UPLOAD_SIZE = 10485760  # 10MB
```

#### 4. Migration Conflicts
```bash
# Show migration history
python manage.py showmigrations

# Create new migration after model changes
python manage.py makemigrations core --name descriptive_name

# Fake migration if needed
python manage.py migrate --fake core 0002
```

### Debug Mode
```python
# In settings.py
DEBUG = True  # Development
DEBUG = False  # Production

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'debug.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
```

## Contact & Support

### Project Documentation
- **PRD:** `product/Ready/implemenation.md`
- **Technical Design:** This document
- **User Manual:** To be created after UAT

### Development Team
- **Primary Contact:** [Your Name/Team]
- **Backup Contact:** [Secondary Contact]
- **Support Hours:** [Specify if applicable]

### External Dependencies
- **Django Documentation:** https://docs.djangoproject.com/
- **Bootstrap 5 Docs:** https://getbootstrap.com/docs/5.3/
- **PostgreSQL Docs:** https://www.postgresql.org/docs/
- **Pillow (PIL) Docs:** https://pillow.readthedocs.io/

---

## Final Notes

### Success Criteria Met
- ✅ All 8 user stories implemented
- ✅ Mobile-first design for field use
- ✅ Color-coded section tracking
- ✅ Metrics capture with touch-friendly interface
- ✅ Photo documentation with validation
- ✅ Weekly planning grid
- ✅ Daily supervisor agenda
- ✅ Django admin for management

### Handover Complete
This document, along with the fully implemented codebase, provides everything needed for ongoing maintenance and future development. The application is ready for User Acceptance Testing and subsequent deployment to production.

**Handover Date:** 2026-02-16  
**Next Steps:** Conduct UAT, address feedback, deploy to staging environment.

---
*Document generated by AI Assistant during implementation phase*