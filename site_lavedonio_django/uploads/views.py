from django import forms
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from django.views import View

from base.images import optimize_image
from .models import UploadedImage

MAX_UPLOAD_SIZE = 15 * 1024 * 1024


class ImageUploadForm(forms.Form):
    image = forms.ImageField()

    def clean_image(self):
        image = self.cleaned_data['image']
        if image.size > MAX_UPLOAD_SIZE:
            raise forms.ValidationError(_('The image must be smaller than 15 MB.'))
        return image


class ImageUploadView(PermissionRequiredMixin, View):
    """Receives images pasted, dropped or chosen in the editors and returns their URL."""
    permission_required = 'uploads.add_uploadedimage'
    raise_exception = True

    def post(self, request, *args, **kwargs):
        form = ImageUploadForm(request.POST, request.FILES)
        if not form.is_valid():
            return JsonResponse({'error': ' '.join(form.errors.get('image', [_('Invalid image.')]))}, status=400)

        original = form.cleaned_data['image']
        uploaded = UploadedImage.objects.create(
            image=optimize_image(original),
            original_name=original.name[:255],
            uploaded_by=request.user,
        )
        return JsonResponse({'url': uploaded.image.url, 'name': uploaded.original_name}, status=201)
