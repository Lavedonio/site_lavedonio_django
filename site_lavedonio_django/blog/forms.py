from django import forms
from django.core.files.uploadedfile import UploadedFile
from django.utils.text import slugify
from django.utils.translation import get_language, gettext_lazy as _

from base.editing import PublicationDateMixin, TranslationForm
from base.images import optimize_image
from .models import Post, PostTranslation, Tag, TagTranslation

COVER_IMAGE_MAX_SIZE = 2400


class PostForm(PublicationDateMixin, forms.ModelForm):
    new_tags = forms.CharField(
        required=False,
        label=_('New tags'),
        help_text=_('Separated by commas. They are created when the post is saved.'),
        widget=forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'}),
    )

    class Meta:
        model = Post
        fields = ['published', 'featured', 'date_posted', 'tags', 'cover_image']
        widgets = {
            'published': forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch'}),
            'featured': forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch'}),
            'date_posted': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}, format='%Y-%m-%dT%H:%M'),
            'tags': forms.CheckboxSelectMultiple(attrs={'class': 'btn-check'}),
            'cover_image': forms.ClearableFileInput(attrs={'accept': 'image/*', 'class': 'form-control', 'data-cover-input': ''}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tags'].queryset = Tag.objects.prefetch_related('translations')

    def clean_cover_image(self):
        image = self.cleaned_data.get('cover_image')
        if isinstance(image, UploadedFile):
            return optimize_image(image, max_size=COVER_IMAGE_MAX_SIZE)
        return image

    def clean_new_tags(self):
        names = [name.strip() for name in self.cleaned_data['new_tags'].split(',')]
        return list(dict.fromkeys(name for name in names if name))

    def save(self, commit=True):
        post = super().save(commit=commit)
        if commit:
            self.save_new_tags(post)
        return post

    def save_new_tags(self, post):
        language = get_language()
        for name in self.cleaned_data['new_tags']:
            slug = slugify(name)[:64] or 'tag'
            tag, created = Tag.objects.get_or_create(slug=slug)
            if created:
                TagTranslation.objects.create(tag=tag, language=language, name=name)
            post.tags.add(tag)


class PostTranslationForm(TranslationForm):

    class Meta:
        model = PostTranslation
        fields = ['title', 'subtitle', 'slug', 'content', 'credits']
        widgets = {
            'subtitle': forms.Textarea(attrs={'rows': 2}),
            'content': forms.Textarea(attrs={'rows': 20, 'data-markdown-editor': ''}),
            'credits': forms.Textarea(attrs={'rows': 2}),
        }
