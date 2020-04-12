from django import forms
from django.utils.translation import gettext_lazy as _


class ContactForm(forms.Form):
    name = forms.CharField(label=_("Name"))
    subject = forms.CharField(label=_("Subject"))
    email = forms.EmailField(label=_("E-mail"))
    message = forms.CharField(widget=forms.Textarea, label=_("Message"))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.label_suffix = ""  # Removes : as label suffix
