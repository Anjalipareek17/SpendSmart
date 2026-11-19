-- ===================================================================
-- SpendSmart Database Schema (SQLite DDL)
-- Designed for Academic / Faculty Evaluation
-- ===================================================================

-- 1. Transactions Table
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(120) NOT NULL,
    amount REAL NOT NULL CHECK (amount > 0),
    transaction_type VARCHAR(10) NOT NULL CHECK (transaction_type IN ('Income', 'Expense')),
    category VARCHAR(50) NOT NULL,
    date DATE NOT NULL,
    description VARCHAR(255),
    is_demo BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index on date and category for optimized query analytics
CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date);
CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category);
CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(transaction_type);

-- 2. Budgets Table
CREATE TABLE IF NOT EXISTS budgets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category VARCHAR(50) NOT NULL,
    amount REAL NOT NULL CHECK (amount > 0),
    month INTEGER NOT NULL CHECK (month BETWEEN 1 AND 12),
    year INTEGER NOT NULL CHECK (year >= 2020),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_budget_category_month_year UNIQUE (category, month, year)
);

-- Index on month and year for rapid budget summary lookups
CREATE INDEX IF NOT EXISTS idx_budgets_period ON budgets(month, year);
