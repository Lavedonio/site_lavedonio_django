"""projects URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
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
from django.urls import path
from django.conf import settings
from .views import ProjectListView, ProjectDetailView, ProjectTestView

urlpatterns = [
    path('', ProjectListView.as_view(), name="projects"),
    path('<slug:slug>/', ProjectDetailView.as_view(), name="project"),
]

if settings.ENVIRONMENT != "production":
    # Slug url must be the last item of the list because Django isn't able to access the items after it
    # So that's why the slug path is removed from the list and then added again.
    slug = urlpatterns.pop()
    urlpatterns += [path('testing/', ProjectTestView.as_view(), name="project-testing"), slug]
