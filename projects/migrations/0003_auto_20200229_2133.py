# Generated by Django 2.2.10 on 2020-03-01 00:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0002_project_featured'),
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
        migrations.RemoveField(
            model_name='project',
            name='downloads',
        ),
        migrations.RemoveField(
            model_name='project',
            name='highest_score',
        ),
        migrations.AddField(
            model_name='project',
            name='content',
            field=models.TextField(default='Default content for already existent Projects', verbose_name='Content'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='project',
            name='category',
            field=models.ManyToManyField(blank=True, to='projects.Category'),
        ),
    ]