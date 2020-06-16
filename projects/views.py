from django.conf import settings
from django.shortcuts import get_object_or_404
from django.views.generic import ListView, DetailView, TemplateView
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


class ProjectTestView(TemplateView):
    template_name = "projects/testing.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Teste de novo projeto - Projetos"
        context["navbar_active"] = "projects"

        # Project specific settings
        project_manual_settings = {
            "title": "Snake",
            "description": "Esta é uma recriação do clássico \"jogo da cobrinha\", mas com uma diferença: agora a inteligência artificial também pode jogar.",
            "dark_background": True,
            "credits": 'Imagem principal retirada do próprio jogo.<br>Imagem GIF cortesia de <a href="https://imgur.com/user/jervis" target="_blank" rel="noopener noreferrer"><em>jervis</em></a>, retirado de <a href="https://imgur.com/gallery/dAtcCfH" target="_blank" rel="noopener noreferrer">imgur</a>.<br>Ícone para fechamento da tela cheia feito por <a href="https://www.flaticon.com/authors/alfredo-hernandez" title="Alfredo Hernandez" target="_blank" rel="noopener noreferrer">Alfredo Hernandez</a> em <a href="https://www.flaticon.com/" title="Flaticon" target="_blank" rel="noopener noreferrer">Flaticon</a>.',
            "categories": ["Games", "IA"],
            "fix_scale": True,
            "custom_font": True,
            "css": "css/snake.css",
            "js": "js/snake.js"
        }

        context["project"] = project_manual_settings
        return context
