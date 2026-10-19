import datetime

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase, override_settings
from django.utils import timezone

from .models import Post, PostTranslation, Tag, TagTranslation

LANGUAGE_DOMAINS = {'en': 'example.com', 'pt-br': 'example.com.br'}
EN = {'host': 'example.com'}
PT = {'host': 'example.com.br'}


def create_post(translations, published=True, date_posted=None, **kwargs):
    post = Post.objects.create(published=published, date_posted=date_posted or timezone.now(), **kwargs)
    for language, title in translations.items():
        PostTranslation.objects.create(post=post, language=language, title=title, content=f'Content of {title}')
    return post


@override_settings(LANGUAGE_DOMAINS=LANGUAGE_DOMAINS, ALLOWED_HOSTS=['example.com', 'example.com.br'])
class BlogTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.staff = get_user_model().objects.create_user('staff', password='test-password', is_staff=True)
        cls.staff.user_permissions.add(*Permission.objects.filter(content_type__app_label__in=['blog', 'uploads']))
        cls.reader = get_user_model().objects.create_user('reader', password='test-password')


class PostVisibilityTests(BlogTestCase):

    def test_drafts_and_scheduled_posts_are_hidden_from_readers(self):
        create_post({'en': 'Public post'})
        draft = create_post({'en': 'Draft post'}, published=False)
        scheduled = create_post({'en': 'Scheduled post'}, date_posted=timezone.now() + datetime.timedelta(days=1))

        response = self.client.get('/blog/', headers=EN)
        self.assertContains(response, 'Public post')
        self.assertNotContains(response, 'Draft post')
        self.assertNotContains(response, 'Scheduled post')
        self.assertEqual(self.client.get(f'/blog/{draft.pk}/draft-post/', headers=EN).status_code, 404)
        self.assertEqual(self.client.get(f'/blog/{scheduled.pk}/scheduled-post/', headers=EN).status_code, 404)

    def test_editors_see_drafts(self):
        draft = create_post({'en': 'Draft post'}, published=False)
        self.client.force_login(self.staff)

        self.assertContains(self.client.get('/blog/', headers=EN), 'Draft post')
        self.assertEqual(self.client.get(f'/blog/{draft.pk}/draft-post/', headers=EN).status_code, 200)


class PostLanguageTests(BlogTestCase):

    def test_same_post_in_each_language(self):
        post = create_post({'en': 'Hello world', 'pt-br': 'Olá mundo'})

        response = self.client.get(f'/blog/{post.pk}/hello-world/', headers=EN)
        self.assertContains(response, '<h1 class="content-header__title">Hello world</h1>', html=True)
        self.assertContains(response, f'hreflang="pt-br" href="http://example.com.br/blog/{post.pk}/ola-mundo/"')

        response = self.client.get(f'/blog/{post.pk}/ola-mundo/', headers=PT)
        self.assertContains(response, '<h1 class="content-header__title">Olá mundo</h1>', html=True)
        self.assertNotContains(response, 'só está disponível')

    def test_outdated_or_foreign_slug_redirects(self):
        post = create_post({'en': 'Hello world', 'pt-br': 'Olá mundo'})
        self.assertRedirects(self.client.get(f'/blog/{post.pk}/hello-world/', headers=PT), f'/blog/{post.pk}/ola-mundo/', status_code=301)
        self.assertRedirects(self.client.get(f'/blog/{post.pk}/', headers=EN), f'/blog/{post.pk}/hello-world/', status_code=301)

    def test_post_only_in_another_language(self):
        post = create_post({'pt-br': 'Só em português'})

        response = self.client.get(f'/blog/{post.pk}/so-em-portugues/', headers=EN)
        self.assertContains(response, 'This post is only available in Brazilian Portuguese.')
        self.assertContains(response, f'<link rel="canonical" href="http://example.com.br/blog/{post.pk}/so-em-portugues/">')
        self.assertNotContains(response, '<link rel="alternate" hreflang="en"')

        # Listed with a badge in the English blog
        response = self.client.get('/blog/', headers=EN)
        self.assertContains(response, 'Só em português')
        self.assertContains(response, 'PT-BR</span>')

    def test_tags_are_translated(self):
        tag = Tag.objects.create(slug='data')
        TagTranslation.objects.create(tag=tag, language='en', name='Data')
        TagTranslation.objects.create(tag=tag, language='pt-br', name='Dados')
        post = create_post({'en': 'Tagged', 'pt-br': 'Com tag'})
        post.tags.add(tag)

        self.assertContains(self.client.get('/blog/tag/data/', headers=PT), 'Publicações com a tag “Dados”')
        self.assertContains(self.client.get('/blog/tag/data/', headers=EN), 'Posts tagged “Data”')

    def test_archive(self):
        create_post({'en': 'Old post'}, date_posted=timezone.make_aware(datetime.datetime(2024, 5, 10, 12)))
        create_post({'en': 'New post'})

        response = self.client.get('/blog/archive/2024/5/', headers=EN)
        self.assertContains(response, 'Old post')
        self.assertNotContains(response, 'New post')
        self.assertEqual(self.client.get('/blog/arquivo/2024/5/', headers=PT).status_code, 200)
        self.assertEqual(self.client.get('/blog/archive/2024/13/', headers=EN).status_code, 404)


