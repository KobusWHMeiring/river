# Generated manually - Step 1: Create TaskType model only

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0019_status_alter_section_status'),
    ]

    operations = [
        migrations.CreateModel(
            name='TaskType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
                ('code', models.CharField(help_text="Short code used internally (e.g., 'litter_run', 'weeding')", max_length=20, unique=True)),
                ('description', models.TextField(blank=True, help_text='Optional description of this task type')),
                ('applicable_to', models.CharField(choices=[('team', 'Team'), ('manager', 'Manager'), ('both', 'Both')], default='both', help_text='Which assignee types this task type is applicable to', max_length=10)),
                ('is_active', models.BooleanField(default=True, help_text='Only active task types are shown in dropdowns')),
                ('position', models.PositiveIntegerField(default=0, help_text='Order in which task types appear')),
                ('icon_name', models.CharField(default='task', help_text="Material Symbols icon name (e.g., 'delete_sweep', 'grass', 'forest')", max_length=50)),
                ('color_class', models.CharField(default='bg-slate-50 text-slate-600 border-slate-100', help_text="Tailwind CSS classes for styling (e.g., 'bg-amber-50 text-amber-600 border-amber-100')", max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Task Type',
                'verbose_name_plural': 'Task Types',
                'ordering': ['position', 'name'],
            },
        ),
    ]
