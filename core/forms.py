from django import forms
from django.forms import inlineformset_factory
from django.core.validators import MinLengthValidator
from .models import Section, Task, TaskTemplate, VisitLog, Metric, Photo

class SectionForm(forms.ModelForm):
    class Meta:
        model = Section
        fields = ['name', 'color_code', 'current_stage', 'status', 'description', 'position', 'boundary_data', 'center_point']
        widgets = {
            'color_code': forms.TextInput(attrs={'type': 'color'}),
            'description': forms.Textarea(attrs={'rows': 3}),
            'position': forms.NumberInput(attrs={'min': 0}),
            'boundary_data': forms.HiddenInput(),
            'center_point': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active statuses in the dropdown
        from .models import Status
        self.fields['status'].queryset = Status.objects.filter(is_active=True)

class TaskTemplateForm(forms.ModelForm):
    class Meta:
        model = TaskTemplate
        fields = ['name', 'task_type', 'assignee_type', 'default_instructions', 'is_active']
        widgets = {
            'default_instructions': forms.Textarea(attrs={'rows': 4, 'class': 'w-full p-4 bg-slate-50 dark:bg-slate-900/50 border border-slate-200 dark:border-slate-700 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all text-slate-700 dark:text-slate-300 outline-none resize-none leading-relaxed'}),
            'name': forms.TextInput(attrs={'class': 'w-full pl-10 pr-4 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all text-slate-800 dark:text-slate-200 outline-none'}),
            'task_type': forms.Select(attrs={'class': 'w-full pl-10 pr-10 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg appearance-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all text-slate-800 dark:text-slate-200 outline-none'}),
            'assignee_type': forms.Select(attrs={'class': 'w-full pl-10 pr-10 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg appearance-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all text-slate-800 dark:text-slate-200 outline-none'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'w-5 h-5 rounded border-slate-300 text-primary focus:ring-primary'}),
        }

class TaskForm(forms.ModelForm):
    template = forms.ModelChoiceField(
        queryset=TaskTemplate.objects.none(),  # Will be set in __init__
        required=False,
        empty_label="No template"
    )

    class Meta:
        model = Task
        fields = ['date', 'section', 'assignee_type', 'instructions', 'template']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'instructions': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set the queryset for template field - only show active templates
        self.fields['template'].queryset = TaskTemplate.objects.filter(is_active=True)

        if 'template' in self.data and self.data['template']:
            try:
                template_id = int(self.data['template'])
                template = TaskTemplate.objects.get(id=template_id)
                self.fields['instructions'].initial = template.default_instructions
            except (ValueError, TaskTemplate.DoesNotExist):
                pass

class VisitLogForm(forms.ModelForm):
    class Meta:
        model = VisitLog
        fields = ['task', 'section', 'date', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['task'].required = False
        self.fields['section'].required = True

class MetricForm(forms.ModelForm):
    class Meta:
        model = Metric
        fields = ['metric_type', 'label', 'value']
        widgets = {
            'value': forms.NumberInput(attrs={'min': 0}),
        }

class PhotoForm(forms.ModelForm):
    # Make description completely optional - no validators at form level
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3})
    )
    
    class Meta:
        model = Photo
        fields = ['file', 'description']
    
    def clean_description(self):
        description = self.cleaned_data.get('description', '')
        file = self.cleaned_data.get('file')
        
        # Only validate description length if a file is being uploaded
        if file and description and len(description) < 10:
            raise forms.ValidationError("Description must be at least 10 characters when uploading a photo.")
        
        return description

class BaseMetricFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()
        for form in self.forms:
            if self.can_delete and hasattr(form, 'cleaned_data'):
                metric_type = form.cleaned_data.get('metric_type')
                value = form.cleaned_data.get('value', 0)
                # Skip saving if value is 0 for plants and weeds
                if metric_type in ['plant', 'weed'] and value == 0:
                    form.cleaned_data['DELETE'] = True

# Formset for metrics
MetricFormSet = inlineformset_factory(
    VisitLog, Metric, form=MetricForm, formset=BaseMetricFormSet, extra=0, can_delete=True
)

class BasePhotoFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()
        # Mark forms without files for deletion
        for form in self.forms:
            if self.can_delete and hasattr(form, 'cleaned_data'):
                file = form.cleaned_data.get('file')
                if not file:
                    form.cleaned_data['DELETE'] = True

# Formset for photos
PhotoFormSet = inlineformset_factory(
    VisitLog, Photo, form=PhotoForm, formset=BasePhotoFormSet, extra=0, can_delete=True
)
