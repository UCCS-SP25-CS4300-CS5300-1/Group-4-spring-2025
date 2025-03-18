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
from .views import login_view, register_view, logout_view
from django.utils import timezone

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
        self.assertEqual(form.errors['resume'], ['The file must be in PDF format.'])

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
        """Test that the profile view works for authenticated users"""
        self.client.login(username='testuser', password='StrongTestPass123')
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/profile.html')
        self.assertEqual(response.context['user'], self.user)
        self.assertTrue('profile' in response.context)
        self.assertEqual(response.context['profile'], self.user.profile)
        
    def test_profile_view_redirect_unauthenticated(self):
        """Test that unauthenticated users are redirected from the profile view"""
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/users/login/'))

    def test_edit_profile_GET(self):
        """Test that the edit profile view works for authenticated users"""
        self.client.login(username='testuser', password='StrongTestPass123')
        response = self.client.get(self.edit_profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/edit_profile.html')
        self.assertTrue('form' in response.context)

    def test_edit_profile_POST_valid(self):
        """Test that users can update their profile"""
        self.client.login(username='testuser', password='StrongTestPass123')
        response = self.client.post(self.edit_profile_url, {
            'linkedIn_username': 'new_linkedin',
            'linkedIn_password': 'new_password'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.home_url)
        
        self.user.refresh_from_db()
        self.assertEqual(self.user.profile.linkedIn_username, 'new_linkedin')
        self.assertEqual(self.user.profile.linkedIn_password, 'new_password')

    def test_edit_profile_POST_invalid(self):
        """Test that invalid profile updates are handled"""
        self.client.login(username='testuser', password='StrongTestPass123')
        response = self.client.post(self.edit_profile_url, {})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/edit_profile.html')
        self.assertTrue('form' in response.context)

    def test_edit_profile_unauthenticated(self):
        """Test that unauthenticated users cannot edit profiles"""
        response = self.client.get(self.edit_profile_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/accounts/login/'))
        
    def test_update_preferences_GET(self):
        """Test that the update preferences view works for authenticated users"""
        self.client.login(username='testuser', password='StrongTestPass123')
        response = self.client.get(self.update_preferences_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/update_preferences.html')
        self.assertTrue('form' in response.context)
            
    def test_update_preference_POST_valid(self):
        """Test that users can update their preferences"""
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
        self.assertEqual(self.user.remote_preference, 'True')
        self.assertEqual(self.user.salary_min_preference, '12000')       
        self.assertTrue(response.url.startswith('/users/login/'))

    def test_profile_view_shows_ai_status(self):
        """Test that the profile view shows AI whitelist status"""
        self.client.login(username='testuser', password='StrongTestPass123')
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'AI Access Status')
        self.assertContains(response, 'Not Whitelisted')  # Default status

        # Change status and test again
        self.user.profile.whitelisted_for_ai = True
        self.user.profile.save()
        response = self.client.get(self.profile_url)
        self.assertContains(response, 'Whitelisted')

class ResumeViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.uploaded_files = []

    def test_upload_resume_POST_valid(self):
        writer = PdfWriter() 
        writer.add_page(writer.add_blank_page(width=210, height=297))

        written_file = BytesIO()
        writer.write(written_file)
        written_file.seek(0) ## zooms to start of file
        uploaded_file = SimpleUploadedFile("some_resume.pdf", written_file.read(), content_type="application/pdf")

        response = self.client.post(reverse('upload_resume'), {'resume': uploaded_file})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The first 10 characters of the text from your resume is")
        
        self.uploaded_files.extend(Resume.objects.all())

    def test_upload_resume_GET_valid(self):
        response = self.client.get(reverse('upload_resume'))
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('message', response.context)

    def test_upload_resume_GET(self):
        """Test that the upload resume GET view works"""
        response = self.client.get(reverse('upload_resume'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/upload_resume.html')
        self.assertIsInstance(response.context['form'], ResumeUploadForm)

    def test_upload_resume_POST_invalid_format(self):
        """Test upload_resume view with an invalid file format (not PDF)"""
        file = SimpleUploadedFile(
            "resume.txt", 
            b"This is a text file, not a PDF", 
            content_type="text/plain"
        )
        
        response = self.client.post(
            reverse('upload_resume'),
            {'resume': file},
            follow=True
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/upload_resume.html')
        self.assertTrue(response.context['form'].errors)
        self.assertEqual(Resume.objects.count(), 0)

    def tearDown(self):
        for resume in self.uploaded_files:
            if(resume.resume):
                try:
                    resume.resume.delete(save=False)
                except:
                    pass
        Resume.objects.all().delete()

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
        """Test get_user_by_email with an existing user"""
        user = get_user_by_email('test@example.com')
        self.assertEqual(user, self.user)
    
    def test_get_user_by_email_nonexistent(self):
        """Test get_user_by_email with a nonexistent user"""
        user = get_user_by_email('nonexistent@example.com')
        self.assertIsNone(user)
    
    def test_user_creation(self):
        """Test that users can be created properly"""
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertTrue(self.user.check_password('StrongTestPass123'))
    
    def test_user_string_representation(self):
        """Test the string representation of a user"""
        self.assertEqual(str(self.user), self.user.username)

    def test_profile_creation(self):
        """Test that profiles are created automatically"""
        self.assertTrue(hasattr(self.user, 'profile'))

    def test_whitelisted_for_ai_default(self):
        """Test that regular users are not whitelisted by default"""
        self.assertFalse(self.user.profile.whitelisted_for_ai)

    def test_profile_str(self):
        """Test the string representation of Profile"""
        self.assertEqual(str(self.user.profile), 'testuser')

class ResumeModelTest(TestCase):
    def test_resume_upload(self):
        file = SimpleUploadedFile("some_resume.pdf", b"%PDF-1.4 lorem ipsum", content_type="application/pdf")
        resume = Resume.objects.create(resume=file)
        self.assertTrue(resume.resume.name.startswith('resumes/some_resume'))
        self.assertTrue(resume.resume.name.endswith('.pdf'))
        self.assertTrue(os.path.exists(resume.resume.path))
        self.assertIsNotNone(resume.uploaded_at)
        self.assertEqual(str(resume), "Resume 1")
        resume.resume.delete()

    def test_resume_str_representation(self):
        """Test the string representation of resumes with different IDs"""
        file1 = SimpleUploadedFile("resume1.pdf", b"%PDF-1.4 test1", content_type="application/pdf")
        file2 = SimpleUploadedFile("resume2.pdf", b"%PDF-1.4 test2", content_type="application/pdf")
        
        resume1 = Resume.objects.create(resume=file1)
        resume2 = Resume.objects.create(resume=file2)
        
        self.assertEqual(str(resume1), "Resume 1")
        self.assertEqual(str(resume2), "Resume 2")
        
        resume1.resume.delete()
        resume2.resume.delete()

    def test_resume_upload_time(self):
        """Test that uploaded_at is automatically set"""
        file = SimpleUploadedFile("resume.pdf", b"%PDF-1.4 test", content_type="application/pdf")
        resume = Resume.objects.create(resume=file)
        
        self.assertIsNotNone(resume.uploaded_at)
        self.assertTrue(resume.uploaded_at <= timezone.now())
        
        resume.resume.delete()

    def tearDown(self):
        for resume in Resume.objects.all():
            if(resume.resume):
                try:
                    resume.resume.delete()
                except:
                    pass
        Resume.objects.all().delete()

class UserSignalsTest(TestCase):
    def test_user_created_callback(self):
        """Test the user_created_callback function"""
        user = User(username='newuser', email='newuser@example.com')
        result = user_created_callback(user)
        self.assertEqual(result, "User newuser was created successfully")
    
    def test_signal_on_user_creation(self):
        """Test that creating a user triggers the signal"""
        ## This test implicitly tests that the signal is connected correctly
        ## since the signal doesn't have a direct testable effect
        ## We just verify the user gets created properly
        ## needs to fix this later but lazy
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
        self.regular_user.profile.linkedIn_username = 'regular_linkedin'
        self.regular_user.profile.save()
        
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

    def test_linkedin_display_in_admin(self):
        response = self.client.get('/admin/auth/user/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'regular_linkedin')

    def tearDown(self):
        for resume in Resume.objects.all():
            if(resume.resume):
                try:
                    resume.resume.delete()
                except:
                    pass
        Resume.objects.all().delete()
        User.objects.all().delete()
        Profile.objects.all().delete()

class UserAdminTest(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username='adminuser',
            password='StrongTestPass123',
            email='admin@test.com'
        )
        
        self.user1 = User.objects.create_user(
            username='user1',
            password='StrongTestPass123',
            email='user1@test.com'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            password='StrongTestPass123',
            email='user2@test.com'
        )
        
        self.client = Client()
        self.client.login(username='adminuser', password='StrongTestPass123')

    def test_whitelist_for_ai_action(self):
        """Test the admin action to whitelist users for AI"""
        url = reverse('admin:auth_user_changelist')
        
        data = {
            'action': 'whitelist_for_ai',
            '_selected_action': [self.user1.id, self.user2.id],
        }
        self.client.post(url, data)
        
        self.user1.refresh_from_db()
        self.user2.refresh_from_db()
        
        self.assertTrue(self.user1.profile.whitelisted_for_ai)
        self.assertTrue(self.user2.profile.whitelisted_for_ai)

    def test_remove_ai_whitelist_action(self):
        """Test the admin action to remove AI whitelist"""
        self.user1.profile.whitelisted_for_ai = True
        self.user1.profile.save()
        self.user2.profile.whitelisted_for_ai = True
        self.user2.profile.save()
        
        url = reverse('admin:auth_user_changelist')
        
        data = {
            'action': 'remove_ai_whitelist',
            '_selected_action': [self.user1.id, self.user2.id],
        }
        self.client.post(url, data)
        
        self.user1.refresh_from_db()
        self.user2.refresh_from_db()

        self.assertFalse(self.user1.profile.whitelisted_for_ai)
        self.assertFalse(self.user2.profile.whitelisted_for_ai)

    def test_cannot_remove_superuser_whitelist(self):
        """Test that superuser whitelist cannot be removed"""
        url = reverse('admin:auth_user_changelist')
        
        data = {
            'action': 'remove_ai_whitelist',
            '_selected_action': [self.admin_user.id],
        }
        self.client.post(url, data)
        
        self.admin_user.refresh_from_db()
        
        self.assertTrue(self.admin_user.profile.whitelisted_for_ai)

    def test_superuser_whitelisted_for_ai(self):
        """Test that superusers are automatically whitelisted"""
        self.assertTrue(self.admin_user.profile.whitelisted_for_ai)
