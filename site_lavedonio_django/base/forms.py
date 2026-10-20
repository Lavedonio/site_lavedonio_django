from django import forms
from django.core.files.uploadedfile import UploadedFile
from django.db.models import Max
from django.utils.translation import gettext_lazy as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Column, Layout, Row
from crispy_bootstrap5.bootstrap5 import FloatingField

from .editing import TranslationForm
from .images import optimize_image
from .models import AboutSection, AboutSectionTranslation

# The pictures take up to a third of the page width (the whole width on phones, which have 3x screens)
ABOUT_IMAGE_MAX_SIZE = 1200

# Gap left between the orders of consecutive sections, so new ones can go in between
ABOUT_ORDER_STEP = 10


class ContactForm(forms.Form):
    name = forms.CharField(label=_("Name"), max_length=100)
    subject = forms.CharField(label=_("Subject"), max_length=150)
    email = forms.EmailField(label=_("E-mail"))
    message = forms.CharField(widget=forms.Textarea, label=_("Message"), max_length=5000)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.label_suffix = ""  # Removes : as label suffix

        self.helper = FormHelper(self)
        # The <form> and its CSRF token are in the template
        self.helper.form_tag = False
        self.helper.disable_csrf = True
        self.helper.layout = Layout(
            Row(
                Column(FloatingField('name', autocomplete='name'), css_class='col-md-6'),
                Column(FloatingField('email', autocomplete='email'), css_class='col-md-6'),
            ),
            FloatingField('subject'),
            FloatingField('message'),
        )

    def clean_subject(self):
        # It's the subject of the e-mail, which can't have line breaks
        return ' '.join(self.cleaned_data['subject'].split())


class AboutSectionForm(forms.ModelForm):

    class Meta:
        model = AboutSection
        fields = ['order', 'slug', 'image']
        widgets = {
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'slug': forms.TextInput(attrs={'class': 'form-control', 'autocapitalize': 'none'}),
            'image': forms.ClearableFileInput(attrs={'accept': 'image/*'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Generated from the title when left blank (see AboutSectionEditMixin.prepare_object)
        self.fields['slug'].required = False
        self.fields['slug'].help_text = _('Used in links to the section (e.g. /about/#education). Leave it blank to generate it from the title.')

        # New sections go after the last one
        if self.instance.pk is None:
            last_order = AboutSection.objects.aggregate(Max('order'))['order__max']
            self.initial['order'] = 0 if last_order is None else last_order + ABOUT_ORDER_STEP

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if isinstance(image, UploadedFile):
            return optimize_image(image, max_size=ABOUT_IMAGE_MAX_SIZE)
        return image


class AboutSectionTranslationForm(TranslationForm):

    class Meta:
        model = AboutSectionTranslation
        fields = ['title', 'content', 'image_caption']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 16, 'data-markdown-editor': ''}),
        }
