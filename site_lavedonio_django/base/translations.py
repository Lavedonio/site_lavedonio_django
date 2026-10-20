"""
Base classes for content available in multiple languages.

The language independent fields live in a `TranslatableModel` (e.g. Post) and
the texts in a `Translation` model with one row per language (e.g. PostTranslation),
linked by a foreign key with related_name='translations'. A post can therefore
exist only in English, only in Portuguese or in both, always under the same ID,
and new languages can be added without changing the database schema.
"""
from django.db import models
from django.utils import translation
from django.utils.translation import gettext_lazy as _

from .i18n import get_fallback_languages, get_language_choices, get_language_codes, get_language_display_name, get_language_short_name


class TranslatableModel(models.Model):

    class Meta:
        abstract = True

    def get_translations(self):
        """{language_code: translation}. Uses prefetch_related('translations') when available."""
        if '_translations_by_language' not in self.__dict__:
            self._translations_by_language = {item.language: item for item in self.translations.all()}
        return self._translations_by_language

    def clear_translations_cache(self):
        self.__dict__.pop('_translations_by_language', None)
        if hasattr(self, '_prefetched_objects_cache'):
            self._prefetched_objects_cache.pop('translations', None)

    def get_translation(self, language=None, fallback=True):
        translations = self.get_translations()
        language = language or translation.get_language()
        languages = get_fallback_languages(language) if fallback else [language]

        for code in languages:
            if code in translations:
                return translations[code]
        return None

    @property
    def translation(self):
        """Translation in the active language or, if it doesn't exist, in another one."""
        return self.get_translation()

    @property
    def available_languages(self):
        translations = self.get_translations()
        return [code for code in get_language_codes() if code in translations]

    def __str__(self):
        current = self.translation
        return str(current) if current else f'{self._meta.verbose_name} #{self.pk}'


class Translation(models.Model):
    language = models.CharField(max_length=15, choices=get_language_choices, db_index=True, verbose_name=_('Language'))

    class Meta:
        abstract = True

    @property
    def language_name(self):
        return get_language_display_name(self.language)

    @property
    def language_short_name(self):
        return get_language_short_name(self.language)

    @property
    def is_fallback(self):
        """True when shown in a site whose language is different from this translation's."""
        return self.language != translation.get_language()
