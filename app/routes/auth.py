from flask import Blueprint, jsonify, request, current_app, render_template, redirect, url_for, flash, send_from_directory
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from flask_mail import Message
from config import Config
from app import mail
import mysql.connector
import random
import string
import time
import traceback
import os
import uuid

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

# API endpoints for React frontend
@auth_bp.route('/api/auth/login', methods=['POST'])
def api_login():
    try:
        data = request.get_json()
        username = data.get('email')  # React sends email as username
        password = data.get('password')
        
        if not username or not password:
            return jsonify({
                'success': False,
                'error': 'Username and password are required'
            }), 400
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM user WHERE username = %s OR user_email = %s', (username, username))
        user_data = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not user_data:
            return jsonify({
                'success': False,
                'error': 'Invalid username or password'
            }), 401
        
        if not check_password_hash(user_data['password'], password):
            return jsonify({
                'success': False,
                'error': 'Invalid username or password'
            }), 401
        
        # Create a simple user object
        class User:
            def __init__(self, user_data):
                self.id = user_data['user_id']
                self.is_authenticated = True
                self.is_active = True
                self.is_anonymous = False
                self.role = user_data['role']
                self.username = user_data['username']
                self.email = user_data['user_email']
                self.name = user_data['name']
            
            def get_id(self):
                return str(self.id)
        
        user = User(user_data)
        login_user(user)
        
        # Insert into audit_logs
        conn2 = get_db_connection()
        cursor2 = conn2.cursor()
        cursor2.execute(
            "INSERT INTO audit_logs (user_id, action, table_affected, timestamp) VALUES (%s, %s, %s, NOW())",
            (user_data['user_id'], 'LOGIN', 'user')
        )
        conn2.commit()
        cursor2.close()
        conn2.close()
        
        return jsonify({
            'success': True,
            'token': 'session-token',  # For React, we'll use session-based auth
            'user': {
                'id': user_data['user_id'],
                'username': user_data['username'],
                'email': user_data['user_email'],
                'name': user_data['name'],
                'role': user_data['role']
            }
        })
    except Exception as e:
        current_app.logger.error(f"API login error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'An error occurred during login'
        }), 500

@auth_bp.route('/api/auth/register', methods=['POST'])
def api_register():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['username', 'email', 'password', 'firstName', 'lastName']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': f'{field} is required'
                }), 400
        
        username = data['username']
        email = data['email']
        password = data['password']
        first_name = data['firstName']
        last_name = data['lastName']
        role = data.get('role', 'user')
        
        # Check if user already exists
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM user WHERE username = %s OR user_email = %s', (username, email))
        existing_user = cursor.fetchone()
        
        if existing_user:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Username or email already exists'
            }), 409
        
        # Create new user
        hashed_password = generate_password_hash(password)
        name = f"{first_name} {last_name}"
        
        cursor.execute('''
            INSERT INTO user (name, username, password, role, user_email)
            VALUES (%s, %s, %s, %s, %s)
        ''', (name, username, hashed_password, role, email))
        
        user_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'User registered successfully'
        })
    except Exception as e:
        current_app.logger.error(f"API register error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'An error occurred during registration'
        }), 500

@auth_bp.route('/api/auth/logout', methods=['POST'])
@login_required
def api_logout():
    try:
        logout_user()
        return jsonify({
            'success': True,
            'message': 'Logged out successfully'
        })
    except Exception as e:
        current_app.logger.error(f"API logout error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'An error occurred during logout'
        }), 500

@auth_bp.route('/api/user/profile')
@login_required
def api_user_profile():
    try:
        return jsonify({
            'id': current_user.id,
            'username': current_user.username,
            'email': getattr(current_user, 'email', ''),
            'name': getattr(current_user, 'name', ''),
            'role': current_user.role
        })
    except Exception as e:
        current_app.logger.error(f"API profile error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'An error occurred while fetching profile'
        }), 500

@auth_bp.route('/api/user/profile', methods=['PUT'])
@login_required
def api_update_profile():
    try:
        data = request.get_json()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Update user profile
        cursor.execute('''
            UPDATE user 
            SET name = %s, user_email = %s 
            WHERE user_id = %s
        ''', (data.get('name'), data.get('email'), current_user.id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Profile updated successfully'
        })
    except Exception as e:
        current_app.logger.error(f"API update profile error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'An error occurred while updating profile'
        }), 500

