import os
import unittest
from unittest.mock import patch
from flask import json
from app import app
import sqlite3
from io import BytesIO

class TestApp(unittest.TestCase):
    def setUp(self):
        # Use a temporary test database
        self.test_db_path = os.path.join(os.getcwd(), 'test.db')
        app.config['TESTING'] = True
        app.config['DB_PATH'] = self.test_db_path
        self.client = app.test_client()

        # Initialize the database
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS inspections (id INTEGER PRIMARY KEY AUTOINCREMENT, inspector_name TEXT NOT NULL, location TEXT NOT NULL, inspection_date TEXT NOT NULL, installation_name TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP)")
        cursor.execute("CREATE TABLE IF NOT EXISTS checklist_items (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL)")
        cursor.execute("INSERT OR IGNORE INTO checklist_items (name) VALUES ('Check electrical wiring'), ('Check plumbing'), ('Check fire safety'), ('Check electrical safety'), ('Check water pressure'), ('Check drainage'), ('Check structural integrity'), ('Check emergency exits'), ('Check fire extinguishers'), ('Check ventilation')")
        cursor.execute("CREATE TABLE IF NOT EXISTS inspection_photos (id INTEGER PRIMARY KEY AUTOINCREMENT, inspection_id INTEGER NOT NULL, photo_path TEXT NOT NULL, comment TEXT, resolved INTEGER DEFAULT 0, uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP)")
        conn.commit()
        conn.close()

    def tearDown(self):
        # Clean up the test database
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)

    def test_create_inspection(self):
        response = self.client.post('/new', data={
            'inspector_name': 'Test Inspector',
            'location': 'Test Location',
            'inspection_date': '2026-02-23',
            'installation_name': 'Test Installation'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Inspector', response.data)
        self.assertIn(b'Test Location', response.data)
        self.assertIn(b'Test Installation', response.data)

    def test_view_inspection(self):
        # Create an inspection
        response = self.client.post('/new', data={
            'inspector_name': 'Test Inspector',
            'location': 'Test Location',
            'inspection_date': '2026-02-23',
            'installation_name': 'Test Installation'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # View the inspection
        response = self.client.get('/view/1')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Inspection Report', response.data)

    def test_upload_photo(self):
        # Create an inspection
        response = self.client.post('/new', data={
            'inspector_name': 'Test Inspector',
            'location': 'Test Location',
            'inspection_date': '2026-02-23',
            'installation_name': 'Test Installation'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # Upload a photo
        with BytesIO(b'test photo data') as photo:
            response = self.client.post('/upload/1', data={
                'photo': (photo, 'test.jpg'),
                'comment': 'Test comment'
            }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Photo uploaded successfully', response.data)

    def test_generate_pdf(self):
        # Create an inspection
        response = self.client.post('/new', data={
            'inspector_name': 'Test Inspector',
            'location': 'Test Location',
            'inspection_date': '2026-02-23',
            'installation_name': 'Test Installation'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # Generate PDF
        response = self.client.get('/generate_pdf/1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/pdf')

if __name__ == '__main__':
    unittest.main()