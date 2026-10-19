"""
Tests of the import_v1_content command, against a small v1 database built with
the v1 schema (from the v1 migrations) in a temporary SQLite file.
"""
import datetime
import shutil
import sqlite3
import tempfile
from io import StringIO
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management import CommandError, call_command
from django.test import TestCase, override_settings

from blog.models import Post, PostTranslation, Tag, TagTranslation
from projects.models import Category, CategoryTranslation, Project, ProjectTranslation

from .markdown import render_markdown

V1_SCHEMA = """
CREATE TABLE "auth_user" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "password" varchar(128) NOT NULL, "username" varchar(150) NOT NULL UNIQUE, "email" varchar(254) NOT NULL);
CREATE TABLE "blog_tag" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "name" varchar(32) NOT NULL, "color" varchar(7) NOT NULL, "background_color" varchar(7) NOT NULL);
CREATE TABLE "blog_post" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "title" varchar(128) NOT NULL, "subtitle" varchar(512) NOT NULL, "slug" varchar(128) NOT NULL UNIQUE, "main_image" varchar(100) NOT NULL, "credits" varchar(1024) NOT NULL, "featured" bool NOT NULL, "published" bool NOT NULL, "date_posted" datetime NOT NULL, "last_updated" datetime NOT NULL, "date_posted_year_month" date NOT NULL, "content" text NOT NULL, "author_id" integer NULL REFERENCES "auth_user" ("id"));
CREATE TABLE "blog_post_tags" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "post_id" integer NOT NULL REFERENCES "blog_post" ("id"), "tag_id" integer NOT NULL REFERENCES "blog_tag" ("id"));
CREATE TABLE "projects_category" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "name" varchar(32) NOT NULL, "abbreviation" varchar(32) NOT NULL);
CREATE TABLE "projects_project" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "title" varchar(64) NOT NULL, "slug" varchar(32) NOT NULL UNIQUE, "featured" bool NOT NULL, "dark_background" bool NOT NULL, "published" bool NOT NULL, "main_image" varchar(100) NOT NULL, "description" varchar(128) NOT NULL, "credits" varchar(1024) NOT NULL, "date_posted" datetime NOT NULL, "last_updated" datetime NOT NULL, "content" text NOT NULL, "fix_autoscale" bool NOT NULL, "custom_font" bool NOT NULL, "custom_css" bool NOT NULL, "custom_js" bool NOT NULL);
CREATE TABLE "projects_project_categories" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "project_id" integer NOT NULL REFERENCES "projects_project" ("id"), "category_id" integer NOT NULL REFERENCES "projects_category" ("id"));
CREATE TABLE "file_tools_imageupload" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "name" varchar(128) NOT NULL, "slug" varchar(128) NOT NULL UNIQUE, "image_upload" varchar(100) NOT NULL, "resize_image" bool NOT NULL, "max_size" integer NOT NULL, "description" varchar(128) NOT NULL, "created_at" datetime NOT NULL, "updated_at" datetime NOT NULL);
"""

# v1 post written in an HTML textarea: CRLF line endings, a blank line followed by
# indented HTML (a code block in Markdown) and a <pre> with a blank line
V1_POST_CONTENT = (
    '<div class="post">\r\n'
    '    <p>Primeiro parágrafo, com "aspas".</p>\r\n'
    '\r\n'
    '    <p>Segundo parágrafo -- com <img src="/media/images/grafico.png"></p>\r\n'
    '\r\n'
    '    <pre><code>linha 1\r\n'
    '\r\n'
    'linha 3</code></pre>\r\n'
    '</div>'
)

PROJECT_CSS = '#game { color: red; }\n'
PROJECT_JS = 'console.log("pong");\n'
UTC = datetime.timezone.utc


