"""
Forms and view helpers for the editors of translatable content (blog posts and
projects), where each language is edited in its own tab and can be included or
left out independently.
"""
from django import forms
from django.contrib import messages
from django.db import transaction
from django.forms.utils import ErrorDict
from django.http import HttpResponseRedirect
from django.utils import timezone
from django.utils.translation import get_language, gettext as _, gettext_lazy

from .i18n import get_language_codes, get_language_display_name, get_language_short_name


class PublicationDateMixin:
    """
    For ModelForms with a `date_posted` field: it starts empty in new objects
    (instead of the time the editor was opened) and, when left empty, the
    object gets the date and time it was saved.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['date_posted'].required = False
        self.fields['date_posted'].help_text = _('Leave it empty to use the moment it is saved.')
        if self.instance.pk is None:
            self.initial['date_posted'] = None

    def clean_date_posted(self):
        return self.cleaned_data.get('date_posted') or timezone.now()


class TranslationForm(forms.ModelForm):
    """Form for the texts of one language. Its fields are only validated when the language is included."""

    # The rich text editors hide their textareas, so the browser can't focus
    # them to complain about required fields. Validation happens server side.
    use_required_attribute = False

    enabled = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch', 'data-translation-toggle': ''}),
    )

    def __init__(self, *args, language, enabled_by_default=False, **kwargs):
        self.language = language
        super().__init__(*args, **kwargs)

        self.fields['enabled'].label = _('Include the %(language)s version') % {'language': self.language_name}
        self.fields['enabled'].initial = self.instance.pk is not None or enabled_by_default

    @property
    def language_name(self):
        return get_language_display_name(self.language)

    @property
    def language_short_name(self):
        return get_language_short_name(self.language)

    @property
    def is_enabled(self):
        if self.is_bound:
            return bool(self['enabled'].data)
        return bool(self['enabled'].initial)

    def full_clean(self):
        if self.is_bound and not self.is_enabled:
            self._errors = ErrorDict()
            self.cleaned_data = {}
            return
        super().full_clean()


class TranslatableEditMixin:
    """
    For CreateView/UpdateView of a TranslatableModel. Adds one
    `translation_form_class` form per language to the page, as
    `translation_forms`, and saves them together with the main form.
    """
    translation_form_class = None
    # Name of the foreign key from the translation model to the edited model
    translation_parent_field = None
    success_message = gettext_lazy('Changes saved.')

    def get_translation_forms(self):
        existing = self.object.get_translations() if getattr(self, 'object', None) else {}
        is_post = self.request.method == 'POST'

        return [
            self.translation_form_class(
                data=self.request.POST if is_post else None,
                files=self.request.FILES if is_post else None,
                instance=existing.get(code),
                prefix=f'translation_{code}',
                language=code,
                # New content starts with the language of the site where it's being written
                enabled_by_default=not existing and code == get_language(),
            )
            for code in get_language_codes()
        ]

    def get_context_data(self, **kwargs):
        if 'translation_forms' not in kwargs:
            kwargs['translation_forms'] = self.get_translation_forms()
        return super().get_context_data(**kwargs)

    def validate_translation_forms(self, form, translation_forms):
        # Validates all of them (no short-circuit), so every tab shows its errors
        are_valid = all([translation_form.is_valid() for translation_form in translation_forms])

        if not any(translation_form.is_enabled for translation_form in translation_forms):
            form.add_error(None, _('Include at least one language.'))
            return False

        return are_valid

    def prepare_object(self, form, translation_forms):
        """Hook to set fields of the edited object that depend on the translations before saving it."""

    def form_valid(self, form):
        translation_forms = self.get_translation_forms()
        if not self.validate_translation_forms(form, translation_forms):
            return self.render_to_response(self.get_context_data(form=form, translation_forms=translation_forms))

        with transaction.atomic():
            self.prepare_object(form, translation_forms)
            self.object = form.save()
            self.save_translations(translation_forms)

        messages.success(self.request, self.success_message)
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        translation_forms = self.get_translation_forms()
        self.validate_translation_forms(form, translation_forms)
        return self.render_to_response(self.get_context_data(form=form, translation_forms=translation_forms))

    def save_translations(self, translation_forms):
        for translation_form in translation_forms:
            if translation_form.is_enabled:
                item = translation_form.save(commit=False)
                setattr(item, self.translation_parent_field, self.object)
                item.language = translation_form.language
                item.save()
            elif translation_form.instance.pk:
                translation_form.instance.delete()

        self.object.clear_translations_cache()
