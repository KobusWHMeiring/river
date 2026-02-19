from django.urls import path
from . import views

urlpatterns = [
    # Dashboard URL
    path('dashboard/', views.GlobalDashboardView.as_view(), name='dashboard'),
    
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

    # Task Template Management URLs
    path('templates/', views.TaskTemplateListView.as_view(), name='task_template_list'),
    path('templates/create/', views.TaskTemplateCreateView.as_view(), name='task_template_create'),
    path('templates/<int:pk>/edit/', views.TaskTemplateUpdateView.as_view(), name='task_template_edit'),
    path('templates/<int:pk>/delete/', views.TaskTemplateDeleteView.as_view(), name='task_template_delete'),
]