class V1Fixture:
    """A v1 database plus the v1 media and static folders, in a temporary folder."""

    def __init__(self):
        self.root = Path(tempfile.mkdtemp())
        self.database = self.root / 'v1.sqlite3'
        self.media_root = self.root / 'v1_media'
        self.static_dir = self.root / 'v1_static'

        self.write(self.media_root / 'posts' / 'capa.jpg', b'v1 post cover')
        self.write(self.media_root / 'projects' / 'pong.png', b'v1 project cover')
        self.write(self.media_root / 'images' / 'grafico.png', b'v1 article image')
        self.write(self.media_root / 'images' / 'Site homepage.jpg', b'v1 uploaded screenshot')
        self.write(self.static_dir / 'css' / 'pong.css', PROJECT_CSS.encode())
        self.write(self.static_dir / 'js' / 'pong.js', PROJECT_JS.encode())
        self.write(self.static_dir / 'fonts' / 'bit5x3' / 'bit5x3.woff2', b'woff2 font')
        self.write(self.static_dir / 'fonts' / 'bit5x3' / 'bit5x3.woff', b'woff font')

        with closing_connection(self.database) as db:
            db.executescript(V1_SCHEMA)
            db.executemany('INSERT INTO auth_user VALUES (?, ?, ?, ?)', [
                (1, '!', 'daniel', 'daniel@example.com'),
                (2, '!', 'guest', 'guest@example.com'),
            ])
            db.executemany('INSERT INTO blog_tag VALUES (?, ?, ?, ?)', [
                (1, 'Python', '#FFFFFF', '#3776AB'),
                (2, 'Engenharia de Dados', '#000000', '#FFD43B'),
            ])
            db.executemany('INSERT INTO blog_post VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', [
                (1, 'Olá mundo', 'O primeiro post', 'ola-mundo', 'posts/capa.jpg', 'Foto de <a href="https://example.com">Fulano</a>',
                 True, True, '2021-12-10 23:38:00', '2022-01-05 10:00:00.123456', '2021-12-01', V1_POST_CONTENT, 1),
                (2, 'Rascunho', 'S' * 400, 'rascunho', 'default_post_img.jpg', '',
                 False, False, '2022-03-01 12:00:00', '2022-03-01 12:00:00', '2022-03-01', '<p>Texto</p>', 2),
            ])
            db.executemany('INSERT INTO blog_post_tags (post_id, tag_id) VALUES (?, ?)', [(1, 1), (1, 2)])
            db.executemany('INSERT INTO projects_category VALUES (?, ?, ?)', [
                (1, 'Jogos', 'Games'),
                (2, 'Inteligência Artificial', 'IA'),
            ])
            db.executemany('INSERT INTO projects_project VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', [
                (1, 'Pong', 'pong', True, True, True, 'projects/pong.png', 'O clássico jogo Pong.', 'Ícones de Fulano',
                 '2021-06-01 15:00:00', '2021-07-01 15:00:00', '<canvas id="game"></canvas>\n\n<p>Use as setas.</p>',
                 True, True, True, True),
                (2, 'Site', 'site', False, False, True, 'default_project_img.jpg', 'Este site.', '',
                 '2020-01-01 00:00:00', '2020-01-01 00:00:00', '<p>Feito com Django <img src="/static/img/logo.svg"></p>',
                 False, False, False, False),
            ])
            db.executemany('INSERT INTO projects_project_categories (project_id, category_id) VALUES (?, ?)', [(1, 1), (1, 2)])
            db.execute('INSERT INTO file_tools_imageupload VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)', (
                1, 'Homepage', 'site-homepage-a9f23192', 'images/Site homepage.jpg', True, 800, '',
                '2020-04-20 10:00:00', '2020-04-20 10:00:00',
            ))

    @staticmethod
    def write(path, data):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def execute(self, sql, params=()):
        with closing_connection(self.database) as db:
            db.execute(sql, params)

    def cleanup(self):
        shutil.rmtree(self.root, ignore_errors=True)


class closing_connection:
    """sqlite3 connection that commits and closes at the end of the `with` block."""

    def __init__(self, path):
        self.connection = sqlite3.connect(path)

    def __enter__(self):
        return self.connection

    def __exit__(self, *exc_info):
        if exc_info[0] is None:
            self.connection.commit()
        self.connection.close()


