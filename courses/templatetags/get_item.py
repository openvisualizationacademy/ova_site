from django import template

register = template.Library()


@register.filter
def get_item(mapping, key):
    if not isinstance(mapping, dict):
        return None
    try:
        return mapping.get(int(key))
    except (ValueError, TypeError):
        return None
