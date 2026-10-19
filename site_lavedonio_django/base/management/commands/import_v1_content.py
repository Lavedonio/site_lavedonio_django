"""
Imports the blog posts and projects of the first version (v1) of the site.

v1 content is all in Brazilian Portuguese, so each post, project, tag and
category becomes a v2 object with a 'pt-br' translation. The v1 database is read
with plain SQL, so the v1 apps don't need to be installed:

    python manage.py import_v1_content /path/to/v1.sqlite3 --dry-run
    python manage.py import_v1_content v1  # alias of the v1 database in settings.DATABASES

Running it again updates what was imported before instead of duplicating it:
tags and categories are matched by slug, projects by slug and posts by their
Portuguese slug, which is the v1 slug, so old links can be redirected. Objects
created by the import keep their v1 ID when no v2 object uses it.

It lives in the base app because it imports into both the blog and projects apps.
"""
import base64
import datetime
import glob
import posixpath
import re
import sqlite3
from collections import Counter
from contextlib import closing
from pathlib import Path
from urllib.parse import quote, unquote

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.staticfiles import finders
from django.core.exceptions import SuspiciousFileOperation
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand, CommandError
from django.core.management.color import no_style
from django.db import DEFAULT_DB_ALIAS, connection, connections, transaction
from django.utils import timezone
from django.utils._os import safe_join
from django.utils.dateparse import parse_datetime
from django.utils.text import Truncator, slugify

from base.markdown import get_markdown_parser
from blog.models import Post, PostTranslation, Tag, TagTranslation
from projects.models import Category, CategoryTranslation, Project, ProjectTranslation

LANGUAGE = 'pt-br'

# Tables read from the v1 database and the columns the import needs from them
V1_TABLES = {
    'auth_user': {'id', 'username', 'email'},
    'blog_tag': {'id', 'name', 'color', 'background_color'},
    'blog_post': {
        'id', 'title', 'subtitle', 'slug', 'main_image', 'credits', 'author_id', 'featured',
        'published', 'date_posted', 'last_updated', 'content',
    },
    'blog_post_tags': {'post_id', 'tag_id'},
    'projects_category': {'id', 'name', 'abbreviation'},
    'projects_project': {
        'id', 'title', 'slug', 'featured', 'dark_background', 'published', 'main_image', 'description',
        'credits', 'date_posted', 'last_updated', 'content', 'fix_autoscale', 'custom_css', 'custom_js',
    },
    'projects_project_categories': {'project_id', 'category_id'},
}

# Columns read when the v1 database has them (export_v1_database copies them too)
V1_OPTIONAL_COLUMNS = {
    'projects_project': {'custom_font'},
}

# Tables read when the v1 database has them, with the columns the import needs.
# v1 served the images uploaded in file_tools at /arquivos/imagens/<slug>/, the
# address used in posts and projects, which v2 doesn't have.
V1_OPTIONAL_TABLES = {
    'file_tools_imageupload': {'id', 'slug', 'image_upload'},
}

# v1 used Bootstrap 4 and v2 uses Bootstrap 5, which renamed or dropped these
# classes. Classes mapped to '' are removed.
BOOTSTRAP_5_CLASSES = {
    'font-italic': 'fst-italic',
    'font-weight-bold': 'fw-bold',
    'font-weight-bolder': 'fw-bolder',
    'font-weight-normal': 'fw-normal',
    'font-weight-light': 'fw-light',
    'float-left': 'float-start',
    'float-right': 'float-end',
    'text-left': 'text-start',
    'text-right': 'text-end',
    'sr-only': 'visually-hidden',
    'badge-pill': 'rounded-pill',
    'btn-block': 'w-100',
    'no-gutters': 'g-0',
    'custom-select': 'form-select',
    'custom-select-sm': 'form-select-sm',
    'custom-select-lg': 'form-select-lg',
    'embed-responsive': 'ratio',
    'embed-responsive-21by9': 'ratio-21x9',
    'embed-responsive-16by9': 'ratio-16x9',
    'embed-responsive-4by3': 'ratio-4x3',
    'embed-responsive-1by1': 'ratio-1x1',
    'embed-responsive-item': '',
}
# Margins and paddings: ml-2 -> ms-2, pr-md-3 -> pe-md-3...
BOOTSTRAP_4_SPACING = re.compile(r'^([mp])([lr])(-(?:sm|md|lg|xl)?-?(?:n?\d|auto))$')
# Attributes of Bootstrap's JavaScript components: data-toggle -> data-bs-toggle...
BOOTSTRAP_4_DATA = re.compile(r'\bdata-(toggle|target|dismiss|parent|ride|slide|slide-to|interval|placement|content|offset|spy)=')
CLASS_ATTRIBUTE = re.compile(r'''(\bclass=)(["'])(.*?)\2''', re.DOTALL)

