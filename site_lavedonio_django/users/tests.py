import time
from unittest import mock
from urllib.parse import urlsplit

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase, override_settings

LANGUAGE_DOMAINS = {'en': 'example.com', 'pt-br': 'example.com.br'}
EN = {'host': 'example.com'}
PT = {'host': 'example.com.br'}


def path_of(url):
    parts = urlsplit(url)
    return f'{parts.path}?{parts.query}' if parts.query else parts.path


@override_settings(LANGUAGE_DOMAINS=LANGUAGE_DOMAINS, ALLOWED_HOSTS=['example.com', 'example.com.br'])
class SessionSyncTests(TestCase):
    """Each host has its own cookies, so each one is a separate Client here."""

    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user('daniel', password='test-password', is_staff=True)

    def setUp(self):
        cache.clear()
        self.english, self.portuguese = Client(), Client()

    def log_in_on_english_host(self):
        response = self.english.post('/accounts/login/?next=/blog/', {'username': 'daniel', 'password': 'test-password'}, headers=EN)
        sync_url = response.url
        self.assertTrue(sync_url.startswith('http://example.com.br/accounts/sync/?token='), sync_url)
        return sync_url

    def test_login_also_logs_in_on_the_other_hosts(self):
        sync_url = self.log_in_on_english_host()

        response = self.portuguese.get(path_of(sync_url), headers=PT)
        self.assertEqual(response.url, 'http://example.com/blog/')
        self.assertEqual(int(self.portuguese.session['_auth_user_id']), self.user.pk)
        self.assertEqual(int(self.english.session['_auth_user_id']), self.user.pk)

    def test_logout_also_logs_out_on_the_other_hosts(self):
        self.portuguese.get(path_of(self.log_in_on_english_host()), headers=PT)

        response = self.english.post('/accounts/logout/', headers=EN)
        self.assertTrue(response.url.startswith('http://example.com.br/accounts/sync/?token='))
        self.assertNotIn('_auth_user_id', self.english.session)

        response = self.portuguese.get(path_of(response.url), headers=PT)
        self.assertEqual(response.url, 'http://example.com/')
        self.assertNotIn('_auth_user_id', self.portuguese.session)

    def test_tokens_work_only_once(self):
        sync_url = self.log_in_on_english_host()
        self.portuguese.get(path_of(sync_url), headers=PT)

        self.assertEqual(Client().get(path_of(sync_url), headers=PT).status_code, 403)

    def test_tokens_expire(self):
        sync_url = self.log_in_on_english_host()

        with mock.patch('django.core.signing.time.time', return_value=time.time() + 120):
            self.assertEqual(self.portuguese.get(path_of(sync_url), headers=PT).status_code, 403)
        self.assertNotIn('_auth_user_id', self.portuguese.session)

    def test_tokens_stop_working_when_the_password_changes(self):
        sync_url = self.log_in_on_english_host()
        self.user.set_password('another-password')
        self.user.save()

        self.assertEqual(self.portuguese.get(path_of(sync_url), headers=PT).status_code, 403)

    def test_invalid_tokens(self):
        self.assertEqual(self.portuguese.get('/accounts/sync/?token=invalid', headers=PT).status_code, 403)
        self.assertEqual(self.portuguese.get('/accounts/sync/', headers=PT).status_code, 403)

    @override_settings(LANGUAGE_DOMAINS={})
    def test_single_host(self):
        response = self.english.post('/accounts/login/', {'username': 'daniel', 'password': 'test-password'}, headers=EN)
        self.assertEqual(response.url, 'http://example.com/')
