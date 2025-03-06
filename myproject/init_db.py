import os
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

DEV_DB_PATH = BASE_DIR / 'db.sqlite3'
PROD_DB_PATH = Path('/app/database/db.sqlite3')

DEBUG = 'DEBUG' in os.environ

db_path = DEV_DB_PATH if DEBUG else PROD_DB_PATH

os.makedirs(os.path.dirname(DEV_DB_PATH), exist_ok=True)

print(f"Creating database at {DEV_DB_PATH}")
conn = sqlite3.connect(DEV_DB_PATH)
conn.close()
print("Database created successfully!")

print("Now run 'python manage.py migrate' to create the database schema.") 