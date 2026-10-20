"""
Fills the site with fake posts and projects, to test layouts, pagination,
filters and languages (e.g. on staging):

    python manage.py create_demo_content
    python manage.py create_demo_content --delete

They cover the cases the pages handle differently: English only, Portuguese
only or both; featured, drafts and scheduled posts; every project status; with
and without covers. Everything it creates is marked so --delete finds it: the
"demo" tag on posts and the "demo-" prefix on project slugs and categories.
Run again, it replaces the previous demo content. It refuses to run in
production.
"""
import datetime
import os
from io import BytesIO

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from PIL import Image, ImageDraw, ImageFont

from blog.models import Post, PostTranslation, Tag, TagTranslation
from projects.models import Category, CategoryTranslation, Project, ProjectTranslation

DEMO_TAG = 'demo'
DEMO_PREFIX = 'demo-'

# (slug, English name, Portuguese name, text color, background color)
TAGS = [
    (DEMO_TAG, 'Demo', 'Demonstração', '#FFFFFF', '#6C757D'),
    ('demo-python', 'Python', 'Python', '#212529', '#FFD43B'),
    ('demo-data', 'Data Engineering', 'Engenharia de Dados', '#FFFFFF', '#0D6EFD'),
    ('demo-cloud', 'Cloud', 'Nuvem', '#FFFFFF', '#198754'),
]

CATEGORIES = [
    ('demo-web', 'Web', 'Web'),
    ('demo-data', 'Data', 'Dados'),
    ('demo-automation', 'Automation', 'Automação'),
]

# Colors of the generated covers' gradients
PALETTES = [
    ((13, 27, 94), (0, 180, 216)),
    ((80, 20, 90), (240, 110, 80)),
    ((10, 70, 50), (150, 220, 120)),
    ((60, 60, 60), (200, 200, 200)),
    ((120, 30, 30), (250, 200, 80)),
    ((20, 40, 80), (120, 90, 220)),
]

POST_MARKDOWN = {
    'en': """\
This is a **demo post**, created by `create_demo_content` to test how the blog looks with more content.

## A section

Some text with a [link](https://www.djangoproject.com/), *italics* and ~~strikethrough~~.

- A list item
- Another one, with `inline code`

> A quote, to check how it looks.

## Some code

```python
def greet(name):
    return f"Hello, {name}!"
```

| Language | Year |
| --- | --- |
| Python | 1991 |
| SQL | 1974 |
""",
    'pt-br': """\
Esta é uma **publicação de demonstração**, criada pelo `create_demo_content` para testar como o blog fica com mais conteúdo.

## Uma seção

Um texto com um [link](https://www.djangoproject.com/), *itálico* e ~~riscado~~.

- Um item de lista
- Outro, com `código`

> Uma citação, para ver como fica.

## Um pouco de código

```python
def saudar(nome):
    return f"Olá, {nome}!"
```

| Linguagem | Ano |
| --- | --- |
| Python | 1991 |
| SQL | 1974 |
""",
}

PROJECT_HTML = {
    'en': (
        '<p>This is a <strong>demo project</strong>, created by <code>create_demo_content</code>.</p>'
        '<h2>What it does</h2><ul><li>Something useful</li><li>Something else</li></ul>'
        '<h2>How it was made</h2><p>With care, and a lot of coffee.</p>'
    ),
    'pt-br': (
        '<p>Este é um <strong>projeto de demonstração</strong>, criado pelo <code>create_demo_content</code>.</p>'
        '<h2>O que ele faz</h2><ul><li>Algo útil</li><li>Algo mais</li></ul>'
        '<h2>Como foi feito</h2><p>Com cuidado e muito café.</p>'
    ),
}

# (titles by language, days ago, options)
POSTS = [
    ({'en': 'Building a data pipeline with Airflow', 'pt-br': 'Construindo um pipeline de dados com Airflow'}, 10, {'featured': True, 'tags': ['demo-data', 'demo-python']}),
    ({'en': 'Notes on moving a database to the cloud'}, 45, {'tags': ['demo-cloud']}),
    ({'pt-br': 'Anotações sobre testes automatizados'}, 80, {'tags': ['demo-python']}),
    ({'en': 'What I learned rewriting my website', 'pt-br': 'O que aprendi reescrevendo meu site'}, 140, {'featured': True, 'tags': ['demo-python']}),
    ({'en': 'A post without a cover', 'pt-br': 'Uma publicação sem capa'}, 200, {'cover': False}),
    ({'en': 'Spot instances for Spark jobs', 'pt-br': 'Instâncias Spot para jobs Spark'}, 320, {'tags': ['demo-data', 'demo-cloud']}),
    ({'pt-br': 'Uma publicação antiga'}, 500, {}),
    ({'en': 'A draft that only editors see', 'pt-br': 'Um rascunho que só editores veem'}, 2, {'published': False}),
    ({'en': 'A post scheduled for next week', 'pt-br': 'Uma publicação agendada para semana que vem'}, -7, {}),
]

