from django.conf import settings
from django.shortcuts import get_object_or_404
from django.views.generic import ListView, DetailView
from .models import Project


class ProjectListView(ListView):
    model = Project
    context_object_name = "projects"
    ordering = ["-id"]

    def get_queryset(self, **kwargs):
        if self.request.user.is_authenticated:
            return Project.objects.all().order_by('-id')
        else:
            return Project.objects.filter(published=True).order_by('-id')

    def get_context_data(self):
        context = super().get_context_data()
        context["title"] = "Projetos"
        context["navbar_active"] = "projects"
        context["analytics_id"] = settings.ANALYTICS_ID

        # Featured Projects
        has_featured = Project.objects.filter(featured=True).count() > 0
        context["featured"] = has_featured

        if has_featured:
            context["projects_featured"] = Project.objects.filter(featured=True).order_by('-id')[:3]

        return context


class ProjectDetailView(DetailView):
    model = Project
    context_object_name = "project"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = get_object_or_404(Project, slug=self.kwargs['slug'])
        context["title"] = project.title + " - Projetos"
        context["navbar_active"] = "projects"
        context["analytics_id"] = settings.ANALYTICS_ID
        return context
