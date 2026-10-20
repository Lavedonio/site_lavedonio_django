from django.db import models
from django.urls import reverse
from django.utils import translation
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from .markdown import render_markdown
from .translations import TranslatableModel, Translation


class AboutSection(TranslatableModel):
    """One of the sections of the About page (e.g. Education), each with a text and a picture."""
    order = models.PositiveSmallIntegerField(default=0, verbose_name=_('Order'),
        help_text=_('Sections are shown from the lowest to the highest number.'))
    slug = models.SlugField(max_length=64, unique=True, verbose_name=_('Slug'),
        help_text=_('Used in links to the section (e.g. /about/#education).'))
    image = models.ImageField(upload_to='about/', width_field='image_width', height_field='image_height', verbose_name=_('Picture'))
    # Rendered as the size of the <img>, so the page doesn't jump while the pictures load
    image_width = models.PositiveIntegerField(null=True, blank=True, editable=False)
    image_height = models.PositiveIntegerField(null=True, blank=True, editable=False)

    class Meta:
        verbose_name = _('About Section')
        verbose_name_plural = _('About Sections')
        ordering = ['order', 'pk']

    def get_absolute_url(self, language=None):
        with translation.override(language or translation.get_language()):
            return f"{reverse('base:about')}#{self.slug}"


class AboutSectionTranslation(Translation):
    section = models.ForeignKey(AboutSection, on_delete=models.CASCADE, related_name='translations', verbose_name=_('Section'))
    title = models.CharField(max_length=100, verbose_name=_('Title'))
    content = models.TextField(verbose_name=_('Text'), help_text=_('Written in Markdown.'))
    image_caption = models.CharField(max_length=200, blank=True, verbose_name=_('Picture description'),
        help_text=_('Shown under the picture.'))

    class Meta:
        verbose_name = _('About Section Translation')
        verbose_name_plural = _('About Section Translations')
        constraints = [
            models.UniqueConstraint(fields=['section', 'language'], name='unique_about_section_language'),
        ]

    def __str__(self):
        return self.title

    @cached_property
    def content_html(self):
        return render_markdown(self.content)
