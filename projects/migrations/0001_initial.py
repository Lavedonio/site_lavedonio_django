# Generated by Django 2.2.10 on 2020-03-04 03:07

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=32, verbose_name='Name')),
                ('abbreviation', models.CharField(max_length=32, verbose_name='Abbreviation')),
            ],
            options={
                'verbose_name': 'Category',
                'verbose_name_plural': 'Categories',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=64, verbose_name='Title')),
                ('slug', models.SlugField(max_length=32, unique=True, verbose_name='Slug')),
                ('featured', models.BooleanField(default=False, verbose_name='Featured')),
                ('dark_background', models.BooleanField(default=False, verbose_name='Dark Background')),
                ('published', models.BooleanField(default=True, verbose_name='Published')),
                ('main_image', models.ImageField(default='default_project_img.jpg', upload_to='projects', verbose_name='Main Image')),
                ('description', models.CharField(max_length=128, verbose_name='Description')),
                ('content', models.TextField(verbose_name='Content')),
                ('custom_css', models.BooleanField(default=False, verbose_name='Custom CSS')),
                ('custom_js', models.BooleanField(default=False, verbose_name='Custom JavaScript')),
                ('categories', models.ManyToManyField(blank=True, to='projects.Category', verbose_name='Categories')),
            ],
            options={
                'verbose_name': 'Project',
                'verbose_name_plural': 'Projects',
            },
        ),
    ]
