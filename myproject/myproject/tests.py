"""
This file contains the tests for the myproject app.
"""

from django.test import TestCase
from django.core.asgi import get_asgi_application
from django.core.wsgi import get_wsgi_application
from django.core.handlers.asgi import ASGIHandler
from django.core.handlers.wsgi import WSGIHandler
import os
import sys

class DeploymentTests(TestCase):
    """
    This class contains the tests for the myproject app.
    """

    def test_asgi_import(self):
        """Test that ASGI application can be imported."""
        try:
            from myproject.asgi import application
            self.assertIsNotNone(application)
            self.assertIsInstance(application, ASGIHandler)
            self.assertIsInstance(get_asgi_application(), ASGIHandler)
        except ImportError as e:
            self.fail(f"Failed to import ASGI application: {e}")

    def test_wsgi_import(self):
        """Test that WSGI application can be imported."""
        try:
            from myproject.wsgi import application
            self.assertIsNotNone(application)
            self.assertIsInstance(application, WSGIHandler)
            self.assertIsInstance(get_wsgi_application(), WSGIHandler)
        except ImportError as e:
            self.fail(f"Failed to import WSGI application: {e}")

    def test_wsgi_env_path(self):
        """Test that WSGI environment path is set correctly."""
        project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.assertIn(project_path, sys.path)
