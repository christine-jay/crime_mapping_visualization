from flask import Blueprint, render_template, request, redirect, url_for, flash
import mysql.connector
from werkzeug.security import generate_password_hash
from config import Config

register_bp = Blueprint('register', __name__)

@register_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        user_email = request.form['user_email']
        password = request.form['password']
        role = request.form.get('role', 'admin')
        hashed_password = generate_password_hash(password)
        conn = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB
        )
        cursor = conn.cursor(dictionary=True)
        # Check for duplicate username or email
        cursor.execute('SELECT * FROM user WHERE username = %s OR user_email = %s', (username, user_email))
        if cursor.fetchone():
            flash('Username or email already exists.', 'danger')
            cursor.close()
            conn.close()
            return render_template('register.html')
        cursor.execute('INSERT INTO user (name, username, password, role, user_email) VALUES (%s, %s, %s, %s, %s)',
                       (name, username, hashed_password, role, user_email))
        conn.commit()
        cursor.close()
        conn.close()
        flash('Admin account created! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('register.html') 