# v1 pages loaded jQuery (needed by Bootstrap 4) and v2 doesn't. These are the
# jQuery calls used by the v1 projects, rewritten without it. Bootstrap 5 tab
# events bubble up to the document, so listening there keeps the same callback.
V1_JQUERY_REWRITES = [
    (re.compile(r'''\$\((['"])a\[data-toggle=(["'])tab\2\]\1\)\.on\((['"])shown\.bs\.tab\3,'''), "document.addEventListener('shown.bs.tab',"),
    (re.compile(r'''\$\((\w+)\.target\)\.attr\((["'])href\2\)'''), r"\1.target.getAttribute('href')"),
]
JQUERY_CALL = re.compile(r'(?<![\w.])(?:\$|jQuery)\(')

# v1 loaded css/projects.css and js/projects.js in every project page. They make
# the element with id="lockpage" toggle a fullscreen mode (used by the games), so
# projects that have it get them in their custom CSS and JavaScript.
V1_FULLSCREEN_MARKUP = 'id="lockpage"'
V1_SHARED_PROJECT_FILES = {'css': 'projects.css', 'js': 'projects.js'}

# Tried, in this order, when a v1 main image isn't found with the extension
# saved in the database (e.g. "logo.jpg" downloaded from the bucket as "logo.png")
V1_IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.webp', '.gif')

# Placeholders v1 used when no image was uploaded. v2 shows its own placeholder for empty covers.
V1_DEFAULT_IMAGES = {'default_post_img.jpg', 'default_project_img.jpg'}

# The font v1 added to projects with "custom font" checked, served from its static files.
# v2 has no such option, so it's embedded in the project's custom CSS.
V1_FONT_DIR = Path('fonts', 'bit5x3')
V1_FONT_FACE = """/* Bit5x3 font (http://www.mattlag.com/bitfonts/), imported from v1 */
@font-face {{
  font-family: "Bit5x3";
  src: url(data:font/woff2;base64,{woff2}) format("woff2"),
       url(data:font/woff;base64,{woff}) format("woff");
  font-weight: normal;
  font-style: normal;
}}
"""

# Links to uploaded and static files in v1 content, relative or with a v1 domain
FILE_REFERENCE = re.compile(
    r"""(?<=["'(=\s])(?:https?://(?:www\.)?lavedonio\.com(?:\.br)?)?/(?P<kind>media|static)/(?P<path>[^"'\s)?#]+)"""
)

# Links to the images uploaded in v1's file_tools (/arquivos/imagens/<slug>/,
# which redirected to the file), relative or with a v1 domain. They are replaced
# by the file's address in the media folder, so FILE_REFERENCE copies it.
V1_IMAGE_LINK = re.compile(
    r"""(?<=["'(=\s])(?:https?://(?:www\.)?lavedonio\.com(?:\.br)?)?/arquivos/imagens/(?P<slug>[-\w]+)/?(?=["'\s)?#]|$)"""
)

