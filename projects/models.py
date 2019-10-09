from django.db import models
from django.utils.translation import gettext_lazy as _


class Project(models.Model):
    title = models.CharField(max_length=64, verbose_name=_('Title'))
    slug = models.SlugField(max_length=32, unique=True, verbose_name=_('Slug'))
    featured = models.BooleanField(default=False, verbose_name=_('Featured'))
    description = models.CharField(max_length=128, verbose_name=_('Description'))
    dark_background = models.BooleanField(default=False, verbose_name=_('Dark Background'))
    highest_score = models.IntegerField(default=0, verbose_name=_('Highest Score'))
    downloads = models.IntegerField(default=0, verbose_name=_('Downloads'))

    class Meta:
        verbose_name = _('Project')
        verbose_name_plural = _('Projects')

    def __str__(self):
        return self.title
