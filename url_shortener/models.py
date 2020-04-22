import uuid
import short_url
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class URLShortener(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=32, verbose_name=_('Name'))
    slug = models.SlugField(max_length=128, unique=True, default=uuid.uuid4, verbose_name=_('Slug'))
    custom = models.BooleanField(verbose_name=_('Custom slug'))
    full_uri = models.CharField(max_length=1024, verbose_name=_('Full URI'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))

    class Meta:
        verbose_name = _("URL Shortener")
        verbose_name_plural = _("URL Shorteners")
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('shortened_url', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if not self.custom:
            self.slug = short_url.encode_url(self.id)
            super().save(*args, **kwargs)
