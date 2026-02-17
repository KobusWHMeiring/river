from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Section, Task, TaskTemplate, VisitLog, Metric, Photo
from .forms import SectionForm, TaskForm, VisitLogForm, MetricFormSet, PhotoFormSet

from django.db.models import Sum, Q
from django.utils import timezone

class SectionListView(LoginRequiredMixin, ListView):
    model = Section
    template_name = 'core/section_list.html'
    context_object_name = 'sections'

class SectionDetailView(LoginRequiredMixin, DetailView):
    model = Section
    template_name = 'core/section_detail.html'
    context_object_name = 'section'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        section = self.object
        today = timezone.now().date()
        
        print(f"[DEBUG] SectionDetailView.get_context_data for section: {section.name} (ID: {section.id})")
        
        # Cumulative Metrics
        metrics = Metric.objects.filter(visit__section=section)
        print(f"[DEBUG] Found {metrics.count()} total metrics for this section")
        
        # Debug: Show all metrics
        for metric in metrics:
            print(f"[DEBUG] Metric: type={metric.metric_type}, value={metric.value}, visit_id={metric.visit.id if metric.visit else 'None'}")
        
        total_bags_general = metrics.filter(metric_type='litter_general').aggregate(total=Sum('value'))['total'] or 0
        total_bags_recyclable = metrics.filter(metric_type='litter_recyclable').aggregate(total=Sum('value'))['total'] or 0
        total_plants = metrics.filter(metric_type='plant').aggregate(total=Sum('value'))['total'] or 0
        
        print(f"[DEBUG] Totals: general={total_bags_general}, recyclable={total_bags_recyclable}, plants={total_plants}")
        
        # Timeline queries with prefetching
        past_visits = VisitLog.objects.filter(section=section).prefetch_related('metrics', 'photos').order_by('-date', '-created_at')
        print(f"[DEBUG] Found {past_visits.count()} past visits")
        
        today_tasks = Task.objects.filter(section=section, date=today)
        future_tasks = Task.objects.filter(section=section, date__gt=today, is_completed=False).order_by('date')
        
        context.update({
            'total_bags_general': total_bags_general,
            'total_bags_recyclable': total_bags_recyclable,
            'total_plants': total_plants,
            'past_visits': past_visits,
            'today_tasks': today_tasks,
            'future_tasks': future_tasks,
            'today': today,
            'days_in_stage': (timezone.now() - section.updated_at).days
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
        # Get current week's tasks
        today = timezone.now().date()
        start_of_week = today - timedelta(days=today.weekday() + 1)  # Sunday start
        end_of_week = start_of_week + timedelta(days=6)
        return Task.objects.filter(date__range=[start_of_week, end_of_week])
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        start_of_week = today - timedelta(days=today.weekday() + 1)
        
        # Create week days list
        week_days = []
        for i in range(7):
            day = start_of_week + timedelta(days=i)
            week_days.append(day)
        
        context['week_days'] = week_days
        context['sections'] = Section.objects.all()
        context['task_form'] = TaskForm()
        context['team_task_templates'] = TaskTemplate.objects.filter(assignee_type='team')
        context['manager_task_templates'] = TaskTemplate.objects.filter(assignee_type='manager')
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
            except (ValueError, TypeError):
                target_date = timezone.now().date()
        else:
            target_date = timezone.now().date()
        return Task.objects.filter(
            date=target_date
        ).order_by('assignee_type', 'section__name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        date_str = self.request.GET.get('date')
        if date_str:
            try:
                target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                target_date = timezone.now().date()
        else:
            target_date = timezone.now().date()
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
        context['task_templates'] = TaskTemplate.objects.all()
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
    success_url = reverse_lazy('weekly_planner')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['task_templates'] = TaskTemplate.objects.all()
        return context

class TaskDeleteView(LoginRequiredMixin, DeleteView):
    model = Task
    template_name = 'core/task_confirm_delete.html'
    success_url = reverse_lazy('weekly_planner')

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
        else:
            initial['date'] = timezone.now().date()
            
        return initial
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        next_url = self.request.POST.get('next', self.request.GET.get('next', ''))
        context['next'] = next_url
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
        print("[DEBUG] form_valid called")
        context = self.get_context_data()
        metric_formset = context['metric_formset']
        photo_formset = context['photo_formset']
        
        print(f"[DEBUG] MetricFormSet valid: {metric_formset.is_valid()}")
        print(f"[DEBUG] PhotoFormSet valid: {photo_formset.is_valid()}")
        
        if not metric_formset.is_valid():
            print(f"[DEBUG] MetricFormSet errors: {metric_formset.errors}")
            print(f"[DEBUG] MetricFormSet non-form errors: {metric_formset.non_form_errors()}")
        
        if not photo_formset.is_valid():
            print(f"[DEBUG] PhotoFormSet errors: {photo_formset.errors}")
            print(f"[DEBUG] PhotoFormSet non-form errors: {photo_formset.non_form_errors()}")
        else:
            # Check which forms are marked for deletion
            for i, photo_form in enumerate(photo_formset.forms):
                if photo_form.cleaned_data.get('DELETE'):
                    print(f"[DEBUG] Photo form {i} marked for deletion (no file uploaded)")
        
        if metric_formset.is_valid() and photo_formset.is_valid():
            print("[DEBUG] All forms valid, saving...")
            print(f"[DEBUG] Main form cleaned_data: section={form.cleaned_data.get('section')}, date={form.cleaned_data.get('date')}")
            try:
                response = super().form_valid(form)
                print(f"[DEBUG] VisitLog saved with ID: {self.object.id}, section={self.object.section}")
                
                metric_formset.instance = self.object
                print("[DEBUG] About to save metrics...")
                metrics_saved = metric_formset.save()
                print(f"[DEBUG] Saved {len(metrics_saved)} metrics")
                
                photo_formset.instance = self.object
                print("[DEBUG] About to save photos...")
                print(f"[DEBUG] Photo formset forms count: {len(photo_formset.forms)}")
                for i, form in enumerate(photo_formset.forms):
                    file_data = form.cleaned_data.get('file') if hasattr(form, 'cleaned_data') else None
                    desc_data = form.cleaned_data.get('description') if hasattr(form, 'cleaned_data') else None
                    print(f"[DEBUG] Photo form {i}: file={file_data}, desc={desc_data}")
                    # Set the section on each photo form before saving
                    if file_data and hasattr(form, 'instance'):
                        form.instance.section = self.object.section
                        print(f"[DEBUG] Set section on photo {i}: {self.object.section}")
                photos_saved = photo_formset.save()
                print(f"[DEBUG] Saved {len(photos_saved)} photos")
                
                # Mark task as completed if linked
                if self.object.task:
                    self.object.task.is_completed = True
                    self.object.task.save()
                    print("[DEBUG] Task marked as completed")
                
                return response
            except Exception as e:
                print(f"[DEBUG] ERROR during save: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
                raise
        else:
            print("[DEBUG] Form invalid, returning form_invalid")
            return self.form_invalid(form)

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
