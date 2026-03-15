from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinLengthValidator
from django.utils import timezone


class TaskType(models.Model):
    """Dynamic task types that can be managed from the frontend."""
    ASSIGNEE_CHOICES = [
        ('team', 'Team'),
        ('manager', 'Manager'),
        ('chairperson', 'Chairperson'),
        ('all', 'All'),
    ]

    name = models.CharField(max_length=50, unique=True)
    code = models.CharField(max_length=20, unique=True, help_text="Short code used internally (e.g., 'litter_run', 'weeding')")
    description = models.TextField(blank=True, help_text="Optional description of this task type")
    applicable_to = models.CharField(
        max_length=15,
        choices=ASSIGNEE_CHOICES,
        default='all',
        help_text="Which assignee types this task type is applicable to"
    )
    is_active = models.BooleanField(default=True, help_text="Only active task types are shown in dropdowns")
    position = models.PositiveIntegerField(default=0, help_text="Order in which task types appear")
    icon_name = models.CharField(
        max_length=50,
        default='task',
        help_text="Material Symbols icon name (e.g., 'delete_sweep', 'grass', 'forest')"
    )
    color_class = models.CharField(
        max_length=50,
        default='bg-slate-50 text-slate-600 border-slate-100',
        help_text="Tailwind CSS classes for styling (e.g., 'bg-amber-50 text-amber-600 border-amber-100')"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['position', 'name']
        verbose_name = 'Task Type'
        verbose_name_plural = 'Task Types'

    def __str__(self):
        status = "Active" if self.is_active else "Inactive"
        return f"{self.name} ({self.code}) - {status}"

    def is_applicable_to_assignee(self, assignee_type):
        """Check if this task type is applicable to a specific assignee type."""
        if self.applicable_to == 'both':
            return True
        return self.applicable_to == assignee_type


class Status(models.Model):
    name = models.CharField(max_length=50, unique=True)
    color_code = models.CharField(max_length=7, default='#808080', help_text="Hex color code for visual distinction")
    is_active = models.BooleanField(default=True, help_text="Only active statuses are shown in dropdowns")
    position = models.PositiveIntegerField(default=0, help_text="Order in which statuses appear")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['position', 'name']
        verbose_name_plural = 'Statuses'

    def __str__(self):
        return str(self.name)


class Section(models.Model):
    STAGE_CHOICES = [
        ('mitigation', 'Mitigation'),
        ('clearing', 'Clearing'),
        ('planting', 'Planting'),
        ('follow_up', 'Follow-up'),
        ('community', 'Community'),
    ]

    name = models.CharField(max_length=100, unique=True)
    color_code = models.CharField(max_length=7, default='#808080')
    current_stage = models.CharField(max_length=20, choices=STAGE_CHOICES, default='mitigation')
    status = models.ForeignKey(Status, on_delete=models.SET_NULL, null=True, blank=True, help_text="Current status of this section")
    description = models.TextField(blank=True)
    position = models.PositiveIntegerField(default=0, help_text="Order of the section (upstream to downstream)")
    boundary_data = models.JSONField(default=dict, blank=True, help_text="GeoJSON-style polygon coordinates for section boundaries")
    center_point = models.JSONField(default=dict, blank=True, help_text="GeoJSON-style center point coordinates [lng, lat]")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return str(self.name)

    def save(self, *args, **kwargs):
        if self.pk:
            try:
                old_instance = Section.objects.get(pk=self.pk)
                if old_instance.current_stage != self.current_stage:
                    super().save(*args, **kwargs)
                    SectionStageHistory.objects.create(
                        section=self,
                        stage=self.current_stage,
                        changed_at=timezone.now()
                    )
                    return
            except Section.DoesNotExist:
                pass
        else:
            super().save(*args, **kwargs)
            SectionStageHistory.objects.create(
                section=self,
                stage=self.current_stage,
                changed_at=timezone.now()
            )
            return
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['position', 'name']

class TaskTemplate(models.Model):
    ASSIGNEE_TYPE_CHOICES = [
        ('team', 'Team'),
        ('manager', 'Manager'),
        ('chairperson', 'Chairperson'),
    ]

    name = models.CharField(max_length=100)
    task_type = models.ForeignKey(
        TaskType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Category of task",
        related_name='templates'
    )
    assignee_type = models.CharField(max_length=15, choices=ASSIGNEE_TYPE_CHOICES, default='team')
    default_instructions = models.TextField()
    is_active = models.BooleanField(default=True, help_text="Inactive templates are hidden from task creation but preserved for existing tasks")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        task_type_display = str(self.task_type) if self.task_type else "Uncategorized"
        status = "Active" if self.is_active else "Retired"
        return f"{self.name} ({task_type_display}) - {status}"

    class Meta:
        ordering = ['name']

class Task(models.Model):
    ASSIGNEE_TYPE_CHOICES = [
        ('team', 'Team'),
        ('manager', 'Manager'),
        ('chairperson', 'Chairperson'),
    ]
    
    TODO_STATUS_CHOICES = [
        ('todo', 'To Do'),
        ('doing', 'Doing'),
        ('done', 'Done'),
    ]
    
    date = models.DateField(null=True, blank=True)
    section = models.ForeignKey(Section, on_delete=models.CASCADE, null=True, blank=True)
    assignee_type = models.CharField(max_length=15, choices=ASSIGNEE_TYPE_CHOICES, default='team')
    instructions = models.TextField()
    is_completed = models.BooleanField(default=False)
    template = models.ForeignKey(TaskTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    group_id = models.UUIDField(null=True, blank=True, db_index=True, help_text="Links tasks created as a series")
    
    # Rolling To-Do Fields
    is_rolling = models.BooleanField(default=False, db_index=True)
    is_urgent = models.BooleanField(default=False)
    todo_status = models.CharField(
        max_length=10, 
        choices=TODO_STATUS_CHOICES, 
        default='todo', 
        db_index=True
    )
    todo_position = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        section_name = self.section.name if self.section else "No Section"
        assignee_display = dict(self.ASSIGNEE_TYPE_CHOICES).get(str(self.assignee_type), str(self.assignee_type))
        if self.is_rolling:
            return f"[Rolling] {self.instructions[:30]} - {section_name}"
        return f"{self.date} - {section_name} - {assignee_display}"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        if not self.is_rolling and not self.date:
            raise ValidationError({'date': 'Date is required for non-rolling tasks.'})
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['date', 'todo_position']
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['is_completed']),
            models.Index(fields=['is_rolling']),
            models.Index(fields=['todo_status']),
        ]

