import shutil
import tempfile
from io import BytesIO

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from .models import UploadedImage

MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class ImageUploadTests(TestCase):

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    @classmethod
    def setUpTestData(cls):
        cls.staff = get_user_model().objects.create_user('staff', password='test-password', is_staff=True)
        cls.staff.user_permissions.add(Permission.objects.get(codename='add_uploadedimage'))

    def make_image(self):
        output = BytesIO()
        Image.new('RGB', (3000, 1000), 'blue').save(output, format='PNG')
        return SimpleUploadedFile('screenshot.png', output.getvalue(), content_type='image/png')

    def test_requires_permission(self):
        response = self.client.post(reverse('uploads:image'), {'image': self.make_image()})
        self.assertEqual(response.status_code, 403)

    def test_upload(self):
        self.client.force_login(self.staff)
        response = self.client.post(reverse('uploads:image'), {'image': self.make_image()})

        self.assertEqual(response.status_code, 201)
        uploaded = UploadedImage.objects.get()
        self.assertEqual(response.json(), {'url': uploaded.image.url, 'name': 'screenshot.png'})
        self.assertTrue(uploaded.image.name.endswith('.webp'))
        self.assertEqual((uploaded.width, uploaded.height), (1920, 640))

    def test_rejects_files_that_are_not_images(self):
        self.client.force_login(self.staff)
        response = self.client.post(reverse('uploads:image'), {'image': SimpleUploadedFile('notes.txt', b'hello')})

        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())
        self.assertFalse(UploadedImage.objects.exists())
