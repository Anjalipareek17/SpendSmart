import os

class Config:
    """
    Backend Configuration Settings for SpendSmart Application.
    Links the backend server with frontend templates and the database layer.
    """
    # Project Root Directory (one level up from /backend)
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    # Path to database and templates
    DATABASE_DIR = os.path.join(BASE_DIR, 'database')
    FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')
    TEMPLATES_DIR = os.path.join(FRONTEND_DIR, 'templates')
    STATIC_DIR = os.path.join(FRONTEND_DIR, 'static')

    # Secret key for session management
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'spendsmart-academic-college-project-key-2026'

    # SQLite Database URI pointing to /database/finance.db
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(DATABASE_DIR, 'finance.db')

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Standard Expense Categories
    EXPENSE_CATEGORIES = [
        'Food',
        'Travel',
        'Shopping',
        'Bills',
        'Education',
        'Entertainment',
        'Healthcare',
        'Other'
    ]

    # Standard Income Categories
    INCOME_CATEGORIES = [
        'Salary',
        'Allowance',
        'Freelancing',
        'Business',
        'Other'
    ]

    # Visual Icons (Bootstrap Icons)
    CATEGORY_ICONS = {
        'Food': 'bi-cup-hot-fill',
        'Travel': 'bi-airplane-fill',
        'Shopping': 'bi-bag-fill',
        'Bills': 'bi-receipt-cutoff',
        'Education': 'bi-mortarboard-fill',
        'Entertainment': 'bi-controller',
        'Healthcare': 'bi-heart-pulse-fill',
        'Salary': 'bi-cash-coin',
        'Allowance': 'bi-wallet2',
        'Freelancing': 'bi-laptop',
        'Business': 'bi-briefcase-fill',
        'Other': 'bi-tag-fill'
    }

    # Chart Palette Colors
    CATEGORY_COLORS = {
        'Food': '#f59e0b',
        'Travel': '#3b82f6',
        'Shopping': '#ec4899',
        'Bills': '#ef4444',
        'Education': '#8b5cf6',
        'Entertainment': '#10b981',
        'Healthcare': '#06b6d4',
        'Salary': '#10b981',
        'Allowance': '#6366f1',
        'Freelancing': '#0ea5e9',
        'Business': '#14b8a6',
        'Other': '#64748b'
    }