class VisitLog(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, null=True, blank=True)
    section = models.ForeignKey(Section, on_delete=models.CASCADE, null=True, blank=True, help_text="River section where activity took place (optional for general logs)")
    date = models.DateField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        task_str = f"Task: {self.task}" if self.task else "Unplanned"
        section_name = self.section.name if self.section else "General"
        return f"{self.date} - {section_name} - {task_str}"
    
    class Meta:
        ordering = ['-date', '-created_at']

class Metric(models.Model):
    METRIC_TYPE_CHOICES = [
        ('litter_general', 'Litter (General)'),
        ('litter_recyclable', 'Litter (Recyclable)'),
        ('plant', 'Plant'),
        ('weed', 'Weeding / Removal'),
    ]
    
    visit = models.ForeignKey(VisitLog, on_delete=models.CASCADE, related_name='metrics')
    metric_type = models.CharField(max_length=20, choices=METRIC_TYPE_CHOICES)
    label = models.CharField(max_length=100, blank=True)
    value = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        metric_display = dict(self.METRIC_TYPE_CHOICES).get(str(self.metric_type), str(self.metric_type))
        return f"{metric_display}: {self.value} ({self.label})"
    
    class Meta:
        ordering = ['metric_type', 'label']

class Photo(models.Model):
    file = models.ImageField(upload_to='photos/%Y/%m/%d/')
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    visit = models.ForeignKey(VisitLog, on_delete=models.CASCADE, null=True, blank=True, related_name='photos')
    description = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.section.name} - {self.timestamp}"
    
    class Meta:
        ordering = ['-timestamp']

class SectionStageHistory(models.Model):
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='stage_history')
    stage = models.CharField(max_length=20, choices=Section.STAGE_CHOICES)
    changed_at = models.DateTimeField()
    notes = models.TextField(blank=True)

    def __str__(self):
        stage_display = dict(Section.STAGE_CHOICES).get(self.stage, self.stage)
        return f"{self.section.name} → {stage_display} at {self.changed_at}"

    class Meta:
        ordering = ['-changed_at']
        verbose_name = 'Stage History'
        verbose_name_plural = 'Stage History'
        indexes = [
            models.Index(fields=['section', 'changed_at']),
        ]