# Elements whose blank lines are part of the content
PRESERVED_BLOCK = re.compile(r'<(pre|textarea)\b.*?</\1\s*>', re.IGNORECASE | re.DOTALL)
BLANK_LINE = re.compile(r'\n[ \t]*(?=\n)')
PRESERVED_BLANK_LINE = re.compile(r'(\n[ \t]*)\n')


def parse_v1_datetime(value):
    # SQLite returns text and v1 had USE_TZ = True, so naive values are in UTC
    if isinstance(value, str):
        value = parse_datetime(value)
    if value is not None and timezone.is_naive(value):
        value = timezone.make_aware(value, datetime.timezone.utc)
    return value


def bootstrap_5_class(name):
    if name in BOOTSTRAP_5_CLASSES:
        return BOOTSTRAP_5_CLASSES[name]
    match = BOOTSTRAP_4_SPACING.match(name)
    if match:
        side = {'l': 's', 'r': 'e'}[match[2]]
        return f'{match[1]}{side}{match[3]}'
    return name


def convert_to_bootstrap_5(html):
    """Updates the Bootstrap 4 classes and data attributes of v1 content to Bootstrap 5."""
    def replace_classes(match):
        classes = ' '.join(name for name in map(bootstrap_5_class, match[3].split()) if name)
        return f'{match[1]}{match[2]}{classes}{match[2]}' if classes else ''

    html = CLASS_ATTRIBUTE.sub(replace_classes, html or '')
    return BOOTSTRAP_4_DATA.sub(r'data-bs-\1=', html)


def is_raw_html(text):
    return all(token.type == 'html_block' for token in get_markdown_parser().parse(text))


def html_for_markdown(html):
    """
    v1 posts are HTML and v2 renders posts as Markdown, which passes raw HTML
    through only until the next blank line: after it, indented lines become code
    blocks and text becomes Markdown paragraphs. So blank lines are removed (in
    <pre> and <textarea> they're kept as &#10;, which the browser reads as a line
    break) and, if the result still isn't parsed as raw HTML only, it's wrapped in
    a <div>. HTML that is already rendered as-is is kept unchanged.
    """
    html = (html or '').replace('\r\n', '\n').replace('\r', '\n').strip()
    if is_raw_html(html):
        return html

    parts, position = [], 0
    for match in PRESERVED_BLOCK.finditer(html):
        parts.append(BLANK_LINE.sub('', html[position:match.start()]))
        parts.append(PRESERVED_BLANK_LINE.sub(r'\1&#10;', match.group()))
        position = match.end()
    parts.append(BLANK_LINE.sub('', html[position:]))
    html = ''.join(parts)

    return html if is_raw_html(html) else f'<div>\n{html}\n</div>'


def fit(model, field_name, value, warnings, label):
    max_length = model._meta.get_field(field_name).max_length
    if value and max_length and len(value) > max_length:
        warnings.append(f'{label}: {field_name} has {len(value)} characters and was shortened to {max_length}.')
        return Truncator(value).chars(max_length)
    return value


def assign(instance, values):
    """Sets `values` on `instance` and returns the names of the fields that changed."""
    changed = []
    for field, value in values.items():
        if getattr(instance, field) != value:
            setattr(instance, field, value)
            changed.append(field)
    return changed


