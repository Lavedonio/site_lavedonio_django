from django.contrib import admin
from .models import FileUpload, ImageUpload


class FileUploadAdmin(admin.ModelAdmin):
    '''
        Admin View for FileUpload
    '''
    list_display = ('id', 'name', 'slug', 'description', 'created_at', 'updated_at')
    list_display_links = ('id', 'name')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('name', 'slug')

admin.site.register(FileUpload, FileUploadAdmin)


class ImageUploadAdmin(admin.ModelAdmin):
    '''
        Admin View for ImageUploadAdmin
    '''
    list_display = ('id', 'name', 'slug', 'description', 'resize_image', 'max_size', 'created_at', 'updated_at')
    list_display_links = ('id', 'name')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('name', 'slug')

admin.site.register(ImageUpload, ImageUploadAdmin)
