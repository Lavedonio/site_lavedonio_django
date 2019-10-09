from django.views.generic import TemplateView
from blog.models import Post
from projects.models import Project


class HomepageView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Homepage"
        context["navbar_active"] = "home"

        context["posts"] = Post.objects.filter(featured=True).order_by('-date_posted')[:3]
        context["projects"] = Project.objects.filter(featured=True).order_by('-pk')[:3]
        return context


class AboutView(TemplateView):
    template_name = "about.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Sobre"
        context["navbar_active"] = "about"
        return context


class ContactView(TemplateView):
    template_name = "contact.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Contato"
        context["navbar_active"] = "contact"
        return context
