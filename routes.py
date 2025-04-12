import os
import datetime
import pandas as pd
import json
import io
import csv
import logging
from flask import render_template, request, redirect, url_for, jsonify, flash, session, Response
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db, MockDB, get_user_by_email, create_user, verify_password
from models import User, Expense
from utils import generate_spending_tips, generate_category_chart, generate_trend_chart, get_expense_statistics

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Add current date to all templates
@app.context_processor
def inject_now():
    return {'now': datetime.datetime.now()}

# Main routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    # Get all possible auth data from the request
    email = request.json.get('email')
    password = request.json.get('password')
    is_registration = request.json.get('isRegistration', False)
    
    logging.debug(f"Login request: email present: {bool(email)}")
    
    try:
        # Email/password login or registration (server-side)
        if email and password:
            # Create a deterministic user ID from email for consistency
            uid = f"email-user-{email.replace('@', '-').replace('.', '-')}"
            display_name = email.split('@')[0]
            
            # For registration, check if creating a new user
            if is_registration:
                logging.info(f"Registering new email user: {email}")
                
                # Check if user already exists
                existing_user = get_user_by_email(email)
                if existing_user:
                    return jsonify({'success': False, 'error': 'User already exists'}), 400
                
                # Create new user
                uid = create_user(email, password, display_name)
            else:
                # This is a login - verify the password
                user_data = get_user_by_email(email)
                if not user_data or not verify_password(user_data.get('passwordHash', ''), password):
                    return jsonify({'success': False, 'error': 'Invalid email or password'}), 401
                
                uid = user_data.get('id')
                display_name = user_data.get('displayName', email.split('@')[0])
            
            # Create User object and log them in
            user = User(
                uid=uid,
                email=email,
                display_name=display_name
            )
            
            login_user(user, remember=False)
            session['user_id'] = uid
            
            return jsonify({'success': True, 'redirect': url_for('dashboard')})
        else:
            return jsonify({'success': False, 'error': 'Missing authentication data'}), 400
    
    except Exception as e:
        logging.error(f"Login error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 401

@app.route('/google-login')
def google_login():
    """Redirect to Google OAuth route"""
    return redirect(url_for('google_oauth.login'))

@app.route('/demo-login')
def demo_login():
    """Direct demo login route for development without Firebase."""
    logging.info("Demo login route activated")
    try:
        # Create a demo user with hardcoded ID (no Firebase needed)
        uid = "demo-user-id"
        demo_email = "demo@example.com"
        demo_name = "Demo User"
        
        logging.info(f"Creating demo user with ID: {uid}")
        
        # Skip DB operations and directly create the user object
        # This prevents timeouts when trying to access Firestore
        user = User(
            uid=uid,
            email=demo_email,
            display_name=demo_name
        )
        
        # Log in the user with Flask-Login
        logging.info("Calling login_user with demo user")
        login_successful = login_user(user, remember=False)  # Don't remember user between sessions
        
        if login_successful:
            logging.info("Demo login successful")
            # Add a session value for additional verification
            session['user_id'] = uid
            session['is_demo'] = True
            session.permanent = False  # Session will expire when browser closes
            
            # Create some demo expenses in memory
            logging.info("Creating demo expenses")
            expenses_collection = db.collection('expenses')
            
            # Demo expenses data
            demo_expenses = [
                {
                    'user_id': uid,
                    'amount': 25.99,
                    'category': 'Food',
                    'date': datetime.datetime.now() - datetime.timedelta(days=1),
                    'description': 'Grocery shopping'
                },
                {
                    'user_id': uid,
                    'amount': 45.00,
                    'category': 'Transport',
                    'date': datetime.datetime.now() - datetime.timedelta(days=2),
                    'description': 'Gas'
                },
                {
                    'user_id': uid,
                    'amount': 9.99,
                    'category': 'Entertainment',
                    'date': datetime.datetime.now() - datetime.timedelta(days=3),
                    'description': 'Movie ticket'
                }
            ]
            
            # Add demo expenses
            for expense in demo_expenses:
                expenses_collection.add(expense)
            
            # Flash a message to the user
            flash('Logged in as demo user for development purposes.', 'info')
            return redirect(url_for('dashboard'))
        else:
            logging.error("Demo login_user call failed")
            flash("Demo login failed: login_user returned False", "danger")
            return redirect(url_for('index'))
    
    except Exception as e:
        logging.error(f"Demo login error: {str(e)}")
        flash(f"Demo login failed: {str(e)}", "danger")
        return redirect(url_for('index'))

@app.route('/logout')
@login_required
def logout():
    # Clear all session data
    user_id = current_user.id  # Store for logging
    logout_user()
    
    # Remove all session data
    session.clear()
    
    # Also remove Flask remember me cookie
    response = redirect(url_for('index'))
    response.delete_cookie('remember_token')
    
    # Log and flash message
    logging.info(f"User {user_id} logged out successfully")
    flash('You have been logged out. Please sign in again.', 'info')
    
    return response

@app.route('/dashboard')
@login_required
def dashboard():
    # Get current date for filtering
    today = datetime.datetime.now().date()
    current_month_start = datetime.datetime(today.year, today.month, 1)

    # Prepare empty data for fallback
    recent_expenses = []
    all_expenses = []
    stats = {'total': 0, 'average_daily': 0, 'top_category': 'None', 'largest_expense': 0}
    category_chart = None
    tips = ['Start tracking your expenses to get personalized spending tips!']
    
    # Query expenses for current month
    try:
        # Check if we're in demo mode
        if session.get('is_demo', False) and isinstance(db, MockDB):
            logging.info("Using demo data for dashboard")
            
            # Get all expenses from mock DB
            expenses_docs = db.collection('expenses').stream()
            # Filter in memory for demo mode
            filtered_expenses = []
            
            for doc in expenses_docs:
                data = doc.to_dict()
                if data.get('user_id') == current_user.id:
                    filtered_expenses.append((doc.id, data))
            
            # Sort by date descending (in memory)
            filtered_expenses.sort(key=lambda x: x[1].get('date', datetime.datetime.now()), reverse=True)
            
            # Get recent 5 expenses for display
            for doc_id, expense_data in filtered_expenses[:5]:
                expense = Expense.from_dict(doc_id, expense_data)
                # Convert date to string format
                if isinstance(expense.date, datetime.datetime):
                    date_str = expense.date.strftime('%Y-%m-%d')
                else:
                    date_str = str(expense.date)
                
                recent_expenses.append({
                    'id': doc_id,
                    'amount': expense.amount,
                    'category': expense.category,
                    'date': date_str,
                    'description': expense.description
                })
            
            # Create expense objects for all expenses
            all_expenses = [Expense.from_dict(doc_id, data) for doc_id, data in filtered_expenses]
        else:
            # Normal mode with Firestore - show all expenses without date limitation
            expenses_ref = db.collection('expenses') \
                .where('user_id', '==', current_user.id) \
                .order_by('date', direction='DESCENDING')
            
            # Get all expenses for the user (no limit)
            recent_expenses_docs = expenses_ref.stream()
            
            for doc in recent_expenses_docs:
                expense_data = doc.to_dict()
                expense = Expense.from_dict(doc.id, expense_data)
                # Convert Firestore timestamp to datetime
                if isinstance(expense.date, datetime.datetime):
                    expense_data['date'] = expense.date.strftime('%Y-%m-%d')
                recent_expenses.append({
                    'id': doc.id,
                    'amount': expense.amount,
                    'category': expense.category,
                    'date': expense_data['date'],
                    'description': expense.description
                })
            
            # Get expense statistics
            all_expenses_docs = expenses_ref.stream()
            all_expenses = [Expense.from_dict(doc.id, doc.to_dict()) for doc in all_expenses_docs]
        
        # Only calculate stats and charts if we have expenses
        if all_expenses:
            # Generate statistics
            stats = get_expense_statistics(all_expenses)
            
            # Generate category chart
            category_chart = generate_category_chart(all_expenses)
            
            # Generate spending tips
            tips = generate_spending_tips(all_expenses)
        
        return render_template(
            'dashboard.html',
            recent_expenses=recent_expenses,
            stats=stats,
            category_chart=category_chart,
            tips=tips
        )
        
    except Exception as e:
        logging.error(f"Dashboard error: {str(e)}")
        flash(f"Error loading dashboard: {str(e)}", "danger")
        return render_template('dashboard.html', error=str(e))

@app.route('/add-expense', methods=['GET', 'POST'])
@login_required
def add_expense():
    if request.method == 'POST':
        try:
            # Get form data
            amount = float(request.form.get('amount'))
            category = request.form.get('category')
            date_str = request.form.get('date')
            description = request.form.get('description', '')
            
            # Convert date string to date object
            date = datetime.datetime.strptime(date_str, '%Y-%m-%d')
            
            # Create expense object
            expense = Expense(
                id=None,
                user_id=current_user.id,
                amount=amount,
                category=category,
                date=date,
                description=description
            )
            
            # Save to Firestore
            db.collection('expenses').add(expense.to_dict())
            
            flash('Expense added successfully!', 'success')
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            flash(f'Error adding expense: {str(e)}', 'danger')
    
    # Define expense categories
    categories = ['Food', 'Transport', 'Bills', 'Education', 'Entertainment', 'Shopping', 'Health', 'Misc']
    
    return render_template('add_expense.html', categories=categories, today=datetime.date.today().strftime('%Y-%m-%d'))

@app.route('/edit-expense/<expense_id>', methods=['GET', 'POST'])
@login_required
def edit_expense(expense_id):
    expense_doc = db.collection('expenses').document(expense_id).get()
    
    if not expense_doc.exists:
        flash('Expense not found', 'danger')
        return redirect(url_for('dashboard'))
    
    expense_data = expense_doc.to_dict()
    
    # Verify that the expense belongs to the current user
    if expense_data.get('user_id') != current_user.id:
        flash('You do not have permission to edit this expense', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        try:
            # Get form data
            amount = float(request.form.get('amount'))
            category = request.form.get('category')
            date_str = request.form.get('date')
            description = request.form.get('description', '')
            
            # Convert date string to date object
            date = datetime.datetime.strptime(date_str, '%Y-%m-%d')
            
            # Update expense
            db.collection('expenses').document(expense_id).update({
                'amount': amount,
                'category': category,
                'date': date,
                'description': description
            })
            
            flash('Expense updated successfully!', 'success')
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            flash(f'Error updating expense: {str(e)}', 'danger')
    
    # Format date for the form
    if isinstance(expense_data.get('date'), datetime.datetime):
        expense_data['date'] = expense_data['date'].strftime('%Y-%m-%d')
    
    # Define expense categories
    categories = ['Food', 'Transport', 'Bills', 'Education', 'Entertainment', 'Shopping', 'Health', 'Misc']
    
    return render_template('edit_expense.html', expense=expense_data, expense_id=expense_id, categories=categories)

@app.route('/delete-expense/<expense_id>', methods=['POST'])
@login_required
def delete_expense(expense_id):
    try:
        # Get the expense document
        expense_doc = db.collection('expenses').document(expense_id).get()
        
        if not expense_doc.exists:
            return jsonify({'success': False, 'error': 'Expense not found'}), 404
        
        expense_data = expense_doc.to_dict()
        
        # Verify that the expense belongs to the current user
        if expense_data.get('user_id') != current_user.id:
            return jsonify({'success': False, 'error': 'Permission denied'}), 403
        
        # Delete the expense
        db.collection('expenses').document(expense_id).delete()
        
        return jsonify({'success': True})
        
    except Exception as e:
        logging.error(f"Error deleting expense: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/reports')
@login_required
def reports():
    try:
        # Get all expenses for the user
        expenses_ref = db.collection('expenses') \
            .where('user_id', '==', current_user.id) \
            .order_by('date', direction='DESCENDING')
        
        expenses_docs = expenses_ref.stream()
        all_expenses = [Expense.from_dict(doc.id, doc.to_dict()) for doc in expenses_docs]
        
        # Generate category chart
        category_chart = generate_category_chart(all_expenses)
        
        # Generate trend chart
        trend_chart = generate_trend_chart(all_expenses)
        
        # Get expense statistics
        stats = get_expense_statistics(all_expenses)
        
        # Generate spending tips
        tips = generate_spending_tips(all_expenses)
        
        return render_template(
            'reports.html',
            category_chart=category_chart,
            trend_chart=trend_chart,
            stats=stats,
            tips=tips
        )
        
    except Exception as e:
        logging.error(f"Reports error: {str(e)}")
        flash(f"Error generating reports: {str(e)}", "danger")
        return render_template('reports.html', error=str(e))

@app.route('/export-expenses')
@login_required
def export_expenses():
    try:
        # Get all expenses for the user
        expenses_ref = db.collection('expenses') \
            .where('user_id', '==', current_user.id) \
            .order_by('date', direction='DESCENDING')
        
        expenses_docs = expenses_ref.stream()
        
        # Create a DataFrame
        data = []
        for doc in expenses_docs:
            expense = doc.to_dict()
            # Convert date to string if it's a datetime
            if isinstance(expense.get('date'), datetime.datetime):
                expense['date'] = expense['date'].strftime('%Y-%m-%d')
            data.append({
                'Date': expense.get('date'),
                'Category': expense.get('category'),
                'Amount': expense.get('amount'),
                'Description': expense.get('description', '')
            })
        
        if not data:
            flash('No expenses to export', 'warning')
            return redirect(url_for('reports'))
        
        df = pd.DataFrame(data)
        
        # Create CSV in memory
        csv_data = io.StringIO()
        df.to_csv(csv_data, index=False)
        
        # Create response with CSV file
        response = Response(
            csv_data.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition': 'attachment; filename=expenses.csv',
                'Content-Type': 'text/csv'
            }
        )
        
        return response
        
    except Exception as e:
        logging.error(f"Export error: {str(e)}")
        flash(f"Error exporting expenses: {str(e)}", "danger")
        return redirect(url_for('reports'))
@app.route('/reset-password', methods=['POST'])
def reset_password():
    try:
        email = request.json.get('email')
        if not email:
            return jsonify({'success': False, 'error': 'Email is required'}), 400
            
        user = get_user_by_email(email)
        if not user:
            # Don't reveal if user exists
            return jsonify({'success': True})
            
        # In a real app, you would:
        # 1. Generate a reset token
        # 2. Save it to the database with an expiration
        # 3. Send an email with reset instructions
        
        # For demo, we'll just return success
        return jsonify({'success': True})
        
    except Exception as e:
        logging.error(f"Password reset error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
