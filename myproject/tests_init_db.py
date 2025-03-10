import unittest
import os
import sys
import tempfile
import shutil
from pathlib import Path
import sqlite3

class TestInitDb(unittest.TestCase):
    
    def set_up(self):
        self.test_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        self.old_stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w') ## throw this bullshit away
    
    def tear_down(self):
        sys.stdout.close()
        sys.stdout = self.old_stdout
        
        os.chdir(self.old_cwd)
        shutil.rmtree(self.test_dir)
    
    def test_sqlite_connection(self):
        """Test that we can create and connect to a SQLite database"""
        db_path = os.path.join(self.test_dir, 'test_db.sqlite3')
        
        conn = sqlite3.connect(db_path)
        conn.close()
        
        self.assertTrue(os.path.exists(db_path))
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)')
        conn.commit()
        
        cursor.execute('INSERT INTO test (name) VALUES (?)', ('test_name',))
        conn.commit()
        
        cursor.execute('SELECT name FROM test WHERE id = 1')
        result = cursor.fetchone()
        self.assertEqual(result[0], 'test_name')
        
        conn.close()

if(__name__ == '__main__'):
    unittest.main()