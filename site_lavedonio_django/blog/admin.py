from django.contrib import admin

from .models import Post, PostTranslation, Tag, TagTranslation


class TagTranslationInline(admin.TabularInline):
    model = TagTranslation
    extra = 1
    min_num = 1


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'slug', 'color', 'background_color')
    search_fields = ('slug', 'translations__name')
    inlines = [TagTranslationInline]


class PostTranslationInline(admin.StackedInline):
    model = PostTranslation
    extra = 0
    min_num = 1
    prepopulated_fields = {'slug': ('title',)}


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'available_languages', 'author', 'featured', 'published', 'date_posted', 'last_updated')
    list_filter = ('featured', 'published', 'translations__language', 'tags')
    search_fields = ('translations__title', 'translations__subtitle')
    date_hierarchy = 'date_posted'
    filter_horizontal = ('tags',)
    inlines = [PostTranslationInline]

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('translations')
