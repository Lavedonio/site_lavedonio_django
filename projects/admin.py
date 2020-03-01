from django.contrib import admin
from .models import Category, Project


class CategoryAdmin(admin.ModelAdmin):
    '''
        Admin View for Project
    '''
    list_display = ('name', 'abbreviation')
    search_fields = ('name', 'abbreviation')

admin.site.register(Category, CategoryAdmin)


class ProjectAdmin(admin.ModelAdmin):
    '''
        Admin View for Project
    '''
    list_display = ('title', 'slug', 'featured', 'dark_background', 'description')
    list_filter = ('featured', 'dark_background')
    search_fields = ('title', 'slug')

admin.site.register(Project, ProjectAdmin)
