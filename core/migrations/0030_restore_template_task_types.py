# Generated manually - Restore task_type mappings for templates that lost them

from django.db import migrations


def restore_template_task_types(apps, schema_editor):
    """Restore task_type foreign keys based on original migration 0002 definitions and name patterns."""
    TaskTemplate = apps.get_model('core', 'TaskTemplate')
    TaskType = apps.get_model('core', 'TaskType')
    
    # Get task type IDs by code
    task_types = {}
    for tt in TaskType.objects.all():
        task_types[tt.code] = tt.id
    
    # If TaskTypes don't exist, we can't do anything
    if not task_types:
        print("No TaskType records found. Skipping migration.")
        return
    
    # Original mapping from migration 0002_add_real_world_task_templates.py
    original_mappings = {
        'Emergency Litter Cleanup': 'litter_run',
        'River Bank Stabilization': 'weeding',
        'Native Tree Planting': 'planting',
        'Water Quality Monitoring': 'litter_run',
        'Community Cleanup Day': 'litter_run',
        'Invasive Plant Removal - Wattle': 'weeding',
        'Wetland Planting': 'planting',
        'Debris Removal - Large Items': 'litter_run',
        'Pathway Maintenance': 'weeding',
        'Pollinator Garden Planting': 'planting',
        'Storm Drain Clearing': 'litter_run',
        'Biological Control Monitoring': 'weeding',
        'Riparian Buffer Planting': 'planting',
        'Illegal Dumping Site Cleanup': 'litter_run',
        'Seed Collection': 'weeding',
        'Educational Planting Day': 'planting',
    }
    
    # Keyword-based mappings for templates added after migration 0002
    # Order matters - earlier matches take precedence
    keyword_mappings = [
        # Weeding/Removal related → weeding (check these first to avoid 'plant removal' matching planting)
        (['weed', 'invasive removal', 'wattle', 'brush', 'removal', 'stabilization', 'pathway', 'biological', 'seed collection'], 'weeding'),
        # Litter/Cleanup related → litter_run
        (['litter', 'clean', 'trash', 'debris', 'dumping', 'drain', 'quality monitoring'], 'litter_run'),
        # Planting related → planting
        (['planting', 'plant tree', 'tree planting', 'wetland', 'pollinator', 'riparian', 'garden'], 'planting'),
        # Admin/Manager related → admin
        (['admin', 'fundraising', 'media', 'meeting', 'outreach', 'planning', 'reporting', 'survey', 'committee', 'intern', 'workshop'], 'admin'),
    ]
    
    updated_count = 0
    skipped_count = 0
    
    # Process templates that need task_type assignment
    for template in TaskTemplate.objects.filter(task_type__isnull=True):
        task_type_code = None
        
        # First, check exact match from original mappings
        if template.name in original_mappings:
            task_type_code = original_mappings[template.name]
        else:
            # Try keyword matching (case-insensitive)
            name_lower = template.name.lower()
            for keywords, code in keyword_mappings:
                if any(keyword in name_lower for keyword in keywords):
                    task_type_code = code
                    break
        
        # Apply the mapping if found
        if task_type_code and task_type_code in task_types:
            template.task_type_id = task_types[task_type_code]
            template.save(update_fields=['task_type'])
            updated_count += 1
            print(f"  Updated '{template.name}' -> {task_type_code}")
        else:
            skipped_count += 1
            print(f"  Skipped '{template.name}' (no matching task type)")
    
    print(f"\nMigration complete: {updated_count} templates updated, {skipped_count} skipped")


def revert_template_task_types(apps, schema_editor):
    """Revert task_type to NULL for all templates (reverse migration)."""
    TaskTemplate = apps.get_model('core', 'TaskTemplate')
    
    # This is a destructive reverse - we could try to store old values
    # but for simplicity, we'll just set them back to NULL
    TaskTemplate.objects.exclude(task_type__isnull=True).update(task_type=None)
    print("Reverted all template task_types to NULL")


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0029_create_missing_tasktypes'),
    ]

    operations = [
        migrations.RunPython(restore_template_task_types, revert_template_task_types),
    ]
