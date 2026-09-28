from django import forms
from django.utils.translation import gettext_lazy as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from crispy_bootstrap5.bootstrap5 import FloatingField


class ContactForm(forms.Form):
    name = forms.CharField(label=_("Name"))
    subject = forms.CharField(label=_("Subject"))
    email = forms.EmailField(label=_("E-mail"))
    message = forms.CharField(widget=forms.Textarea, label=_("Message"))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.label_suffix = ""  # Removes : as label suffix

        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            FloatingField('name'),
            FloatingField('subject'),
            FloatingField('email'),
            FloatingField('message'),
        )
