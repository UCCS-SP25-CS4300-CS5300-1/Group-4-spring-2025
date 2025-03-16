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
    
    def test_home_view_authenticated_user(self):
        self.client.login(username='testuser', password='StrongTestPass123')
        response = self.client.get(self.home_url)
        
        self.assertContains(response, 'Hello, testuser')
        self.assertContains(response, 'Logout')
        self.assertContains(response, 'View Dashboard')
        
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
        self.assertTrue(response.url.startswith('/accounts/login/'))
    
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
    
    def test_dashboard_search_form_submission(self):
        """Test that the search form can be submitted"""
        self.client.login(username='testuser', password='StrongTestPass123')
        response = self.client.post(self.dashboard_url, {'search_term': 'software developer'})
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home/dashboard.html')
    
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
        self.assertContains(response, '<footer>')
    
    def test_page_contains_main_content(self):
        response = self.client.get(self.home_url)
        self.assertContains(response, '<main>')
        self.assertContains(response, 'id="features"')
        self.assertContains(response, 'id="how-it-works"')
