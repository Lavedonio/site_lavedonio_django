from django.db import models
from django.utils.translation import gettext_lazy as _
from django.urls import reverse


class Category(models.Model):
    name = models.CharField(max_length=32, verbose_name=_('Name'))
    abbreviation = models.CharField(max_length=32, verbose_name=_('Abbreviation'))

    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")
        ordering = ["name"]

    def __str__(self):
        return self.name


class Project(models.Model):
    title = models.CharField(max_length=64, verbose_name=_('Title'))
    slug = models.SlugField(max_length=32, unique=True, verbose_name=_('Slug'))
    featured = models.BooleanField(default=False, verbose_name=_('Featured'))
    dark_background = models.BooleanField(default=False, verbose_name=_('Dark Background'))
    published = models.BooleanField(default=True, verbose_name=_('Published'))
    categories = models.ManyToManyField(Category, blank=True, verbose_name=_('Categories'))
    main_image = models.ImageField(default='default_project_img.jpg', upload_to='projects', verbose_name=_('Main Image'))
    description = models.CharField(max_length=128, verbose_name=_('Description'))
    content = models.TextField(verbose_name=_('Content'))
    custom_css = models.BooleanField(default=False, verbose_name=_('Custom CSS'))
    custom_js = models.BooleanField(default=False, verbose_name=_('Custom JavaScript'))

    @property
    def css(self):
        return f"css/{self.slug}.css"

    @property
    def js(self):
        return f"js/{self.slug}.js"

    class Meta:
        verbose_name = _('Project')
        verbose_name_plural = _('Projects')

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('project', kwargs={'slug': self.slug})
