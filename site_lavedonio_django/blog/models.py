import datetime

from django.conf import settings
from django.db import models
from django.db.models import Prefetch
from django.urls import reverse
from django.utils import timezone, translation
from django.utils.functional import cached_property
from django.utils.html import strip_tags
from django.utils.text import Truncator, slugify
from django.utils.translation import gettext_lazy as _

from base.markdown import render_markdown
from base.translations import TranslatableModel, Translation

WORDS_PER_MINUTE = 200


class Tag(TranslatableModel):
    slug = models.SlugField(max_length=64, unique=True, verbose_name=_('Slug'))
    color = models.CharField(max_length=7, default='#FFFFFF', verbose_name=_('Color'))
    background_color = models.CharField(max_length=7, default='#000599', verbose_name=_('Background Color'))

    class Meta:
        verbose_name = _('Tag')
        verbose_name_plural = _('Tags')
        ordering = ['slug']

    def get_absolute_url(self):
        return reverse('blog:tag', kwargs={'tag': self.slug})


class TagTranslation(Translation):
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name='translations', verbose_name=_('Tag'))
    name = models.CharField(max_length=64, verbose_name=_('Name'))

    class Meta:
        verbose_name = _('Tag Translation')
        verbose_name_plural = _('Tag Translations')
        constraints = [
            models.UniqueConstraint(fields=['tag', 'language'], name='unique_tag_language'),
        ]

    def __str__(self):
        return self.name


class PostQuerySet(models.QuerySet):

    def published(self):
        """Posts readers can see: published and whose date has arrived (posts can be scheduled)."""
        return self.filter(published=True, date_posted__lte=timezone.now())

    def visible_to(self, user):
        """Drafts and scheduled posts are also listed to who can edit them."""
        return self if user.has_perm('blog.change_post') else self.published()

    def in_language(self, language):
        return self.filter(pk__in=PostTranslation.objects.filter(language=language).values('post'))

    def with_related(self):
        return self.select_related('author').prefetch_related(
            'translations',
            Prefetch('tags', queryset=Tag.objects.prefetch_related('translations')),
        )


class Post(TranslatableModel):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='posts', verbose_name=_('Author'))
    tags = models.ManyToManyField(Tag, blank=True, related_name='posts', verbose_name=_('Tags'))
    cover_image = models.ImageField(upload_to='blog/covers/%Y/', blank=True, verbose_name=_('Cover Image'))
    featured = models.BooleanField(default=False, verbose_name=_('Featured'))
    published = models.BooleanField(default=False, verbose_name=_('Published'),
        help_text=_('Unpublished posts are only visible to you. Published posts with a future date are only shown from that date on.'))
    date_posted = models.DateTimeField(default=timezone.now, verbose_name=_('Date Posted'))
    last_updated = models.DateTimeField(auto_now=True, verbose_name=_('Last Updated'))

    objects = PostQuerySet.as_manager()

    class Meta:
        verbose_name = _('Post')
        verbose_name_plural = _('Posts')
        ordering = ['-date_posted']

    @property
    def is_scheduled(self):
        return self.published and self.date_posted > timezone.now()

    @property
    def was_updated(self):
        return self.last_updated - self.date_posted > datetime.timedelta(minutes=1)

    def get_absolute_url(self, language=None):
        """URL of the post in `language` (or in the active one), which may have a different slug."""
        language = language or translation.get_language()
        post_translation = self.get_translation(language)
        with translation.override(language):
            return reverse('blog:post-detail', kwargs={'pk': self.pk, 'slug': post_translation.slug})


class PostTranslation(Translation):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='translations', verbose_name=_('Post'))
    title = models.CharField(max_length=160, verbose_name=_('Title'))
    subtitle = models.CharField(max_length=300, blank=True, verbose_name=_('Subtitle'))
    slug = models.SlugField(max_length=180, blank=True, verbose_name=_('Slug'),
        help_text=_('Used in the address of the post. Leave it blank to generate it from the title.'))
    content = models.TextField(verbose_name=_('Content'), help_text=_('Written in Markdown.'))
    credits = models.TextField(blank=True, verbose_name=_('Credits'),
        help_text=_('Shown in the footer, e.g. who took the photos. HTML is allowed.'))

    class Meta:
        verbose_name = _('Post Translation')
        verbose_name_plural = _('Post Translations')
        constraints = [
            models.UniqueConstraint(fields=['post', 'language'], name='unique_post_language'),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)[:180].strip('-') or 'post'
        super().save(*args, **kwargs)

    @cached_property
    def content_html(self):
        return render_markdown(self.content)

    @cached_property
    def word_count(self):
        return len(strip_tags(self.content_html).split())

    @property
    def reading_time(self):
        """In minutes"""
        return max(1, round(self.word_count / WORDS_PER_MINUTE))

    @property
    def excerpt(self):
        return self.subtitle or Truncator(strip_tags(self.content_html)).words(40)
