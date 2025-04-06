from asyncio.log import logger
import os
import unittest
from django.test import TestCase, tag
from applier_pilot.linkedin_auth import login_to_linkedin

@tag('integration')
class LinkedInAuthTest(TestCase):
    """Integration tests for LinkedIn authentication"""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if not os.environ.get('LINKEDIN_TEST_USERNAME') or not os.environ.get('LINKEDIN_TEST_PASSWORD'):
            logger.warning("LinkedIn test credentials not found in environment variables. Skipping tests.")
            raise unittest.SkipTest(
                "LinkedIn test credentials not found in environment variables. "
                "Please set LINKEDIN_TEST_USERNAME and LINKEDIN_TEST_PASSWORD"
            )
        cls.username = os.environ.get('LINKEDIN_TEST_USERNAME')
        cls.password = os.environ.get('LINKEDIN_TEST_PASSWORD')
    
    def test_linkedin_login_success(self):
        """Test successful login to LinkedIn with valid credentials"""
        success, message, browser = login_to_linkedin(self.username, self.password)
        try:
            self.assertTrue(success, f"Login failed: {message}")
            self.assertEqual(message, "Successfully logged in")
        finally:
            if browser:
                browser.quit() 