import json
import shutil
import tempfile
from io import BytesIO
from smtplib import SMTPException
from unittest import mock
from urllib.error import URLError
from urllib.parse import parse_qs

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from django.utils import translation
from PIL import Image

from .i18n import get_language_alternates, language_from_host
from .images import optimize_image
from .markdown import render_markdown
from .models import AboutSection, AboutSectionTranslation

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


@override_settings(
    LANGUAGE_DOMAINS=LANGUAGE_DOMAINS, ALLOWED_HOSTS=ALLOWED_HOSTS, CONTACT_EMAIL='owner@example.com',
    TURNSTILE_SITE_KEY='site-key', TURNSTILE_SECRET_KEY='secret-key',
)
class ContactPageTests(TestCase):
    EN = {'host': 'example.com'}
    PT = {'host': 'example.com.br'}
    form_data = {'name': 'Ada', 'email': 'ada@example.org', 'subject': 'Hello', 'message': 'Nice site!', 'cf-turnstile-response': 'token'}
    TURNSTILE_PASSED = {'success': True, 'error-codes': [], 'action': 'contact', 'hostname': 'example.com'}
    TURNSTILE_ERROR = "Couldn't verify that you're not a robot. Please try again."

    def setUp(self):
        # Cloudflare's Siteverify API, which answers with self.siteverify_result
        self.siteverify_result = dict(self.TURNSTILE_PASSED)
        patcher = mock.patch('base.turnstile.urlopen', side_effect=lambda *args, **kwargs: BytesIO(json.dumps(self.siteverify_result).encode()))
        self.urlopen = patcher.start()
        self.addCleanup(patcher.stop)

    def test_social_links_dont_use_third_party_widgets(self):
        response = self.client.get('/contact/', headers=self.EN)
        self.assertContains(response, 'class="social-link social-link--linkedin"')
        self.assertNotContains(response, 'platform.linkedin.com')
        self.assertNotContains(response, 'platform.twitter.com')

    def test_form_isnt_nested(self):
        response = self.client.get('/contact/', headers=self.EN)
        self.assertContains(response, '<form', count=1)
        self.assertContains(response, 'name="csrfmiddlewaretoken"', count=1)

    def test_sends_the_message_and_redirects(self):
        self.siteverify_result['hostname'] = 'www.example.com'
        response = self.client.post('/contact/', self.form_data, headers={'host': 'www.example.com'})

        self.assertRedirects(response, '/contact/success/', fetch_redirect_response=False)
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.to, ['owner@example.com'])
        self.assertEqual(email.subject, '[Via example.com] Hello')
        self.assertIn('Ada <ada@example.org>', email.body)
        self.assertIn('Nice site!', email.body)
        # Only the owner gets the e-mail, but replies go to the visitor
        self.assertEqual(email.recipients(), ['owner@example.com'])
        self.assertEqual(email.reply_to, ['ada@example.org'])
        self.assertEqual(email.message()['Reply-To'], 'ada@example.org')

    def test_subject_has_the_domain_of_the_language(self):
        self.siteverify_result['hostname'] = 'example.com.br'
        response = self.client.post('/contato/', self.form_data, headers=self.PT)

        self.assertRedirects(response, '/contato/sucesso/', fetch_redirect_response=False)
        self.assertEqual(mail.outbox[0].subject, '[Via example.com.br] Hello')

    def test_line_breaks_are_removed_from_the_subject(self):
        self.client.post('/contact/', {**self.form_data, 'subject': 'Hello\r\nBcc: spam@example.org'}, headers=self.EN)
        self.assertEqual(mail.outbox[0].subject, '[Via example.com] Hello Bcc: spam@example.org')

    def test_invalid_form_shows_the_errors(self):
        response = self.client.post('/contact/', {**self.form_data, 'email': 'not-an-email', 'message': ''}, headers=self.EN)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.context['form'].errors), {'email', 'message'})
        self.assertContains(response, 'Enter a valid email address.')
        self.assertContains(response, 'value="Ada"')
        self.assertEqual(len(mail.outbox), 0)
        # The Turnstile token isn't spent
        self.urlopen.assert_not_called()

    @mock.patch('base.views.EmailMessage.send', side_effect=SMTPException)
    def test_shows_an_error_when_the_email_cant_be_sent(self, _send):
        self.siteverify_result['hostname'] = 'example.com.br'
        with self.assertLogs('base.views', 'ERROR'):
            response = self.client.post('/contato/', self.form_data, headers=self.PT)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Não foi possível enviar a sua mensagem agora.')
        # What the visitor typed isn't lost
        self.assertContains(response, 'Nice site!')

    def test_success_page(self):
        self.assertContains(self.client.get('/contact/success/', headers=self.EN), 'Message sent!')
        response = self.client.get('/contato/sucesso/', headers=self.PT)
        self.assertContains(response, 'Mensagem enviada!')
        self.assertContains(response, '<title>Mensagem enviada - Contato - Daniel Lavedonio de Lima</title>')
        self.assertContains(response, '<meta name="robots" content="noindex">')

    def test_turnstile_widget(self):
        response = self.client.get('/contato/', headers=self.PT)
        self.assertContains(response, 'class="cf-turnstile mb-3" data-sitekey="site-key" data-action="contact" data-language="pt-br"')
        self.assertContains(response, '<script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async defer></script>')

    def test_turnstile_token_is_validated_by_cloudflare(self):
        self.client.post('/contact/', self.form_data, headers=self.EN)

        request = self.urlopen.call_args.args[0]
        self.assertEqual(request.full_url, 'https://challenges.cloudflare.com/turnstile/v0/siteverify')
        self.assertEqual(parse_qs(request.data.decode()), {'secret': ['secret-key'], 'response': ['token']})

    def test_bots_are_blocked(self):
        failures = {
            'challenge failed': {'success': False, 'error-codes': ['invalid-input-response']},
            'token already used': {'success': False, 'error-codes': ['timeout-or-duplicate']},
            'widget of another form': {'action': 'login'},
            'widget on another site': {'hostname': 'other.com'},
        }
        for case, result in failures.items():
            with self.subTest(case):
                self.siteverify_result = {**self.TURNSTILE_PASSED, **result}
                response = self.client.post('/contact/', self.form_data, headers=self.EN)

                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.context['form'].non_field_errors(), [self.TURNSTILE_ERROR])
                self.assertContains(response, 'Nice site!')
                self.assertEqual(len(mail.outbox), 0)

    def test_missing_turnstile_token(self):
        data = {**self.form_data, 'cf-turnstile-response': ''}
        response = self.client.post('/contato/', data, headers=self.PT)

        self.assertContains(response, 'Não foi possível verificar que você não é um robô.')
        self.urlopen.assert_not_called()
        self.assertEqual(len(mail.outbox), 0)

    def test_blocks_the_form_when_cloudflare_cant_be_reached(self):
        self.urlopen.side_effect = URLError('timed out')
        with self.assertLogs('base.turnstile', 'ERROR'):
            response = self.client.post('/contact/', self.form_data, headers=self.EN)

        self.assertEqual(response.context['form'].non_field_errors(), [self.TURNSTILE_ERROR])
        self.assertEqual(len(mail.outbox), 0)

    def test_logs_a_wrong_secret_key(self):
        self.siteverify_result = {'success': False, 'error-codes': ['invalid-input-secret']}
        with self.assertLogs('base.turnstile', 'ERROR'):
            self.client.post('/contact/', self.form_data, headers=self.EN)
        self.assertEqual(len(mail.outbox), 0)

    def test_turnstile_test_keys_only_work_in_development(self):
        # What Cloudflare answers for the test secret key: no action and the hostname of another site
        self.siteverify_result = {'success': True, 'error-codes': [], 'hostname': 'example.com', 'metadata': {'result_with_testing_key': True}}

        response = self.client.post('/contato/', self.form_data, headers=self.PT)
        self.assertEqual(response.context['form'].non_field_errors(), ['Não foi possível verificar que você não é um robô. Tente novamente.'])
        self.assertEqual(len(mail.outbox), 0)

        with self.settings(DEBUG=True):
            response = self.client.post('/contato/', self.form_data, headers=self.PT)
        self.assertRedirects(response, '/contato/sucesso/', fetch_redirect_response=False)
        self.assertEqual(len(mail.outbox), 1)


