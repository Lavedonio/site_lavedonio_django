# from django.conf import settings
from django.utils.translation import get_language, gettext as _
from django.views.generic import TemplateView
from django.views.generic.edit import FormView
from django.urls import reverse_lazy
from blog.models import Post
from projects.models import Project
from .forms import ContactForm

# How many featured projects and posts are shown in the homepage
HOME_FEATURED_COUNT = 3


class HomeView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Homepage")
        context["navbar_active"] = "home"
        # context["analytics_id"] = settings.ANALYTICS_ID

        # Each section is only shown when it has featured content
        user = self.request.user
        context["projects"] = list(Project.objects.visible_to(user).filter(featured=True).with_related()[:HOME_FEATURED_COUNT])
        context["posts"] = list(Post.objects.visible_to(user).filter(featured=True).with_related()[:HOME_FEATURED_COUNT])
        return context


class AboutView(TemplateView):
    template_name = "about.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("About")
        context["navbar_active"] = "about"
        # context["analytics_id"] = settings.ANALYTICS_ID

        # Long texts are kept in one template per language instead of the .po files
        context["content_templates"] = [f"about/content_{get_language()}.html", "about/content_en.html"]

        return context


class ContactView(FormView):
    template_name = "contact.html"
    form_class = ContactForm
    success_url = reverse_lazy("contact-success")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Contact")
        context["navbar_active"] = "contact"
        # context["analytics_id"] = settings.ANALYTICS_ID

        return context

        # Sets public key and, if not found, uses a test one publicly made available by Google
        # Docs: https://developers.google.com/recaptcha/docs/faq
        try:
            site_key = settings.RECAPTCHA_PUBLIC_KEY
        except AttributeError:
            site_key = "6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI"

        context["recaptcha_public_key"] = site_key
        return context

    def post(self, request, *args, **kwargs):
        print("Teste")
        form_class = self.get_form_class()
        form = self.get_form(form_class)

        # captcha verification based on: https://medium.com/@mihfazhillah/how-to-implement-google-recaptcha-v3-on-your-django-app-3e4cc5b65013

        # Sets private key and, if not found, uses a test one publicly made available by Google
        # Docs: https://developers.google.com/recaptcha/docs/faq
        # try:
        #     secret_key = settings.RECAPTCHA_PRIVATE_KEY
        # except AttributeError:
        #     secret_key = "6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe"

        # data = {
        #     'response': request.POST.get('g-recaptcha-response'),
        #     'secret': secret_key
        # }
        # resp = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data)
        # result_json = resp.json()

        # # Sets minimum score to pass validation
        # try:
        #     threshold = settings.RECAPTCHA_REQUIRED_SCORE
        # except AttributeError:
        #     threshold = 0.5
        print("Teste")

        # if form.is_valid() and result_json.get("success") and result_json.get("score") >= threshold:
        if form.is_valid():
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

        # from_email = settings.EMAIL_HOST_USER
        # send_mail(subject, message, from_email, [settings.EMAIL_HOST_USER, email], fail_silently=False)

        return super().form_valid(form)


class ContactSuccessView(TemplateView):
    template_name = "contact_success.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Contact - Form Submitted Successfully")
        context["navbar_active"] = "contact"
        # context["analytics_id"] = settings.ANALYTICS_ID
        return context


class TempAdminView(TemplateView):
    template_name = "base_admin.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Project"
        context["navbar_active"] = "projects"
        # context["analytics_id"] = settings.ANALYTICS_ID

        return context