class ImportV1ContentTests(TestCase):

    def setUp(self):
        self.v1 = V1Fixture()
        self.addCleanup(self.v1.cleanup)

        # Files saved by v2 go to a temporary MEDIA_ROOT
        self.media_root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.media_root, ignore_errors=True)
        media_settings = override_settings(MEDIA_ROOT=self.media_root)
        media_settings.enable()
        self.addCleanup(media_settings.disable)

        self.author = get_user_model().objects.create_user('daniel', email='daniel@example.com')

    def run_import(self, *args, **options):
        stdout, stderr = StringIO(), StringIO()
        call_command(
            'import_v1_content', str(self.v1.database), '--media-root', str(self.v1.media_root),
            '--static-dir', str(self.v1.static_dir), *args, stdout=stdout, stderr=stderr, **options,
        )
        return stdout.getvalue(), stderr.getvalue()

    def counts(self):
        models = [Post, PostTranslation, Tag, TagTranslation, Project, ProjectTranslation, Category, CategoryTranslation]
        return {model.__name__: model.objects.count() for model in models}

    def test_imports_posts_as_portuguese_translations(self):
        self.run_import()

        post = Post.objects.get(pk=1)
        self.assertEqual(post.available_languages, ['pt-br'])
        self.assertEqual(post.author, self.author)
        self.assertTrue(post.featured)
        self.assertTrue(post.published)
        self.assertEqual(post.date_posted, datetime.datetime(2021, 12, 10, 23, 38, tzinfo=UTC))
        self.assertEqual(post.last_updated, datetime.datetime(2022, 1, 5, 10, 0, 0, 123456, tzinfo=UTC))
        self.assertEqual(post.cover_image.read(), b'v1 post cover')

        translation = post.get_translation('pt-br', fallback=False)
        self.assertEqual(translation.title, 'Olá mundo')
        self.assertEqual(translation.subtitle, 'O primeiro post')
        self.assertEqual(translation.slug, 'ola-mundo')
        self.assertEqual(translation.credits, 'Foto de <a href="https://example.com">Fulano</a>')

        self.assertEqual(sorted(tag.slug for tag in post.tags.all()), ['engenharia-de-dados', 'python'])
        tag = Tag.objects.get(slug='engenharia-de-dados')
        self.assertEqual((tag.color, tag.background_color), ('#000000', '#FFD43B'))
        self.assertEqual(tag.get_translation('pt-br').name, 'Engenharia de Dados')

    def test_post_html_is_rendered_as_in_v1(self):
        self.run_import()

        content = PostTranslation.objects.get(slug='ola-mundo').content
        html = render_markdown(content)

        # Nothing became a Markdown code block or paragraph, and the blank line of the <pre> is kept
        self.assertNotIn('&lt;', html)
        self.assertEqual(html.count('<p>'), 2)
        self.assertIn('"aspas"', html)
        self.assertIn('parágrafo -- com', html)
        self.assertIn('<pre><code>linha 1\n&#10;linha 3</code></pre>', html)

    def test_html_already_rendered_as_is_is_kept(self):
        self.run_import()
        self.assertEqual(PostTranslation.objects.get(slug='rascunho').content, '<p>Texto</p>')

    def test_post_details(self):
        _stdout, stderr = self.run_import()

        draft = PostTranslation.objects.get(slug='rascunho').post
        self.assertFalse(draft.published)
        self.assertFalse(draft.cover_image)  # v1 default image
        self.assertIsNone(draft.author)
        self.assertEqual(len(draft.get_translation('pt-br').subtitle), 300)
        self.assertIn('no v2 user matches the v1 author "guest"', stderr)
        self.assertIn('subtitle has 400 characters and was shortened to 300', stderr)

    def test_author_option_is_used_when_the_v1_author_has_no_v2_user(self):
        editor = get_user_model().objects.create_user('editor')
        self.run_import('--author', 'editor')
        self.assertEqual(PostTranslation.objects.get(slug='rascunho').post.author, editor)
        self.assertEqual(PostTranslation.objects.get(slug='ola-mundo').post.author, self.author)

    def test_imports_projects_with_custom_code_and_font(self):
        self.run_import()

        project = Project.objects.get(slug='pong')
        self.assertEqual(project.pk, 1)
        self.assertEqual(project.available_languages, ['pt-br'])
        self.assertTrue(project.featured)
        self.assertTrue(project.dark_background)
        self.assertTrue(project.fix_autoscale)
        self.assertEqual(project.status, Project.Status.IN_PROGRESS)
        self.assertEqual(project.date_posted, datetime.datetime(2021, 6, 1, 15, 0, tzinfo=UTC))
        self.assertEqual(project.last_updated, datetime.datetime(2021, 7, 1, 15, 0, tzinfo=UTC))
        self.assertEqual(project.cover_image.read(), b'v1 project cover')
        self.assertTrue(project.custom_css.endswith(PROJECT_CSS))
        self.assertIn('font-family: "Bit5x3"', project.custom_css)
        self.assertIn('base64,d29mZjIgZm9udA==', project.custom_css)
        self.assertEqual(project.custom_js, PROJECT_JS)

        translation = project.get_translation('pt-br')
        self.assertEqual(translation.title, 'Pong')
        self.assertEqual(translation.summary, 'O clássico jogo Pong.')
        self.assertEqual(translation.content, '<canvas id="game"></canvas>\n\n<p>Use as setas.</p>')
        self.assertEqual(translation.credits, 'Ícones de Fulano')

        self.assertEqual(sorted(category.slug for category in project.categories.all()), ['games', 'ia'])
        self.assertEqual(Category.objects.get(slug='ia').get_translation('pt-br').name, 'Inteligência Artificial')

        site = Project.objects.get(slug='site')
        self.assertFalse(site.cover_image)
        self.assertEqual((site.custom_css, site.custom_js), ('', ''))

    def test_files_linked_in_the_content(self):
        stdout, stderr = self.run_import()

        self.assertEqual((self.media_root / 'images' / 'grafico.png').read_bytes(), b'v1 article image')
        self.assertIn('Files linked in the content: 1 copied', stdout)
        self.assertIn('links to the v1 static file "img/logo.svg", which v2 does not have', stderr)

    def test_running_again_updates_instead_of_duplicating(self):
        self.run_import()
        counts = self.counts()
        cover = Post.objects.get(pk=1).cover_image.name

        stdout, _stderr = self.run_import()
        self.assertEqual(self.counts(), counts)
        self.assertIn('Posts: 0 created, 0 updated, 2 unchanged', stdout)
        self.assertIn('Projects: 0 created, 0 updated, 2 unchanged', stdout)
        self.assertIn('Tags: 0 created, 0 updated, 2 unchanged', stdout)
        self.assertEqual(Post.objects.get(pk=1).cover_image.name, cover)

        self.v1.execute("UPDATE blog_post SET title = 'Olá, mundo!', last_updated = '2023-01-01 00:00:00' WHERE id = 1")
        self.v1.execute("UPDATE projects_project SET custom_js = 0 WHERE id = 1")
        stdout, _stderr = self.run_import()

        self.assertEqual(self.counts(), counts)
        self.assertIn('Post v1 #1 "Olá, mundo!" → #1: updated (last_updated, title)', stdout)
        post = Post.objects.get(pk=1)
        self.assertEqual(post.get_translation('pt-br').title, 'Olá, mundo!')
        self.assertEqual(post.last_updated, datetime.datetime(2023, 1, 1, tzinfo=UTC))
        self.assertEqual(Project.objects.get(slug='pong').custom_js, '')

    def test_dry_run_changes_nothing(self):
        stdout, _stderr = self.run_import('--dry-run')

        self.assertEqual(set(self.counts().values()), {0})
        self.assertEqual(list(self.media_root.iterdir()), [])
        self.assertIn('Posts: 2 created, 0 updated, 0 unchanged', stdout)
        self.assertIn('Dry run: nothing was saved', stdout)

    def test_existing_v2_content_is_kept(self):
        # A post written in v2 already uses the ID of the first v1 post
        v2_post = Post.objects.create(pk=1)
        PostTranslation.objects.create(post=v2_post, language='en', title='Hello', content='Hi')

        # A tag and a category created in v2, in English
        python = Tag.objects.create(slug='python', color='#111111', background_color='#222222')
        TagTranslation.objects.create(tag=python, language='en', name='Python')
        ai = Category.objects.create(slug='ai')
        CategoryTranslation.objects.create(category=ai, language='en', name='Artificial Intelligence')

        _stdout, stderr = self.run_import('--category-slug', 'IA=ai')

        self.assertEqual(v2_post.translations.get().title, 'Hello')
        imported = PostTranslation.objects.get(slug='ola-mundo').post
        self.assertNotEqual(imported.pk, v2_post.pk)
        self.assertIn('a different v2 object already has this ID', stderr)

        python.refresh_from_db()
        self.assertEqual(python.background_color, '#3776AB')
        self.assertEqual(python.get_translation('en').name, 'Python')
        self.assertEqual(python.get_translation('pt-br').name, 'Python')
        self.assertIn(python, imported.tags.all())

        self.assertEqual(Category.objects.filter(slug='ia').count(), 0)
        self.assertEqual(ai.get_translation('pt-br').name, 'Inteligência Artificial')
        self.assertIn(ai, Project.objects.get(slug='pong').categories.all())

    def test_missing_files_are_reported(self):
        (self.v1.media_root / 'posts' / 'capa.jpg').unlink()
        (self.v1.static_dir / 'js' / 'pong.js').unlink()

        _stdout, stderr = self.run_import()

        self.assertFalse(PostTranslation.objects.get(slug='ola-mundo').post.cover_image)
        self.assertEqual(Project.objects.get(slug='pong').custom_js, '')
        self.assertIn('main image "posts/capa.jpg" not found', stderr)
        self.assertIn('custom JS is enabled in v1, but', stderr)

    def test_rejects_databases_that_are_not_v1(self):
        with closing_connection(self.v1.root / 'other.sqlite3') as db:
            db.execute('CREATE TABLE "auth_user" ("id" integer, "username" text, "email" text)')
            db.execute('CREATE TABLE "blog_tag" ("id" integer, "slug" text, "color" text, "background_color" text)')

        with self.assertRaisesMessage(CommandError, 'has no column name'):
            call_command('import_v1_content', str(self.v1.root / 'other.sqlite3'), stdout=StringIO())
        with self.assertRaisesMessage(CommandError, 'neither a SQLite file nor an alias'):
            call_command('import_v1_content', str(self.v1.root / 'missing.sqlite3'), stdout=StringIO())
        with self.assertRaisesMessage(CommandError, 'is the v2 database'):
            call_command('import_v1_content', 'default', stdout=StringIO())

    def test_links_to_v1_images_point_to_the_imported_files(self):
        self.v1.execute("UPDATE blog_post SET content = ?, credits = ? WHERE id = 2", [
            '<p><a href="https://www.lavedonio.com.br/arquivos/imagens/site-homepage-a9f23192">'
            '<img src="https://lavedonio.com/arquivos/imagens/site-homepage-a9f23192/" alt="Home"></a>'
            '<img src="/arquivos/imagens/apagada-123"></p>',
            'Imagem: <a href="/arquivos/imagens/site-homepage-a9f23192">home</a>',
        ])
        stdout, stderr = self.run_import()

        translation = PostTranslation.objects.get(post_id=2)
        self.assertEqual(translation.content.count('"/media/images/Site%20homepage.jpg"'), 2)
        self.assertIn('<img src="/arquivos/imagens/apagada-123">', translation.content)
        self.assertEqual(translation.credits, 'Imagem: <a href="/media/images/Site%20homepage.jpg">home</a>')
        self.assertEqual((self.media_root / 'images' / 'Site homepage.jpg').read_bytes(), b'v1 uploaded screenshot')
        self.assertIn('Links to v1 images (/arquivos/imagens/): 3 rewritten', stdout)
        self.assertIn('links to the v1 image "apagada-123", which is not in the v1 database', stderr)

    def test_v1_databases_without_uploaded_images(self):
        self.v1.execute('DROP TABLE file_tools_imageupload')
        self.v1.execute("UPDATE blog_post SET content = ? WHERE id = 2", ['<img src="/arquivos/imagens/site-homepage-a9f23192">'])
        stdout, stderr = self.run_import()

        self.assertEqual(PostTranslation.objects.get(post_id=2).content, '<img src="/arquivos/imagens/site-homepage-a9f23192">')
        self.assertIn('links to the v1 image "site-homepage-a9f23192"', stderr)

    def test_main_image_with_another_extension_is_used(self):
        # v1 saved "pong.jpg", but the downloaded file is "pong.png"
        self.v1.execute("UPDATE projects_project SET main_image = 'projects/pong.jpg' WHERE slug = 'pong'")
        self.v1.write(self.v1.media_root / 'posts' / 'capa.txt', b'not an image')
        self.v1.execute("UPDATE blog_post SET main_image = 'posts/capa.gif' WHERE id = 1")
        (self.v1.media_root / 'posts' / 'capa.jpg').rename(self.v1.media_root / 'posts' / 'outra.jpg')
        stdout, stderr = self.run_import()

        pong = Project.objects.get(slug='pong')
        self.assertEqual(pong.cover_image.read(), b'v1 project cover')
        self.assertTrue(pong.cover_image.name.endswith('.png'))
        self.assertIn('main image "projects/pong.jpg" not found, so "projects/pong.png" was used', stderr)

        # Only images are considered
        self.assertFalse(Post.objects.get(pk=1).cover_image)
        self.assertIn('main image "posts/capa.gif" not found in', stderr)

    def test_content_is_converted_to_bootstrap_5(self):
        self.v1.execute("UPDATE blog_post SET content = ? WHERE id = 2", ['<p class="font-weight-bold ml-2">Texto</p>'])
        self.v1.execute("UPDATE projects_project SET content = ? WHERE id = 2", ['<a data-toggle="tab" class="mr-3">Aba</a>'])
        self.run_import()

        self.assertIn('<p class="fw-bold ms-2">Texto</p>', PostTranslation.objects.get(post_id=2).content)
        self.assertEqual(ProjectTranslation.objects.get(project__slug='site').content, '<a data-bs-toggle="tab" class="me-3">Aba</a>')

    def test_fullscreen_projects_get_the_v1_shared_code(self):
        self.v1.write(self.v1.static_dir / 'css' / 'projects.css', b'.fullscreen { position: fixed; }')
        self.v1.write(self.v1.static_dir / 'js' / 'projects.js', b'var lock = document.getElementById("lockpage");')
        self.v1.execute("UPDATE projects_project SET content = ? WHERE slug = 'pong'", ['<a id="lockpage" href="#">Tela cheia</a>'])
        self.run_import()

        pong = Project.objects.get(slug='pong')
        self.assertIn('.fullscreen { position: fixed; }', pong.custom_css)
        self.assertTrue(pong.custom_css.endswith(PROJECT_CSS))
        self.assertTrue(pong.custom_js.startswith('/* v1 projects.js'))
        self.assertTrue(pong.custom_js.endswith(PROJECT_JS))

        site = Project.objects.get(slug='site')
        self.assertEqual((site.custom_css, site.custom_js), ('', ''))


