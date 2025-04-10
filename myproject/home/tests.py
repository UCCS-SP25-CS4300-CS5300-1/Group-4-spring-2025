from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from users.models import Profile
from home.models import Application, JobListing
from .forms import SearchJobForm
from django.utils import timezone
from unittest.mock import patch

class HomeViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.home_url = reverse('index')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='StrongTestPass123'
        )
    
    def test_home_view_GET(self):
        response = self.client.get(self.home_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home/index.html')
    
    def test_home_view_contains_expected_content(self):
        response = self.client.get(self.home_url)
        self.assertContains(response, '<title>ApplierPilotAI - Your AI Job Application Assistant</title>')
        self.assertContains(response, 'Supercharge Your Job Applications with AI')
        self.assertContains(response, 'AI-Powered Application Tools')
        self.assertContains(response, 'How Our AI Tools Help You')
        
        self.assertContains(response, '<a href="#features">Features</a>')
        self.assertContains(response, '<a href="#how-it-works">How It Works</a>')
        self.assertContains(response, '<a href="#contact">Contact</a>')
        self.assertNotContains(response, '<a href="#about">About</a>')

        self.assertContains(response, 'contact@ApplierPilot.com')
        self.assertNotContains(response, 'Pricing')
    
    def test_home_view_authenticated_user(self):
        self.client.login(username='testuser', password='StrongTestPass123')
        response = self.client.get(self.home_url)
        
        self.assertContains(response, 'Hello, testuser')
        self.assertContains(response, 'Logout')
        self.assertContains(response, 'Access AI Tools')
        self.assertContains(response, 'href="/dashboard/"')
        
        self.assertNotContains(response, 'class="login-btn"')
        self.assertNotContains(response, 'Start Using AI Tools')
    
    def test_home_view_unauthenticated_user(self):
        response = self.client.get(self.home_url)
        
        self.assertContains(response, 'Login')
        self.assertContains(response, 'Sign Up')
        self.assertContains(response, 'Start Using AI Tools')
        
        self.assertNotContains(response, 'Hello, testuser')
        self.assertNotContains(response, 'Access AI Tools')

class DashboardViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.dashboard_url = reverse('dashboard')
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='StrongTestPass123'
        )
        
        self.profile = Profile.objects.get(user=self.user)
        self.profile.save()
        
        # Create some job listings for testing
        self.job1 = JobListing.objects.create(
            job_id='test-job-1',
            title='Senior Python Developer',
            company='Test Company',
            location='Remote',
            description='Test job description',
            url='https://example.com/job1',
            job_type='Full-time',
            published_at=timezone.now(),
            search_key='python'
        )
        
        self.job2 = JobListing.objects.create(
            job_id='test-job-2',
            title='Data Scientist',
            company='Another Company',
            location='New York',
            description='Another test job description',
            url='https://example.com/job2',
            job_type='Remote',
            published_at=timezone.now(),
            search_key='data-science'
        )
    
    def test_dashboard_login_required(self):
        """Test that unauthenticated users are redirected to login"""
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/users/login/'))
        self.assertTrue('next=/dashboard/' in response.url)
    
    def test_dashboard_authenticated_user(self):
        """Test that authenticated users can access the dashboard"""
        self.client.login(username='testuser', password='StrongTestPass123')
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home/dashboard.html')
    
    def test_dashboard_context_data(self):
        """Test that the dashboard contains correct context data"""
        self.client.login(username='testuser', password='StrongTestPass123')
        response = self.client.get(self.dashboard_url)
        
        self.assertIsInstance(response.context['form'], SearchJobForm)
        self.assertIn('job_list', response.context)
        self.assertEqual(len(response.context['job_list']), 0)  # Empty by default
    
    def test_dashboard_search_results(self):
        """Test that the dashboard displays search results"""
        self.client.login(username='testuser', password='StrongTestPass123')
        
        # Mock the JobicyService.search_jobs method
        with patch('home.services.JobicyService.search_jobs') as mock_search:
            mock_search.return_value = [self.job1]
            
            response = self.client.post(self.dashboard_url, {'search_term': 'python'})
            
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'home/dashboard.html')
            self.assertIsInstance(response.context['form'], SearchJobForm)
            self.assertIn('job_list', response.context)
            self.assertEqual(len(response.context['job_list']), 1)
            
            # Verify the job details are displayed
            self.assertContains(response, 'Senior Python Developer')
            self.assertContains(response, 'Test Company')
            self.assertContains(response, 'Remote')
    
    def test_dashboard_form_validation_empty_search(self):
        """Test that empty search term is handled properly"""
        self.client.login(username='testuser', password='StrongTestPass123')
        response = self.client.post(self.dashboard_url, {'search_term': ''})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home/dashboard.html')
        self.assertTrue('form' in response.context)
        self.assertTrue(response.context['form'].errors)

    def test_dashboard_form_validation_missing_field(self):
        """Test that missing search term field is handled properly"""
        self.client.login(username='testuser', password='StrongTestPass123')
        response = self.client.post(self.dashboard_url, {})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home/dashboard.html')
        self.assertTrue('form' in response.context)
        self.assertTrue(response.context['form'].errors)

    def test_search_jobs_empty_function(self):
        """Test the empty search_jobs function"""
        self.client.login(username='testuser', password='StrongTestPass123')
        response = self.client.get(reverse('search_jobs'))
        self.assertEqual(response.status_code, 200)

