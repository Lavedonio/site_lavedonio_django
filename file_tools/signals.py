from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.text import slugify
from .models import ImageUpload


@receiver(pre_save, sender=ImageUpload)
def before_imageupload_saved(sender, instance, **kwargs):
    if slugify(instance.name) not in instance.slug:
        instance.slug = slugify(instance.name) + "-" + instance.slug
