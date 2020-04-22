from django.contrib import admin
from .models import URLShortener


class URLShortenerAdmin(admin.ModelAdmin):
    '''
        Admin View for URLShortener
    '''
    list_display = ('id', 'name', 'slug', 'custom', 'full_uri', 'created_at', 'updated_at')
    list_display_links = ('id', 'name')
    list_filter = ('custom', 'created_at', 'updated_at')
    search_fields = ('name', 'slug', 'full_uri')

admin.site.register(URLShortener, URLShortenerAdmin)
