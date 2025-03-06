from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

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
        self.assertTemplateUsed(response, 'index.html')
    
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
