# Generated manually to fix missing assignee_type field in TaskTemplate table
from django.db import migrations, models


def update_existing_templates(apps, schema_editor):
    """
    Update existing TaskTemplate records with appropriate assignee_type.
    This ensures data consistency after adding the field.
    """
    TaskTemplate = apps.get_model('core', 'TaskTemplate')
    
    # Manager task names (admin activities)
    manager_task_names = [
        'River survey',
        'Meeting',
        'Workshop',
        'Reporting',
        'Fundraising',
        'Planning',
        'Team admin',
        'Intern admin',
        'Committee admin',
        'Media',
        'Outreach',
    ]
    
    # Update manager tasks
    TaskTemplate.objects.filter(name__in=manager_task_names).update(assignee_type='manager')
    
    # Update all others as team tasks (default)
    TaskTemplate.objects.exclude(name__in=manager_task_names).update(assignee_type='team')


def revert_updates(apps, schema_editor):
    """Revert function for migration - sets all to team (default)."""
    TaskTemplate = apps.get_model('core', 'TaskTemplate')
    TaskTemplate.objects.all().update(assignee_type='team')


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_add_admin_task_type'),
    ]

    operations = [
        # Add missing assignee_type field to TaskTemplate
        # Migration 0006 should have added this but may have failed
        migrations.AddField(
            model_name='tasktemplate',
            name='assignee_type',
            field=models.CharField(
                choices=[('team', 'Team'), ('manager', 'Manager')],
                default='team',
                max_length=10
            ),
        ),
        # Temporary model ordering fixes (remove assignee_type from ordering)
        migrations.AlterModelOptions(
            name='tasktemplate',
            options={'ordering': ['name']},
        ),
        migrations.AlterModelOptions(
            name='task',
            options={'ordering': ['date']},
        ),
        # Update existing data with correct assignee_type values
        migrations.RunPython(update_existing_templates, revert_updates),
    ]