class V1Database:
    """Read-only access to the v1 tables, in a SQLite file or in a settings.DATABASES alias."""

    def __init__(self, source):
        path = Path(source).expanduser()
        if path.is_file():
            self.connection = sqlite3.connect(f'{path.resolve().as_uri()}?mode=ro', uri=True)
            self.owns_connection = True
        elif source in settings.DATABASES:
            if source == DEFAULT_DB_ALIAS:
                raise CommandError(f'"{source}" is the v2 database. Pass the alias of the v1 database.')
            self.connection = connections[source]
            self.owns_connection = False
        else:
            raise CommandError(f'"{source}" is neither a SQLite file nor an alias in settings.DATABASES.')
        self.source = source

    def has_table(self, table):
        if self.owns_connection:
            with closing(self.connection.cursor()) as cursor:
                cursor.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", [table])
                return cursor.fetchone() is not None
        return table in self.connection.introspection.table_names()

    def fetch(self, table, required_columns=None):
        required_columns = V1_TABLES[table] if required_columns is None else required_columns
        try:
            with closing(self.connection.cursor()) as cursor:
                cursor.execute(f'SELECT * FROM "{table}"')
                columns = [column[0] for column in cursor.description]
                rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as error:
            raise CommandError(f'Could not read the table {table} of {self.source}: {error}. Is it the v1 database?') from error

        missing = required_columns - set(columns)
        if missing:
            raise CommandError(
                f'The table {table} of {self.source} has no column {", ".join(sorted(missing))}. Is it the v1 database?'
            )
        return sorted(rows, key=lambda row: row.get('id') or 0)

    def close(self):
        if self.owns_connection:
            self.connection.close()


