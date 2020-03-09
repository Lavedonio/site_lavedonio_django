# Generated by Django 2.2.10 on 2020-03-04 03:07

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='FileUpload',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=128, verbose_name='Name')),
                ('slug', models.SlugField(default=uuid.uuid4, max_length=128, unique=True, verbose_name='Slug')),
                ('file_upload', models.FileField(upload_to='files/', verbose_name='File Upload')),
                ('description', models.CharField(blank=True, max_length=128, verbose_name='Description')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At')),
            ],
            options={
                'verbose_name': 'File Upload',
                'verbose_name_plural': 'File Uploads',
            },
        ),
        migrations.CreateModel(
            name='ImageUpload',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=128, verbose_name='Name')),
                ('slug', models.SlugField(default=uuid.uuid4, max_length=128, unique=True, verbose_name='Slug')),
                ('image_upload', models.ImageField(upload_to='images/', verbose_name='Image Upload')),
                ('description', models.CharField(blank=True, max_length=128, verbose_name='Description')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At')),
            ],
            options={
                'verbose_name': 'Image Upload',
                'verbose_name_plural': 'Image Uploads',
            },
        ),
    ]
