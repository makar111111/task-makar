from django import template

register = template.Library()

AVATAR_COLORS_COUNT = 5


@register.filter
def avatar_class(worker):
    """CSS class that gives every worker a stable avatar color."""
    return f"tm-av-{worker.pk % AVATAR_COLORS_COUNT}"
