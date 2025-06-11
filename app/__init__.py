from flask import Flask
from flask_mail import Mail
from flask_login import LoginManager
import mysql.connector
import os
from config import Config

# Initialize extensions
mail = Mail()
login_manager = LoginManager()

def create_database():
    try:
        # Connect without specifying database
        conn = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD
        )
        cursor = conn.cursor()
        
        # Create database if it doesn't exist
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {Config.MYSQL_DB}")
        cursor.close()
        conn.close()
        print(f"Database '{Config.MYSQL_DB}' created or already exists")
    except mysql.connector.Error as err:
        print(f"Error creating database: {err}")

def create_tables(app):
    try:
        conn = mysql.connector.connect(
            host=app.config['MYSQL_HOST'],
            user=app.config['MYSQL_USER'],
            password=app.config['MYSQL_PASSWORD'],
            database=app.config['MYSQL_DB']
        )
        cursor = conn.cursor()
        
        # Check if user table exists
        cursor.execute("SHOW TABLES LIKE 'user'")
        if not cursor.fetchone():
            # Create user table if not exists
            cursor.execute("""
CREATE TABLE user (
  user_id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  username VARCHAR(255) NOT NULL UNIQUE,
  password VARCHAR(255) NOT NULL,
  role VARCHAR(50) NOT NULL,
  user_email VARCHAR(255) NOT NULL UNIQUE,
  otp VARCHAR(6),
  otp_expiry INT
)
""")
        else:
            # Check and add OTP columns if they don't exist
            cursor.execute("SHOW COLUMNS FROM user LIKE 'otp'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE user ADD COLUMN otp VARCHAR(6)")
            
            cursor.execute("SHOW COLUMNS FROM user LIKE 'otp_expiry'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE user ADD COLUMN otp_expiry INT")
        
        # Create crime_report table if not exists
        cursor.execute("""
CREATE TABLE IF NOT EXISTS crime_report (
  report_id INT AUTO_INCREMENT PRIMARY KEY,
  barangay_name VARCHAR(255) NOT NULL,
  type_of_place VARCHAR(255) NOT NULL,
  date_reported DATE NOT NULL,
  time_reported TIME NOT NULL,
  date_committed DATE NOT NULL,
  time_committed TIME NOT NULL,
  offense VARCHAR(255) NOT NULL,
  type_of_crime VARCHAR(255) NOT NULL,
  classification_of_crime VARCHAR(255) NOT NULL,
  victim VARCHAR(255) NOT NULL,
  suspect VARCHAR(255) NOT NULL,
  narrative TEXT NOT NULL,
  status VARCHAR(50) NOT NULL,
  batch_id INT NOT NULL
)
""")
        # Create barangay table if not exists
        cursor.execute("""
CREATE TABLE IF NOT EXISTS barangay (
  barangay_id INT AUTO_INCREMENT PRIMARY KEY,
  barangay_name VARCHAR(255) NOT NULL UNIQUE,
  barangay_population INT NOT NULL,
  barangay_district VARCHAR(255) NOT NULL
)
""")
        
        cursor.execute("""
CREATE TABLE IF NOT EXISTS audit_logs (
  log_id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  action VARCHAR(255) NOT NULL,
  table_affected VARCHAR(255) NOT NULL,
  timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES user(user_id)
)
""")
        # Create password_reset table if not exists
        cursor.execute("""
CREATE TABLE IF NOT EXISTS password_reset (
  reset_id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  reset_token VARCHAR(255) NOT NULL UNIQUE,
  expiration_time TIMESTAMP NOT NULL,
  is_used BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES user(user_id)
)
""")
        conn.commit()
        cursor.close()
        conn.close()
        print("Tables created successfully")
    except mysql.connector.Error as err:
        print(f"Error creating tables: {err}")

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.secret_key = os.urandom(24)  # Generate a secure random secret key

    # Create database and tables
    create_database()
    create_tables(app)

    # Initialize extensions with app
    mail.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes import main_bp
    from app.routes.barangay import barangay_bp
    from app.routes.audit_logs import audit_logs
    from app.routes.password_reset import password_reset_bp
    from app.routes.register import register_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(barangay_bp)
    app.register_blueprint(audit_logs)
    app.register_blueprint(password_reset_bp)
    app.register_blueprint(register_bp)

    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        conn = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB
        )
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM user WHERE user_id = %s', (user_id,))
        user_data = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user_data:
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
            
            return User(user_data)
        return None

    return app 