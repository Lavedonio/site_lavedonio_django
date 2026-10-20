"""
URL configuration for site_lavedonio_django project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.utils.translation import gettext_lazy as _

from users.views import AdminLoginView


# Paths wrapped in _() are translated to the language of the host, e.g.
# lavedonio.com/projects/ and lavedonio.com.br/projetos/
urlpatterns = [
    path('admin/login/', AdminLoginView.as_view()),
    path('admin/', admin.site.urls),
    path('accounts/', include('users.urls', namespace='users')),
    path('uploads/', include('uploads.urls', namespace='uploads')),
    path(_('blog/'), include('blog.urls', namespace='blog')),
    path(_('projects/'), include('projects.urls', namespace='projects')),
    path('', include('base.urls', namespace='base')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
