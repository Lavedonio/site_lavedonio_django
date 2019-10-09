from django.contrib import admin
from .models import Project


class ProjectAdmin(admin.ModelAdmin):
    '''
        Admin View for Project
    '''
    list_display = ('title', 'slug', 'featured', 'description', 'dark_background', 'highest_score', 'downloads')
    list_filter = ('featured', 'dark_background')
    search_fields = ('title', 'slug')

admin.site.register(Project, ProjectAdmin)
