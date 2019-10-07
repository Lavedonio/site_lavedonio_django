from django.views.generic import TemplateView


class HomepageView(TemplateView):
    template_name = "home.html"

    def get_context_data(self):
        context = super().get_context_data()
        context["title"] = "Homepage"
        context["navbar_active"] = "home"
        return context


class AboutView(TemplateView):
    template_name = "about.html"

    def get_context_data(self):
        context = super().get_context_data()
        context["title"] = "Sobre"
        context["navbar_active"] = "about"
        return context


class ContactView(TemplateView):
    template_name = "contact.html"

    def get_context_data(self):
        context = super().get_context_data()
        context["title"] = "Contato"
        context["navbar_active"] = "contact"
        return context
