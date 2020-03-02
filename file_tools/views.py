from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView
from django.views import View
from .models import FileUpload, ImageUpload


class FileUploadListView(ListView):
    model = FileUpload
    context_object_name = "files"
    ordering = ["-id"]

    def get_context_data(self):
        context = super().get_context_data()
        context["title"] = "Arquivos"
        context["navbar_active"] = "files"

        return context


class ImageUploadListView(ListView):
    model = ImageUpload
    context_object_name = "images"
    ordering = ["-id"]

    def get_context_data(self):
        context = super().get_context_data()
        context["title"] = "Imagens"
        context["navbar_active"] = "images"

        return context


class ImageUploadDetailView(View):
	def get(self, request, slug):
		image = get_object_or_404(ImageUpload, slug=slug)
		return redirect(image.image_upload.url)
