from django.views.generic import TemplateView


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
