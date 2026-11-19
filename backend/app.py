import os
import sys
import csv
import io
from datetime import datetime, date
from flask import (
    Flask, render_template, request, redirect, url_for, flash, jsonify, Response
)
from sqlalchemy import func, extract

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.config import Config
from database.models import db, Transaction, Budget

def format_currency_inr(value):
    try:
        val = float(value)
        if val < 0:
            return f"-₹{abs(val):,.2f}"
        return f"₹{val:,.2f}"
    except (ValueError, TypeError):
        return "₹0.00"

def format_number_inr(value):
    try:
        val = float(value)
        return f"{abs(val):,.2f}"
    except (ValueError, TypeError):
        return "0.00"

def create_app(custom_config=None):
    app = Flask(
        __name__,
        template_folder=Config.TEMPLATES_DIR,
        static_folder=Config.STATIC_DIR
    )
    app.config.from_object(Config)

    app.jinja_env.filters['currency'] = format_currency_inr
    app.jinja_env.filters['inr'] = format_number_inr

    if custom_config:
        app.config.update(custom_config)

    os.makedirs(Config.DATABASE_DIR, exist_ok=True)
    db.init_app(app)

    with app.app_context():
        db.create_all()

    @app.context_processor
    def inject_globals():
        today = date.today()
        return {
            'expense_categories': Config.EXPENSE_CATEGORIES,
            'income_categories': Config.INCOME_CATEGORIES,
            'category_icons': Config.CATEGORY_ICONS,
            'category_colors': Config.CATEGORY_COLORS,
            'current_month': today.month,
            'current_year': today.year,
            'today_date': today.strftime('%Y-%m-%d'),
            'currency_symbol': '₹',
            'app_name': 'SpendSmart'
        }

    def calculate_budget_summary(target_month=None, target_year=None):
        today = date.today()
        month = target_month if target_month is not None else today.month
        year = target_year if target_year is not None else today.year

        budgets = Budget.query.filter_by(month=month, year=year).all()

        category_spending_query = db.session.query(
            Transaction.category,
            func.coalesce(func.sum(Transaction.amount), 0.0).label('total_spent')
        ).filter(
            Transaction.transaction_type == 'Expense',
            extract('month', Transaction.date) == month,
            extract('year', Transaction.date) == year
        ).group_by(Transaction.category).all()

        spending_map = {cat: float(spent) for cat, spent in category_spending_query}
        overall_spent = sum(spending_map.values())

        overall_budget_obj = next((b for b in budgets if b.category == 'Overall'), None)
        category_budget_objs = [b for b in budgets if b.category != 'Overall']

        if overall_budget_obj:
            overall_budget = overall_budget_obj.amount
        elif category_budget_objs:
            overall_budget = sum(b.amount for b in category_budget_objs)
        else:
            overall_budget = 0.0

        remaining_budget = max(0.0, overall_budget - overall_spent) if overall_budget > 0 else 0.0
        overall_percent = min(100.0, round((overall_spent / overall_budget * 100), 1)) if overall_budget > 0 else 0.0

        category_budgets = []
        active_alerts = []

        for b in category_budget_objs:
            spent = spending_map.get(b.category, 0.0)
            percent = round((spent / b.amount * 100), 1) if b.amount > 0 else 0.0
            remaining = max(0.0, b.amount - spent)

            if percent >= 100.0:
                alert_level = 'danger'
                active_alerts.append({
                    'category': b.category,
                    'level': 'danger',
                    'percent': percent,
                    'spent': spent,
                    'limit': b.amount,
                    'message': f"Critical Alert: You have exceeded your {b.category} budget limit (₹{b.amount:,.2f}) with spending of ₹{spent:,.2f} ({percent}%)."
                })
            elif percent >= 80.0:
                alert_level = 'warning'
                active_alerts.append({
                    'category': b.category,
                    'level': 'warning',
                    'percent': percent,
                    'spent': spent,
                    'limit': b.amount,
                    'message': f"Warning: You have reached {percent}% of your {b.category} budget limit (₹{spent:,.2f} of ₹{b.amount:,.2f})."
                })
            else:
                alert_level = 'normal'

            category_budgets.append({
                'id': b.id,
                'category': b.category,
                'amount': b.amount,
                'spent': spent,
                'remaining': remaining,
                'percent': percent,
                'display_percent': min(100.0, percent),
                'alert_level': alert_level
            })

        if overall_budget > 0:
            actual_overall_pct = round((overall_spent / overall_budget * 100), 1)
            if actual_overall_pct >= 100.0:
                active_alerts.insert(0, {
                    'category': 'Overall Budget',
                    'level': 'danger',
                    'percent': actual_overall_pct,
                    'spent': overall_spent,
                    'limit': overall_budget,
                    'message': f"Critical Alert: Total monthly expenses (₹{overall_spent:,.2f}) have exceeded your overall monthly budget (₹{overall_budget:,.2f})!"
                })
            elif actual_overall_pct >= 80.0:
                active_alerts.insert(0, {
                    'category': 'Overall Budget',
                    'level': 'warning',
                    'percent': actual_overall_pct,
                    'spent': overall_spent,
                    'limit': overall_budget,
                    'message': f"Warning: Total monthly spending is at {actual_overall_pct}% (₹{overall_spent:,.2f} of ₹{overall_budget:,.2f}) of your overall monthly budget."
                })

        return {
            'overall_budget': round(overall_budget, 2),
            'overall_spent': round(overall_spent, 2),
            'overall_percent': overall_percent,
            'remaining_budget': round(remaining_budget, 2),
            'category_budgets': category_budgets,
            'active_alerts': active_alerts
        }

    @app.route('/login')
    def login():
        return render_template('login.html')

    @app.route('/signup')
    def signup():
        return render_template('signup.html')

    @app.route('/')
    def dashboard():
        today = date.today()

        total_income_all = db.session.query(
            func.coalesce(func.sum(Transaction.amount), 0.0)
        ).filter(Transaction.transaction_type == 'Income').scalar() or 0.0

        total_expense_all = db.session.query(
            func.coalesce(func.sum(Transaction.amount), 0.0)
        ).filter(Transaction.transaction_type == 'Expense').scalar() or 0.0

        total_balance = total_income_all - total_expense_all

        current_month_income = db.session.query(
            func.coalesce(func.sum(Transaction.amount), 0.0)
        ).filter(
            Transaction.transaction_type == 'Income',
            extract('month', Transaction.date) == today.month,
            extract('year', Transaction.date) == today.year
        ).scalar() or 0.0

        current_month_expense = db.session.query(
            func.coalesce(func.sum(Transaction.amount), 0.0)
        ).filter(
            Transaction.transaction_type == 'Expense',
            extract('month', Transaction.date) == today.month,
            extract('year', Transaction.date) == today.year
        ).scalar() or 0.0

        total_transactions_count = Transaction.query.count()
        current_month_transactions_count = Transaction.query.filter(
            extract('month', Transaction.date) == today.month,
            extract('year', Transaction.date) == today.year
        ).count()

        budget_summary = calculate_budget_summary(today.month, today.year)

        recent_transactions = Transaction.query.order_by(
            Transaction.date.desc(), Transaction.id.desc()
        ).limit(6).all()

        return render_template(
            'index.html',
            total_balance=total_balance,
            current_month_income=current_month_income,
            current_month_expense=current_month_expense,
            remaining_budget=budget_summary['remaining_budget'],
            overall_budget=budget_summary['overall_budget'],
            overall_percent=budget_summary['overall_percent'],
            budget_summary=budget_summary,
            recent_transactions=recent_transactions,
            total_transactions_count=total_transactions_count,
            current_month_transactions_count=current_month_transactions_count
        )

    @app.route('/transactions')
    def transactions():
        q = request.args.get('q', '').strip()
        t_type = request.args.get('type', '').strip()
        cat = request.args.get('category', '').strip()
        start_date = request.args.get('start_date', '').strip()
        end_date = request.args.get('end_date', '').strip()

        query = Transaction.query

        if q:
            query = query.filter(Transaction.title.ilike(f'%{q}%'))
        if t_type in ['Income', 'Expense']:
            query = query.filter(Transaction.transaction_type == t_type)
        if cat:
            query = query.filter(Transaction.category == cat)
        if start_date:
            try:
                s_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                query = query.filter(Transaction.date >= s_date)
            except ValueError:
                pass
        if end_date:
            try:
                e_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                query = query.filter(Transaction.date <= e_date)
            except ValueError:
                pass

        all_transactions = query.order_by(Transaction.date.desc(), Transaction.id.desc()).all()
        db_total_count = Transaction.query.count()

        filtered_income = sum(t.amount for t in all_transactions if t.transaction_type == 'Income')
        filtered_expense = sum(t.amount for t in all_transactions if t.transaction_type == 'Expense')
        filtered_net = filtered_income - filtered_expense

        return render_template(
            'transactions.html',
            transactions=all_transactions,
            total_count=len(all_transactions),
            db_total_count=db_total_count,
            filtered_income=filtered_income,
            filtered_expense=filtered_expense,
            filtered_net=filtered_net,
            filter_q=q,
            filter_type=t_type,
            filter_cat=cat,
            filter_start_date=start_date,
            filter_end_date=end_date
        )

    @app.route('/transactions/add', methods=['POST'])
    def add_transaction():
        title = request.form.get('title', '').strip()
        amount_raw = request.form.get('amount', '').strip()
        transaction_type = request.form.get('transaction_type', '').strip()
        category = request.form.get('category', '').strip()
        trans_date_raw = request.form.get('date', '').strip()
        description = request.form.get('description', '').strip()

        if not title:
            flash('Transaction title is required.', 'danger')
            return redirect(request.referrer or url_for('dashboard'))

        if transaction_type not in ['Income', 'Expense']:
            flash('Invalid transaction type selected.', 'danger')
            return redirect(request.referrer or url_for('dashboard'))

        try:
            amount = float(amount_raw)
            if amount <= 0:
                flash('Transaction amount must be greater than zero.', 'danger')
                return redirect(request.referrer or url_for('dashboard'))
        except (ValueError, TypeError):
            flash('Please enter a valid numeric amount.', 'danger')
            return redirect(request.referrer or url_for('dashboard'))

        valid_cats = Config.EXPENSE_CATEGORIES if transaction_type == 'Expense' else Config.INCOME_CATEGORIES
        if category not in valid_cats:
            flash(f'Please select a valid {transaction_type} category.', 'danger')
            return redirect(request.referrer or url_for('dashboard'))

        try:
            trans_date = datetime.strptime(trans_date_raw, '%Y-%m-%d').date() if trans_date_raw else date.today()
        except ValueError:
            flash('Invalid date format provided.', 'danger')
            return redirect(request.referrer or url_for('dashboard'))

        new_trans = Transaction(
            title=title,
            amount=round(amount, 2),
            transaction_type=transaction_type,
            category=category,
            date=trans_date,
            description=description,
            is_demo=False
        )

        db.session.add(new_trans)
        db.session.commit()

        flash(f'Successfully recorded {transaction_type.lower()} "{title}" of ₹{amount:,.2f}!', 'success')
        return redirect(request.referrer or url_for('transactions'))

    @app.route('/transactions/delete/<int:id>', methods=['POST'])
    def delete_transaction(id):
        trans = db.session.get(Transaction, id)
        if not trans:
            flash('Transaction not found.', 'danger')
            return redirect(request.referrer or url_for('transactions'))
        db.session.delete(trans)
        db.session.commit()
        flash(f'Transaction "{trans.title}" was deleted successfully.', 'info')
        return redirect(request.referrer or url_for('transactions'))

    @app.route('/budgets', methods=['GET'])
    def budgets():
        today = date.today()
        month = request.args.get('month', today.month, type=int)
        year = request.args.get('year', today.year, type=int)

        budget_summary = calculate_budget_summary(month, year)
        budget_records = Budget.query.filter_by(month=month, year=year).all()

        return render_template(
            'budgets.html',
            selected_month=month,
            selected_year=year,
            budget_summary=budget_summary,
            budget_records=budget_records
        )

    @app.route('/budgets/add', methods=['POST'])
    def add_budget():
        category = request.form.get('category', '').strip()
        amount_raw = request.form.get('amount', '').strip()
        month_raw = request.form.get('month', '').strip()
        year_raw = request.form.get('year', '').strip()

        allowed_categories = ['Overall'] + Config.EXPENSE_CATEGORIES
        if category not in allowed_categories:
            flash('Please select a valid budget category.', 'danger')
            return redirect(url_for('budgets'))

        try:
            amount = float(amount_raw)
            if amount <= 0:
                flash('Budget amount must be a positive number.', 'danger')
                return redirect(url_for('budgets'))
        except (ValueError, TypeError):
            flash('Please enter a valid numeric budget amount.', 'danger')
            return redirect(url_for('budgets'))

        try:
            month = int(month_raw)
            year = int(year_raw)
            if not (1 <= month <= 12 and year >= 2020):
                raise ValueError
        except ValueError:
            flash('Invalid month or year selected.', 'danger')
            return redirect(url_for('budgets'))

        existing_budget = Budget.query.filter_by(
            category=category, month=month, year=year
        ).first()

        if existing_budget:
            existing_budget.amount = round(amount, 2)
            flash(f'Updated budget limit for {category} to ₹{amount:,.2f}.', 'success')
        else:
            new_budget = Budget(
                category=category,
                amount=round(amount, 2),
                month=month,
                year=year
            )
            db.session.add(new_budget)
            flash(f'Set new budget limit for {category} to ₹{amount:,.2f}.', 'success')

        db.session.commit()
        return redirect(url_for('budgets', month=month, year=year))

    @app.route('/budgets/delete/<int:id>', methods=['POST'])
    def delete_budget(id):
        budget_obj = db.session.get(Budget, id)
        if not budget_obj:
            flash('Budget not found.', 'danger')
            return redirect(url_for('budgets'))
        m = budget_obj.month
        y = budget_obj.year
        cat = budget_obj.category
        db.session.delete(budget_obj)
        db.session.commit()
        flash(f'Budget limit for {cat} was removed.', 'info')
        return redirect(url_for('budgets', month=m, year=y))

    @app.route('/reports')
    def reports():
        today = date.today()
        month = request.args.get('month', today.month, type=int)
        year = request.args.get('year', today.year, type=int)

        month_income = db.session.query(
            func.coalesce(func.sum(Transaction.amount), 0.0)
        ).filter(
            Transaction.transaction_type == 'Income',
            extract('month', Transaction.date) == month,
            extract('year', Transaction.date) == year
        ).scalar() or 0.0

        month_expense = db.session.query(
            func.coalesce(func.sum(Transaction.amount), 0.0)
        ).filter(
            Transaction.transaction_type == 'Expense',
            extract('month', Transaction.date) == month,
            extract('year', Transaction.date) == year
        ).scalar() or 0.0

        net_savings = month_income - month_expense
        savings_rate = round((net_savings / month_income * 100), 1) if month_income > 0 else 0.0

        category_spending = db.session.query(
            Transaction.category,
            func.coalesce(func.sum(Transaction.amount), 0.0).label('total')
        ).filter(
            Transaction.transaction_type == 'Expense',
            extract('month', Transaction.date) == month,
            extract('year', Transaction.date) == year
        ).group_by(Transaction.category).order_by(func.sum(Transaction.amount).desc()).all()

        category_data = []
        for cat, amt in category_spending:
            cat_pct = round((amt / month_expense * 100), 1) if month_expense > 0 else 0.0
            category_data.append({
                'category': cat,
                'amount': float(amt),
                'percent': cat_pct,
                'icon': Config.CATEGORY_ICONS.get(cat, 'bi-tag-fill'),
                'color': Config.CATEGORY_COLORS.get(cat, '#64748b')
            })

        month_transactions = Transaction.query.filter(
            extract('month', Transaction.date) == month,
            extract('year', Transaction.date) == year
        ).order_by(Transaction.date.desc(), Transaction.id.desc()).all()

        return render_template(
            'reports.html',
            selected_month=month,
            selected_year=year,
            month_income=month_income,
            month_expense=month_expense,
            net_savings=net_savings,
            savings_rate=savings_rate,
            category_data=category_data,
            transactions=month_transactions
        )

    @app.route('/export/csv')
    def export_csv():
        transactions = Transaction.query.order_by(Transaction.date.desc()).all()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', 'Title', 'Amount', 'Type', 'Category', 'Date', 'Description'])

        for t in transactions:
            writer.writerow([
                t.id,
                t.title,
                f"{t.amount:.2f}",
                t.transaction_type,
                t.category,
                t.date.strftime('%Y-%m-%d'),
                t.description or ''
            ])

        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=SpendSmart_Transactions.csv'}
        )

    @app.route('/api/dashboard')
    def api_dashboard():
        today = date.today()
        summary = calculate_budget_summary(today.month, today.year)

        total_income = db.session.query(
            func.coalesce(func.sum(Transaction.amount), 0.0)
        ).filter(Transaction.transaction_type == 'Income').scalar() or 0.0

        total_expense = db.session.query(
            func.coalesce(func.sum(Transaction.amount), 0.0)
        ).filter(Transaction.transaction_type == 'Expense').scalar() or 0.0

        return jsonify({
            'total_balance': round(total_income - total_expense, 2),
            'total_income': round(total_income, 2),
            'total_expense': round(total_expense, 2),
            'remaining_budget': summary['remaining_budget'],
            'overall_budget': summary['overall_budget'],
            'overall_percent': summary['overall_percent'],
            'alerts': summary['active_alerts']
        })

    @app.route('/api/charts')
    def api_charts():
        today = date.today()
        target_month = request.args.get('month', today.month, type=int)
        target_year = request.args.get('year', today.year, type=int)

        expense_query = db.session.query(
            Transaction.category,
            func.coalesce(func.sum(Transaction.amount), 0.0)
        ).filter(
            Transaction.transaction_type == 'Expense',
            extract('month', Transaction.date) == target_month,
            extract('year', Transaction.date) == target_year
        ).group_by(Transaction.category).all()

        expense_labels = []
        expense_values = []
        expense_colors = []

        for cat, amt in expense_query:
            if amt > 0:
                expense_labels.append(cat)
                expense_values.append(round(float(amt), 2))
                expense_colors.append(Config.CATEGORY_COLORS.get(cat, '#3b82f6'))

        has_expenses = len(expense_labels) > 0

        months_labels = []
        income_series = []
        expense_series = []

        curr_m = today.month
        curr_y = today.year
        months_to_fetch = []
        for i in range(5, -1, -1):
            m = curr_m - i
            y = curr_y
            while m <= 0:
                m += 12
                y -= 1
            months_to_fetch.append((m, y))

        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

        has_bar_data = False
        for m, y in months_to_fetch:
            months_labels.append(f"{month_names[m-1]} {y % 100:02d}")

            m_inc = db.session.query(
                func.coalesce(func.sum(Transaction.amount), 0.0)
            ).filter(
                Transaction.transaction_type == 'Income',
                extract('month', Transaction.date) == m,
                extract('year', Transaction.date) == y
            ).scalar() or 0.0

            m_exp = db.session.query(
                func.coalesce(func.sum(Transaction.amount), 0.0)
            ).filter(
                Transaction.transaction_type == 'Expense',
                extract('month', Transaction.date) == m,
                extract('year', Transaction.date) == y
            ).scalar() or 0.0

            if m_inc > 0 or m_exp > 0:
                has_bar_data = True

            income_series.append(round(float(m_inc), 2))
            expense_series.append(round(float(m_exp), 2))

        return jsonify({
            'doughnut': {
                'labels': expense_labels,
                'data': expense_values,
                'backgroundColor': expense_colors,
                'hasData': has_expenses
            },
            'bar': {
                'labels': months_labels,
                'income': income_series,
                'expenses': expense_series,
                'hasData': has_bar_data
            }
        })

    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
