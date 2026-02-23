from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import JsonResponse
from datetime import datetime, timedelta
import calendar
import json
from collections import defaultdict
from .models import Section, Task, TaskTemplate, VisitLog, Metric, Photo, SectionStageHistory
from .forms import SectionForm, TaskForm, TaskTemplateForm, VisitLogForm, MetricFormSet, PhotoFormSet

from django.db.models import Sum, Q
from django.utils import timezone


@login_required
def section_reorder_view(request):
    """AJAX endpoint to reorder sections by updating their position field."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            section_order = data.get('order', [])
            
            # Update each section's position
            for index, section_id in enumerate(section_order):
                Section.objects.filter(id=section_id).update(position=index)
            
            return JsonResponse({'success': True, 'message': 'Order updated successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)

class GlobalDashboardView(LoginRequiredMixin, ListView):
    model = VisitLog
    template_name = 'core/dashboard.html'
    context_object_name = 'recent_visits'

    def get_queryset(self):
        return VisitLog.objects.all().prefetch_related('metrics', 'photos', 'section').order_by('-date', '-created_at')[:15]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Aggregated Stats
        metrics = Metric.objects.all()
        total_bags_general = metrics.filter(metric_type='litter_general').aggregate(total=Sum('value'))['total'] or 0
        total_bags_recyclable = metrics.filter(metric_type='litter_recyclable').aggregate(total=Sum('value'))['total'] or 0
        total_plants = metrics.filter(metric_type='plant').aggregate(total=Sum('value'))['total'] or 0
        total_weeds = metrics.filter(metric_type='weed').aggregate(total=Sum('value'))['total'] or 0

        # Section Stage Distribution
        from django.db.models import Count
        stage_counts = Section.objects.values('current_stage').annotate(count=Count('id'))
        
        # Convert to a more usable dict with display names
        stage_choices = dict(Section.STAGE_CHOICES)
        stage_distribution = []
        max_count = 1  # Default to 1 to avoid division by zero
        for stage_code, label in stage_choices.items():
            count = next((item['count'] for item in stage_counts if item['current_stage'] == stage_code), 0)
            percentage = int(count / max_count * 100) if max_count > 0 else 0
            stage_distribution.append({
                'code': stage_code,
                'label': label,
                'count': count,
                'percentage': percentage
            })
            if count > max_count:
                max_count = count
        
        # Recalculate percentages after we know the max
        for stage in stage_distribution:
            stage['percentage'] = int(stage['count'] / max_count * 100) if max_count > 0 else 0

        # Plant Species Breakdown
        plant_metrics = Metric.objects.filter(metric_type='plant')
        total_plant_species = plant_metrics.exclude(label='').values('label').distinct().count()
        plant_species_breakdown = list(plant_metrics.exclude(label='').values('label').annotate(
            total=Sum('value')
        ).order_by('-total')[:5])

        # Weed Species Breakdown
        weed_metrics = Metric.objects.filter(metric_type='weed')
        total_weed_species = weed_metrics.exclude(label='').values('label').distinct().count()
        weed_species_breakdown = list(weed_metrics.exclude(label='').values('label').annotate(
            total=Sum('value')
        ).order_by('-total')[:5])

        # Active Sections (with activity in last 30 days)
        from django.db.models import Max, Count
        thirty_days_ago = timezone.now().date() - timedelta(days=30)
        active_sections = Section.objects.filter(
            visitlog__date__gte=thirty_days_ago
        ).annotate(
            last_visit_date=Max('visitlog__date'),
            visit_count=Count('visitlog')
        ).distinct().order_by('-last_visit_date')[:10]

        context.update({
            'total_bags_general': total_bags_general,
            'total_bags_recyclable': total_bags_recyclable,
            'total_plants': total_plants,
            'total_weeds': total_weeds,
            'total_bags': total_bags_general + total_bags_recyclable,
            'stage_distribution': stage_distribution,
            'total_plant_species': total_plant_species,
            'plant_species_breakdown': plant_species_breakdown,
            'total_weed_species': total_weed_species,
            'weed_species_breakdown': weed_species_breakdown,
            'active_sections': active_sections,
        })
        return context

class SectionListView(LoginRequiredMixin, ListView):
    model = Section
    template_name = 'core/section_list.html'
    context_object_name = 'sections'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Prepare GeoJSON data for sections with boundaries
        sections_geojson = []
        for section in context['sections']:
            section_data = {
                'id': section.id,
                'name': section.name,
                'color_code': section.color_code,
                'current_stage': section.current_stage,
                'stage_display': section.get_current_stage_display(),
                'description': section.description or '',
                'boundary_data': section.boundary_data if section.boundary_data else {},
                'center_point': section.center_point if section.center_point else {},
                'detail_url': reverse_lazy('section_detail', kwargs={'pk': section.pk}),
            }
            sections_geojson.append(section_data)
        
        context['sections_geojson'] = sections_geojson
        return context

class SectionDetailView(LoginRequiredMixin, DetailView):
    model = Section
    template_name = 'core/section_detail.html'
    context_object_name = 'section'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        section = self.object
        today = timezone.now().date()

        # Cumulative Metrics
        metrics = Metric.objects.filter(visit__section=section)
        total_bags_general = metrics.filter(metric_type='litter_general').aggregate(total=Sum('value'))['total'] or 0
        total_bags_recyclable = metrics.filter(metric_type='litter_recyclable').aggregate(total=Sum('value'))['total'] or 0
        total_plants = metrics.filter(metric_type='plant').aggregate(total=Sum('value'))['total'] or 0
        total_weeds = metrics.filter(metric_type='weed').aggregate(total=Sum('value'))['total'] or 0

        # Top 3 Weeding Species
        top_weeds = metrics.filter(metric_type='weed').values('label').annotate(total=Sum('value')).order_by('-total')[:3]
        top_weeds_list = []
        weeds_sum_top3 = 0
        for w in top_weeds:
            top_weeds_list.append(f"{w['label']}: {w['total']}")
            weeds_sum_top3 += w['total']
        
        if total_weeds > weeds_sum_top3:
            top_weeds_list.append(f"Other: {total_weeds - weeds_sum_top3}")
        
        weeding_summary = ", ".join(top_weeds_list) if top_weeds_list else "None recorded"

        # Timeline queries with prefetching
        past_visits = VisitLog.objects.filter(section=section).prefetch_related('metrics', 'photos').order_by('-date', '-created_at')

        # Stage History
        stage_history = SectionStageHistory.objects.filter(section=section).order_by('-changed_at')

        # Calculate days in current stage (from most recent history entry)
        latest_stage_change = stage_history.first()
        if latest_stage_change:
            days_in_stage = (timezone.now() - latest_stage_change.changed_at).days
        else:
            days_in_stage = (timezone.now() - section.created_at).days

        today_tasks = Task.objects.filter(section=section, date=today)
        future_tasks = Task.objects.filter(section=section, date__gt=today, is_completed=False).order_by('date')

        # Combine visits and stage history for timeline
        timeline_items = []

        # Add visits
        for visit in past_visits:
            timeline_items.append({
                'type': 'visit',
                'date': visit.date,
                'created_at': visit.created_at,
                'object': visit
            })

        # Add stage changes
        for history in stage_history:
            timeline_items.append({
                'type': 'stage_change',
                'date': history.changed_at.date(),
                'created_at': history.changed_at,
                'object': history
            })

        # Sort by created_at descending
        timeline_items.sort(key=lambda x: x['created_at'], reverse=True)

        context.update({
            'total_bags_general': total_bags_general,
            'total_bags_recyclable': total_bags_recyclable,
            'total_plants': total_plants,
            'total_weeds': total_weeds,
            'weeding_summary': weeding_summary,
            'past_visits': past_visits,
            'stage_history': stage_history,
            'timeline_items': timeline_items,
            'today_tasks': today_tasks,
            'future_tasks': future_tasks,
            'today': today,
            'days_in_stage': days_in_stage
        })
        return context

class SectionCreateView(LoginRequiredMixin, CreateView):
    model = Section
    form_class = SectionForm
    template_name = 'core/section_form.html'
    success_url = reverse_lazy('section_list')

class SectionUpdateView(LoginRequiredMixin, UpdateView):
    model = Section
    form_class = SectionForm
    template_name = 'core/section_form.html'
    success_url = reverse_lazy('section_list')

class SectionDeleteView(LoginRequiredMixin, DeleteView):
    model = Section
    template_name = 'core/section_confirm_delete.html'
    success_url = reverse_lazy('section_list')

class WeeklyPlannerView(LoginRequiredMixin, ListView):
    model = Task
    template_name = 'core/weekly_planner.html'
    context_object_name = 'tasks'

    def get_queryset(self):
        # Get week from query param or default to current week
        week_str = self.request.GET.get('week')
        if week_str:
            try:
                week_date = datetime.strptime(week_str, '%Y-%m-%d').date()
                # Start from Monday of that week
                start_of_week = week_date - timedelta(days=week_date.weekday())
            except (ValueError, TypeError):
                today = timezone.now().date()
                start_of_week = today - timedelta(days=today.weekday())
        else:
            today = timezone.now().date()
            start_of_week = today - timedelta(days=today.weekday())

        end_of_week = start_of_week + timedelta(days=6)
        return Task.objects.filter(date__range=[start_of_week, end_of_week])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Always get today's date first
        today = timezone.now().date()

        # Get week from query param or default to current week
        week_str = self.request.GET.get('week')
        if week_str:
            try:
                week_date = datetime.strptime(week_str, '%Y-%m-%d').date()
                # Start from Monday of that week
                start_of_week = week_date - timedelta(days=week_date.weekday())
            except (ValueError, TypeError):
                start_of_week = today - timedelta(days=today.weekday())
        else:
            start_of_week = today - timedelta(days=today.weekday())

        # Create week days list (Monday start)
        week_days = []
        for i in range(7):
            day = start_of_week + timedelta(days=i)
            week_days.append(day)

        context['week_days'] = week_days
        context['sections'] = Section.objects.all()
        context['task_form'] = TaskForm()
        context['today'] = today

        # Only show active templates
        context['team_task_templates'] = TaskTemplate.objects.filter(assignee_type='team', is_active=True)
        context['manager_task_templates'] = TaskTemplate.objects.filter(assignee_type='manager', is_active=True)

        # Navigation dates for prev/next week
        context['prev_week'] = start_of_week - timedelta(days=7)
        context['next_week'] = start_of_week + timedelta(days=7)

        return context


class MonthlyPlannerView(LoginRequiredMixin, ListView):
    model = Task
    template_name = 'core/monthly_planner.html'
    context_object_name = 'tasks'

    def get_queryset(self):
        # Get year and month from query params or default to current
        year_str = self.request.GET.get('year')
        month_str = self.request.GET.get('month')

        if year_str and month_str:
            try:
                year = int(year_str)
                month = int(month_str)
            except (ValueError, TypeError):
                today = timezone.now().date()
                year = today.year
                month = today.month
        else:
            today = timezone.now().date()
            year = today.year
            month = today.month

        # Get first and last day of month
        cal = calendar.Calendar(firstweekday=0)  # Monday start
        month_days = cal.monthdatescalendar(year, month)

        # Get date range including padding days
        first_day = month_days[0][0]
        last_day = month_days[-1][-1]

        return Task.objects.filter(
            date__range=[first_day, last_day]
        ).select_related('section')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get year and month from query params or default to current
        year_str = self.request.GET.get('year')
        month_str = self.request.GET.get('month')

        if year_str and month_str:
            try:
                year = int(year_str)
                month = int(month_str)
            except (ValueError, TypeError):
                today = timezone.now().date()
                year = today.year
                month = today.month
        else:
            today = timezone.now().date()
            year = today.year
            month = today.month

        context['year'] = year
        context['month'] = month
        context['month_name'] = calendar.month_name[month]

        # Generate calendar grid (Monday start)
        cal = calendar.Calendar(firstweekday=0)
        month_weeks = cal.monthdatescalendar(year, month)
        
        context['month_weeks'] = month_weeks

        # Group tasks by date for efficient template rendering
        tasks_by_date = defaultdict(list)
        for task in context['tasks']:
            tasks_by_date[task.date].append(task)
        context['tasks_by_date'] = dict(tasks_by_date)

        # Navigation dates
        # Previous month
        if month == 1:
            context['prev_year'] = year - 1
            context['prev_month'] = 12
        else:
            context['prev_year'] = year
            context['prev_month'] = month - 1

        # Next month
        if month == 12:
            context['next_year'] = year + 1
            context['next_month'] = 1
        else:
            context['next_year'] = year
            context['next_month'] = month + 1

        # Current month flag
        today = timezone.now().date()
        context['is_current_month'] = (today.year == year and today.month == month)
        context['today'] = today

        # For task creation modal
        context['sections'] = Section.objects.all()
        context['team_task_templates'] = TaskTemplate.objects.filter(assignee_type='team', is_active=True)
        context['manager_task_templates'] = TaskTemplate.objects.filter(assignee_type='manager', is_active=True)

        return context

class DailyAgendaView(LoginRequiredMixin, ListView):
    model = Task
    template_name = 'core/daily_agenda.html'
    context_object_name = 'tasks'
    
    def get_queryset(self):
        date_str = self.request.GET.get('date')
        if date_str:
            try:
                target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                try:
                    return Task.objects.filter(
                        date=target_date
                    ).order_by('assignee_type', 'section__name')
                except Exception:
                    return Task.objects.filter(
                        date=target_date
                    ).order_by('section__name')
            except (ValueError, TypeError):
                pass
        return Task.objects.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        date_str = self.request.GET.get('date')
        if date_str:
            try:
                target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                target_date = None
        else:
            target_date = None
        context['today'] = target_date
        return context

class TaskCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Task
    form_class = TaskForm
    template_name = 'core/task_form.html'
    success_url = reverse_lazy('weekly_planner')
    success_message = "Task created successfully!"
    
    def get_initial(self):
        initial = super().get_initial()
        date_str = self.request.GET.get('date')
        if date_str:
            try:
                target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                initial['date'] = target_date
            except (ValueError, TypeError):
                pass
        return initial
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['task_templates'] = TaskTemplate.objects.filter(is_active=True)
        return context

    def get_success_url(self):
        next_url = self.request.POST.get('next', self.request.GET.get('next', ''))
        if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts=None):
            return next_url
        return reverse_lazy('weekly_planner')

class TaskUpdateView(LoginRequiredMixin, UpdateView):
    model = Task
    form_class = TaskForm
    template_name = 'core/task_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['task_templates'] = TaskTemplate.objects.filter(is_active=True)
        return context

    def get_success_url(self):
        next_url = self.request.GET.get('next') or self.request.POST.get('next')
        if next_url:
            return next_url
        return reverse_lazy('weekly_planner')

class TaskDeleteView(LoginRequiredMixin, DeleteView):
    model = Task
    template_name = 'core/task_confirm_delete.html'

    def get_success_url(self):
        next_url = self.request.GET.get('next') or self.request.POST.get('next')
        if next_url:
            return next_url
        return reverse_lazy('weekly_planner')

class VisitLogCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = VisitLog
    form_class = VisitLogForm
    template_name = 'core/visit_log_form.html'
    success_url = reverse_lazy('daily_agenda')
    success_message = "Visit log created successfully!"
    
    def get_initial(self):
        initial = super().get_initial()
        section_id = self.request.GET.get('section')
        task_id = self.request.GET.get('task')
        
        if section_id:
            initial['section'] = section_id
        if task_id:
            task = get_object_or_404(Task, pk=task_id)
            initial['task'] = task
            initial['section'] = task.section
            initial['date'] = task.date
            # Pre-fill notes with task instructions for context-aware logging
            initial['notes'] = task.instructions
        else:
            initial['date'] = timezone.now().date()
            
        return initial
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        next_url = self.request.POST.get('next', self.request.GET.get('next', ''))
        context['next'] = next_url
        
        # Get task from initial data or GET params for context-aware logging
        task_id = self.request.GET.get('task')
        task = None
        if task_id:
            try:
                task = Task.objects.get(pk=task_id)
            except Task.DoesNotExist:
                pass
        elif 'task' in context['form'].initial:
            task = context['form'].initial.get('task')
        
        # Determine task_type for UI adaptation
        if task and task.template:
            context['task_type'] = task.template.task_type
            context['task_template_name'] = task.template.name
        else:
            # Default to 'unplanned' if no task or template
            context['task_type'] = 'unplanned'
            context['task_template_name'] = None
        
        context['related_task'] = task
        
        print(f"[DEBUG] VisitLogCreateView.get_context_data called - method: {self.request.method}")
        if self.request.method == 'POST':
            print(f"[DEBUG] POST data keys: {list(self.request.POST.keys())}")
            print(f"[DEBUG] POST metrics data: {dict(self.request.POST.lists()) if 'metrics-0-metric_type' in self.request.POST else 'NO METRICS DATA'}")
            context['metric_formset'] = MetricFormSet(self.request.POST)
            context['photo_formset'] = PhotoFormSet(self.request.POST, self.request.FILES)
            print(f"[DEBUG] MetricFormSet created with {len(context['metric_formset'].forms)} forms")
            print(f"[DEBUG] PhotoFormSet created with {len(context['photo_formset'].forms)} forms")
        else:
            context['metric_formset'] = MetricFormSet()
            context['photo_formset'] = PhotoFormSet()
            print(f"[DEBUG] GET - MetricFormSet has {len(context['metric_formset'].forms)} forms")
            print(f"[DEBUG] GET - PhotoFormSet has {len(context['photo_formset'].forms)} forms")
        return context
    
    def get_success_url(self):
        next_url = self.request.POST.get('next', self.request.GET.get('next', ''))
        if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts=None):
            return next_url
        return reverse_lazy('daily_agenda')

    def form_valid(self, form):
        print(f"[DEBUG] VisitLogCreateView.form_valid called")
        context = self.get_context_data()
        metric_formset = context['metric_formset']
        photo_formset = context['photo_formset']
        
        print(f"[DEBUG] MetricFormSet valid: {metric_formset.is_valid()}")
        print(f"[DEBUG] PhotoFormSet valid: {photo_formset.is_valid()}")
        
        if metric_formset.is_valid() and photo_formset.is_valid():
            print("[DEBUG] All forms valid, saving...")
            try:
                response = super().form_valid(form)
                metric_formset.instance = self.object
                metric_formset.save()
                
                photo_formset.instance = self.object
                for photo_form in photo_formset.forms:
                    if photo_form.cleaned_data.get('file') and not photo_form.cleaned_data.get('DELETE'):
                        photo_form.instance.section = self.object.section
                photo_formset.save()
                
                if self.object.task:
                    self.object.task.is_completed = True
                    self.object.task.save()
                
                return response
            except Exception as e:
                print(f"[DEBUG] ERROR during save: {e}")
                raise
        else:
            print(f"[DEBUG] form_valid called but formsets invalid")
            return self.form_invalid(form)

    def form_invalid(self, form):
        print(f"[DEBUG] VisitLogCreateView.form_invalid called")
        print(f"[DEBUG] Main form errors: {form.errors}")
        context = self.get_context_data()
        print(f"[DEBUG] Metric formset errors: {context['metric_formset'].errors}")
        print(f"[DEBUG] Photo formset errors: {context['photo_formset'].errors}")
        return super().form_invalid(form)

class VisitLogUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = VisitLog
    form_class = VisitLogForm
    template_name = 'core/visit_log_form.html'
    success_message = "Visit log updated successfully!"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        next_url = self.request.POST.get('next', self.request.GET.get('next', ''))
        context['next'] = next_url
        
        visit_log = self.get_object()
        task = visit_log.task
        
        # Determine task_type for UI adaptation
        if task and task.template:
            context['task_type'] = task.template.task_type
            context['task_template_name'] = task.template.name
        else:
            context['task_type'] = 'unplanned'
            context['task_template_name'] = None
            
        context['related_task'] = task

        if self.request.method == 'POST':
            context['metric_formset'] = MetricFormSet(self.request.POST, instance=visit_log)
            context['photo_formset'] = PhotoFormSet(self.request.POST, self.request.FILES, instance=visit_log)
        else:
            context['metric_formset'] = MetricFormSet(instance=visit_log)
            context['photo_formset'] = PhotoFormSet(instance=visit_log)
            
        return context

    def form_valid(self, form):
        print(f"[DEBUG] VisitLogUpdateView.form_valid called")
        context = self.get_context_data()
        metric_formset = context['metric_formset']
        photo_formset = context['photo_formset']
        
        print(f"[DEBUG] MetricFormSet valid: {metric_formset.is_valid()}")
        print(f"[DEBUG] PhotoFormSet valid: {photo_formset.is_valid()}")
        
        if metric_formset.is_valid() and photo_formset.is_valid():
            print("[DEBUG] All forms valid, saving...")
            response = super().form_valid(form)
            metric_formset.save()
            
            # Ensure section is set on photos
            for photo_form in photo_formset.forms:
                if photo_form.cleaned_data.get('file') and not photo_form.cleaned_data.get('DELETE'):
                    photo_form.instance.section = self.object.section
            
            photo_formset.save()
            return response
        else:
            print(f"[DEBUG] form_valid called but formsets invalid")
            return self.form_invalid(form)

    def form_invalid(self, form):
        print(f"[DEBUG] VisitLogUpdateView.form_invalid called")
        print(f"[DEBUG] Main form errors: {form.errors}")
        context = self.get_context_data()
        print(f"[DEBUG] Metric formset errors: {context['metric_formset'].errors}")
        print(f"[DEBUG] Photo formset errors: {context['photo_formset'].errors}")
        return super().form_invalid(form)

    def get_success_url(self):
        next_url = self.request.POST.get('next', self.request.GET.get('next', ''))
        if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts=None):
            return next_url
        return reverse_lazy('daily_agenda')

def task_complete_view(request, pk):
    task = get_object_or_404(Task, pk=pk)
    task.is_completed = True
    task.save()

    # Create a visit log for the completed task
    VisitLog.objects.create(
        task=task,
        section=task.section,
        date=timezone.now().date(),
        notes=f"Task completed: {task.instructions}"
    )

    return redirect('daily_agenda')


# Task Template Management Views
class TaskTemplateListView(LoginRequiredMixin, ListView):
    model = TaskTemplate
    template_name = 'core/task_template_list.html'
    context_object_name = 'templates'

    def get_queryset(self):
        # Order by active first, then by name
        return TaskTemplate.objects.all().order_by('-is_active', 'name')


class TaskTemplateCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = TaskTemplate
    form_class = TaskTemplateForm
    template_name = 'core/task_template_form.html'
    success_url = reverse_lazy('task_template_list')
    success_message = "Task template created successfully!"


class TaskTemplateUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = TaskTemplate
    form_class = TaskTemplateForm
    template_name = 'core/task_template_form.html'
    success_url = reverse_lazy('task_template_list')
    success_message = "Task template updated successfully!"


class TaskTemplateDeleteView(LoginRequiredMixin, DeleteView):
    model = TaskTemplate
    template_name = 'core/task_template_confirm_delete.html'
    success_url = reverse_lazy('task_template_list')

    def delete(self, request, *args, **kwargs):
        # Instead of hard delete, set is_active to False
        self.object = self.get_object()
        self.object.is_active = False
        self.object.save()
        from django.contrib import messages
        messages.success(request, f"'{self.object.name}' has been retired. Existing tasks using this template are preserved.")
        return redirect(self.get_success_url())


class VisitLogListView(LoginRequiredMixin, ListView):
    """Master Activity Log - comprehensive view of all visit logs with search and filtering."""
    model = VisitLog
    template_name = 'core/visit_log_list.html'
    context_object_name = 'visit_logs'
    paginate_by = 25

    def get_queryset(self):
        queryset = VisitLog.objects.select_related('section', 'task').prefetch_related('metrics', 'photos').order_by('-date', '-created_at')
        
        # Global search
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(notes__icontains=search_query) | 
                Q(section__name__icontains=search_query) |
                Q(task__template__name__icontains=search_query)
            )
        
        # Section filter
        section_id = self.request.GET.get('section')
        if section_id:
            queryset = queryset.filter(section_id=section_id)
        
        # Date range filters
        start_date = self.request.GET.get('start_date')
        if start_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d').date()
                queryset = queryset.filter(date__gte=start)
            except (ValueError, TypeError):
                pass
        
        end_date = self.request.GET.get('end_date')
        if end_date:
            try:
                end = datetime.strptime(end_date, '%Y-%m-%d').date()
                queryset = queryset.filter(date__lte=end)
            except (ValueError, TypeError):
                pass
        
        # Activity type filter (Planned vs Unplanned)
        activity_type = self.request.GET.get('activity_type')
        if activity_type == 'planned':
            queryset = queryset.filter(task__isnull=False)
        elif activity_type == 'unplanned':
            queryset = queryset.filter(task__isnull=True)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sections'] = Section.objects.all()
        context['search_query'] = self.request.GET.get('q', '')
        context['selected_section'] = self.request.GET.get('section', '')
        context['start_date'] = self.request.GET.get('start_date', '')
        context['end_date'] = self.request.GET.get('end_date', '')
        context['activity_type'] = self.request.GET.get('activity_type', '')
        
        # Preserve query parameters for pagination
        query_params = self.request.GET.copy()
        if 'page' in query_params:
            del query_params['page']
        context['query_params'] = query_params.urlencode()
        
        return context