class PostEditorTests(BlogTestCase):

    def form_data(self, **overrides):
        data = {
            'published': 'on',
            'date_posted': '',
            'new_tags': '',
            'translation_en-enabled': 'on',
            'translation_en-title': 'English title',
            'translation_en-subtitle': '',
            'translation_en-slug': '',
            'translation_en-content': 'English **content**',
            'translation_en-credits': '',
            'translation_pt-br-title': '',
            'translation_pt-br-content': '',
        }
        data.update(overrides)
        return data

    def test_requires_permission(self):
        response = self.client.get('/blog/new/', headers=EN)
        self.assertRedirects(response, '/accounts/login/?next=/blog/new/', fetch_redirect_response=False)

        self.client.force_login(self.reader)
        self.assertEqual(self.client.get('/blog/new/', headers=EN).status_code, 403)

    def test_create_post_in_both_languages(self):
        self.client.force_login(self.staff)
        response = self.client.post('/blog/new/', self.form_data(**{
            'new_tags': 'Python, Data Engineering, Python',
            'translation_pt-br-enabled': 'on',
            'translation_pt-br-title': 'Título em português',
            'translation_pt-br-content': 'Conteúdo',
        }), headers=EN)

        post = Post.objects.get()
        self.assertRedirects(response, f'/blog/{post.pk}/english-title/', fetch_redirect_response=False)
        self.assertEqual(post.author, self.staff)
        self.assertEqual(post.available_languages, ['en', 'pt-br'])
        self.assertEqual(post.get_translation('pt-br').slug, 'titulo-em-portugues')
        self.assertEqual(sorted(post.tags.values_list('slug', flat=True)), ['data-engineering', 'python'])
        self.assertAlmostEqual(post.date_posted, timezone.now(), delta=datetime.timedelta(minutes=1))
        self.assertFalse(post.was_updated)

    def test_disabled_language_is_ignored(self):
        self.client.force_login(self.staff)
        self.client.post('/blog/new/', self.form_data(), headers=EN)
        self.assertEqual(Post.objects.get().available_languages, ['en'])

    def test_needs_at_least_one_language(self):
        self.client.force_login(self.staff)
        data = self.form_data()
        del data['translation_en-enabled']
        response = self.client.post('/blog/new/', data, headers=EN)

        self.assertContains(response, 'Include at least one language.')
        self.assertFalse(Post.objects.exists())

    def test_enabled_language_validates_its_fields(self):
        self.client.force_login(self.staff)
        response = self.client.post('/blog/new/', self.form_data(**{'translation_pt-br-enabled': 'on'}), headers=EN)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['translation_forms'][1].errors)
        self.assertFalse(Post.objects.exists())

    def test_disabling_a_language_deletes_its_version(self):
        post = create_post({'en': 'English title', 'pt-br': 'Título'})
        self.client.force_login(self.staff)

        self.client.post(f'/blog/edit/{post.pk}/', self.form_data(), headers=EN)
        self.assertEqual(Post.objects.get().available_languages, ['en'])

    def test_delete(self):
        post = create_post({'en': 'To delete'})
        self.client.force_login(self.staff)

        self.assertRedirects(self.client.post(f'/blog/delete/{post.pk}/', headers=EN), '/blog/', fetch_redirect_response=False)
        self.assertFalse(Post.objects.exists())
        self.assertFalse(PostTranslation.objects.exists())


class PostTranslationTests(TestCase):

    def test_excerpt_and_reading_time(self):
        post = Post.objects.create()
        translation = PostTranslation.objects.create(post=post, language='en', title='Long', content='word ' * 600)
        self.assertEqual(translation.reading_time, 3)
        self.assertEqual(len(translation.excerpt.split()), 40)
