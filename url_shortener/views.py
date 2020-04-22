from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView
from django.views import View
from .models import URLShortener


class URLShortenerListView(LoginRequiredMixin, ListView):
    model = URLShortener
    ordering = ["-id"]

    def get_context_data(self):
        context = super().get_context_data()
        context["title"] = "Imagens"
        context["navbar_active"] = "urls"

        return context


class URLShortenerRedirectView(View):

    def get(self, request, slug):
        url = get_object_or_404(URLShortener, slug=slug)
        return redirect(url.full_uri)
