from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import Http404
from django.urls import reverse_lazy
from django.utils.text import slugify
from django.utils.translation import gettext as _, gettext_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from base.editing import TranslatableEditMixin
from base.i18n import build_language_url
from .forms import RESERVED_SLUGS, ProjectForm, ProjectTranslationForm
from .models import Category, Project


class ProjectListView(ListView):
    context_object_name = "projects"
    featured_count = 2

    def get_base_queryset(self):
        return Project.objects.visible_to(self.request.user)

    def get_queryset(self):
        queryset = self.get_base_queryset().with_related()

        self.category = None
        category_slug = self.request.GET.get("category")
        if category_slug:
            self.category = Category.objects.prefetch_related("translations").filter(slug=category_slug).first()
            if self.category is None:
                raise Http404
            queryset = queryset.filter(categories=self.category)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Projects")
        context["navbar_active"] = "projects"
        context["filter_category"] = self.category
        context["categories"] = (
            Category.objects.filter(projects__in=self.get_base_queryset().values("pk"))
            .distinct()
            .prefetch_related("translations")
        )

        # Featured projects get a highlight on top and aren't repeated in the grid below
        if self.category is None:
            featured = [project for project in context["projects"] if project.featured][:self.featured_count]
            context["featured_projects"] = featured
            context["projects"] = [project for project in context["projects"] if project not in featured]

        return context


class ProjectDetailView(DetailView):
    context_object_name = "project"

    def get_queryset(self):
        return Project.objects.visible_to(self.request.user).with_related()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.object
        project_translation = project.translation
        if project_translation is None:
            raise Http404

        context["title"] = _("%(project)s - Projects") % {"project": project_translation.title}
        context["navbar_active"] = "projects"
        context["project_translation"] = project_translation
        context["canonical_url"] = build_language_url(self.request, project_translation.language, project.get_absolute_url(project_translation.language))

        self.request.language_alternate_paths = {
            language: project.get_absolute_url(language) for language in project.available_languages
        }
        return context


class ProjectEditMixin(PermissionRequiredMixin, TranslatableEditMixin):
    model = Project
    form_class = ProjectForm
    translation_form_class = ProjectTranslationForm
    translation_parent_field = "project"
    success_message = gettext_lazy("Project saved.")

    def get_queryset(self):
        return Project.objects.prefetch_related("translations")

    def get_success_url(self):
        return self.object.get_absolute_url()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["navbar_active"] = "projects"
        return context

    def prepare_object(self, form, translation_forms):
        if form.instance.slug:
            return

        # Unique slug based on the title of the first included language
        title = next(item.cleaned_data["title"] for item in translation_forms if item.is_enabled)
        base_slug = slugify(title)[:56].strip("-") or "project"
        slug, number = base_slug, 2
        while slug in RESERVED_SLUGS or Project.objects.filter(slug=slug).exclude(pk=form.instance.pk).exists():
            slug, number = f"{base_slug}-{number}", number + 1
        form.instance.slug = slug


class ProjectCreateView(ProjectEditMixin, CreateView):
    permission_required = "projects.add_project"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("New project - Projects")
        return context


class ProjectUpdateView(ProjectEditMixin, UpdateView):
    permission_required = "projects.change_project"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Edit project - Projects")
        return context


class ProjectDeleteView(PermissionRequiredMixin, DeleteView):
    model = Project
    permission_required = "projects.delete_project"
    success_url = reverse_lazy("projects:list")

    def get_queryset(self):
        return Project.objects.prefetch_related("translations")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Delete project - Projects")
        context["navbar_active"] = "projects"
        return context

    def form_valid(self, form):
        messages.success(self.request, _("Project deleted."))
        return super().form_valid(form)
