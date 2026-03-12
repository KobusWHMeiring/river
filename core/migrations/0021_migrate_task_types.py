# Generated manually - Step 2: Change task_type field and migrate data

import django.db.models.deletion
from django.db import migrations, models


def migrate_task_type_data(apps, schema_editor):
    """Migrate old task_type string values to new TaskType foreign keys."""
    TaskTemplate = apps.get_model('core', 'TaskTemplate')
    TaskType = apps.get_model('core', 'TaskType')
    
    # Get task types by code
    task_types = {tt.code: tt for tt in TaskType.objects.all()}
    
    # Get all templates with their old task_type values using raw SQL
    from django.db import connection
    
    with connection.cursor() as cursor:
        # Get all templates with their old task_type values
        cursor.execute("SELECT id, task_type_old FROM core_tasktemplate")
        rows = cursor.fetchall()
    
    # Store updates to apply
    updates = []
    for template_id, old_task_type in rows:
        if old_task_type and old_task_type in task_types:
            task_type = task_types[old_task_type]
            updates.append((task_type.id, template_id))
    
    # Apply updates using Django ORM
    for task_type_id, template_id in updates:
        TaskTemplate.objects.filter(id=template_id).update(task_type_id=task_type_id)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0020_add_tasktype_model'),
    ]

    operations = [
        # First, rename the old field to preserve it temporarily
        migrations.RenameField(
            model_name='tasktemplate',
            old_name='task_type',
            new_name='task_type_old',
        ),
        # Add the new field
        migrations.AddField(
            model_name='tasktemplate',
            name='task_type',
            field=models.ForeignKey(
                blank=True, 
                help_text='Category of task', 
                null=True, 
                on_delete=django.db.models.deletion.SET_NULL, 
                related_name='templates', 
                to='core.tasktype'
            ),
        ),
        # Run data migration
        migrations.RunPython(migrate_task_type_data, migrations.RunPython.noop),
        # Remove the old field
        migrations.RemoveField(
            model_name='tasktemplate',
            name='task_type_old',
        ),
    ]
