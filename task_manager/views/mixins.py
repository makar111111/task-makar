"""Mixins and helpers shared by the views of several sections."""

from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.shortcuts import redirect
from django.utils.http import url_has_allowed_host_and_scheme

from task_manager.forms import SearchForm


class SearchMixin:
    """Filters a list view by the "search" GET parameter."""

    search_fields = ("name",)
    search_placeholder = "Search by name..."

    def get_queryset(self):
        queryset = super().get_queryset()
        self.search_form = SearchForm(
            self.request.GET, placeholder=self.search_placeholder
        )
        if self.search_form.is_valid():
            query = self.search_form.cleaned_data["search"]
            if query:
                conditions = Q()
                for field in self.search_fields:
                    conditions |= Q(**{f"{field}__icontains": query})
                queryset = queryset.filter(conditions)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_form"] = self.search_form
        return context


class ObjectMessageMixin(SuccessMessageMixin):
    """Success message with the saved or deleted object, e.g.
    'Task "Fix login" was created.' Works for delete views too, where
    the form has no cleaned data about the object."""

    def get_success_message(self, cleaned_data):
        return self.success_message % {"object": self.object}


class ConfirmDeleteMixin(ObjectMessageMixin):
    """Shared confirmation page for all delete views."""

    template_name = "task_manager/confirm_delete.html"
    success_message = '"%(object)s" was deleted.'

    def get_cancel_url(self):
        if hasattr(self.object, "get_absolute_url"):
            return self.object.get_absolute_url()
        return self.get_success_url()

    def get_delete_warning(self):
        return ""

    def can_delete(self):
        return True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object_type"] = self.model._meta.verbose_name
        context["cancel_url"] = self.get_cancel_url()
        context["delete_warning"] = self.get_delete_warning()
        context["can_delete"] = self.can_delete()
        return context


def redirect_back(request, fallback_url):
    """Redirect to the "next" URL of the form, if it's a safe local URL."""
    next_url = request.POST.get("next")
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(next_url)
    return redirect(fallback_url)
