from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from django.utils import translation
from PIL import Image

from .i18n import get_language_alternates, language_from_host
from .images import optimize_image
from .markdown import render_markdown

LANGUAGE_DOMAINS = {'en': 'example.com', 'pt-br': 'example.com.br'}
ALLOWED_HOSTS = ['example.com', 'www.example.com', 'example.com.br', 'www.example.com.br', 'other.com']


@override_settings(LANGUAGE_DOMAINS=LANGUAGE_DOMAINS, ALLOWED_HOSTS=ALLOWED_HOSTS)
class LanguageFromHostTests(SimpleTestCase):

    def test_each_domain_has_its_language(self):
        self.assertEqual(language_from_host('example.com'), 'en')
        self.assertEqual(language_from_host('example.com.br'), 'pt-br')

    def test_ignores_www_port_and_case(self):
        self.assertEqual(language_from_host('www.Example.com.br:8000'), 'pt-br')

    def test_unknown_hosts_use_the_default_language(self):
        self.assertEqual(language_from_host('other.com'), 'en')


@override_settings(LANGUAGE_DOMAINS=LANGUAGE_DOMAINS, ALLOWED_HOSTS=ALLOWED_HOSTS)
class DomainLocaleMiddlewareTests(TestCase):

    def test_english_domain(self):
        response = self.client.get('/', headers={'host': 'example.com'})
        self.assertEqual(response.headers['Content-Language'], 'en')
        self.assertContains(response, '<html lang="en">')
        self.assertContains(response, 'Hello, welcome!')

    def test_portuguese_domain(self):
        response = self.client.get('/', headers={'host': 'example.com.br'})
        self.assertEqual(response.headers['Content-Language'], 'pt-br')
        self.assertContains(response, '<html lang="pt-br">')
        self.assertContains(response, 'Olá, seja bem-vindo!')

    def test_url_paths_are_translated(self):
        self.assertEqual(self.client.get('/sobre/', headers={'host': 'example.com.br'}).status_code, 200)
        self.assertEqual(self.client.get('/about/', headers={'host': 'example.com.br'}).status_code, 404)
        self.assertEqual(self.client.get('/about/', headers={'host': 'example.com'}).status_code, 200)

    def test_about_page_uses_the_content_of_the_language(self):
        self.assertContains(self.client.get('/about/', headers={'host': 'example.com'}), 'Polytechnic School')
        self.assertContains(self.client.get('/sobre/', headers={'host': 'example.com.br'}), 'Escola Politécnica')

    def test_hreflang_links_point_to_the_other_domain(self):
        response = self.client.get('/about/', headers={'host': 'example.com'})
        self.assertContains(response, '<link rel="alternate" hreflang="pt-br" href="http://example.com.br/sobre/">')
        self.assertContains(response, '<link rel="alternate" hreflang="x-default" href="http://example.com/about/">')


@override_settings(LANGUAGE_DOMAINS=LANGUAGE_DOMAINS, ALLOWED_HOSTS=ALLOWED_HOSTS)
class LanguageAlternatesTests(SimpleTestCase):

    def get_alternates(self, path, host, language, paths=None):
        request = RequestFactory().get(path, headers={'host': host})
        with translation.override(language):
            return {item['code']: item for item in get_language_alternates(request, paths)}

    def test_keeps_port_www_and_query_string(self):
        alternates = self.get_alternates('/contact/?page=2', 'www.example.com:8000', 'en')
        self.assertEqual(alternates['pt-br']['url'], 'http://www.example.com.br:8000/contato/?page=2')
        self.assertEqual(alternates['pt-br']['switch_url'], 'http://www.example.com.br:8000/contato/?page=2&lang_chosen=1')

    def test_drops_the_language_chosen_flag(self):
        alternates = self.get_alternates('/sobre/?lang_chosen=1', 'example.com.br', 'pt-br')
        self.assertEqual(alternates['en']['url'], 'http://example.com/about/')

    def test_unavailable_current_language_stays_in_the_menu(self):
        alternates = self.get_alternates('/blog/1/post/', 'example.com.br', 'pt-br', paths={'en': '/blog/1/post/'})
        self.assertTrue(alternates['en']['is_available'])
        self.assertTrue(alternates['pt-br']['is_current'])
        self.assertFalse(alternates['pt-br']['is_available'])


