import operator
from functools import reduce
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q
from django.views.generic import TemplateView
from django.views.generic.edit import FormView
from django.urls import reverse_lazy
from blog.models import Post
from projects.models import Project
from .forms import ContactForm


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


class ContactView(FormView):
    template_name = "contact.html"
    form_class = ContactForm
    success_url = reverse_lazy("contact-success")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Contato"
        context["navbar_active"] = "contact"
        return context

    def form_valid(self, form):
        # Sending email
        name = form.cleaned_data.get('name')
        subject = form.cleaned_data.get('subject')
        email = form.cleaned_data.get('email')
        raw_message = form.cleaned_data.get('message')

        message = "Mensagem de {0}, e-mail {1}:\n\n{2}".format(name, email, raw_message)

        from_email = settings.EMAIL_HOST_USER
        send_mail(subject, message, from_email, [settings.EMAIL_HOST_USER, email], fail_silently=False)

        return super().form_valid(form)


class ContactSuccessView(TemplateView):
    template_name = "contact_success.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Contato"
        context["navbar_active"] = "contact"
        return context


class SearchView(TemplateView):
    template_name = "search.html"

    def get_queryset(self, **kwargs):
        query = self.request.GET.get('q')

        if query:
            print(query)
            query_list = query.split()

            post_search = Post.objects.filter(
                reduce(operator.or_, (Q(title__icontains=q) for q in query_list)) |
                reduce(operator.or_, (Q(subtitle__icontains=q) for q in query_list))
            ).order_by("-date_posted")

            project_search = Project.objects.filter(
                reduce(operator.or_, (Q(title__icontains=q) for q in query_list)) |
                reduce(operator.or_, (Q(description__icontains=q) for q in query_list))
            ).order_by("-id")

            return post_search, project_search
        else:
            return None, None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Pesquisa"

        context["query"] = self.request.GET.get("q")

        post_search, project_search = self.get_queryset()
        context["post_search"] = post_search
        context["project_search"] = project_search

        return context
