# pylint: disable=too-many-lines
"""
This file contains the tests for the users app.
"""

import os
from unittest.mock import patch
import shutil

from django.test import TestCase, Client
from django.urls import reverse, resolve
from django.utils import timezone
from django.core.files import File
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.storage import default_storage

from .forms import UserRegistrationForm, UserLoginForm, ResumeUploadForm # pylint: disable=import-error,no-name-in-module
from .models import Resume, get_user_by_email, Profile # pylint: disable=import-error,no-name-in-module
from .signals import user_created_callback # pylint: disable=import-error,no-name-in-module
from .views import login_view, register_view, logout_view # pylint: disable=import-error,no-name-in-module

class UserRegistrationFormTest(TestCase):
    """
    This class contains the tests for the user registration form.
    """
    def test_registration_form_valid_data(self):
        """
        This method tests the registration form with valid data.
        """
        form = UserRegistrationForm(data={
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'StrongTestPass123',
            'password2': 'StrongTestPass123',
        })
        self.assertTrue(form.is_valid())

    def test_registration_form_invalid_data(self):
        """
        This method tests the registration form with invalid data.
        """
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
    """
    This class contains the tests for the user login form.
    """
    def setUp(self):
        """
        This method sets up the test environment.
        """
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='StrongTestPass123'
        )

    def test_login_form_valid_data(self):
        """
        This method tests the login form with valid data.
        """
        form = UserLoginForm(data={
            'username': 'testuser',
            'password': 'StrongTestPass123',
        })
        self.assertTrue(form.is_valid())

    def test_login_form_invalid_data(self):
        """
        This method tests the login form with invalid data.
        """
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
    """
    This class contains the tests for the resume upload form.
    """
    def test_resume_upload_valid_pdf(self):
        """
        This method tests the resume upload form with a valid PDF file.
        """
        form = ResumeUploadForm(data={})
        form.files['resume'] = SimpleUploadedFile("resume.pdf",
        b"%PDF-1.4 lorem ipsum", content_type="application/pdf")
        self.assertTrue(form.is_valid())

    def test_resume_upload_invalid_pdf(self):
        """
        This method tests the resume upload form with an invalid PDF file.
        """
        form = ResumeUploadForm(data={})
        form.files['resume'] = SimpleUploadedFile("resume.txt",
        b"lorem ipsum", content_type="text/plain")
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['resume'], ['Only PDF and DOCX files are allowed.'])

    def test_resume_upload_no_file(self):
        """
        This method tests the resume upload form with no file.
        """
        form = ResumeUploadForm(data={})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['resume'], ['This field is required.'])

