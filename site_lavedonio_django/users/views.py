from django.conf import settings
from django.contrib import admin
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.views import LoginView as BaseLoginView, LogoutView as BaseLogoutView
from django.core import signing
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.crypto import constant_time_compare
from django.utils.translation import gettext as _
from django.views import View

from .forms import LoginForm
from .sync import LOGIN, LOGOUT, get_sync_url, read_token


class LoginView(BaseLoginView):
    template_name = 'users/login.html'
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Log in")
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        # Also logs in on the hosts of the other languages before going to the next page
        next_url = self.request.build_absolute_uri(response.url)
        return HttpResponseRedirect(get_sync_url(self.request, LOGIN, form.get_user(), next_url))


class LogoutView(BaseLogoutView):

    def post(self, request, *args, **kwargs):
        user = request.user if request.user.is_authenticated else None
        response = super().post(request, *args, **kwargs)
        # Also logs out on the hosts of the other languages
        next_url = request.build_absolute_uri(response.url)
        return HttpResponseRedirect(get_sync_url(request, LOGOUT, user, next_url))


class AdminLoginView(View):
    """
    Replaces the admin's login page with the site's one, which also logs in on
    the hosts of the other languages. Users already logged in without access to
    the admin get the admin's page, which explains it (the site's login would
    send them back to the admin, in a loop).
    """

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return admin.site.login(request)

        url = reverse('users:login')
        query_string = request.META.get('QUERY_STRING')
        return HttpResponseRedirect(f'{url}?{query_string}' if query_string else url)


class SyncSessionView(View):
    """One step of the login/logout across the hosts of every language (see users.sync)."""

    def get(self, request, *args, **kwargs):
        try:
            data = read_token(request.GET.get('token', ''))
        except signing.BadSignature:
            raise PermissionDenied

        user = get_user_model()._default_manager.filter(pk=data['user'], is_active=True).first()
        if user is None or not constant_time_compare(user.get_session_auth_hash(), data['hash']):
            raise PermissionDenied

        if data['action'] == LOGIN:
            if request.user != user:
                login(request, user, backend=settings.AUTHENTICATION_BACKENDS[0])
        elif request.user == user:
            logout(request)

        return HttpResponseRedirect(get_sync_url(request, data['action'], user, data['next'], data['languages'][1:]))