class Bootstrap5ConversionTests(TestCase):

    def test_jquery_tab_events_are_rewritten(self):
        from .management.commands.import_v1_content import Command

        command = Command(stdout=StringIO(), stderr=StringIO())
        command.warnings = []
        command.warn = command.warnings.append
        code = "$('a[data-toggle=\"tab\"]').on('shown.bs.tab', function(e) {\n  var target = $(e.target).attr(\"href\");\n});"
        self.assertEqual(
            command.without_jquery(code, 'Pong'),
            "document.addEventListener('shown.bs.tab', function(e) {\n  var target = e.target.getAttribute('href');\n});",
        )
        self.assertEqual(command.warnings, [])

        command.without_jquery('$(".x").hide();', 'Pong')
        self.assertEqual(command.warnings, ['Pong: the custom JavaScript uses jQuery, which v2 does not load.'])

    def test_renamed_classes_and_attributes(self):
        from .management.commands.import_v1_content import convert_to_bootstrap_5

        html = (
            '<p class="font-italic ml-2 pr-md-3 mx-auto text-center">a</p>'
            '<div class="embed-responsive embed-responsive-16by9"><iframe class="embed-responsive-item" src="x"></iframe></div>'
            "<a class='nav-link' data-toggle=\"tab\" href=\"#b\">b</a><select class=\"custom-select custom-select-sm\"></select>"
        )
        self.assertHTMLEqual(convert_to_bootstrap_5(html), (
            '<p class="fst-italic ms-2 pe-md-3 mx-auto text-center">a</p>'
            '<div class="ratio ratio-16x9"><iframe src="x"></iframe></div>'
            '<a class="nav-link" data-bs-toggle="tab" href="#b">b</a><select class="form-select form-select-sm"></select>'
        ))
