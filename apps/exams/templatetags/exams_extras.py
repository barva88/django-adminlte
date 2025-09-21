from django import template
register = template.Library()


@register.filter
def fmt_score(value):
    try:
        return f"{float(value):.2f}%"
    except Exception:
        return value


@register.filter
def dict_get(d, key):
    try:
        return d.get(key)
    except Exception:
        try:
            return d[key]
        except Exception:
            return None