class Command(BaseCommand):
    help = (
        'Imports the posts, projects, tags and categories of v1 of the site as Brazilian Portuguese (pt-br) '
        'translations. Running it again updates what was imported before.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            'source',
            help='Path to a SQLite copy of the v1 database, or the alias of the v1 database in settings.DATABASES.',
        )
        parser.add_argument(
            '--media-root', type=Path,
            help='Folder with the v1 uploads (main images and files linked in the content). Defaults to MEDIA_ROOT, which v1 also used.',
        )
        parser.add_argument(
            '--static-dir', type=Path,
            help="v1 projects' static folder, with css/<slug>.css, js/<slug>.js and fonts/. Defaults to <BASE_DIR>/v1_export/static.",
        )
        parser.add_argument(
            '--author',
            help='Username of the author for v1 posts whose author has no v2 user with the same username or e-mail.',
        )
        parser.add_argument(
            '--tag-slug', action='append', default=[], metavar='V1_TAG=SLUG',
            help='Imports a v1 tag into the v2 tag with this slug, e.g. --tag-slug "Engenharia de Dados=data-engineering". Can be repeated.',
        )
        parser.add_argument(
            '--category-slug', action='append', default=[], metavar='V1_CATEGORY=SLUG',
            help='Imports a v1 category (name or abbreviation) into the v2 category with this slug, e.g. --category-slug IA=ai. Can be repeated.',
        )
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Shows what would be imported, without changing the database or copying files.',
        )

    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        self.verbosity = options['verbosity']
        self.media_root = options['media_root'] or Path(settings.MEDIA_ROOT)
        self.static_dir = options['static_dir'] or Path(settings.BASE_DIR) / 'v1_export' / 'static'
        self.tag_slugs = self.parse_slug_map(options['tag_slug'], '--tag-slug')
        self.category_slugs = self.parse_slug_map(options['category_slug'], '--category-slug')
        self.default_author = self.get_default_author(options['author'])
        self.stats = Counter()
        self.warnings = []
        self.saved_files = []
        self.copied_references = set()

        v1 = V1Database(options['source'])
        try:
            data = {table: v1.fetch(table) for table in V1_TABLES}
            data.update({
                table: v1.fetch(table, columns) if v1.has_table(table) else []
                for table, columns in V1_OPTIONAL_TABLES.items()
            })
        finally:
            v1.close()
        self.v1_users = {row['id']: row for row in data['auth_user']}
        self.v1_images = {row['slug']: row['image_upload'] for row in data['file_tools_imageupload']}

        try:
            with transaction.atomic():
                tags = self.import_tags(data['blog_tag'])
                self.import_posts(data['blog_post'], data['blog_post_tags'], tags)
                categories = self.import_categories(data['projects_category'])
                self.import_projects(data['projects_project'], data['projects_project_categories'], categories)
                self.reset_sequences()
                if self.dry_run:
                    transaction.set_rollback(True)
        except BaseException:
            for name in self.saved_files:
                default_storage.delete(name)
            raise

        self.print_summary()

    # Options

    def parse_slug_map(self, values, option):
        slugs = {}
        for value in values:
            v1_name, separator, slug = value.rpartition('=')
            if not separator or not v1_name.strip() or not slug or slugify(slug) != slug:
                raise CommandError(f'{option} expects V1_NAME=slug (e.g. "Inteligência Artificial=ai"), got "{value}".')
            slugs[slugify(v1_name)] = slug
        return slugs

    def get_default_author(self, username):
        if not username:
            return None
        try:
            return get_user_model().objects.get(username=username)
        except get_user_model().DoesNotExist:
            raise CommandError(f'There is no v2 user "{username}" (--author).')

    # Importers

    def import_tags(self, rows):
        """Returns {v1 id: v2 Tag}"""
        tags, v1_names = {}, {}
        for row in rows:
            name = row['name']
            slug = self.tag_slugs.get(slugify(name)) or slugify(name)[:64] or 'tag'
            label = f'Tag v1 #{row["id"]} "{name}"'
            if slug in v1_names:
                self.warn(f'{label} was merged into the v2 tag "{slug}", together with "{v1_names[slug]}".')
            v1_names[slug] = name

            tag = Tag.objects.filter(slug=slug).first()
            created = tag is None
            if created:
                tag = Tag(pk=self.free_pk(Tag, row['id']), slug=slug)
            changed = assign(tag, {'color': row['color'], 'background_color': row['background_color']})
            if created or changed:
                tag.save()

            changed += self.save_translation(TagTranslation, {'tag': tag}, {
                'name': fit(TagTranslation, 'name', name, self.warnings, label),
            })
            self.report('Tags', f'{label} → #{tag.pk} "{slug}"', created, changed)
            tags[row['id']] = tag
        return tags

    def import_posts(self, rows, post_tags, tags):
        tags_by_post = {}
        for row in post_tags:
            tags_by_post.setdefault(row['post_id'], []).append(tags[row['tag_id']])

        for row in rows:
            label = f'Post v1 #{row["id"]} "{row["title"]}"'
            post = Post.objects.filter(translations__language=LANGUAGE, translations__slug=row['slug']).first()
            created = post is None
            if created:
                post = Post(pk=self.free_pk(Post, row['id']))

            values = {
                'featured': bool(row['featured']),
                'published': bool(row['published']),
                'date_posted': parse_v1_datetime(row['date_posted']),
                'last_updated': parse_v1_datetime(row['last_updated']),
            }
            author_id = self.get_author_id(row['author_id'], label)
            if author_id or created:
                values['author_id'] = author_id
            changed = assign(post, values)
            changed += self.copy_cover(post, row['main_image'], label)
            if created or changed:
                self.save_keeping_last_updated(post, values['last_updated'])

            content = html_for_markdown(convert_to_bootstrap_5(self.with_media_image_links(row['content'], label)))
            credits = self.with_media_image_links(row['credits'] or '', label)
            changed += self.save_translation(PostTranslation, {'post': post}, {
                'title': fit(PostTranslation, 'title', row['title'], self.warnings, label),
                'subtitle': fit(PostTranslation, 'subtitle', row['subtitle'] or '', self.warnings, label),
                'slug': row['slug'],
                'content': content,
                'credits': credits,
            })

            post_tag_ids = {tag.pk for tag in tags_by_post.get(row['id'], [])}
            if created or set(post.tags.values_list('pk', flat=True)) != post_tag_ids:
                post.tags.set(post_tag_ids)
                changed.append('tags')

            self.check_file_references(label, content, credits)
            self.report('Posts', f'{label} → #{post.pk}', created, changed)

    def import_categories(self, rows):
        """Returns {v1 id: v2 Category}"""
        categories = {}
        for row in rows:
            name, abbreviation = row['name'], row['abbreviation']
            slug = (
                self.category_slugs.get(slugify(name)) or self.category_slugs.get(slugify(abbreviation))
                or slugify(abbreviation or name)[:64] or 'category'
            )
            label = f'Category v1 #{row["id"]} "{name}"'

            category = Category.objects.filter(slug=slug).first()
            created = category is None
            if created:
                category = Category.objects.create(pk=self.free_pk(Category, row['id']), slug=slug)

            changed = self.save_translation(CategoryTranslation, {'category': category}, {
                'name': fit(CategoryTranslation, 'name', name, self.warnings, label),
            })
            self.report('Categories', f'{label} → #{category.pk} "{slug}"', created, changed)
            categories[row['id']] = category
        return categories

    def import_projects(self, rows, project_categories, categories):
        categories_by_project = {}
        for row in project_categories:
            categories_by_project.setdefault(row['project_id'], []).append(categories[row['category_id']])

        for row in rows:
            slug = row['slug']
            label = f'Project v1 #{row["id"]} "{row["title"]}"'
            project = Project.objects.filter(slug=slug).first()
            created = project is None
            if created:
                project = Project(pk=self.free_pk(Project, row['id']), slug=slug)

            values = {
                'featured': bool(row['featured']),
                'published': bool(row['published']),
                'date_posted': parse_v1_datetime(row['date_posted']),
                'last_updated': parse_v1_datetime(row['last_updated']),
                'dark_background': bool(row['dark_background']),
                'fix_autoscale': bool(row['fix_autoscale']),
            }
            custom_css = self.read_custom_code(row['custom_css'], 'css', slug, label)
            if row.get('custom_font'):
                custom_css = self.get_v1_font_face(label) + ('\n' + custom_css if custom_css else '')
            custom_js = self.without_jquery(self.read_custom_code(row['custom_js'], 'js', slug, label), label)
            if V1_FULLSCREEN_MARKUP in (row['content'] or ''):
                custom_css = self.with_shared_project_code(custom_css, 'css', label)
                custom_js = self.with_shared_project_code(custom_js, 'js', label)
            if custom_css is not None:
                values['custom_css'] = custom_css
            if custom_js is not None:
                values['custom_js'] = custom_js

            changed = assign(project, values)
            changed += self.copy_cover(project, row['main_image'], label)
            if created or changed:
                self.save_keeping_last_updated(project, values['last_updated'])

            content = convert_to_bootstrap_5(self.with_media_image_links(row['content'], label))
            credits = self.with_media_image_links(row['credits'] or '', label)
            changed += self.save_translation(ProjectTranslation, {'project': project}, {
                'title': fit(ProjectTranslation, 'title', row['title'], self.warnings, label),
                'summary': fit(ProjectTranslation, 'summary', row['description'], self.warnings, label),
                'content': content,
                'credits': credits,
            })

            category_ids = {category.pk for category in categories_by_project.get(row['id'], [])}
            if created or set(project.categories.values_list('pk', flat=True)) != category_ids:
                project.categories.set(category_ids)
                changed.append('categories')

            self.check_file_references(label, content, credits, project.custom_css, project.custom_js)
            self.report('Projects', f'{label} → #{project.pk} "{slug}"', created, changed)

    # Helpers

    def free_pk(self, model, v1_id):
        """The v1 ID, unless a v2 object already uses it (then the database picks a new one)."""
        if model.objects.filter(pk=v1_id).exists():
            self.warn(f'{model._meta.verbose_name.title()} v1 #{v1_id}: a different v2 object already has this ID, so it gets a new one.')
            return None
        return v1_id

    def save_translation(self, model, parent, values):
        translation = model.objects.filter(language=LANGUAGE, **parent).first() or model(language=LANGUAGE, **parent)
        changed = assign(translation, values)
        if translation.pk is None or changed:
            translation.save()
        return changed

    def save_keeping_last_updated(self, instance, last_updated):
        # last_updated has auto_now=True, so save() replaces it with now and update() puts the v1 date back
        instance.save()
        type(instance).objects.filter(pk=instance.pk).update(last_updated=last_updated)
        instance.last_updated = last_updated

    def get_author_id(self, v1_author_id, label):
        v1_user = self.v1_users.get(v1_author_id)
        user = None
        if v1_user:
            users = get_user_model().objects
            user = users.filter(username=v1_user['username']).first()
            if user is None and v1_user['email']:
                user = users.filter(email__iexact=v1_user['email']).first()
        user = user or self.default_author
        if user is None and v1_author_id is not None:
            username = v1_user['username'] if v1_user else f'#{v1_author_id}'
            self.warn(f'{label}: no v2 user matches the v1 author "{username}". Use --author to pick one.')
        return user.pk if user else None

    def v1_media_path(self, name):
        try:
            return Path(safe_join(self.media_root, name))
        except SuspiciousFileOperation:
            return None

    def find_v1_image(self, name, label):
        """
        Path of the v1 upload `name` or, when it's missing, of a file with the
        same name and another image extension (with a warning). None if neither exists.
        """
        source = self.v1_media_path(name)
        if source is None:
            return None
        if source.is_file():
            return source

        candidates = {path.suffix.lower(): path for path in source.parent.glob(f'{glob.escape(source.stem)}.*') if path.is_file()}
        for extension in V1_IMAGE_EXTENSIONS:
            if extension in candidates:
                alternative = candidates[extension]
                self.warn(f'{label}: main image "{name}" not found, so "{posixpath.join(posixpath.dirname(name), alternative.name)}" was used.')
                return alternative
        return None

    def copy_cover(self, instance, v1_name, label):
        """Copies the v1 main image to `cover_image`, unless it's already there."""
        if not v1_name or posixpath.basename(v1_name) in V1_DEFAULT_IMAGES:
            return []

        source = self.find_v1_image(v1_name, label)
        if source is None:
            self.warn(f'{label}: main image "{v1_name}" not found in {self.media_root}.')
            return []

        data = source.read_bytes()
        current = instance.cover_image
        if current and current.storage.exists(current.name):
            with current.storage.open(current.name, 'rb') as current_file:
                if current_file.read() == data:
                    return []

        if not self.dry_run:
            instance.cover_image.save(source.name, ContentFile(data), save=False)
            self.saved_files.append(instance.cover_image.name)
        return ['cover_image']

    def read_custom_code(self, enabled, kind, slug, label):
        """
        Contents of the v1 static file css/<slug>.css or js/<slug>.js, '' when the
        project didn't use it or None (keeps the current value) when it's missing.
        """
        if not enabled:
            return ''
        path = self.static_dir / kind / f'{slug}.{kind}'
        if not path.is_file():
            self.warn(f'{label}: custom {kind.upper()} is enabled in v1, but {path} was not found.')
            return None
        return path.read_text(encoding='utf-8')

    def without_jquery(self, code, label):
        if not code:
            return code
        for pattern, replacement in V1_JQUERY_REWRITES:
            code = pattern.sub(replacement, code)
        if JQUERY_CALL.search(code):
            self.warn(f'{label}: the custom JavaScript uses jQuery, which v2 does not load.')
        return code

    def with_shared_project_code(self, code, kind, label):
        """`code` preceded by the v1 file shared by all projects (css/projects.css or js/projects.js)."""
        if code is None:
            return None
        path = self.static_dir / kind / V1_SHARED_PROJECT_FILES[kind]
        if not path.is_file():
            self.warn(f'{label}: uses the v1 fullscreen mode, but {path} was not found.')
            return code
        shared = f'/* v1 {V1_SHARED_PROJECT_FILES[kind]}, shared by all projects (fullscreen mode) */\n{path.read_text(encoding="utf-8").strip()}'
        return f'{shared}\n\n{code}' if code else shared

    def get_v1_font_face(self, label):
        font_dir = self.static_dir / V1_FONT_DIR
        try:
            fonts = {kind: base64.b64encode((font_dir / f'bit5x3.{kind}').read_bytes()).decode() for kind in ('woff2', 'woff')}
        except OSError:
            self.warn(f'{label}: custom font is enabled in v1, but its files were not found in {font_dir}.')
            return ''
        return V1_FONT_FACE.format(**fonts)

    def with_media_image_links(self, text, label):
        """Replaces links to v1 uploaded images (/arquivos/imagens/<slug>/) by the image's address in the media folder."""
        def replace(match):
            path = self.v1_images.get(match['slug'])
            if not path:
                self.warn(f'{label}: links to the v1 image "{match["slug"]}", which is not in the v1 database.')
                return match.group()
            self.stats['Links to v1 images (/arquivos/imagens/)', 'rewritten'] += 1
            return f'/media/{quote(path)}'

        return V1_IMAGE_LINK.sub(replace, text or '')

    def check_file_references(self, label, *texts):
        """
        Warns about links to uploaded or static files that v2 doesn't have. Uploads
        found in --media-root (when it isn't MEDIA_ROOT) are copied to the same path,
        so their links keep working.
        """
        copy_from_v1 = self.media_root.resolve() != Path(settings.MEDIA_ROOT).resolve()
        for text in texts:
            for match in FILE_REFERENCE.finditer(text or ''):
                path = posixpath.normpath(unquote(match['path']))
                if path.startswith(('/', '..')):
                    self.warn(f'{label}: links to "{match.group()}", which is outside the {match["kind"]} folder.')
                    continue
                if match['kind'] == 'static':
                    if not finders.find(path):
                        self.warn(f'{label}: links to the v1 static file "{path}", which v2 does not have.')
                    continue

                if path in self.copied_references or default_storage.exists(path):
                    continue
                source = self.v1_media_path(path) if copy_from_v1 else None
                if source is None or not source.is_file():
                    self.warn(f'{label}: links to the uploaded file "{path}", which was not found.')
                    continue
                if not self.dry_run:
                    self.saved_files.append(default_storage.save(path, ContentFile(source.read_bytes())))
                self.copied_references.add(path)
                self.stats['Files linked in the content', 'copied'] += 1

    def reset_sequences(self):
        # Objects created with their v1 ID don't advance the ID sequences in PostgreSQL
        with connection.cursor() as cursor:
            for sql in connection.ops.sequence_reset_sql(no_style(), [Tag, Post, Category, Project]):
                cursor.execute(sql)

    # Output

    def warn(self, message):
        self.warnings.append(message)

    def report(self, section, label, created, changed):
        status = 'created' if created else 'updated' if changed else 'unchanged'
        self.stats[section, status] += 1
        if self.verbosity >= 1:
            details = f' ({", ".join(dict.fromkeys(changed))})' if changed and not created else ''
            self.stdout.write(f'{label}: {status}{details}')

    def print_summary(self):
        self.stdout.write('')
        for section in ('Tags', 'Posts', 'Categories', 'Projects'):
            counts = ', '.join(f'{self.stats[section, status]} {status}' for status in ('created', 'updated', 'unchanged'))
            self.stdout.write(f'{section}: {counts}')
        if self.stats['Links to v1 images (/arquivos/imagens/)', 'rewritten']:
            self.stdout.write(f'Links to v1 images (/arquivos/imagens/): {self.stats["Links to v1 images (/arquivos/imagens/)", "rewritten"]} rewritten')
        if self.stats['Files linked in the content', 'copied']:
            self.stdout.write(f'Files linked in the content: {self.stats["Files linked in the content", "copied"]} copied')

        for message in self.warnings:
            self.stderr.write(self.style.WARNING(f'Warning: {message}'))

        if self.dry_run:
            self.stdout.write(self.style.WARNING('Dry run: nothing was saved and no file was copied.'))
        else:
            self.stdout.write(self.style.SUCCESS('Import finished.'))
