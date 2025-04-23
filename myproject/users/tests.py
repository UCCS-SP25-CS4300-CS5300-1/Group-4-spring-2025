import os
from io import BytesIO
from pypdf import PdfWriter
from django.test import TestCase, Client
from django.urls import reverse, resolve
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.storage import default_storage
from .forms import UserRegistrationForm, UserLoginForm, ResumeUploadForm
from .models import Resume, get_user_by_email, Profile
from .signals import user_created_callback
from .views import login_view, register_view, logout_view, resume_feedback
from django.utils import timezone
from unittest.mock import patch
import shutil

class UserRegistrationFormTest(TestCase):
    def test_registration_form_valid_data(self):
        form = UserRegistrationForm(data={
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'StrongTestPass123',
            'password2': 'StrongTestPass123',
        })
        self.assertTrue(form.is_valid())

    def test_registration_form_invalid_data(self):
        form = UserRegistrationForm(data={
            'username': '',
            'email': 'test@example.com',
            'password1': 'StrongTestPass123',
            'password2': 'StrongTestPass123',
        })
        self.assertFalse(form.is_valid())

        form = UserRegistrationForm(data={
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'StrongTestPass123',
            'password2': 'DifferentPass123',
        })
        self.assertFalse(form.is_valid())

        form = UserRegistrationForm(data={
            'username': 'testuser',
            'email': 'invalid-email',
            'password1': 'StrongTestPass123',
            'password2': 'StrongTestPass123',
        })
        self.assertFalse(form.is_valid())

class UserLoginFormTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='StrongTestPass123'
        )

    def test_login_form_valid_data(self):
        form = UserLoginForm(data={
            'username': 'testuser',
            'password': 'StrongTestPass123',
        })
        self.assertTrue(form.is_valid())

    def test_login_form_invalid_data(self):
        form = UserLoginForm(data={
            'username': 'testuser',
            'password': 'WrongPassword123',
        })
        self.assertFalse(form.is_valid())

        form = UserLoginForm(data={
            'username': 'nonexistentuser',
            'password': 'StrongTestPass123',
        })
        self.assertFalse(form.is_valid())

class ResumeUploadFormTest(TestCase):
    def test_resume_upload_valid_pdf(self):
        form = ResumeUploadForm(data={})
        form.files['resume'] = SimpleUploadedFile("resume.pdf", b"%PDF-1.4 lorem ipsum", content_type="application/pdf")
        self.assertTrue(form.is_valid())

    def test_resume_upload_invalid_pdf(self):
        form = ResumeUploadForm(data={})
        form.files['resume'] = SimpleUploadedFile("resume.txt", b"lorem ipsum", content_type="text/plain")
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['resume'], ['Only PDF and DOCX files are allowed.'])

    def test_resume_upload_no_file(self):
        form = ResumeUploadForm(data={})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['resume'], ['This field is required.'])

class UserViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        self.logout_url = reverse('logout')
        self.home_url = reverse('index')
        self.profile_url = reverse('profile')
        self.edit_profile_url = reverse('edit_profile')
        self.update_preferences_url = reverse('update_preferences')

        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='StrongTestPass123'
        )

    def test_register_view_GET(self):
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/register.html')

    def test_register_view_POST_valid(self):
        response = self.client.post(self.register_url, {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'NewUserPass123',
            'password2': 'NewUserPass123',
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.profile_url)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_register_view_POST_invalid(self):
        response = self.client.post(self.register_url, {
            'username': '',
            'email': 'newuser@example.com',
            'password1': 'NewUserPass123',
            'password2': 'NewUserPass123',
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/register.html')
        self.assertFalse(User.objects.filter(email='newuser@example.com').exists())

    def test_login_view_GET(self):
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/login.html')

    def test_login_view_POST_valid(self):
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'StrongTestPass123',
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.profile_url)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_login_view_POST_invalid(self):
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'WrongPassword',
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/login.html')
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_logout_view(self):
        self.client.login(username='testuser', password='StrongTestPass123')
        response = self.client.get(self.logout_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.home_url)

        response = self.client.get(self.home_url)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_profile_view(self):
        self.client.login(username='testuser', password='StrongTestPass123')
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/profile.html')
        self.assertEqual(response.context['user'], self.user)
        self.assertTrue('profile' in response.context)
        self.assertEqual(response.context['profile'], self.user.profile)

    def test_profile_view_redirect_unauthenticated(self):
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/users/login/'))

    def test_edit_profile_GET(self):
        self.client.login(username='testuser', password='StrongTestPass123')
        response = self.client.get(self.edit_profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/edit_profile.html')
        self.assertTrue('form' in response.context)

    def test_edit_profile_POST_valid(self):
        self.client.login(username='testuser', password='StrongTestPass123')
        response = self.client.post(self.edit_profile_url, {
            'first_name': 'John',
            'last_name': 'Doe'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.home_url)

        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'John')
        self.assertEqual(self.user.last_name, 'Doe')

    def test_edit_profile_POST_invalid(self):
        self.client.login(username='testuser', password='StrongTestPass123')
        response = self.client.post(self.edit_profile_url, {
            'first_name': 'A' * 100,
            'last_name': 'B' * 100
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/edit_profile.html')
        self.assertTrue('form' in response.context)

    def test_edit_profile_unauthenticated(self):
        response = self.client.get(self.edit_profile_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/accounts/login/') or response.url.startswith('/users/login/'))

    def test_update_preferences_GET(self):
        self.client.login(username='testuser', password='StrongTestPass123')
        response = self.client.get(self.update_preferences_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/update_preferences.html')
        self.assertTrue('form' in response.context)

    def test_update_preference_POST_valid(self):
        self.client.login(username='testuser', password='StrongTestPass123')
        response = self.client.post(self.update_preferences_url, {
            'industry_preference': 'Computer Science',
            'location_preference': 'Colorado',
            'remote_preference': 'True',
            'salary_min_preference': '12000',
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.home_url)

        self.user.refresh_from_db()
        self.assertEqual(self.user.profile.industry_preference, 'Computer Science')
        self.assertEqual(self.user.profile.location_preference, 'Colorado')
        self.assertEqual(self.user.profile.remote_preference, True)
        self.assertEqual(self.user.profile.salary_min_preference, 12000)

    def test_profile_view_shows_ai_status(self):
        self.client.login(username='testuser', password='StrongTestPass123')
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'AI Access Status')
        self.assertContains(response, 'Not Whitelisted')

        self.user.profile.whitelisted_for_ai = True
        self.user.profile.save()
        response = self.client.get(self.profile_url)
        self.assertContains(response, 'Whitelisted')

class ResumeViewTest(TestCase):
    def setUp(self):
        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
        self.client = Client()
        self.uploaded_files = []
        self.user = User.objects.create_user(
            username='testresumeuser',
            email='testresumeuser@example.com',
            password='StrongTestPass123'
        )
        self.client.login(username='testresumeuser', password='StrongTestPass123')
        self.resume_file_content = b"%PDF-1.4 test content"
        self.resume_file = SimpleUploadedFile("resume.pdf", self.resume_file_content, content_type="application/pdf")

    def test_upload_resume_POST_valid(self):
        response = self.client.post(reverse('upload_resume'), {'resume': self.resume_file})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('profile'))
        self.assertTrue(Resume.objects.filter(user=self.user).exists())
        self.uploaded_files.extend(Resume.objects.all())

    @patch('users.views.openai.chat.completions.create', side_effect=Exception("AI Error"))
    @patch('users.views.load_resume_guide', return_value='Mocked guide content')
    @patch('users.views.parse_resume', return_value='Parsed resume text')
    def test_resume_feedback_view_openai_exception(self, mock_parse, mock_load_guide, mock_openai_call):
        resume = Resume.objects.create(user=self.user, resume=self.resume_file)
        self.uploaded_files.append(resume)
        self.user.profile.whitelisted_for_ai = True
        self.user.profile.save()

        url = reverse('resume_feedback', args=[resume.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<h2>Error</h2>")
        self.assertIn("Error generating AI feedback: AI Error", response.content.decode())

        resume.refresh_from_db()

    def test_delete_resume(self):
        resume = Resume.objects.create(user=self.user, resume=self.resume_file)
        self.uploaded_files.append(resume)
        self.assertTrue(Resume.objects.filter(user=self.user, id=resume.id).exists())

        delete_response = self.client.post(reverse('delete_resume'))

        self.assertEqual(delete_response.status_code, 302)
        self.assertRedirects(delete_response, reverse('profile'))
        self.assertFalse(Resume.objects.filter(user=self.user, id=resume.id).exists())

    def tearDown(self):
        for resume in self.uploaded_files:
            if resume.resume and os.path.exists(resume.resume.path):
                try:
                    default_storage.delete(resume.resume.name)
                except Exception as e:
                    pass
        Resume.objects.all().delete()
        User.objects.all().delete()
        Profile.objects.all().delete()
        if os.path.exists(settings.MEDIA_ROOT):
            shutil.rmtree(settings.MEDIA_ROOT)

class UserAuthenticationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.home_url = reverse('index')

        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='StrongTestPass123'
        )

    def test_authenticated_user_sees_username(self):
        self.client.login(username='testuser', password='StrongTestPass123')
        response = self.client.get(self.home_url)
        self.assertContains(response, 'Hello, testuser')

    def test_unauthenticated_user_sees_login_buttons(self):
        response = self.client.get(self.home_url)
        self.assertContains(response, 'Login')
        self.assertContains(response, 'Sign Up')
        self.assertNotContains(response, 'Hello, testuser')

class UserModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='StrongTestPass123'
        )

    def test_get_user_by_email_existing(self):
        user = get_user_by_email('test@example.com')
        self.assertEqual(user, self.user)

    def test_get_user_by_email_nonexistent(self):
        user = get_user_by_email('nonexistent@example.com')
        self.assertIsNone(user)

    def test_user_creation(self):
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertTrue(self.user.check_password('StrongTestPass123'))

    def test_user_string_representation(self):
        self.assertEqual(str(self.user), self.user.username)

    def test_profile_creation(self):
        self.assertTrue(hasattr(self.user, 'profile'))

    def test_whitelisted_for_ai_default(self):
        self.assertFalse(self.user.profile.whitelisted_for_ai)

    def test_profile_str(self):
        self.assertEqual(str(self.user.profile), 'testuser')

class ResumeModelTest(TestCase):
    def setUp(self):
        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)

        self.uploaded_files = []

    def test_resume_upload(self):
        file = SimpleUploadedFile("some_resume.pdf", b"%PDF-1.4 lorem ipsum", content_type="application/pdf")
        resume = Resume.objects.create(resume=file)
        self.uploaded_files.append(resume)

        self.assertTrue(resume.resume.name.startswith('resumes/some_resume'))
        self.assertTrue(resume.resume.name.endswith('.pdf'))
        self.assertTrue(os.path.exists(resume.resume.path))
        self.assertIsNotNone(resume.uploaded_at)
        self.assertEqual(str(resume), "Resume 1")

    def test_resume_str_representation(self):
        file1 = SimpleUploadedFile("resume1.pdf", b"%PDF-1.4 test1", content_type="application/pdf")
        file2 = SimpleUploadedFile("resume2.pdf", b"%PDF-1.4 test2", content_type="application/pdf")

        resume1 = Resume.objects.create(resume=file1)
        resume2 = Resume.objects.create(resume=file2)
        self.uploaded_files.extend([resume1, resume2])

        self.assertEqual(str(resume1), "Resume 1")
        self.assertEqual(str(resume2), "Resume 2")

    def test_resume_upload_time(self):
        file = SimpleUploadedFile("resume.pdf", b"%PDF-1.4 test", content_type="application/pdf")
        resume = Resume.objects.create(resume=file)
        self.uploaded_files.append(resume)

        self.assertIsNotNone(resume.uploaded_at)
        self.assertTrue(resume.uploaded_at <= timezone.now())

    def tearDown(self):
        for resume in self.uploaded_files:
            if(resume.resume):
                try:
                    resume.resume.delete(save=False)
                except:
                    pass
        Resume.objects.all().delete()

        try:
            shutil.rmtree(settings.MEDIA_ROOT)
        except:
            pass

class UserSignalsTest(TestCase):
    def test_user_created_callback(self):
        user = User(username='newuser', email='newuser@example.com')
        result = user_created_callback(user)
        self.assertEqual(result, "User newuser was created successfully")

    def test_signal_on_user_creation(self):
        user = User.objects.create_user(
            username='signaluser',
            email='signal@example.com',
            password='SignalPass123'
        )
        self.assertTrue(User.objects.filter(username='signaluser').exists())
        self.assertEqual(user.email, 'signal@example.com')

class UserUrlsTest(TestCase):
    def test_login_url_resolves_to_login_view(self):
        url = reverse('login')
        self.assertEqual(resolve(url).func, login_view)

    def test_register_url_resolves_to_register_view(self):
        url = reverse('register')
        self.assertEqual(resolve(url).func, register_view)

    def test_logout_url_resolves_to_logout_view(self):
        url = reverse('logout')
        self.assertEqual(resolve(url).func, logout_view)

class AdminPanelTest(TestCase):
    def setUp(self):
        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)

        self.client = Client()
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='AdminPass123'
        )
        self.regular_user = User.objects.create_user(
            username='regular',
            email='regular@example.com',
            password='RegularPass123'
        )

        self.client.login(username='admin', password='AdminPass123')

    def test_admin_can_access_admin_panel(self):
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 200)

    def test_admin_can_view_user_list(self):
        response = self.client.get('/admin/auth/user/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'regular')
        self.assertContains(response, 'admin')

    def test_admin_can_edit_user(self):
        response = self.client.get(f'/admin/auth/user/{self.regular_user.id}/change/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'regular')
        self.assertContains(response, 'regular@example.com')

    def test_admin_can_make_user_staff(self):
        self.assertFalse(self.regular_user.is_staff)
        response = self.client.post('/admin/auth/user/', {
            'action': 'make_staff',
            '_selected_action': [self.regular_user.id],
        })
        self.regular_user.refresh_from_db()
        self.assertTrue(self.regular_user.is_staff)

    def test_admin_can_make_user_inactive(self):
        self.assertTrue(self.regular_user.is_active)
        response = self.client.post('/admin/auth/user/', {
            'action': 'make_inactive',
            '_selected_action': [self.regular_user.id],
        })
        self.regular_user.refresh_from_db()
        self.assertFalse(self.regular_user.is_active)

    def test_regular_user_cannot_access_admin(self):
        self.client.logout()
        self.client.login(username='regular', password='RegularPass123')
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 302)

    def test_admin_can_view_resumes(self):
        resume = Resume.objects.create(
            resume=SimpleUploadedFile("test_resume.pdf", b"%PDF-1.4 test content", content_type="application/pdf")
        )
        response = self.client.get('/admin/users/resume/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'test_resume.pdf')

    def tearDown(self):
        for resume in Resume.objects.all():
            if(resume.resume):
                try:
                    resume.resume.delete(save=False)
                except:
                    pass
        Resume.objects.all().delete()
        User.objects.all().delete()
        Profile.objects.all().delete()

        try:
            shutil.rmtree(settings.MEDIA_ROOT)
        except:
            pass

class UserAdminTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='AdminPass123'
        )
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='User1Pass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='User2Pass123'
        )
        self.client.login(username='admin', password='AdminPass123')

    def test_whitelist_for_ai_action(self):
        self.assertFalse(self.user1.profile.whitelisted_for_ai)
        response = self.client.post('/admin/auth/user/', {
            'action': 'whitelist_for_ai',
            '_selected_action': [self.user1.id],
        })
        self.user1.profile.refresh_from_db()
        self.assertTrue(self.user1.profile.whitelisted_for_ai)

    def test_remove_ai_whitelist_action(self):
        self.user1.profile.whitelisted_for_ai = True
        self.user1.profile.save()

        response = self.client.post('/admin/auth/user/', {
            'action': 'remove_ai_whitelist',
            '_selected_action': [self.user1.id],
        })
        self.user1.profile.refresh_from_db()
        self.assertFalse(self.user1.profile.whitelisted_for_ai)

    def test_cannot_remove_superuser_whitelist(self):
        response = self.client.post('/admin/auth/user/', {
            'action': 'remove_ai_whitelist',
            '_selected_action': [self.admin_user.id],
        })
        self.admin_user.profile.refresh_from_db()
        self.assertTrue(self.admin_user.profile.whitelisted_for_ai)

    def test_superuser_whitelisted_for_ai(self):
        self.assertTrue(self.admin_user.profile.whitelisted_for_ai)

class ResumePrivacyTest(TestCase):
    def setUp(self):
        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)

        self.client = Client()
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='StrongTestPass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='StrongTestPass123'
        )
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='AdminPass123'
        )

        self.resume_file = SimpleUploadedFile(
            "test_resume.pdf",
            b"%PDF-1.4 test resume content",
            content_type="application/pdf"
        )
        self.resume = Resume.objects.create(
            user=self.user1,
            resume=self.resume_file
        )

        self.uploaded_files = [self.resume]

    def test_user_can_only_see_own_resume(self):
        self.client.login(username='user1', password='StrongTestPass123')
        response = self.client.get(reverse('view_resume', args=[self.resume.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')

        self.client.logout()
        self.client.login(username='user2', password='StrongTestPass123')
        response = self.client.get(reverse('view_resume', args=[self.resume.id]))
        self.assertEqual(response.status_code, 404)

    def test_admin_can_access_any_resume(self):
        self.client.login(username='admin', password='AdminPass123')
        response = self.client.get(reverse('view_resume', args=[self.resume.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')

    def test_unauthenticated_user_cannot_access_resume(self):
        response = self.client.get(reverse('view_resume', args=[self.resume.id]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue('/users/login/' in response.url)

    def test_profile_only_shows_user_resumes(self):
        user2_resume = Resume.objects.create(
            user=self.user2,
            resume=SimpleUploadedFile(
                "user2_resume.pdf",
                b"%PDF-1.4 user2 resume content",
                content_type="application/pdf"
            )
        )
        self.uploaded_files.append(user2_resume)

        self.client.login(username='user1', password='StrongTestPass123')
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['latest_resume'], self.resume)

        self.client.logout()
        self.client.login(username='user2', password='StrongTestPass123')
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['latest_resume'], user2_resume)

    def tearDown(self):
        for resume in self.uploaded_files:
            if(resume.resume):
                try:
                    resume.resume.delete(save=False)
                except:
                    pass
        Resume.objects.all().delete()
        User.objects.all().delete()

        try:
            shutil.rmtree(settings.MEDIA_ROOT)
        except:
            pass

class AIFeatureAccessTest(TestCase):
    def setUp(self):
        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
        self.client = Client()
        self.uploaded_files = []
        self.pdf_content = b"%PDF-1.3\nTest PDF content"
        self.resume_file = SimpleUploadedFile("resume.pdf", self.pdf_content, content_type="application/pdf")

        self.regular_user = User.objects.create_user(
            username='regularuser',
            email='regular@example.com',
            password='StrongTestPass123'
        )
        Profile.objects.get_or_create(user=self.regular_user)
        self.resume = Resume.objects.create(user=self.regular_user, resume=self.resume_file)
        self.uploaded_files.append(self.resume)

        self.whitelisted_user = User.objects.create_user(
            username='whitelisteduser',
            email='whitelisted@example.com',
            password='StrongTestPass123'
        )
        profile, _ = Profile.objects.get_or_create(user=self.whitelisted_user)
        profile.whitelisted_for_ai = True
        profile.save()
        self.whitelisted_resume = Resume.objects.create(user=self.whitelisted_user, resume=self.resume_file)
        self.uploaded_files.append(self.whitelisted_resume)

        self.admin_user = User.objects.create_superuser(
            username='adminuser',
            email='admin@example.com',
            password='StrongTestPass123'
        )
        Profile.objects.get_or_create(user=self.admin_user)
        self.admin_resume = Resume.objects.create(user=self.admin_user, resume=self.resume_file)
        self.uploaded_files.append(self.admin_resume)

    @patch('users.views.get_resume_feedback')
    @patch('users.views.parse_resume', return_value='Parsed resume text')
    def test_regular_user_doesnt_get_ai_feedback(self, mock_parse, mock_get_feedback):
        self.client.login(username='regularuser', password='StrongTestPass123')
        url = reverse('resume_feedback', args=[self.resume.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "not currently eligible")
        mock_get_feedback.assert_not_called()

    @patch('users.views.get_resume_feedback', return_value='<p>Mocked AI Feedback</p>')
    @patch('users.views.parse_resume', return_value='Parsed resume text')
    def test_whitelisted_user_gets_ai_feedback(self, mock_parse, mock_get_feedback):
        self.client.login(username='whitelisteduser', password='StrongTestPass123')
        url = reverse('resume_feedback', args=[self.whitelisted_resume.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<p>Mocked AI Feedback</p>")
        mock_get_feedback.assert_called_once()

    @patch('users.views.get_resume_feedback', return_value='<p>Mocked AI Feedback</p>')
    @patch('users.views.parse_resume', return_value='Parsed resume text')
    def test_admin_user_gets_ai_feedback(self, mock_parse, mock_get_feedback):
        self.client.login(username='adminuser', password='StrongTestPass123')
        url = reverse('resume_feedback', args=[self.admin_resume.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<p>Mocked AI Feedback</p>")
        mock_get_feedback.assert_called_once()

    def tearDown(self):
        for resume in self.uploaded_files:
            if resume.resume and os.path.exists(resume.resume.path):
                try:
                    default_storage.delete(resume.resume.name)
                except Exception as e:
                    pass
        Resume.objects.all().delete()
        User.objects.all().delete()
        Profile.objects.all().delete()
        if os.path.exists(settings.MEDIA_ROOT):
            shutil.rmtree(settings.MEDIA_ROOT)

class SecureResumeViewTest(TestCase):
    def setUp(self):
        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)

        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='StrongTestPass123'
        )

        self.resume_file = SimpleUploadedFile(
            "test_resume.pdf",
            b"%PDF-1.4 test resume content",
            content_type="application/pdf"
        )
        self.resume = Resume.objects.create(
            user=self.user,
            resume=self.resume_file
        )

    def test_direct_media_url_not_accessible(self):
        self.client.login(username='testuser', password='StrongTestPass123')

        secure_response = self.client.get(reverse('view_resume', args=[self.resume.id]))
        self.assertEqual(secure_response.status_code, 200)

    def test_nonexistent_resume_returns_404(self):
        self.client.login(username='testuser', password='StrongTestPass123')

        response = self.client.get(reverse('view_resume', args=[9999]))
        self.assertEqual(response.status_code, 404)

    @patch('users.views.PdfReader')
    def test_resume_linked_to_user(self, mock_pdf_reader):
        mock_instance = mock_pdf_reader.return_value
        mock_instance.pages = [type('obj', (object,), {'extract_text': lambda: 'Sample resume text'})]

        self.client.login(username='testuser', password='StrongTestPass123')

        new_file = SimpleUploadedFile(
            "new_resume.pdf",
            b"%PDF-1.4 new resume content",
            content_type="application/pdf"
        )

        response = self.client.post(
            reverse('upload_resume'),
            {'resume': new_file},
            follow=True
        )

        self.assertEqual(response.status_code, 200)

        latest_resume = Resume.objects.latest('uploaded_at')
        self.assertEqual(latest_resume.user, self.user)

    def tearDown(self):
        for resume in Resume.objects.all():
            if(resume.resume):
                try:
                    resume.resume.delete(save=False)
                except:
                    pass
        User.objects.all().delete()
        Resume.objects.all().delete()

        try:
            shutil.rmtree(settings.MEDIA_ROOT)
        except:
            pass
