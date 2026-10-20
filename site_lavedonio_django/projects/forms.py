from django import forms
from django.core.files.uploadedfile import UploadedFile
from django.utils.translation import gettext_lazy as _

from base.editing import PublicationDateMixin, TranslationForm
from base.images import optimize_image
from .models import Category, Project, ProjectTranslation

COVER_IMAGE_MAX_SIZE = 2400

# Paths of the projects URLs (in every language) that can't be used as slugs
RESERVED_SLUGS = {'new', 'novo', 'edit', 'editar', 'delete', 'excluir'}

SWITCH = forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch'})


class ProjectForm(PublicationDateMixin, forms.ModelForm):

    class Meta:
        model = Project
        fields = [
            'published', 'featured', 'date_posted',
            'status', 'categories', 'repository_url', 'live_url', 'slug',
            'cover_image',
            'dark_background', 'fix_autoscale', 'custom_css', 'custom_js',
        ]
        widgets = {
            'published': SWITCH,
            'featured': SWITCH,
            'dark_background': SWITCH,
            'fix_autoscale': SWITCH,
            'date_posted': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}, format='%Y-%m-%dT%H:%M'),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'categories': forms.CheckboxSelectMultiple(attrs={'class': 'btn-check'}),
            'repository_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://github.com/...'}),
            'live_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://'}),
            'slug': forms.TextInput(attrs={'class': 'form-control', 'autocapitalize': 'none'}),
            'cover_image': forms.ClearableFileInput(attrs={'accept': 'image/*'}),
            'custom_css': forms.Textarea(attrs={'class': 'form-control code-input', 'rows': 8, 'spellcheck': 'false', 'autocapitalize': 'none'}),
            'custom_js': forms.Textarea(attrs={'class': 'form-control code-input', 'rows': 8, 'spellcheck': 'false', 'autocapitalize': 'none'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Generated from the title when left blank (see ProjectEditMixin.prepare_object)
        self.fields['slug'].required = False
        self.fields['categories'].queryset = Category.objects.prefetch_related('translations')

    def clean_slug(self):
        slug = self.cleaned_data['slug']
        if slug in RESERVED_SLUGS:
            raise forms.ValidationError(_('This slug is reserved, please choose another one.'))
        return slug

    def clean_cover_image(self):
        image = self.cleaned_data.get('cover_image')
        if isinstance(image, UploadedFile):
            return optimize_image(image, max_size=COVER_IMAGE_MAX_SIZE)
        return image


class ProjectTranslationForm(TranslationForm):

    class Meta:
        model = ProjectTranslation
        fields = ['title', 'summary', 'content', 'credits']
        widgets = {
            'summary': forms.Textarea(attrs={'rows': 2}),
            'content': forms.Textarea(attrs={'rows': 20, 'data-html-editor': ''}),
            'credits': forms.Textarea(attrs={'rows': 2}),
        }
