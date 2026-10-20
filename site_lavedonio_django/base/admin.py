from django.contrib import admin

from .models import AboutSection, AboutSectionTranslation


class AboutSectionTranslationInline(admin.StackedInline):
    model = AboutSectionTranslation
    extra = 0
    min_num = 1


@admin.register(AboutSection)
class AboutSectionAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'order', 'slug', 'available_languages')
    list_editable = ('order',)
    search_fields = ('slug', 'translations__title')
    inlines = [AboutSectionTranslationInline]

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('translations')
