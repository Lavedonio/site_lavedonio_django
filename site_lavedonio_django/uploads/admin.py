from django.contrib import admin
from django.utils.html import format_html

from .models import UploadedImage


@admin.register(UploadedImage)
class UploadedImageAdmin(admin.ModelAdmin):
    list_display = ('thumbnail', 'original_name', 'width', 'height', 'uploaded_by', 'created_at')
    readonly_fields = ('thumbnail', 'width', 'height', 'uploaded_by', 'created_at')
    search_fields = ('original_name',)

    @admin.display(description='')
    def thumbnail(self, obj):
        return format_html('<img src="{}" alt="" style="max-height: 80px;">', obj.image.url) if obj.image else ''
