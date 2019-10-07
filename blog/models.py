import os
import datetime
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.urls import reverse


class Post(models.Model):
    title = models.CharField(max_length=128, verbose_name=_('Title'))
    subtitle = models.CharField(max_length=512, blank=True, null=True, verbose_name=_('Subtitle'))
    light_title_text = models.BooleanField(default=False, verbose_name=_('Light Title Text'))
    main_image = models.ImageField(default='posts/default.jpg', upload_to='posts', verbose_name=_('Main Image'))
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name=_('Author'))
    draft = models.BooleanField(default=False, verbose_name=_('Draft'))
    date_posted = models.DateTimeField(default=timezone.now, verbose_name=_('Date Posted'))
    last_updated = models.DateTimeField(auto_now=True, verbose_name=_('Last Updated'))
    content = models.TextField(verbose_name=_('Content'))

    @property
    def lt_one_minute_between_creation_and_update(self):
        minutes = self.last_updated > self.date_posted + datetime.timedelta(minutes=1)
        return minutes < 1

    @property
    def image_name(self):
        return os.path.basename(self.main_image.name)

    class Meta:
        verbose_name = _('Post')
        verbose_name_plural = _('Posts')

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('post', kwargs={'pk': self.pk})
