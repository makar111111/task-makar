from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from task_manager.models import (
    Position,
    Project,
    Tag,
    Task,
    TaskType,
    Team,
    Worker,
)


@admin.register(Worker)
class WorkerAdmin(UserAdmin):
    list_display = UserAdmin.list_display + ("position",)
    list_filter = UserAdmin.list_filter + ("position",)
    fieldsets = UserAdmin.fieldsets + (
        ("Additional info", {"fields": ("position",)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "Additional info",
            {"fields": ("first_name", "last_name", "email", "position")},
        ),
    )


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "project",
        "task_type",
        "priority",
        "deadline",
        "is_completed",
    )
    list_filter = ("is_completed", "priority", "task_type", "project", "tags")
    search_fields = ("name", "description")
    filter_horizontal = ("assignees", "tags")


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    filter_horizontal = ("teams",)


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    filter_horizontal = ("members",)


@admin.register(Position, TaskType, Tag)
class NameOnlyAdmin(admin.ModelAdmin):
    search_fields = ("name",)
