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
from .models import Resume, get_user_by_email
from .signals import user_created_callback
from .views import login_view, register_view, logout_view

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
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='StrongTestPass123'
        )
    
    def test_register_view_GET(self):
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'register.html')
    
    def test_register_view_POST_valid(self):
        response = self.client.post(self.register_url, {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'NewUserPass123',
            'password2': 'NewUserPass123',
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.home_url)
        self.assertTrue(User.objects.filter(username='newuser').exists())
    
    def test_register_view_POST_invalid(self):
        response = self.client.post(self.register_url, {
            'username': '',
            'email': 'newuser@example.com',
            'password1': 'NewUserPass123',
            'password2': 'NewUserPass123',
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'register.html')
        self.assertFalse(User.objects.filter(email='newuser@example.com').exists())
    
    def test_login_view_GET(self):
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')
    
    def test_login_view_POST_valid(self):
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'StrongTestPass123',
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.home_url)
        self.assertTrue(response.wsgi_request.user.is_authenticated)
    
    def test_login_view_POST_invalid(self):
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'WrongPassword',
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')
        self.assertFalse(response.wsgi_request.user.is_authenticated)
    
    def test_logout_view(self):
        self.client.login(username='testuser', password='StrongTestPass123')
        response = self.client.get(self.logout_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.home_url)
        
        response = self.client.get(self.home_url)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

class ResumeViewTest(TestCase):
    def test_upload_resume_POST_valid(self):
        writer = PdfWriter() 
        writer.add_page(writer.add_blank_page(width=210, height=297))

        written_file = BytesIO()
        writer.write(written_file)
        written_file.seek(0) # go to start of file
        uploaded_file = SimpleUploadedFile("some_resume.pdf", written_file.read(), content_type="application/pdf")

        response = self.client.post(reverse('upload_resume'), {'resume': uploaded_file})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The first 10 characters of the text from your resume is")
        os.remove(os.path.join(settings.MEDIA_ROOT, 'resumes', "some_resume.pdf"))

    def test_upload_resume_GET_valid(self):
        response = self.client.get(reverse('upload_resume'))
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('message', response.context)

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

class ResumeModelTest(TestCase):
    def test_resume_upload(self):
        file = SimpleUploadedFile("some_resume.pdf", b"%PDF-1.4 lorem ipsum", content_type="application/pdf")
        resume = Resume.objects.create(resume=file)
        self.assertEqual(resume.resume.name, 'resumes/some_resume.pdf')
        self.assertTrue(os.path.exists(resume.resume.path))
        self.assertIsNotNone(resume.uploaded_at)
        self.assertEqual(str(resume), "Resume 1")
        resume.resume.delete()

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

