import os
import unittest
from django.test import TestCase, Client, tag
from django.urls import reverse
from django.contrib.auth.models import User
from users.models import Profile
from home.models import Application

@tag('integration')
class LinkedInIntegrationTest(TestCase):
    """Integration tests that require LinkedIn credentials"""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if not os.environ.get('LINKEDIN_TEST_USERNAME') or not os.environ.get('LINKEDIN_TEST_PASSWORD'):
            raise unittest.SkipTest(
                "LinkedIn test credentials not found in environment variables. "
                "Please set LINKEDIN_TEST_USERNAME and LINKEDIN_TEST_PASSWORD"
            )
    
    def setUp(self):
        self.client = Client()
        self.dashboard_url = reverse('dashboard')
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='StrongTestPass123'
        )
        
        self.profile = Profile.objects.get(user=self.user)
        self.profile.linkedIn_username = os.environ.get('LINKEDIN_TEST_USERNAME')
        self.profile.linkedIn_password = os.environ.get('LINKEDIN_TEST_PASSWORD')
        self.profile.save()
    
    def test_dashboard_search_form_submission(self):
        """Test that the search form can be submitted and jobs are fetched from LinkedIn"""
        self.client.login(username='testuser', password='StrongTestPass123')
        
        response = self.client.post(self.dashboard_url, {'search_term': 'software developer'})
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home/dashboard.html')
        
        applications = Application.objects.filter(user=self.user)
        self.assertTrue(len(applications) > 0)
        
        self.assertTrue(
            applications.filter(search_word='software developer').exists()
        ) 