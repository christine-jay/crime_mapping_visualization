from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from flask_mail import Message
from config import Config
from app import mail
import mysql.connector
import random
import string
import time
import traceback

auth_bp = Blueprint('auth', __name__)

def get_db_connection():
    try:
        return mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB
        )
    except mysql.connector.Error as err:
        current_app.logger.error(f"Database connection error: {err}")
        raise

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                username = request.form.get('username')
                password = request.form.get('password')
                
                if not username or not password:
                    return jsonify({
                        'success': False,
                        'message': 'Username and password are required'
                    })
                
                conn = get_db_connection()
                cursor = conn.cursor(dictionary=True)
                cursor.execute('SELECT * FROM user WHERE username = %s', (username,))
                user_data = cursor.fetchone()
                cursor.close()
                conn.close()
                
                if not user_data:
                    current_app.logger.warning(f"Login attempt failed: User {username} not found")
                    return jsonify({
                        'success': False,
                        'message': 'Invalid username or password'
                    })
                
                if not check_password_hash(user_data['password'], password):
                    current_app.logger.warning(f"Login attempt failed: Invalid password for user {username}")
                    return jsonify({
                        'success': False,
                        'message': 'Invalid username or password'
                    })
                
                # Generate and store OTP
                try:
                    current_app.logger.info("Starting OTP generation process")
                    otp = ''.join(random.choices(string.digits, k=6))
                    otp_expiry = int(time.time()) + 300  # 5 minutes in seconds
                    current_app.logger.info(f"Generated OTP: {otp}, Expiry: {otp_expiry}")
                    
                    current_app.logger.info("Attempting database connection for OTP storage")
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    
                    current_app.logger.info(f"Updating OTP for user_id: {user_data['user_id']}")
                    update_query = 'UPDATE user SET otp = %s, otp_expiry = %s WHERE user_id = %s'
                    update_values = (otp, otp_expiry, user_data['user_id'])
                    current_app.logger.info(f"Query: {update_query}, Values: {update_values}")
                    
                    cursor.execute(update_query, update_values)
                    current_app.logger.info("OTP update query executed")
                    
                    conn.commit()
                    current_app.logger.info("Database changes committed")
                    
                    cursor.close()
                    conn.close()
                    current_app.logger.info("Database connection closed")
                    
                    # For development, log the OTP
                    current_app.logger.info(f"OTP generation successful for user {username}")
                    
                    # Send OTP via email
                    try:
                        msg = Message(
                            'Your OTP for Login',
                            recipients=[user_data['user_email']],
                            body=f'Your OTP is: {otp}\n\nThis OTP will expire in 5 minutes.\n\nIf you did not request this OTP, please ignore this email.'
                        )
                        mail.send(msg)
                        current_app.logger.info(f"OTP email sent to {user_data['user_email']}")
                    except Exception as email_err:
                        current_app.logger.error(f"Failed to send OTP email: {str(email_err)}")
                        # Don't fail the login if email fails, just log it
                    
                    return jsonify({'success': True})
                except mysql.connector.Error as db_err:
                    current_app.logger.error(f"Database error during OTP generation: {str(db_err)}\nError Code: {db_err.errno}\nSQL State: {db_err.sqlstate}\n{traceback.format_exc()}")
                    if conn:
                        try:
                            conn.rollback()
                            current_app.logger.info("Database transaction rolled back")
                        except:
                            pass
                        try:
                            conn.close()
                            current_app.logger.info("Database connection closed after error")
                        except:
                            pass
                    return jsonify({
                        'success': False,
                        'message': 'Database error while generating OTP. Please try again.'
                    })
                except Exception as e:
                    current_app.logger.error(f"Unexpected error during OTP generation: {str(e)}\n{traceback.format_exc()}")
                    if 'conn' in locals() and conn:
                        try:
                            conn.close()
                            current_app.logger.info("Database connection closed after error")
                        except:
                            pass
                    return jsonify({
                        'success': False,
                        'message': 'Error generating OTP. Please try again.'
                    })
                    
            except mysql.connector.Error as err:
                current_app.logger.error(f"Database error during login: {err}\n{traceback.format_exc()}")
                return jsonify({
                    'success': False,
                    'message': 'Database error. Please try again.'
                })
            except Exception as e:
                current_app.logger.error(f"Unexpected error during login: {str(e)}\n{traceback.format_exc()}")
                return jsonify({
                    'success': False,
                    'message': 'An unexpected error occurred. Please try again.'
                })
    
    return render_template('login.html')

