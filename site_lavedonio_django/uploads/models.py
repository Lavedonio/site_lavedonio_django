from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class UploadedImage(models.Model):
    """Image inserted in a blog post or project through the editors."""
    image = models.ImageField(upload_to='uploads/%Y/%m/', width_field='width', height_field='height', verbose_name=_('Image'))
    width = models.PositiveIntegerField(null=True, blank=True, editable=False, verbose_name=_('Width'))
    height = models.PositiveIntegerField(null=True, blank=True, editable=False, verbose_name=_('Height'))
    original_name = models.CharField(max_length=255, blank=True, verbose_name=_('Original Name'))
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_('Uploaded By'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))

    class Meta:
        verbose_name = _('Uploaded Image')
        verbose_name_plural = _('Uploaded Images')
        ordering = ['-created_at']

    def __str__(self):
        return self.original_name or self.image.name