# Original template routes (keep these for existing functionality)
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
    try:
        user_id = current_user.id
        logout_user()
        # Insert into audit_logs
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO audit_logs (user_id, action, table_affected, timestamp) VALUES (%s, %s, %s, NOW())",
            (user_id, 'LOGOUT', 'user')
        )
        conn.commit()
        cursor.close()
        conn.close()
        flash('Logged out successfully.', 'success')
        return redirect(url_for('auth.login'))
    except Exception as e:
        current_app.logger.error(f"Error during logout: {str(e)}")
        flash('An error occurred during logout', 'danger')
        return redirect(url_for('main.dashboard'))

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

            # Handle profile picture upload
            profile_picture_path = user_data.get('profile_picture')
            if 'profile_picture' in request.files:
                file = request.files['profile_picture']
                if file and file.filename != '':
                    filename = secure_filename(file.filename)
                    unique_filename = f"{uuid.uuid4().hex}_{filename}"
                    upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
                    try:
                        file.save(upload_path)
                        profile_picture_path = unique_filename
                    except Exception as e:
                        current_app.logger.error(f"Failed to save profile picture: {e}")
                        flash('Failed to upload profile picture.', 'danger')
                        cursor.close()
                        conn.close()
                        return redirect(url_for('auth.profile'))

            # Update basic info and profile picture
            cursor.execute('UPDATE user SET name = %s, username = %s, user_email = %s, profile_picture = %s WHERE user_id = %s',
                         (name, username, user_email, profile_picture_path, current_user.id))

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

            # Log profile update
            conn2 = get_db_connection()
            cursor2 = conn2.cursor()
            cursor2.execute(
                "INSERT INTO audit_logs (user_id, action, table_affected, timestamp) VALUES (%s, %s, %s, NOW())",
                (current_user.id, 'UPDATE', 'user')
            )
            conn2.commit()
            cursor2.close()
            conn2.close()

            # If password was changed, log it
            if current_password and new_password and confirm_password and new_password == confirm_password and len(new_password) >= 6:
                conn3 = get_db_connection()
                cursor3 = conn3.cursor()
                cursor3.execute(
                    "INSERT INTO audit_logs (user_id, action, table_affected, timestamp) VALUES (%s, %s, %s, NOW())",
                    (current_user.id, 'PASSWORD_CHANGE', 'user')
                )
                conn3.commit()
                cursor3.close()
                conn3.close()

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
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        name = request.form.get('name')
        username = request.form.get('username')
        user_email = request.form.get('user_email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        role = request.form.get('role')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('auth.create_user'))

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user WHERE username = %s OR user_email = %s", (username, user_email))
        if cursor.fetchone():
            flash('Username or email already exists.', 'error')
            cursor.close()
            conn.close()
            return redirect(url_for('auth.create_user'))

        profile_picture_path = None
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file.filename != '':
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4().hex}_{filename}"
                upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
                
                try:
                    file.save(upload_path)
                    profile_picture_path = unique_filename
                except Exception as e:
                    current_app.logger.error(f"Failed to save profile picture: {e}")
                    flash('Failed to upload profile picture.', 'error')
                    return redirect(url_for('auth.create_user'))

        hashed_password = generate_password_hash(password)
        
        try:
            cursor.execute(
                "INSERT INTO user (name, username, user_email, password, role, profile_picture) VALUES (%s, %s, %s, %s, %s, %s)",
                (name, username, user_email, hashed_password, role, profile_picture_path)
            )
            # Insert into audit_logs
            cursor.execute(
                "INSERT INTO audit_logs (user_id, action, table_affected, timestamp) VALUES (%s, %s, %s, NOW())",
                (current_user.id, 'CREATE', 'user')
            )
            conn.commit()
            flash('User created successfully.', 'success')
        except mysql.connector.Error as err:
            flash(f'Error: {err}', 'error')
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('auth.create_user'))

    return render_template('register.html')

def send_password_reset_email(user_email, token):
    try:
        pass  # TODO: implement this function
    except Exception as e:
        current_app.logger.error(f"Error sending password reset email: {str(e)}")
        return False

@auth_bp.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename) 