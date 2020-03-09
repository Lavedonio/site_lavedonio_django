# Generated by Django 2.2.10 on 2020-03-04 03:07

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=32, verbose_name='Name')),
                ('color', models.CharField(max_length=7, verbose_name='Color')),
                ('background_color', models.CharField(max_length=7, verbose_name='Background Color')),
            ],
            options={
                'verbose_name': 'Tag',
                'verbose_name_plural': 'Tags',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=128, verbose_name='Title')),
                ('subtitle', models.CharField(blank=True, max_length=512, verbose_name='Subtitle')),
                ('slug', models.SlugField(default=uuid.uuid4, max_length=128, unique=True, verbose_name='Slug')),
                ('main_image', models.ImageField(default='default_post_img.jpg', upload_to='posts', verbose_name='Main Image')),
                ('featured', models.BooleanField(default=False, verbose_name='Featured')),
                ('published', models.BooleanField(default=True, verbose_name='Published')),
                ('date_posted', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Date Posted')),
                ('last_updated', models.DateTimeField(auto_now=True, verbose_name='Last Updated')),
                ('date_posted_year_month', models.DateField(default=django.utils.timezone.now, verbose_name='Date Posted Year/Month')),
                ('content', models.TextField(verbose_name='Content')),
                ('author', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Author')),
                ('tags', models.ManyToManyField(blank=True, to='blog.Tag', verbose_name='Tags')),
            ],
            options={
                'verbose_name': 'Post',
                'verbose_name_plural': 'Posts',
            },
        ),
    ]
