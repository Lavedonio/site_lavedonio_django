import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.urls import reverse


class FileUpload(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=128, verbose_name=_('Name'))
    slug = models.SlugField(max_length=128, unique=True, default=uuid.uuid4, verbose_name=_('Slug'))
    file_upload = models.FileField(upload_to="files/", verbose_name=_('File Upload'))
    description = models.CharField(max_length=128, blank=True, verbose_name=_('Description'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))

    class Meta:
        verbose_name = _("File Upload")
        verbose_name_plural = _("File Uploads")

    def __str__(self):
        return str(self.id)

    def get_absolute_url(self):
        return reverse('file', kwargs={'slug': self.slug})


class ImageUpload(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=128, verbose_name=_('Name'))
    slug = models.SlugField(max_length=128, unique=True, default=uuid.uuid4, verbose_name=_('Slug'))
    image_upload = models.ImageField(upload_to="images/", verbose_name=_('Image Upload'))
    description = models.CharField(max_length=128, blank=True, verbose_name=_('Description'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))

    class Meta:
        verbose_name = _("Image Upload")
        verbose_name_plural = _("Image Uploads")

    def __str__(self):
        return str(self.id)

    def get_absolute_url(self):
        return reverse('image', kwargs={'slug': self.slug})
