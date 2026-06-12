# routes/auth.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from database import supabase_client
import functools

auth_bp = Blueprint('auth', __name__)

# Helper to check login required
def login_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

# Helper to check role specific access
def role_required(roles):
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user' not in session:
                flash("Please log in to access this page.", "warning")
                return redirect(url_for('auth.login'))
            user_role = session['user'].get('role')
            if user_role not in roles:
                flash("Access denied. You do not have permissions for this section.", "danger")
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if 'user' in session:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'citizen')
        
        if not name or not email or not password:
            flash("All fields are required.", "danger")
            return render_template('register.html')
            
        # Check if email already exists
        existing_user = supabase_client.get_user_by_email(email)
        if existing_user:
            flash("Email address is already registered.", "danger")
            return render_template('register.html')
            
        # Create user
        pw_hash = generate_password_hash(password)
        new_user = supabase_client.create_user(name, email, pw_hash, role)
        
        if new_user:
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for('auth.login'))
        else:
            flash("Registration failed. Please try again later.", "danger")
            
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash("Please fill in all fields.", "danger")
            return render_template('login.html')
            
        user = supabase_client.get_user_by_email(email)
        if user and check_password_hash(user.get('password_hash', ''), password):
            # Login successful
            session['user'] = {
                'id': user.get('id'),
                'name': user.get('name'),
                'email': user.get('email'),
                'role': user.get('role')
            }
            # Permanent session
            session.permanent = True
            flash(f"Welcome back, {user.get('name')}!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid email or password.", "danger")
            
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.pop('user', None)
    flash("You have been logged out successfully.", "info")
    return redirect(url_for('auth.login'))
