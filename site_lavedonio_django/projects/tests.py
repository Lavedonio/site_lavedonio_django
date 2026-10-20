from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase, override_settings

from .models import Category, CategoryTranslation, Project, ProjectTranslation

LANGUAGE_DOMAINS = {'en': 'example.com', 'pt-br': 'example.com.br'}
EN = {'host': 'example.com'}
PT = {'host': 'example.com.br'}


def create_project(slug, translations, published=True, **kwargs):
    project = Project.objects.create(slug=slug, published=published, **kwargs)
    for language, title in translations.items():
        ProjectTranslation.objects.create(project=project, language=language, title=title, summary=f'Summary of {title}', content=f'<p>{title}</p>')
    return project


@override_settings(LANGUAGE_DOMAINS=LANGUAGE_DOMAINS, ALLOWED_HOSTS=['example.com', 'example.com.br'])
class ProjectTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.staff = get_user_model().objects.create_user('staff', password='test-password', is_staff=True)
        cls.staff.user_permissions.add(*Permission.objects.filter(content_type__app_label='projects'))

    def test_list_hides_unpublished_projects(self):
        create_project('public', {'en': 'Public project'})
        create_project('draft', {'en': 'Draft project'}, published=False)

        response = self.client.get('/projects/', headers=EN)
        self.assertContains(response, 'Public project')
        self.assertNotContains(response, 'Draft project')
        self.assertEqual(self.client.get('/projects/draft/', headers=EN).status_code, 404)

    def test_featured_projects_are_not_repeated(self):
        create_project('featured', {'en': 'Featured project'}, featured=True)
        create_project('regular', {'en': 'Regular project'})

        response = self.client.get('/projects/', headers=EN)
        self.assertEqual([project.slug for project in response.context['featured_projects']], ['featured'])
        self.assertEqual([project.slug for project in response.context['projects']], ['regular'])

    def test_category_filter(self):
        games = Category.objects.create(slug='games')
        CategoryTranslation.objects.create(category=games, language='pt-br', name='Jogos')
        create_project('snake', {'en': 'Snake'}).categories.add(games)
        create_project('site', {'en': 'Website'})

        response = self.client.get('/projetos/?category=games', headers=PT)
        self.assertContains(response, 'Snake')
        self.assertNotContains(response, 'Website')
        self.assertContains(response, 'Jogos')
        self.assertEqual(self.client.get('/projects/?category=unknown', headers=EN).status_code, 404)

    def test_detail_in_each_language(self):
        create_project('snake', {'en': 'Snake game', 'pt-br': 'Jogo da cobrinha'}, custom_js='console.log("hi");', custom_css='.x{}')

        response = self.client.get('/projects/snake/', headers=EN)
        self.assertContains(response, 'Snake game')
        self.assertContains(response, '<script>console.log("hi");</script>', html=False)
        self.assertContains(response, '<style>.x{}</style>', html=False)
        self.assertContains(self.client.get('/projetos/snake/', headers=PT), 'Jogo da cobrinha')

    def test_create_generates_a_unique_slug(self):
        create_project('my-game', {'en': 'Existing'})
        self.client.force_login(self.staff)

        response = self.client.post('/projects/new/', {
            'published': 'on',
            'status': Project.Status.IN_PROGRESS,
            'slug': '',
            'date_posted': '',
            'translation_en-enabled': 'on',
            'translation_en-title': 'My game',
            'translation_en-summary': 'A game',
            'translation_en-content': '<p>Hi</p>',
        }, headers=EN)

        self.assertRedirects(response, '/projects/my-game-2/', fetch_redirect_response=False)
        self.assertEqual(Project.objects.get(slug='my-game-2').available_languages, ['en'])

    def test_reserved_slugs(self):
        self.client.force_login(self.staff)
        response = self.client.post('/projects/new/', {
            'status': Project.Status.IN_PROGRESS,
            'slug': 'new',
            'translation_en-enabled': 'on',
            'translation_en-title': 'New',
            'translation_en-summary': 'Summary',
        }, headers=EN)
        self.assertContains(response, 'This slug is reserved')
