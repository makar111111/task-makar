from django import template

register = template.Library()

AVATAR_COLORS_COUNT = 5
PROJECT_COLORS = (
    "#534ab7",
    "#1d9e75",
    "#ba7517",
    "#d4537e",
    "#378add",
    "#d85a30",
)


@register.filter
def avatar_class(worker):
    """CSS class that gives every worker a stable avatar color."""
    return f"tm-av-{worker.pk % AVATAR_COLORS_COUNT}"


@register.filter
def project_color(project):
    """Stable color of the project dot and progress bar."""
    return PROJECT_COLORS[project.pk % len(PROJECT_COLORS)]