@auth_bp.route('/otp', methods=['POST'])
def otp():
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return jsonify({'success': False, 'message': 'Invalid request'})
    
    data = request.get_json()
    otp = data.get('otp')
    
    if not otp:
        return jsonify({'success': False, 'message': 'OTP is required'})
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM user WHERE otp = %s AND otp_expiry > %s',
                  (otp, int(time.time())))
    user_data = cursor.fetchone()
    
    if user_data:
        # Clear OTP after successful verification
        cursor.execute('UPDATE user SET otp = NULL, otp_expiry = NULL WHERE user_id = %s',
                      (user_data['user_id'],))
        conn.commit()
        
        # Create a simple user object with required Flask-Login attributes
        class User:
            def __init__(self, user_data):
                self.id = user_data['user_id']
                self.is_authenticated = True
                self.is_active = True
                self.is_anonymous = False
                self.role = user_data['role']
                self.username = user_data['username']
            
            def get_id(self):
                return str(self.id)
        
        user = User(user_data)
        login_user(user)
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'redirect': url_for('main.dashboard')
        })
    else:
        cursor.close()
        conn.close()
        return jsonify({
            'success': False,
            'message': 'Invalid or expired OTP'
        })

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@auth_bp.route('/debug/check-user/<username>')
def check_user(username):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT user_id, username, role FROM user WHERE username = %s', (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user:
            return jsonify({
                'exists': True,
                'user_id': user['user_id'],
                'username': user['username'],
                'role': user['role']
            })
        return jsonify({
            'exists': False,
            'message': f'User {username} not found'
        })
    except Exception as e:
        current_app.logger.error(f"Error checking user: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        try:
            # Get form data
            name = request.form.get('name')
            username = request.form.get('username')
            user_email = request.form.get('user_email')
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Get current user data
            cursor.execute('SELECT * FROM user WHERE user_id = %s', (current_user.id,))
            user_data = cursor.fetchone()
            
            if not user_data:
                flash('User not found', 'danger')
                return redirect(url_for('auth.profile'))
            
            # Check if username or email already exists (excluding current user)
            cursor.execute('SELECT * FROM user WHERE (username = %s OR user_email = %s) AND user_id != %s', 
                         (username, user_email, current_user.id))
            if cursor.fetchone():
                flash('Username or email already exists', 'danger')
                cursor.close()
                conn.close()
                return redirect(url_for('auth.profile'))
            
            # Update basic info
            cursor.execute('UPDATE user SET name = %s, username = %s, user_email = %s WHERE user_id = %s',
                         (name, username, user_email, current_user.id))
            
            # Handle password change if provided
            if current_password and new_password and confirm_password:
                if not check_password_hash(user_data['password'], current_password):
                    flash('Current password is incorrect', 'danger')
                    cursor.close()
                    conn.close()
                    return redirect(url_for('auth.profile'))
                
                if new_password != confirm_password:
                    flash('New passwords do not match', 'danger')
                    cursor.close()
                    conn.close()
                    return redirect(url_for('auth.profile'))
                
                if len(new_password) < 6:
                    flash('New password must be at least 6 characters long', 'danger')
                    cursor.close()
                    conn.close()
                    return redirect(url_for('auth.profile'))
                
                hashed_password = generate_password_hash(new_password)
                cursor.execute('UPDATE user SET password = %s WHERE user_id = %s',
                             (hashed_password, current_user.id))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            flash('Profile updated successfully', 'success')
            return redirect(url_for('auth.profile'))
            
        except Exception as e:
            current_app.logger.error(f"Error updating profile: {str(e)}")
            flash('An error occurred while updating profile', 'danger')
            return redirect(url_for('auth.profile'))
    
    # GET request - show profile form
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM user WHERE user_id = %s', (current_user.id,))
        user_data = cursor.fetchone()
        cursor.close()
        conn.close()
        
        return render_template('profile.html', user=user_data)
    except Exception as e:
        current_app.logger.error(f"Error loading profile: {str(e)}")
        flash('An error occurred while loading profile', 'danger')
        return redirect(url_for('main.dashboard'))

@auth_bp.route('/create_user', methods=['GET', 'POST'])
@login_required
def create_user():
    # Only allow admin users to create new users
    if current_user.role != 'admin':
        flash('You do not have permission to create users', 'danger')
        return redirect(url_for('main.dashboard'))
        
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            username = request.form.get('username')
            user_email = request.form.get('user_email')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            role = request.form.get('role')
            
            # Validate input
            if not all([name, username, user_email, password, confirm_password, role]):
                flash('All fields are required', 'danger')
                return redirect(url_for('auth.create_user'))
                
            if password != confirm_password:
                flash('Passwords do not match', 'danger')
                return redirect(url_for('auth.create_user'))
                
            if len(password) < 6:
                flash('Password must be at least 6 characters long', 'danger')
                return redirect(url_for('auth.create_user'))
            
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Check for duplicate username or email
            cursor.execute('SELECT * FROM user WHERE username = %s OR user_email = %s', (username, user_email))
            if cursor.fetchone():
                flash('Username or email already exists', 'danger')
                cursor.close()
                conn.close()
                return redirect(url_for('auth.create_user'))
            
            # Create new user
            hashed_password = generate_password_hash(password)
            cursor.execute('''
                INSERT INTO user (name, username, password, role, user_email)
                VALUES (%s, %s, %s, %s, %s)
            ''', (name, username, hashed_password, role, user_email))
            
            # Log the user creation
            cursor.execute('''
                INSERT INTO audit_logs (user_id, action, table_affected, timestamp)
                VALUES (%s, %s, %s, NOW())
            ''', (current_user.id, 'CREATE_USER', 'user'))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            flash('User created successfully', 'success')
            return redirect(url_for('auth.create_user'))
            
        except Exception as e:
            current_app.logger.error(f"Error creating user: {str(e)}\n{traceback.format_exc()}")
            flash('An error occurred while creating the user', 'danger')
            return redirect(url_for('auth.create_user'))
    
    return render_template('register.html')

print(generate_password_hash('admin123')) 