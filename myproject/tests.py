from django.test import TestCase
import importlib

class WSGIASGITests(TestCase):
    """Tests for WSGI and ASGI application configuration."""
    
    def test_wsgi_config(self):
        """Test that the WSGI application module can be imported."""
        wsgi_module = importlib.import_module('myproject.wsgi')
        self.assertIsNotNone(wsgi_module)
        self.assertTrue(hasattr(wsgi_module, 'application'))
    
    def test_asgi_config(self):
        """Test that the ASGI application module can be imported."""
        asgi_module = importlib.import_module('myproject.asgi')
        self.assertIsNotNone(asgi_module)
        self.assertTrue(hasattr(asgi_module, 'application')) 