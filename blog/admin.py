from django.contrib import admin
from .models import Post, Tag


class PostAdmin(admin.ModelAdmin):
    '''
        Admin View for Post
    '''
    list_display = ('title', 'subtitle', 'slug', 'author', 'featured', 'published', 'date_posted', 'last_updated')
    list_filter = ('featured', 'published', 'author')
    search_fields = ('title',)

admin.site.register(Post, PostAdmin)

admin.site.register(Tag)
