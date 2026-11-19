"""
Automated Test Suite for SpendSmart
Verifies end-to-end integration across frontend, backend, and database layers.
"""

import os
import sys
import unittest
from datetime import date

# Ensure root directory is in Python path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.app import create_app
from database.models import db, Transaction, Budget

class SpendSmartArchitectureTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app({'TESTING': True})
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()
            Transaction.query.delete()
            Budget.query.delete()
            db.session.commit()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()

    def test_01_layers_integration(self):
        """Test Frontend, Backend, and Database integration."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'SpendSmart', response.data)
        self.assertIn(b'Financial Dashboard', response.data)

    def test_02_database_operations(self):
        """Test adding income and expenses to the database layer."""
        today_str = date.today().strftime('%Y-%m-%d')

        resp_inc = self.client.post('/transactions/add', data={
            'title': 'Stipend',
            'amount': '500.00',
            'transaction_type': 'Income',
            'category': 'Salary',
            'date': today_str
        }, follow_redirects=True)
        self.assertEqual(resp_inc.status_code, 200)

        resp_exp = self.client.post('/transactions/add', data={
            'title': 'Books',
            'amount': '120.00',
            'transaction_type': 'Expense',
            'category': 'Education',
            'date': today_str
        }, follow_redirects=True)
        self.assertEqual(resp_exp.status_code, 200)

        with self.app.app_context():
            self.assertEqual(Transaction.query.count(), 2)

    def test_03_budget_and_alerts(self):
        """Test budget limits and 80%/100% alert triggers."""
        today = date.today()

        self.client.post('/budgets/add', data={
            'category': 'Food',
            'amount': '100.00',
            'month': str(today.month),
            'year': str(today.year)
        }, follow_redirects=True)

        self.client.post('/transactions/add', data={
            'title': 'Lunch',
            'amount': '85.00',
            'transaction_type': 'Expense',
            'category': 'Food',
            'date': today.strftime('%Y-%m-%d')
        }, follow_redirects=True)

        api_resp = self.client.get('/api/dashboard')
        data = api_resp.get_json()
        self.assertTrue(any(a['category'] == 'Food' and a['level'] == 'warning' for a in data['alerts']))

    def test_04_rest_charts_api(self):
        """Test /api/charts REST endpoint."""
        resp = self.client.get('/api/charts')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn('doughnut', data)
        self.assertIn('bar', data)

    def test_05_csv_export(self):
        """Test export CSV endpoint."""
        resp = self.client.get('/export/csv')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('text/csv', resp.content_type)

if __name__ == '__main__':
    unittest.main()
