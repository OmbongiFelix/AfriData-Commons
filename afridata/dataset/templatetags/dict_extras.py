from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get item from dictionary by key"""
    if isinstance(dictionary, dict):
        return dictionary.get(key, "N/A")
    return "N/A"

@register.filter
def truncate_chars(value, max_length):
    """Truncate string to specified length"""
    if len(str(value)) > max_length:
        return str(value)[:max_length] + "..."
    return str(value)