ABOUT_MEDIA_ROOT = tempfile.mkdtemp()


def make_image(name='photo.png', size=(3000, 2000)):
    output = BytesIO()
    Image.new('RGB', size, 'green').save(output, format='PNG')
    return SimpleUploadedFile(name, output.getvalue(), content_type='image/png')


@override_settings(LANGUAGE_DOMAINS=LANGUAGE_DOMAINS, ALLOWED_HOSTS=ALLOWED_HOSTS, MEDIA_ROOT=ABOUT_MEDIA_ROOT)
class AboutSectionTests(TestCase):
    EN = {'host': 'example.com'}
    PT = {'host': 'example.com.br'}

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(ABOUT_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    @classmethod
    def setUpTestData(cls):
        cls.staff = get_user_model().objects.create_user('staff', password='test-password', is_staff=True)
        cls.staff.user_permissions.add(*Permission.objects.filter(content_type__app_label='base'))
        cls.reader = get_user_model().objects.create_user('reader', password='test-password')

    def create_section(self, slug, order, translations):
        section = AboutSection.objects.create(slug=slug, order=order, image=make_image(f'{slug}.png', (40, 30)))
        for language, title in translations.items():
            AboutSectionTranslation.objects.create(section=section, language=language, title=title, content=f'Text of **{title}**')
        return section

    def form_data(self, **extra):
        data = {
            'order': '',
            'slug': '',
            'translation_en-enabled': 'on',
            'translation_en-title': 'Hobbies',
            'translation_en-content': 'Trains and *more*.',
            'translation_en-image_caption': 'A model railway.',
        }
        data.update(extra)
        return data

    def test_migration_created_the_sections_of_the_old_page(self):
        sections = AboutSection.objects.prefetch_related('translations')
        self.assertEqual([section.slug for section in sections], ['about-me', 'education', 'career', 'projects', 'hiring'])
        for section in sections:
            self.assertEqual(section.available_languages, ['en', 'pt-br'])
            self.assertTrue(section.image.name.startswith('about/'))

    def test_sections_are_shown_in_order_with_the_sidebar(self):
        AboutSection.objects.filter(slug='hiring').update(order=0)
        content = self.client.get('/about/', headers=self.EN).content.decode()

        self.assertLess(content.index('id="hiring"'), content.index('id="about-me"'))
        self.assertLess(content.index('href="#hiring"'), content.index('href="#about-me"'))

    def test_markdown_picture_and_caption(self):
        section = self.create_section('hobbies', 60, {'en': 'Hobbies'})
        AboutSectionTranslation.objects.filter(section=section).update(image_caption='A model railway.')

        response = self.client.get('/about/', headers=self.EN)
        self.assertContains(response, '<strong>Hobbies</strong>', html=True)
        self.assertContains(response, f'<img src="{section.image.url}" width="40" height="30" alt="" loading="lazy">', html=True)
        self.assertContains(response, '<figcaption>A model railway.</figcaption>', html=True)

    def test_section_only_in_another_language(self):
        self.create_section('so-em-portugues', 60, {'pt-br': 'Só em português'})

        response = self.client.get('/about/', headers=self.EN)
        self.assertContains(response, '<article id="so-em-portugues" class="about-article" lang="pt-br">')
        self.assertContains(response, 'Só em português')

    def test_edit_buttons_are_only_shown_to_editors(self):
        section = AboutSection.objects.get(slug='career')
        self.assertNotContains(self.client.get('/about/', headers=self.EN), f'/about/sections/edit/{section.pk}/')

        self.client.force_login(self.staff)
        response = self.client.get('/about/', headers=self.EN)
        self.assertContains(response, f'/about/sections/edit/{section.pk}/')
        self.assertContains(response, '/about/sections/new/')
        self.assertContains(self.client.get('/sobre/', headers=self.PT), f'/sobre/secoes/editar/{section.pk}/')

    def test_editor_requires_permission(self):
        response = self.client.get('/about/sections/new/', headers=self.EN)
        self.assertRedirects(response, '/accounts/login/?next=/about/sections/new/', fetch_redirect_response=False)

        self.client.force_login(self.reader)
        self.assertEqual(self.client.get('/about/sections/new/', headers=self.EN).status_code, 403)

    def test_create_section(self):
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get('/about/sections/new/', headers=self.EN).context['form']['order'].value(), 60)

        response = self.client.post('/about/sections/new/', self.form_data(order='60', image=make_image()), headers=self.EN)

        section = AboutSection.objects.get(slug='hobbies')
        self.assertRedirects(response, '/about/#hobbies', fetch_redirect_response=False)
        self.assertEqual(section.available_languages, ['en'])
        self.assertEqual(section.translation.image_caption, 'A model railway.')
        # Resized and converted, like the other uploads
        self.assertTrue(section.image.name.endswith('.webp'))
        self.assertEqual((section.image_width, section.image_height), (1200, 800))

    def test_picture_is_required(self):
        self.client.force_login(self.staff)
        response = self.client.post('/about/sections/new/', self.form_data(order='60'), headers=self.EN)

        self.assertEqual(response.status_code, 200)
        self.assertIn('image', response.context['form'].errors)
        self.assertFalse(AboutSection.objects.filter(slug='hobbies').exists())

    def test_generated_slug_is_unique(self):
        self.client.force_login(self.staff)
        self.client.post('/about/sections/new/', self.form_data(**{'order': '60', 'image': make_image(), 'translation_en-title': 'Career'}), headers=self.EN)
        self.assertTrue(AboutSection.objects.filter(slug='career-2').exists())

    def test_edit_keeps_the_picture(self):
        section = self.create_section('hobbies', 60, {'en': 'Hobbies'})
        image = section.image.name
        self.client.force_login(self.staff)

        response = self.client.post(f'/about/sections/edit/{section.pk}/', self.form_data(**{
            'order': '35',
            'slug': 'hobbies',
            'translation_en-title': 'Free time',
            'translation_pt-br-enabled': 'on',
            'translation_pt-br-title': 'Trabalho',
            'translation_pt-br-content': 'Texto',
        }), headers=self.EN)

        self.assertRedirects(response, '/about/#hobbies', fetch_redirect_response=False)
        section.refresh_from_db()
        self.assertEqual(section.image.name, image)
        self.assertEqual(section.order, 35)
        self.assertEqual(section.get_translation('en').title, 'Free time')
        self.assertEqual(section.get_translation('pt-br').title, 'Trabalho')

    def slugs(self):
        return list(AboutSection.objects.values_list('slug', flat=True))

    def test_move_section(self):
        section = AboutSection.objects.get(slug='career')
        self.client.force_login(self.staff)

        response = self.client.post(f'/about/sections/move/{section.pk}/', {'direction': 'up'}, headers=self.EN)
        self.assertRedirects(response, '/about/#career', fetch_redirect_response=False)
        self.assertEqual(self.slugs(), ['about-me', 'career', 'education', 'projects', 'hiring'])

        self.client.post(f'/about/sections/move/{section.pk}/', {'direction': 'down'}, headers=self.EN)
        self.client.post(f'/about/sections/move/{section.pk}/', {'direction': 'down'}, headers=self.EN)
        self.assertEqual(self.slugs(), ['about-me', 'education', 'projects', 'career', 'hiring'])
        self.assertEqual(list(AboutSection.objects.values_list('order', flat=True)), [10, 20, 30, 40, 50])

    def test_move_untangles_sections_with_the_same_order(self):
        AboutSection.objects.update(order=0)
        section = AboutSection.objects.get(slug='hiring')
        self.client.force_login(self.staff)

        self.client.post(f'/about/sections/move/{section.pk}/', {'direction': 'up'}, headers=self.EN)
        self.assertEqual(self.slugs(), ['about-me', 'education', 'career', 'hiring', 'projects'])

    def test_first_and_last_sections_stay_in_place(self):
        self.client.force_login(self.staff)
        first, last = AboutSection.objects.get(slug='about-me'), AboutSection.objects.get(slug='hiring')

        self.client.post(f'/about/sections/move/{first.pk}/', {'direction': 'up'}, headers=self.EN)
        self.client.post(f'/about/sections/move/{last.pk}/', {'direction': 'down'}, headers=self.EN)
        self.assertEqual(self.slugs(), ['about-me', 'education', 'career', 'projects', 'hiring'])

        # The buttons that would do nothing are disabled
        response = self.client.get('/about/', headers=self.EN)
        self.assertContains(response, 'value="up" title="Move up" aria-label="Move up" disabled', count=1)
        self.assertContains(response, 'value="down" title="Move down" aria-label="Move down" disabled', count=1)

    def test_move_requires_permission_and_a_direction(self):
        section = AboutSection.objects.get(slug='career')
        url = f'/about/sections/move/{section.pk}/'

        self.client.force_login(self.reader)
        self.assertEqual(self.client.post(url, {'direction': 'up'}, headers=self.EN).status_code, 403)

        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(url, headers=self.EN).status_code, 405)
        self.assertEqual(self.client.post(url, {'direction': 'left'}, headers=self.EN).status_code, 400)
        self.assertEqual(self.slugs(), ['about-me', 'education', 'career', 'projects', 'hiring'])

    def test_delete_section(self):
        section = AboutSection.objects.get(slug='hiring')
        self.client.force_login(self.staff)

        response = self.client.post(f'/about/sections/delete/{section.pk}/', headers=self.EN)
        self.assertRedirects(response, '/about/', fetch_redirect_response=False)
        self.assertFalse(AboutSection.objects.filter(pk=section.pk).exists())
