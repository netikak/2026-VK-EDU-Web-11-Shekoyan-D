from io import BytesIO
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from PIL import Image


User = get_user_model()
PASSWORD = 'copper-coral-cello-72'


class AccountTests(TestCase):
    def signup(self, password=PASSWORD):
        return self.client.post('/signup/', {
            'username': 'new-user', 'email': 'new@example.org', 'first_name': 'Тест',
            'password1': password, 'password2': password,
        })

    def test_signup_creates_profile_and_logs_in(self):
        self.assertRedirects(self.signup(), '/')
        user = User.objects.get(username='new-user')
        self.assertTrue(user.check_password(PASSWORD))
        self.assertEqual(user.profile.user_id, user.pk)
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)

    def test_password_validators_and_bound_fields(self):
        response = self.signup('123')
        self.assertTrue(response.context['form'].errors['password2'])
        self.assertContains(response, 'new@example.org')
        self.assertFalse(User.objects.filter(username='new-user').exists())

    def test_login_redirect_and_logout(self):
        user = User.objects.create_user('member', password=PASSWORD)
        credentials = {'username': user.username, 'password': PASSWORD}
        self.assertRedirects(self.client.post('/login/?next=/hot/', credentials), '/hot/')
        self.assertEqual(self.client.get('/logout/').status_code, 405)
        self.assertRedirects(self.client.post('/logout/', {'next': '/hot/?page=2'}), '/hot/?page=2')
        self.assertNotIn('_auth_user_id', self.client.session)
        self.assertRedirects(self.client.post('/login/', {
            **credentials, 'next': 'https://example.org/',
        }), '/')
        self.assertRedirects(self.client.post('/logout/', {'next': 'https://example.org/'}), '/')

    def test_profile_upload_and_validation(self):
        self.assertRedirects(self.client.get('/profile/'), '/login/?next=/profile/')
        user = User.objects.create_user('member', email='old@example.org')
        self.client.force_login(user)
        with TemporaryDirectory() as directory, override_settings(MEDIA_ROOT=directory):
            data = BytesIO()
            Image.new('RGB', (2, 2)).save(data, 'PNG')
            fields = {'email': 'new@example.org', 'nick': 'Ник'}
            for invalid_file in (
                SimpleUploadedFile('original.png', b'not an image'),
                SimpleUploadedFile('original.gif', data.getvalue()),
                SimpleUploadedFile('original.png', b'0' * (2 * 1024 * 1024 + 1)),
            ):
                invalid = self.client.post('/profile/', {**fields, 'avatar': invalid_file})
                self.assertTrue(invalid.context['form'].errors['avatar'])
                self.assertContains(invalid, 'new@example.org')

            avatar = SimpleUploadedFile('original.png', data.getvalue(), 'image/png')
            self.assertRedirects(self.client.post('/profile/', {**fields, 'avatar': avatar}), '/profile/')
            user.refresh_from_db()
            self.assertEqual((user.email, user.first_name), ('new@example.org', 'Ник'))
            self.assertRegex(user.profile.avatar.name, r'^avatars/[a-f0-9]{32}\.png$')
            self.assertContains(self.client.get('/'), user.profile.avatar.url)
