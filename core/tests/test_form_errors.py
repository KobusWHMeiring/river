from django.test import TestCase
from django.template import Template, Context

from core.forms import TaskForm, MetricFormSet


class RenderFormErrorsTagTests(TestCase):
    """The shared error-summary tag flattens form and formset errors into a
    single accessible banner, and renders nothing when there are no errors."""

    def test_renders_field_error_with_label_and_anchor(self):
        form = TaskForm(data={})
        out = Template(
            '{% load form_tags %}{% render_form_errors form %}'
        ).render(Context({'form': form}))

        self.assertIn('Please correct the errors below', out)
        self.assertIn('Date is required for non-rolling tasks.', out)
        self.assertIn('id_date', out)

    def test_renders_formset_error_with_row_label(self):
        form = TaskForm()  # unbound -> no errors
        data = {
            'metrics-TOTAL_FORMS': '1',
            'metrics-INITIAL_FORMS': '0',
            'metrics-MIN_NUM_FORMS': '0',
            'metrics-MAX_NUM_FORMS': '1000',
        }
        formset = MetricFormSet(data)
        out = Template(
            '{% load form_tags %}{% render_form_errors form formset %}'
        ).render(Context({'form': form, 'formset': formset}))

        self.assertIn('Metric type', out)
        self.assertIn('This field is required.', out)

    def test_renders_nothing_when_no_errors(self):
        form = TaskForm()  # unbound -> no errors
        out = Template(
            '{% load form_tags %}{% render_form_errors form %}'
        ).render(Context({'form': form}))
        self.assertEqual(out.strip(), '')