class MarkdownTests(SimpleTestCase):

    def test_each_line_is_a_paragraph_like_in_the_editor(self):
        self.assertHTMLEqual(render_markdown('First\nSecond\n\nThird'), '<p>First</p><p>Second</p><p>Third</p>')

    def test_tight_lists_are_not_split(self):
        self.assertHTMLEqual(render_markdown('- a\n- b'), '<ul><li>a</li><li>b</li></ul>')

    def test_code_is_highlighted(self):
        html = render_markdown('```python\ndef f():\n    pass\n```')
        self.assertIn('<code class="language-python"><span class="k">def</span>', html)

    def test_tables_are_responsive(self):
        html = render_markdown('| a | b |\n|---|---|\n| 1 | 2 |')
        self.assertIn('<div class="table-responsive"><table class="table">', html)

    def test_raw_html_is_kept(self):
        self.assertIn('<iframe src="https://www.youtube.com/embed/x"></iframe>', render_markdown('<iframe src="https://www.youtube.com/embed/x"></iframe>'))


class OptimizeImageTests(SimpleTestCase):

    def make_image(self, size, format='JPEG', mode='RGB', color='red', **save_kwargs):
        output = BytesIO()
        Image.new(mode, size, color).save(output, format=format, **save_kwargs)
        return SimpleUploadedFile(f'photo.{format.lower()}', output.getvalue(), content_type=f'image/{format.lower()}')

    def test_resizes_and_converts_to_webp(self):
        optimized = optimize_image(self.make_image((4000, 3000)), max_size=1000)
        self.assertEqual(optimized.name, 'photo.webp')
        with Image.open(optimized) as image:
            self.assertEqual(image.format, 'WEBP')
            self.assertEqual(image.size, (1000, 750))

    def test_applies_exif_orientation(self):
        exif = Image.Exif()
        exif[0x0112] = 6  # Rotated 90° clockwise, as many phones save photos
        with Image.open(optimize_image(self.make_image((400, 200), exif=exif))) as image:
            self.assertEqual(image.size, (200, 400))

    def test_keeps_transparency(self):
        with Image.open(optimize_image(self.make_image((100, 100), format='PNG', mode='RGBA', color=(255, 0, 0, 128)))) as image:
            self.assertEqual(image.mode, 'RGBA')

    def test_animated_gifs_are_untouched(self):
        output = BytesIO()
        frames = [Image.new('RGB', (50, 50), color) for color in ('red', 'blue')]
        frames[0].save(output, format='GIF', save_all=True, append_images=frames[1:])
        uploaded = SimpleUploadedFile('animation.gif', output.getvalue(), content_type='image/gif')
        self.assertIs(optimize_image(uploaded), uploaded)


@override_settings(LANGUAGE_DOMAINS=LANGUAGE_DOMAINS, ALLOWED_HOSTS=ALLOWED_HOSTS)
class LoginTests(TestCase):

    def test_login_page_renders_in_the_domain_language(self):
        response = self.client.get(reverse('users:login'), headers={'host': 'example.com.br'})
        self.assertContains(response, 'Entrar')


