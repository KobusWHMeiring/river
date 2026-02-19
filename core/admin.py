from django.contrib import admin
from .models import Section, TaskTemplate, Task, VisitLog, Metric, Photo, SectionStageHistory


class SectionStageHistoryInline(admin.TabularInline):
    model = SectionStageHistory
    extra = 0
    readonly_fields = ('stage', 'changed_at')
    fields = ('stage', 'changed_at', 'notes')
    ordering = ('-changed_at',)


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'color_code', 'current_stage', 'created_at')
    list_filter = ('current_stage',)
    search_fields = ('name', 'description')
    ordering = ('name',)
    inlines = [SectionStageHistoryInline]

@admin.register(TaskTemplate)
class TaskTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'task_type', 'created_at')
    list_filter = ('task_type',)
    search_fields = ('name', 'default_instructions')
    ordering = ('name',)

class MetricInline(admin.TabularInline):
    model = Metric
    extra = 1

class PhotoInline(admin.TabularInline):
    model = Photo
    extra = 1


@admin.register(VisitLog)
class VisitLogAdmin(admin.ModelAdmin):
    list_display = ('date', 'section', 'task', 'created_at')
    list_filter = ('date', 'section')
    search_fields = ('notes', 'section__name')
    inlines = [MetricInline, PhotoInline]
    ordering = ('-date', '-created_at')

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('date', 'section', 'assignee_type', 'is_completed', 'created_at')
    list_filter = ('date', 'assignee_type', 'is_completed', 'section')
    search_fields = ('instructions', 'section__name')
    ordering = ('-date', 'assignee_type')

@admin.register(Metric)
class MetricAdmin(admin.ModelAdmin):
    list_display = ('visit', 'metric_type', 'label', 'value')
    list_filter = ('metric_type',)
    search_fields = ('label', 'visit__section__name')
    ordering = ('metric_type', 'label')

@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ('section', 'timestamp', 'description_preview')
    list_filter = ('section', 'timestamp')
    search_fields = ('description', 'section__name')
    ordering = ('-timestamp',)
    
    def description_preview(self, obj):
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_preview.short_description = 'Description'