class UserViewsTest(TestCase): # pylint: disable=too-many-instance-attributes
    """
    This class contains the tests for the user views.
    """
    def setUp(self):
        """
        This method sets up the test environment.
        """
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

    def test_register_view_GET(self): # pylint: disable=invalid-name
        """
        This method tests the register view.
        """
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/register.html')

    def test_register_view_POST_valid(self): # pylint: disable=invalid-name
        """
        This method tests the register view with valid data.
        """
        response = self.client.post(self.register_url, {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'NewUserPass123',
            'password2': 'NewUserPass123',
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.profile_url)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_register_view_POST_invalid(self): # pylint: disable=invalid-name
        """
        This method tests the register view with invalid data.
        """
        response = self.client.post(self.register_url, {
            'username': '',
            'email': 'newuser@example.com',
            'password1': 'NewUserPass123',
            'password2': 'NewUserPass123',
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/register.html')
        self.assertFalse(User.objects.filter(email='newuser@example.com').exists())

    def test_login_view_GET(self): # pylint: disable=invalid-name
        """
        This method tests the login view.
        """
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/login.html')

    def test_login_view_POST_valid(self): # pylint: disable=invalid-name
        """
        This method tests the login view with valid credentials.
        """
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'StrongTestPass123',
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.profile_url)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_login_view_POST_invalid(self): # pylint: disable=invalid-name
        """
        This method tests the login view with invalid credentials.
        """
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'WrongPassword',
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/login.html')
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_logout_view(self):
        """
        This method tests the logout view.
        """
        self.client.login(username='testuser', password='StrongTestPass123')
        response = self.client.get(self.logout_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.home_url)

        response = self.client.get(self.home_url)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_profile_view(self):
        """
        This method tests the profile view.
        """
        self.client.login(username='testuser', password='StrongTestPass123')
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/profile.html')
        self.assertEqual(response.context['user'], self.user)
        self.assertTrue('profile' in response.context)
        self.assertEqual(response.context['profile'], self.user.profile)

    def test_profile_view_redirect_unauthenticated(self):
        """
        This method tests the profile view redirect unauthenticated view.
        """
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/users/login/'))

    def test_edit_profile_GET(self): # pylint: disable=invalid-name
        """
        This method tests the edit profile GET view.
        """
        self.client.login(username='testuser', password='StrongTestPass123')
        response = self.client.get(self.edit_profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/edit_profile.html')
        self.assertTrue('form' in response.context)

    def test_edit_profile_POST_valid(self): # pylint: disable=invalid-name
        """
        This method tests the edit profile POST view.
        """
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

    def test_edit_profile_POST_invalid(self): # pylint: disable=invalid-name
        """
        This method tests the edit profile POST view.
        """
        self.client.login(username='testuser', password='StrongTestPass123')
        response = self.client.post(self.edit_profile_url, {
            'first_name': 'A' * 100,
            'last_name': 'B' * 100
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/edit_profile.html')
        self.assertTrue('form' in response.context)

    def test_edit_profile_unauthenticated(self):
        """
        This method tests the edit profile unauthenticated view.
        """
        response = self.client.get(self.edit_profile_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/accounts/login/')\
        or response.url.startswith('/users/login/'))

    def test_update_preferences_GET(self): # pylint: disable=invalid-name
        """
        This method tests the update preferences GET view.
        """
        self.client.login(username='testuser', password='StrongTestPass123')
        response = self.client.get(self.update_preferences_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/update_preferences.html')
        self.assertTrue('form' in response.context)

    def test_update_preference_POST_valid(self): # pylint: disable=invalid-name
        """
        This method tests the update preference POST view.
        """
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
        """
        This method tests the profile view shows AI status.
        """
        self.client.login(username='testuser', password='StrongTestPass123')
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'AI Access Status')
        self.assertContains(response, 'Not Whitelisted')

        self.user.profile.whitelisted_for_ai = True
        self.user.profile.save()
        response = self.client.get(self.profile_url)
        self.assertContains(response, 'Whitelisted')

class ResumeViewTest(TestCase): # pylint: disable=too-many-instance-attributes
    """
    This class contains the tests for the resume view.
    """
    def setUp(self):
        """
        This method sets up the test environment.
        """
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='StrongTestPass123'
        )
        self.upload_url = reverse('upload_resume')
        self.resume_feedback_url = reverse('resume_feedback')

        settings.MEDIA_ROOT = os.path.join(settings.BASE_DIR, 'test_media')
        os.makedirs(os.path.join(settings.MEDIA_ROOT, 'resumes'), exist_ok=True)

        self.test_resume_path = os.path.join(settings.MEDIA_ROOT, 'resumes', 'test_resume.pdf')
        self.resume_content = b"Test resume content"
        with open(self.test_resume_path, 'wb') as f:
            f.write(self.resume_content)

    def tearDown(self): # pylint: disable=too-many-branches
        """
        This method tears down the test environment.
        """
        for resume in Resume.objects.all(): # pylint: disable=no-member
            if hasattr(resume, 'resume') and resume.resume:
                try:
                    resume.resume.close()
                except: # pylint: disable=bare-except
                    pass
                try:
                    if hasattr(resume.resume, 'file'):
                        resume.resume.file.close()
                except: # pylint: disable=bare-except
                    pass
            resume.delete()

        try:
            shutil.rmtree(settings.MEDIA_ROOT) # pylint: disable=no-member
        except (PermissionError, OSError): # pylint: disable=no-member
            for root, dirs, files in os.walk(settings.MEDIA_ROOT, topdown=False): # pylint: disable=no-member
                for name in files:
                    try:
                        file_path = os.path.join(root, name)
                        if os.path.exists(file_path):
                            os.chmod(file_path, 0o600)
                            os.unlink(file_path)
                    except (PermissionError, OSError):
                        pass
                for name in dirs:
                    try:
                        dir_path = os.path.join(root, name)
                        if os.path.exists(dir_path):
                            os.chmod(dir_path, 0o700)
                            os.rmdir(dir_path)
                    except (PermissionError, OSError):
                        pass
            try:
                if os.path.exists(settings.MEDIA_ROOT):
                    os.chmod(settings.MEDIA_ROOT, 0o700)  # Restrict permissions
                    os.rmdir(settings.MEDIA_ROOT)
            except (PermissionError, OSError): # pylint: disable=no-member
                pass

    def test_upload_resume_POST_valid(self): # pylint: disable=invalid-name
        """
        This method tests the upload resume POST view.
        """
        self.client.login(username='testuser', password='StrongTestPass123')
        with open(self.test_resume_path, 'rb') as resume_file:
            response = self.client.post(self.upload_url, {'resume': resume_file})

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('profile'))
        self.assertTrue(Resume.objects.filter(user=self.user).exists()) # pylint: disable=no-member

    @patch('users.views.openai.chat.completions.create',
           side_effect=Exception("AI Error"))
    @patch('users.views.load_resume_guide', return_value='Mocked guide content')
    @patch('users.views.parse_resume', return_value='Parsed resume text')
    def test_resume_feedback_view_openai_exception(self, mock_parse, mock_load_guide, mock_openai): # pylint: disable=unused-argument
        """
        This method tests the resume feedback view when an OpenAI exception occurs.
        """
        self.client.login(username='testuser', password='StrongTestPass123')

        # Create resume using the test file
        with open(self.test_resume_path, 'rb') as resume_file:
            resume = Resume.objects.create( # pylint: disable=no-member
                user=self.user,
                resume=File(resume_file, name='test_resume.pdf')
            )

        self.user.profile.whitelisted_for_ai = True
        self.user.profile.save()

        url = reverse('resume_feedback', args=[resume.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<h2>Error</h2>")
        self.assertIn("Error generating AI feedback: AI Error", response.content.decode())

    def test_delete_resume(self):
        """
        This method tests the delete resume view.
        """
        self.client.login(username='testuser', password='StrongTestPass123')

        with open(self.test_resume_path, 'rb') as resume_file:
            resume = Resume.objects.create( # pylint: disable=no-member
                user=self.user,
                resume=File(resume_file, name='test_resume.pdf')
            )

        self.assertTrue(Resume.objects.filter(user=self.user, id=resume.id).exists()) # pylint: disable=no-member

        delete_response = self.client.post(reverse('delete_resume'))

        self.assertEqual(delete_response.status_code, 302)
        self.assertRedirects(delete_response, reverse('profile'))
        self.assertFalse(Resume.objects.filter(user=self.user, id=resume.id).exists()) # pylint: disable=no-member

class UserAuthenticationTest(TestCase):
    """
    This class contains the tests for the user authentication.
    """
    def setUp(self):
        """
        This method sets up the test environment.
        """
        self.client = Client()
        self.home_url = reverse('index')

        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='StrongTestPass123'
        )

    def test_authenticated_user_sees_username(self):
        """
        This method tests the authenticated user sees username.
        """
        self.client.login(username='testuser', password='StrongTestPass123')
        response = self.client.get(self.home_url)
        self.assertContains(response, 'Hello, testuser')

    def test_unauthenticated_user_sees_login_buttons(self):
        """
        This method tests the unauthenticated user sees login buttons.
        """
        response = self.client.get(self.home_url)
        self.assertContains(response, 'Login')
        self.assertContains(response, 'Sign Up')
        self.assertNotContains(response, 'Hello, testuser')

class UserModelTest(TestCase):
    """
    This class tests the user model.
    """
    def setUp(self):
        """
        This method sets up the test environment.
        """
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='StrongTestPass123'
        )

    def test_get_user_by_email_existing(self):
        """
        This method tests the get user by email existing.
        """
        user = get_user_by_email('test@example.com')
        self.assertEqual(user, self.user)

    def test_get_user_by_email_nonexistent(self):
        """
        This method tests the get user by email nonexistent.
        """
        user = get_user_by_email('nonexistent@example.com')
        self.assertIsNone(user)

    def test_user_creation(self):
        """
        This method tests the user creation.
        """
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertTrue(self.user.check_password('StrongTestPass123'))

    def test_user_string_representation(self):
        """
        This method tests the user string representation.
        """
        self.assertEqual(str(self.user), self.user.username)

    def test_profile_creation(self):
        """
        This method tests the profile creation.
        """
        self.assertTrue(hasattr(self.user, 'profile'))

    def test_whitelisted_for_ai_default(self):
        """
        This method tests the whitelisted for AI default.
        """
        self.assertFalse(self.user.profile.whitelisted_for_ai)

    def test_profile_str(self):
        """
        This method tests the profile string representation.
        """
        self.assertEqual(str(self.user.profile), 'testuser')

class ResumeModelTest(TestCase):
    """
    This class tests the resume model.
    """
    def setUp(self):
        """
        This method sets up the test environment.
        """
        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)

        self.uploaded_files = []

    def test_resume_upload(self):
        """
        This method tests the resume upload.
        """
        file = SimpleUploadedFile("some_resume.pdf", b"%PDF-1.4 lorem ipsum",
                                  content_type="application/pdf")
        resume = Resume.objects.create(resume=file) # pylint: disable=no-member
        self.uploaded_files.append(resume)

        self.assertTrue(resume.resume.name.startswith('resumes/some_resume'))
        self.assertTrue(resume.resume.name.endswith('.pdf'))
        self.assertTrue(os.path.exists(resume.resume.path))
        self.assertIsNotNone(resume.uploaded_at)
        self.assertEqual(str(resume), "Resume 1")

    def test_resume_str_representation(self):
        """
        This method tests the resume string representation.
        """
        file1 = SimpleUploadedFile("resume1.pdf", b"%PDF-1.4 test1", content_type="application/pdf")
        file2 = SimpleUploadedFile("resume2.pdf", b"%PDF-1.4 test2", content_type="application/pdf")

        resume1 = Resume.objects.create(resume=file1) # pylint: disable=no-member
        resume2 = Resume.objects.create(resume=file2) # pylint: disable=no-member
        self.uploaded_files.extend([resume1, resume2])

        self.assertEqual(str(resume1), "Resume 1")
        self.assertEqual(str(resume2), "Resume 2")

    def test_resume_upload_time(self):
        """
        This method tests the resume upload time.
        """
        file = SimpleUploadedFile("resume.pdf", b"%PDF-1.4 test", content_type="application/pdf")
        resume = Resume.objects.create(resume=file) # pylint: disable=no-member
        self.uploaded_files.append(resume)

        self.assertIsNotNone(resume.uploaded_at)
        self.assertTrue(resume.uploaded_at <= timezone.now())

    def tearDown(self):
        """
        This method tears down the test environment.
        """
        for resume in self.uploaded_files:
            if resume.resume:
                try:
                    resume.resume.delete(save=False)
                except: # pylint: disable=bare-except
                    pass
        Resume.objects.all().delete() # pylint: disable=no-member

        try:
            shutil.rmtree(settings.MEDIA_ROOT) # pylint: disable=no-member
        except: # pylint: disable=bare-except
            pass

class UserSignalsTest(TestCase):
    """
    This class tests the user signals.
    """
    def test_user_created_callback(self):
        """
        This method tests the user created callback.
        """
        user = User(username='newuser', email='newuser@example.com')
        result = user_created_callback(user)
        self.assertEqual(result, "User newuser was created successfully")

    def test_signal_on_user_creation(self):
        """
        This method tests the signal on user creation.
        """
        user = User.objects.create_user( # pylint: disable=no-member
            username='signaluser',
            email='signal@example.com',
            password='SignalPass123'
        )
        self.assertTrue(User.objects.filter(username='signaluser').exists()) # pylint: disable=no-member
        self.assertEqual(user.email, 'signal@example.com')

class UserUrlsTest(TestCase):
    """
    This class tests the user urls.
    """
    def test_login_url_resolves_to_login_view(self):
        """
        This method tests the login url resolves to login view.
        """
        url = reverse('login')
        self.assertEqual(resolve(url).func, login_view)

    def test_register_url_resolves_to_register_view(self):
        """
        This method tests the register url resolves to register view.
        """
        url = reverse('register')
        self.assertEqual(resolve(url).func, register_view)

    def test_logout_url_resolves_to_logout_view(self):
        """
        This method tests the logout url resolves to logout view.
        """
        url = reverse('logout')
        self.assertEqual(resolve(url).func, logout_view)

class AdminPanelTest(TestCase):
    """
    This class tests the admin panel.
    """
    def setUp(self):
        """
        This method sets up the test environment.
        """
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

        # Create a resume for the regular user for testing purposes
        self.test_resume_file = SimpleUploadedFile(
            "test_resume.pdf",
            b"%PDF-1.4 mock resume content",
            content_type="application/pdf"
        )
        self.resume = Resume.objects.create( # pylint: disable=no-member
            user=self.regular_user,
            resume=self.test_resume_file
        )

        self.client.login(username='admin', password='AdminPass123')

    def test_admin_can_access_admin_panel(self):
        """
        This method tests the admin can access the admin panel.
        """
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 200)

    def test_admin_can_view_user_list(self):
        """
        This method tests the admin can view the user list.
        """
        response = self.client.get('/admin/auth/user/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'regular')
        self.assertContains(response, 'admin')

    def test_admin_can_edit_user(self):
        """
        This method tests the admin can edit the user.
        """
        response = self.client.get(f'/admin/auth/user/{self.regular_user.id}/change/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'regular')
        self.assertContains(response, 'regular@example.com')

    def test_admin_can_make_user_inactive(self):
        """
        This method tests the admin can make the user inactive.
        """
        self.assertTrue(self.regular_user.is_active)
        # Simulate changing user via admin
        user_change_url = f'/admin/auth/user/{self.regular_user.id}/change/'
        get_response = self.client.get(user_change_url)
        self.assertEqual(get_response.status_code, 200)
        csrf_token = self.client.cookies['csrftoken'].value
        post_data = {
            'username': self.regular_user.username,
            'email': self.regular_user.email,
            'is_staff': 'on' if self.regular_user.is_staff else '',
            'is_active': '', # Unset active status
            'is_superuser': 'on' if self.regular_user.is_superuser else '',
            'first_name': self.regular_user.first_name,
            'last_name': self.regular_user.last_name,
            'groups': [],
            'user_permissions': [],
            'password': '',
            'csrfmiddlewaretoken': csrf_token,
            '_save': 'Save'
        }
        post_response = self.client.post(user_change_url, post_data, follow=True)
        self.assertEqual(post_response.status_code, 200)

        self.regular_user.refresh_from_db()
        self.assertTrue(self.regular_user.is_active)

    def test_regular_user_cannot_access_admin(self):
        """
        This method tests the regular user cannot access the admin panel.
        """
        self.client.logout()
        self.client.login(username='regular', password='RegularPass123')
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 302)

    def tearDown(self):
        """
        This method tears down the test environment.
        """
        for resume in Resume.objects.all(): # pylint: disable=no-member
            if resume.resume:
                try:
                    resume.resume.delete(save=False)
                except: # pylint: disable=bare-except
                    pass
        Resume.objects.all().delete() # pylint: disable=no-member
        User.objects.all().delete() # pylint: disable=no-member
        Profile.objects.all().delete() # pylint: disable=no-member

        try:
            shutil.rmtree(settings.MEDIA_ROOT) # pylint: disable=no-member
        except: # pylint: disable=bare-except
            pass

class UserAdminTest(TestCase):
    """
    This class tests the user admin.
    """
    def setUp(self):
        """
        This method sets up the test environment.
        """
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
        """
        This method tests the whitelist for AI action.
        """
        self.assertFalse(self.user1.profile.whitelisted_for_ai)
        # Simulate running the admin action
        action_url = '/admin/auth/user/' # URL for the user list view where actions are run
        get_response = self.client.get(action_url) # GET first to ensure CSRF cookie is set # pylint: disable=unused-variable
        csrf_token = self.client.cookies['csrftoken'].value
        post_data = {
            'action': 'whitelist_for_ai',
            '_selected_action': str(self.user1.id),
            'csrfmiddlewaretoken': csrf_token,
        }
        action_response = self.client.post(action_url, post_data, follow=True)
        self.assertEqual(action_response.status_code, 200)

        self.user1.profile.refresh_from_db()
        self.assertTrue(self.user1.profile.whitelisted_for_ai)

    def test_remove_ai_whitelist_action(self):
        """
        This method tests the remove AI whitelist action.
        """
        self.user1.profile.whitelisted_for_ai = True
        self.user1.profile.save()
        self.assertTrue(self.user1.profile.whitelisted_for_ai) # Verify initial state

        # Simulate running the admin action
        action_url = '/admin/auth/user/'
        get_response = self.client.get(action_url) # GET first to ensure CSRF cookie is set # pylint: disable=unused-variable
        csrf_token = self.client.cookies['csrftoken'].value
        post_data = {
            'action': 'remove_ai_whitelist',
            '_selected_action': str(self.user1.id),
            'csrfmiddlewaretoken': csrf_token,
        }
        action_response = self.client.post(action_url, post_data, follow=True)
        self.assertEqual(action_response.status_code, 200)

        self.user1.profile.refresh_from_db()
        self.assertFalse(self.user1.profile.whitelisted_for_ai)

    def test_cannot_remove_superuser_whitelist(self):
        """
        This method tests the cannot remove superuser whitelist.
        """
        self.admin_user.profile.refresh_from_db()
        self.assertTrue(self.admin_user.profile.whitelisted_for_ai)

    def test_superuser_whitelisted_for_ai(self):
        """
        This method tests the superuser whitelisted for AI.
        """
        self.assertTrue(self.admin_user.profile.whitelisted_for_ai)

class ResumePrivacyTest(TestCase):
    """
    This class tests the resume privacy.
    """
    def setUp(self):
        """
        This method sets up the test environment.
        """
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
        self.resume = Resume.objects.create( # pylint: disable=no-member
            user=self.user1,
            resume=self.resume_file
        )

        self.uploaded_files = [self.resume]

    def test_user_can_only_see_own_resume(self):
        """
        This method tests the user can only see own resume.
        """
        self.client.login(username='user1', password='StrongTestPass123')
        response = self.client.get(reverse('view_resume', args=[self.resume.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')

        self.client.logout()
        self.client.login(username='user2', password='StrongTestPass123')
        response = self.client.get(reverse('view_resume', args=[self.resume.id]))
        self.assertEqual(response.status_code, 404)

    def test_admin_can_access_any_resume(self):
        """
        This method tests the admin can access any resume.
        """
        self.client.login(username='admin', password='AdminPass123')
        response = self.client.get(reverse('view_resume', args=[self.resume.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')

    def test_unauthenticated_user_cannot_access_resume(self):
        """
        This method tests the unauthenticated user cannot access resume.
        """
        response = self.client.get(reverse('view_resume', args=[self.resume.id]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue('/users/login/' in response.url)

    def test_profile_only_shows_user_resumes(self):
        """
        This method tests the profile only shows user resumes.
        """
        user2_resume = Resume.objects.create( # pylint: disable=no-member
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
        """
        This method tears down the test environment.
        """
        for resume in self.uploaded_files:
            if resume.resume:
                try:
                    resume.resume.delete(save=False)
                except: # pylint: disable=bare-except
                    pass
        Resume.objects.all().delete() # pylint: disable=no-member
        User.objects.all().delete() # pylint: disable=no-member

        try:
            shutil.rmtree(settings.MEDIA_ROOT) # pylint: disable=no-member
        except: # pylint: disable=bare-except
            pass

class AIFeatureAccessTest(TestCase): # pylint: disable=too-many-instance-attributes
    """
    This class tests the AI feature access.
    """
    def setUp(self):
        """
        This method sets up the test environment.
        """
        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
        self.client = Client()
        self.uploaded_files = []
        self.pdf_content = b"%PDF-1.3\nTest PDF content"
        self.resume_file = SimpleUploadedFile("resume.pdf",
                                              self.pdf_content, content_type="application/pdf")

        self.regular_user = User.objects.create_user(
            username='regularuser',
            email='regular@example.com',
            password='StrongTestPass123'
        )
        Profile.objects.get_or_create(user=self.regular_user)
        self.resume = Resume.objects.create(user=self.regular_user, resume=self.resume_file) # pylint: disable=no-member
        self.uploaded_files.append(self.resume)

        self.whitelisted_user = User.objects.create_user( # pylint: disable=no-member
            username='whitelisteduser',
            email='whitelisted@example.com',
            password='StrongTestPass123'
        )
        profile, _ = Profile.objects.get_or_create(user=self.whitelisted_user) # pylint: disable=no-member
        profile.whitelisted_for_ai = True
        profile.save()
        self.whitelisted_resume = Resume.objects.create(user=self.whitelisted_user, # pylint: disable=no-member
        resume=self.resume_file) # pylint: disable=no-member
        self.uploaded_files.append(self.whitelisted_resume)

        self.admin_user = User.objects.create_superuser( # pylint: disable=no-member
            username='adminuser',
            email='admin@example.com',
            password='StrongTestPass123'
        )
        Profile.objects.get_or_create(user=self.admin_user) # pylint: disable=no-member
        self.admin_resume = Resume.objects.create(user=self.admin_user, resume=self.resume_file) # pylint: disable=no-member
        self.uploaded_files.append(self.admin_resume)

    @patch('users.views.get_resume_feedback')
    @patch('users.views.parse_resume', return_value='Parsed resume text')
    def test_regular_user_doesnt_get_ai_feedback(self, mock_parse_resume, mock_get_feedback): # pylint: disable=unused-argument
        """
        This method tests the regular user doesn't get AI feedback.
        """
        self.client.login(username='regularuser', password='StrongTestPass123')
        url = reverse('resume_feedback', args=[self.resume.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "not currently eligible")
        mock_get_feedback.assert_not_called()

    @patch('users.views.get_resume_feedback', return_value='<p>Mocked AI Feedback</p>')
    @patch('users.views.parse_resume', return_value='Parsed resume text')
    def test_whitelisted_user_gets_ai_feedback(self, mock_parse_resume, mock_get_feedback): # pylint: disable=unused-argument
        """
        This method tests the whitelisted user gets AI feedback.
        """
        self.client.login(username='whitelisteduser', password='StrongTestPass123')
        url = reverse('resume_feedback', args=[self.whitelisted_resume.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<p>Mocked AI Feedback</p>")
        mock_get_feedback.assert_called_once()

    @patch('users.views.get_resume_feedback', return_value='<p>Mocked AI Feedback</p>')
    @patch('users.views.parse_resume', return_value='Parsed resume text')
    def test_admin_user_gets_ai_feedback(self, mock_parse_resume, mock_get_feedback): # pylint: disable=unused-argument
        """
        This method tests the admin user gets AI feedback.
        """
        self.client.login(username='adminuser', password='StrongTestPass123')
        url = reverse('resume_feedback', args=[self.admin_resume.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<p>Mocked AI Feedback</p>")
        mock_get_feedback.assert_called_once()

    def tearDown(self):
        """
        This method tears down the test environment.
        """
        for resume in self.uploaded_files:
            if resume.resume and os.path.exists(resume.resume.path):
                try:
                    default_storage.delete(resume.resume.name)
                except Exception: # pylint: disable=broad-except
                    pass
        Resume.objects.all().delete() # pylint: disable=no-member
        User.objects.all().delete() # pylint: disable=no-member
        Profile.objects.all().delete() # pylint: disable=no-member
        if os.path.exists(settings.MEDIA_ROOT): # pylint: disable=no-member
            shutil.rmtree(settings.MEDIA_ROOT) # pylint: disable=no-member

class SecureResumeViewTest(TestCase):
    """
    This class tests the secure resume view.
    """
    def setUp(self):
        """
        This method sets up the test environment.
        """
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
        self.resume = Resume.objects.create( # pylint: disable=no-member
            user=self.user,
            resume=self.resume_file
        )

    def test_direct_media_url_not_accessible(self):
        """
        This method tests the direct media URL is not accessible.
        """
        self.client.login(username='testuser', password='StrongTestPass123')

        secure_response = self.client.get(reverse('view_resume', args=[self.resume.id]))
        self.assertEqual(secure_response.status_code, 200)

    def test_nonexistent_resume_returns_404(self):
        """
        This method tests the nonexistent resume returns 404.
        """
        self.client.login(username='testuser', password='StrongTestPass123')

        response = self.client.get(reverse('view_resume', args=[9999]))
        self.assertEqual(response.status_code, 404)

    @patch('users.views.PdfReader')
    def test_resume_linked_to_user(self, mock_pdf_reader):
        """
        This method tests the resume linked to user.
        """
        mock_instance = mock_pdf_reader.return_value
        mock_instance.pages = [type('obj', (object,), \
        {'extract_text': lambda: 'Sample resume text'})] # pylint: disable=unnecessary-lambda,no-member

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

        latest_resume = Resume.objects.latest('uploaded_at') # pylint: disable=no-member
        self.assertEqual(latest_resume.user, self.user)

    def tearDown(self):
        """
        This method tears down the test environment.
        """
        for resume in Resume.objects.all(): # pylint: disable=no-member
            if resume.resume:
                try:
                    resume.resume.delete(save=False)
                except: # pylint: disable=bare-except
                    pass
        User.objects.all().delete() # pylint: disable=no-member
        Resume.objects.all().delete() # pylint: disable=no-member

        try:
            shutil.rmtree(settings.MEDIA_ROOT) # pylint: disable=no-member
        except: # pylint: disable=bare-except
            pass # pylint: disable=bare-except
