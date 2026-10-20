from django.urls import path
from django.utils.translation import gettext_lazy as _

from .views import ProjectCreateView, ProjectDeleteView, ProjectDetailView, ProjectListView, ProjectUpdateView


app_name = 'projects'

urlpatterns = [
    path('', ProjectListView.as_view(), name='list'),
    path(_('new/'), ProjectCreateView.as_view(), name='project-create'),
    path(_('edit/<int:pk>/'), ProjectUpdateView.as_view(), name='project-update'),
    path(_('delete/<int:pk>/'), ProjectDeleteView.as_view(), name='project-delete'),
    path('<slug:slug>/', ProjectDetailView.as_view(), name='project-detail'),
]
