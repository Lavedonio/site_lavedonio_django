from django.contrib import admin
from .models import Post


class PostAdmin(admin.ModelAdmin):
    '''
        Admin View for Post
    '''
    list_display = ('title', 'subtitle', 'author', 'draft', 'date_posted', 'last_updated')
    list_filter = ('draft', 'author')
    search_fields = ('title',)

admin.site.register(Post, PostAdmin)
