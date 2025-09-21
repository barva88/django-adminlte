from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css_class):
    try:
        existing = field.field.widget.attrs.get('class', '')
        classes = (existing + ' ' + css_class).strip()
        return field.as_widget(attrs={'class': classes})
    except Exception:
        # If it's not a form field, just return as string
        return mark_safe(str(field))
