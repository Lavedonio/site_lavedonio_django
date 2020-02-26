import datetime
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils.text import slugify
from .models import Post


@receiver(pre_save, sender=Post)
def before_post_saved(sender, instance, **kwargs):
    instance.slug = str(instance.id) + "-" + slugify(instance.title)


@receiver(post_save, sender=Post)
def after_post_saved(sender, instance, created, **kwargs):
    if created:
        date_post_created = instance.date_posted
        instance.date_posted_year_month = datetime.date(
            year=date_post_created.year,
            month=date_post_created.month,
            day=1
        )
        instance.save()
