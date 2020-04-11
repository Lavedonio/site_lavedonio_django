from captcha import fields, widgets
from django import forms
from django.core.mail import send_mail
from django.utils.translation import gettext_lazy as _


class ContactForm(forms.Form):
    name = forms.CharField(label=_("Name"))
    subject = forms.CharField(label=_("Subject"))
    email = forms.EmailField(label=_("E-mail"))
    message = forms.CharField(widget=forms.Textarea, label=_("Message"))
    captcha = fields.ReCaptchaField(widget=widgets.ReCaptchaV3())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.label_suffix = ""  # Removes : as label suffix

    def send_email(self):
        # send email using the self.cleaned_data dictionary
        name = self.cleaned_data.get('name')
        subject = self.cleaned_data.get('subject')
        email = self.cleaned_data.get('email')
        raw_message = self.cleaned_data.get('message')

        message = "Mensagem de {0}, e-mail {1}:\n\n{2}".format(name, email, raw_message)

        from_email = "teste@gmail.com"
        send_mail(subject, message, from_email, ["daniel@lavedonio.com.br", email], fail_silently=True)