@override_settings(LANGUAGE_DOMAINS=LANGUAGE_DOMAINS, ALLOWED_HOSTS=ALLOWED_HOSTS)
class HomeSectionsTests(TestCase):

    def create_post(self, title, **kwargs):
        from blog.models import Post, PostTranslation

        post = Post.objects.create(**kwargs)
        PostTranslation.objects.create(post=post, language='en', title=title, content='Content')
        return post

    def create_project(self, slug, title, **kwargs):
        from projects.models import Project, ProjectTranslation

        project = Project.objects.create(slug=slug, **kwargs)
        ProjectTranslation.objects.create(project=project, language='en', title=title, summary='Summary')
        return project

    def test_sections_are_hidden_without_featured_content(self):
        self.create_post('Not featured', published=True)
        self.create_project('not-featured', 'Not featured project', published=True)

        response = self.client.get('/', headers={'host': 'example.com'})
        self.assertNotContains(response, 'id="home-projects"')
        self.assertNotContains(response, 'id="home-posts"')
        self.assertNotContains(response, 'Background photo')

    def test_sections_show_featured_published_content(self):
        self.create_post('Featured post', published=True, featured=True)
        self.create_post('Featured draft', published=False, featured=True)
        self.create_project('featured', 'Featured project', published=True, featured=True)

        response = self.client.get('/', headers={'host': 'example.com'})
        self.assertContains(response, 'id="home-projects"')
        self.assertContains(response, 'Featured project')
        self.assertContains(response, 'id="home-posts"')
        self.assertContains(response, 'Featured post')
        self.assertNotContains(response, 'Featured draft')
        self.assertContains(response, 'Jeff Sheldon')
        self.assertContains(response, 'Émile Perron')

    def test_only_one_section(self):
        self.create_post('Featured post', published=True, featured=True)

        response = self.client.get('/', headers={'host': 'example.com.br'})
        self.assertNotContains(response, 'id="home-projects"')
        self.assertContains(response, 'Publicações em destaque')
        self.assertContains(response, 'Foto em segundo plano desta página por <a href="https://unsplash.com/@emilep')


@override_settings(LANGUAGE_DOMAINS=LANGUAGE_DOMAINS, ALLOWED_HOSTS=ALLOWED_HOSTS)
class CookieConsentTests(TestCase):

    @override_settings(ANALYTICS_ID='G-TEST')
    def test_asks_for_consent_when_analytics_is_configured(self):
        response = self.client.get('/', headers={'host': 'example.com'})
        self.assertContains(response, 'id="cookie-banner"')
        # Analytics is only loaded by main.js after consent
        self.assertNotContains(response, 'googletagmanager')
        self.assertEqual(response.context['cookie_settings'], {'cookieName': 'cookie_consent', 'consent': None, 'analyticsId': 'G-TEST'})

    @override_settings(ANALYTICS_ID='G-TEST')
    def test_remembers_the_choice(self):
        self.client.cookies['cookie_consent'] = 'rejected'
        response = self.client.get('/', headers={'host': 'example.com'})
        self.assertNotContains(response, 'id="cookie-banner"')
        self.assertContains(response, '<a class="dropdown-item active" href="#" data-cookie-consent="rejected">')
        self.assertEqual(response.context['cookie_settings']['consent'], 'rejected')

    @override_settings(ANALYTICS_ID='G-TEST')
    def test_ignores_invalid_values(self):
        self.client.cookies['cookie_consent'] = 'maybe'
        self.assertContains(self.client.get('/', headers={'host': 'example.com'}), 'id="cookie-banner"')

    @override_settings(ANALYTICS_ID=None)
    def test_no_banner_without_optional_cookies(self):
        self.assertNotContains(self.client.get('/', headers={'host': 'example.com'}), 'id="cookie-banner"')


@override_settings(LANGUAGE_DOMAINS=LANGUAGE_DOMAINS, ALLOWED_HOSTS=ALLOWED_HOSTS)
class ContactPageTests(TestCase):

    def test_social_links_dont_use_third_party_widgets(self):
        response = self.client.get('/contact/', headers={'host': 'example.com'})
        self.assertContains(response, 'class="social-link social-link--linkedin"')
        self.assertNotContains(response, 'platform.linkedin.com')
        self.assertNotContains(response, 'platform.twitter.com')

    def test_form_isnt_nested(self):
        response = self.client.get('/contact/', headers={'host': 'example.com'})
        self.assertContains(response, '<form', count=1)
        self.assertContains(response, 'name="csrfmiddlewaretoken"', count=1)