# (slug, titles by language, status, days ago, options)
PROJECTS = [
    ('demo-dashboard', {'en': 'Sales dashboard', 'pt-br': 'Dashboard de vendas'}, Project.Status.COMPLETED, 30,
     {'featured': True, 'categories': ['demo-data', 'demo-web'], 'live_url': 'https://example.com/', 'repository_url': 'https://github.com/Lavedonio'}),
    ('demo-scraper', {'en': 'Web scraper', 'pt-br': 'Web scraper'}, Project.Status.IN_PROGRESS, 90,
     {'categories': ['demo-automation'], 'repository_url': 'https://github.com/Lavedonio'}),
    ('demo-reports', {'pt-br': 'Relatórios automáticos'}, Project.Status.ARCHIVED, 400, {'categories': ['demo-automation', 'demo-data']}),
    ('demo-portfolio', {'en': 'Portfolio template'}, Project.Status.COMPLETED, 200, {'categories': ['demo-web'], 'cover': False}),
    ('demo-dark', {'en': 'Project with a dark background', 'pt-br': 'Projeto com fundo escuro'}, Project.Status.IN_PROGRESS, 15,
     {'categories': ['demo-web'], 'dark_background': True}),
    ('demo-draft', {'en': 'Unpublished project', 'pt-br': 'Projeto não publicado'}, Project.Status.IN_PROGRESS, 1, {'published': False}),
]


def make_cover(title, index):
    """A 1600x900 WebP gradient with the title, as an uploadable file."""
    width, height = 1600, 900
    start, end = PALETTES[index % len(PALETTES)]
    image = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(image)
    for x in range(width):
        ratio = x / (width - 1)
        draw.line([(x, 0), (x, height)], fill=tuple(round(a + (b - a) * ratio) for a, b in zip(start, end)))

    font = ImageFont.load_default(size=72)
    draw.multiline_text((100, height - 260), f'{title}\nDemo', font=font, fill=(255, 255, 255), spacing=20)

    output = BytesIO()
    image.save(output, format='WEBP', quality=80)
    return ContentFile(output.getvalue(), name=f'demo-{index}.webp')


class Command(BaseCommand):
    help = 'Creates (or with --delete, removes) fake posts and projects to test the site. Not in production.'

    def add_arguments(self, parser):
        parser.add_argument('--delete', action='store_true', help='Only remove the demo content.')

    def handle(self, *args, **options):
        if os.environ.get('ENVIRONMENT') == 'production':
            raise CommandError('Demo content is not allowed in production.')

        with transaction.atomic():
            deleted = self.delete_demo_content()
            if options['delete']:
                self.stdout.write(self.style.SUCCESS(f'Removed {deleted} demo objects.'))
                return

            tags = self.create_tags()
            categories = self.create_categories()
            posts = self.create_posts(tags)
            projects = self.create_projects(categories)

        self.stdout.write(self.style.SUCCESS(f'Created {posts} demo posts and {projects} demo projects.'))

    def delete_demo_content(self):
        count = 0
        for queryset in [
            Post.objects.filter(tags__slug=DEMO_TAG),
            Project.objects.filter(slug__startswith=DEMO_PREFIX),
            Tag.objects.filter(slug__in=[slug for slug, *_ in TAGS]),
            Category.objects.filter(slug__startswith=DEMO_PREFIX),
        ]:
            for item in queryset.distinct():
                # The covers are deleted from the storage too (R2 on the servers)
                if getattr(item, 'cover_image', None):
                    item.cover_image.delete(save=False)
                item.delete()
                count += 1
        return count

    def create_tags(self):
        tags = {}
        for slug, name_en, name_pt, color, background in TAGS:
            tag = Tag.objects.create(slug=slug, color=color, background_color=background)
            TagTranslation.objects.create(tag=tag, language='en', name=name_en)
            TagTranslation.objects.create(tag=tag, language='pt-br', name=name_pt)
            tags[slug] = tag
        return tags

    def create_categories(self):
        categories = {}
        for slug, name_en, name_pt in CATEGORIES:
            category = Category.objects.create(slug=slug)
            CategoryTranslation.objects.create(category=category, language='en', name=name_en)
            CategoryTranslation.objects.create(category=category, language='pt-br', name=name_pt)
            categories[slug] = category
        return categories

    def create_posts(self, tags):
        now = timezone.now()
        for index, (titles, days_ago, options) in enumerate(POSTS):
            post = Post.objects.create(
                published=options.get('published', True),
                featured=options.get('featured', False),
                date_posted=now - datetime.timedelta(days=days_ago),
            )
            if options.get('cover', True):
                post.cover_image.save('demo.webp', make_cover(next(iter(titles.values())), index), save=True)
            post.tags.add(tags[DEMO_TAG], *(tags[slug] for slug in options.get('tags', [])))

            for language, title in titles.items():
                PostTranslation.objects.create(
                    post=post, language=language, title=title, content=POST_MARKDOWN[language],
                    subtitle='Demo' if language == 'en' else 'Demonstração',
                )
            # The same update time as the publication, or it's shown as "updated"
            Post.objects.filter(pk=post.pk).update(last_updated=post.date_posted)
        return len(POSTS)

    def create_projects(self, categories):
        now = timezone.now()
        for index, (slug, titles, status, days_ago, options) in enumerate(PROJECTS):
            project = Project.objects.create(
                slug=slug,
                status=status,
                published=options.get('published', True),
                featured=options.get('featured', False),
                date_posted=now - datetime.timedelta(days=days_ago),
                repository_url=options.get('repository_url', ''),
                live_url=options.get('live_url', ''),
                dark_background=options.get('dark_background', False),
            )
            if options.get('cover', True):
                project.cover_image.save('demo.webp', make_cover(next(iter(titles.values())), index + len(POSTS)), save=True)
            project.categories.add(*(categories[category] for category in options.get('categories', [])))

            for language, title in titles.items():
                ProjectTranslation.objects.create(
                    project=project, language=language, title=title, content=PROJECT_HTML[language],
                    summary='A demo project, to test the site.' if language == 'en' else 'Um projeto de demonstração, para testar o site.',
                )
        return len(PROJECTS)
