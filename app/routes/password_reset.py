from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_mail import Message
import mysql.connector
import secrets
import datetime
from werkzeug.security import generate_password_hash
from config import Config
from app import mail

password_reset_bp = Blueprint('password_reset', __name__)

@password_reset_bp.route('/reset_password', methods=['GET', 'POST'])
def reset_password_request():
    if request.method == 'POST':
        email = request.form['email']
        conn = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB
        )
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM user WHERE user_email = %s', (email,))
        user = cursor.fetchone()
        if user:
            token = secrets.token_urlsafe(32)
            expiration = datetime.datetime.now() + datetime.timedelta(hours=1)
            cursor.execute('INSERT INTO password_reset (user_id, reset_token, expiration_time, is_used, created_at) VALUES (%s, %s, %s, %s, %s)',
                (user['user_id'], token, expiration, False, datetime.datetime.now()))
            conn.commit()
            reset_link = url_for('password_reset.reset_password', token=token, _external=True)
            msg = Message('Password Reset Request', recipients=[email])
            msg.body = f'Click the link to reset your password: {reset_link}'
            mail.send(msg)
            flash('Password reset link sent to your email.', 'info')
        else:
            flash('Email not found.', 'danger')
        cursor.close()
        conn.close()
    return render_template('reset_password_request.html')

@password_reset_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    conn = mysql.connector.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB
    )
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM password_reset WHERE reset_token = %s AND is_used = 0 AND expiration_time > NOW()', (token,))
    reset = cursor.fetchone()
    if not reset:
        flash('Invalid or expired token.', 'danger')
        cursor.close()
        conn.close()
        return redirect(url_for('password_reset.reset_password_request'))
    if request.method == 'POST':
        new_password = request.form['password']
        hashed = generate_password_hash(new_password)
        cursor.execute('UPDATE user SET password = %s WHERE user_id = %s', (hashed, reset['user_id']))
        cursor.execute('UPDATE password_reset SET is_used = 1 WHERE reset_id = %s', (reset['reset_id'],))
        conn.commit()
        flash('Password reset successful!', 'success')
        cursor.close()
        conn.close()
        return redirect(url_for('auth.login'))
    cursor.close()
    conn.close()
    return render_template('reset_password.html', token=token) 