import operator
import requests
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

        # Sets public key and, if not found, uses a test one publicly made available by Google
        # Docs: https://developers.google.com/recaptcha/docs/faq
        try:
            site_key = settings.RECAPTCHA_PUBLIC_KEY
        except AttributeError:
            site_key = "6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI"

        context["recaptcha_public_key"] = site_key
        return context

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)

        # captcha verification based on: https://medium.com/@mihfazhillah/how-to-implement-google-recaptcha-v3-on-your-django-app-3e4cc5b65013

        # Sets private key and, if not found, uses a test one publicly made available by Google
        # Docs: https://developers.google.com/recaptcha/docs/faq
        try:
            secret_key = settings.RECAPTCHA_PRIVATE_KEY
        except AttributeError:
            secret_key = "6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe"

        data = {
            'response': request.POST.get('g-recaptcha-response'),
            'secret': secret_key
        }
        resp = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data)
        result_json = resp.json()

        # Sets minimum score to pass validation
        try:
            threshold = settings.RECAPTCHA_REQUIRED_SCORE
        except AttributeError:
            threshold = 0.5

        if form.is_valid() and result_json.get("success") and result_json.get("score") >= threshold:
            return self.form_valid(form)
        else:
            return self.form_invalid(form, **kwargs)

    def form_valid(self, form):
        # Sending email
        name = form.cleaned_data.get('name')
        raw_subject = form.cleaned_data.get('subject')
        email = form.cleaned_data.get('email')
        raw_message = form.cleaned_data.get('message')

        subject = "[Via lavedonio.com.br] {0}".format(raw_subject)
        message = "Mensagem de {0};\nE-mail {1}:\n\n{2}".format(name, email, raw_message)

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
