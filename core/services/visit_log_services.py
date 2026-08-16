"""Shared filtering and aggregation for VisitLog list and export views."""
from datetime import datetime
from typing import Optional

from django.db.models import F, Q, QuerySet, Sum

from ..models import VisitLog


def base_visit_log_queryset(params: dict) -> QuerySet:
    """Apply search/section/date/activity-type filters and prefetch relations.

    Data Flow Contract:
      in:  params — request.GET-like mapping with optional keys
           q, section, start_date, end_date, activity_type
      out: QuerySet[VisitLog] with select_related('section','task') and
           prefetch_related('metrics','photos')
      side effects: none
    """
    queryset = VisitLog.objects.select_related('section', 'task').prefetch_related('metrics', 'photos')

    search_query = params.get('q')
    if search_query:
        queryset = queryset.filter(
            Q(notes__icontains=search_query)
            | Q(section__name__icontains=search_query)
            | Q(task__template__name__icontains=search_query)
        )

    section_id = params.get('section')
    if section_id:
        queryset = queryset.filter(section_id=section_id)

    start_date = params.get('start_date')
    if start_date:
        try:
            queryset = queryset.filter(date__gte=datetime.strptime(start_date, '%Y-%m-%d').date())
        except (ValueError, TypeError):
            pass

    end_date = params.get('end_date')
    if end_date:
        try:
            queryset = queryset.filter(date__lte=datetime.strptime(end_date, '%Y-%m-%d').date())
        except (ValueError, TypeError):
            pass

    activity_type = params.get('activity_type')
    if activity_type == 'planned':
        queryset = queryset.filter(task__isnull=False)
    elif activity_type == 'unplanned':
        queryset = queryset.filter(task__isnull=True)

    return queryset