class UrlsTest(TestCase):
    def setUp(self):
        self.client = Client()
    
    def test_home_url_resolves_to_index_view(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
    
    def test_login_url_exists(self):
        response = self.client.get('/users/login/')
        self.assertEqual(response.status_code, 200)
    
    def test_register_url_exists(self):
        response = self.client.get('/users/register/')
        self.assertEqual(response.status_code, 200)
    
    def test_logout_url_redirects(self):
        response = self.client.get('/users/logout/')
        self.assertEqual(response.status_code, 302)
    
    def test_dashboard_url_exists(self):
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='StrongTestPass123'
        )
        self.client.login(username='testuser', password='StrongTestPass123')
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 200)

class StaticContentTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.home_url = reverse('index')
    
    def test_static_css_loaded(self):
        response = self.client.get(self.home_url)
        self.assertContains(response, '<link rel="stylesheet" href="')
    
    def test_font_awesome_loaded(self):
        response = self.client.get(self.home_url)
        self.assertContains(response, 'font-awesome')
    
    def test_page_contains_header(self):
        response = self.client.get(self.home_url)
        self.assertContains(response, '<header>')
    
    def test_page_contains_footer(self):
        response = self.client.get(self.home_url)
        self.assertContains(response, '<footer')
        self.assertContains(response, 'id="contact"')
    
    def test_page_contains_main_content(self):
        response = self.client.get(self.home_url)
        self.assertContains(response, '<main>')
        self.assertContains(response, 'id="features"')
        self.assertContains(response, 'id="how-it-works"')

class AuthRedirectTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.dashboard_url = reverse('dashboard')
        self.profile_url = reverse('profile')
        
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='StrongTestPass123'
        )
    
    def test_dashboard_redirects_to_login(self):
        """Test that dashboard redirects to login when user is not authenticated"""
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/users/login/'))
        self.assertTrue('next=/dashboard/' in response.url)
    
    def test_profile_redirects_to_login(self):
        """Test that profile redirects to login when user is not authenticated"""
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/users/login/'))
        self.assertTrue('next=/users/profile/' in response.url)
    
    def test_dashboard_accessible_when_authenticated(self):
        """Test that dashboard is accessible when user is authenticated"""
        self.client.login(username='testuser', password='StrongTestPass123')
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)
    
    def test_profile_accessible_when_authenticated(self):
        """Test that profile is accessible when user is authenticated"""
        self.client.login(username='testuser', password='StrongTestPass123')
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200)
    
    def test_login_redirect_to_next_url(self):
        """Test that after login, user is redirected to the 'next' URL"""
        response = self.client.get(self.dashboard_url)
        login_url = response.url  # This will be '/users/login/?next=/dashboard/'
        
        # Now login with this URL
        response = self.client.post(
            login_url, 
            {'username': 'testuser', 'password': 'StrongTestPass123'},
            follow=True
        )
        
        # The first redirected URL should be to the dashboard
        self.assertEqual(response.redirect_chain[0][0], '/dashboard/')
        self.assertEqual(response.status_code, 200)
