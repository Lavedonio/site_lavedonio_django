from django.views.generic import TemplateView
from blog.models import Post
from projects.models import Project


class DashboardView(TemplateView):
    template_name = "admin_dashboard/admin_base.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Homepage"
        context["navbar_active"] = "home"

        context["posts"] = Post.objects.all().order_by('-date_posted')[:3]
        context["projects"] = Project.objects.all().order_by('-pk')[:3]
        return context
