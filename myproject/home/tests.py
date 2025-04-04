from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from users.models import Profile
from home.models import Application
from .forms import SearchJobForm

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
        self.assertContains(response, '<title>ApplierPilotAI - Automate Your Job Search</title>')
        self.assertContains(response, 'AI-Powered Job Search Automation')
        self.assertContains(response, 'Streamline Your Job Hunt')
        self.assertContains(response, 'How ApplierPilotAI Works')
        
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
        self.assertContains(response, 'View Dashboard</a>')
        self.assertContains(response, 'href="/dashboard/"')
        
        self.assertNotContains(response, 'class="login-btn"')
        self.assertNotContains(response, 'Get Started For Free')
    
    def test_home_view_unauthenticated_user(self):
        response = self.client.get(self.home_url)
        
        self.assertContains(response, 'Login')
        self.assertContains(response, 'Sign Up')
        self.assertContains(response, 'Get Started For Free')
        
        self.assertNotContains(response, 'Hello, testuser')
        self.assertNotContains(response, 'View Dashboard')

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
        self.profile.linkedIn_username = 'test_linkedin'
        self.profile.save()
        
        self.app1 = Application.objects.create(
            user=self.user,
            search_word='python developer',
            job_title='Senior Python Developer',
            company='Test Company',
            link='https://example.com/job1',
            type='Full-time',
            progress='Applied'
        )
        
        self.app2 = Application.objects.create(
            user=self.user,
            search_word='data scientist',
            job_title='Data Scientist',
            company='Another Company',
            link='https://example.com/job2',
            type='Remote',
            progress='Interviewed'
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
        
        self.assertEqual(response.context['linkedIn_username'], 'test_linkedin')
        self.assertEqual(response.context['count'], 2)
        self.assertEqual(len(response.context['applications']), 2)
        self.assertIsInstance(response.context['form'], SearchJobForm)
    
    def test_dashboard_displays_applications(self):
        """Test that the dashboard displays the user's applications"""
        self.client.login(username='testuser', password='StrongTestPass123')
        response = self.client.get(self.dashboard_url)
        
        self.assertContains(response, 'Senior Python Developer')
        self.assertContains(response, 'Test Company')
        self.assertContains(response, 'Data Scientist')
        self.assertContains(response, 'Another Company')
        self.assertContains(response, 'Applied')
        self.assertContains(response, 'Interviewed')
    
    def test_dashboard_application_count(self):
        """Test that the dashboard shows the correct application count"""
        self.client.login(username='testuser', password='StrongTestPass123')
        response = self.client.get(self.dashboard_url)
        
        self.assertContains(response, '<span class="stat-value">2</span>')
        self.assertContains(response, '<span class="stat-label">Applications</span>')
    
    def test_dashboard_with_no_applications(self):
        """Test dashboard display when user has no applications"""
        new_user = User.objects.create_user(
            username='newuser',
            email='new@example.com',
            password='NewUserPass123'
        )
        
        self.client.login(username='newuser', password='NewUserPass123')
        response = self.client.get(self.dashboard_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['count'], 0)
        self.assertEqual(len(response.context['applications']), 0)
        self.assertContains(response, 'You haven\'t applied to any jobs yet')
        self.assertContains(response, '<span class="stat-value">0</span>')

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

    def test_dashboard_missing_linkedin_credentials(self):
        """Test dashboard behavior when LinkedIn credentials are missing"""
        self.client.login(username='testuser', password='StrongTestPass123')
        self.profile.linkedIn_username = ''
        self.profile.save()
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home/dashboard.html')
        self.assertContains(response, 'LinkedIn: Not Connected')

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
