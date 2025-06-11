import os
from datetime import timedelta

class Config:
    # Mail configuration
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'christinelatorre678@gmail.com'
    MAIL_PASSWORD = 'txjs ycyp ercp tegl'
    MAIL_DEFAULT_SENDER = 'christinelatorre678@gmail.com'

    # MySQL settings
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = ''  # Set your XAMPP MySQL password
    MYSQL_DB = 'crime_mapping_visualization'
    MYSQL_CURSORCLASS = 'DictCursor'