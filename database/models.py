from datetime import datetime, date, timezone
from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy instance
db = SQLAlchemy()

def get_utc_now():
    """Return timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)

class Transaction(db.Model):
    """
    Transaction Entity (Data Layer)
    Stores individual financial activities (Income or Expense).
    """
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(120), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    transaction_type = db.Column(db.String(10), nullable=False)  # 'Income' or 'Expense'
    category = db.Column(db.String(50), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    description = db.Column(db.String(255), nullable=True)
    is_demo = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=get_utc_now)

    def to_dict(self):
        """Serialize model instance to dictionary for REST JSON responses."""
        return {
            'id': self.id,
            'title': self.title,
            'amount': round(self.amount, 2),
            'transaction_type': self.transaction_type,
            'category': self.category,
            'date': self.date.strftime('%Y-%m-%d') if self.date else '',
            'description': self.description or '',
            'is_demo': self.is_demo,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else ''
        }

    def __repr__(self):
        return f"<Transaction {self.id}: {self.title} (${self.amount})>"


class Budget(db.Model):
    """
    Budget Entity (Data Layer)
    Stores monthly spending thresholds per category or overall.
    """
    __tablename__ = 'budgets'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    category = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    month = db.Column(db.Integer, nullable=False)   # 1 - 12
    year = db.Column(db.Integer, nullable=False)    # e.g., 2026
    created_at = db.Column(db.DateTime, default=get_utc_now)

    # Composite Unique Constraint: One budget limit per category per month/year
    __table_args__ = (
        db.UniqueConstraint('category', 'month', 'year', name='uq_budget_category_month_year'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'category': self.category,
            'amount': round(self.amount, 2),
            'month': self.month,
            'year': self.year,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else ''
        }

    def __repr__(self):
        return f"<Budget {self.category} ({self.month}/{self.year}): ${self.amount}>"
