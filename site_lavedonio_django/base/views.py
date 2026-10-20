import logging
from smtplib import SMTPException

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.mail import EmailMessage
from django.http import HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.text import slugify
from django.utils.translation import gettext as _, gettext_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, TemplateView, UpdateView
from django.views.generic.edit import FormView
from django.urls import reverse_lazy
from blog.models import Post
from projects.models import Project
from .editing import TranslatableEditMixin
from .forms import ABOUT_ORDER_STEP, AboutSectionForm, AboutSectionTranslationForm, ContactForm
from .i18n import normalize_host
from .models import AboutSection
from .turnstile import verify_turnstile

logger = logging.getLogger(__name__)

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

        # Sections only written in another language are shown in that language
        sections = AboutSection.objects.prefetch_related("translations")
        context["sections"] = [(section, section.translation) for section in sections if section.translation]

        return context


class AboutSectionEditMixin(PermissionRequiredMixin, TranslatableEditMixin):
    model = AboutSection
    form_class = AboutSectionForm
    translation_form_class = AboutSectionTranslationForm
    translation_parent_field = "section"
    success_message = gettext_lazy("Section saved.")
    template_name = "about/section_form.html"

    def get_queryset(self):
        return AboutSection.objects.prefetch_related("translations")

    def get_success_url(self):
        return self.object.get_absolute_url()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["navbar_active"] = "about"
        return context

    def prepare_object(self, form, translation_forms):
        if form.instance.slug:
            return

        # Unique slug based on the title of the first included language
        title = next(item.cleaned_data["title"] for item in translation_forms if item.is_enabled)
        base_slug = slugify(title)[:56].strip("-") or "section"
        slug, number = base_slug, 2
        while AboutSection.objects.filter(slug=slug).exclude(pk=form.instance.pk).exists():
            slug, number = f"{base_slug}-{number}", number + 1
        form.instance.slug = slug


class AboutSectionCreateView(AboutSectionEditMixin, CreateView):
    permission_required = "base.add_aboutsection"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("New section - About")
        return context


class AboutSectionUpdateView(AboutSectionEditMixin, UpdateView):
    permission_required = "base.change_aboutsection"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Edit section - About")
        return context


class AboutSectionMoveView(PermissionRequiredMixin, View):
    """Moves a section one position up or down (the `direction` sent by the buttons of the About page)."""
    permission_required = "base.change_aboutsection"
    offsets = {"up": -1, "down": 1}

    def post(self, request, *args, **kwargs):
        section = get_object_or_404(AboutSection, pk=kwargs["pk"])
        offset = self.offsets.get(request.POST.get("direction"))
        if offset is None:
            return HttpResponseBadRequest()

        sections = list(AboutSection.objects.all())
        index = sections.index(section)
        if 0 <= index + offset < len(sections):
            sections.insert(index + offset, sections.pop(index))
            # Renumbers all of them, which also untangles sections with the same order
            for position, item in enumerate(sections, start=1):
                item.order = position * ABOUT_ORDER_STEP
            AboutSection.objects.bulk_update(sections, ["order"])

        return HttpResponseRedirect(section.get_absolute_url())


class AboutSectionDeleteView(PermissionRequiredMixin, DeleteView):
    model = AboutSection
    permission_required = "base.delete_aboutsection"
    template_name = "about/section_confirm_delete.html"
    success_url = reverse_lazy("base:about")

    def get_queryset(self):
        return AboutSection.objects.prefetch_related("translations")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Delete section - About")
        context["navbar_active"] = "about"
        return context

    def form_valid(self, form):
        messages.success(self.request, _("Section deleted."))
        return super().form_valid(form)


class ContactView(FormView):
    template_name = "contact.html"
    form_class = ContactForm
    success_url = reverse_lazy("base:contact-success")
    turnstile_action = "contact"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Contact")
        context["navbar_active"] = "contact"
        context["turnstile_site_key"] = settings.TURNSTILE_SITE_KEY
        context["turnstile_action"] = self.turnstile_action
        return context

    def form_valid(self, form):
        if not verify_turnstile(self.request, self.turnstile_action):
            form.add_error(None, _("Couldn't verify that you're not a robot. Please try again."))
            return self.form_invalid(form)

        try:
            self.build_email(form).send()
        except (SMTPException, OSError):
            logger.exception("Couldn't send the contact form e-mail")
            form.add_error(None, _("Your message couldn't be sent right now. Please try again later or reach me through social media."))
            return self.form_invalid(form)

        return super().form_valid(form)

    def build_email(self, form):
        name = form.cleaned_data["name"]
        email = form.cleaned_data["email"]
        # The domain tells which language version of the site the message came from
        domain = normalize_host(self.request.get_host())

        return EmailMessage(
            subject=f"[Via {domain}] {form.cleaned_data['subject']}",
            body=f"Message from {name} <{email}>:\n\n{form.cleaned_data['message']}",
            to=[settings.CONTACT_EMAIL],
            # Replies go to the visitor, but no copy is sent to them, so the
            # form can't be used to send e-mails to arbitrary addresses
            reply_to=[email],
        )


class ContactSuccessView(TemplateView):
    template_name = "contact_success.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Message sent - Contact")
        context["navbar_active"] = "contact"
        return context


class TempAdminView(TemplateView):
    template_name = "base_admin.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Project"
        context["navbar_active"] = "projects"
        # context["analytics_id"] = settings.ANALYTICS_ID

        return context
