from django.contrib import admin

from .models import Category, CategoryTranslation, Project, ProjectTranslation


class CategoryTranslationInline(admin.TabularInline):
    model = CategoryTranslation
    extra = 1
    min_num = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'slug')
    search_fields = ('slug', 'translations__name')
    inlines = [CategoryTranslationInline]


class ProjectTranslationInline(admin.StackedInline):
    model = ProjectTranslation
    extra = 0
    min_num = 1


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'slug', 'available_languages', 'status', 'featured', 'published', 'date_posted', 'last_updated')
    list_filter = ('status', 'featured', 'published', 'translations__language', 'categories')
    search_fields = ('slug', 'translations__title', 'translations__summary')
    filter_horizontal = ('categories',)
    inlines = [ProjectTranslationInline]

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('translations')
