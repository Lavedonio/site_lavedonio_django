"""file_tools URL Configuration

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
from .views import FileUploadListView, ImageUploadListView, ImageUploadDetailView

urlpatterns = [
    path('', FileUploadListView.as_view(), name="files"),
    path('imagens/', ImageUploadListView.as_view(), name="images"),
    path('imagens/<slug:slug>/', ImageUploadDetailView.as_view(), name="image"),
]
