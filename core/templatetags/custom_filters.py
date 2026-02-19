from django import template
from datetime import timedelta

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary by key."""
    if dictionary is None:
        return None
    return dictionary.get(key)


@register.filter
def filter_by_assignee(tasks, assignee_type):
    """Filter tasks by assignee type."""
    if tasks is None:
        return []
    return [task for task in tasks if task.assignee_type == assignee_type]


@register.filter
def add_days(date, days):
    """Add days to a date."""
    return date + timedelta(days=int(days))
