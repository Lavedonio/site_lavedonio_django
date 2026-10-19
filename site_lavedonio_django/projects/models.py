from django.db import models
from django.db.models import Prefetch
from django.urls import reverse
from django.utils import timezone, translation
from django.utils.translation import gettext_lazy as _

from base.translations import TranslatableModel, Translation


class Category(TranslatableModel):
    slug = models.SlugField(max_length=64, unique=True, verbose_name=_('Slug'))

    class Meta:
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')
        ordering = ['slug']


class CategoryTranslation(Translation):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='translations', verbose_name=_('Category'))
    name = models.CharField(max_length=64, verbose_name=_('Name'))

    class Meta:
        verbose_name = _('Category Translation')
        verbose_name_plural = _('Category Translations')
        constraints = [
            models.UniqueConstraint(fields=['category', 'language'], name='unique_category_language'),
        ]

    def __str__(self):
        return self.name


class ProjectQuerySet(models.QuerySet):

    def published(self):
        return self.filter(published=True, date_posted__lte=timezone.now())

    def visible_to(self, user):
        """Unpublished projects are also listed to who can edit them."""
        return self if user.has_perm('projects.change_project') else self.published()

    def with_related(self):
        return self.prefetch_related(
            'translations',
            Prefetch('categories', queryset=Category.objects.prefetch_related('translations')),
        )


class Project(TranslatableModel):

    class Status(models.TextChoices):
        IN_PROGRESS = 'in_progress', _('In progress')
        COMPLETED = 'completed', _('Completed')
        ARCHIVED = 'archived', _('Archived')

    slug = models.SlugField(max_length=64, unique=True, verbose_name=_('Slug'),
        help_text=_('Used in the address of the project, in every language. Leave it blank to generate it from the title.'))
    categories = models.ManyToManyField(Category, blank=True, related_name='projects', verbose_name=_('Categories'))
    cover_image = models.ImageField(upload_to='projects/covers/%Y/', blank=True, verbose_name=_('Cover Image'))
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.IN_PROGRESS, verbose_name=_('Status'))
    repository_url = models.URLField(blank=True, verbose_name=_('Source code URL'))
    live_url = models.URLField(blank=True, verbose_name=_('Live demo URL'))
    featured = models.BooleanField(default=False, verbose_name=_('Featured'))
    published = models.BooleanField(default=False, verbose_name=_('Published'),
        help_text=_('Unpublished projects are only visible to you.'))
    date_posted = models.DateTimeField(default=timezone.now, verbose_name=_('Date Posted'))
    last_updated = models.DateTimeField(auto_now=True, verbose_name=_('Last Updated'))

    # Options for interactive projects (games, demos, etc.)
    dark_background = models.BooleanField(default=False, verbose_name=_('Dark Background'),
        help_text=_('Keeps the content area dark, even when the site is in light mode.'))
    fix_autoscale = models.BooleanField(default=False, verbose_name=_('Fix Autoscale'),
        help_text=_("Stops Safari on iPhones from zooming in automatically on form inputs, while keeping the visitor's ability to zoom in manually."))
    custom_css = models.TextField(blank=True, verbose_name=_('Custom CSS'),
        help_text=_('Added to the page inside a <style> tag.'))
    custom_js = models.TextField(blank=True, verbose_name=_('Custom JavaScript'),
        help_text=_('Added to the end of the page inside a <script> tag.'))

    objects = ProjectQuerySet.as_manager()

    class Meta:
        verbose_name = _('Project')
        verbose_name_plural = _('Projects')
        ordering = ['-date_posted']

    def get_absolute_url(self, language=None):
        with translation.override(language or translation.get_language()):
            return reverse('projects:project-detail', kwargs={'slug': self.slug})


class ProjectTranslation(Translation):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='translations', verbose_name=_('Project'))
    title = models.CharField(max_length=100, verbose_name=_('Title'))
    summary = models.CharField(max_length=300, verbose_name=_('Summary'),
        help_text=_('Shown in the project cards and below the title.'))
    content = models.TextField(blank=True, verbose_name=_('Content'))
    credits = models.TextField(blank=True, verbose_name=_('Credits'),
        help_text=_('Shown in the footer, e.g. who took the photos. HTML is allowed.'))

    class Meta:
        verbose_name = _('Project Translation')
        verbose_name_plural = _('Project Translations')
        constraints = [
            models.UniqueConstraint(fields=['project', 'language'], name='unique_project_language'),
        ]

    def __str__(self):
        return self.title
