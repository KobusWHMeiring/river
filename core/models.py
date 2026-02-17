from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinLengthValidator

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
    description = models.TextField(blank=True)
    position = models.PositiveIntegerField(default=0, help_text="Order of the section (upstream to downstream)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return str(self.name)
    
    class Meta:
        ordering = ['position', 'name']

class TaskTemplate(models.Model):
    TASK_TYPE_CHOICES = [
        ('litter_run', 'Litter Run'),
        ('weeding', 'Weeding'),
        ('planting', 'Planting'),
        ('admin', 'Admin'),
    ]
    
    ASSIGNEE_TYPE_CHOICES = [
        ('team', 'Team'),
        ('manager', 'Manager'),
    ]
    
    name = models.CharField(max_length=100)
    task_type = models.CharField(max_length=20, choices=TASK_TYPE_CHOICES)
    assignee_type = models.CharField(max_length=10, choices=ASSIGNEE_TYPE_CHOICES, default='team')
    default_instructions = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        task_type_display = dict(self.TASK_TYPE_CHOICES).get(str(self.task_type), str(self.task_type))
        return f"{self.name} ({task_type_display})"
    
    class Meta:
        ordering = ['assignee_type', 'name']

class Task(models.Model):
    ASSIGNEE_TYPE_CHOICES = [
        ('team', 'Team'),
        ('manager', 'Manager'),
    ]
    
    date = models.DateField()
    section = models.ForeignKey(Section, on_delete=models.CASCADE, null=True, blank=True)
    assignee_type = models.CharField(max_length=10, choices=ASSIGNEE_TYPE_CHOICES, default='team')
    instructions = models.TextField()
    is_completed = models.BooleanField(default=False)
    template = models.ForeignKey(TaskTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        section_name = self.section.name if self.section else "No Section"
        assignee_display = dict(self.ASSIGNEE_TYPE_CHOICES).get(str(self.assignee_type), str(self.assignee_type))
        return f"{self.date} - {section_name} - {assignee_display}"
    
    class Meta:
        ordering = ['date', 'assignee_type']
        indexes = [
            models.Index(fields=['date', 'assignee_type']),
            models.Index(fields=['is_completed']),
        ]

class VisitLog(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, null=True, blank=True)
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    date = models.DateField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        task_str = f"Task: {self.task}" if self.task else "Unplanned"
        section_name = self.section.name if self.section else "No Section"
        return f"{self.date} - {section_name} - {task_str}"
    
    class Meta:
        ordering = ['-date', '-created_at']

class Metric(models.Model):
    METRIC_TYPE_CHOICES = [
        ('litter_general', 'Litter (General)'),
        ('litter_recyclable', 'Litter (Recyclable)'),
        ('plant', 'Plant'),
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
