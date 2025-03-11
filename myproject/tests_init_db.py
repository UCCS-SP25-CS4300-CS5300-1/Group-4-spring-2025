import os
import sqlite3
import tempfile
import shutil
from unittest import TestCase

class TestInitDb(TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_sqlite_connection(self):
        """Test that we can create and connect to a SQLite database"""
        db_path = os.path.join(self.test_dir, 'test_db.sqlite3')
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE test_table (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            )
        ''')
        
        cursor.execute('INSERT INTO test_table (name) VALUES (?)', ('test_name',))
        conn.commit()
        
        cursor.execute('SELECT name FROM test_table WHERE id = 1')
        result = cursor.fetchone()
        self.assertEqual(result[0], 'test_name')
        
        conn.close()
        
    def test_db_file_creation(self):
        """Test that the database file is created in the correct location"""
        db_path = os.path.join(self.test_dir, 'test_db.sqlite3')
        
        conn = sqlite3.connect(db_path)
        conn.close()
        
        self.assertTrue(os.path.exists(db_path))
        self.assertTrue(os.path.isfile(db_path))
        
    def test_table_creation(self):
        """Test that we can create tables in the database"""
        db_path = os.path.join(self.test_dir, 'test_db.sqlite3')
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE test_table (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE
            )
        ''')
        conn.commit()
        
        cursor.execute('''
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='test_table'
        ''')
        result = cursor.fetchone()
        self.assertIsNotNone(result)
        self.assertEqual(result[0], 'test_table')
        
        conn.close()
        
    def test_data_persistence(self):
        """Test that data persists between connections"""
        db_path = os.path.join(self.test_dir, 'test_db.sqlite3')
        
        conn1 = sqlite3.connect(db_path)
        cursor1 = conn1.cursor()
        
        cursor1.execute('''
            CREATE TABLE test_table (
                id INTEGER PRIMARY KEY,
                value TEXT
            )
        ''')
        cursor1.execute('INSERT INTO test_table (value) VALUES (?)', ('test_value',))
        conn1.commit()
        conn1.close()
        
        conn2 = sqlite3.connect(db_path)
        cursor2 = conn2.cursor()
        
        cursor2.execute('SELECT value FROM test_table WHERE id = 1')
        result = cursor2.fetchone()
        self.assertEqual(result[0], 'test_value')
        
        conn2.close()