"""Template tags for rendering form and formset validation errors."""
from django import template

register = template.Library()


@register.inclusion_tag("core/includes/form_errors.html")
def render_form_errors(form, *formsets):
    """Flatten validation errors from a form (and optional inline formsets) into
    a single list of ``{"label", "message", "anchor"}`` items for the shared
    error-summary banner. Returns an empty list when there is nothing to show,
    so the partial renders no markup in that case.

    The logic is kept here in Python rather than in the template, per the
    "No Logic in Templates" build principle.
    """
    errors = []

    def add(label, message, anchor=None):
        if message:
            errors.append({"label": label, "message": message, "anchor": anchor})

    # Main form non-field errors (no field label / anchor).
    for message in form.non_field_errors():
        add(None, message)

    # Main form field errors (with human label + anchor link).
    for field_name, errs in form.errors.items():
        if field_name == "__all__":
            continue
        try:
            bound = form[field_name]
            label = bound.label or field_name
            anchor = bound.id_for_label
        except KeyError:
            label = field_name
            anchor = None
        for message in errs:
            add(label, message, anchor)

    # Inline formset errors (labelled with the formset prefix and row number).
    for formset in formsets:
        prefix = (getattr(formset, "prefix", "") or "").replace("_", " ").strip().title() or "Form"
        for message in formset.non_form_errors():
            add(prefix, message)
        for index, subform in enumerate(formset.forms, start=1):
            for message in subform.non_field_errors():
                add(f"{prefix} {index}", message)
            for field_name, errs in subform.errors.items():
                if field_name == "__all__":
                    continue
                try:
                    label = subform[field_name].label or field_name
                except KeyError:
                    label = field_name
                for message in errs:
                    add(f"{prefix} {index} · {label}", message)

    return {"errors": errors}
