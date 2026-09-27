from django import template

from task_manager.models import Task

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


@register.filter
def startswith(text, prefix):
    return str(text).startswith(prefix)


@register.simple_tag
def query_transform(request, **kwargs):
    """Return the current query string with the given parameters replaced.

    Pagination and status links use it to change one parameter and keep
    the search and filters, e.g. ``?search=login&priority=high&page=2``.
    A parameter passed as ``None`` is removed.
    """
    updated = request.GET.copy()
    for key, new_value in kwargs.items():
        if new_value is None:
            updated.pop(key, None)
        else:
            updated[key] = new_value
    return updated.urlencode()


@register.simple_tag
def elided_page_range(page_obj):
    """Page numbers with "…" in place of long runs: 1 2 3 … 9 10."""
    return page_obj.paginator.get_elided_page_range(
        page_obj.number, on_each_side=1, on_ends=1
    )


@register.simple_tag
def open_tasks_count():
    return Task.objects.filter(is_completed=False).count()
