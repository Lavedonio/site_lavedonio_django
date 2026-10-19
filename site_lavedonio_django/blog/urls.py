from django.urls import path
from django.utils.translation import gettext_lazy as _

from .views import PostCreateView, PostDeleteView, PostDetailView, PostListView, PostRedirectView, PostUpdateView


app_name = 'blog'

urlpatterns = [
    path('', PostListView.as_view(), name='list'),
    path('tag/<slug:tag>/', PostListView.as_view(), name='tag'),
    path(_('archive/<int:year>/<int:month>/'), PostListView.as_view(), name='archive'),
    path(_('new/'), PostCreateView.as_view(), name='post-create'),
    path(_('edit/<int:pk>/'), PostUpdateView.as_view(), name='post-update'),
    path(_('delete/<int:pk>/'), PostDeleteView.as_view(), name='post-delete'),
    path('<int:pk>/', PostRedirectView.as_view(), name='post-short'),
    path('<int:pk>/<slug:slug>/', PostDetailView.as_view(), name='post-detail'),
]
