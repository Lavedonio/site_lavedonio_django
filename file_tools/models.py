import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.core.files.uploadedfile import InMemoryUploadedFile

from PIL import Image
from io import BytesIO


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
    resize_image = models.BooleanField(default=True, verbose_name=_('Resize Image'))
    max_size = models.IntegerField(default=800, verbose_name=_('Maximum Size (px)'))
    description = models.CharField(max_length=128, blank=True, verbose_name=_('Description'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))

    class Meta:
        verbose_name = _("Image Upload")
        verbose_name_plural = _("Image Uploads")

    # This idea was adapted from:
    # https://stackoverflow.com/questions/1355150/when-saving-how-can-you-check-if-a-field-has-changed/13842223#13842223
    __previous_image_upload = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__previous_image_upload = self.image_upload

    def __str__(self):
        return str(self.id)

    def get_absolute_url(self):
        return reverse('image', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        # If image has changed and resizing is activated, compress it and save.
        if self.image_upload != self.__previous_image_upload and self.resize_image:
            with Image.open(BytesIO(self.image_upload.read())) as img:

                # Convert to RGB
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                # Resizing
                size = (self.max_size, self.max_size)
                img.thumbnail(size, Image.ANTIALIAS)

                # Reattributing resized file
                with BytesIO() as output:

                    # Outputing saved file
                    img.save(output, format='JPEG', quality=90)
                    output.seek(0)

                    # Replacing image instance
                    self.image_upload = InMemoryUploadedFile(
                        output, 'ImageField',
                        "%s.jpg" % self.image_upload.name.split('.')[0],
                        'image/jpeg',
                        output.getbuffer().nbytes, None
                    )

                    # Complete instance saving
                    super().save(*args, **kwargs)

        # If the image hasn't changed, save normally and update self.__previous_image_upload variable
        else:
            super().save(*args, **kwargs)
            self.__previous_image_upload = self.image_upload
