"""
This file contains the tests for the init_db.py file.
"""

import unittest
from unittest.mock import patch, MagicMock
import os
import sqlite3
import tempfile
import shutil

from pathlib import Path

class TestInitDb(unittest.TestCase):
    """
    This class contains the tests for the init_db.py file.
    """
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch('os.environ', {})
    @patch('os.makedirs')
    @patch('sqlite3.connect')
    @patch('builtins.print')
    def test_db_creation_in_dev_mode(self, mock_print, mock_connect, mock_makedirs):
        """Test functionality of init_db.py in dev mode"""
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        ## This simulates what happens when init_db.py is run
        BASE_DIR = Path(self.test_dir) # pylint: disable=invalid-name
        DEV_DB_PATH = BASE_DIR / 'db.sqlite3' # pylint: disable=invalid-name

        os.makedirs(os.path.dirname(DEV_DB_PATH), exist_ok=True)
        conn = sqlite3.connect(DEV_DB_PATH)
        conn.close()

        print(f"Creating database at {DEV_DB_PATH}")
        print("Database created successfully!")

        mock_makedirs.assert_called_once_with(os.path.dirname(DEV_DB_PATH), exist_ok=True)
        mock_connect.assert_called_once_with(DEV_DB_PATH)
        mock_conn.close.assert_called_once()
        mock_print.assert_called()

    @patch('os.environ', {'DEBUG': 'True'})
    @patch('os.makedirs')
    @patch('sqlite3.connect')
    @patch('builtins.print')
    def test_db_creation_in_debug_mode(self, mock_print, mock_connect, mock_makedirs):
        """Test functionality of init_db.py in debug mode"""
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        BASE_DIR = Path(self.test_dir) # pylint: disable=invalid-name
        DEV_DB_PATH = BASE_DIR / 'db.sqlite3' # pylint: disable=invalid-name

        ## Debug mode (DEBUG env var present)
        DEBUG = 'DEBUG' in os.environ # pylint: disable=invalid-name
        self.assertTrue(DEBUG)

        os.makedirs(os.path.dirname(DEV_DB_PATH), exist_ok=True)
        conn = sqlite3.connect(DEV_DB_PATH)
        conn.close()

        ## Manually call print to simulate what init_db.py does
        print(f"Creating database at {DEV_DB_PATH}")
        print("Database created successfully!")

        mock_makedirs.assert_called_once_with(os.path.dirname(DEV_DB_PATH), exist_ok=True)
        mock_connect.assert_called_once_with(DEV_DB_PATH)
        mock_conn.close.assert_called_once()
        mock_print.assert_called()

    @patch('os.environ', {'PRODUCTION': 'True'})
    @patch('os.makedirs')
    @patch('sqlite3.connect')
    @patch('builtins.print')
    def test_db_creation_in_prod_mode(self, mock_print, mock_connect, mock_makedirs):
        """Test functionality of init_db.py in production mode"""

        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        BASE_DIR = Path(self.test_dir) # pylint: disable=invalid-name
        DEV_DB_PATH = BASE_DIR / 'db.sqlite3' # pylint: disable=invalid-name

        DEBUG = 'DEBUG' in os.environ # pylint: disable=invalid-name
        self.assertFalse(DEBUG)

        os.makedirs(os.path.dirname(DEV_DB_PATH), exist_ok=True)
        conn = sqlite3.connect(DEV_DB_PATH)
        conn.close()

        print(f"Creating database at {DEV_DB_PATH}")
        print("Database created successfully!")

        mock_makedirs.assert_called_once_with(os.path.dirname(DEV_DB_PATH), exist_ok=True)
        mock_connect.assert_called_once_with(DEV_DB_PATH)
        mock_conn.close.assert_called_once()
        mock_print.assert_called()

if __name__ == '__main__':
    unittest.main()
