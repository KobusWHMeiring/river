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


_METRIC_TYPES = {
    'litter': ('litter_general', 'litter_recyclable'),
    'plant': ('plant',),
    'weed': ('weed',),
}


def build_visit_log_queryset(params: dict) -> QuerySet:
    """Build the full, sorted, de-duplicated VisitLog queryset for list/export.

    Data Flow Contract:
      in:  params — request.GET-like mapping with optional keys
           q, section, start_date, end_date, activity_type, metric, species, sort
      out: QuerySet[VisitLog] filtered, de-duplicated, ordered
      side effects: none
    """
    queryset = base_visit_log_queryset(params)

    metric = params.get('metric')
    if metric == 'participants':
        queryset = queryset.filter(participant_count__gt=0)
    elif metric in _METRIC_TYPES:
        queryset = queryset.filter(metrics__metric_type__in=_METRIC_TYPES[metric])

    species = params.get('species')
    if species:
        queryset = queryset.filter(metrics__label=species)

    if metric in _METRIC_TYPES or metric == 'participants' or species:
        queryset = queryset.distinct()

    sort = params.get('sort', '-date')
    if sort == 'date':
        queryset = queryset.order_by('date', '-created_at')
    elif sort == 'section':
        queryset = queryset.order_by(F('section__name').asc(nulls_last=True), '-date')
    elif sort == '-participant_count':
        queryset = queryset.order_by('-participant_count', '-date')
    else:
        queryset = queryset.order_by('-date', '-created_at')

    return queryset


METRIC_DISPLAY = {
    'litter': ('Litter', 'bags'),
    'participants': ('Participation', 'people'),
    'plant': ('Plants', ''),
    'weed': ('Weeds', ''),
}


def visit_log_total(queryset: QuerySet, metric: Optional[str] = None, species: Optional[str] = None) -> int:
    """Return the aggregate total for the active metric/species filter.

    Data Flow Contract:
      in:  queryset — base-filtered QuerySet[VisitLog] (from base_visit_log_queryset)
           metric — 'litter' | 'plant' | 'weed' | 'participants' | None
           species — exact Metric.label, or None
      out: int — sum of matching Metric.value for litter/plant/weed;
           sum of participant_count for participants; 0 when no metric
      side effects: none
    """
    if metric == 'litter':
        return queryset.filter(metrics__metric_type__in=('litter_general', 'litter_recyclable')).aggregate(total=Sum('metrics__value'))['total'] or 0
    if metric in ('plant', 'weed'):
        qs = queryset.filter(metrics__metric_type=metric)
        if species:
            qs = qs.filter(metrics__label=species)
        return qs.aggregate(total=Sum('metrics__value'))['total'] or 0
    if metric == 'participants':
        return queryset.aggregate(total=Sum('participant_count'))['total'] or 0
    return 0


def metric_total_display(metric: Optional[str], total: int, species: Optional[str] = None) -> Optional[str]:
    """Return the human summary line for the drill-down total header, or None.

    Data Flow Contract:
      in:  metric ('litter'|'plant'|'weed'|'participants'|None), total int, species str|None
      out: str like 'Litter — 8 bags' / 'Plants · Restio — 10', or None when no metric
      side effects: none
    """
    if not metric or metric not in METRIC_DISPLAY:
        return None
    label, unit = METRIC_DISPLAY[metric]
    if species:
        label = f'{label} · {species}'
    unit = f' {unit}' if unit else ''
    return f'{label} — {total}{unit}'
