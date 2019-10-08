"""blog URL Configuration

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
from .views import PostListView, PostDetailView, PostCreateView, PostUpdateView, PostDeleteView, PostFilterListView

urlpatterns = [
    path('', PostListView.as_view(), name="blog"),
    path('post/<int:pk>/', PostDetailView.as_view(), name="post"),
    path('post/novo/', PostCreateView.as_view(), name="post-create"),
    path('post/<int:pk>/editar/', PostUpdateView.as_view(), name="post-update"),
    path('post/<int:pk>/deletar/', PostDeleteView.as_view(), name="post-delete"),
    path('arquivo/<str:year_month>/', PostFilterListView.as_view(), name="archive"),
]
