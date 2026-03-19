# Generated manually - Create missing TaskTypes for template restoration

from django.db import migrations


def create_missing_tasktypes(apps, schema_editor):
    """Create the standard TaskTypes if they don't exist."""
    TaskType = apps.get_model('core', 'TaskType')
    
    task_types_data = [
        {
            'code': 'litter_run',
            'name': 'Litter Run',
            'applicable_to': 'team',
            'icon_name': 'delete_sweep',
            'color_class': 'bg-amber-50 text-amber-600 border-amber-100',
            'position': 1,
        },
        {
            'code': 'weeding',
            'name': 'Weeding',
            'applicable_to': 'all',
            'icon_name': 'grass',
            'color_class': 'bg-emerald-50 text-emerald-600 border-emerald-100',
            'position': 2,
        },
        {
            'code': 'planting',
            'name': 'Planting',
            'applicable_to': 'all',
            'icon_name': 'forest',
            'color_class': 'bg-green-50 text-green-600 border-green-100',
            'position': 3,
        },
    ]
    
    created_count = 0
    skipped_count = 0
    
    for data in task_types_data:
        # Only create if it doesn't exist
        task_type, created = TaskType.objects.get_or_create(
            code=data['code'],
            defaults=data
        )
        if created:
            created_count += 1
            print(f"  Created TaskType: {data['code']} ({data['name']})")
        else:
            skipped_count += 1
            print(f"  Skipped (already exists): {data['code']}")
    
    print(f"\nTaskType creation: {created_count} created, {skipped_count} already existed")


def delete_created_tasktypes(apps, schema_editor):
    """Delete the TaskTypes created by this migration (reverse)."""
    TaskType = apps.get_model('core', 'TaskType')
    codes = ['litter_run', 'weeding', 'planting']
    deleted = TaskType.objects.filter(code__in=codes).delete()
    print(f"Deleted {deleted[0]} TaskTypes")


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0028_fix_tasktype_applicable_to_data'),
    ]

    operations = [
        migrations.RunPython(create_missing_tasktypes, delete_created_tasktypes),
    ]
