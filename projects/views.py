from django.views.generic import ListView, TemplateView
from .models import Project


class ProjectListView(ListView):
    model = Project
    context_object_name = "projects"
    ordering = ["-id"]

    def get_context_data(self):
        context = super().get_context_data()
        context["title"] = "Projetos"
        context["navbar_active"] = "projects"

        # Featured Projects
        has_featured = Project.objects.filter(featured=True).count() > 0
        context["featured"] = has_featured

        if has_featured:
            context["projects_featured"] = Project.objects.filter(featured=True).order_by('-id')[:3]

        return context


class PongProjectView(TemplateView):
    template_name = "projects/pong.html"

    def get_context_data(self):
        context = super().get_context_data()
        context["title"] = "Pong - Projetos"
        context["navbar_active"] = "projects"
        return context


class SnakeProjectView(TemplateView):
    template_name = "projects/snake.html"

    def get_context_data(self):
        context = super().get_context_data()
        context["title"] = "Snake - Projetos"
        context["navbar_active"] = "projects"
        return context
